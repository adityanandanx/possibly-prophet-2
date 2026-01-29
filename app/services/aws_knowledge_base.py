"""
AWS Bedrock Knowledge Base service for storing and retrieving educational content.

This service uses Amazon Bedrock Knowledge Bases for RAG (Retrieval Augmented Generation)
to store educational content and retrieve relevant context for content generation.
"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, List, Optional
import logging
import json
import uuid
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class AWSKnowledgeBaseService:
    """
    Service for managing AWS Bedrock Knowledge Base operations.

    This service provides:
    - Document ingestion into Knowledge Base
    - Semantic search/retrieval from Knowledge Base
    - Knowledge base management operations
    """

    def __init__(
        self,
        knowledge_base_id: Optional[str] = None,
        data_source_id: Optional[str] = None,
        s3_bucket: Optional[str] = None,
    ):
        """
        Initialize AWS Knowledge Base service.

        Args:
            knowledge_base_id: ID of the Bedrock Knowledge Base
            data_source_id: ID of the data source within the Knowledge Base
            s3_bucket: S3 bucket for document storage (data source)
        """
        self.knowledge_base_id = knowledge_base_id or settings.BEDROCK_KNOWLEDGE_BASE_ID
        self.data_source_id = data_source_id or settings.BEDROCK_DATA_SOURCE_ID
        self.s3_bucket = s3_bucket or settings.S3_KNOWLEDGE_BUCKET
        self.s3_prefix = "knowledge-base-documents/"

        # Initialize AWS clients
        self._bedrock_agent_client = None
        self._bedrock_agent_runtime_client = None
        self._s3_client = None

        logger.info(
            f"Initialized AWSKnowledgeBaseService with KB: {self.knowledge_base_id}"
        )

    @property
    def bedrock_agent_client(self):
        """Lazy initialization of Bedrock Agent client (for management operations)."""
        if self._bedrock_agent_client is None:
            self._bedrock_agent_client = boto3.client(
                "bedrock-agent",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                aws_session_token=settings.AWS_SESSION_TOKEN,
                region_name=settings.AWS_DEFAULT_REGION,
            )
        return self._bedrock_agent_client

    @property
    def bedrock_agent_runtime_client(self):
        """Lazy initialization of Bedrock Agent Runtime client (for queries)."""
        if self._bedrock_agent_runtime_client is None:
            self._bedrock_agent_runtime_client = boto3.client(
                "bedrock-agent-runtime",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                aws_session_token=settings.AWS_SESSION_TOKEN,
                region_name=settings.AWS_DEFAULT_REGION,
            )
        return self._bedrock_agent_runtime_client

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

    async def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any],
        content_type: str = "educational_content",
    ) -> Dict[str, Any]:
        """
        Add a document to the Knowledge Base via S3.

        The document is first uploaded to S3, then the data source is synced
        to ingest the document into the Knowledge Base.

        Args:
            document_id: Unique identifier for the document
            content: Text content of the document
            metadata: Additional metadata about the document
            content_type: Type of content (educational_content, script, etc.)

        Returns:
            Dictionary with upload status and document info
        """
        try:
            # Prepare document with metadata
            document = {
                "id": document_id,
                "content": content,
                "metadata": {
                    **metadata,
                    "content_type": content_type,
                    "created_at": datetime.now().isoformat(),
                },
            }

            # Create S3 key for the document
            s3_key = f"{self.s3_prefix}{content_type}/{document_id}.json"

            # Upload document to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json.dumps(document, indent=2),
                ContentType="application/json",
                Metadata={
                    "document-id": document_id,
                    "content-type": content_type,
                },
            )

            logger.info(
                f"Uploaded document {document_id} to s3://{self.s3_bucket}/{s3_key}"
            )

            return {
                "success": True,
                "document_id": document_id,
                "s3_key": s3_key,
                "s3_uri": f"s3://{self.s3_bucket}/{s3_key}",
                "message": "Document uploaded. Run sync_data_source() to ingest into Knowledge Base.",
            }

        except ClientError as e:
            logger.error(f"Failed to upload document to S3: {str(e)}")
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e),
            }

    async def sync_data_source(self) -> Dict[str, Any]:
        """
        Start a sync job to ingest documents from S3 into the Knowledge Base.

        This should be called after adding new documents to trigger ingestion.

        Returns:
            Dictionary with sync job status
        """
        try:
            response = self.bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=self.knowledge_base_id,
                dataSourceId=self.data_source_id,
            )

            ingestion_job = response.get("ingestionJob", {})

            logger.info(f"Started ingestion job: {ingestion_job.get('ingestionJobId')}")

            return {
                "success": True,
                "ingestion_job_id": ingestion_job.get("ingestionJobId"),
                "status": ingestion_job.get("status"),
                "started_at": ingestion_job.get("startedAt"),
            }

        except ClientError as e:
            logger.error(f"Failed to start ingestion job: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_ingestion_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of an ingestion job.

        Args:
            job_id: The ingestion job ID

        Returns:
            Dictionary with job status details
        """
        try:
            response = self.bedrock_agent_client.get_ingestion_job(
                knowledgeBaseId=self.knowledge_base_id,
                dataSourceId=self.data_source_id,
                ingestionJobId=job_id,
            )

            job = response.get("ingestionJob", {})

            return {
                "success": True,
                "job_id": job_id,
                "status": job.get("status"),
                "statistics": job.get("statistics", {}),
                "started_at": job.get("startedAt"),
                "updated_at": job.get("updatedAt"),
            }

        except ClientError as e:
            logger.error(f"Failed to get ingestion job status: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def retrieve(
        self,
        query: str,
        max_results: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant documents from the Knowledge Base.

        Args:
            query: The search query
            max_results: Maximum number of results to return
            filters: Optional filters to apply to the search

        Returns:
            Dictionary with retrieved documents and relevance scores
        """
        try:
            # Build retrieval configuration
            retrieval_config = {
                "vectorSearchConfiguration": {
                    "numberOfResults": max_results,
                }
            }

            # Add filters if provided
            if filters:
                retrieval_config["vectorSearchConfiguration"]["filter"] = filters

            response = self.bedrock_agent_runtime_client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={"text": query},
                retrievalConfiguration=retrieval_config,
            )

            # Process results
            results = []
            for result in response.get("retrievalResults", []):
                results.append(
                    {
                        "content": result.get("content", {}).get("text", ""),
                        "score": result.get("score", 0),
                        "location": result.get("location", {}),
                        "metadata": result.get("metadata", {}),
                    }
                )

            logger.info(f"Retrieved {len(results)} results for query: {query[:50]}...")

            return {
                "success": True,
                "query": query,
                "results": results,
                "result_count": len(results),
            }

        except ClientError as e:
            logger.error(f"Failed to retrieve from Knowledge Base: {str(e)}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": [],
            }

    async def retrieve_and_generate(
        self,
        query: str,
        model_id: str = "amazon.nova-premier-v1:0",
        max_results: int = 5,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant documents and generate a response using RAG.

        This combines retrieval from the Knowledge Base with generation
        using a foundation model.

        Args:
            query: The user's question or prompt
            model_id: The Bedrock model ID to use for generation
            max_results: Maximum number of documents to retrieve
            system_prompt: Optional system prompt for the model

        Returns:
            Dictionary with generated response and source citations
        """
        try:
            # Build the request
            request_params = {
                "input": {"text": query},
                "retrieveAndGenerateConfiguration": {
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.knowledge_base_id,
                        "modelArn": f"arn:aws:bedrock:{settings.AWS_DEFAULT_REGION}::foundation-model/{model_id}",
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": max_results,
                            }
                        },
                    },
                },
            }

            # Add system prompt if provided
            if system_prompt:
                request_params["retrieveAndGenerateConfiguration"][
                    "knowledgeBaseConfiguration"
                ]["generationConfiguration"] = {
                    "promptTemplate": {
                        "textPromptTemplate": system_prompt
                        + "\n\nContext: $search_results$\n\nQuestion: $query$"
                    }
                }

            response = self.bedrock_agent_runtime_client.retrieve_and_generate(
                **request_params
            )

            # Extract response and citations
            output = response.get("output", {})
            citations = response.get("citations", [])

            # Process citations
            processed_citations = []
            for citation in citations:
                for ref in citation.get("retrievedReferences", []):
                    processed_citations.append(
                        {
                            "content": ref.get("content", {}).get("text", ""),
                            "location": ref.get("location", {}),
                            "metadata": ref.get("metadata", {}),
                        }
                    )

            logger.info(f"Generated response with {len(processed_citations)} citations")

            return {
                "success": True,
                "response": output.get("text", ""),
                "citations": processed_citations,
                "session_id": response.get("sessionId"),
            }

        except ClientError as e:
            logger.error(f"Failed to retrieve and generate: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "",
                "citations": [],
            }

    async def delete_document(
        self, document_id: str, content_type: str = "educational_content"
    ) -> Dict[str, Any]:
        """
        Delete a document from S3 (will be removed from KB on next sync).

        Args:
            document_id: The document ID to delete
            content_type: The content type folder

        Returns:
            Dictionary with deletion status
        """
        try:
            s3_key = f"{self.s3_prefix}{content_type}/{document_id}.json"

            self.s3_client.delete_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
            )

            logger.info(f"Deleted document {document_id} from S3")

            return {
                "success": True,
                "document_id": document_id,
                "message": "Document deleted. Run sync_data_source() to update Knowledge Base.",
            }

        except ClientError as e:
            logger.error(f"Failed to delete document: {str(e)}")
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e),
            }

    async def list_documents(
        self, content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List documents in the Knowledge Base S3 bucket.

        Args:
            content_type: Optional filter by content type

        Returns:
            Dictionary with list of documents
        """
        try:
            prefix = self.s3_prefix
            if content_type:
                prefix = f"{self.s3_prefix}{content_type}/"

            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix,
            )

            documents = []
            for obj in response.get("Contents", []):
                documents.append(
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                    }
                )

            return {
                "success": True,
                "documents": documents,
                "count": len(documents),
            }

        except ClientError as e:
            logger.error(f"Failed to list documents: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "documents": [],
            }

    def get_knowledge_base_info(self) -> Dict[str, Any]:
        """
        Get information about the Knowledge Base.

        Returns:
            Dictionary with Knowledge Base details
        """
        try:
            response = self.bedrock_agent_client.get_knowledge_base(
                knowledgeBaseId=self.knowledge_base_id
            )

            kb = response.get("knowledgeBase", {})

            return {
                "success": True,
                "knowledge_base_id": kb.get("knowledgeBaseId"),
                "name": kb.get("name"),
                "description": kb.get("description"),
                "status": kb.get("status"),
                "created_at": kb.get("createdAt"),
                "updated_at": kb.get("updatedAt"),
            }

        except ClientError as e:
            logger.error(f"Failed to get Knowledge Base info: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }


# Create a singleton instance
knowledge_base_service: Optional[AWSKnowledgeBaseService] = None


def get_knowledge_base_service() -> AWSKnowledgeBaseService:
    """Get or create the Knowledge Base service singleton."""
    global knowledge_base_service
    if knowledge_base_service is None:
        knowledge_base_service = AWSKnowledgeBaseService()
    return knowledge_base_service
