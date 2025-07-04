# # app/schemas/user.py
# from datetime import datetime, date
# from typing import Optional, Dict, Any, List
# from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
# from uuid import UUID

# from app.models.user import UserRole, GenderType


# class AddressBase(BaseModel):
#     """Base schema for address information"""
#     address_line1: Optional[str] = Field(None, max_length=255)
#     address_line2: Optional[str] = Field(None, max_length=255)
#     city: Optional[str] = Field(None, max_length=100)
#     state: Optional[str] = Field(None, max_length=100)
#     postal_code: Optional[str] = Field(None, max_length=20)
#     country: Optional[str] = Field(default="US", max_length=100)


# class SocialHandlesBase(BaseModel):
#     """Base schema for social media handles"""
#     tiktok_handle: Optional[str] = Field(None, max_length=100)
#     discord_handle: Optional[str] = Field(None, max_length=100)
#     instagram_handle: Optional[str] = Field(None, max_length=100)
    
#     @field_validator('tiktok_handle', 'instagram_handle')
#     @classmethod
#     def validate_social_handle(cls, v: Optional[str]) -> Optional[str]:
#         """Remove @ symbol and validate format"""
#         if v:
#             v = v.lstrip('@').strip()
#             if not v.replace('_', '').replace('.', '').isalnum():
#                 raise ValueError('Handle can only contain letters, numbers, underscores, and periods')
#         return v


# class CreatorMetricsBase(BaseModel):
#     """Base schema for creator metrics"""
#     content_niche: Optional[str] = Field(None, max_length=100)
#     follower_count: Optional[int] = Field(default=0, ge=0)
#     average_views: Optional[int] = Field(default=0, ge=0)
#     engagement_rate: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)


# class UserBase(BaseModel):
#     """Base user schema with common fields"""
#     model_config = ConfigDict(
#         use_enum_values=True,
#         from_attributes=True
#     )
    
#     email: EmailStr
#     username: Optional[str] = Field(None, min_length=3, max_length=100, pattern="^[a-zA-Z0-9_-]+$")
#     role: UserRole
    
#     # Personal information
#     first_name: Optional[str] = Field(None, max_length=100)
#     last_name: Optional[str] = Field(None, max_length=100)
#     phone: Optional[str] = Field(None, pattern="^\\+?[1-9]\\d{1,14}$")  # E.164 format
#     date_of_birth: Optional[date] = None
#     gender: Optional[GenderType] = None
#     bio: Optional[str] = Field(None, max_length=500)
    
#     # Business information
#     company_name: Optional[str] = Field(None, max_length=200)
#     website_url: Optional[str] = Field(None, max_length=500)
#     tax_id: Optional[str] = Field(None, max_length=50)
    
#     @field_validator('website_url')
#     @classmethod
#     def validate_website(cls, v: Optional[str]) -> Optional[str]:
#         """Add https:// if not present"""
#         if v and not v.startswith(('http://', 'https://')):
#             return f'https://{v}'
#         return v
    
#     @property
#     def full_name(self) -> Optional[str]:
#         """Computed full name property"""
#         if self.first_name and self.last_name:
#             return f"{self.first_name} {self.last_name}"
#         return self.first_name or self.last_name


# class UserCreate(UserBase, SocialHandlesBase):
#     """Schema for creating a new user - used in signup"""
#     model_config = ConfigDict(
#         use_enum_values=True
#     )
    
#     password: str = Field(..., min_length=8)
#     confirm_password: str
#     accept_terms: bool = Field(..., description="User must accept terms")
    
#     # For backward compatibility
#     tiktok_username: Optional[str] = None  # Alias for tiktok_handle
#     contact_full_name: Optional[str] = None  # For agencies/brands
#     website: Optional[str] = None  # Alias for website_url
    
#     @model_validator(mode='before')
#     @classmethod
#     def handle_legacy_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
#         """Handle legacy field names for backward compatibility"""
#         if isinstance(values, dict):
#             # Handle full_name splitting
#             if values.get('full_name') and not values.get('first_name'):
#                 name_parts = values['full_name'].strip().split(' ', 1)
#                 values['first_name'] = name_parts[0] if name_parts else None
#                 values['last_name'] = name_parts[1] if len(name_parts) > 1 else None
            
#             # Handle contact_full_name for agencies/brands
#             if values.get('contact_full_name') and not values.get('first_name'):
#                 name_parts = values['contact_full_name'].strip().split(' ', 1)
#                 values['first_name'] = name_parts[0] if name_parts else None
#                 values['last_name'] = name_parts[1] if len(name_parts) > 1 else None
            
#             # Map old field names to new ones
#             if values.get('tiktok_username'):
#                 values['tiktok_handle'] = values['tiktok_username']
#             if values.get('website'):
#                 values['website_url'] = values['website']
                
#         return values
    
