# # app/main.py - Fixed with better route debugging
# from fastapi import FastAPI, APIRouter
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# import logging

# # Import configurations
# from app.core.config import settings

# # Import rate limiter (with try/except for graceful fallback)
# try:
#     from app.core.rate_limiter import add_rate_limiter
#     RATE_LIMITER_AVAILABLE = True
# except ImportError:
#     RATE_LIMITER_AVAILABLE = False
#     logging.warning("Rate limiter not available - continuing without it")

# # Import API modules (with detailed error reporting)
# try:
#     from app.api.v1 import auth
#     AUTH_MODULE_AVAILABLE = True
#     logging.info("✅ Auth module imported successfully")
# except ImportError as e:
#     AUTH_MODULE_AVAILABLE = False
#     logging.error(f"❌ Failed to import auth module: {e}")

# try:
#     from app.api.v1 import users
#     USERS_MODULE_AVAILABLE = True
#     logging.info("✅ Users module imported successfully")
# except ImportError as e:
#     USERS_MODULE_AVAILABLE = False
#     logging.error(f"❌ Failed to import users module: {e}")

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )

# logger = logging.getLogger(__name__)

# # Create FastAPI app
# app = FastAPI(
#     title=settings.APP_NAME,
#     version=settings.APP_VERSION,
#     openapi_url="/api/openapi.json",
#     docs_url="/api/docs",
#     redoc_url="/api/redoc"
# )

# # Add rate limiter if available
# if RATE_LIMITER_AVAILABLE and settings.RATE_LIMIT_ENABLED:
#     app = add_rate_limiter(app)
#     logger.info("✅ Rate limiting enabled")
# else:
#     logger.warning("⚠️ Rate limiting disabled")

# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.BACKEND_CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Create API router and include routes with detailed logging
# api_router = APIRouter()

# # Add auth routes
# if AUTH_MODULE_AVAILABLE and hasattr(auth, 'router'):
#     try:
#         api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
#         logger.info("✅ Auth routes registered: /api/v1/auth/*")
        
#         # Log available auth routes
#         for route in auth.router.routes:
#             if hasattr(route, 'path') and hasattr(route, 'methods'):
#                 for method in route.methods:
#                     logger.info(f"   📍 {method} /api/v1/auth{route.path}")
#     except Exception as e:
#         logger.error(f"❌ Failed to register auth routes: {e}")
# else:
#     logger.error("❌ Auth router not available")

# # Add users routes
# if USERS_MODULE_AVAILABLE and hasattr(users, 'router'):
#     try:
#         api_router.include_router(users.router, prefix="/users", tags=["users"])
#         logger.info("✅ Users routes registered: /api/v1/users/*")
        
#         # Log available user routes
#         for route in users.router.routes:
#             if hasattr(route, 'path') and hasattr(route, 'methods'):
#                 for method in route.methods:
#                     logger.info(f"   📍 {method} /api/v1/users{route.path}")
#     except Exception as e:
#         logger.error(f"❌ Failed to register users routes: {e}")
# else:
#     logger.error("❌ Users router not available")

# # Include API router
# app.include_router(api_router, prefix="/api/v1")

# # Root endpoint
# @app.get("/")
# async def root():
#     return {
#         "message": "Welcome to LaunchPAID API",
#         "version": settings.APP_VERSION,
#         "service": settings.SERVICE_NAME,
#         "docs": "/api/docs",
#         "status": "running",
#         "available_modules": {
#             "auth": AUTH_MODULE_AVAILABLE,
#             "users": USERS_MODULE_AVAILABLE,
#             "rate_limiter": RATE_LIMITER_AVAILABLE
#         }
#     }

# # Health check endpoint
# @app.get("/health")
# async def health_check():
#     return {
#         "status": "healthy",
#         "service": settings.SERVICE_NAME,
#         "version": settings.APP_VERSION,
#         "environment": settings.ENVIRONMENT,
#         "modules": {
#             "auth": AUTH_MODULE_AVAILABLE,
#             "users": USERS_MODULE_AVAILABLE,
#             "rate_limiter": RATE_LIMITER_AVAILABLE
#         }
#     }

# # Debug endpoint to list all routes
# @app.get("/api/routes")
# async def list_routes():
#     """Debug endpoint to see all registered routes"""
#     routes = []
#     for route in app.routes:
#         if hasattr(route, 'path') and hasattr(route, 'methods'):
#             for method in route.methods:
#                 if method != "HEAD":  # Skip HEAD methods
#                     routes.append({
#                         "method": method,
#                         "path": route.path,
#                         "name": getattr(route, 'name', None)
#                     })
#     return {
#         "total_routes": len(routes),
#         "routes": sorted(routes, key=lambda x: x['path'])
#     }

