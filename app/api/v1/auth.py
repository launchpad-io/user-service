# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.core.rate_limiter import (
    login_limit, 
    signup_limit, 
    password_reset_limit, 
    verify_email_limit,
    api_limit
)
from app.schemas.auth import (
    SignupRequest, LoginRequest, AuthResponse,
    EmailVerificationRequest, ForgotPasswordRequest,
    ResetPasswordRequest, MessageResponse,
    ResendVerificationRequest, ChangePasswordRequest
)
from app.schemas.token import (
    RefreshTokenRequest, RefreshTokenResponse, TokenPair,
    TokenValidationResponse
)
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.utils.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from app.models.user_token import TokenType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@signup_limit
async def signup(
    request: Request,
    signup_data: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Rate limit: 3 signups per hour per IP
    
    Returns access token only after email verification.
    """
    try:
        user, message = auth_service.signup(db, signup_data)
        
        return AuthResponse(
            access_token="",  # No token until email verified
            token_type="bearer",
            user=UserResponse.from_orm(user),
            message=message,
            requires_verification=True
        )
    except ValueError as e:
        logger.warning(f"Signup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during signup"
        )


@router.post("/login", response_model=TokenPair)
@login_limit
async def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login with email/username and password.
    
    Rate limit: 5 attempts per minute per IP
    
    Returns both access and refresh tokens.
    Sets refresh token as httpOnly cookie for security.
    """
    try:
        user, access_token, refresh_token = await auth_service.login_with_refresh(
            db, 
            login_data,
            user_agent=request.headers.get("user-agent", "Unknown"),
            ip_address=request.client.host
        )
        
        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Only over HTTPS in production
            samesite="lax",
            max_age=30 * 24 * 60 * 60  # 30 days
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=900  # 15 minutes
        )
    except ValueError as e:
        logger.warning(f"Login failed for {login_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
@api_limit
async def refresh_token(
    request: Request,
    refresh_request: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Accepts refresh token from either:
    1. Request body (for mobile apps)
    2. Cookie (for web apps)
    
    Optionally rotates refresh token for additional security.
    """
    # Get refresh token from body or cookie
    refresh_token = None
    if refresh_request and refresh_request.refresh_token:
        refresh_token = refresh_request.refresh_token
    else:
        refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    try:
        access_token, new_refresh_token = await auth_service.refresh_access_token(
            db,
            refresh_token,
            rotate_refresh_token=True  # Security best practice
        )
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_in=900,  # 15 minutes
            refresh_token=new_refresh_token  # New refresh token if rotated
        )
    except ValueError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/verify-email", response_model=MessageResponse)
@verify_email_limit
async def verify_email(
    request: Request,
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address with token from email.
    
    Rate limit: 10 attempts per hour per IP
    """
    try:
        user = auth_service.verify_email(db, verification_data)
        
        logger.info(f"Email verified for user: {user.email}")
        
        return MessageResponse(
            message="Email verified successfully! You can now login.",
            success=True
        )
    except ValueError as e:
        logger.warning(f"Email verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/resend-verification", response_model=MessageResponse)
@password_reset_limit  # Use same limit as password reset
async def resend_verification(
    request: Request,
    resend_data: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Resend email verification link.
    
    Rate limit: 3 requests per hour per IP
    """
    try:
        message = await auth_service.resend_verification_email(db, resend_data.email)
        
        return MessageResponse(
            message=message,
            success=True
        )
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        # Always return success to prevent email enumeration
        return MessageResponse(
            message="If your email is registered and unverified, you will receive a verification link.",
            success=True
        )


@router.post("/forgot-password", response_model=MessageResponse)
@password_reset_limit
async def forgot_password(
    request: Request,
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset link via email.
    
    Rate limit: 3 requests per hour per IP
    """
    message = auth_service.request_password_reset(db, request_data)
    
    return MessageResponse(
        message=message,
        success=True
    )


@router.post("/reset-password", response_model=MessageResponse)
@password_reset_limit
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password with token from email.
    
    Rate limit: 3 attempts per hour per IP
    """
    try:
        user = auth_service.reset_password(db, reset_data)
        
        logger.info(f"Password reset successful for user: {user.email}")
        
        return MessageResponse(
            message="Password reset successfully! You can now login with your new password.",
            success=True
        )
    except ValueError as e:
        logger.warning(f"Password reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user.
    
    Requires current password verification.
    Invalidates all existing sessions for security.
    """
    try:
        success = await user_service.change_password(
            db,
            current_user.id,
            change_data.current_password,
            change_data.new_password
        )
        
        if success:
            logger.info(f"Password changed for user: {current_user.email}")
            return MessageResponse(
                message="Password changed successfully. Please login again with your new password.",
                success=True
            )
    except ValueError as e:
        logger.warning(f"Password change failed for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    revoke_token: bool = True
):
    """
    Logout current user.
    
    - Clears refresh token cookie
    - Optionally revokes the current token
    """
    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")
    
    if revoke_token:
        # Could implement token revocation here if using a blacklist
        pass
    
    logger.info(f"User logged out: {current_user.email}")
    
    return MessageResponse(
        message="Logged out successfully",
        success=True
    )


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout from all devices/sessions.
    
    Revokes all refresh tokens and active sessions.
    """
    revoked_count = await user_service.revoke_all_sessions(db, current_user.id)
    
    logger.info(f"All sessions revoked for user: {current_user.email} (count: {revoked_count})")
    
    return MessageResponse(
        message=f"Successfully logged out from {revoked_count} device(s)",
        success=True
    )


@router.post("/validate-token", response_model=TokenValidationResponse)
async def validate_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Validate an access token.
    
    Useful for service-to-service authentication or token introspection.
    """
    try:
        validation_result = await auth_service.validate_token(db, token)
        return validation_result
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return TokenValidationResponse(valid=False)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's basic profile.
    
    For detailed profile, use /users/profile endpoint.
    """
    return UserResponse.from_orm(current_user)