# app/core/exceptions.py - Missing Exception Module
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from typing import Union

logger = logging.getLogger(__name__)

class CampaignServiceException(Exception):
    """Base exception class for campaign service"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class CampaignNotFoundException(CampaignServiceException):
    """Exception raised when campaign is not found"""
    def __init__(self, campaign_id: str):
        super().__init__(f"Campaign with id {campaign_id} not found", 404)

class UnauthorizedAccessException(CampaignServiceException):
    """Exception raised for unauthorized access"""
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, 403)

class ValidationException(CampaignServiceException):
    """Exception raised for validation errors"""
    def __init__(self, message: str):
        super().__init__(message, 400)

class ExternalServiceException(CampaignServiceException):
    """Exception raised for external service errors"""
    def __init__(self, service_name: str, message: str):
        super().__init__(f"External service {service_name} error: {message}", 502)

# Global exception handlers
async def campaign_service_exception_handler(request: Request, exc: CampaignServiceException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An internal server error occurred",
            "status_code": 500
        }
    )

# Middleware for request logging
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            # Log response
            logger.info(f"Response: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise