# ==============================================================================
# CONFIGURATION MODULE
# ==============================================================================
# This module loads and validates all configuration from environment variables.
# We use Pydantic Settings for type-safe configuration management.
# ==============================================================================

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic Settings automatically reads from:
    1. Environment variables
    2. .env file (if python-dotenv is installed)
    
    All values are validated and type-converted automatically.
    """
    
    # Database connection string
    # Format: postgresql+asyncpg://user:password@host:port/database
    # The +asyncpg part tells SQLAlchemy to use the async driver
    database_url: str
    
    @field_validator("database_url")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        """
        Fixes the connection string provided by Render/Neon.
        SQLAlchemy+asyncpg requires 'postgresql+asyncpg://' but Render provides 'postgres://'.
        """
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v
    
    # JWT Authentication settings
    # SECRET_KEY should be a long random string (use: openssl rand -hex 32)
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours by default
    
    # CORS (Cross-Origin Resource Sharing) settings
    # This allows our React frontend to call the API from a different port
    cors_origins: str = "http://localhost:5173"
    
    # API configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Exam Scheduling Platform"
    debug: bool = False
    
    # Supabase configuration (optional, for direct Supabase client usage)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    
    # Model configuration tells Pydantic where to find the .env file
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,       # DATABASE_URL and database_url are the same
        extra="ignore"              # Ignore extra env vars
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """
        Convert the comma-separated CORS origins string into a list.
        This makes it easier to configure multiple origins.
        """
        return [origin.strip() for origin in self.cors_origins.split(",")]


# We use lru_cache to create a singleton - settings are loaded once and reused
# This is a common pattern in FastAPI applications
@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings singleton.
    
    Using lru_cache ensures we only load settings once, even if this
    function is called multiple times. This improves performance
    and ensures consistency across the application.
    
    Returns:
        Settings: The application configuration object
    """
    return Settings()
