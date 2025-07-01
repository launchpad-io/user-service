# app/core/config.py
from typing import Optional, Union, List
from pydantic_settings import BaseSettings
from pydantic import EmailStr, validator
import json


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LaunchPAID API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    STORAGE_BACKEND: str = "local"  # 'local' or 's3'
    CDN_URL: Optional[str] = None

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REMEMBER_ME_DAYS: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://127.0.0.1:3000"]

    # Email
    MAIL_ENABLED: bool = True
    MAIL_FROM: EmailStr = "noreply@launchpaid.com"
    MAIL_FROM_NAME: str = "LaunchPAID"

    # SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
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
    
    # Rate Limit Storage (future enhancement)
    RATE_LIMIT_STORAGE_URL: Optional[str] = None  # For Redis in production

    # Environment
    ENVIRONMENT: str = "development"

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            # Handle JSON array format like ["http://localhost:3000"]
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as single URL
                    return [v.strip("[]").strip('"').strip()]
            # Handle comma-separated format
            elif "," in v:
                return [i.strip() for i in v.split(",")]
            # Handle single URL
            else:
                return [v.strip()]
        elif isinstance(v, list):
            return v
        else:
            return [str(v)]

    class Config:
        env_file = ".env"
        case_sensitive = True


# ✅ No circular imports — instantiate settings here
settings = Settings()