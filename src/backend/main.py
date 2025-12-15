"""
Main FastAPI application entry point for the multi-agent market research system.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Multi-Agent Market Research System...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Gemini Model: {settings.gemini_model}")
    
    if settings.langsmith_api_key:
        logger.info("LangSmith observability enabled")
    
    # Ensure directories exist
    settings.create_directories()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="Multi-Agent Market Research System",
    description="Deep research market report generation using LangGraph and Google Gemini",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "online",
        "service": "Multi-Agent Market Research System",
        "version": "1.0.0",
        "environment": settings.app_env
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "gemini_configured": bool(settings.gemini_api_key),
        "langsmith_enabled": bool(settings.langsmith_api_key)
    }


# Import and include API routes
from api.routes import router as api_router
app.include_router(api_router, prefix="/api", tags=["api"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower()
    )

