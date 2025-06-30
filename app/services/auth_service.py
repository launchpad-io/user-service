# app/services/auth_service.py
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import logging
import secrets

from app.models.user import User, UserRole
from app.models.user_token import UserToken, TokenType
from app.schemas.auth import (
    SignupRequest, LoginRequest, ForgotPasswordRequest, 
    ResetPasswordRequest, EmailVerificationRequest
)
from app.schemas.user import UserResponse
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    validate_password_strength, generate_token
)
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class AuthService:
    """Enterprise-grade authentication service with token management"""
    
    def _create_token(self, db: Session, user_id: str, token_type: TokenType, 
                     expires_hours: int = 24) -> UserToken:
        """
        Create a new token for user
        
        Args:
            db: Database session
            user_id: User UUID
            token_type: Type of token
            expires_hours: Hours until expiration
            
        Returns:
            UserToken instance
        """
        # Invalidate any existing tokens of the same type
        existing_tokens = db.query(UserToken).filter(
            and_(
                UserToken.user_id == user_id,
                UserToken.token_type == token_type,
                UserToken.is_used == False
            )
        ).all()
        
        for token in existing_tokens:
            token.is_used = True
        
        # Create new token
        token_value = generate_token(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        user_token = UserToken(
            user_id=user_id,
            token_type=token_type,
            token_value=token_value,
            expires_at=expires_at,
            is_used=False
        )
        
        db.add(user_token)
        db.commit()
        
        return user_token
    
    def _generate_username(self, email: str, role: UserRole, company_name: Optional[str] = None) -> str:
        """Generate unique username from email or company name"""
        base_username = email.split('@')[0].lower()
        
        # For brands/agencies, try to use company name
        if role in [UserRole.BRAND, UserRole.AGENCY] and company_name:
            # Convert company name to username format
            base_username = ''.join(c.lower() if c.isalnum() else '_' for c in company_name)
            base_username = base_username.strip('_')[:50]  # Limit length
        
        # Ensure username is unique
        username = base_username
        counter = 1
        
        while True:
            existing = db.query(User).filter(User.username == username).first()
            if not existing:
                break
            username = f"{base_username}{counter}"
            counter += 1
            
        return username
    
    def signup(self, db: Session, signup_data: SignupRequest) -> Tuple[User, str]:
        """
        Register a new user with enhanced profile fields
        Returns: (user, verification_message)
        """
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == signup_data.email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Validate password strength
        is_valid, error_msg = validate_password_strength(signup_data.password)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Generate username
        username = self._generate_username(
            signup_data.email, 
            signup_data.role,
            getattr(signup_data, 'company_name', None)
        )
        
        # Create user based on role
        user_data = {
            "email": signup_data.email,
            "username": username,
            "hashed_password": get_password_hash(signup_data.password),
            "role": signup_data.role,
            "is_active": True,
            "email_verified": False,
            "profile_completion_percentage": 30  # Basic signup complete
        }
        
        # Add role-specific fields
        if signup_data.role == UserRole.CREATOR:
            # Split full_name into first and last
            name_parts = (signup_data.full_name or "").strip().split(' ', 1)
            user_data["first_name"] = name_parts[0] if name_parts else None
            user_data["last_name"] = name_parts[1] if len(name_parts) > 1 else None
            user_data["tiktok_handle"] = signup_data.tiktok_username
            
        elif signup_data.role in [UserRole.AGENCY, UserRole.BRAND]:
            user_data["company_name"] = signup_data.company_name
            if signup_data.contact_full_name:
                name_parts = signup_data.contact_full_name.strip().split(' ', 1)
                user_data["first_name"] = name_parts[0] if name_parts else None
                user_data["last_name"] = name_parts[1] if len(name_parts) > 1 else None
            user_data["website_url"] = signup_data.website
        
        # Create user
        user = User(**user_data)
        db.add(user)
        db.flush()  # Get user ID without committing
        
        # Create verification token
        verification_token = self._create_token(
            db, 
            str(user.id), 
            TokenType.EMAIL_VERIFICATION,
            expires_hours=24
        )
        
        db.commit()
        db.refresh(user)
        
        # Send verification email
        display_name = user.display_name
        email_sent = email_service.send_verification_email(
            user.email, 
            display_name, 
            verification_token.token_value
        )
        
        if email_sent:
            message = "Account created successfully. Please check your email to verify your account."
        else:
            message = "Account created successfully. Verification email could not be sent."
        
        logger.info(f"New user registered: {user.email} ({user.role}) with username: {user.username}")
        return user, message
    
    def login(self, db: Session, login_data: LoginRequest) -> Tuple[User, str]:
        """
        Authenticate user and return access token
        Supports login with email or username
        """
        # Find user by email or username
        user = db.query(User).filter(
            or_(
                User.email == login_data.email,
                User.username == login_data.email  # Allow username login
            )
        ).first()
        
        if not user:
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is deactivated. Please contact support.")
        
        # Check if email is verified
        if not user.email_verified:
            raise ValueError("Please verify your email before logging in.")
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        # Create access token
        access_token = create_access_token(
            subject=str(user.id),
            remember_me=login_data.remember_me
        )
        
        logger.info(f"User logged in: {user.email}")
        return user, access_token
    
    def verify_email(self, db: Session, verification_data: EmailVerificationRequest) -> User:
        """Verify user's email address using token"""
        # Find token
        token = db.query(UserToken).filter(
            and_(
                UserToken.token_value == verification_data.token,
                UserToken.token_type == TokenType.EMAIL_VERIFICATION,
                UserToken.is_used == False
            )
        ).first()
        
        if not token:
            raise ValueError("Invalid verification token")
        
        # Check if token is expired
        if token.is_expired:
            raise ValueError("Verification token has expired")
        
        # Get user
        user = token.user
        
        # Check if already verified
        if user.email_verified:
            raise ValueError("Email already verified")
        
        # Verify user
        user.email_verified = True
        user.profile_completion_percentage = max(user.profile_completion_percentage, 40)
        token.is_used = True
        
        db.commit()
        
        # Send welcome email
        email_service.send_welcome_email(
            user.email, 
            user.display_name, 
            user.role.value
        )
        
        logger.info(f"Email verified for user: {user.email}")
        return user
    
    def request_password_reset(self, db: Session, request_data: ForgotPasswordRequest) -> str:
        """Generate password reset token and send email"""
        # Find user by email
        user = db.query(User).filter(User.email == request_data.email).first()
        
        if not user:
            # Don't reveal if email exists
            return "If your email is registered, you will receive a password reset link."
        
        # Create reset token
        reset_token = self._create_token(
            db,
            str(user.id),
            TokenType.PASSWORD_RESET,
            expires_hours=1
        )
        
        # Send reset email
        email_service.send_password_reset_email(
            user.email, 
            user.display_name, 
            reset_token.token_value
        )
        
        logger.info(f"Password reset requested for: {user.email}")
        return "If your email is registered, you will receive a password reset link."
    
    def reset_password(self, db: Session, reset_data: ResetPasswordRequest) -> User:
        """Reset user's password with token"""
        # Find token
        token = db.query(UserToken).filter(
            and_(
                UserToken.token_value == reset_data.token,
                UserToken.token_type == TokenType.PASSWORD_RESET,
                UserToken.is_used == False
            )
        ).first()
        
        if not token:
            raise ValueError("Invalid reset token")
        
        # Check if token is expired
        if token.is_expired:
            raise ValueError("Reset token has expired")
        
        # Get user
        user = token.user
        
        # Validate new password
        is_valid, error_msg = validate_password_strength(reset_data.password)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Update password
        user.hashed_password = get_password_hash(reset_data.password)
        token.is_used = True
        
        # Invalidate all user tokens for security
        db.query(UserToken).filter(
            and_(
                UserToken.user_id == user.id,
                UserToken.is_used == False
            )
        ).update({"is_used": True})
        
        db.commit()
        
        logger.info(f"Password reset for user: {user.email}")
        return user
    
    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get user by ID with eager loading"""
        return db.query(User).filter(User.id == user_id).first()
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired tokens - should be run periodically"""
        expired_tokens = db.query(UserToken).filter(
            and_(
                UserToken.expires_at < datetime.utcnow(),
                UserToken.is_used == False
            )
        ).all()
        
        count = len(expired_tokens)
        for token in expired_tokens:
            token.is_used = True
        
        db.commit()
        logger.info(f"Cleaned up {count} expired tokens")
        return count


# Create singleton instance
auth_service = AuthService()