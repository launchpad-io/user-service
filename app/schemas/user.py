# app/schemas/user.py
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from uuid import UUID

from app.models.user import UserRole, GenderType


class AddressBase(BaseModel):
    """Base schema for address information"""
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(default="US", max_length=100)


class SocialHandlesBase(BaseModel):
    """Base schema for social media handles"""
    tiktok_handle: Optional[str] = Field(None, max_length=100)
    discord_handle: Optional[str] = Field(None, max_length=100)
    instagram_handle: Optional[str] = Field(None, max_length=100)
    
    @validator('tiktok_handle', 'instagram_handle')
    def validate_social_handle(cls, v):
        """Remove @ symbol and validate format"""
        if v:
            v = v.lstrip('@').strip()
            if not v.replace('_', '').replace('.', '').isalnum():
                raise ValueError('Handle can only contain letters, numbers, underscores, and periods')
        return v


class CreatorMetricsBase(BaseModel):
    """Base schema for creator metrics"""
    content_niche: Optional[str] = Field(None, max_length=100)
    follower_count: Optional[int] = Field(default=0, ge=0)
    average_views: Optional[int] = Field(default=0, ge=0)
    engagement_rate: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=100, regex="^[a-zA-Z0-9_-]+$")
    role: UserRole
    
    # Personal information
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, regex="^\\+?[1-9]\\d{1,14}$")  # E.164 format
    date_of_birth: Optional[date] = None
    gender: Optional[GenderType] = None
    bio: Optional[str] = Field(None, max_length=500)
    
    # Business information
    company_name: Optional[str] = Field(None, max_length=200)
    website_url: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    
    @validator('website_url')
    def validate_website(cls, v):
        """Add https:// if not present"""
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v
    
    @property
    def full_name(self) -> Optional[str]:
        """Computed full name property"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name


class UserCreate(UserBase, SocialHandlesBase):
    """Schema for creating a new user - used in signup"""
    password: str = Field(..., min_length=8)
    confirm_password: str
    accept_terms: bool = Field(..., description="User must accept terms")
    
    # For backward compatibility
    full_name: Optional[str] = None
    tiktok_username: Optional[str] = None  # Alias for tiktok_handle
    contact_full_name: Optional[str] = None  # For agencies/brands
    website: Optional[str] = None  # Alias for website_url
    
    @root_validator(pre=True)
    def handle_legacy_fields(cls, values):
        """Handle legacy field names for backward compatibility"""
        # Handle full_name splitting
        if values.get('full_name') and not values.get('first_name'):
            name_parts = values['full_name'].strip().split(' ', 1)
            values['first_name'] = name_parts[0] if name_parts else None
            values['last_name'] = name_parts[1] if len(name_parts) > 1 else None
        
        # Handle contact_full_name for agencies/brands
        if values.get('contact_full_name') and not values.get('first_name'):
            name_parts = values['contact_full_name'].strip().split(' ', 1)
            values['first_name'] = name_parts[0] if name_parts else None
            values['last_name'] = name_parts[1] if len(name_parts) > 1 else None
        
        # Map old field names to new ones
        if values.get('tiktok_username'):
            values['tiktok_handle'] = values['tiktok_username']
        if values.get('website'):
            values['website_url'] = values['website']
            
        return values
    
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
    
    @root_validator
    def validate_role_fields(cls, values):
        """Validate required fields based on role"""
        role = values.get('role')
        
        if role == UserRole.CREATOR:
            if not values.get('first_name'):
                raise ValueError('First name is required for creators')
            if not values.get('tiktok_handle') and not values.get('tiktok_username'):
                raise ValueError('TikTok handle is required for creators')
                
        elif role in [UserRole.AGENCY, UserRole.BRAND]:
            if not values.get('company_name'):
                raise ValueError('Company name is required for agencies and brands')
                
        return values


class UserUpdate(UserBase, AddressBase, SocialHandlesBase, CreatorMetricsBase):
    """Schema for updating user profile"""
    email: Optional[EmailStr] = None  # Email can't be updated directly
    username: Optional[str] = None  # Username update requires validation
    role: Optional[UserRole] = None  # Role can't be updated by user
    
    # Make all fields optional for updates
    profile_image_url: Optional[str] = Field(None, max_length=500)
    notification_preferences: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = Field(None, max_length=50)
    
    class Config:
        exclude = {'email', 'role'}  # Exclude from updates


class UserResponse(BaseModel):
    """Schema for user responses - public user data"""
    id: UUID
    email: EmailStr
    username: str
    role: UserRole
    
    # Profile information
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]  # Computed property
    company_name: Optional[str]
    profile_image_url: Optional[str]
    bio: Optional[str]
    
    # Social handles (public)
    tiktok_handle: Optional[str]
    instagram_handle: Optional[str]
    
    # Status
    is_active: bool
    email_verified: bool
    profile_completion_percentage: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True
        
    @validator('full_name', always=True)
    def compute_full_name(cls, v, values):
        """Compute full name from first and last name"""
        if not v:
            first = values.get('first_name', '')
            last = values.get('last_name', '')
            if first and last:
                return f"{first} {last}"
            return first or last or None
        return v


class UserProfileResponse(UserResponse, AddressBase, CreatorMetricsBase):
    """Extended user response with private profile data - for own profile"""
    phone: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[GenderType]
    
    # Business details
    website_url: Optional[str]
    tax_id: Optional[str]
    
    # Social IDs (private)
    tiktok_user_id: Optional[str]
    discord_handle: Optional[str]
    discord_user_id: Optional[str]
    
    # Preferences
    notification_preferences: Dict[str, Any]
    timezone: str
    
    # Creator specific
    audience_demographics: Optional[List['CreatorAudienceDemographicsResponse']] = []
    badges: Optional[List['CreatorBadgeResponse']] = []


class CreatorAudienceDemographicsResponse(BaseModel):
    """Response schema for creator audience demographics"""
    age_group: str
    gender: GenderType
    percentage: float
    country: Optional[str]
    
    class Config:
        from_attributes = True


class CreatorBadgeResponse(BaseModel):
    """Response schema for creator badges"""
    badge_type: str
    badge_name: str
    badge_description: Optional[str]
    gmv_threshold: Optional[float]
    earned_at: datetime
    
    class Config:
        from_attributes = True


# Update forward references
UserProfileResponse.model_rebuild()