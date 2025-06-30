# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.rate_limiter import api_limit
from app.schemas.user import UserResponse, UserUpdate, UsernameCheckRequest, UsernameCheckResponse
from app.schemas.auth import MessageResponse
from app.models.user import User, UserRole
from app.models.user_token import UserToken, TokenType
from app.utils.dependencies import get_current_verified_user, get_optional_current_user
from app.services.auth_service import auth_service
from app.services.user_service import user_service

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get current user's profile.
    Requires verified email.
    """
    return UserResponse.from_orm(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_update: UserUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    Only non-null fields will be updated.
    """
    # Check if TikTok username is being updated (for creators)
    if (current_user.role == UserRole.CREATOR and 
        profile_update.tiktok_username and 
        profile_update.tiktok_username != current_user.tiktok_username):
        
        # Check if new TikTok username already exists
        existing = db.query(User).filter(
            User.tiktok_username == profile_update.tiktok_username,
            User.id != current_user.id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TikTok username already taken"
            )
    
    # Update only provided fields
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        # Validate role-specific fields
        if field == "tiktok_username" and current_user.role != UserRole.CREATOR:
            continue  # Skip TikTok username for non-creators
        
        if field in ["company_name", "contact_full_name"] and current_user.role == UserRole.CREATOR:
            continue  # Skip company fields for creators
        
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)


@router.delete("/account", response_model=MessageResponse)
async def delete_account(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete user account.
    Sets is_active to False instead of removing from database.
    """
    current_user.is_active = False
    db.commit()
    
    return MessageResponse(
        message="Account deactivated successfully",
        success=True
    )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Resend email verification link.
    Only for unverified users.
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Use the new token system
    from app.services.auth_service import auth_service
    
    # Create verification token in user_tokens table
    verification_token = auth_service._create_token(
        db,
        str(current_user.id),
        TokenType.EMAIL_VERIFICATION,
        expires_hours=24
    )
    
    # Send verification email
    from app.services.email_service import email_service
    display_name = current_user.display_name
    
    email_sent = email_service.send_verification_email(
        current_user.email,
        display_name,
        verification_token.token_value
    )
    
    if email_sent:
        return MessageResponse(
            message="Verification email sent successfully",
            success=True
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post("/check-username", response_model=UsernameCheckResponse)
@api_limit
async def check_username_availability(
    request: UsernameCheckRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if a username is available.
    
    Returns availability status and suggestions if taken.
    Public endpoint but considers current user if authenticated.
    
    Rate limit: 100 requests per minute
    """
    result = await user_service.check_username_availability(
        db,
        request.username,
        current_user.id if current_user else None
    )
    
    return UsernameCheckResponse(**result)