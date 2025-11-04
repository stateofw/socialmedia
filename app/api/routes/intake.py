from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form, Request
import asyncio
from datetime import datetime
from typing import Set
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.client import Client
from app.models.content import Content, ContentType, ContentStatus
from app.models.user import User
from app.schemas.content import ContentIntakeForm
from app.services.ai import ai_service
from app.services.storage import storage_service
from app.services.email import email_service
from app.services.hashtag_generator import hashtag_generator
from app.services.content_polisher import content_polisher
from app.services.publer import publer_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Keep references to running background tasks to prevent garbage collection
background_tasks_set: Set[asyncio.Task] = set()


@router.get("/{intake_token}/form", response_class=HTMLResponse)
async def show_intake_form(
    intake_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show the intake form HTML page."""
    result = await db.execute(
        select(Client).where(Client.intake_token == intake_token)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Invalid intake form link",
        )

    if not client.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is not active",
        )

    # Prepare client data for template
    client_data = {
        "business_name": client.business_name,
        "service_area": client.service_area or f"{client.city}, {client.state}" if client.city else "",
        "posts_remaining": client.monthly_post_limit - client.posts_this_month,
        "monthly_post_limit": client.monthly_post_limit,
        "auto_post": client.auto_post,
    }

    return templates.TemplateResponse(
        "intake.html",
        {"request": request, "client": client_data, "token": intake_token}
    )


@router.get("/{intake_token}")
async def get_client_by_token(
    intake_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get client information by intake token.
    This endpoint powers pre-filled intake forms.
    """
    result = await db.execute(
        select(Client).where(Client.intake_token == intake_token)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Invalid intake form link. Please contact support.",
        )

    if not client.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is not active. Please contact support.",
        )

    # Return client info for form pre-filling
    return {
        "business_name": client.business_name,
        "industry": client.industry,
        "service_area": client.service_area or f"{client.city}, {client.state}" if client.city else None,
        "platforms": client.platforms_enabled or [],
        "monthly_post_limit": client.monthly_post_limit,
        "posts_this_month": client.posts_this_month,
        "posts_remaining": client.monthly_post_limit - client.posts_this_month,
    }


