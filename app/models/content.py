from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class ContentStatus(str, enum.Enum):
    """Status of content in the workflow."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"  # Content rejected by approver
    RETRYING = "RETRYING"  # Content being regenerated after rejection
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class ContentType(str, enum.Enum):
    """Type of content/post."""
    BEFORE_AFTER = "BEFORE_AFTER"
    TESTIMONIAL = "TESTIMONIAL"
    OFFER = "OFFER"
    TIP = "TIP"
    TEAM_UPDATE = "TEAM_UPDATE"
    PROJECT_SHOWCASE = "PROJECT_SHOWCASE"
    SEASONAL = "SEASONAL"
    OTHER = "OTHER"


class Content(Base):
    """Content/Post model - represents a social media post or blog."""

    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)

    # Client relationship
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    client = relationship("Client", back_populates="contents")

    # Content Details
    topic = Column(String, nullable=False)
    content_type = Column(Enum(ContentType), default=ContentType.OTHER)
    notes = Column(Text)  # Client's special instructions

    # Location (for local SEO)
    focus_location = Column(String)  # e.g., "Brewster, NY"

    # AI-Generated Content
    caption = Column(Text)  # Base social media caption
    hashtags = Column(JSON)  # List of hashtags
    cta = Column(String)  # Call-to-action

    # Per-platform caption variations
    platform_captions = Column(JSON)  # {"facebook": "caption", "instagram": "caption", etc.}

    # Blog content (if generating blog)
    blog_title = Column(String)
    blog_content = Column(Text)
    blog_meta_title = Column(String)
    blog_meta_description = Column(String)
    blog_url = Column(String)  # WordPress post URL after publishing

    # Media
    media_urls = Column(JSON)  # List of image/video URLs
    media_type = Column(String)  # "image", "video", "carousel"

    # Platforms
    platforms = Column(JSON)  # ["facebook", "instagram", "google_business"]
    platform_post_ids = Column(JSON)  # {"facebook": "post_id", "instagram": "post_id"}

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True))
    published_at = Column(DateTime(timezone=True))

    # Status & Workflow
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT)
    error_message = Column(Text)  # If failed, why?
    retry_count = Column(Integer, default=0)  # Number of retry attempts
    rejection_reason = Column(Text)  # Reason for rejection if status is REJECTED

    # AI Metadata
    ai_model_used = Column(String)  # e.g., "gpt-4-turbo-preview"
    ai_prompt_version = Column(String)  # Track which prompt version was used

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
