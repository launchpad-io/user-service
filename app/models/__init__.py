# app/models/__init__.py
"""
Database models for LaunchPAID platform.
Organized by schema for better separation of concerns.
"""

# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User, UserRole, GenderType
from app.models.user_token import (
    UserToken, 
    TokenType,
    CreatorAudienceDemographics,
    CreatorBadge,
    BadgeType
)

# Re-export for easier imports
__all__ = [
    # User models
    "User",
    "UserRole",
    "GenderType",
    
    # Token models
    "UserToken",
    "TokenType",
    
    # Creator related models
    "CreatorAudienceDemographics",
    "CreatorBadge",
    "BadgeType",
]

# Model registry for migrations
USER_MODELS = [
    User,
    UserToken,
    CreatorAudienceDemographics,
    CreatorBadge,
]

# Future model categories (for organization)
CAMPAIGN_MODELS = []  # Future: Campaign, CampaignCreator, Deliverable
ANALYTICS_MODELS = []  # Future: CreatorAnalytics, CampaignAnalytics
PAYMENT_MODELS = []  # Future: Payout, Transaction, Invoice
INTEGRATION_MODELS = []  # Future: TikTokIntegration, DiscordIntegration

# Helper function to get all models
def get_all_models():
    """Return all registered models for migrations"""
    return (
        USER_MODELS +
        CAMPAIGN_MODELS +
        ANALYTICS_MODELS +
        PAYMENT_MODELS +
        INTEGRATION_MODELS
    )