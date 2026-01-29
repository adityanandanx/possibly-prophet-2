"""
Video rendering service for executing Manim code and uploading to S3.

This service:
1. Executes generated Manim code to render videos
2. Uploads rendered videos to AWS S3
3. Returns the S3 URL for playback
"""

import subprocess
import tempfile
import os
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoRenderer:
    """
    Service for rendering Manim code into videos and uploading to S3.
    """

    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        s3_prefix: str = "presentations/",
        local_media_dir: Optional[str] = None,
    ):
        """
        Initialize the video renderer.

        Args:
            s3_bucket: S3 bucket name for uploads (defaults to env var S3_BUCKET)
            s3_prefix: Prefix/folder path in S3 bucket
            local_media_dir: Local directory for rendered videos
        """
        self.s3_bucket = s3_bucket or os.environ.get(
            "S3_BUCKET", "educational-presentations"
        )
        self.s3_prefix = s3_prefix

        # Default to backend/media directory
        if local_media_dir:
            self.local_media_dir = Path(local_media_dir)
        else:
            backend_dir = Path(__file__).parent.parent.parent
            self.local_media_dir = backend_dir / "media"

        self.local_media_dir.mkdir(parents=True, exist_ok=True)

        # Initialize S3 client
        self._s3_client = None

        logger.info(
            f"Initialized VideoRenderer with bucket={self.s3_bucket}, local_dir={self.local_media_dir}"
        )

    @property
    def s3_client(self):
        """Lazy initialization of S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                aws_session_token=settings.AWS_SESSION_TOKEN,
                region_name=settings.AWS_DEFAULT_REGION,
            )
        return self._s3_client

    async def render_and_upload(
        self,
        manim_code: str,
        generation_id: str,
        quality: str = "medium_quality",
        frame_rate: int = 30,
    ) -> Dict[str, Any]:
        """
        Render Manim code to video and upload to S3.

        Args:
            manim_code: The Manim Python code to execute
            generation_id: Unique ID for this generation
            quality: Manim quality setting (low_quality, medium_quality, high_quality, production_quality)
            frame_rate: Video frame rate

        Returns:
            Dictionary with video URL and metadata
        """
        video_id = f"{generation_id}_{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting video render for {video_id}")

        try:
            # Pre-validation: Check if the code looks valid before attempting render
            if not self._validate_code_structure(manim_code):
                raise ValueError("Invalid Manim code structure - missing required elements")
            
            # Step 1: Write Manim code to temp file
            temp_dir = tempfile.mkdtemp(prefix="manim_")
            script_path = os.path.join(temp_dir, "presentation.py")

            with open(script_path, "w") as f:
                f.write(manim_code)

            logger.info(f"Written Manim script to {script_path}")

            # Step 2: Execute Manim to render the video
            video_path = await self._execute_manim(
                script_path=script_path,
                output_dir=temp_dir,
                quality=quality,
                frame_rate=frame_rate,
            )

            if not video_path or not os.path.exists(video_path):
                raise RuntimeError("Manim rendering failed - no video file produced")

            logger.info(f"Video rendered successfully: {video_path}")

            # Step 3: Get video metadata
            video_size = os.path.getsize(video_path)

            # Step 4: Upload to S3
            s3_key = f"{self.s3_prefix}{video_id}/presentation.mp4"
            s3_url = await self._upload_to_s3(video_path, s3_key)

            # Step 5: Copy to local media directory for local serving
            local_video_dir = self.local_media_dir / "videos" / video_id
            local_video_dir.mkdir(parents=True, exist_ok=True)
            local_video_path = local_video_dir / "presentation.mp4"

            # Copy file to local media directory
            import shutil

            shutil.copy2(video_path, local_video_path)

            logger.info(f"Video copied to local: {local_video_path}")

            # Step 6: Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

            return {
                "success": True,
                "video_id": video_id,
                "s3_url": s3_url,
                "s3_key": s3_key,
                "local_url": f"/media/videos/{video_id}/presentation.mp4",
                "file_size_bytes": video_size,
                "quality": quality,
                "frame_rate": frame_rate,
                "rendered_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Video rendering failed: {str(e)}")
            return {
                "success": False,
                "video_id": video_id,
                "error": str(e),
                "rendered_at": datetime.now().isoformat(),
            }

    async def _execute_manim(
        self,
        script_path: str,
        output_dir: str,
        quality: str = "medium_quality",
        frame_rate: int = 30,
    ) -> Optional[str]:
        """
        Execute Manim command to render the video.

        Args:
            script_path: Path to the Manim Python script
            output_dir: Directory for output files
            quality: Quality setting
            frame_rate: Frame rate

        Returns:
            Path to the rendered video file, or None if failed
        """
        # Map quality to Manim flags
        quality_flags = {
            "low_quality": "-ql",
            "medium_quality": "-qm",
            "high_quality": "-qh",
            "production_quality": "-qp",
        }

        quality_flag = quality_flags.get(quality, "-qm")

        # Build Manim command
        # We need to find the scene class name from the code
        scene_name = "EducationalPresentation"  # Default, could be parsed from code

        cmd = [
            "manim",
            quality_flag,
            "--frame_rate",
            str(frame_rate),
            "--media_dir",
            output_dir,
            script_path,
            scene_name,
        ]

        logger.info(f"Executing Manim command: {' '.join(cmd)}")

        try:
            # Run Manim subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.path.dirname(script_path),
            )

            if result.returncode != 0:
                logger.error(f"Manim stderr: {result.stderr}")
                logger.error(f"Manim stdout: {result.stdout}")
                raise RuntimeError(
                    f"Manim exited with code {result.returncode}: {result.stderr}"
                )

            logger.info(f"Manim output: {result.stdout}")

            # Find the rendered video file
            # Manim outputs to: media_dir/videos/script_name/quality/scene_name.mp4
            video_search_dir = Path(output_dir) / "videos"

            # Search for .mp4 files
            for mp4_file in video_search_dir.rglob("*.mp4"):
                logger.info(f"Found video file: {mp4_file}")
                return str(mp4_file)

            # Also check direct output
            for mp4_file in Path(output_dir).rglob("*.mp4"):
                logger.info(f"Found video file: {mp4_file}")
                return str(mp4_file)

            logger.error("No video file found after Manim execution")
            return None

        except subprocess.TimeoutExpired:
            logger.error("Manim rendering timed out after 5 minutes")
            raise RuntimeError("Video rendering timed out")
        except FileNotFoundError:
            logger.error("Manim command not found - is Manim installed?")
            raise RuntimeError("Manim is not installed or not in PATH")

    async def _upload_to_s3(self, local_path: str, s3_key: str) -> str:
        """
        Upload a file to S3.

        Args:
            local_path: Local file path
            s3_key: S3 object key

        Returns:
            S3 URL of the uploaded file
        """
        try:
            logger.info(f"Uploading {local_path} to s3://{self.s3_bucket}/{s3_key}")

            # Upload with public-read ACL for easy access
            self.s3_client.upload_file(
                local_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    "ContentType": "video/mp4",
                    # Note: For public access, bucket policy or ACL needs to be configured
                },
            )

            # Generate the S3 URL
            s3_url = f"https://{self.s3_bucket}.s3.{settings.AWS_DEFAULT_REGION}.amazonaws.com/{s3_key}"

            logger.info(f"Successfully uploaded to {s3_url}")
            return s3_url

        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            # Don't fail the whole operation - return a placeholder
            return f"s3://{self.s3_bucket}/{s3_key} (upload failed: {str(e)})"

    async def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for accessing a private S3 object.

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.s3_bucket, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise

    def check_video_exists(self, video_id: str) -> Dict[str, Any]:
        """
        Check if a video exists locally and/or in S3.

        Args:
            video_id: The video ID to check

        Returns:
            Dictionary with existence status
        """
        local_path = self.local_media_dir / "videos" / video_id / "presentation.mp4"
        s3_key = f"{self.s3_prefix}{video_id}/presentation.mp4"

        local_exists = local_path.exists()

        s3_exists = False
        try:
            self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
            s3_exists = True
        except ClientError:
            pass

        return {
            "video_id": video_id,
            "local_exists": local_exists,
            "local_path": str(local_path) if local_exists else None,
            "s3_exists": s3_exists,
            "s3_key": s3_key if s3_exists else None,
        }

    def _validate_code_structure(self, code: str) -> bool:
        """
        Validate that code has the basic structure required for Manim.
        
        This is a quick sanity check before attempting to render.
        
        Args:
            code: The Manim Python code to validate
            
        Returns:
            True if code structure looks valid, False otherwise
        """
        if not code or not isinstance(code, str):
            logger.error("Code is empty or not a string")
            return False
        
        # Check for obvious non-code patterns (raw AI response)
        invalid_patterns = [
            "'role':",
            '"role":',
            "'content':",
            '"content":',
            "{'role'",
            '{"role"',
        ]
        for pattern in invalid_patterns:
            if pattern in code:
                logger.error(f"Code contains invalid pattern (raw AI response): {pattern}")
                return False
        
        # Check for required elements
        required = [
            "from manim import",
            "class",
            "def construct",
        ]
        for req in required:
            if req not in code:
                logger.error(f"Code missing required element: {req}")
                return False
        
        # Try to compile to check for syntax errors
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            logger.error(f"Code has syntax error at line {e.lineno}: {e.msg}")
            return False
        
        return True
