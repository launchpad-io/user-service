# app/services/user_service.py
"""
Enterprise-grade user management service.
Handles profile management, username validation, and user operations.
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import UploadFile, HTTPException
import re
import hashlib
from PIL import Image
import io
import uuid

from app.models.user import User, UserRole
from app.models.user_token import UserToken, TokenType
from app.schemas.user import UserUpdate, UserProfileResponse
from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class UserService:
    """
    Service layer for user management operations.
    Implements business logic for user profiles, validation, and management.
    """
    
    # Username validation rules
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    RESERVED_USERNAMES = {
        'admin', 'api', 'app', 'auth', 'blog', 'config', 'dashboard',
        'help', 'home', 'launchpaid', 'login', 'logout', 'profile',
        'register', 'root', 'settings', 'signup', 'support', 'user',
        'users', 'www', 'mail', 'ftp', 'email', 'static', 'assets',
        'public', 'private', 'secure', 'about', 'contact', 'terms',
        'privacy', 'legal', 'docs', 'documentation', 'test', 'testing'
    }
    
    # Profile image constraints
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
    IMAGE_DIMENSIONS = (800, 800)  # Max dimensions
    THUMBNAIL_DIMENSIONS = (200, 200)
    
    def __init__(self):
        """Initialize user service with configuration."""
        self.storage_backend = settings.STORAGE_BACKEND  # 'local' or 's3'
        self.cdn_url = settings.CDN_URL if hasattr(settings, 'CDN_URL') else None
    
    def validate_username(self, db: Session, username: str, current_user_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate username according to business rules.
        
        Args:
            db: Database session
            username: Username to validate
            current_user_id: Current user's ID (for updates)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Convert to lowercase for consistency
        username_lower = username.lower()
        
        # Check pattern
        if not self.USERNAME_PATTERN.match(username):
            return False, "Username must be 3-30 characters and contain only letters, numbers, underscores, and hyphens"
        
        # Check reserved words
        if username_lower in self.RESERVED_USERNAMES:
            return False, "This username is reserved and cannot be used"
        
        # Check profanity filter (implement if needed)
        # if self._contains_profanity(username_lower):
        #     return False, "Username contains inappropriate content"
        
        # Check availability
        query = db.query(User).filter(func.lower(User.username) == username_lower)
        if current_user_id:
            query = query.filter(User.id != current_user_id)
        
        if query.first():
            return False, "Username is already taken"
        
        return True, None
    
    def check_username_availability(self, db: Session, username: str) -> Dict[str, Any]:
        """
        Check if username is available with suggestions if not.
        
        Args:
            db: Database session
            username: Username to check
            
        Returns:
            Dict with availability status and suggestions
        """
        is_valid, error = self.validate_username(db, username)
        
        result = {
            "username": username,
            "available": is_valid,
            "error": error,
            "suggestions": []
        }
        
        # Generate suggestions if username is taken
        if not is_valid and "already taken" in (error or ""):
            result["suggestions"] = self._generate_username_suggestions(db, username)
        
        return result
    
    def _generate_username_suggestions(self, db: Session, base_username: str, count: int = 5) -> List[str]:
        """Generate alternative username suggestions."""
        suggestions = []
        base = re.sub(r'[^a-zA-Z0-9]', '', base_username.lower())[:20]
        
        # Try different patterns
        patterns = [
            lambda i: f"{base}{i}",
            lambda i: f"{base}_{i}",
            lambda i: f"{base}{datetime.now().year}",
            lambda i: f"{base}_{datetime.now().year}_{i}",
            lambda i: f"real_{base}",
            lambda i: f"{base}_official",
            lambda i: f"the_{base}",
        ]
        
        for pattern in patterns:
            for i in range(1, 100):
                suggestion = pattern(i)
                if len(suggestions) >= count:
                    break
                
                # Check if suggestion is valid and available
                is_valid, _ = self.validate_username(db, suggestion)
                if is_valid:
                    suggestions.append(suggestion)
        
        return suggestions[:count]
    
    def get_user_profile(self, db: Session, user: User) -> UserProfileResponse:
        """
        Get complete user profile with calculated fields.
        
        Args:
            db: Database session
            user: User instance
            
        Returns:
            Complete user profile response
        """
        # Recalculate profile completion
        user.calculate_profile_completion()
        db.commit()
        
        # Load relationships if needed
        if user.role == UserRole.CREATOR:
            # Eager load creator-specific relationships
            db.refresh(user, ['audience_demographics', 'badges'])
        
        return UserProfileResponse.from_orm(user)
    
    def update_user_profile(self, db: Session, user: User, update_data: UserUpdate) -> User:
        """
        Update user profile with validation.
        
        Args:
            db: Database session
            user: User to update
            update_data: Update data
            
        Returns:
            Updated user
        """
        # Extract update dict excluding None values
        update_dict = update_data.dict(exclude_unset=True, exclude_none=True)
        
        # Handle username update separately
        if 'username' in update_dict:
            new_username = update_dict['username']
            is_valid, error = self.validate_username(db, new_username, str(user.id))
            if not is_valid:
                raise ValueError(f"Username validation failed: {error}")
        
        # Validate role-specific fields
        if user.role == UserRole.CREATOR:
            # Ensure creator fields are not removed
            if 'company_name' in update_dict:
                del update_dict['company_name']
            if 'tax_id' in update_dict:
                del update_dict['tax_id']
        elif user.role in [UserRole.AGENCY, UserRole.BRAND]:
            # Ensure business fields are not removed
            if 'tiktok_handle' in update_dict:
                del update_dict['tiktok_handle']
            if 'content_niche' in update_dict:
                del update_dict['content_niche']
        
        # Update fields
        for field, value in update_dict.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        # Update timestamps
        user.updated_at = datetime.now(timezone.utc)
        
        # Recalculate profile completion
        user.calculate_profile_completion()
        
        # Commit changes
        db.commit()
        db.refresh(user)
        
        logger.info(f"Updated profile for user {user.email}")
        return user
    
    def upload_profile_image(self, db: Session, user: User, file: UploadFile) -> str:
        """
        Upload and process user profile image.
        
        Args:
            db: Database session
            user: User uploading image
            file: Uploaded file
            
        Returns:
            URL of uploaded image
        """
        # Validate file type
        if file.content_type not in self.ALLOWED_IMAGE_TYPES:
            raise ValueError(f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_IMAGE_TYPES)}")
        
        # Check file size
        file_data = file.file.read()
        if len(file_data) > self.MAX_IMAGE_SIZE:
            raise ValueError(f"File too large. Maximum size: {self.MAX_IMAGE_SIZE / 1024 / 1024}MB")
        
        try:
            # Process image
            image = Image.open(io.BytesIO(file_data))
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            
            # Resize if needed
            image.thumbnail(self.IMAGE_DIMENSIONS, Image.Resampling.LANCZOS)
            
            # Generate filename
            file_ext = file.filename.split('.')[-1].lower()
            filename = f"profile_{user.id}_{uuid.uuid4().hex[:8]}.{file_ext}"
            
            # Save image (implement based on storage backend)
            image_url = self._save_image(image, filename, user.id)
            
            # Update user profile
            old_image = user.profile_image_url
            user.profile_image_url = image_url
            user.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            # Delete old image if exists
            if old_image:
                self._delete_image(old_image)
            
            logger.info(f"Uploaded profile image for user {user.email}")
            return image_url
            
        except Exception as e:
            logger.error(f"Error processing image for user {user.email}: {str(e)}")
            raise ValueError("Failed to process image. Please try again.")
    
    def _save_image(self, image: Image.Image, filename: str, user_id: str) -> str:
        """Save image to storage backend."""
        # This is a placeholder - implement based on your storage backend
        # For S3: Use boto3 to upload
        # For local: Save to disk
        # Return the URL
        
        if self.storage_backend == 'local':
            # Local storage implementation
            path = f"/uploads/profiles/{user_id}/{filename}"
            # Save image...
            return f"{settings.FRONTEND_URL}{path}"
        else:
            # S3 or other cloud storage
            # Upload to S3...
            return f"{self.cdn_url}/profiles/{user_id}/{filename}"
    
    def _delete_image(self, image_url: str) -> None:
        """Delete image from storage."""
        # Implement based on storage backend
        pass
    
    def delete_user_account(self, db: Session, user: User, password: str) -> None:
        """
        Soft delete user account after password verification.
        
        Args:
            db: Database session
            user: User to delete
            password: User's password for confirmation
        """
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise ValueError("Incorrect password")
        
        # Soft delete - mark as inactive
        user.is_active = False
        user.email = f"deleted_{user.id}_{user.email}"  # Prevent email reuse
        user.username = f"deleted_{user.id}_{user.username}"  # Prevent username reuse
        user.updated_at = datetime.now(timezone.utc)
        
        # Invalidate all tokens
        db.query(UserToken).filter(
            UserToken.user_id == user.id,
            UserToken.is_used == False
        ).update({"is_used": True})
        
        db.commit()
        
        # Send confirmation email
        # email_service.send_account_deletion_confirmation(original_email)
        
        logger.info(f"Soft deleted account for user {user.id}")
    
    def get_user_sessions(self, db: Session, user: User) -> List[Dict[str, Any]]:
        """
        Get active sessions for user.
        
        Args:
            db: Database session
            user: User
            
        Returns:
            List of active sessions
        """
        # Get active refresh tokens
        active_tokens = db.query(UserToken).filter(
            UserToken.user_id == user.id,
            UserToken.token_type == TokenType.REFRESH,
            UserToken.is_used == False,
            UserToken.expires_at > datetime.utcnow()
        ).all()
        
        sessions = []
        for token in active_tokens:
            # Parse metadata for session info
            metadata = {}
            if token.metadata:
                # Assuming metadata is JSON string with user agent, IP, etc.
                import json
                try:
                    metadata = json.loads(token.metadata)
                except:
                    pass
            
            sessions.append({
                "id": str(token.id),
                "created_at": token.created_at,
                "last_active": token.created_at,  # Could track last use
                "user_agent": metadata.get("user_agent", "Unknown"),
                "ip_address": metadata.get("ip_address", "Unknown"),
                "location": metadata.get("location", "Unknown"),
                "device": self._parse_device(metadata.get("user_agent", "")),
                "is_current": metadata.get("is_current", False)
            })
        
        return sorted(sessions, key=lambda x: x['created_at'], reverse=True)
    
    def _parse_device(self, user_agent: str) -> str:
        """Parse device type from user agent."""
        user_agent_lower = user_agent.lower()
        
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
            return "Mobile"
        elif 'ipad' in user_agent_lower or 'tablet' in user_agent_lower:
            return "Tablet"
        elif 'darwin' in user_agent_lower or 'mac' in user_agent_lower:
            return "Mac"
        elif 'windows' in user_agent_lower:
            return "Windows"
        elif 'linux' in user_agent_lower:
            return "Linux"
        else:
            return "Unknown"
    
    def revoke_all_sessions(self, db: Session, user: User, except_current: Optional[str] = None) -> int:
        """
        Revoke all user sessions except optionally the current one.
        
        Args:
            db: Database session
            user: User
            except_current: Current token ID to keep active
            
        Returns:
            Number of sessions revoked
        """
        query = db.query(UserToken).filter(
            UserToken.user_id == user.id,
            UserToken.token_type.in_([TokenType.REFRESH, TokenType.OAUTH]),
            UserToken.is_used == False
        )
        
        if except_current:
            query = query.filter(UserToken.id != except_current)
        
        count = query.count()
        query.update({"is_used": True})
        db.commit()
        
        logger.info(f"Revoked {count} sessions for user {user.email}")
        return count


# Create singleton instance
user_service = UserService()