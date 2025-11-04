"""
Client Portal API Routes

Authenticated routes for clients to access their own data only.
Clients log in with business_name + password and can view/manage their content.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_client
from app.models.client import Client
from app.models.content import Content, ContentStatus
from app.schemas.client import ClientLogin, ClientPortalResponse
from app.schemas.user import Token
from app.schemas.content import ContentResponse

router = APIRouter()


class ContentPreferenceUpdate(BaseModel):
    """Schema for updating content generation preference."""
    content_generation_preference: str  # own_media, auto_generate, or mixed


@router.post("/login", response_model=Token)
async def client_login(
    login_data: ClientLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Client portal login with business name and password.
    Returns JWT token with client_id claim.
    """
    # Find client by business name
    result = await db.execute(
        select(Client).where(Client.business_name == login_data.business_name)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid business name or password",
        )

    # Check if password is set
    if not client.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portal access not set up. Please contact support to set your password.",
        )

    # Verify password
    if not verify_password(login_data.password, client.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid business name or password",
        )

    # Check if client is active
    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please contact support.",
        )

    # Update last login timestamp
    client.last_login = datetime.utcnow()
    await db.commit()

    # Create access token with client_id claim (not 'sub')
    access_token = create_access_token(data={"client_id": client.id})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=ClientPortalResponse)
async def get_client_info(
    client: Client = Depends(get_current_client),
):
    """
    Get current client information for portal dashboard.
    """
    return {
        "id": client.id,
        "business_name": client.business_name,
        "industry": client.industry,
        "city": client.city,
        "state": client.state,
        "service_area": client.service_area,
        "monthly_post_limit": client.monthly_post_limit,
        "posts_this_month": client.posts_this_month,
        "posts_remaining": client.monthly_post_limit - client.posts_this_month,
        "content_generation_preference": client.content_generation_preference,
        "platforms_enabled": client.platforms_enabled,
        "publer_account_ids": client.publer_account_ids,
        "is_active": client.is_active,
        "intake_form_url": f"/api/v1/intake/{client.intake_token}/form" if client.intake_token else None,
    }


