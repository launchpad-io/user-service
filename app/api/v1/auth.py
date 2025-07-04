# # user-service/app/api/v1/auth.py - Fixed to match frontend expectations

# from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
# from sqlalchemy.orm import Session
# from typing import Optional
# import logging

# from app.core.database import get_db
# from app.core.rate_limiter import (
#     login_limit, 
#     signup_limit, 
#     password_reset_limit, 
#     verify_email_limit,
#     api_limit
# )
# from app.schemas.auth import (
#     SignupRequest, LoginRequest, AuthResponse,
#     EmailVerificationRequest, ForgotPasswordRequest,
#     ResetPasswordRequest, MessageResponse,
#     ResendVerificationRequest, ChangePasswordRequest
# )
# from app.schemas.token import (
#     RefreshTokenRequest, RefreshTokenResponse, TokenPair,
#     TokenValidationResponse
# )
# from app.schemas.user import UserResponse
# from app.services.auth_service import auth_service
# from app.services.user_service import user_service
# from app.utils.dependencies import get_current_user, get_current_active_user
# from app.models.user import User
# from app.models.user_token import TokenType

# logger = logging.getLogger(__name__)

# router = APIRouter(tags=["Authentication"])


# def create_success_response(data, message: str = "Success"):
#     """Create standardized success response matching frontend expectations"""
#     return {
#         "success": True,
#         "data": data,
#         "message": message
#     }

# def create_error_response(error: str, message: str = "An error occurred"):
#     """Create standardized error response"""
#     return {
#         "success": False,
#         "error": error,
#         "message": message
#     }

# def format_user_for_response(user: User) -> dict:
#     """Format user object for frontend response"""
#     return {
#         "id": str(user.id),
#         "email": user.email,
#         "username": user.username,
#         "role": user.role.value,
#         "firstName": user.first_name,
#         "lastName": user.last_name,
#         "isActive": user.is_active,
#         "emailVerified": user.email_verified,
#         "createdAt": user.created_at.isoformat() if user.created_at else None,
#         "lastLogin": user.last_login.isoformat() if user.last_login else None
#     }


# # ADD THIS NEW ENDPOINT FOR FRONTEND COMPATIBILITY
# @router.post("/register")
# async def register(
#     request: Request,
#     response: Response,
#     signup_data: SignupRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Register endpoint matching frontend expectations
#     This is an alias for signup with consistent response format
#     """
#     try:
#         user, message = auth_service.signup(db, signup_data)
        
#         # For now, return empty tokens until email verification
#         # In production, you might want to auto-verify for testing
#         user_data = {
#             "user": format_user_for_response(user),
#             "access_token": "",  # Empty until verified
#             "refresh_token": ""
#         }
        
#         return create_success_response(user_data, message)
        
#     except ValueError as e:
#         logger.warning(f"Registration failed: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=create_error_response(str(e), "Registration failed")
#         )
#     except Exception as e:
#         logger.error(f"Registration error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=create_error_response("Internal server error", "Registration failed")
#         )


# @router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
# @signup_limit
# async def signup(
#     request: Request,
#     response: Response,
#     signup_data: SignupRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Original signup endpoint - keeping for compatibility
#     """
#     try:
#         user, message = auth_service.signup(db, signup_data)
        
#         return AuthResponse(
#             access_token="",  # No token until email verified
#             token_type="bearer",
#             user=UserResponse.model_validate(user),
#             message=message,
#             requires_verification=True
#         )
#     except ValueError as e:
#         logger.warning(f"Signup failed: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#     except Exception as e:
#         logger.error(f"Signup error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred during signup"
#         )


# @router.post("/login")
# @login_limit
# async def login(
#     request: Request,
#     response: Response,
#     login_data: LoginRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Login with email/username and password - Updated to match frontend expectations
#     """
#     try:
#         # Get user agent and IP for token metadata
#         user_agent = request.headers.get("User-Agent", "Unknown")
#         ip_address = request.client.host if request.client else "Unknown"
        
