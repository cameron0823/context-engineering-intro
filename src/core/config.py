"""
Core configuration management using pydantic-settings.
Handles all environment variables and application settings.
"""
from typing import List, Optional
from decimal import Decimal
from datetime import time
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )
    
    # Application
    APP_NAME: str = "Tree Service Estimating"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("CORS_ORIGINS", mode='before')
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v
    
    # External APIs
    GOOGLE_MAPS_API_KEY: str
    GOOGLE_MAPS_DAILY_LIMIT: int = 2500
    
    QUICKBOOKS_CLIENT_ID: str
    QUICKBOOKS_CLIENT_SECRET: str
    QUICKBOOKS_COMPANY_ID: str
    QUICKBOOKS_API_URL: AnyHttpUrl = "https://sandbox-quickbooks.api.intuit.com"
    
    FUEL_API_KEY: str
    FUEL_API_HOURLY_LIMIT: int = 100
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600
    
    # Business Rules (using Decimal for precision)
    DEFAULT_OVERHEAD_PERCENT: Decimal = Decimal("25.0")
    DEFAULT_PROFIT_PERCENT: Decimal = Decimal("35.0")
    DEFAULT_SAFETY_BUFFER_PERCENT: Decimal = Decimal("10.0")
    DEFAULT_VEHICLE_RATE_PER_MILE: Decimal = Decimal("0.65")
    DEFAULT_DRIVER_HOURLY_RATE: Decimal = Decimal("25.00")
    
    @field_validator(
        "DEFAULT_OVERHEAD_PERCENT",
        "DEFAULT_PROFIT_PERCENT",
        "DEFAULT_SAFETY_BUFFER_PERCENT",
        "DEFAULT_VEHICLE_RATE_PER_MILE",
        "DEFAULT_DRIVER_HOURLY_RATE",
        mode='before'
    )
    def convert_to_decimal(cls, v):
        if isinstance(v, str):
            return Decimal(v)
        return v
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Business Hours
    BUSINESS_HOURS_START: time = time(8, 0)
    BUSINESS_HOURS_END: time = time(18, 0)
    BUSINESS_TIMEZONE: str = "America/New_York"
    
    @field_validator("BUSINESS_HOURS_START", "BUSINESS_HOURS_END", mode='before')
    def parse_time(cls, v):
        if isinstance(v, str):
            hour, minute = map(int, v.split(":"))
            return time(hour, minute)
        return v
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # API Limits
    MAX_ESTIMATE_HOURS: Decimal = Decimal("16.0")
    MAX_TRAVEL_MILES: Decimal = Decimal("500.0")
    MAX_CREW_SIZE: int = 10
    
    # Rounding
    FINAL_TOTAL_ROUNDING: Decimal = Decimal("5.0")


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance (useful for dependency injection)."""
    return settings