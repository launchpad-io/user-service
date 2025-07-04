# app/core/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Create limiter instance with custom key function
def get_real_client_ip(request: Request) -> str:
    """
    Get the real client IP address, considering proxy headers.
    """
    # Check for proxy headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, get the first one
        return forwarded_for.split(",")[0].strip()
    
    # Check for other proxy headers
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return get_remote_address(request)

# Import settings
from app.core.config import settings

# Create the limiter instance
limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=[settings.GLOBAL_RATE_LIMIT] if settings.RATE_LIMIT_ENABLED else [],
    headers_enabled=True,  # Enable rate limit headers in responses
    enabled=settings.RATE_LIMIT_ENABLED,  # Enable/disable based on settings
)

# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    """
    # Parse the detail to extract retry time
    detail = str(exc.detail)
    
    # Extract retry_after from the exception or calculate it
    retry_after = 60  # Default to 60 seconds
    
    response = JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {detail}",
            "success": False,
            "message": "Too many requests. Please try again later."
        }
    )
    
    # Add rate limit headers
    response.headers["Retry-After"] = str(retry_after)
    
    return response

# Rate limit decorators for specific endpoints
# These can be imported and used on specific routes

# Auth endpoints limits - using settings
login_limit = limiter.limit(settings.LOGIN_RATE_LIMIT)
signup_limit = limiter.limit(settings.SIGNUP_RATE_LIMIT)
password_reset_limit = limiter.limit(settings.PASSWORD_RESET_RATE_LIMIT)
verify_email_limit = limiter.limit(settings.VERIFY_EMAIL_RATE_LIMIT)

# General API limits
api_limit = limiter.limit("100 per minute")
strict_limit = limiter.limit("10 per minute")

# Helper function to add rate limiter to FastAPI app
def add_rate_limiter(app):
    """
    Add rate limiter middleware and exception handler to FastAPI app.
    """
    # Add the middleware
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    
    # Add the exception handler
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    
    return app