from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class ClientSignup(Base):
    """Model for client signup requests before onboarding."""

    __tablename__ = "client_signups"

    id = Column(Integer, primary_key=True, index=True)

    # Contact Information
    email = Column(String, nullable=False, index=True)
    business_name = Column(String, nullable=False, index=True)
    contact_person_name = Column(String)
    contact_person_email = Column(String)
    contact_person_phone = Column(String)

    # Business Details
    business_industry = Column(JSON)  # List of selected industries
    business_website = Column(String)
    preferred_platforms = Column(JSON)  # List of selected platforms
    additional_notes = Column(Text)

    # Media files
    media_urls = Column(JSON)  # List of uploaded media URLs

    # Status tracking
    status = Column(String, default="pending")  # pending, approved, rejected, onboarded
    admin_notes = Column(Text)  # Internal notes from admin
    onboarded_client_id = Column(Integer)  # Link to created client after onboarding

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<ClientSignup(id={self.id}, business_name='{self.business_name}', status='{self.status}')>"
