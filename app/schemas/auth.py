# app/schemas/auth.py
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from datetime import datetime

from app.schemas.user import UserCreate, UserResponse
from app.models.user import UserRole


class SignupRequest(UserCreate):
    """Schema for signup requests - extends UserCreate"""
    pass


class LoginRequest(BaseModel):
    """Schema for login requests"""
    email: EmailStr = Field(..., description="Email or username")  # Now accepts both
    password: str
    remember_me: bool = False
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "remember_me": True
            }
        }
    )


class AuthResponse(BaseModel):
    """Schema for authentication responses"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    message: Optional[str] = None
    requires_verification: bool = False  # Added for signup flow
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "role": "creator"
                },
                "message": "Login successful",
                "requires_verification": False
            }
        }
    )


class EmailVerificationRequest(BaseModel):
    """Schema for email verification"""
    token: str = Field(..., min_length=32, max_length=32)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "Abc123Def456Ghi789Jkl012Mno345Pq"
            }
        }
    )


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email"""
    email: EmailStr
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password requests"""
    email: EmailStr
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class ResetPasswordRequest(BaseModel):
    """Schema for password reset"""
    token: str = Field(..., min_length=32, max_length=32)
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Basic password strength validation"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "Rst789Uvw012Xyz345Abc678Def901Gh",
                "password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }
    )


class ChangePasswordRequest(BaseModel):
    """Schema for changing password when logged in"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    
    @field_validator('confirm_new_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('New passwords do not match')
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str, info) -> str:
        """Validate password strength and ensure it's different from current"""
        if 'current_password' in info.data and v == info.data['current_password']:
            raise ValueError('New password must be different from current password')
        
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePass456!",
                "confirm_new_password": "NewSecurePass456!"
            }
        }
    )


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True
    data: Optional[dict] = None  # Added for additional response data
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully",
                "success": True,
                "data": {}
            }
        }
    )


class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[str] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    token_type: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "exp": "2024-01-01T12:00:00Z",
                "iat": "2024-01-01T11:00:00Z",
                "token_type": "access"
            }
        }
    )


# Additional schemas for user management

class UsernameCheckRequest(BaseModel):
    """Request to check username availability"""
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_-]+$")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe123"
            }
        }
    )


class UsernameCheckResponse(BaseModel):
    """Response for username availability check"""
    available: bool
    username: Optional[str] = None
    reason: Optional[str] = None
    suggestions: Optional[List[str]] = []
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "available": False,
                "reason": "Username already taken",
                "suggestions": ["johndoe124", "johndoe_official", "real_johndoe"]
            }
        }
    )


class DeleteAccountRequest(BaseModel):
    """Request to delete user account"""
    password: str = Field(..., description="Current password for verification")
    reason: Optional[str] = Field(None, max_length=500, description="Optional reason for deletion")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "password": "MyCurrentPassword123!",
                "reason": "No longer using the service"
            }
        }
    )


class ProfileCompletionResponse(BaseModel):
    """Response for profile completion status"""
    percentage: int = Field(..., ge=0, le=100)
    is_complete: bool
    missing_required_fields: List[str] = []
    missing_optional_fields: List[str] = []
    next_steps: List[str] = []
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "percentage": 75,
                "is_complete": False,
                "missing_required_fields": ["phone"],
                "missing_optional_fields": ["bio", "profile_image"],
                "next_steps": ["Complete required fields: phone", "Add a profile picture to increase trust"]
            }
        }
    )