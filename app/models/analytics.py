from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PostAnalytics(Base):
    """Analytics data for published posts."""

    __tablename__ = "post_analytics"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    platform = Column(String, nullable=False)  # "facebook", "instagram", etc.

    # Engagement Metrics
    impressions = Column(Integer, default=0)  # How many people saw the post
    reach = Column(Integer, default=0)  # Unique viewers
    engagement = Column(Integer, default=0)  # Total interactions
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    clicks = Column(Integer, default=0)  # Link clicks

    # Calculated Metrics
    engagement_rate = Column(Float, default=0.0)  # engagement / reach * 100

    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
