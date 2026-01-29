"""
Vector database service using ChromaDB for content storage and retrieval
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import logging
import os
from app.core.config import settings
from app.models.content import EducationalScript

logger = logging.getLogger(__name__)

class VectorDBService:
    """Service for managing vector database operations with ChromaDB"""
    
    def __init__(self):
        """Initialize ChromaDB client and collections"""
        self.client = None
        self.content_collection = None
        self.scripts_collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and create collections"""
        try:
            # Ensure persist directory exists
            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create or get collections
            self.content_collection = self.client.get_or_create_collection(
                name="educational_content",
                metadata={"description": "Raw educational content embeddings"}
            )
            
            self.scripts_collection = self.client.get_or_create_collection(
                name="educational_scripts",
                metadata={"description": "Generated educational script embeddings"}
            )
            
            logger.info("ChromaDB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
            raise
    
    def add_content(
        self,
        content_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Add content to the vector database
        
        Args:
            content_id: Unique identifier for the content
            content: Text content to store
            metadata: Additional metadata about the content
            embedding: Pre-computed embedding (optional, will be computed if not provided)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare documents and metadata
            documents = [content]
            ids = [content_id]
            metadatas = [metadata]
            
            if embedding:
                embeddings = [embedding]
                self.content_collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
            else:
                # Let ChromaDB compute embeddings automatically
                self.content_collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
            
            logger.info(f"Added content with ID: {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add content {content_id}: {str(e)}")
            return False
    
    def add_educational_script(
        self,
        script_id: str,
        script: EducationalScript,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add educational script to the vector database
        
        Args:
            script_id: Unique identifier for the script
            script: Educational script object
            metadata: Additional metadata about the script
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create searchable text from script
            searchable_text = self._create_searchable_text(script)
            
            # Prepare metadata with script information
            script_metadata = {
                **metadata,
                "title": script.title,
                "description": script.description or "",
                "num_sections": len(script.sections),
                "num_objectives": len(script.learning_objectives),
                "num_assessments": len(script.assessments),
                "estimated_duration": script.estimated_duration_minutes,
            }
            
            # Add tags and prerequisites as strings
            if script.tags:
                script_metadata["tags_str"] = ", ".join(script.tags)
            if script.prerequisites:
                script_metadata["prerequisites_str"] = ", ".join(script.prerequisites)
            
            # Add to scripts collection
            self.scripts_collection.add(
                documents=[searchable_text],
                ids=[script_id],
                metadatas=[script_metadata]
            )
            
            logger.info(f"Added educational script with ID: {script_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add educational script {script_id}: {str(e)}")
            return False
    
    def search_content(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content
        
        Args:
            query: Search query text
            n_results: Number of results to return
            where: Metadata filter conditions
        
        Returns:
            List of search results with content and metadata
        """
        try:
            results = self.content_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        "id": results['ids'][0][i],
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'][0] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} content results for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search content: {str(e)}")
            return []
    
    def search_scripts(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar educational scripts
        
        Args:
            query: Search query text
            n_results: Number of results to return
            where: Metadata filter conditions
        
        Returns:
            List of search results with script information and metadata
        """
        try:
            results = self.scripts_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        "id": results['ids'][0][i],
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'][0] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} script results for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search scripts: {str(e)}")
            return []
    
    def get_content_by_id(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve content by ID
        
        Args:
            content_id: Content identifier
        
        Returns:
            Content data if found, None otherwise
        """
        try:
            results = self.content_collection.get(ids=[content_id])
            
            if results['documents'] and results['documents'][0]:
                return {
                    "id": content_id,
                    "content": results['documents'][0],
                    "metadata": results['metadatas'][0] if results['metadatas'] else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get content {content_id}: {str(e)}")
            return None
    
    def delete_content(self, content_id: str) -> bool:
        """
        Delete content by ID
        
        Args:
            content_id: Content identifier
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.content_collection.delete(ids=[content_id])
            logger.info(f"Deleted content with ID: {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete content {content_id}: {str(e)}")
            return False
    
    def delete_script(self, script_id: str) -> bool:
        """
        Delete educational script by ID
        
        Args:
            script_id: Script identifier
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.scripts_collection.delete(ids=[script_id])
            logger.info(f"Deleted script with ID: {script_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete script {script_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collections
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            content_count = self.content_collection.count()
            scripts_count = self.scripts_collection.count()
            
            return {
                "content_count": content_count,
                "scripts_count": scripts_count,
                "total_items": content_count + scripts_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"content_count": 0, "scripts_count": 0, "total_items": 0}
    
    def _create_searchable_text(self, script: EducationalScript) -> str:
        """
        Create searchable text from educational script
        
        Args:
            script: Educational script object
        
        Returns:
            Combined searchable text
        """
        text_parts = [script.title]
        
        if script.description:
            text_parts.append(script.description)
        
        # Add learning objectives
        for obj in script.learning_objectives:
            text_parts.append(obj.objective)
        
        # Add section content
        for section in script.sections:
            text_parts.append(section.title)
            text_parts.append(section.content)
        
        # Add assessment questions
        for assessment in script.assessments:
            text_parts.append(assessment.title)
            for question in assessment.questions:
                text_parts.append(question.question)
        
        # Add tags and prerequisites
        text_parts.extend(script.tags)
        text_parts.extend(script.prerequisites)
        
        return " ".join(text_parts)
    
    def reset_collections(self) -> bool:
        """
        Reset all collections (for testing purposes)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.delete_collection("educational_content")
            self.client.delete_collection("educational_scripts")
            
            # Recreate collections
            self.content_collection = self.client.create_collection(
                name="educational_content",
                metadata={"description": "Raw educational content embeddings"}
            )
            
            self.scripts_collection = self.client.create_collection(
                name="educational_scripts",
                metadata={"description": "Generated educational script embeddings"}
            )
            
            logger.info("Collections reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collections: {str(e)}")
            return False

# Global instance
vector_db_service = VectorDBService()