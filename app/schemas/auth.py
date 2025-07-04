# Missing files that are likely causing the auth module import failures

# 1. app/schemas/auth.py - Create this file
# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import UserRole

class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    role: UserRole
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email_or_username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    remember_me: bool = False

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"
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

# Forward reference resolution
from app.schemas.user import UserResponse
AuthResponse.model_rebuild()


