"""
Input storage API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from app.models.content import (
    StoredInput, StoredInputMetadata, InputSearchRequest, InputListRequest,
    InputStorageStats, InputHistoryEntry, ContentType
)
from app.services.input_storage import input_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/input-storage", tags=["input-storage"])

@router.get("/search", response_model=List[StoredInput])
async def search_stored_inputs(
    query: str = Query(..., description="Search query text"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    generation_id: Optional[str] = Query(None, description="Filter by generation ID"),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100)
):
    """
    Search stored inputs using semantic search and filters
    """
    try:
        results = await input_storage_service.search_inputs(
            query=query,
            content_type=content_type,
            generation_id=generation_id,
            limit=limit
        )
        
        # Convert to response model
        stored_inputs = []
        for result in results:
            metadata = StoredInputMetadata(
                storage_id=result["storage_id"],
                content_type=ContentType(result["metadata"]["content_type"]),
                content_hash=result["metadata"]["content_hash"],
                stored_at=result["metadata"]["stored_at"],
                generation_id=result["metadata"].get("generation_id"),
                content_length=result["metadata"]["content_length"],
                validation_status=result["metadata"].get("validation_result", {}).get("is_valid"),
                processing_status=result["metadata"].get("processing_metadata", {}).get("status")
            )
            
            stored_input = StoredInput(
                storage_id=result["storage_id"],
                content=result["content"],
                metadata=metadata,
                similarity_score=result.get("similarity_score"),
                search_snippet=result.get("search_snippet")
            )
            stored_inputs.append(stored_input)
        
        return stored_inputs
        
    except Exception as e:
        logger.error(f"Error searching stored inputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/list", response_model=List[StoredInputMetadata])
async def list_stored_inputs(
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    generation_id: Optional[str] = Query(None, description="Filter by generation ID"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=200),
    offset: int = Query(0, description="Number of results to skip", ge=0)
):
    """
    List stored inputs with optional filters and pagination
    """
    try:
        results = await input_storage_service.list_inputs(
            content_type=content_type,
            generation_id=generation_id,
            limit=limit,
            offset=offset
        )
        
        # Convert to response model
        stored_inputs = []
        for result in results:
            metadata = StoredInputMetadata(
                storage_id=result["storage_id"],
                content_type=ContentType(result["content_type"]),
                content_hash=result["content_hash"],
                stored_at=result["stored_at"],
                generation_id=result.get("generation_id"),
                content_length=result["content_length"],
                validation_status=result.get("validation_status"),
                processing_status=result.get("processing_status")
            )
            stored_inputs.append(metadata)
        
        return stored_inputs
        
    except Exception as e:
        logger.error(f"Error listing stored inputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")

@router.get("/{storage_id}", response_model=StoredInput)
async def get_stored_input(storage_id: str):
    """
    Retrieve a specific stored input by ID
    """
    try:
        result = await input_storage_service.retrieve_input(storage_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Input not found: {storage_id}")
        
        # Convert to response model
        metadata = StoredInputMetadata(
            storage_id=storage_id,
            content_type=ContentType(result["metadata"]["content_type"]),
            content_hash=result["metadata"]["content_hash"],
            stored_at=result["metadata"]["stored_at"],
            generation_id=result["metadata"].get("generation_id"),
            content_length=result["metadata"]["content_length"],
            validation_status=result["metadata"].get("validation_result", {}).get("is_valid"),
            processing_status=result["metadata"].get("processing_metadata", {}).get("status")
        )
        
        stored_input = StoredInput(
            storage_id=storage_id,
            content=result["content"],
            metadata=metadata
        )
        
        return stored_input
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stored input {storage_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@router.get("/{storage_id}/history", response_model=List[InputHistoryEntry])
async def get_input_history(storage_id: str):
    """
    Get processing history for inputs with the same content hash
    """
    try:
        # First get the input to find its content hash
        stored_input = await input_storage_service.retrieve_input(storage_id)
        if not stored_input:
            raise HTTPException(status_code=404, detail=f"Input not found: {storage_id}")
        
        content_hash = stored_input["metadata"]["content_hash"]
        
        # Get history for this content hash
        history = await input_storage_service.get_input_history(content_hash)
        
        # Convert to response model
        history_entries = []
        for entry in history:
            history_entry = InputHistoryEntry(
                storage_id=entry["storage_id"],
                stored_at=entry["stored_at"],
                generation_id=entry.get("generation_id"),
                validation_result=entry.get("validation_result", {}),
                processing_metadata=entry.get("processing_metadata", {})
            )
            history_entries.append(history_entry)
        
        return history_entries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting input history for {storage_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

@router.delete("/{storage_id}")
async def delete_stored_input(storage_id: str):
    """
    Delete a stored input and its metadata
    """
    try:
        success = await input_storage_service.delete_input(storage_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Input not found or could not be deleted: {storage_id}")
        
        return {"message": f"Input {storage_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting stored input {storage_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@router.get("/stats/overview", response_model=InputStorageStats)
async def get_storage_statistics():
    """
    Get comprehensive storage statistics
    """
    try:
        stats = await input_storage_service.get_storage_stats()
        
        # Convert to response model
        storage_stats = InputStorageStats(
            total_inputs=stats["total_inputs"],
            content_type_distribution=stats["content_type_distribution"],
            total_content_size_bytes=stats["total_content_size_bytes"],
            total_content_size_mb=stats["total_content_size_mb"],
            vector_db_stats=stats["vector_db_stats"],
            file_storage_stats=stats["file_storage_stats"],
            storage_directory=stats["storage_directory"]
        )
        
        return storage_stats
        
    except Exception as e:
        logger.error(f"Error getting storage statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")

@router.post("/search", response_model=List[StoredInput])
async def search_stored_inputs_post(request: InputSearchRequest):
    """
    Search stored inputs using POST request (for complex queries)
    """
    try:
        results = await input_storage_service.search_inputs(
            query=request.query,
            content_type=request.content_type,
            generation_id=request.generation_id,
            limit=request.limit
        )
        
        # Convert to response model
        stored_inputs = []
        for result in results:
            metadata = StoredInputMetadata(
                storage_id=result["storage_id"],
                content_type=ContentType(result["metadata"]["content_type"]),
                content_hash=result["metadata"]["content_hash"],
                stored_at=result["metadata"]["stored_at"],
                generation_id=result["metadata"].get("generation_id"),
                content_length=result["metadata"]["content_length"],
                validation_status=result["metadata"].get("validation_result", {}).get("is_valid"),
                processing_status=result["metadata"].get("processing_metadata", {}).get("status")
            )
            
            stored_input = StoredInput(
                storage_id=result["storage_id"],
                content=result["content"],
                metadata=metadata,
                similarity_score=result.get("similarity_score"),
                search_snippet=result.get("search_snippet")
            )
            stored_inputs.append(stored_input)
        
        return stored_inputs
        
    except Exception as e:
        logger.error(f"Error searching stored inputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/list", response_model=List[StoredInputMetadata])
async def list_stored_inputs_post(request: InputListRequest):
    """
    List stored inputs using POST request (for complex filters)
    """
    try:
        results = await input_storage_service.list_inputs(
            content_type=request.content_type,
            generation_id=request.generation_id,
            limit=request.limit,
            offset=request.offset
        )
        
        # Convert to response model
        stored_inputs = []
        for result in results:
            metadata = StoredInputMetadata(
                storage_id=result["storage_id"],
                content_type=ContentType(result["content_type"]),
                content_hash=result["content_hash"],
                stored_at=result["stored_at"],
                generation_id=result.get("generation_id"),
                content_length=result["content_length"],
                validation_status=result.get("validation_status"),
                processing_status=result.get("processing_status")
            )
            stored_inputs.append(metadata)
        
        return stored_inputs
        
    except Exception as e:
        logger.error(f"Error listing stored inputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")