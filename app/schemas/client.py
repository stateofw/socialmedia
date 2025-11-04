from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime


class ClientBase(BaseModel):
    """Base schema for client."""
    business_name: str = Field(..., min_length=1, max_length=200)
    industry: Optional[str] = None
    website_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    service_area: Optional[str] = None


class ClientCreate(ClientBase):
    """Schema for creating a new client."""
    monthly_post_limit: int = Field(default=8, ge=1, le=100)
    auto_post: bool = False
    content_generation_preference: str = Field(
        default="own_media",
        description="Content generation preference: own_media, auto_generate, or mixed"
    )
    brand_voice: Optional[str] = None
    tone_preference: str = Field(default="professional", description="professional, friendly, or local_expert")
    platforms_enabled: List[str] = Field(default_factory=list)

    # PRD fields
    promotions_offers: Optional[str] = None
    off_limits_topics: Optional[List[str]] = None
    reuse_media: bool = True
    media_folder_url: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    backup_contact_name: Optional[str] = None
    backup_contact_email: Optional[str] = None

    # Publer multi-workspace
    publer_workspace_id: Optional[str] = None
    publer_api_key: Optional[str] = None

    # Placid image generation
    placid_template_id: Optional[str] = None


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    business_name: Optional[str] = None
    industry: Optional[str] = None
    website_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    service_area: Optional[str] = None
    monthly_post_limit: Optional[int] = Field(default=None, ge=1, le=100)
    auto_post: Optional[bool] = None
    content_generation_preference: Optional[str] = None
    brand_voice: Optional[str] = None
    tone_preference: Optional[str] = None
    brand_colors: Optional[Dict[str, str]] = None
    logo_url: Optional[str] = None
    platforms_enabled: Optional[List[str]] = None
    is_active: Optional[bool] = None

    # PRD fields
    promotions_offers: Optional[str] = None
    off_limits_topics: Optional[List[str]] = None
    reuse_media: Optional[bool] = None
    media_folder_url: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    backup_contact_name: Optional[str] = None
    backup_contact_email: Optional[str] = None

    # Publer multi-workspace
    publer_workspace_id: Optional[str] = None
    publer_api_key: Optional[str] = None

    # Placid image generation
    placid_template_id: Optional[str] = None


class ClientResponse(ClientBase):
    """Schema for client response."""
    id: int
    intake_token: Optional[str] = None  # Unique token for intake form URL
    monthly_post_limit: int
    posts_this_month: int
    auto_post: bool
    content_generation_preference: Optional[str] = None
    brand_voice: Optional[str] = None
    tone_preference: Optional[str] = None
    brand_colors: Optional[Dict[str, str]] = None
    logo_url: Optional[str] = None
    platforms_enabled: Optional[List[str]] = None
    is_active: bool

    # PRD fields
    promotions_offers: Optional[str] = None
    off_limits_topics: Optional[List[str]] = None
    reuse_media: Optional[bool] = None
    media_folder_url: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    backup_contact_name: Optional[str] = None
    backup_contact_email: Optional[str] = None

    # Publer multi-workspace
    publer_workspace_id: Optional[str] = None
    publer_api_key: Optional[str] = None

    # Placid image generation
    placid_template_id: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClientSetPassword(BaseModel):
    """Schema for setting client portal password."""
    password: str = Field(..., min_length=8, max_length=100)


class ClientLogin(BaseModel):
    """Schema for client login."""
    business_name: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ClientPortalResponse(BaseModel):
    """Schema for client portal dashboard data."""
    id: int
    business_name: str
    industry: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    service_area: Optional[str] = None
    monthly_post_limit: int
    posts_this_month: int
    posts_remaining: int
    content_generation_preference: Optional[str] = None
    platforms_enabled: Optional[List[str]] = None
    publer_account_ids: Optional[List[str]] = None
    is_active: bool
    intake_form_url: Optional[str] = None

    class Config:
        from_attributes = True
