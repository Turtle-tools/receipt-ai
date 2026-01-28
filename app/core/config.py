"""
Application configuration.

Uses pydantic-settings for environment variable loading.
"""

from functools import lru_cache
from typing import Optional, Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_name: str = "Receipt AI"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    
    # API
    api_prefix: str = "/api"
    
    # Database (for future use)
    database_url: Optional[str] = None
    
    # Redis (for Celery background tasks)
    redis_url: Optional[str] = None
    
    # AI Extraction
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ai_provider: Literal["openai", "anthropic"] = "openai"
    ai_model: str = "gpt-4o"  # or claude-3-5-sonnet-20241022
    
    # QuickBooks Online
    qbo_client_id: Optional[str] = None
    qbo_client_secret: Optional[str] = None
    qbo_redirect_uri: str = "http://localhost:8000/api/qbo/callback"
    qbo_environment: Literal["sandbox", "production"] = "sandbox"
    
    # Storage
    storage_type: Literal["local", "s3", "r2"] = "local"
    local_storage_path: str = "./uploads"
    
    # S3 / R2
    s3_bucket: Optional[str] = None
    s3_region: str = "us-east-1"
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    r2_account_id: Optional[str] = None
    r2_bucket: Optional[str] = None
    
    # Webhooks
    webhook_secret: Optional[str] = None  # HMAC secret for webhook verification
    
    # Stripe (for billing)
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_starter: Optional[str] = None  # Stripe Price ID
    stripe_price_pro: Optional[str] = None
    stripe_price_firm: Optional[str] = None
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    # Document processing
    max_file_size_mb: int = 50
    max_pages_per_document: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def ai_api_key(self) -> Optional[str]:
        """Get the configured AI API key."""
        if self.ai_provider == "openai":
            return self.openai_api_key
        return self.anthropic_api_key
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()
