# app/core/config.py - User Service Configuration
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import json


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LaunchPAID User Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Service Configuration
    SERVICE_NAME: str = "user-service"
    SERVICE_PORT: int = 8000
    SERVICE_HOST: str = "0.0.0.0"

    # Database - Single source of truth
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REMEMBER_ME_DAYS: int = 30

    # CORS - Properly formatted
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001"
    ]

    

    # Email Configuration
    MAIL_ENABLED: bool = True
    MAIL_FROM: str = "noreply@launchpaid.com"
    MAIL_FROM_NAME: str = "LaunchPAID"

    # SMTP Settings (all required if email enabled)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Redis (Optional)
    REDIS_URL: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    LOGIN_RATE_LIMIT: str = "5/minute"
    SIGNUP_RATE_LIMIT: str = "3/hour"
    PASSWORD_RESET_RATE_LIMIT: str = "3/hour"
    VERIFY_EMAIL_RATE_LIMIT: str = "10/hour"
    GLOBAL_RATE_LIMIT: str = "100/minute"

    # Microservice URLs (for inter-service communication)
    CAMPAIGN_SERVICE_URL: str = "http://localhost:8002"
    ANALYTICS_SERVICE_URL: str = "http://localhost:8003"
    PAYMENT_SERVICE_URL: str = "http://localhost:8004"
    INTEGRATION_SERVICE_URL: str = "http://localhost:8005"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [v.strip("[]").strip('"').strip()]
            elif "," in v:
                return [i.strip() for i in v.split(",")]
            else:
                return [v.strip()]
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instantiate settings
settings = Settings()