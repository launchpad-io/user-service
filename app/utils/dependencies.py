# app/utils/dependencies.py
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
import logging

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.models.user_token import UserToken, TokenType
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    Enhanced with better error messages and logging.
    """
    token = credentials.credentials
    
    # Decode token
    try:
        payload = decode_access_token(token)
        if payload is None:
            logger.warning("Failed to decode token - invalid or expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token missing subject")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = auth_service.get_user_by_id(db, user_id)
    if user is None:
        logger.warning(f"User not found for ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
        )
    
    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user who has verified their email.
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address to access this resource",
        )
    return current_user


async def get_current_active_user(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """
    Get current active and verified user.
    This is the most common dependency for protected endpoints.
    """
    # Profile completion check for certain features
    if current_user.profile_completion_percentage < 50:
        logger.info(f"User {current_user.email} has incomplete profile: {current_user.profile_completion_percentage}%")
    
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that have different behavior for authenticated users.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                user = auth_service.get_user_by_id(db, user_id)
                if user and user.is_active:
                    return user
    except Exception as e:
        logger.debug(f"Optional auth failed: {str(e)}")
    
    return None


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_checker


def require_profile_completion(min_percentage: int = 80):
    """
    Dependency factory to require minimum profile completion.
    
    Usage:
        @router.post("/create-campaign", dependencies=[Depends(require_profile_completion(80))])
    """
    async def completion_checker(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        # Recalculate profile completion
        current_user.calculate_profile_completion()
        db.commit()
        
        if current_user.profile_completion_percentage < min_percentage:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Please complete your profile to at least {min_percentage}%. Current: {current_user.profile_completion_percentage}%"
            )
        return current_user
    
    return completion_checker


async def get_current_creator(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if they are a creator."""
    if current_user.role != UserRole.CREATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This resource is only available to creators"
        )
    return current_user


async def get_current_agency(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if they are an agency."""
    if current_user.role != UserRole.AGENCY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This resource is only available to agencies"
        )
    return current_user


async def get_current_brand(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if they are a brand."""
    if current_user.role != UserRole.BRAND:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This resource is only available to brands"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if they are an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative access required"
        )
    return current_user


async def validate_token_from_query(
    token: str,
    token_type: TokenType,
    db: Session = Depends(get_db)
) -> UserToken:
    """
    Validate a token from query parameters (for email verification, password reset, etc.)
    """
    user_token = db.query(UserToken).filter(
        UserToken.token_value == token,
        UserToken.token_type == token_type,
        UserToken.is_used == False
    ).first()
    
    if not user_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    if user_token.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired. Please request a new one."
        )
    
    return user_token