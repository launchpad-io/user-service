# app/services/auth_service.py
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

from app.models.user import User, UserRole
from app.schemas.auth import (
    SignupRequest, LoginRequest, ForgotPasswordRequest, 
    ResetPasswordRequest, EmailVerificationRequest
)
from app.schemas.user import UserResponse
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    generate_verification_token, generate_reset_token,
    validate_password_strength
)
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""
    
    def signup(self, db: Session, signup_data: SignupRequest) -> tuple[User, str]:
        """
        Register a new user.
        Returns: (user, verification_message)
        """
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == signup_data.email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Check if TikTok username already exists (for creators)
        if signup_data.role == UserRole.CREATOR and signup_data.tiktok_username:
            existing_tiktok = db.query(User).filter(
                User.tiktok_username == signup_data.tiktok_username
            ).first()
            if existing_tiktok:
                raise ValueError("TikTok username already registered")
        
        # Validate password strength
        is_valid, error_msg = validate_password_strength(signup_data.password)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Generate verification token
        verification_token, token_expires = generate_verification_token()
        
        # Create user based on role
        user_data = {
            "email": signup_data.email,
            "hashed_password": get_password_hash(signup_data.password),
            "role": signup_data.role,
            "verification_token": verification_token,
            "verification_token_expires": token_expires,
            "is_active": True,
            "is_verified": False
        }
        
        # Add role-specific fields
        if signup_data.role == UserRole.CREATOR:
            user_data["full_name"] = signup_data.full_name
            user_data["tiktok_username"] = signup_data.tiktok_username
        elif signup_data.role in [UserRole.AGENCY, UserRole.BRAND]:
            user_data["company_name"] = signup_data.company_name or signup_data.full_name
            user_data["contact_full_name"] = signup_data.contact_full_name
            user_data["website"] = signup_data.website
        
        # Create user
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send verification email
        display_name = user.full_name or user.company_name or "there"
        email_sent = email_service.send_verification_email(
            user.email, 
            display_name, 
            verification_token
        )
        
        if email_sent:
            message = "Account created successfully. Please check your email to verify your account."
        else:
            message = "Account created successfully. Verification email could not be sent."
        
        logger.info(f"New user registered: {user.email} ({user.role})")
        return user, message
    
    def login(self, db: Session, login_data: LoginRequest) -> tuple[User, str]:
        """
        Authenticate user and return access token.
        Returns: (user, access_token)
        """
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is deactivated. Please contact support.")
        
        # Check if email is verified
        if not user.is_verified:
            raise ValueError("Please verify your email before logging in.")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token = create_access_token(
            subject=str(user.id),
            remember_me=login_data.remember_me
        )
        
        logger.info(f"User logged in: {user.email}")
        return user, access_token
    
    def verify_email(self, db: Session, verification_data: EmailVerificationRequest) -> User:
        """
        Verify user's email address.
        Returns: verified user
        """
        # Find user by verification token
        user = db.query(User).filter(
            User.verification_token == verification_data.token
        ).first()
        
        if not user:
            raise ValueError("Invalid verification token")
        
        # Check if token is expired
        if user.verification_token_expires < datetime.utcnow():
            raise ValueError("Verification token has expired")
        
        # Check if already verified
        if user.is_verified:
            raise ValueError("Email already verified")
        
        # Verify user
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        db.commit()
        
        # Send welcome email
        display_name = user.full_name or user.company_name or "there"
        email_service.send_welcome_email(user.email, display_name, user.role.value)
        
        logger.info(f"Email verified for user: {user.email}")
        return user
    
    def request_password_reset(self, db: Session, request_data: ForgotPasswordRequest) -> str:
        """
        Generate password reset token and send email.
        Returns: success message
        """
        # Find user by email
        user = db.query(User).filter(User.email == request_data.email).first()
        
        if not user:
            # Don't reveal if email exists
            return "If your email is registered, you will receive a password reset link."
        
        # Generate reset token
        reset_token, token_expires = generate_reset_token()
        
        # Save token to user
        user.reset_token = reset_token
        user.reset_token_expires = token_expires
        db.commit()
        
        # Send reset email
        display_name = user.full_name or user.company_name or "there"
        email_service.send_password_reset_email(
            user.email, 
            display_name, 
            reset_token
        )
        
        logger.info(f"Password reset requested for: {user.email}")
        return "If your email is registered, you will receive a password reset link."
    
    def reset_password(self, db: Session, reset_data: ResetPasswordRequest) -> User:
        """
        Reset user's password with token.
        Returns: user with updated password
        """
        # Find user by reset token
        user = db.query(User).filter(
            User.reset_token == reset_data.token
        ).first()
        
        if not user:
            raise ValueError("Invalid reset token")
        
        # Check if token is expired
        if user.reset_token_expires < datetime.utcnow():
            raise ValueError("Reset token has expired")
        
        # Validate new password
        is_valid, error_msg = validate_password_strength(reset_data.password)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Update password
        user.hashed_password = get_password_hash(reset_data.password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        
        logger.info(f"Password reset for user: {user.email}")
        return user
    
    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()


# Create singleton instance
auth_service = AuthService()