from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.content import Content, ContentType, ContentStatus
from app.models.client import Client
from app.services.classifier import classify_platforms
from app.services.email import email_service


router = APIRouter()


class WebhookPayload(BaseModel):
    client_id: int = Field(..., description="Target client ID")
    topic: str = Field(..., description="Topic for the post")
    content: Optional[str] = Field(None, description="Optional draft content/caption")
    platforms: Optional[List[str]] = Field(None, description="Target platforms")
    platform: Optional[str] = Field(None, description="Single platform variant")
    image_urls: Optional[List[str]] = Field(None, description="Image/Video URLs")
    content_type: Optional[ContentType] = ContentType.OTHER
    focus_location: Optional[str] = None
    notes: Optional[str] = None


@router.post("/content-intake", status_code=status.HTTP_202_ACCEPTED)
async def content_intake_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook to receive raw content and trigger the automation workflow.

    Steps:
    - Classify platforms (if not explicitly provided)
    - Create Content record
    - Trigger AI generation (caption + per-platform variations)
    - Send approval email to team (if configured)
    """
    # Ensure client exists
    result = await db.execute(select(Client).where(Client.id == payload.client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Classify platforms
    platforms = payload.platforms or ([payload.platform] if payload.platform else None) or []
    platforms = classify_platforms({
        "platforms": platforms,
        "platform": payload.platform,
        "topic": payload.topic,
        "content": payload.content,
    })

    # Create content
    content = Content(
        client_id=payload.client_id,
        topic=payload.topic,
        content_type=payload.content_type,
        notes=payload.notes,
        focus_location=payload.focus_location,
        media_urls=payload.image_urls or [],
        platforms=platforms,
        status=ContentStatus.DRAFT,
        caption=payload.content or None,
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)

    # Trigger AI generation in background
    background_tasks.add_task(_generate_and_notify, content.id, client.business_name, payload.topic)

    return {"accepted": True, "content_id": content.id, "platforms": platforms}


async def _generate_and_notify(content_id: int, client_name: str, topic: str):
    """Generate AI content (including platform variants) and notify approver."""
    from app.tasks.content_tasks import _generate_content  # reuse existing async impl
    await _generate_content(content_id)

    # Email approval if configured
    from app.core.config import settings
    if settings.TEAM_APPROVAL_EMAIL:
        try:
            # Send a concise preview
            await email_service.notify_content_ready_for_review(
                team_email=settings.TEAM_APPROVAL_EMAIL,
                client_name=client_name,
                content_id=content_id,
                topic=topic,
                caption_preview=f"AI-generated content ready for review",
            )
        except Exception as e:
            print(f"⚠️ Approval email failed: {e}")

