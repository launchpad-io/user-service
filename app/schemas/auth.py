# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.user import UserRole

class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8)
    firstName: str = Field(..., min_length=1, max_length=50)
    lastName: str = Field(..., min_length=1, max_length=50)
    role: UserRole
    phone: Optional[str] = None
    
    # Role-specific fields
    # For creators
    tiktok_handle: Optional[str] = None
    content_niche: Optional[str] = None
    
    # For agencies/brands
    company_name: Optional[str] = None
    website_url: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]  # Simplified for now
    message: Optional[str] = None
    requires_verification: bool = False

class MessageResponse(BaseModel):
    message: str
    success: bool = True

class EmailVerificationRequest(BaseModel):
    token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class UsernameCheckRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)

class UsernameCheckResponse(BaseModel):
    available: bool
    username: str
    reason: Optional[str] = None
    suggestions: Optional[list[str]] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Also add any other missing schemas that might be needed
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None