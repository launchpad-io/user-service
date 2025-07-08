# app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Integer, DECIMAL, Text, Date, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    AGENCY = "agency"
    CREATOR = "creator"
    BRAND = "brand"
    ADMIN = "admin"
    
    # Override the __str__ method to always return lowercase
    def __str__(self):
        return self.value


class GenderType(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    
    def __str__(self):
        return self.value


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "users"}
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Role - Force lowercase values
    role = Column(
        SQLEnum(UserRole, schema="users", name="user_role", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    
    # Account status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    phone = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(
        SQLEnum(GenderType, schema="users", name="gender_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=True
    )
    profile_image_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    
    # Address information for shipping
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default='US')
    
    # Social media handles
    tiktok_handle = Column(String(100), nullable=True)
    tiktok_user_id = Column(String(100), nullable=True)
    discord_handle = Column(String(100), nullable=True)
    discord_user_id = Column(String(100), nullable=True)
    instagram_handle = Column(String(100), nullable=True)
    
    # Creator specific fields
    content_niche = Column(String(100), nullable=True)
    follower_count = Column(Integer, default=0)
    average_views = Column(Integer, default=0)
    engagement_rate = Column(DECIMAL(5, 2), default=0.00)
    
    # Agency/Brand specific fields
    company_name = Column(String(200), nullable=True)
    website_url = Column(Text, nullable=True)
    tax_id = Column(String(50), nullable=True)
    
    # Profile completion tracking
    profile_completion_percentage = Column(Integer, default=0)
    
    # Preferences
    notification_preferences = Column(JSON, default=dict)
    timezone = Column(String(50), default='UTC')
    
    # Relationships
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    audience_demographics = relationship("CreatorAudienceDemographics", back_populates="creator", cascade="all, delete-orphan")
    badges = relationship("CreatorBadge", back_populates="creator", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def full_name(self):
        """Computed property for backward compatibility"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or None
    
    @property
    def display_name(self):
        """Get the appropriate display name based on role"""
        if self.role in [UserRole.AGENCY, UserRole.BRAND]:
            return self.company_name or self.full_name or self.username
        return self.full_name or self.username
    
    def calculate_profile_completion(self):
        """Calculate profile completion percentage"""
        required_fields = ['email', 'username', 'first_name', 'last_name']
        optional_fields = ['phone', 'bio', 'profile_image_url']
        
        if self.role == UserRole.CREATOR:
            required_fields.extend(['tiktok_handle', 'content_niche'])
            optional_fields.extend(['date_of_birth', 'gender'])
        elif self.role in [UserRole.AGENCY, UserRole.BRAND]:
            required_fields.extend(['company_name'])
            optional_fields.extend(['website_url', 'tax_id'])
        
        # Calculate completion
        total_fields = len(required_fields) + len(optional_fields)
        completed = 0
        
        for field in required_fields:
            if getattr(self, field):
                completed += 2  # Required fields worth more
        
        for field in optional_fields:
            if getattr(self, field):
                completed += 1
                
        # Normalize to percentage
        max_points = (len(required_fields) * 2) + len(optional_fields)
        self.profile_completion_percentage = int((completed / max_points) * 100)
        
        return self.profile_completion_percentage