# # Global exception handler
# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc):
#     logger.error(f"Global exception handler caught: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={
#             "detail": "Internal server error",
#             "success": False,
#             "service": settings.SERVICE_NAME
#         }
#     )

# # Startup event
# @app.on_event("startup")
# async def startup_event():
#     logger.info("=" * 50)
#     logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting up...")
#     logger.info(f"Service: {settings.SERVICE_NAME}")
#     logger.info(f"Environment: {settings.ENVIRONMENT}")
#     logger.info(f"Debug: {settings.DEBUG}")
#     logger.info(f"CORS origins: {settings.BACKEND_CORS_ORIGINS}")
#     logger.info("=" * 50)
    
#     # Summary of available features
#     logger.info("📋 Feature Status:")
#     logger.info(f"   Auth Module: {'✅' if AUTH_MODULE_AVAILABLE else '❌'}")
#     logger.info(f"   Users Module: {'✅' if USERS_MODULE_AVAILABLE else '❌'}")
#     logger.info(f"   Rate Limiting: {'✅' if RATE_LIMITER_AVAILABLE and settings.RATE_LIMIT_ENABLED else '❌'}")
#     logger.info("=" * 50)

# # Shutdown event
# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info(f"{settings.SERVICE_NAME} shutting down...")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=settings.SERVICE_PORT,
#         reload=settings.DEBUG
#     )

# app/main.py - Simple working version with direct auth endpoints
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import logging
import uuid
from datetime import datetime

# Import configurations
from app.core.config import settings
from app.core.database import get_db

# Import the email service
from app.services.email_service import email_service

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
# DIRECT PYDANTIC MODELS (inline)
# ==========================================

class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    firstName: str
    lastName: str
    role: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    message: str = None
    requires_verification: bool = False

class MessageResponse(BaseModel):
    message: str
    success: bool = True

# STORAGE
users_storage = []

