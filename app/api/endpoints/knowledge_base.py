"""
API endpoints for AWS Bedrock Knowledge Base operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging

from app.services.aws_knowledge_base import (
    AWSKnowledgeBaseService,
    get_knowledge_base_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# Request/Response Models
class AddDocumentRequest(BaseModel):
    """Request model for adding a document to the Knowledge Base."""

    document_id: str
    content: str
    metadata: Dict[str, Any] = {}
    content_type: str = "educational_content"


class RetrieveRequest(BaseModel):
    """Request model for retrieving documents."""

    query: str
    max_results: int = 5
    filters: Optional[Dict[str, Any]] = None


class RetrieveAndGenerateRequest(BaseModel):
    """Request model for RAG queries."""

    query: str
    model_id: str = "amazon.nova-premier-v1:0"
    max_results: int = 5
    system_prompt: Optional[str] = None


# Dependency
def get_kb_service() -> AWSKnowledgeBaseService:
    """Dependency to get Knowledge Base service instance."""
    return get_knowledge_base_service()


# Endpoints
@router.post("/documents")
async def add_document(
    request: AddDocumentRequest,
    kb_service: AWSKnowledgeBaseService = Depends(get_kb_service),
):
    """
    Add a document to the AWS Bedrock Knowledge Base.

    The document is uploaded to S3 and will be ingested into the Knowledge Base
    when sync_data_source is called.
    """
    try:
        result = await kb_service.add_document(
            document_id=request.document_id,
            content=request.content,
            metadata=request.metadata,
            content_type=request.content_type,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_data_source(
    kb_service: AWSKnowledgeBaseService = Depends(get_kb_service),
):
    """
    Start an ingestion job to sync documents from S3 into the Knowledge Base.

    This should be called after adding new documents to trigger ingestion.
    """
    try:
        result = await kb_service.sync_data_source()

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error syncing data source: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/{job_id}")
async def get_sync_status(
    job_id: str,
    kb_service: AWSKnowledgeBaseService = Depends(get_kb_service),
):
    """
    Get the status of an ingestion job.
    """
    try:
        result = await kb_service.get_ingestion_job_status(job_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve")
async def retrieve_documents(
    request: RetrieveRequest,
    kb_service: AWSKnowledgeBaseService = Depends(get_kb_service),
):
    """
    Retrieve relevant documents from the Knowledge Base using semantic search.
    """
    try:
        result = await kb_service.retrieve(
            query=request.query,
            max_results=request.max_results,
            filters=request.filters,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag")
async def retrieve_and_generate(
    request: RetrieveAndGenerateRequest,
    kb_service: AWSKnowledgeBaseService = Depends(get_kb_service),
):
    """
    Retrieve relevant documents and generate a response using RAG.

    This combines retrieval from the Knowledge Base with generation
    using a foundation model for question answering over your documents.
    """
    try:
        result = await kb_service.retrieve_and_generate(
            query=request.query,
            model_id=request.model_id,
            max_results=request.max_results,
            system_prompt=request.system_prompt,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    content_type: str = "educational_content",
    kb_service: AWSKnowledgeBaseService = Depends(get_kb_service),
):
    """
    Delete a document from the Knowledge Base S3 bucket.

    The document will be removed from the Knowledge Base on the next sync.
    """
    try:
        result = await kb_service.delete_document(
            document_id=document_id,
            content_type=content_type,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(
    content_type: Optional[str] = None,
    kb_service: AWSKnowledgeBaseService = Depends(get_kb_service),
):
    """
    List documents in the Knowledge Base S3 bucket.
    """
    try:
        result = await kb_service.list_documents(content_type=content_type)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_knowledge_base_info(
    kb_service: AWSKnowledgeBaseService = Depends(get_kb_service),
):
    """
    Get information about the Knowledge Base.
    """
    try:
        result = kb_service.get_knowledge_base_info()

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error getting KB info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
