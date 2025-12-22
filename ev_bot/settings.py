from typing import Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Amadeus API settings and configuration
    base_url: str = Field(
        "https://test.api.amadeus.com/v1",
        description="Base URL for Amadeus API endpoints"
    )
    auth_url: str = Field(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        description="URL for authentication endpoint"
    )

    client_id: Optional[str] = Field(None, alias="AMADEUS_CLIENT_ID")
    client_secret: Optional[str] = Field(None, alias="AMADEUS_CLIENT_SECRET")

    # TravelPayouts API settings
    travelpayouts_token: Optional[str] = Field(None, alias="TRAVELPAYOUTS_TOKEN")
    travelpayouts_marker: Optional[str] = Field(None, alias="TRAVELPAYOUTS_MARKER")

    # OpenAI API Key
    openai_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    
    # Telegram Settings
    telegram_bot_token: Optional[str] = Field(None, alias="TELEGRAM_BOT_TOKEN")
    telegram_channel_id: Optional[str] = Field(None, alias="TELEGRAM_CHANNEL_ID")

    # Default Location
    origin: str = Field(
        "MAD",
        description="Default origin location for flight searches",
        alias="ORIGIN"
    )

    # Language and Currency
    language: Optional[str] = Field(
        None,
        alias="LANGUAGE",
        description="Preferred language for message texts"
    )

    currency: Optional[str] = Field(
        "EUR",
        alias="CURRENCY",
        description="Currency for API responses"
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
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create a global settings instance
settings = Settings()
