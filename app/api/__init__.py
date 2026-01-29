"""
API routes for Educational Content Generator
"""

from fastapi import APIRouter
from .endpoints import content, health, input_storage

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(input_storage.router, tags=["input-storage"])