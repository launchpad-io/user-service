# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import string

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token settings
ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET_KEY


def create_access_token(
    subject: Union[str, int], 
    expires_delta: Optional[timedelta] = None,
    remember_me: bool = False
) -> str:
    """
    Create JWT access token.
    
    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional custom expiration time
        remember_me: If True, extends expiration time
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    elif remember_me:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REMEMBER_ME_DAYS)
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode JWT access token and return subject.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return pwd_context.hash(password)


def generate_token(length: int = 32) -> str:
    """
    Generate a random token for email verification or password reset.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_verification_token() -> tuple[str, datetime]:
    """
    Generate email verification token and expiration time.
    Returns: (token, expiration_datetime)
    """
    token = generate_token(32)
    expires = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiration
    return token, expires


def generate_reset_token() -> tuple[str, datetime]:
    """
    Generate password reset token and expiration time.
    Returns: (token, expiration_datetime)
    """
    token = generate_token(32)
    expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration
    return token, expires


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets minimum requirements.
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
    
    return True, ""