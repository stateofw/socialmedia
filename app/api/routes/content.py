from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.content import Content, ContentStatus
from app.models.client import Client
from app.schemas.content import ContentCreate, ContentUpdate, ContentResponse, ContentRejection
from app.services.ai import ai_service

# Optional Celery import for queuing publish task
try:
    from app.tasks.posting_tasks import publish_content_task, _publish_content
    HAS_CELERY = True
except Exception:
    HAS_CELERY = False

router = APIRouter()


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create new content and generate AI caption."""

    # Verify client exists
    result = await db.execute(select(Client).where(Client.id == content_data.client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check monthly post limit
    if client.posts_this_month >= client.monthly_post_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Monthly post limit reached ({client.monthly_post_limit})",
        )

    # Create content record
    content = Content(**content_data.model_dump())
    db.add(content)
    await db.commit()
    await db.refresh(content)

    # Generate AI content in background
    background_tasks.add_task(
        generate_ai_content,
        content_id=content.id,
        client=client,
    )

    return content


@router.get("/", response_model=List[ContentResponse])
async def list_content(
    client_id: int | None = None,
    status_filter: ContentStatus | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all content with optional filters."""

    query = select(Content)

    if client_id:
        query = query.where(Content.client_id == client_id)

    if status_filter:
        query = query.where(Content.status == status_filter)

    query = query.offset(skip).limit(limit).order_by(Content.created_at.desc())

    result = await db.execute(query)
    contents = result.scalars().all()

    return contents


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get specific content by ID."""

    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    return content


@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    content_data: ContentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update content."""

    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Update fields
    for field, value in content_data.model_dump(exclude_unset=True).items():
        setattr(content, field, value)

    await db.commit()
    await db.refresh(content)

    return content


@router.post("/{content_id}/approve", response_model=ContentResponse)
async def approve_content(
    content_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Approve content and schedule for posting."""

    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    content.status = ContentStatus.APPROVED
    content.rejection_reason = None  # Clear any previous rejection

    # Enqueue publish job via Celery if available; else run in background
    try:
        if HAS_CELERY:
            publish_content_task.delay(content.id)
        else:
            background_tasks.add_task(_publish_content, content.id)
    except Exception:
        # Fallback to background task on any failure
        background_tasks.add_task(_publish_content, content.id)

    await db.commit()
    await db.refresh(content)

    return content


@router.post("/{content_id}/reject", response_model=ContentResponse)
async def reject_content(
    content_id: int,
    rejection_data: ContentRejection,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Reject content with feedback and optionally regenerate with improvements.

    This implements the retry with feedback loop from the workflow:
    - Marks content as REJECTED
    - Stores rejection reason
    - If regenerate=True, automatically creates improved version
    """

    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Update status and store rejection reason
    content.status = ContentStatus.REJECTED
    content.rejection_reason = rejection_data.rejection_reason
    content.retry_count += 1

    await db.commit()
    await db.refresh(content)

    # If regenerate requested, trigger AI regeneration with feedback
    if rejection_data.regenerate:
        # Get client for context
        client_result = await db.execute(select(Client).where(Client.id == content.client_id))
        client = client_result.scalar_one_or_none()

        if client:
            background_tasks.add_task(
                regenerate_content_with_feedback,
                content_id=content.id,
                client=client,
                feedback=rejection_data.rejection_reason,
            )

    return content


async def generate_ai_content(content_id: int, client: Client):
    """Background task to generate AI content."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Content).where(Content.id == content_id))
        content = result.scalar_one_or_none()

        if not content:
            return

        try:
            # Generate social post
            ai_result = await ai_service.generate_social_post(
                business_name=client.business_name,
                industry=client.industry or "local business",
                topic=content.topic,
                location=content.focus_location or client.service_area or f"{client.city}, {client.state}",
                content_type=content.content_type.value,
                brand_voice=client.brand_voice,
                notes=content.notes,
            )

            # Update content with AI-generated data
            content.caption = ai_result["caption"]
            content.hashtags = ai_result["hashtags"]
            content.cta = ai_result["cta"]
            content.status = ContentStatus.PENDING_APPROVAL
            content.ai_model_used = "gpt-4-turbo-preview"

            await db.commit()

        except Exception as e:
            content.status = ContentStatus.FAILED
            content.error_message = str(e)
            await db.commit()


async def regenerate_content_with_feedback(
    content_id: int,
    client: Client,
    feedback: str,
):
    """
    Background task to regenerate AI content with rejection feedback.

    This implements the retry with improvement loop:
    - Takes rejection feedback
    - Incorporates it into the AI prompt
    - Generates improved content
    - Updates status to PENDING_APPROVAL for re-review
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Content).where(Content.id == content_id))
        content = result.scalar_one_or_none()

        if not content:
            return

        # Update status to RETRYING while regenerating
        content.status = ContentStatus.RETRYING
        await db.commit()

        try:
            # Build enhanced notes with feedback
            enhanced_notes = f"""
Previous version feedback: {feedback}

Please address the feedback above and improve the content.
"""
            if content.notes:
                enhanced_notes += f"\nOriginal notes: {content.notes}"

            # Generate improved social post with feedback incorporated
            ai_result = await ai_service.generate_social_post(
                business_name=client.business_name,
                industry=client.industry or "local business",
                topic=content.topic,
                location=content.focus_location or client.service_area or f"{client.city}, {client.state}",
                content_type=content.content_type.value,
                brand_voice=client.brand_voice,
                notes=enhanced_notes,
            )

            # Update content with improved AI-generated data
            content.caption = ai_result["caption"]
            content.hashtags = ai_result["hashtags"]
            content.cta = ai_result["cta"]
            content.status = ContentStatus.PENDING_APPROVAL
            content.ai_model_used = "gpt-4-turbo-preview"

            # Generate platform-specific variations
            if content.platforms:
                platform_variations = await ai_service.generate_platform_variations(
                    base_caption=content.caption,
                    hashtags=content.hashtags,
                    cta=content.cta,
                    business_name=client.business_name,
                    location=content.focus_location or client.service_area or f"{client.city}, {client.state}",
                    platforms=content.platforms,
                )
                content.platform_captions = platform_variations

            await db.commit()

            print(f"✅ Regenerated content {content_id} with feedback")

        except Exception as e:
            content.status = ContentStatus.FAILED
            content.error_message = f"Regeneration failed: {str(e)}"
            await db.commit()
            print(f"❌ Failed to regenerate content {content_id}: {str(e)}")
