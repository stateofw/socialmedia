from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.content import ContentStatus, ContentType


class ContentBase(BaseModel):
    """Base schema for content."""
    topic: str = Field(..., min_length=1, max_length=500)
    content_type: ContentType = ContentType.OTHER
    notes: Optional[str] = None
    focus_location: Optional[str] = None
    platforms: List[str] = Field(default_factory=list)


class ContentCreate(ContentBase):
    """Schema for creating content via intake form."""
    client_id: int
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None


class ContentUpdate(BaseModel):
    """Schema for updating content."""
    topic: Optional[str] = None
    content_type: Optional[ContentType] = None
    notes: Optional[str] = None
    focus_location: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    cta: Optional[str] = None
    status: Optional[ContentStatus] = None
    scheduled_at: Optional[datetime] = None
    platforms: Optional[List[str]] = None


class ContentResponse(ContentBase):
    """Schema for content response."""
    id: int
    client_id: int
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    cta: Optional[str] = None
    blog_title: Optional[str] = None
    blog_url: Optional[str] = None
    media_urls: Optional[List[str]] = None
    status: ContentStatus
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContentIntakeForm(BaseModel):
    """Schema for client intake form (simplified)."""
    business_name: str  # Used to lookup client
    topic: Optional[str] = None  # Optional - will be generated from images if not provided
    content_type: Optional[ContentType] = ContentType.OTHER  # Optional - will be inferred from images
    focus_location: Optional[str] = None  # Optional - will use client default if not provided
    notes: Optional[str] = None
    auto_post: bool = False
    media_urls: Optional[List[str]] = None


class ContentRejection(BaseModel):
    """Schema for rejecting content with feedback."""
    rejection_reason: str = Field(..., min_length=10, max_length=1000, description="Reason for rejection with improvement suggestions")
    regenerate: bool = Field(default=True, description="Whether to automatically regenerate content with feedback")
