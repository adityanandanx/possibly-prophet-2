"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # Basic app settings
    APP_NAME: str = "Educational Content Generator"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # AI Service Credentials (optional - will use fallbacks if not provided)
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    AWS_BEARER_TOKEN_BEDROCK: Optional[str] = None
    AWS_DEFAULT_REGION: str = "us-east-1"

    # S3 settings for video storage
    S3_BUCKET: str = "educational-presentations"
    S3_PREFIX: str = "presentations/"

    # AWS Bedrock Knowledge Base settings
    BEDROCK_KNOWLEDGE_BASE_ID: Optional[str] = None
    BEDROCK_DATA_SOURCE_ID: Optional[str] = None
    S3_KNOWLEDGE_BUCKET: str = "educational-knowledge-base"

    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
    ]

    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]

    # URL processing settings
    MAX_URL_CONTENT_SIZE: int = 5 * 1024 * 1024  # 5MB
    REQUEST_TIMEOUT: int = 30  # seconds
    USER_AGENT: str = "Educational Content Generator Bot 1.0"

    # Agent settings
    AGENT_TIMEOUT: int = 300  # 5 minutes
    MAX_CONCURRENT_AGENTS: int = 5

    # Database settings (for future use)
    DATABASE_URL: str = "sqlite:///./educational_content.db"

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
