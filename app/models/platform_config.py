from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PlatformConfig(Base):
    """Platform configuration - stores API credentials and settings for each client's platforms."""

    __tablename__ = "platform_configs"

    id = Column(Integer, primary_key=True, index=True)

    # Client relationship
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    client = relationship("Client", back_populates="platform_configs")

    # Platform
    platform = Column(String, nullable=False)  # "facebook", "instagram", "google_business", "linkedin", "wordpress"

    # Authentication
    access_token = Column(String)  # Encrypted in production
    refresh_token = Column(String)
    token_expires_at = Column(DateTime(timezone=True))

    # Platform-specific IDs
    platform_user_id = Column(String)  # Facebook Page ID, Google Business Location ID, etc.
    platform_account_name = Column(String)

    # Additional Config
    config = Column(JSON)  # Platform-specific settings
    # Example for WordPress: {"site_url": "https://example.com", "username": "api_user"}
    # Example for Google Business: {"location_id": "123456"}

    # Status
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
