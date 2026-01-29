"""
File storage service for handling file uploads and storage
"""

import os
import shutil
import hashlib
import magic
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from pathlib import Path
import aiofiles
from fastapi import UploadFile
from app.core.config import settings
from app.models.content import FileUploadResponse

logger = logging.getLogger(__name__)

class FileStorageService:
    """Service for managing file uploads and storage"""
    
    def __init__(self):
        """Initialize file storage service"""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_FILE_TYPES
        self.allowed_mime_types = settings.ALLOWED_MIME_TYPES
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"File storage initialized with upload dir: {self.upload_dir}")
    
    async def save_uploaded_file(
        self,
        file: UploadFile,
        user_id: Optional[str] = None
    ) -> Optional[FileUploadResponse]:
        """
        Save an uploaded file to storage
        
        Args:
            file: FastAPI UploadFile object
            user_id: Optional user identifier
        
        Returns:
            FileUploadResponse if successful, None otherwise
        """
        try:
            # Validate file
            validation_result = await self._validate_file(file)
            if not validation_result["valid"]:
                logger.error(f"File validation failed: {validation_result['error']}")
                return None
            
            # Generate unique file ID and path
            file_id = self._generate_file_id(file.filename)
            file_extension = Path(file.filename).suffix.lower()
            stored_filename = f"{file_id}{file_extension}"
            file_path = self.upload_dir / stored_filename
            
            # Save file to disk
            await self._write_file_to_disk(file, file_path)
            
            # Get file info
            file_size = file_path.stat().st_size
            mime_type = self._get_mime_type(file_path)
            
            # Create response
            response = FileUploadResponse(
                file_id=file_id,
                filename=file.filename,
                file_size=file_size,
                mime_type=mime_type,
                uploaded_at=datetime.now(),
                processed=False
            )
            
            logger.info(f"File saved successfully: {file_id} ({file.filename})")
            return response
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file {file.filename}: {str(e)}")
            return None
    
    async def get_file_content(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve file content by ID
        
        Args:
            file_id: File identifier
        
        Returns:
            File content as bytes if found, None otherwise
        """
        try:
            file_path = self._get_file_path(file_id)
            if not file_path or not file_path.exists():
                logger.warning(f"File not found: {file_id}")
                return None
            
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            logger.info(f"Retrieved file content: {file_id}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to retrieve file content {file_id}: {str(e)}")
            return None
    
    async def get_file_text_content(self, file_id: str) -> Optional[str]:
        """
        Retrieve file content as text (for text files)
        
        Args:
            file_id: File identifier
        
        Returns:
            File content as string if found and readable, None otherwise
        """
        try:
            content = await self.get_file_content(file_id)
            if not content:
                return None
            
            # Try to decode as UTF-8
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        return content.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                
                logger.error(f"Could not decode file {file_id} as text")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get text content for file {file_id}: {str(e)}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file by ID
        
        Args:
            file_id: File identifier
        
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_file_path(file_id)
            if not file_path or not file_path.exists():
                logger.warning(f"File not found for deletion: {file_id}")
                return False
            
            file_path.unlink()
            logger.info(f"File deleted successfully: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {str(e)}")
            return False
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file information by ID
        
        Args:
            file_id: File identifier
        
        Returns:
            File information dictionary if found, None otherwise
        """
        try:
            file_path = self._get_file_path(file_id)
            if not file_path or not file_path.exists():
                return None
            
            stat = file_path.stat()
            mime_type = self._get_mime_type(file_path)
            
            return {
                "file_id": file_id,
                "filename": file_path.name,
                "file_size": stat.st_size,
                "mime_type": mime_type,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime)
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info {file_id}: {str(e)}")
            return None
    
    def list_files(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List stored files
        
        Args:
            limit: Maximum number of files to return
        
        Returns:
            List of file information dictionaries
        """
        try:
            files = []
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file() and len(files) < limit:
                    file_id = file_path.stem  # Filename without extension
                    file_info = self.get_file_info(file_id)
                    if file_info:
                        files.append(file_info)
            
            return sorted(files, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            total_files = 0
            total_size = 0
            
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "upload_dir": str(self.upload_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {"total_files": 0, "total_size_bytes": 0, "total_size_mb": 0}
    
    async def _validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validate uploaded file
        
        Args:
            file: FastAPI UploadFile object
        
        Returns:
            Validation result dictionary
        """
        # Check file size
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            return {
                "valid": False,
                "error": f"File size {file.size} exceeds maximum {self.max_file_size}"
            }
        
        # Check file extension
        if file.filename:
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                return {
                    "valid": False,
                    "error": f"File extension {file_extension} not allowed"
                }
        
        # Check MIME type if available
        if hasattr(file, 'content_type') and file.content_type:
            if file.content_type not in self.allowed_mime_types:
                return {
                    "valid": False,
                    "error": f"MIME type {file.content_type} not allowed"
                }
        
        return {"valid": True}
    
    async def _write_file_to_disk(self, file: UploadFile, file_path: Path) -> None:
        """
        Write uploaded file to disk
        
        Args:
            file: FastAPI UploadFile object
            file_path: Path where to save the file
        """
        async with aiofiles.open(file_path, 'wb') as f:
            # Read and write in chunks to handle large files
            chunk_size = 8192
            await file.seek(0)  # Reset file pointer
            
            while chunk := await file.read(chunk_size):
                await f.write(chunk)
    
    def _generate_file_id(self, filename: str) -> str:
        """
        Generate unique file ID
        
        Args:
            filename: Original filename
        
        Returns:
            Unique file identifier
        """
        # Create hash from filename and current timestamp
        content = f"{filename}_{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_file_path(self, file_id: str) -> Optional[Path]:
        """
        Get file path from file ID
        
        Args:
            file_id: File identifier
        
        Returns:
            Path object if file exists, None otherwise
        """
        # Look for file with any allowed extension
        for extension in self.allowed_extensions:
            file_path = self.upload_dir / f"{file_id}{extension}"
            if file_path.exists():
                return file_path
        
        return None
    
    def _get_mime_type(self, file_path: Path) -> str:
        """
        Get MIME type of file
        
        Args:
            file_path: Path to file
        
        Returns:
            MIME type string
        """
        try:
            return magic.from_file(str(file_path), mime=True)
        except Exception:
            # Fallback to extension-based detection
            extension = file_path.suffix.lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain'
            }
            return mime_map.get(extension, 'application/octet-stream')

# Global instance
file_storage_service = FileStorageService()