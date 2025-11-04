from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import secrets


class Client(Base):
    """Client/Business model."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    business_name = Column(String, nullable=False, index=True)
    industry = Column(String)  # e.g., "landscaping", "HVAC", "roofing"
    website_url = Column(String)

    # Intake Form Token (unique URL for client)
    intake_token = Column(String, unique=True, index=True)

    # Location (for SEO)
    city = Column(String)
    state = Column(String)
    service_area = Column(String)  # e.g., "Brewster, NY", "Putnam County"

    # Plan Details
    monthly_post_limit = Column(Integer, default=8)
    posts_this_month = Column(Integer, default=0)

    # Settings
    auto_post = Column(Boolean, default=False)  # Auto-post or require approval
    generate_blog = Column(Boolean, default=False)  # Auto-generate blog posts from social content
    content_generation_preference = Column(String, default="own_media")  # own_media, auto_generate, or mixed
    brand_voice = Column(Text)  # Custom tone/voice instructions
    tone_preference = Column(String, default="professional")  # professional, friendly, local_expert
    brand_colors = Column(JSON)  # {"primary": "#hex", "secondary": "#hex"}
    logo_url = Column(String)
    placid_template_id = Column(String)  # Client-specific Placid template for branded images

    # Content Preferences (PRD fields)
    promotions_offers = Column(Text)  # Current promotions/offers to highlight
    off_limits_topics = Column(JSON)  # List of topics to avoid
    reuse_media = Column(Boolean, default=True)  # Allow media recycling
    media_folder_url = Column(String)  # Link to client's media folder (Drive, Dropbox, etc)

    # Contact Information
    primary_contact_name = Column(String)
    primary_contact_email = Column(String)
    primary_contact_phone = Column(String)
    backup_contact_name = Column(String)
    backup_contact_email = Column(String)

    # Platforms
    platforms_enabled = Column(JSON)  # ["facebook", "instagram", "google_business", "linkedin"]

    # Publer Multi-Workspace Support
    publer_workspace_id = Column(String)  # Override default workspace for this client
    publer_api_key = Column(String)  # Optional: client-specific API key
    publer_account_ids = Column(JSON)  # List of Publer account IDs for this client ["68ff8b28dbe5ada5b0944612", ...]

    # Status
    is_active = Column(Boolean, default=True)

    # Client Portal Authentication
    password_hash = Column(String)  # Hashed password for client portal login
    last_login = Column(DateTime(timezone=True))  # Track last portal login

    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="clients")

    contents = relationship("Content", back_populates="client", cascade="all, delete-orphan")
    platform_configs = relationship("PlatformConfig", back_populates="client", cascade="all, delete-orphan")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