# ==========================================
# DIRECT AUTH ENDPOINTS (no separate router)
# ==========================================
# ENDPOINTS
@app.post("/api/v1/auth/signup", response_model=AuthResponse)
async def signup(signup_data: SignupRequest):
    """Register a new user account with email verification"""
    logger.info(f"📝 Signup attempt for: {signup_data.email}")
    
    try:
        # Check if user already exists
        existing_user = next(
            (user for user in users_storage 
             if user["email"] == signup_data.email or user["username"] == signup_data.username), 
            None
        )
        
        if existing_user:
            logger.warning(f"❌ User already exists: {signup_data.email}")
            raise HTTPException(
                status_code=400,
                detail="User with this email or username already exists"
            )
        
        # Create new user - UNVERIFIED initially
        verification_token = str(uuid.uuid4())
        new_user = {
            "id": str(uuid.uuid4()),
            "email": signup_data.email,
            "username": signup_data.username,
            "password": "hashed_" + signup_data.password,  # Simple hash for demo
            "role": signup_data.role,
            "firstName": signup_data.firstName,
            "lastName": signup_data.lastName,
            "isActive": True,
            "emailVerified": False,  # Start as unverified
            "verificationToken": verification_token,
            "tokenExpiry": (datetime.utcnow() + timedelta(hours=24)).isoformat(),  # 24 hour expiry
            "createdAt": datetime.utcnow().isoformat()
        }
        
        # Store in memory/database
        users_storage.append(new_user)
        
        logger.info(f"✅ User created (UNVERIFIED): {new_user['email']}")
        
        # 🔑 SEND VERIFICATION EMAIL
        try:
            email_sent = email_service.send_verification_email(
                to_email=new_user["email"],
                username=new_user["firstName"] or new_user["username"],
                verification_token=verification_token,
                frontend_url=settings.FRONTEND_URL
            )
            
            if email_sent:
                logger.info(f"📧 Verification email sent to: {new_user['email']}")
                email_message = "Please check your email to verify your account."
            else:
                logger.error(f"❌ Failed to send verification email to: {new_user['email']}")
                email_message = f"Account created, but email failed to send. Your verification token is: {verification_token}"
        
        except Exception as e:
            logger.error(f"❌ Email service error: {str(e)}")
            email_message = f"Account created, but email failed to send. Your verification token is: {verification_token}"
        
        # Return response with NO access token and requires_verification: True
        return AuthResponse(
            access_token="",  # NO TOKEN until verified
            user={
                "id": new_user["id"],
                "email": new_user["email"],
                "username": new_user["username"],
                "role": new_user["role"],
                "firstName": new_user["firstName"],
                "lastName": new_user["lastName"],
                "isActive": new_user["isActive"],
                "emailVerified": new_user["emailVerified"]
            },
            message=email_message,
            requires_verification=True  # Tell frontend verification is required
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

@app.post("/api/v1/auth/login")
async def login():
    """Login endpoint - placeholder"""
    return {"message": "Login endpoint - not implemented yet"}

@app.get("/api/v1/auth/profile")
async def get_profile():
    """Profile endpoint - placeholder"""
    return {"message": "Profile endpoint - not implemented yet"}
@app.post("/api/v1/auth/verify-email")
async def verify_email(token: str):
    """Verify email with token"""
    logger.info(f"📧 Email verification attempt with token: {token[:8]}...")
    
    try:
        # Find user by verification token
        user = next(
            (u for u in users_storage 
             if u.get("verificationToken") == token), 
            None
        )
        
        if not user:
            logger.warning(f"❌ Invalid verification token")
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
        # Check if token is expired
        token_expiry = datetime.fromisoformat(user["tokenExpiry"])
        if datetime.utcnow() > token_expiry:
            logger.warning(f"❌ Expired verification token for: {user['email']}")
            raise HTTPException(status_code=400, detail="Verification token has expired")
        
        if user["emailVerified"]:
            logger.info(f"⚠️ Email already verified for: {user['email']}")
            raise HTTPException(status_code=400, detail="Email already verified")
        
        # Mark as verified
        user["emailVerified"] = True
        user["verificationToken"] = None  # Clear the token
        user["tokenExpiry"] = None
        
        logger.info(f"✅ Email verified successfully: {user['email']}")
        
        # Return access token after verification
        return {
            "success": True,
            "message": "Email verified successfully! Welcome to LaunchPAID!",
            "access_token": "token_" + user["id"],
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "role": user["role"],
                "firstName": user["firstName"],
                "lastName": user["lastName"],
                "isActive": user["isActive"],
                "emailVerified": user["emailVerified"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Email verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Email verification failed")

@app.get("/api/v1/auth/resend-verification")
async def resend_verification(email: str):
    """Resend verification email"""
    logger.info(f"📧 Resend verification request for: {email}")
    
    try:
        user = next((u for u in users_storage if u["email"] == email), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user["emailVerified"]:
            raise HTTPException(status_code=400, detail="Email already verified")
        
        # Generate new verification token
        new_token = str(uuid.uuid4())
        user["verificationToken"] = new_token
        user["tokenExpiry"] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        # Send email
        email_sent = email_service.send_verification_email(
            to_email=user["email"],
            username=user["firstName"] or user["username"],
            verification_token=new_token,
            frontend_url=settings.FRONTEND_URL
        )
        
        if email_sent:
            logger.info(f"📧 Verification email resent to: {email}")
            return {
                "success": True,
                "message": "Verification email resent! Check your inbox."
            }
        else:
            logger.error(f"❌ Failed to resend verification email to: {email}")
            return {
                "success": False,
                "message": f"Failed to send email. Your verification token is: {new_token}"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Resend verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resend verification email")

# ==========================================
# OTHER ENDPOINTS
# ==========================================

@app.get("/")
async def root():
    return {
        "message": "Welcome to LaunchPAID API",
        "version": settings.APP_VERSION,
        "service": settings.SERVICE_NAME,
        "users_count": len(users_storage),
        "docs": "/api/docs",
        "status": "running",
        "mode":"with_email_service",
        "email_configured": True
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
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
                        "path": route.path
                    })
    return {
        "total_routes": len(routes),
        "routes": sorted(routes, key=lambda x: x['path'])
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "success": False,
            "service": settings.SERVICE_NAME
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    logger.info(f"Service: {settings.SERVICE_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("🚀 Direct auth endpoints registered:")
    logger.info("   📍 POST /api/v1/auth/signup")
    logger.info("   📍 POST /api/v1/auth/login")
    logger.info("   📍 GET /api/v1/auth/profile")
    logger.info("=" * 50)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"{settings.SERVICE_NAME} shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )