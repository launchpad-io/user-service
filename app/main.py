# app/main.py - User Service Main Application
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

# Import configurations and dependencies
from app.core.config import settings
from app.core.database import engine, Base
from app.core.rate_limiter import add_rate_limiter
from app.core.exceptions import (
    CampaignServiceException, 
    campaign_service_exception_handler,
    general_exception_handler
)

# Import API routers
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("=" * 60)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Service: {settings.SERVICE_NAME}")
    logger.info(f"Port: {settings.SERVICE_PORT}")
    logger.info(f"Database: Connected")
    logger.info(f"CORS origins: {settings.BACKEND_CORS_ORIGINS}")
    logger.info(f"Rate limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    logger.info("=" * 60)
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("User Service shutting down...")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="User management and authentication service for LaunchPAID platform",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan
)

# Add rate limiter if enabled
if settings.RATE_LIMIT_ENABLED:
    app = add_rate_limiter(app)
    logger.info("Rate limiting middleware added")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(CampaignServiceException, campaign_service_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routers
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"]
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs": "/api/v1/docs",
        "environment": settings.ENVIRONMENT
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # You can add database connectivity check here
        return {
            "status": "healthy",
            "service": settings.SERVICE_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": settings.SERVICE_NAME,
                "error": str(e)
            }
        )

# Service info endpoint
@app.get("/api/v1/info")
async def service_info():
    """Get service information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "service": settings.SERVICE_NAME,
        "environment": settings.ENVIRONMENT,
        "port": settings.SERVICE_PORT,
        "features": {
            "authentication": True,
            "user_management": True,
            "email_verification": settings.MAIL_ENABLED if hasattr(settings, 'MAIL_ENABLED') else False,
            "rate_limiting": settings.RATE_LIMIT_ENABLED
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )