"""
Education Content Generation Workflow (New Architecture)

This workflow implements the new 3-agent pipeline:
1. Text Input -> Pedagogical Agent -> FDA Agent -> Manim Agent -> Video
2. File/URL Input -> FDA Agent -> Manim Agent -> Video

The Pedagogical Agent is ONLY used for text input to expand the context.
File and URL inputs skip this step as their content should remain biased to source.
"""

import logging
import subprocess
import boto3
import os
import json
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, Literal
from pathlib import Path
from enum import Enum

from .pedagogical_agent import PedagogicalAgent
from .fda_agent import FDAAgent
from .manim_generation_agent import ManimGenerationAgent
from .exceptions import (
    WorkflowError,
    WorkflowExecutionError,
    WorkflowTimeoutError,
    AgentError,
)
from config.agents_config import get_workflow_config

logger = logging.getLogger(__name__)


class InputType(Enum):
    """Types of content input"""
    TEXT = "text"
    FILE = "file"
    URL = "url"


class ContentPipeline:
    """
    New content generation pipeline implementing the 3-agent architecture.
    
    Pipeline:
    - Text Input: Pedagogical -> FDA -> Manim -> Render -> S3
    - File/URL: FDA -> Manim -> Render -> S3
    """
    
    def __init__(self, **kwargs):
        """Initialize the content pipeline"""
        try:
            self.config = get_workflow_config()
            self.config.update(kwargs)
            
            # Initialize agents
            self.pedagogical_agent = PedagogicalAgent()
            self.fda_agent = FDAAgent()
            self.manim_agent = ManimGenerationAgent()
            
            # S3 configuration
            self.s3_client = None
            self.s3_bucket = os.getenv("S3_BUCKET_NAME", "bloom-educational-videos")
            
            # Output directories
            self.output_dir = Path(os.getenv("OUTPUT_DIR", "./media/videos"))
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Tracking
            self.execution_count = 0
            self.last_execution_time: Optional[datetime] = None
            
            logger.info("Initialized ContentPipeline with 3-agent architecture")
            
        except Exception as e:
            logger.error(f"Failed to initialize ContentPipeline: {str(e)}")
            raise WorkflowError(
                "Failed to initialize content pipeline",
                original_error=e
            )
    
    def _init_s3_client(self):
        """Initialize S3 client if not already done"""
        if self.s3_client is None:
            try:
                self.s3_client = boto3.client('s3')
                logger.info(f"Initialized S3 client for bucket: {self.s3_bucket}")
            except Exception as e:
                logger.warning(f"Could not initialize S3 client: {e}")
    
    def execute(
        self,
        content: str,
        input_type: InputType = InputType.TEXT,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the content generation pipeline.
        
        Args:
            content: Raw content to process
            input_type: Type of input (TEXT, FILE, URL)
            context: Additional context including:
                - topic: Topic name
                - difficulty_level: beginner/intermediate/advanced
                - target_audience: Target audience description
                - learning_goals: List of learning goals
                
        Returns:
            Dictionary containing:
                - video_url: S3 URL to generated video
                - video_path: Local path to video (if available)
                - fda: FDA specification used
                - manim_code: Generated Manim code
                - metadata: Generation metadata with timestamps
        """
        self.execution_count += 1
        self.last_execution_time = datetime.now()
        execution_id = f"exec_{self.execution_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        context = context or {}
        context["execution_id"] = execution_id
        context["input_type"] = input_type.value
        context["start_time"] = datetime.now().isoformat()
        
        logger.info(f"Starting pipeline execution {execution_id} with input type: {input_type.value}")
        
        try:
            # Step 1: Pedagogical expansion (TEXT input only)
            if input_type == InputType.TEXT:
                logger.info("Step 1: Running Pedagogical Agent for text expansion")
                pedagogical_output = self._run_pedagogical_agent(content, context)
                processed_content = pedagogical_output.get("expanded_content", content)
                context["pedagogical_output"] = pedagogical_output
            else:
                logger.info("Step 1: Skipping Pedagogical Agent (file/URL input)")
                processed_content = content
                context["pedagogical_output"] = None
            
            # Step 2: Generate FDA
            logger.info("Step 2: Running FDA Agent for animation specification")
            fda = self._run_fda_agent(processed_content, context)
            
            # Step 3: Generate Manim code from FDA
            logger.info("Step 3: Running Manim Agent for code generation")
            manim_result = self._run_manim_agent(fda, context)
            manim_code = manim_result.get("manim_code", "")
            
            # Step 4: Render video
            logger.info("Step 4: Rendering video with Manim")
            video_path = self._render_video(manim_code, execution_id)
            
            # Step 5: Upload to S3
            logger.info("Step 5: Uploading to S3")
            video_url = self._upload_to_s3(video_path, execution_id, fda)
            
            # Compile result
            result = {
                "video_url": video_url,
                "video_path": str(video_path) if video_path else None,
                "fda": fda,
                "manim_code": manim_code,
                "metadata": {
                    "execution_id": execution_id,
                    "input_type": input_type.value,
                    "start_time": context["start_time"],
                    "end_time": datetime.now().isoformat(),
                    "topic": context.get("topic", fda.get("topic", "Educational Content")),
                    "difficulty_level": fda.get("difficulty_level", "intermediate"),
                    "total_slides": len(fda.get("slides", [])),
                    "estimated_duration": fda.get("total_duration_seconds", 60),
                    "pipeline_version": "2.0",
                    "agents_used": ["pedagogical"] if input_type == InputType.TEXT else [] + ["fda", "manim"],
                }
            }
            
            logger.info(f"Successfully completed pipeline execution {execution_id}")
            return result
            
        except AgentError as e:
            logger.error(f"Agent error in pipeline: {str(e)}")
            raise WorkflowExecutionError(
                f"Pipeline failed at agent stage: {str(e)}",
                failed_agents=[e.agent_type] if hasattr(e, 'agent_type') else [],
                original_error=e
            )
        except Exception as e:
            logger.error(f"Unexpected error in pipeline: {str(e)}")
            raise WorkflowExecutionError(
                f"Pipeline failed unexpectedly: {str(e)}",
                original_error=e
            )
    
    def _run_pedagogical_agent(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the Pedagogical Agent to expand text content"""
        try:
            result = self.pedagogical_agent.process_content(content, context)
            logger.info("Pedagogical Agent completed successfully")
            return result
        except Exception as e:
            logger.warning(f"Pedagogical Agent failed: {e}, using original content")
            # Return minimal output on failure
            return {
                "expanded_content": content,
                "learning_objectives": [],
                "suggested_structure": [],
                "error": str(e)
            }
    
    def _run_fda_agent(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the FDA Agent to generate animation specification"""
        result = self.fda_agent.process_content(content, context)
        logger.info(f"FDA Agent completed with {len(result.get('slides', []))} slides")
        return result
    
    def _run_manim_agent(
        self,
        fda: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the Manim Agent to generate code from FDA"""
        result = self.manim_agent.process_content(fda, context)
        logger.info("Manim Agent completed code generation")
        return result
    
    def _render_video(
        self,
        manim_code: str,
        execution_id: str
    ) -> Optional[Path]:
        """Render the Manim code to video"""
        temp_file = None
        try:
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create temporary file for Manim code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                prefix='manim_'
            ) as f:
                f.write(manim_code)
                temp_file = f.name
            
            logger.info(f"Wrote Manim code to {temp_file}")
            
            # Output filename (just the name, not full path)
            output_name = f"educational_presentation_{execution_id}"
            
            # Run Manim render command with correct flags
            # --media_dir sets the output directory
            # -o sets the output filename (without extension)
            # -qm is medium quality (720p)
            cmd = [
                "manim",
                "render",
                "-qm",  # Medium quality
                "--media_dir", str(self.output_dir.parent),  # Parent dir, Manim adds videos/
                "-o", output_name,  # Just filename, not full path
                temp_file,
                "EducationalPresentation"
            ]
            
            logger.info(f"Running Manim command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.output_dir.parent)  # Set working directory
            )
            
            # Log output for debugging
            if result.stdout:
                logger.debug(f"Manim stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"Manim stderr: {result.stderr}")
            
            if result.returncode != 0:
                logger.error(f"Manim render failed with code {result.returncode}: {result.stderr}")
                # Still try to find any generated video
            
            # Manim outputs to: media_dir/videos/<scene_name>/720p30/<output_name>.mp4
            # Search for the generated video in multiple possible locations
            search_patterns = [
                f"**/{output_name}.mp4",
                f"**/EducationalPresentation.mp4",
                f"**/*{execution_id}*.mp4",
                "**/*.mp4"
            ]
            
            media_root = self.output_dir.parent
            for pattern in search_patterns:
                possible_outputs = list(media_root.glob(pattern))
                if possible_outputs:
                    # Get the most recently modified file
                    most_recent = max(possible_outputs, key=lambda p: p.stat().st_mtime)
                    logger.info(f"Found rendered video: {most_recent}")
                    return most_recent
            
            logger.error("No video file found after Manim render")
            return None
            
        except subprocess.TimeoutExpired:
            logger.error("Manim render timed out after 5 minutes")
            return None
        except Exception as e:
            logger.error(f"Error rendering video: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
        finally:
            # Cleanup temp file
            if temp_file:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
    
    def _upload_to_s3(
        self,
        video_path: Optional[Path],
        execution_id: str,
        fda: Dict[str, Any]
    ) -> Optional[str]:
        """Upload video and metadata to S3"""
        if not video_path or not video_path.exists():
            logger.warning("No video to upload to S3")
            return None
        
        try:
            self._init_s3_client()
            
            if self.s3_client is None:
                logger.warning("S3 client not available")
                return None
            
            # Generate S3 key
            timestamp = datetime.now().strftime('%Y/%m/%d')
            video_key = f"videos/{timestamp}/{execution_id}/{video_path.name}"
            metadata_key = f"videos/{timestamp}/{execution_id}/metadata.json"
            
            # Upload video
            self.s3_client.upload_file(
                str(video_path),
                self.s3_bucket,
                video_key,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                    'Metadata': {
                        'execution_id': execution_id,
                        'topic': fda.get('topic', 'unknown'),
                        'duration': str(fda.get('total_duration_seconds', 0))
                    }
                }
            )
            
            # Create and upload metadata with timestamp
            metadata = {
                "execution_id": execution_id,
                "video_key": video_key,
                "fda": fda,
                "created_at": datetime.now().isoformat(),
                "topic": fda.get("topic", "Educational Content"),
                "duration_seconds": fda.get("total_duration_seconds", 60),
                "slide_count": len(fda.get("slides", []))
            }
            
            self.s3_client.put_object(
                Body=json.dumps(metadata, indent=2),
                Bucket=self.s3_bucket,
                Key=metadata_key,
                ContentType='application/json'
            )
            
            # Generate presigned URL
            video_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': video_key},
                ExpiresIn=86400  # 24 hours
            )
            
            logger.info(f"Uploaded video to S3: {video_key}")
            return video_url
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return None
    
    # Convenience methods for different input types
    def process_text(
        self,
        text: str,
        topic: Optional[str] = None,
        difficulty_level: str = "intermediate",
        target_audience: str = "general"
    ) -> Dict[str, Any]:
        """Process text input through the full pipeline"""
        context = {
            "topic": topic or "Educational Content",
            "difficulty_level": difficulty_level,
            "target_audience": target_audience
        }
        return self.execute(text, InputType.TEXT, context)
    
    def process_file_content(
        self,
        content: str,
        filename: str,
        topic: Optional[str] = None,
        difficulty_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """Process file content (skips Pedagogical Agent)"""
        context = {
            "topic": topic or Path(filename).stem,
            "difficulty_level": difficulty_level,
            "source_filename": filename
        }
        return self.execute(content, InputType.FILE, context)
    
    def process_url_content(
        self,
        content: str,
        url: str,
        topic: Optional[str] = None,
        difficulty_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """Process URL content (skips Pedagogical Agent)"""
        context = {
            "topic": topic or "Web Content",
            "difficulty_level": difficulty_level,
            "source_url": url
        }
        return self.execute(content, InputType.URL, context)


# Legacy compatibility: Keep PedagogyWorkflow as alias
# This maintains backward compatibility with existing code
class PedagogyWorkflow(ContentPipeline):
    """
    Legacy workflow class maintained for backward compatibility.
    Use ContentPipeline for new implementations.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.warning(
            "PedagogyWorkflow is deprecated. Use ContentPipeline instead."
        )
    
    def execute(
        self,
        input_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute legacy workflow - defaults to text input.
        
        For the new pipeline, use ContentPipeline.execute() with input_type parameter.
        """
        # Determine input type from context if available
        context = context or {}
        input_type_str = context.get("input_type", "text")
        
        if input_type_str == "file":
            input_type = InputType.FILE
        elif input_type_str == "url":
            input_type = InputType.URL
        else:
            input_type = InputType.TEXT
        
        result = super().execute(input_content, input_type, context)
        
        # Convert to legacy format for backward compatibility
        return self._convert_to_legacy_format(result, context)
    
    def _convert_to_legacy_format(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert new pipeline result to legacy format"""
        fda = result.get("fda", {})
        
        # Build legacy educational_script format
        legacy_result = {
            "title": fda.get("title", "Educational Content"),
            "original_content": context.get("original_content", ""),
            "learning_objectives": self._extract_objectives_from_fda(fda),
            "sections": self._extract_sections_from_fda(fda),
            "assessments": [],
            "animations": fda.get("slides", []),
            "metadata": result.get("metadata", {}),
            # Add new fields
            "video_url": result.get("video_url"),
            "video_path": result.get("video_path"),
            "manim_code": result.get("manim_code"),
            "fda": fda,
        }
        
        return legacy_result
    
    def _extract_objectives_from_fda(self, fda: Dict[str, Any]) -> list:
        """Extract learning objectives from FDA metadata"""
        metadata = fda.get("metadata", {})
        return metadata.get("learning_objectives", [])
    
    def _extract_sections_from_fda(self, fda: Dict[str, Any]) -> list:
        """Extract sections from FDA slides"""
        sections = []
        for slide in fda.get("slides", []):
            section = {
                "title": slide.get("title", ""),
                "content": slide.get("content", {}).get("main_text", ""),
                "slide_type": slide.get("slide_type", "concept"),
            }
            sections.append(section)
        return sections
