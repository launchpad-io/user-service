# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.auth import MessageResponse
from app.models.user import User, UserRole
from app.utils.dependencies import get_current_verified_user
from app.services.auth_service import auth_service

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
    
    # Generate new verification token
    from app.core.security import generate_verification_token
    verification_token, token_expires = generate_verification_token()
    
    current_user.verification_token = verification_token
    current_user.verification_token_expires = token_expires
    db.commit()
    
    # Send verification email
    from app.services.email_service import email_service
    display_name = current_user.full_name or current_user.company_name or "there"
    
    email_sent = email_service.send_verification_email(
        current_user.email,
        display_name,
        verification_token
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