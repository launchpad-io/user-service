# app/api/v1/auth.py - Fixed version
from fastapi import APIRouter, HTTPException, status, Depends, Body, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import logging
from typing import Optional
from uuid import UUID
import jwt

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    decode_refresh_token,
    decode_access_token,
    generate_verification_token,
    generate_token,
    SECRET_KEY,
    REFRESH_SECRET_KEY,
    ALGORITHM
)
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])

# Request/Response models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    username: str
    role: str = "creator"
    companyName: Optional[str] = None
    websiteUrl: Optional[str] = None
    tiktokHandle: Optional[str] = None
    contentNiche: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    data: dict
    message: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Dependency function for getting current user
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    # Extract token from header
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token = parts[1]
    
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user

@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login endpoint with JWT token generation"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error": "Invalid credentials",
                    "message": "Email or password is incorrect"
                }
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error": "Invalid credentials",
                    "message": "Email or password is incorrect"
                }
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": "Account inactive",
                    "message": "Your account has been deactivated"
                }
            )
        
        # Create JWT tokens with role using the updated function
        access_token, refresh_token = create_token_pair(
            user_id=str(user.id),
            remember_me=login_data.remember_me,
            user_role=user.role.value  # Pass the role here
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Return user data with JWT tokens
        return AuthResponse(
            success=True,
            data={
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "role": user.role.value,  # Convert enum to string
                    "firstName": user.first_name,
                    "lastName": user.last_name,
                    "isActive": user.is_active,
                    "emailVerified": user.email_verified,
                    "companyName": getattr(user, 'company_name', None),
                    "profileCompletion": user.profile_completion_percentage
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            },
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Internal server error",
                "message": "Login failed"
            }
        )

@router.get("/profile")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile - for frontend compatibility"""
    return {
        "success": True,
        "data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "role": current_user.role.value,
            "firstName": current_user.first_name,
            "lastName": current_user.last_name,
            "isActive": current_user.is_active,
            "emailVerified": current_user.email_verified,
            "companyName": getattr(current_user, 'company_name', None),
            "profileCompletion": current_user.profile_completion_percentage,
            "createdAt": current_user.created_at.isoformat() if current_user.created_at else None
        }
    }

@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        # Decode refresh token
        payload = decode_refresh_token(request.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error": "Invalid refresh token",
                    "message": "Please login again"
                }
            )
        
        # Get user
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error": "User not found",
                    "message": "Please login again"
                }
            )
        
        # Create new token pair with role
        new_access_token, new_refresh_token = create_token_pair(
            user_id=str(user.id),
            user_role=user.role.value
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Internal server error",
                "message": "Token refresh failed"
            }
        )

# Add other endpoints (register, logout, etc.) here...
@router.get("/test")
async def test_auth_endpoint():
    """Test endpoint to verify auth router is working"""
    return {"message": "Auth router is working!", "status": "success"}