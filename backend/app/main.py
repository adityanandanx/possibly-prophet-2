"""
Main FastAPI application for Educational Content Generator
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .api import api_router
from .core.config import settings
import logging
import time
import traceback

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL), format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Create FastAPI application
app = FastAPI(
    title="Educational Content Generator API",
    description="AI-powered educational content generation system built with Strands Agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information"""
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")

        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)

        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {str(e)} - {process_time:.3f}s")
        raise


# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error",
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Request validation failed",
                "type": "validation_error",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "server_error",
            }
        },
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount media files (for generated videos)
import os

# Media is inside the backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
media_path = os.path.join(backend_dir, "media")
if os.path.exists(media_path):
    app.mount("/media", StaticFiles(directory=media_path), name="media")
    logger.info(f"Mounted media directory: {media_path}")
else:
    logger.warning(f"Media directory not found: {media_path}")


@app.get("/")
async def root(request: Request):
    """Root endpoint - serve the frontend"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/demo")
async def demo_page(request: Request):
    """Demo page with pre-loaded examples"""
    return templates.TemplateResponse("demo.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.APP_NAME, "version": "1.0.0"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Allowed origins: {settings.ALLOWED_ORIGINS}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info(f"Shutting down {settings.APP_NAME}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
