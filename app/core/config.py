from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings and configuration."""

    # App
    APP_NAME: str = "Social Automation SaaS"
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # OpenRouter (Alternative AI provider)
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    USE_OPENROUTER: bool = False  # Set to True to use OpenRouter instead of OpenAI

    # AWS S3
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str | None = None

    # Google APIs
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None

    # Meta/Facebook
    META_APP_ID: str | None = None
    META_APP_SECRET: str | None = None

    # LinkedIn
    LINKEDIN_CLIENT_ID: str | None = None
    LINKEDIN_CLIENT_SECRET: str | None = None

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Email
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    FROM_EMAIL: str | None = None

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Placid (image generation - primary)
    PLACID_API_KEY: str | None = None
    PLACID_TEMPLATE_ID: str | None = None

    # Fal AI (image generation - backup)
    FAL_API_KEY: str | None = None

    # Publer (social media publishing)
    PUBLER_API_KEY: str | None = None
    PUBLER_WORKSPACE_ID: str | None = None
    PUBLER_BASE_URL: str = "https://app.publer.com/api/v1"

    # Google Sheets logging
    GOOGLE_SHEETS_ID: str | None = None
    GOOGLE_SERVICE_ACCOUNT_JSON: str | None = None  # JSON string for service account creds

    # Gemini AI (via OpenRouter)
    GEMINI_MODEL: str = "google/gemini-pro-1.5"
    USE_GEMINI: bool = False  # Use Gemini instead of OpenAI/Claude for content generation

    # Content Polisher (via OpenRouter)
    POLISHER_MODEL: str = "openai/gpt-4-turbo-preview"  # GPT-4 for post-polishing via OpenRouter

    # Approvals
    TEAM_APPROVAL_EMAIL: str | None = None

    # Retry Configuration
    RETRY_DELAY_SECONDS: int = 15  # Delay between retry attempts
    MAX_RETRY_ATTEMPTS: int = 3  # Maximum number of retry attempts

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