#     @field_validator('confirm_password')
#     @classmethod
#     def passwords_match(cls, v: str, info) -> str:
#         """Validate passwords match"""
#         if 'password' in info.data and v != info.data['password']:
#             raise ValueError('Passwords do not match')
#         return v
    
#     @field_validator('accept_terms')
#     @classmethod
#     def terms_accepted(cls, v: bool) -> bool:
#         """Ensure terms are accepted"""
#         if not v:
#             raise ValueError('You must accept the terms and conditions')
#         return v
    
#     @model_validator(mode='after')
#     def validate_role_fields(self) -> 'UserCreate':
#         """Validate required fields based on role"""
#         if self.role == UserRole.CREATOR:
#             if not self.first_name:
#                 raise ValueError('First name is required for creators')
#             if not self.tiktok_handle and not self.tiktok_username:
#                 raise ValueError('TikTok handle is required for creators')
                
#         elif self.role in [UserRole.AGENCY, UserRole.BRAND]:
#             if not self.company_name:
#                 raise ValueError('Company name is required for agencies and brands')
                
#         return self


# class UserUpdate(UserBase, AddressBase, SocialHandlesBase, CreatorMetricsBase):
#     """Schema for updating user profile"""
#     model_config = ConfigDict(
#         use_enum_values=True,
#         from_attributes=True
#     )
    
#     email: Optional[EmailStr] = None  # Email can't be updated directly
#     username: Optional[str] = None  # Username update requires validation
#     role: Optional[UserRole] = None  # Role can't be updated by user
    
#     # Make all fields optional for updates
#     profile_image_url: Optional[str] = Field(None, max_length=500)
#     notification_preferences: Optional[Dict[str, Any]] = None
#     timezone: Optional[str] = Field(None, max_length=50)


# class UserResponse(BaseModel):
#     """Schema for user responses - public user data"""
#     model_config = ConfigDict(
#         from_attributes=True,
#         use_enum_values=True
#     )
    
#     id: UUID
#     email: EmailStr
#     username: str
#     role: UserRole
    
#     # Profile information
#     first_name: Optional[str]
#     last_name: Optional[str]
#     full_name: Optional[str] = None  # Computed property
#     company_name: Optional[str]
#     profile_image_url: Optional[str]
#     bio: Optional[str]
    
#     # Social handles (public)
#     tiktok_handle: Optional[str]
#     instagram_handle: Optional[str]
    
#     # Status
#     is_active: bool
#     email_verified: bool
#     profile_completion_percentage: int
    
#     # Timestamps
#     created_at: datetime
#     updated_at: datetime
#     last_login: Optional[datetime]
    
#     @model_validator(mode='after')
#     def compute_full_name(self) -> 'UserResponse':
#         """Compute full name from first and last name"""
#         if not self.full_name:
#             first = self.first_name or ''
#             last = self.last_name or ''
#             if first and last:
#                 self.full_name = f"{first} {last}"
#             else:
#                 self.full_name = first or last or None
#         return self


# class UserProfileResponse(UserResponse, AddressBase, CreatorMetricsBase):
#     """Extended user response with private profile data - for own profile"""
#     model_config = ConfigDict(
#         from_attributes=True,
#         use_enum_values=True
#     )
    
#     phone: Optional[str]
#     date_of_birth: Optional[date]
#     gender: Optional[GenderType]
    
#     # Business details
#     website_url: Optional[str]
#     tax_id: Optional[str]
    
#     # Social IDs (private)
#     tiktok_user_id: Optional[str]
#     discord_handle: Optional[str]
#     discord_user_id: Optional[str]
    
#     # Preferences
#     notification_preferences: Dict[str, Any]
#     timezone: str
    
#     # Creator specific
#     audience_demographics: Optional[List['CreatorAudienceDemographicsResponse']] = []
#     badges: Optional[List['CreatorBadgeResponse']] = []


# class CreatorAudienceDemographicsResponse(BaseModel):
#     """Response schema for creator audience demographics"""
#     model_config = ConfigDict(
#         from_attributes=True,
#         use_enum_values=True
#     )
    
#     age_group: str
#     gender: GenderType
#     percentage: float
#     country: Optional[str]


# class CreatorBadgeResponse(BaseModel):
#     """Response schema for creator badges"""
#     model_config = ConfigDict(
#         from_attributes=True
#     )
    
#     badge_type: str
#     badge_name: str
#     badge_description: Optional[str]
#     gmv_threshold: Optional[float]
#     earned_at: datetime


# # Update forward references
# UserProfileResponse.model_rebuild()


# 2. app/schemas/user.py - Create this file
# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, GenderType

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    role: UserRole
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[GenderType] = None

class UserProfileResponse(UserResponse):
    phone: Optional[str] = None
    last_login: Optional[datetime] = None
    date_of_birth: Optional[str] = None
    gender: Optional[GenderType] = None
