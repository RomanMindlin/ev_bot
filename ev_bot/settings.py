from typing import Optional
from pydantic import BaseSettings, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AmadeusSettings(BaseSettings):
    """Amadeus API settings and configuration."""
    
    # API Credentials
    client_id: Optional[str] = Field(None, env="AMADEUS_CLIENT_ID")
    client_secret: Optional[str] = Field(None, env="AMADEUS_CLIENT_SECRET")
    openai_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Telegram Settings
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_channel_id: Optional[str] = Field(None, env="TELEGRAM_CHANNEL_ID")
    
    # Default Location
    origin: str = Field(
        "NYC",
        description="Default origin location for flight searches"
    )
    
    # API URLs
    base_url: str = Field(
        "https://test.api.amadeus.com/v2",
        description="Base URL for Amadeus API endpoints"
    )
    auth_url: str = Field(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        description="URL for authentication endpoint"
    )
    
    # Retry Configuration
    max_retries: int = Field(
        3,
        description="Maximum number of retry attempts for API calls"
    )
    min_wait: int = Field(
        1,
        description="Minimum wait time between retries in seconds"
    )
    max_wait: int = Field(
        10,
        description="Maximum wait time between retries in seconds"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create a global settings instance
settings = AmadeusSettings() 