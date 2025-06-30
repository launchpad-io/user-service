# app/models/user_token.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import json

from app.core.database import Base


class TokenType(str, enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "reset_password"
    OAUTH = "oauth"
    REFRESH = "refresh"
    API_KEY = "api_key"
    ACCESS = "access"  # Added for tracking access tokens if needed


class UserToken(Base):
    __tablename__ = "user_tokens"
    __table_args__ = (
        Index('ix_user_tokens_user_id_type', 'user_id', 'token_type'),
        Index('ix_user_tokens_expires_at', 'expires_at'),
        {"schema": "users"}
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.users.id", ondelete="CASCADE"), nullable=False)
    
    # Token details
    token_type = Column(String(50), nullable=False)
    token_value = Column(String(500), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_used = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Additional metadata (for OAuth tokens, device info, etc.)
    token_metadata = Column(JSON, nullable=True, default=dict)
    
    # JWT ID for tracking (if using JWT tokens)
    jti = Column(String(100), nullable=True, unique=True, index=True)
    
    # Last used timestamp (for refresh tokens and API keys)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # IP address and user agent (for security tracking)
    created_ip = Column(String(45), nullable=True)  # Supports IPv6
    last_used_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tokens")
    
    def __repr__(self):
        return f"<UserToken {self.token_type} for user {self.user_id}>"
    
    @property
    def is_expired(self):
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self, db_session):
        """Mark token as used"""
        self.is_used = True
        self.last_used_at = datetime.now(timezone.utc)
        db_session.commit()
    
    def update_last_used(self, db_session, ip_address=None):
        """Update last used timestamp and IP"""
        self.last_used_at = datetime.now(timezone.utc)
        if ip_address:
            self.last_used_ip = ip_address
        db_session.commit()
    
    def get_metadata(self, key=None):
        """Get metadata value or entire metadata dict"""
        if not self.token_metadata:
            return None if key else {}
        
        if key:
            return self.token_metadata.get(key)
        return self.token_metadata
    
    def set_metadata(self, key, value, db_session):
        """Set metadata value"""
        if not self.token_metadata:
            self.token_metadata = {}
        
        self.token_metadata[key] = value
        db_session.commit()
    
    @property
    def device_info(self):
        """Extract device info from metadata"""
        return self.get_metadata('device') or {}
    
    @property
    def scopes(self):
        """Get token scopes (for API keys)"""
        return self.get_metadata('scopes') or []
    
    @property
    def time_until_expiry(self):
        """Get time remaining until token expires"""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - datetime.now(timezone.utc)
        return delta if delta.total_seconds() > 0 else None
    
    def to_dict(self):
        """Convert token to dictionary for API responses"""
        return {
            'id': str(self.id),
            'type': self.token_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'is_valid': self.is_valid,
            'device_info': self.device_info,
            'created_ip': self.created_ip,
            'last_used_ip': self.last_used_ip
        }


# Additional models for the users schema (keeping from original)

from sqlalchemy import DECIMAL, Text
from app.models.user import GenderType


class CreatorAudienceDemographics(Base):
    __tablename__ = "creator_audience_demographics"
    __table_args__ = {"schema": "users"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.users.id", ondelete="CASCADE"), nullable=False)
    age_group = Column(String(20), nullable=False)  # '13-17', '18-24', etc.
    gender = Column(SQLEnum(GenderType, schema="users", name="gender_type"), nullable=False)
    percentage = Column(DECIMAL(5, 2), nullable=False)
    country = Column(String(100), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    creator = relationship("User", back_populates="audience_demographics")
    
    def __repr__(self):
        return f"<CreatorAudienceDemographics {self.age_group} {self.gender} - {self.percentage}%>"


class BadgeType(str, enum.Enum):
    GMV_1K = "gmv_1k"
    GMV_10K = "gmv_10k"
    GMV_50K = "gmv_50k"
    GMV_100K = "gmv_100k"
    GMV_500K = "gmv_500k"
    GMV_1M = "gmv_1m"
    TOP_CREATOR = "top_creator"
    VERIFIED = "verified"
    RISING_STAR = "rising_star"


class CreatorBadge(Base):
    __tablename__ = "creator_badges"
    __table_args__ = {"schema": "users"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.users.id", ondelete="CASCADE"), nullable=False)
    badge_type = Column(String(50), nullable=False)
    badge_name = Column(String(100), nullable=False)
    badge_description = Column(Text, nullable=True)
    gmv_threshold = Column(DECIMAL(12, 2), nullable=True)
    earned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Additional badge metadata
    badge_metadata = Column(JSON, nullable=True, default=dict)
    
    # Relationships
    creator = relationship("User", back_populates="badges")
    
    def __repr__(self):
        return f"<CreatorBadge {self.badge_name} for {self.creator_id}>"
    
    def to_dict(self):
        """Convert badge to dictionary for API responses"""
        return {
            'id': str(self.id),
            'badge_type': self.badge_type,
            'badge_name': self.badge_name,
            'badge_description': self.badge_description,
            'gmv_threshold': float(self.gmv_threshold) if self.gmv_threshold else None,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'is_active': self.is_active,
            'metadata': self.badge_metadata or {}
        }