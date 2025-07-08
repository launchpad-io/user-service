# app/main.py - Clean version without mock auth endpoints
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

# Import configurations
from app.core.config import settings
from app.core.database import get_db, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# INCLUDE ROUTERS FIRST
# ==========================================
try:
    from app.api.v1.auth import router as auth_router
    from app.api.v1.users import router as users_router
    
    # Include the routers BEFORE any other endpoints
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
    
    logger.info("✅ API routers included successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import API routers: {e}")
    logger.warning("Running without JWT authentication")

# ==========================================
# UTILITY ENDPOINTS ONLY
# ==========================================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Welcome to LaunchPAID User Service API",
        "version": settings.APP_VERSION,
        "service": settings.SERVICE_NAME,
        "docs": "/api/docs",
        "status": "running",
        "endpoints": {
            "auth": "/api/v1/auth/*",
            "users": "/api/v1/users/*",
            "health": "/health",
            "routes": "/api/routes"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected"  # Could add actual DB health check
    }

@app.get("/api/routes")
async def list_routes():
    """Debug endpoint to see all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            for method in route.methods:
                if method != "HEAD":
                    routes.append({
                        "method": method,
                        "path": route.path,
                        "name": getattr(route, 'name', 'N/A'),
                        "tags": getattr(route, 'tags', [])
                    })
    return {
        "total_routes": len(routes),
        "routes": sorted(routes, key=lambda x: x['path']),
        "auth_endpoints": [r for r in routes if r['path'].startswith('/api/v1/auth')],
        "user_endpoints": [r for r in routes if r['path'].startswith('/api/v1/users')]
    }

# ==========================================
# DEVELOPMENT/TESTING ENDPOINTS
# ==========================================

@app.get("/api/v1/auth/test-verify/{email}")
async def test_verify_user(email: str, db: Session = Depends(get_db)):
    """TEST ENDPOINT - Auto verify a user for development"""
    from app.models.user import User
    
    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=404, 
            detail="This endpoint is only available in development"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.email_verified = True
        db.commit()
        logger.info(f"🧪 TEST: Auto-verified user {email}")
        return {
            "message": f"User {email} verified successfully", 
            "success": True
        }
    return {
        "message": "User not found", 
        "success": False
    }

@app.get("/api/v1/debug/user/{user_id}")
async def debug_user_info(user_id: str, db: Session = Depends(get_db)):
    """DEBUG ENDPOINT - Get user info for development"""
    from app.models.user import User
    
    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=404, 
            detail="This endpoint is only available in development"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    return {"message": "User not found"}

# Add this endpoint to your main.py for development
@app.post("/api/v1/debug/reset-password")
async def reset_user_password(email: str, new_password: str, db: Session = Depends(get_db)):
    """DEBUG: Reset user password to use proper bcrypt - DEVELOPMENT ONLY"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=404, detail="Not available in production")
    
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return {"message": f"Password reset for {email}", "success": True}
    return {"message": "User not found", "success": False}


# Add this to your campaign service main.py or auth router

@app.post("/api/v1/auth/refresh")
async def refresh_token_proxy(refresh_data: dict):
    """Proxy refresh token requests to user service"""
    import requests
    
    try:
        # Forward refresh request to user service
        response = requests.post(
            "http://localhost:8000/api/v1/auth/refresh",
            json=refresh_data,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Token refresh failed"
            )
            
    except requests.RequestException:
        raise HTTPException(
            status_code=503,
            detail="User service unavailable"
        )

# ==========================================
# EXCEPTION HANDLERS
# ==========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Global exception handler caught: {exc}")
    logger.error(f"Request: {request.method} {request.url}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "success": False,
            "service": settings.SERVICE_NAME,
            "error_type": type(exc).__name__
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Endpoint not found: {request.method} {request.url.path}",
            "success": False,
            "service": settings.SERVICE_NAME,
            "available_endpoints": "/api/routes"
        }
    )

# ==========================================
# STARTUP/SHUTDOWN EVENTS
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    logger.info(f"📋 Service: {settings.SERVICE_NAME}")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔗 Host: {settings.SERVICE_HOST}:{settings.SERVICE_PORT}")
    logger.info(f"📚 Docs: http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT}/api/docs")
    logger.info("=" * 60)
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise e

    # Log available endpoints
    logger.info("📍 Available endpoints:")
    logger.info("   🔐 Auth: /api/v1/auth/* (login, register, etc.)")
    logger.info("   👥 Users: /api/v1/users/* (profile, etc.)")
    logger.info("   ⚕️  Health: /health")
    logger.info("   🗺️  Routes: /api/routes")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info(f"🛑 {settings.SERVICE_NAME} shutting down...")
    logger.info("👋 Goodbye!")

# ==========================================
# DEV SERVER
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🔧 Starting development server...")
    logger.info(f"📡 Server will be available at: http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT}")
    logger.info(f"📖 API docs at: http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT}/api/docs")
    
    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )