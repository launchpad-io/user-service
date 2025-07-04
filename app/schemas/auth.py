# user-service/app/schemas/auth.py - Updated to match frontend expectations

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from datetime import datetime

from app.schemas.user import UserCreate, UserResponse
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    """Schema for frontend registration requests - matches frontend useAuth.ts"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    firstName: str = Field(..., min_length=1, max_length=100)
    lastName: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=30)
    role: str = Field(default="creator", pattern="^(creator|agency|brand)$")
    
    # Optional fields that frontend might send
    phone: Optional[str] = None
    tiktokHandle: Optional[str] = None
    instagramHandle: Optional[str] = None
    contentNiche: Optional[str] = None
    companyName: Optional[str] = None
    websiteUrl: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john@example.com",
                "password": "securepassword123",
                "firstName": "John",
                "lastName": "Doe", 
                "username": "johndoe",
                "role": "creator",
                "tiktokHandle": "@johndoe",
                "contentNiche": "fitness"
            }
        }
    )


class SignupRequest(UserCreate):
    """Schema for signup requests - extends UserCreate (keeping original)"""
    pass


class LoginRequest(BaseModel):
    """Schema for login requests"""
    email: EmailStr = Field(..., description="Email or username")
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


class FrontendAuthResponse(BaseModel):
    """Schema matching frontend expectations for auth responses"""
    success: bool
    data: dict  # Contains user, access_token, refresh_token
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "user": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "user@example.com",
                        "username": "johndoe",
                        "role": "creator",
                        "firstName": "John",
                        "lastName": "Doe",
                        "isActive": True,
                        "emailVerified": True
                    },
                    "access_token": "eyJhbGciOiJIUzI1NiIs...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
                },
                "message": "Login successful"
            }
        }
    )


class AuthResponse(BaseModel):
    """Schema for authentication responses (original - keep for compatibility)"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    message: Optional[str] = None
    requires_verification: bool = False
    
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


class FrontendUserResponse(BaseModel):
    """User response format matching frontend expectations"""
    id: str
    email: str
    username: str
    role: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    isActive: bool = True
    emailVerified: bool = False
    createdAt: Optional[str] = None
    lastLogin: Optional[str] = None
    
    # Additional fields from your schema
    phone: Optional[str] = None
    profileImageUrl: Optional[str] = None
    bio: Optional[str] = None
    
    # Address fields
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    
    # Social media
    tiktokHandle: Optional[str] = None
    instagramHandle: Optional[str] = None
    
    # Creator specific
    contentNiche: Optional[str] = None
    followerCount: Optional[int] = None
    
    # Agency/Brand specific  
    companyName: Optional[str] = None
    websiteUrl: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john@example.com",
                "username": "johndoe",
                "role": "creator",
                "firstName": "John",
                "lastName": "Doe",
                "isActive": True,
                "emailVerified": True,
                "tiktokHandle": "@johndoe",
                "contentNiche": "fitness"
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
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "Abc123Def456Ghi789Jkl012Mno345Pq",
                "password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }
    )


class ChangePasswordRequest(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    
    @field_validator('confirm_new_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('New passwords do not match')
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
    data: Optional[dict] = None
    
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


# Standard response wrapper matching your frontend API client expectations
class StandardResponse(BaseModel):
    """Standard API response format"""
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {"key": "value"},
                "message": "Operation successful"
            }
        }
    )