# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    SignupRequest, LoginRequest, AuthResponse,
    EmailVerificationRequest, ForgotPasswordRequest,
    ResetPasswordRequest, MessageResponse
)
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Role-specific required fields:
    - Creator: full_name, tiktok_username
    - Agency/Brand: company_name
    """
    try:
        user, message = auth_service.signup(db, signup_data)
        
        # Create access token for immediate login (optional)
        # You might want to require email verification first
        access_token = ""  # Don't auto-login until email is verified
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user),
            message=message
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    Returns access token on success.
    """
    try:
        user, access_token = auth_service.login(db, login_data)
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user),
            message="Login successful"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address with token from email.
    """
    try:
        user = auth_service.verify_email(db, verification_data)
        return MessageResponse(
            message="Email verified successfully! You can now login.",
            success=True
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset link via email.
    """
    message = auth_service.request_password_reset(db, request_data)
    return MessageResponse(
        message=message,
        success=True
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password with token from email.
    """
    try:
        user = auth_service.reset_password(db, reset_data)
        return MessageResponse(
            message="Password reset successfully! You can now login with your new password.",
            success=True
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user.
    Note: With JWT, we just return success. 
    The client should remove the token.
    """
    return MessageResponse(
        message="Logged out successfully",
        success=True
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile.
    """
    return UserResponse.from_orm(current_user)