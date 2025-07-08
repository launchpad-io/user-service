# app/core/security.py - Clean version without duplicates
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import string
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token settings
ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET_KEY
REFRESH_SECRET_KEY = settings.JWT_SECRET_KEY + "_refresh"  # Different secret for refresh tokens

# Token expiration times
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 30  # Long-lived refresh tokens


def create_access_token(
    subject: Union[str, int], 
    expires_delta: Optional[timedelta] = None,
    remember_me: bool = False,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create JWT access token with enhanced claims.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif remember_me:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(subject),
        "type": "access",
        "jti": generate_token(16)
    }
    
    # Add additional claims if provided
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    device_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create JWT refresh token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(subject),
        "type": "refresh",
        "jti": generate_token(16),
    }
    
    # Add device info if provided
    if device_info:
        to_encode["device"] = device_info
    
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_token_pair(
    user_id: str,
    remember_me: bool = False,
    device_info: Optional[Dict[str, Any]] = None,
    user_role: Optional[str] = None  # KEEP THIS PARAMETER
) -> tuple[str, str]:
    """
    Create both access and refresh tokens with role information.
    
    Returns: (access_token, refresh_token)
    """
    # Include role in additional claims for access token
    additional_claims = {}
    if user_role:
        additional_claims["role"] = user_role
    
    access_token = create_access_token(
        subject=user_id,
        remember_me=remember_me,
        additional_claims=additional_claims
    )
    
    refresh_token = create_refresh_token(
        subject=user_id,
        device_info=device_info
    )
    
    return access_token, refresh_token


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT access token and return payload.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "access":
            logger.warning("Invalid token type: expected access token")
            return None
            
        return payload
    except JWTError as e:
        logger.debug(f"Token decode error: {str(e)}")
        return None


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT refresh token and return payload.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type: expected refresh token")
            return None
            
        return payload
    except JWTError as e:
        logger.debug(f"Refresh token decode error: {str(e)}")
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    Supports both bcrypt hashes and legacy mock hashes for backward compatibility.
    """
    try:
        # Try bcrypt verification first
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.debug(f"Bcrypt verification failed: {str(e)}")
        
        # Fallback: Check if it's a legacy mock hash
        if hashed_password.startswith("hashed_"):
            expected_mock_hash = f"hashed_{plain_password}"
            return hashed_password == expected_mock_hash
        
        logger.error(f"Password verification error: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def generate_token(length: int = 32) -> str:
    """Generate a random token for various purposes."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_secure_token(prefix: str = "", length: int = 32) -> str:
    """Generate a secure token with optional prefix."""
    token = generate_token(length)
    return f"{prefix}{token}" if prefix else token


def generate_verification_token() -> tuple[str, datetime]:
    """Generate email verification token and expiration time."""
    token = generate_token(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    return token, expires


def generate_reset_token() -> tuple[str, datetime]:
    """Generate password reset token and expiration time."""
    token = generate_token(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    return token, expires


def generate_api_key() -> str:
    """Generate an API key for programmatic access."""
    return generate_secure_token(prefix="lpk_", length=32)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets minimum requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
    
    return True, ""


def extract_token_from_header(authorization: str) -> Optional[str]:
    """Extract token from Authorization header."""
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None