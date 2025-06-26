# app/schemas/user.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    role: UserRole
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    contact_full_name: Optional[str] = None
    tiktok_username: Optional[str] = None
    website: Optional[str] = None
    
    @validator('tiktok_username')
    def validate_tiktok_username(cls, v, values):
        """Remove @ symbol if present and validate"""
        if v:
            # Remove @ if user included it
            v = v.lstrip('@')
            # Basic validation - alphanumeric and underscores only
            if not v.replace('_', '').replace('.', '').isalnum():
                raise ValueError('TikTok username can only contain letters, numbers, underscores, and periods')
        return v
    
    @validator('website')
    def validate_website(cls, v):
        """Add https:// if not present"""
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str
    confirm_password: str
    accept_terms: bool = Field(..., description="User must accept terms")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate passwords match"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('accept_terms')
    def terms_accepted(cls, v):
        """Ensure terms are accepted"""
        if not v:
            raise ValueError('You must accept the terms and conditions')
        return v
    
    @validator('full_name', always=True)
    def validate_role_fields(cls, v, values):
        """Validate required fields based on role"""
        if 'role' in values:
            if values['role'] == UserRole.CREATOR:
                if not v:
                    raise ValueError('Full name is required for creators')
            elif values['role'] in [UserRole.AGENCY, UserRole.BRAND]:
                if not values.get('company_name'):
                    raise ValueError('Company name is required for agencies and brands')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    contact_full_name: Optional[str] = None
    tiktok_username: Optional[str] = None
    website: Optional[str] = None
    
    @validator('tiktok_username')
    def validate_tiktok_username(cls, v):
        if v:
            v = v.lstrip('@')
            if not v.replace('_', '').replace('.', '').isalnum():
                raise ValueError('Invalid TikTok username')
        return v


class UserResponse(BaseModel):
    """Schema for user responses"""
    id: UUID
    email: EmailStr
    role: UserRole
    full_name: Optional[str]
    company_name: Optional[str]
    contact_full_name: Optional[str]
    tiktok_username: Optional[str]
    website: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True