@router.post("/{intake_token}/submit", status_code=status.HTTP_201_CREATED)
async def submit_intake_form_with_token(
    intake_token: str,
    intake_data: ContentIntakeForm,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit content via token-based intake form (pre-filled).
    This is the preferred method as it doesn't require business name lookup.
    """
    # Find client by token
    result = await db.execute(
        select(Client).where(Client.intake_token == intake_token)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Invalid intake form link. Please contact support.",
        )

    if not client.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is not active. Please contact support.",
        )

    # Check monthly post limit
    if client.posts_this_month >= client.monthly_post_limit:
        raise HTTPException(
            status_code=400,
            detail=f"You've reached your monthly post limit of {client.monthly_post_limit} posts. Please upgrade your plan.",
        )

    # Handle image-only submissions (no topic provided)
    topic = intake_data.topic
    content_type = intake_data.content_type
    focus_location = intake_data.focus_location or client.service_area or f"{client.city}, {client.state}"

    if not topic and intake_data.media_urls and len(intake_data.media_urls) > 0:
        # Convert relative URL to full URL for AI image analysis
        image_url = intake_data.media_urls[0]
        if image_url.startswith('/'):
            # Convert to full URL (assume localhost for now, in production use proper base URL)
            import os
            base_url = os.getenv('BASE_URL', 'http://localhost:8000')
            image_url = f"{base_url}{image_url}"

        # Analyze the first image to generate topic and content type
        print(f"🖼️ No topic provided, analyzing image: {image_url}")

        image_analysis = await ai_service.analyze_image_for_post(
            image_url=image_url,
            business_name=client.business_name,
            industry=client.industry or "local business",
            location=focus_location,
            notes=intake_data.notes,
        )

        topic = image_analysis.get("topic", "Recent project showcase")
        content_type_str = image_analysis.get("content_type", "project_showcase")

        # Convert content_type string to enum
        try:
            from app.models.content import ContentType
            content_type = ContentType(content_type_str)
        except ValueError:
            content_type = ContentType.PROJECT_SHOWCASE

        # Append image description to notes
        description = image_analysis.get("description", "")
        if description:
            if intake_data.notes:
                intake_data.notes = f"{intake_data.notes}\n\n[AI Image Analysis]: {description}"
            else:
                intake_data.notes = f"[AI Image Analysis]: {description}"

        print(f"✅ Generated topic from image: {topic}")
        print(f"✅ Detected content type: {content_type.value}")

    elif not topic:
        # No topic and no images
        raise HTTPException(
            status_code=400,
            detail="Please provide either a topic or upload at least one image",
        )

    # Create content record
    content = Content(
        client_id=client.id,
        topic=topic,
        content_type=content_type,
        focus_location=focus_location,
        notes=intake_data.notes,
        media_urls=intake_data.media_urls or [],
        platforms=client.platforms_enabled or [],
        status=ContentStatus.DRAFT,
    )

    db.add(content)
    await db.commit()
    await db.refresh(content)

    # Generate AI content in background using asyncio.create_task
    task = asyncio.create_task(
        generate_and_process_content(
            content_id=content.id,
            client_id=client.id,
            auto_post=intake_data.auto_post or client.auto_post,
        )
    )
    # Add task to the set to keep a reference and prevent garbage collection
    background_tasks_set.add(task)
    # Remove task from set when done
    task.add_done_callback(background_tasks_set.discard)

    return {
        "message": "Content submitted successfully! We'll generate your post shortly.",
        "content_id": content.id,
        "status": "processing",
        "business_name": client.business_name,
    }


@router.post("/form", status_code=status.HTTP_201_CREATED)
async def submit_intake_form(
    intake_data: ContentIntakeForm,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint for client intake form.
    Clients submit content ideas and the system generates posts automatically.
    """

    # Find client by business name
    result = await db.execute(
        select(Client).where(Client.business_name == intake_data.business_name)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Business '{intake_data.business_name}' not found. Please contact support.",
        )

    if not client.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is not active. Please contact support.",
        )

    # Check monthly post limit
    if client.posts_this_month >= client.monthly_post_limit:
        raise HTTPException(
            status_code=400,
            detail=f"You've reached your monthly post limit of {client.monthly_post_limit} posts. Please upgrade your plan.",
        )

    # Create content record
    content = Content(
        client_id=client.id,
        topic=intake_data.topic,
        content_type=intake_data.content_type,
        focus_location=intake_data.focus_location,
        notes=intake_data.notes,
        media_urls=intake_data.media_urls or [],
        platforms=client.platforms_enabled or [],
        status=ContentStatus.DRAFT,
    )

    db.add(content)
    await db.commit()
    await db.refresh(content)

    # Generate AI content in background using asyncio.create_task
    task = asyncio.create_task(
        generate_and_process_content(
            content_id=content.id,
            client_id=client.id,
            auto_post=intake_data.auto_post or client.auto_post,
        )
    )
    # Add task to the set to keep a reference and prevent garbage collection
    background_tasks_set.add(task)
    # Remove task from set when done
    task.add_done_callback(background_tasks_set.discard)

    return {
        "message": "Content submitted successfully! We'll generate your post shortly.",
        "content_id": content.id,
        "status": "processing",
    }


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    client_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload media files (images/videos) for content.
    Returns the URL to use in the intake form.
    """

    # Verify client exists
    result = await db.execute(
        select(Client).where(Client.business_name == client_name)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "video/mp4", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed: images (jpg, png, gif) and videos (mp4)",
        )

    try:
        # Upload to storage
        file_url = await storage_service.upload_file(
            file=file.file,
            file_name=file.filename,
            content_type=file.content_type,
            folder=f"clients/{client.id}",
        )

        return {
            "url": file_url,
            "filename": file.filename,
            "content_type": file.content_type,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}",
        )


async def generate_and_process_content(
    content_id: int,
    client_id: int,
    auto_post: bool = False,
):
    """
    Background task to:
    1. Generate AI content
    2. Optionally generate blog post
    3. Auto-approve if client has auto_post enabled
    """
    print(f"🚀 Starting background task for content_id={content_id}, client_id={client_id}")
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get content and client
        content_result = await db.execute(select(Content).where(Content.id == content_id))
        content = content_result.scalar_one_or_none()

        client_result = await db.execute(select(Client).where(Client.id == client_id))
        client = client_result.scalar_one_or_none()

        if not content or not client:
            return

        try:
            print(f"📝 Generating social post for content_id={content_id}...")
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

            # Update content
            raw_caption = ai_result["caption"]
            content.cta = ai_result["cta"]
            content.ai_model_used = "gpt-4-turbo-preview"

            # Polish the caption for quality (OpenAI GPT-4)
            print(f"✨ Polishing caption for content_id={content_id}...")
            location = content.focus_location or client.service_area or f"{client.city}, {client.state}"
            polished_caption = await content_polisher.polish_caption(
                caption=raw_caption,
                industry=client.industry or "local business",
                location=location,
                brand_voice=client.brand_voice,
                tone_preference=client.tone_preference or "professional",
                platform="instagram",  # Default platform for base caption
            )
            content.caption = polished_caption

            # Generate optimized hashtags
            print(f"#️⃣ Generating hashtags for content_id={content_id}...")
            city = location.split(',')[0].strip() if ',' in location else location
            state = location.split(',')[-1].strip() if ',' in location else client.state or ""

            content.hashtags = hashtag_generator.generate_hashtags(
                industry=client.industry or "local business",
                city=city,
                state=state,
                content_type=content.content_type.value,
                platform="instagram",  # Default
                include_local=True,
                include_branded=True,
                business_name=client.business_name,
            )

            # Generate platform-specific variations
            if content.platforms:
                print(f"🎯 Generating platform variations for content_id={content_id}...")
                platform_variations = await ai_service.generate_platform_variations(
                    base_caption=content.caption,
                    hashtags=content.hashtags,
                    cta=content.cta,
                    business_name=client.business_name,
                    location=location,
                    platforms=content.platforms,
                )

                # Polish each platform variation
                polished_variations = await content_polisher.polish_multiple_captions(
                    platform_captions=platform_variations,
                    industry=client.industry or "local business",
                    location=location,
                    brand_voice=client.brand_voice,
                    tone_preference=client.tone_preference or "professional",
                )
                content.platform_captions = polished_variations

            # Always set to pending approval for admin review
            content.status = ContentStatus.PENDING_APPROVAL
            print(f"📋 Content set to PENDING_APPROVAL - awaiting admin review")

            # Increment client's post count
            client.posts_this_month += 1

            await db.commit()
            print(f"✅ Successfully generated content for content_id={content_id}, status={content.status}")

            # Send email notification to team for approval
            if not auto_post:
                # Get team owner email
                owner_result = await db.execute(
                    select(User).where(User.id == client.owner_id)
                )
                owner = owner_result.scalar_one_or_none()

                if owner and owner.email:
                    await email_service.notify_content_ready_for_review(
                        team_email=owner.email,
                        client_name=client.business_name,
                        content_id=content.id,
                        topic=content.topic,
                        caption_preview=content.caption,
                    )

            # TODO: If WordPress is enabled, generate blog post

        except Exception as e:
            print(f"❌ Error generating content for content_id={content_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            content.status = ContentStatus.FAILED
            content.error_message = str(e)
            await db.commit()


async def post_to_publer(content: Content, client: Client) -> dict:
    """
    Post content to Publer for immediate publishing.

    Args:
        content: The Content object with platform_captions
        client: The Client object with publer_account_ids

    Returns:
        Dict with status and platform_post_ids
    """
    try:
        # Build platform-specific content dict
        content_dict = {}

        # Map our platform names to Publer's expected format
        platform_map = {
            "facebook": "facebook",
            "instagram": "instagram",
            "twitter": "twitter",
            "linkedin": "linkedin",
            "pinterest": "pinterest",
            "google_business": "gmb",  # Google My Business
        }

        # Use platform_captions if available, otherwise use base caption
        if content.platform_captions:
            for platform, caption_text in content.platform_captions.items():
                publer_platform = platform_map.get(platform, platform)
                content_dict[publer_platform] = {
                    "type": "status",  # Default to status post
                    "text": caption_text,
                }
        else:
            # Fallback: use base caption for all platforms
            base_text = content.caption or content.topic
            for platform in content.platforms or []:
                publer_platform = platform_map.get(platform, platform)
                content_dict[publer_platform] = {
                    "type": "status",
                    "text": base_text,
                }

        if not content_dict:
            return {"status": "failed", "error": "No platforms configured"}

        print(f"📝 Posting to platforms: {list(content_dict.keys())}")

        # Publish immediately via Publer using client's workspace
        result = await publer_service.publish_now(
            account_ids=client.publer_account_ids,
            content_dict=content_dict,
            workspace_id=client.publer_workspace_id,
        )

        # Extract platform post IDs from result if available
        platform_post_ids = {}
        if result.get("status") == "success":
            payload = result.get("payload")

            # Check if payload is a dict or list
            if isinstance(payload, dict):
                posts = payload.get("posts", [])
            elif isinstance(payload, list):
                posts = payload
            else:
                posts = []

            # Extract post IDs
            for post in posts:
                if isinstance(post, dict) and post.get("social_id"):
                    platform_post_ids[post.get("provider", "unknown")] = post.get("social_id")

        return {
            "status": result.get("status"),
            "platform_post_ids": platform_post_ids,
            "error": result.get("error"),
        }

    except Exception as e:
        print(f"❌ Error posting to Publer: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}
