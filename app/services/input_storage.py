"""
Input storage service for storing processed inputs with comprehensive metadata
"""

import uuid
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import logging

from app.core.config import settings
from app.services.vector_db import vector_db_service
from app.services.file_storage import file_storage_service
from app.models.content import ContentInput, ContentType

logger = logging.getLogger(__name__)

class InputStorageService:
    """Service for storing and retrieving processed inputs with metadata"""
    
    def __init__(self):
        """Initialize input storage service"""
        self.storage_dir = Path(settings.UPLOAD_DIR) / "input_storage"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage for quick access (replace with database later)
        self.stored_inputs = {}
        
        logger.info(f"Input storage service initialized with storage dir: {self.storage_dir}")
    
    async def store_input(
        self,
        content_input: ContentInput,
        validation_result: Optional[Dict[str, Any]] = None,
        processing_metadata: Optional[Dict[str, Any]] = None,
        generation_id: Optional[str] = None
    ) -> str:
        """
        Store input content with comprehensive metadata
        
        Args:
            content_input: The input content to store
            validation_result: Results from content validation
            processing_metadata: Metadata from processing steps
            generation_id: Associated generation ID if applicable
            
        Returns:
            Unique storage ID for the stored input
        """
        try:
            storage_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Create content hash for deduplication
            content_hash = self._create_content_hash(content_input.content)
            
            # Prepare comprehensive metadata
            metadata = {
                "storage_id": storage_id,
                "content_type": content_input.content_type,
                "content_hash": content_hash,
                "stored_at": timestamp.isoformat(),
                "generation_id": generation_id,
                "original_metadata": content_input.metadata,
                "validation_result": validation_result or {},
                "processing_metadata": processing_metadata or {},
                "content_length": len(content_input.content),
                "storage_version": "1.0"
            }
            
            # Add type-specific metadata
            if content_input.content_type == ContentType.FILE:
                metadata.update(self._extract_file_metadata(content_input))
            elif content_input.content_type == ContentType.URL:
                metadata.update(self._extract_url_metadata(content_input))
            elif content_input.content_type == ContentType.TEXT:
                metadata.update(self._extract_text_metadata(content_input))
            
            # Store content and metadata to file system
            await self._store_to_filesystem(storage_id, content_input.content, metadata)
            
            # Store in vector database for semantic search
            await self._store_to_vector_db(storage_id, content_input.content, metadata)
            
            # Store in memory for quick access
            self.stored_inputs[storage_id] = {
                "content": content_input.content,
                "metadata": metadata,
                "stored_at": timestamp
            }
            
            logger.info(f"Successfully stored input with ID: {storage_id}")
            return storage_id
            
        except Exception as e:
            logger.error(f"Failed to store input: {str(e)}")
            raise
    
    async def retrieve_input(self, storage_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored input by ID
        
        Args:
            storage_id: Unique storage identifier
            
        Returns:
            Stored input data with metadata if found, None otherwise
        """
        try:
            # Check memory cache first
            if storage_id in self.stored_inputs:
                return self.stored_inputs[storage_id]
            
            # Load from filesystem
            stored_data = await self._load_from_filesystem(storage_id)
            if stored_data:
                # Cache in memory
                self.stored_inputs[storage_id] = stored_data
                return stored_data
            
            logger.warning(f"Input not found: {storage_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve input {storage_id}: {str(e)}")
            return None
    
    async def search_inputs(
        self,
        query: str,
        content_type: Optional[ContentType] = None,
        generation_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search stored inputs using semantic search and filters
        
        Args:
            query: Search query text
            content_type: Filter by content type
            generation_id: Filter by generation ID
            limit: Maximum number of results
            
        Returns:
            List of matching inputs with metadata
        """
        try:
            # Build metadata filters
            where_filters = {}
            if content_type:
                where_filters["content_type"] = content_type.value
            if generation_id:
                where_filters["generation_id"] = generation_id
            
            # Search in vector database
            search_results = vector_db_service.search_content(
                query=query,
                n_results=limit,
                where=where_filters if where_filters else None
            )
            
            # Enrich results with full metadata
            enriched_results = []
            for result in search_results:
                storage_id = result["id"]
                stored_input = await self.retrieve_input(storage_id)
                if stored_input:
                    enriched_results.append({
                        "storage_id": storage_id,
                        "content": stored_input["content"],
                        "metadata": stored_input["metadata"],
                        "similarity_score": 1 - result.get("distance", 0),  # Convert distance to similarity
                        "search_snippet": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                    })
            
            logger.info(f"Found {len(enriched_results)} inputs for query: {query}")
            return enriched_results
            
        except Exception as e:
            logger.error(f"Failed to search inputs: {str(e)}")
            return []
    
    async def list_inputs(
        self,
        content_type: Optional[ContentType] = None,
        generation_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List stored inputs with optional filters
        
        Args:
            content_type: Filter by content type
            generation_id: Filter by generation ID
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of stored inputs with metadata
        """
        try:
            # Get all stored inputs
            all_inputs = []
            
            # Load from memory cache
            for storage_id, stored_data in self.stored_inputs.items():
                metadata = stored_data["metadata"]
                
                # Apply filters
                if content_type and metadata.get("content_type") != content_type.value:
                    continue
                if generation_id and metadata.get("generation_id") != generation_id:
                    continue
                
                all_inputs.append({
                    "storage_id": storage_id,
                    "content_type": metadata.get("content_type"),
                    "content_hash": metadata.get("content_hash"),
                    "stored_at": metadata.get("stored_at"),
                    "generation_id": metadata.get("generation_id"),
                    "content_length": metadata.get("content_length"),
                    "validation_status": metadata.get("validation_result", {}).get("is_valid"),
                    "processing_status": metadata.get("processing_metadata", {}).get("status")
                })
            
            # Sort by storage time (newest first)
            all_inputs.sort(key=lambda x: x["stored_at"], reverse=True)
            
            # Apply pagination
            paginated_inputs = all_inputs[offset:offset + limit]
            
            logger.info(f"Listed {len(paginated_inputs)} inputs (total: {len(all_inputs)})")
            return paginated_inputs
            
        except Exception as e:
            logger.error(f"Failed to list inputs: {str(e)}")
            return []
    
    async def get_input_history(self, content_hash: str) -> List[Dict[str, Any]]:
        """
        Get processing history for inputs with the same content hash
        
        Args:
            content_hash: Content hash to search for
            
        Returns:
            List of inputs with the same content hash, ordered by storage time
        """
        try:
            history = []
            
            for storage_id, stored_data in self.stored_inputs.items():
                if stored_data["metadata"].get("content_hash") == content_hash:
                    history.append({
                        "storage_id": storage_id,
                        "stored_at": stored_data["metadata"]["stored_at"],
                        "generation_id": stored_data["metadata"].get("generation_id"),
                        "validation_result": stored_data["metadata"].get("validation_result"),
                        "processing_metadata": stored_data["metadata"].get("processing_metadata")
                    })
            
            # Sort by storage time
            history.sort(key=lambda x: x["stored_at"])
            
            logger.info(f"Found {len(history)} entries in history for content hash: {content_hash}")
            return history
            
        except Exception as e:
            logger.error(f"Failed to get input history: {str(e)}")
            return []
    
    async def delete_input(self, storage_id: str) -> bool:
        """
        Delete stored input and its metadata
        
        Args:
            storage_id: Unique storage identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from filesystem
            await self._delete_from_filesystem(storage_id)
            
            # Remove from vector database
            vector_db_service.delete_content(storage_id)
            
            # Remove from memory cache
            if storage_id in self.stored_inputs:
                del self.stored_inputs[storage_id]
            
            logger.info(f"Successfully deleted input: {storage_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete input {storage_id}: {str(e)}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            total_inputs = len(self.stored_inputs)
            
            # Count by content type
            type_counts = {}
            total_size = 0
            
            for stored_data in self.stored_inputs.values():
                content_type = stored_data["metadata"].get("content_type", "unknown")
                type_counts[content_type] = type_counts.get(content_type, 0) + 1
                total_size += stored_data["metadata"].get("content_length", 0)
            
            # Get vector database stats
            vector_stats = vector_db_service.get_collection_stats()
            
            # Get file storage stats
            file_stats = file_storage_service.get_storage_stats()
            
            return {
                "total_inputs": total_inputs,
                "content_type_distribution": type_counts,
                "total_content_size_bytes": total_size,
                "total_content_size_mb": round(total_size / (1024 * 1024), 2),
                "vector_db_stats": vector_stats,
                "file_storage_stats": file_stats,
                "storage_directory": str(self.storage_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {"error": str(e)}
    
    def _create_content_hash(self, content: str) -> str:
        """Create SHA-256 hash of content for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _extract_file_metadata(self, content_input: ContentInput) -> Dict[str, Any]:
        """Extract file-specific metadata"""
        metadata = content_input.metadata or {}
        return {
            "file_metadata": {
                "filename": metadata.get("filename"),
                "file_size": metadata.get("file_size"),
                "mime_type": metadata.get("mime_type"),
                "file_extension": metadata.get("file_extension"),
                "upload_timestamp": metadata.get("upload_timestamp")
            }
        }
    
    def _extract_url_metadata(self, content_input: ContentInput) -> Dict[str, Any]:
        """Extract URL-specific metadata"""
        metadata = content_input.metadata or {}
        return {
            "url_metadata": {
                "source_url": content_input.content if content_input.content_type == ContentType.URL else metadata.get("source_url"),
                "page_title": metadata.get("page_title"),
                "domain": metadata.get("domain"),
                "scraping_timestamp": metadata.get("scraping_timestamp"),
                "content_type": metadata.get("content_type"),
                "response_status": metadata.get("response_status")
            }
        }
    
    def _extract_text_metadata(self, content_input: ContentInput) -> Dict[str, Any]:
        """Extract text-specific metadata"""
        content = content_input.content
        words = content.split()
        
        return {
            "text_metadata": {
                "word_count": len(words),
                "character_count": len(content),
                "line_count": len(content.split('\n')),
                "estimated_reading_time_minutes": max(1, len(words) // 200),  # ~200 words per minute
                "language_detected": None,  # Could add language detection later
                "text_complexity_score": None  # Could add complexity analysis later
            }
        }
    
    async def _store_to_filesystem(self, storage_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Store content and metadata to filesystem"""
        try:
            # Create storage directory for this input
            input_dir = self.storage_dir / storage_id
            input_dir.mkdir(exist_ok=True)
            
            # Store content
            content_file = input_dir / "content.txt"
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Store metadata
            metadata_file = input_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.debug(f"Stored input to filesystem: {input_dir}")
            
        except Exception as e:
            logger.error(f"Failed to store to filesystem: {str(e)}")
            raise
    
    async def _load_from_filesystem(self, storage_id: str) -> Optional[Dict[str, Any]]:
        """Load content and metadata from filesystem"""
        try:
            input_dir = self.storage_dir / storage_id
            if not input_dir.exists():
                return None
            
            # Load content
            content_file = input_dir / "content.txt"
            if not content_file.exists():
                return None
            
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Load metadata
            metadata_file = input_dir / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            return {
                "content": content,
                "metadata": metadata,
                "stored_at": datetime.fromisoformat(metadata.get("stored_at", datetime.now().isoformat()))
            }
            
        except Exception as e:
            logger.error(f"Failed to load from filesystem: {str(e)}")
            return None
    
    async def _store_to_vector_db(self, storage_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Store content in vector database for semantic search"""
        try:
            # Prepare metadata for vector storage (only JSON-serializable values)
            vector_metadata = {
                "storage_id": storage_id,
                "content_type": metadata.get("content_type"),
                "content_hash": metadata.get("content_hash"),
                "stored_at": metadata.get("stored_at"),
                "generation_id": metadata.get("generation_id"),
                "content_length": metadata.get("content_length"),
                "validation_status": metadata.get("validation_result", {}).get("is_valid", False)
            }
            
            # Add type-specific metadata
            if metadata.get("file_metadata"):
                vector_metadata["filename"] = metadata["file_metadata"].get("filename")
                vector_metadata["file_size"] = metadata["file_metadata"].get("file_size")
                vector_metadata["mime_type"] = metadata["file_metadata"].get("mime_type")
            
            if metadata.get("url_metadata"):
                vector_metadata["source_url"] = metadata["url_metadata"].get("source_url")
                vector_metadata["domain"] = metadata["url_metadata"].get("domain")
                vector_metadata["page_title"] = metadata["url_metadata"].get("page_title")
            
            if metadata.get("text_metadata"):
                vector_metadata["word_count"] = metadata["text_metadata"].get("word_count")
                vector_metadata["estimated_reading_time"] = metadata["text_metadata"].get("estimated_reading_time_minutes")
            
            # Store in vector database
            success = vector_db_service.add_content(
                content_id=storage_id,
                content=content,
                metadata=vector_metadata
            )
            
            if not success:
                logger.warning(f"Failed to store input {storage_id} in vector database")
            
        except Exception as e:
            logger.error(f"Failed to store to vector database: {str(e)}")
            # Don't raise - vector storage is not critical for basic functionality
    
    async def _delete_from_filesystem(self, storage_id: str) -> None:
        """Delete content and metadata from filesystem"""
        try:
            input_dir = self.storage_dir / storage_id
            if input_dir.exists():
                import shutil
                shutil.rmtree(input_dir)
                logger.debug(f"Deleted input from filesystem: {input_dir}")
            
        except Exception as e:
            logger.error(f"Failed to delete from filesystem: {str(e)}")
            raise

# Global instance
input_storage_service = InputStorageService()