"""
Health check endpoints
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "Educational Content Generator"}

@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with system information"""
    return {
        "status": "healthy",
        "service": "Educational Content Generator",
        "components": {
            "api": "healthy",
            "agents": "healthy",
            "database": "not_configured"
        }
    }