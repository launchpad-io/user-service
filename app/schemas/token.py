# # app/schemas/token.py
# """
# Token-related schemas for authentication and session management.
# Provides comprehensive token handling with security best practices.
# """
# from datetime import datetime, timezone
# from typing import Optional, Dict, Any, List
# from pydantic import BaseModel, Field, field_validator, ConfigDict
# from uuid import UUID
# import json

# from app.models.user_token import TokenType


# class TokenBase(BaseModel):
#     """Base token schema with common fields."""
#     token_type: TokenType
#     expires_at: Optional[datetime] = None
#     metadata: Optional[Dict[str, Any]] = None


# class TokenCreate(TokenBase):
#     """Schema for creating new tokens internally."""
#     user_id: UUID
#     token_value: str
    
#     model_config = ConfigDict(
#         json_encoders={
#             datetime: lambda v: v.isoformat()
#         }
#     )


# class RefreshTokenRequest(BaseModel):
#     """Request schema for refresh token endpoint."""
#     refresh_token: str = Field(
#         ..., 
#         description="Refresh token obtained from login",
#         min_length=32
#     )


# class RefreshTokenResponse(BaseModel):
#     """Response schema for refresh token endpoint."""
#     access_token: str
#     token_type: str = "bearer"
#     expires_in: int = Field(..., description="Access token expiration in seconds")
    
#     # Optional: Return new refresh token if implementing rotation
#     refresh_token: Optional[str] = Field(
#         None, 
#         description="New refresh token if rotation is enabled"
#     )


# class TokenPair(BaseModel):
#     """Response schema for login with both access and refresh tokens."""
#     access_token: str
#     refresh_token: str
#     token_type: str = "bearer"
#     expires_in: int = Field(..., description="Access token expiration in seconds")
#     refresh_expires_in: Optional[int] = Field(None, description="Refresh token expiration in seconds")


# # Alias for backward compatibility
# TokenPairResponse = TokenPair


# class SessionInfo(BaseModel):
#     """Schema for session information."""
#     model_config = ConfigDict(
#         from_attributes=True
#     )
    
#     id: UUID
#     created_at: datetime
#     last_active: datetime
#     user_agent: str
#     ip_address: str
#     location: Optional[str] = None
#     device: str
#     is_current: bool = False


# class SessionListResponse(BaseModel):
#     """Response schema for listing user sessions."""
#     sessions: List[SessionInfo]
#     total: int
#     current_session_id: Optional[UUID] = None


# class RevokeSessionRequest(BaseModel):
#     """Request schema for revoking specific session."""
#     session_id: UUID = Field(..., description="Session ID to revoke")


# class RevokeAllSessionsRequest(BaseModel):
#     """Request schema for revoking all sessions."""
#     except_current: bool = Field(
#         True, 
#         description="Keep current session active"
#     )
#     password: str = Field(
#         ..., 
#         description="User password for confirmation",
#         min_length=1
#     )


# class TokenValidationResponse(BaseModel):
#     """Response schema for token validation endpoint."""
#     valid: bool
#     token_type: Optional[TokenType] = None
#     user_id: Optional[UUID] = None
#     expires_at: Optional[datetime] = None
#     issued_at: Optional[datetime] = None
    
#     @field_validator('expires_at', 'issued_at')
#     @classmethod
#     def ensure_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
#         """Ensure datetime has timezone info."""
#         if v and v.tzinfo is None:
#             return v.replace(tzinfo=timezone.utc)
#         return v


# class TokenMetadata(BaseModel):
#     """Schema for token metadata."""
#     user_agent: Optional[str] = None
#     ip_address: Optional[str] = None
#     location: Optional[str] = None
#     device_id: Optional[str] = None
#     app_version: Optional[str] = None
    
#     def to_json_string(self) -> str:
#         """Convert metadata to JSON string for storage."""
#         return json.dumps(self.model_dump(exclude_none=True))
    
#     @classmethod
#     def from_json_string(cls, json_str: str) -> 'TokenMetadata':
#         """Create metadata from JSON string."""
#         try:
#             data = json.loads(json_str)
#             return cls(**data)
#         except:
#             return cls()


# class TokenCleanupStats(BaseModel):
#     """Response schema for token cleanup operations."""
#     expired_tokens_removed: int
#     used_tokens_removed: int
#     total_removed: int
#     cleanup_duration_ms: float
    
#     model_config = ConfigDict(
#         json_schema_extra={
#             "example": {
#                 "expired_tokens_removed": 42,
#                 "used_tokens_removed": 13,
#                 "total_removed": 55,
#                 "cleanup_duration_ms": 123.45
#             }
#         }
#     )


# class TokenRateLimitInfo(BaseModel):
#     """Schema for token-related rate limit information."""
#     endpoint: str
#     limit: int
#     remaining: int
#     reset_at: datetime
#     retry_after: Optional[int] = None
    
#     @property
#     def is_limited(self) -> bool:
#         """Check if rate limited."""
#         return self.remaining <= 0


# class OAuthTokenRequest(BaseModel):
#     """Request schema for OAuth token exchange."""
#     provider: str = Field(..., description="OAuth provider (google, tiktok, discord)")
#     code: str = Field(..., description="Authorization code from OAuth provider")
#     state: Optional[str] = Field(None, description="State parameter for CSRF protection")
#     redirect_uri: str = Field(..., description="Redirect URI used in OAuth flow")


# class OAuthTokenResponse(TokenPair):
#     """Response schema for OAuth token exchange."""
#     provider: str
#     provider_user_id: str
#     provider_username: Optional[str] = None
#     email: Optional[str] = None
#     is_new_user: bool = Field(..., description="Whether a new user was created")


# # Re-export commonly used schemas
# __all__ = [
#     'RefreshTokenRequest',
#     'RefreshTokenResponse',
#     'TokenPair',
#     'TokenPairResponse',
#     'SessionInfo',
#     'SessionListResponse',
#     'RevokeSessionRequest',
#     'RevokeAllSessionsRequest',
#     'TokenValidationResponse',
#     'TokenMetadata',
#     'TokenCleanupStats',
#     'OAuthTokenRequest',
#     'OAuthTokenResponse',
# ]


# 3. app/schemas/token.py - Create this file
# app/schemas/token.py
from pydantic import BaseModel
from typing import Optional

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    error: Optional[str] = None