@router.patch("/content-preference")
async def update_content_preference(
    preference: ContentPreferenceUpdate,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Update client's content generation preference.

    Options:
    - own_media: Client will upload their own photos/videos
    - auto_generate: System will auto-generate content with AI + Placid
    - mixed: Client can do both (flexible approach)
    """
    valid_preferences = ["own_media", "auto_generate", "mixed"]

    if preference.content_generation_preference not in valid_preferences:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preference. Must be one of: {', '.join(valid_preferences)}"
        )

    client.content_generation_preference = preference.content_generation_preference
    await db.commit()

    return {
        "message": "Content generation preference updated successfully",
        "preference": client.content_generation_preference,
        "description": {
            "own_media": "You'll upload your own photos and videos for posts",
            "auto_generate": "We'll automatically create posts with AI-generated text and branded images",
            "mixed": "You can upload media or let us auto-generate content as needed"
        }.get(client.content_generation_preference)
    }


@router.get("/content", response_model=List[ContentResponse])
async def list_my_content(
    skip: int = 0,
    limit: int = 50,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    List all content for the authenticated client only.
    Clients can only see their own content.
    """
    result = await db.execute(
        select(Content)
        .where(Content.client_id == client.id)
        .order_by(Content.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    content_list = result.scalars().all()

    return content_list


@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_my_content(
    content_id: int,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Get specific content item.
    Clients can only access their own content.
    """
    result = await db.execute(
        select(Content).where(
            Content.id == content_id,
            Content.client_id == client.id,  # Ensure client owns this content
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    return content


@router.get("/stats")
async def get_my_stats(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics for the authenticated client.
    """
    # Count content by status
    result = await db.execute(
        select(Content).where(Content.client_id == client.id)
    )
    all_content = result.scalars().all()

    stats = {
        "total_posts": len(all_content),
        "posts_this_month": client.posts_this_month,
        "posts_remaining": client.monthly_post_limit - client.posts_this_month,
        "monthly_limit": client.monthly_post_limit,
        "by_status": {},
        "platforms": client.platforms_enabled or [],
        "publer_accounts_connected": len(client.publer_account_ids or []),
    }

    # Count by status
    for content in all_content:
        status_key = content.status.value
        stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1

    return stats


# Pydantic schemas for new endpoints
class ContentSubmission(BaseModel):
    """Schema for client content submission."""
    topic: Optional[str] = None
    content_type: Optional[str] = None
    notes: Optional[str] = None
    media_urls: Optional[List[str]] = []


class RescheduleRequest(BaseModel):
    """Schema for rescheduling a post."""
    new_scheduled_time: datetime


@router.post("/media/upload")
async def upload_client_media(
    files: List[UploadFile] = File(...),
    client: Client = Depends(get_current_client),
):
    """
    Upload media files from client portal.
    Clients can upload images/videos anytime for future posts.
    """
    from pathlib import Path
    import secrets

    # Use same upload logic as intake form
    MEDIA_DIR = Path("media/clients") / str(client.id)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    uploaded_urls = []

    try:
        for file in files:
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type {file_ext} not allowed"
                )

            # Read and validate size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} exceeds 10MB limit"
                )

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = secrets.token_hex(4)
            unique_filename = f"{timestamp}_{random_suffix}{file_ext}"

            # Save file
            file_path = MEDIA_DIR / unique_filename
            with open(file_path, "wb") as f:
                f.write(content)

            # Generate URL
            file_url = f"/media/clients/{client.id}/{unique_filename}"
            uploaded_urls.append(file_url)

            print(f"✅ Client {client.business_name} uploaded: {file.filename} → {file_url}")

    except Exception as e:
        # Cleanup on error
        for url in uploaded_urls:
            try:
                Path(url.lstrip('/')).unlink()
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": f"Successfully uploaded {len(files)} file(s)",
        "media_urls": uploaded_urls,
        "count": len(uploaded_urls)
    }


@router.post("/content/submit")
async def submit_new_content(
    submission: ContentSubmission,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Client can submit new content anytime from their portal.
    Similar to intake form but authenticated via portal login.

    If no media_urls provided, will automatically generate content using AI + Placid.
    """
    import asyncio
    from app.services.ai import ai_service
    from app.services.auto_content_generator import auto_content_generator
    from app.api.routes.intake import generate_and_process_content, background_tasks_set

    # Check monthly limit
    if client.posts_this_month >= client.monthly_post_limit:
        raise HTTPException(
            status_code=400,
            detail=f"You've reached your monthly post limit of {client.monthly_post_limit} posts."
        )

    # Determine content generation strategy
    topic = submission.topic
    content_type = submission.content_type
    focus_location = client.service_area or f"{client.city}, {client.state}"
    media_urls = submission.media_urls or []
    use_auto_generation = False

    # Case 1: No media provided OR images have been reused too much
    if not media_urls or len(media_urls) == 0:
        # Check if we should auto-generate
        has_fresh_images = await auto_content_generator.has_fresh_images(
            client_id=client.id,
            db=db,
            max_uses=3,  # Images can be used max 3 times
        )

        if not has_fresh_images:
            print(f"🤖 Auto-generating content for {client.business_name} (no fresh media available)")
            use_auto_generation = True

    # Case 2: No topic and no media - definitely auto-generate
    if not topic and not media_urls:
        print(f"🤖 Auto-generating content for {client.business_name} (no topic or media provided)")
        use_auto_generation = True

    # AUTO-GENERATE: Complete post with AI text + Placid image
    if use_auto_generation:
        print(f"🚀 Starting auto-generation for {client.business_name}")

        # Generate complete post
        from app.models.content import ContentType as ContentTypeEnum
        content_type_enum = ContentTypeEnum(content_type) if content_type else ContentTypeEnum.OTHER

        generated = await auto_content_generator.generate_complete_post(
            client=client,
            topic=topic,  # Use provided topic if available
            content_type=content_type_enum if content_type else None,
        )

        if generated.get("status") == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Auto-generation failed: {generated.get('error')}"
            )

        # Create content with generated data
        content = Content(
            client_id=client.id,
            topic=generated["topic"],
            content_type=content_type_enum,
            focus_location=focus_location,
            notes=f"[AUTO-GENERATED] {submission.notes or ''}",
            caption=generated["caption"],
            hashtags=generated["hashtags"],
            cta=generated["cta"],
            platform_captions=generated["platform_captions"],
            media_urls=generated["media_urls"],
            media_type=generated["media_type"],
            platforms=client.platforms_enabled or [],
            status=ContentStatus.PENDING_APPROVAL,  # Ready for review
        )

        db.add(content)
        await db.commit()
        await db.refresh(content)

        return {
            "message": "Content auto-generated successfully using AI + Placid! Ready for your review.",
            "content_id": content.id,
            "status": "pending_approval",
            "auto_generated": True,
        }

    # MANUAL: Image-only submissions (analyze image for topic)
    elif not topic and media_urls and len(media_urls) > 0:
        # Analyze image to generate topic
        image_url = media_urls[0]
        if image_url.startswith('/'):
            import os
            base_url = os.getenv('BASE_URL', 'http://localhost:8000')
            image_url = f"{base_url}{image_url}"

        print(f"🖼️ Analyzing image for {client.business_name}: {image_url}")

        image_analysis = await ai_service.analyze_image_for_post(
            image_url=image_url,
            business_name=client.business_name,
            industry=client.industry or "local business",
            location=focus_location,
            notes=submission.notes,
        )

        topic = image_analysis.get("topic", "Recent project showcase")
        content_type = image_analysis.get("content_type", "project_showcase")

        print(f"✅ Generated topic: {topic}")

    # MANUAL: Topic + optional media provided
    elif not topic:
        raise HTTPException(
            status_code=400,
            detail="Please provide either a topic or upload at least one image"
        )

    # Create content record for manual submissions
    from app.models.content import ContentType as ContentTypeEnum
    try:
        content_type_enum = ContentTypeEnum(content_type) if content_type else ContentTypeEnum.OTHER
    except:
        content_type_enum = ContentTypeEnum.OTHER

    content = Content(
        client_id=client.id,
        topic=topic,
        content_type=content_type_enum,
        focus_location=focus_location,
        notes=submission.notes,
        media_urls=media_urls,
        platforms=client.platforms_enabled or [],
        status=ContentStatus.DRAFT,
    )

    db.add(content)
    await db.commit()
    await db.refresh(content)

    # Generate AI content in background
    task = asyncio.create_task(
        generate_and_process_content(
            content_id=content.id,
            client_id=client.id,
            auto_post=False,  # Always require approval
        )
    )
    background_tasks_set.add(task)
    task.add_done_callback(background_tasks_set.discard)

    return {
        "message": "Content submitted successfully! We'll generate your post shortly.",
        "content_id": content.id,
        "status": "processing",
    }


@router.get("/scheduled-posts")
async def get_scheduled_posts(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    View all scheduled posts for this client.
    Shows approved and scheduled posts with their scheduled times.
    """
    # Get scheduled and approved posts
    result = await db.execute(
        select(Content).where(
            and_(
                Content.client_id == client.id,
                Content.status.in_([ContentStatus.SCHEDULED, ContentStatus.APPROVED])
            )
        ).order_by(Content.scheduled_at.asc())
    )
    posts = result.scalars().all()

    scheduled_posts = []
    for post in posts:
        scheduled_posts.append({
            "id": post.id,
            "topic": post.topic,
            "caption": post.caption,
            "status": post.status.value,
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "platforms": post.platforms,
            "media_urls": post.media_urls,
            "can_reschedule": post.status == ContentStatus.SCHEDULED,
        })

    return {
        "total_scheduled": len(scheduled_posts),
        "posts": scheduled_posts,
        "monthly_posts_used": client.posts_this_month,
        "monthly_limit": client.monthly_post_limit,
    }


@router.patch("/content/{content_id}/reschedule")
async def reschedule_post(
    content_id: int,
    reschedule_data: RescheduleRequest,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Reschedule a post to a different time.
    Only works for SCHEDULED posts (not yet published).
    Updates both local database AND Publer schedule.
    """
    from app.services.publer import PublerService

    # Get content and verify ownership
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    if content.client_id != client.id:
        raise HTTPException(status_code=403, detail="Not your content")

    if content.status != ContentStatus.SCHEDULED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only reschedule SCHEDULED posts. This post is {content.status.value}"
        )

    # Validate new time is in the future
    if reschedule_data.new_scheduled_time <= datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="New scheduled time must be in the future"
        )

    # Update Publer schedule if post has been scheduled there
    publer_errors = []
    if content.platform_post_ids:
        publer_service = PublerService()

        # Update each platform post in Publer
        for platform, post_id in content.platform_post_ids.items():
            result = await publer_service.update_post_schedule(
                post_id=post_id,
                new_scheduled_time=reschedule_data.new_scheduled_time,
                workspace_id=client.publer_workspace_id,
            )

            if result.get("status") != "success":
                error_msg = result.get("error", "Unknown error")
                publer_errors.append(f"{platform}: {error_msg}")
                print(f"⚠️ Failed to update {platform} post {post_id} in Publer: {error_msg}")

    # If Publer updates failed, return error
    if publer_errors:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update Publer schedule: {'; '.join(publer_errors)}"
        )

    # Update local database
    old_time = content.scheduled_at
    content.scheduled_at = reschedule_data.new_scheduled_time
    await db.commit()

    print(f"📅 Client {client.business_name} rescheduled content {content_id}: {old_time} → {reschedule_data.new_scheduled_time}")

    return {
        "message": "Post rescheduled successfully in both database and Publer",
        "content_id": content.id,
        "old_time": old_time.isoformat() if old_time else None,
        "new_time": content.scheduled_at.isoformat(),
        "updated_platforms": list(content.platform_post_ids.keys()) if content.platform_post_ids else [],
    }
