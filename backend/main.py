"""
Simple entry point for the Educational Content Generator backend.
This file provides a simple way to run the FastAPI application.
"""

import uvicorn
from app.main import app
from app.core.config import settings

def main():
    """Run the FastAPI application"""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    main()
