# app/api/v1/__init__.py
from fastapi import APIRouter

# Import routers from auth and users modules
from .auth import router as auth_router
from .users import router as users_router

# Create the main API router
api_router = APIRouter()

# Include auth routes
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

# Include user routes
api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)