#         # Perform login with refresh token
#         user, access_token, refresh_token = await auth_service.login_with_refresh(
#             db, login_data, user_agent, ip_address
#         )
        
#         # Set refresh token as httpOnly cookie for security
#         if refresh_token:
#             response.set_cookie(
#                 key="refresh_token",
#                 value=refresh_token,
#                 httponly=True,
#                 secure=True,  # Use HTTPS in production
#                 samesite="strict",
#                 max_age=30 * 24 * 60 * 60  # 30 days
#             )
        
#         # Format response to match frontend expectations
#         user_data = {
#             "user": format_user_for_response(user),
#             "access_token": access_token,
#             "refresh_token": refresh_token
#         }
        
#         logger.info(f"Login successful for: {user.email}")
#         return create_success_response(user_data, "Login successful")
        
#     except ValueError as e:
#         logger.warning(f"Login failed: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=create_error_response("Invalid credentials", str(e))
#         )
#     except Exception as e:
#         logger.error(f"Login error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=create_error_response("Internal server error", "Login failed")
#         )


# # ADD PROFILE ENDPOINT FOR FRONTEND COMPATIBILITY  
# @router.get("/profile")
# async def get_profile(
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Get current user profile - matching frontend expectations
#     """
#     try:
#         user_data = format_user_for_response(current_user)
#         return create_success_response(user_data, "Profile retrieved successfully")
#     except Exception as e:
#         logger.error(f"Profile fetch error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=create_error_response("Internal server error", "Failed to get profile")
#         )


# @router.post("/refresh")
# async def refresh_access_token(
#     request: Request,
#     refresh_data: RefreshTokenRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Refresh access token using refresh token
#     """
#     try:
#         user_agent = request.headers.get("User-Agent", "Unknown")
#         ip_address = request.client.host if request.client else "Unknown"
        
#         user, new_access_token, new_refresh_token = await auth_service.refresh_access_token(
#             db, refresh_data.refresh_token, user_agent, ip_address
#         )
        
#         token_data = {
#             "access_token": new_access_token,
#             "refresh_token": new_refresh_token
#         }
        
#         return create_success_response(token_data, "Token refreshed successfully")
        
#     except ValueError as e:
#         logger.warning(f"Token refresh failed: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=create_error_response("Invalid token", str(e))
#         )
#     except Exception as e:
#         logger.error(f"Token refresh error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=create_error_response("Internal server error", "Token refresh failed")
#         )


# @router.post("/logout")
# async def logout(
#     response: Response,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
#     revoke_token: bool = True
# ):
#     """
#     Logout current user - matching frontend expectations
#     """
#     try:
#         # Clear refresh token cookie
#         response.delete_cookie(key="refresh_token")
        
#         if revoke_token:
#             # Could implement token revocation here if using a blacklist
#             pass
        
#         logger.info(f"User logged out: {current_user.email}")
        
#         return create_success_response({}, "Logged out successfully")
        
#     except Exception as e:
#         logger.error(f"Logout error: {str(e)}")
#         return create_success_response({}, "Logged out successfully")  # Always succeed for logout


# # Keep all your existing endpoints below this line...
# # (verify-email, resend-verification, forgot-password, etc.)

# @router.post("/verify-email", response_model=MessageResponse)
# @verify_email_limit  
# async def verify_email(
#     request: Request,
#     response: Response,
#     verification_data: EmailVerificationRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Verify email address with token from email.
    
#     Rate limit: 10 verification attempts per hour per IP
#     """
#     try:
#         user = auth_service.verify_email(db, verification_data.token)
        
#         logger.info(f"Email verified successfully for user: {user.email}")
        
#         return MessageResponse(
#             message="Email verified successfully! You can now login.",
#             success=True
#         )
#     except ValueError as e:
#         logger.warning(f"Email verification failed: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )


# @router.post("/resend-verification", response_model=MessageResponse)
# @verify_email_limit
# async def resend_verification(
#     request: Request,
#     response: Response,
#     resend_data: ResendVerificationRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Resend email verification link.
    
#     Rate limit: 3 requests per hour per IP
#     """
#     try:
#         message = await auth_service.resend_verification_email(db, resend_data.email)
        
#         return MessageResponse(
#             message=message,
#             success=True
#         )
#     except Exception as e:
#         logger.error(f"Resend verification error: {str(e)}")
#         # Always return success to prevent email enumeration
#         return MessageResponse(
#             message="If your email is registered and unverified, you will receive a verification link.",
#             success=True
#         )


# @router.post("/forgot-password", response_model=MessageResponse)
# @password_reset_limit
# async def forgot_password(
#     request: Request,
#     response: Response,
#     request_data: ForgotPasswordRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Request password reset link via email.
    
#     Rate limit: 3 requests per hour per IP
#     """
#     message = auth_service.request_password_reset(db, request_data)
    
#     return MessageResponse(
#         message=message,
#         success=True
#     )


# @router.post("/reset-password", response_model=MessageResponse)
# @password_reset_limit
# async def reset_password(
#     request: Request,
#     response: Response,
#     reset_data: ResetPasswordRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Reset password with token from email.
    
#     Rate limit: 3 attempts per hour per IP
#     """
#     try:
#         user = auth_service.reset_password(db, reset_data)
        
#         logger.info(f"Password reset successful for user: {user.email}")
        
#         return MessageResponse(
#             message="Password reset successfully! You can now login with your new password.",
#             success=True
#         )
#     except ValueError as e:
#         logger.warning(f"Password reset failed: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )


# @router.get("/me", response_model=UserResponse)
# async def get_current_user_profile(
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Get current user's basic profile.
#     """
#     return UserResponse.model_validate(current_user)

# app/api/v1/auth.py - Minimal version to get server running
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

# Simple request/response models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    username: str
    role: str = "creator"

class AuthResponse(BaseModel):
    success: bool
    data: dict
    message: str

@router.post("/login")
async def login(login_data: LoginRequest):
    """
    Login endpoint - temporary mock implementation
    """
    try:
        # Mock successful login
        if login_data.email == "test@example.com" and login_data.password == "password123":
            return AuthResponse(
                success=True,
                data={
                    "user": {
                        "id": "test-user-123",
                        "email": login_data.email,
                        "role": "creator",
                        "firstName": "Test",
                        "lastName": "User",
                        "isActive": True,
                        "emailVerified": True
                    },
                    "access_token": "mock-access-token-123",
                    "refresh_token": "mock-refresh-token-123"
                },
                message="Login successful"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error": "Invalid credentials",
                    "message": "Email or password is incorrect"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Internal server error",
                "message": "Login failed"
            }
        )

@router.post("/register")
async def register(register_data: RegisterRequest):
    """
    Register endpoint - temporary mock implementation
    """
    try:
        # Mock successful registration
        return AuthResponse(
            success=True,
            data={
                "user": {
                    "id": f"user-{hash(register_data.email) % 10000}",
                    "email": register_data.email,
                    "username": register_data.username,
                    "role": register_data.role,
                    "firstName": register_data.firstName,
                    "lastName": register_data.lastName,
                    "isActive": True,
                    "emailVerified": False  # Requires verification
                },
                "access_token": "",  # Empty until verified
                "refresh_token": ""
            },
            message="Registration successful. Please check your email for verification."
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Internal server error", 
                "message": "Registration failed"
            }
        )

@router.get("/dashboard/profile")
async def get_profile():
    """
    Get profile endpoint - temporary mock implementation
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "error": "Not authenticated",
            "message": "Authentication required"
        }
    )

@router.post("/logout")
async def logout():
    """
    Logout endpoint - temporary mock implementation
    """
    return AuthResponse(
        success=True,
        data={},
        message="Logout successful"
    )

@router.get("/test")
async def test_auth_endpoint():
    """Test endpoint to verify auth router is working"""
    return {"message": "Auth router is working!", "status": "success"}