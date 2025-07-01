# app/services/auth_service.py
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
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
from app.schemas.token import TokenValidationResponse
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_refresh_token,
    validate_password_strength, generate_token, create_token_pair
)
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class AuthService:
    """Enterprise-grade authentication service with token management"""
    
    # In app/services/auth_service.py, update the _create_token method:

    def _create_token(self, db: Session, user_id: str, token_type: TokenType, 
                         expires_hours: int = 24, metadata: Optional[Dict[str, Any]] = None) -> UserToken:
        """
        Create a new token for user
    
     Args:
            db: Database session
            user_id: User UUID
            token_type: Type of token
            expires_hours: Hours until expiration
            metadata: Optional token metadata (not used in simplified version)
        
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
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    
        user_token = UserToken(
            user_id=user_id,
            token_type=token_type,
            token_value=token_value,
            expires_at=expires_at,
            is_used=False
        # Removed: token_metadata, since it doesn't exist in DB
        )
    
        db.add(user_token)
        db.commit()
    
        return user_token
    
    def _generate_username(self, db: Session, email: str, role: UserRole, company_name: Optional[str] = None) -> str:
        """Generate unique username from email or company name"""
        base_username = email.split('@')[0].lower()
        
        # For brands/agencies, try to use company name
        if role in [UserRole.AGENCY, UserRole.BRAND] and company_name:
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
    
        # Get the role value - with the updated enum, this will already be lowercase
        role_value = signup_data.role

        # Debug to confirm
        logger.debug(f"Role value being inserted: {role_value}")
    
        # Generate username
        username = self._generate_username(
            db,
            signup_data.email, 
            UserRole(role_value),  # This will work now since enum values match
            getattr(signup_data, 'company_name', None)
        )
    
        # Create user based on role
        user_data = {
            "email": signup_data.email,
            "username": username,
            "hashed_password": get_password_hash(signup_data.password),
            "role": role_value,  # This will now be the correct lowercase value
            "is_active": True,
            "email_verified": False,
            "profile_completion_percentage": 30  # Basic signup complete
        }
    
        # Debug logging
        logger.debug(f"Creating user with role value: {role_value} (type: {type(role_value)})")
    
        # Add role-specific fields
        if role_value == UserRole.CREATOR:  # Compare with enum
            # Handle full_name for creators
            if hasattr(signup_data, 'full_name') and signup_data.full_name:
                name_parts = signup_data.full_name.strip().split(' ', 1)
                user_data["first_name"] = name_parts[0] if name_parts else None
                user_data["last_name"] = name_parts[1] if len(name_parts) > 1 else None
            else:
                # Use first_name and last_name directly if provided
                user_data["first_name"] = getattr(signup_data, 'first_name', None)
                user_data["last_name"] = getattr(signup_data, 'last_name', None)
        
            # Handle TikTok username/handle
            user_data["tiktok_handle"] = getattr(signup_data, 'tiktok_username', None) or getattr(signup_data, 'tiktok_handle', None)
        
        elif role_value in [UserRole.AGENCY, UserRole.BRAND]:  # Compare with enums
            user_data["company_name"] = getattr(signup_data, 'company_name', None)
        
            # Handle contact full name for agencies/brands
            if hasattr(signup_data, 'contact_full_name') and signup_data.contact_full_name:
                name_parts = signup_data.contact_full_name.strip().split(' ', 1)
                user_data["first_name"] = name_parts[0] if name_parts else None
                user_data["last_name"] = name_parts[1] if len(name_parts) > 1 else None
            else:
                user_data["first_name"] = getattr(signup_data, 'first_name', None)
                user_data["last_name"] = getattr(signup_data, 'last_name', None)
        
         # Handle website URL
            user_data["website_url"] = getattr(signup_data, 'website', None) or getattr(signup_data, 'website_url', None)
    
        # Rest of the m
        
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
    
    # In app/services/auth_service.py, update the login_with_refresh method:

    async def login_with_refresh(self, db: Session, login_data: LoginRequest, 
                            user_agent: str = "Unknown", ip_address: str = "Unknown") -> Tuple[User, str, str]:
        """
        Authenticate user and return both access and refresh tokens
        """
        # Perform standard login
        user, _ = self.login(db, login_data)
    
     # Create token pair
        access_token, refresh_token = create_token_pair(
            user_id=str(user.id),
            remember_me=login_data.remember_me,
            device_info={
                "user_agent": user_agent,
                "ip_address": ip_address,
                "login_time": datetime.now(timezone.utc).isoformat()
            }
        )      
    
        # Store refresh token in database (without metadata since column doesn't exist)
        self._create_token(
            db,
            str(user.id),
            TokenType.REFRESH,
            expires_hours=24 * 30  # 30 days
            # Removed: metadata parameter
        )
    
        return user, access_token, refresh_token
    
    async def refresh_access_token(self, db: Session, refresh_token: str, 
                                  rotate_refresh_token: bool = True) -> Tuple[str, Optional[str]]:
        """
        Refresh access token using refresh token
        """
        # Decode refresh token
        payload = decode_refresh_token(refresh_token)
        if not payload:
            raise ValueError("Invalid refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Get user
        user = self.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Create new access token
        new_access_token = create_access_token(subject=user_id)
        
        new_refresh_token = None
        if rotate_refresh_token:
            # Create new refresh token
            new_refresh_token = create_refresh_token(
                subject=user_id,
                device_info=payload.get("device", {})
            )
            
            # Invalidate old refresh token
            db.query(UserToken).filter(
                UserToken.user_id == user_id,
                UserToken.token_type == TokenType.REFRESH,
                UserToken.is_used == False
            ).update({"is_used": True})
            
            # Store new refresh token
            self._create_token(
                db,
                user_id,
                TokenType.REFRESH,
                expires_hours=24 * 30,
                metadata=payload.get("device", {})
            )
        
        return new_access_token, new_refresh_token
    
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
            user.role
        )
        
        logger.info(f"Email verified for user: {user.email}")
        return user
    
    async def resend_verification_email(self, db: Session, email: str) -> str:
        """Resend verification email"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal if email exists
            return "If your email is registered and unverified, you will receive a verification link."
        
        if user.email_verified:
            return "Email is already verified."
        
        # Create new verification token
        verification_token = self._create_token(
            db,
            str(user.id),
            TokenType.EMAIL_VERIFICATION,
            expires_hours=24
        )
        
        # Send verification email
        email_sent = email_service.send_verification_email(
            user.email,
            user.display_name,
            verification_token.token_value
        )
        
        if email_sent:
            return "Verification email sent successfully."
        else:
            raise Exception("Failed to send verification email.")
    
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
    
    async def validate_token(self, db: Session, token: str) -> TokenValidationResponse:
        """Validate an access token"""
        from app.core.security import decode_access_token
        
        payload = decode_access_token(token)
        if not payload:
            return TokenValidationResponse(valid=False)
        
        user_id = payload.get("sub")
        if not user_id:
            return TokenValidationResponse(valid=False)
        
        user = self.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            return TokenValidationResponse(valid=False)
        
        return TokenValidationResponse(
            valid=True,
            user_id=user_id,
            expires_at=payload.get("exp"),
            issued_at=payload.get("iat")
        )
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired tokens - should be run periodically"""
        expired_tokens = db.query(UserToken).filter(
            and_(
                UserToken.expires_at < datetime.now(timezone.utc),
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