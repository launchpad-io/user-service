# app/schemas/auth.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator

from app.schemas.user import UserCreate, UserResponse
from app.models.user import UserRole


class SignupRequest(UserCreate):
    """Schema for signup requests - extends UserCreate"""
    pass


class LoginRequest(BaseModel):
    """Schema for login requests"""
    email: EmailStr
    password: str
    remember_me: bool = False


class AuthResponse(BaseModel):
    """Schema for authentication responses"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    message: Optional[str] = None


class EmailVerificationRequest(BaseModel):
    """Schema for email verification"""
    token: str = Field(..., min_length=32, max_length=32)


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password requests"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset"""
    token: str = Field(..., min_length=32, max_length=32)
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[str] = None