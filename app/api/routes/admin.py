from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from typing import List
import secrets

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.models.client import Client
from app.models.content import Content, ContentStatus
from app.models.client_signup import ClientSignup


class CaptionUpdate(BaseModel):
    caption: str


class ScheduleUpdate(BaseModel):
    scheduled_at: str


class BrainstormRequest(BaseModel):
    client_id: int
    num_ideas: int = 10
    keyword: str | None = None
    content_format: str = "social"  # "social" or "blog"


class CreateContentRequest(BaseModel):
    client_id: int
    topic: str
    content_type: str
    notes: str = ""

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_current_user_from_cookie(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """Get user from session cookie."""
    token = request.cookies.get("access_token")
    if not token:
        return None

    from app.core.security import decode_access_token
    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Process login form."""

    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password"},
        )

    if not user.is_active:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Account is inactive"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Redirect to dashboard with cookie
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
    )

    return response


@router.get("/logout")
async def logout():
    """Logout - clear cookie and redirect to login."""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show admin dashboard."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get stats
    pending_result = await db.execute(
        select(func.count(Content.id)).where(
            Content.status == ContentStatus.PENDING_APPROVAL
        )
    )
    pending_count = pending_result.scalar()

    scheduled_result = await db.execute(
        select(func.count(Content.id)).where(
            Content.status == ContentStatus.SCHEDULED
        )
    )
    scheduled_count = scheduled_result.scalar()

    clients_result = await db.execute(
        select(func.count(Client.id)).where(Client.owner_id == user.id)
    )
    total_clients = clients_result.scalar()

    published_result = await db.execute(
        select(func.count(Content.id)).where(
            Content.status == ContentStatus.PUBLISHED
        )
    )
    published_this_month = published_result.scalar()

    # Get pending content
    pending_content_result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.status == ContentStatus.PENDING_APPROVAL)
        .where(Client.owner_id == user.id)
        .order_by(Content.created_at.desc())
        .limit(10)
    )
    pending_rows = pending_content_result.all()

    # Format pending content for template
    pending_content = []
    for content, client in pending_rows:
        pending_content.append({
            "id": content.id,
            "client_name": client.business_name,
            "topic": content.topic,
            "caption": content.caption or "",
            "status": content.status.value,
            "focus_location": content.focus_location or "",
        })

    stats = {
        "pending_count": pending_count,
        "scheduled_count": scheduled_count,
        "total_clients": total_clients,
        "published_this_month": published_this_month,
    }

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "pending_content": pending_content,
        },
    )


@router.post("/content/{content_id}/approve")
async def approve_content_htmx(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Approve content (HTMX endpoint)."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get content
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404)

    content, client = row

    # Check monthly limit before approval
    if client.posts_this_month >= client.monthly_post_limit:
        return HTMLResponse(
            '<div class="text-red-600 text-sm">❌ Client has reached monthly post limit</div>',
            status_code=400
        )

    # Update status
    content.status = ContentStatus.APPROVED
    
    # Increment monthly counter
    client.posts_this_month += 1

    await db.commit()

    # Return empty (will remove from list)
    return HTMLResponse("")


@router.get("/clients", response_class=HTMLResponse)
async def clients_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show clients list."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get clients
    result = await db.execute(
        select(Client)
        .where(Client.owner_id == user.id)
        .order_by(Client.created_at.desc())
    )
    clients = result.scalars().all()

    return templates.TemplateResponse(
        "clients.html",
        {
            "request": request,
            "user": user,
            "clients": clients,
        },
    )


@router.get("/clients/new", response_class=HTMLResponse)
async def new_client_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show new client form."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    return templates.TemplateResponse(
        "client_new.html",
        {
            "request": request,
            "user": user,
            "success": False,
        },
    )


@router.post("/clients/new")
async def create_client(
    request: Request,
    business_name: str = Form(...),
    email: str = Form(...),
    industry: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    service_area: str = Form(None),
    website_url: str = Form(None),
    monthly_post_limit: int = Form(10),
    auto_post: bool = Form(False),
    brand_voice: str = Form(None),
    platforms: list = Form([]),
    publer_workspace_id: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Generate unique intake token
    import secrets
    intake_token = secrets.token_urlsafe(16)

    # Create client
    client = Client(
        owner_id=user.id,
        business_name=business_name,
        email=email.lower(),  # Store email in lowercase for consistent lookups
        industry=industry,
        city=city,
        state=state,
        service_area=service_area,
        website_url=website_url,
        monthly_post_limit=monthly_post_limit,
        auto_post=auto_post,
        brand_voice=brand_voice,
        platforms_enabled=platforms if platforms else [],
        publer_workspace_id=publer_workspace_id,
        intake_token=intake_token,
        is_active=True,
    )

    db.add(client)
    await db.commit()
    await db.refresh(client)

    # Generate intake URL
    intake_url = f"{request.base_url}api/v1/intake/{intake_token}/form"

    return templates.TemplateResponse(
        "client_new.html",
        {
            "request": request,
            "user": user,
            "success": True,
            "new_client": client,
            "intake_url": intake_url,
        },
    )


# IMPORTANT: /content/new must come BEFORE /content/{content_id} to avoid route conflicts
@router.get("/content/new", response_class=HTMLResponse)
async def new_content_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show create content page."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get all active clients for dropdown
    clients_result = await db.execute(
        select(Client)
        .where(Client.owner_id == user.id)
        .where(Client.is_active == True)
        .order_by(Client.business_name)
    )
    clients = clients_result.scalars().all()

    return templates.TemplateResponse(
        "content_create.html",
        {
            "request": request,
            "user": user,
            "clients": clients,
        },
    )


@router.get("/content/{content_id}", response_class=HTMLResponse)
async def content_detail_page(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show content detail/review page."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get content with client
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Content not found")

    content, client = row

    return templates.TemplateResponse(
        "content_detail.html",
        {
            "request": request,
            "user": user,
            "content": content,
            "client": client,
        },
    )


@router.post("/content/{content_id}/edit")
async def edit_content_caption(
    content_id: int,
    caption_update: CaptionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Edit content caption."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get content
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404)

    content, client = row

    # Update caption
    content.caption = caption_update.caption
    await db.commit()

    return {"success": True, "message": "Caption updated"}


@router.post("/content/{content_id}/reject")
async def reject_content(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Reject content."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get content
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404)

    content, client = row

    # Update status to failed (or we could add a REJECTED status)
    content.status = ContentStatus.FAILED
    content.error_message = "Content rejected by team"
    await db.commit()

    return HTMLResponse(
        '<div class="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">'
        '<p class="text-sm text-yellow-800">Content has been rejected.</p>'
        '</div>'
    )


@router.post("/content/{content_id}/schedule")
async def schedule_content(
    content_id: int,
    schedule_update: ScheduleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Schedule content for posting."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get content
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404)

    content, client = row

    # Parse and update schedule
    scheduled_at = datetime.fromisoformat(schedule_update.scheduled_at)
    content.scheduled_at = scheduled_at
    content.status = ContentStatus.SCHEDULED
    await db.commit()

    return {"success": True, "message": "Content scheduled"}


@router.post("/content/{content_id}/publish-now")
async def publish_content_now(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Publish content immediately."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get content
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404)

    content, client = row

    # TODO: Add to Celery queue for immediate posting
    # For now, just mark as scheduled for immediate posting
    content.scheduled_at = datetime.utcnow()
    content.status = ContentStatus.SCHEDULED
    await db.commit()

    return HTMLResponse(
        '<div class="mb-4 bg-green-50 border border-green-200 rounded-lg p-4">'
        '<p class="text-sm text-green-800">Content queued for immediate publishing!</p>'
        '</div>'
    )


@router.post("/content/{content_id}/generate-blog")
async def generate_blog(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Generate blog post from social content."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get content
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404)

    content, client = row

    if not content.caption:
        return HTMLResponse(
            '<div class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">'
            '<p class="text-sm text-red-800">Cannot generate blog: No social caption found. Please generate social content first.</p>'
            '</div>'
        )

    # Queue blog generation task
    from app.tasks.content_tasks import generate_blog_task
    generate_blog_task.delay(content_id)

    return HTMLResponse(
        '<div class="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">'
        '<p class="text-sm text-blue-800">Blog post is being generated! This may take 30-60 seconds. Refresh the page to see the result.</p>'
        '</div>'
    )


@router.post("/content/{content_id}/publish-blog")
async def publish_blog_to_wordpress(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Publish blog post to WordPress."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get content
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404)

    content, client = row

    if not content.blog_title or not content.blog_content:
        return HTMLResponse(
            '<div class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">'
            '<p class="text-sm text-red-800">Cannot publish blog: No blog content found. Please generate blog first.</p>'
            '</div>'
        )

    # Queue WordPress publishing task
    from app.tasks.content_tasks import publish_blog_to_wordpress_task
    publish_blog_to_wordpress_task.delay(content_id, "publish")

    return HTMLResponse(
        '<div class="mb-4 bg-green-50 border border-green-200 rounded-lg p-4">'
        '<p class="text-sm text-green-800">Blog is being published to WordPress! Check your WordPress site in a few moments.</p>'
        '</div>'
    )


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show content calendar."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get all clients for filter dropdown
    clients_result = await db.execute(
        select(Client)
        .where(Client.owner_id == user.id)
        .order_by(Client.business_name)
    )
    clients = clients_result.scalars().all()

    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "user": user,
            "clients": clients,
        },
    )


@router.get("/calendar/data")
async def calendar_data(
    request: Request,
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
):
    """Get calendar data for a specific month."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get start and end dates for the month
    from datetime import datetime
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Get all scheduled content for this month
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Client.owner_id == user.id)
        .where(Content.status == ContentStatus.SCHEDULED)
        .where(Content.scheduled_at >= start_date)
        .where(Content.scheduled_at < end_date)
        .order_by(Content.scheduled_at)
    )
    rows = result.all()

    # Format data for calendar
    calendar_posts = []
    for content, client in rows:
        calendar_posts.append({
            "id": content.id,
            "client_id": client.id,
            "client_name": client.business_name,
            "topic": content.topic,
            "scheduled_at": content.scheduled_at.isoformat(),
            "platforms": client.platforms_enabled or [],
            "status": content.status.value,
        })

    return calendar_posts


@router.post("/content/{content_id}/reschedule")
async def reschedule_content(
    content_id: int,
    schedule_update: ScheduleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Reschedule content (for calendar drag-and-drop)."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get content
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404)

    content, client = row

    # Parse and update schedule
    scheduled_at = datetime.fromisoformat(schedule_update.scheduled_at.replace('Z', '+00:00'))
    content.scheduled_at = scheduled_at

    await db.commit()

    return {"success": True, "message": "Content rescheduled", "new_time": scheduled_at.isoformat()}


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    days: Optional[int] = 30,
    client_id: Optional[int] = None,
    platform: Optional[str] = None,
):
    """Show analytics dashboard."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get all clients for filter
    clients_result = await db.execute(
        select(Client)
        .where(Client.owner_id == user.id)
        .order_by(Client.business_name)
    )
    clients = clients_result.scalars().all()

    # Calculate date range
    from datetime import timedelta
    end_date = datetime.utcnow()
    if days != 'all':
        start_date = end_date - timedelta(days=int(days) if days else 30)
    else:
        start_date = datetime(2020, 1, 1)

    # Build base query
    base_query = (
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Client.owner_id == user.id)
    )

    # Apply filters
    if client_id:
        base_query = base_query.where(Client.id == client_id)

    # Get total posts
    total_result = await db.execute(base_query)
    all_posts = total_result.all()

    # Calculate stats
    total_posts = len(all_posts)
    published_count = sum(1 for content, _ in all_posts if content.status == ContentStatus.PUBLISHED)
    scheduled_count = sum(1 for content, _ in all_posts if content.status == ContentStatus.SCHEDULED)

    # Platform stats
    platform_stats = {}
    for content, client in all_posts:
        platforms = client.platforms_enabled or []
        if platform and platform not in platforms:
            continue
        for p in platforms:
            platform_stats[p] = platform_stats.get(p, 0) + 1

    # Client stats
    client_stats_dict = {}
    for content, client in all_posts:
        if client.id not in client_stats_dict:
            client_stats_dict[client.id] = {
                "name": client.business_name,
                "count": 0
            }
        client_stats_dict[client.id]["count"] += 1

    client_stats = sorted(client_stats_dict.values(), key=lambda x: x["count"], reverse=True)

    # Timeline data (last 14 days)
    timeline = []
    timeline_max = 0
    for i in range(13, -1, -1):
        day = end_date - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        count = sum(
            1 for content, _ in all_posts
            if content.published_at and day_start <= content.published_at < day_end
        )

        timeline.append({
            "date": day.strftime("%m/%d"),
            "count": count
        })
        timeline_max = max(timeline_max, count)

    # Recent posts
    recent_result = await db.execute(
        base_query
        .order_by(Content.created_at.desc())
        .limit(10)
    )
    recent_rows = recent_result.all()

    recent_posts = []
    for content, client in recent_rows:
        recent_posts.append({
            "id": content.id,
            "client_name": client.business_name,
            "topic": content.topic,
            "platforms": client.platforms_enabled or [],
            "published_at": content.published_at,
            "status": content.status.value,
        })

    stats = {
        "total_posts": total_posts,
        "published_count": published_count,
        "scheduled_count": scheduled_count,
        "avg_engagement_rate": 0.0,  # TODO: Calculate from analytics data
    }

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "user": user,
            "clients": clients,
            "stats": stats,
            "platform_stats": platform_stats,
            "client_stats": client_stats,
            "timeline": timeline,
            "timeline_max": timeline_max if timeline_max > 0 else 1,
            "recent_posts": recent_posts,
        },
    )


@router.post("/content/{content_id}/generate-image")
async def generate_image_for_content(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    style: str = Form("photographic"),
):
    """Generate AI image for content using DALL-E."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get content
    result = await db.execute(
        select(Content, Client)
        .join(Client, Content.client_id == Client.id)
        .where(Content.id == content_id)
        .where(Client.owner_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404)

    content, client = row

    if not content.caption:
        return HTMLResponse(
            '<div class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">'
            '<p class="text-sm text-red-800">Cannot generate image: No caption found. Please generate content first.</p>'
            '</div>'
        )

    try:
        # Generate image using AI service
        from app.services.ai import ai_service

        image_result = await ai_service.generate_image(
            business_name=client.business_name,
            industry=client.industry or "local business",
            topic=content.topic,
            caption=content.caption,
            style=style,
        )

        # Add image URL to content media
        if not content.media_urls:
            content.media_urls = []

        content.media_urls.append(image_result["url"])
        content.media_type = "image"

        await db.commit()

        return HTMLResponse(
            f'<div class="mb-4 bg-green-50 border border-green-200 rounded-lg p-4">'
            f'<p class="text-sm text-green-800">AI image generated successfully!</p>'
            f'<img src="{image_result["url"]}" class="mt-2 rounded-lg max-w-xs" alt="Generated image">'
            f'</div>'
        )

    except Exception as e:
        return HTMLResponse(
            f'<div class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">'
            f'<p class="text-sm text-red-800">Failed to generate image: {str(e)}</p>'
            f'</div>'
        )


@router.get("/brainstorm", response_class=HTMLResponse)
async def brainstorm_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show content brainstorming page."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get all clients
    clients_result = await db.execute(
        select(Client)
        .where(Client.owner_id == user.id)
        .where(Client.is_active == True)
        .order_by(Client.business_name)
    )
    clients = clients_result.scalars().all()

    return templates.TemplateResponse(
        "brainstorm.html",
        {
            "request": request,
            "user": user,
            "clients": clients,
        },
    )


@router.post("/brainstorm/generate")
async def generate_ideas(
    brainstorm_request: BrainstormRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Generate content ideas for a client."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Get client
    client_result = await db.execute(
        select(Client)
        .where(Client.id == brainstorm_request.client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Generate ideas using AI service
    from app.services.ai import ai_service

    try:
        # Build location string safely
        location_parts = []
        if client.city:
            location_parts.append(client.city)
        if client.state:
            location_parts.append(client.state)
        location = ", ".join(location_parts) if location_parts else "local area"

        ideas = await ai_service.generate_content_ideas(
            business_name=client.business_name,
            industry=client.industry or "local business",
            location=location,
            brand_voice=client.brand_voice,
            num_ideas=brainstorm_request.num_ideas,
            keyword=brainstorm_request.keyword,
            content_format=brainstorm_request.content_format,
        )

        return {"ideas": ideas}

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Failed to generate ideas: {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Return detailed error for debugging
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate ideas: {error_msg[:200]}"  # Limit error message length
        )


@router.post("/brainstorm/create-content")
async def create_content_from_idea(
    content_request: CreateContentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a content draft from a brainstormed idea."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Verify client ownership
    client_result = await db.execute(
        select(Client)
        .where(Client.id == content_request.client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Create content draft
    from app.models.content import ContentType

    # Map content_type string to enum
    try:
        content_type_enum = ContentType[content_request.content_type.upper()]
    except KeyError:
        content_type_enum = ContentType.OTHER

    content = Content(
        client_id=client.id,
        topic=content_request.topic,
        content_type=content_type_enum,
        notes=content_request.notes,
        focus_location=f"{client.city}, {client.state}",
        status=ContentStatus.DRAFT,
    )

    db.add(content)
    await db.commit()
    await db.refresh(content)

    return {"success": True, "content_id": content.id}


class WordPressConfig(BaseModel):
    site_url: str
    username: str
    app_password: str
    test_connection: bool = True


class ContentCreateRequest(BaseModel):
    client_id: int
    topic: str
    content_type: str
    focus_location: str | None = None
    notes: str | None = None
    generate_blog: bool = False
    auto_approve: bool = False


@router.get("/clients/{client_id}", response_class=HTMLResponse)
async def client_detail_page(
    client_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show client detail page with WordPress integration."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get client
    client_result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get WordPress configuration
    from app.models.platform_config import PlatformConfig

    wp_config_result = await db.execute(
        select(PlatformConfig)
        .where(PlatformConfig.client_id == client.id)
        .where(PlatformConfig.platform == "wordpress")
    )
    wp_config = wp_config_result.scalar_one_or_none()

    wordpress_connected = wp_config is not None and wp_config.is_active
    wordpress_config = None

    if wp_config:
        wordpress_config = {
            "site_url": wp_config.config.get("site_url", ""),
            "username": wp_config.config.get("username", ""),
        }

    # Get recent content
    recent_content_result = await db.execute(
        select(Content)
        .where(Content.client_id == client.id)
        .order_by(Content.created_at.desc())
        .limit(5)
    )
    recent_content = recent_content_result.scalars().all()

    return templates.TemplateResponse(
        "client_detail.html",
        {
            "request": request,
            "user": user,
            "client": client,
            "wordpress_connected": wordpress_connected,
            "wordpress_config": wordpress_config,
            "recent_content": recent_content,
        },
    )


@router.post("/clients/{client_id}/wordpress")
async def save_wordpress_config(
    client_id: int,
    wordpress_config: WordPressConfig,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Save WordPress configuration for a client."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Verify client ownership
    client_result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Test connection if requested
    if wordpress_config.test_connection:
        from app.services.wordpress import wordpress_service

        try:
            # Test by fetching posts (doesn't create anything)
            import httpx

            api_url = f"{wordpress_config.site_url.rstrip('/')}/wp-json/wp/v2/posts"
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(
                    api_url,
                    auth=(wordpress_config.username, wordpress_config.app_password),
                    timeout=10.0,
                )
                if response.status_code not in [200, 401]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"WordPress API returned status {response.status_code}. Check your site URL.",
                    )
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid WordPress credentials. Check username and app password.",
                    )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=400, detail="Connection timeout. Check your site URL."
            )
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=400, detail=f"Connection failed: {str(e)}"
            )

    # Get existing config or create new one
    from app.models.platform_config import PlatformConfig

    config_result = await db.execute(
        select(PlatformConfig)
        .where(PlatformConfig.client_id == client_id)
        .where(PlatformConfig.platform == "wordpress")
    )
    config = config_result.scalar_one_or_none()

    if config:
        # Update existing
        config.config = {
            "site_url": wordpress_config.site_url,
            "username": wordpress_config.username,
        }
        # Only update password if provided
        if wordpress_config.app_password:
            config.access_token = wordpress_config.app_password
        config.is_active = True
    else:
        # Create new
        config = PlatformConfig(
            client_id=client_id,
            platform="wordpress",
            is_active=True,
            config={
                "site_url": wordpress_config.site_url,
                "username": wordpress_config.username,
            },
            access_token=wordpress_config.app_password,
        )
        db.add(config)

    await db.commit()

    return {"success": True, "message": "WordPress settings saved successfully!"}


@router.post("/clients/{client_id}/wordpress/test")
async def test_wordpress_connection(
    client_id: int,
    wordpress_config: WordPressConfig,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Test WordPress connection."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Verify client ownership
    client_result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Test connection
    import httpx

    try:
        api_url = f"{wordpress_config.site_url.rstrip('/')}/wp-json/wp/v2/posts"
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                api_url,
                auth=(wordpress_config.username, wordpress_config.app_password),
                timeout=10.0,
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connection successful! WordPress is accessible.",
                }
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid credentials. Check username and app password.",
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"WordPress returned status {response.status_code}",
                )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=400, detail="Connection timeout. Check your site URL."
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@router.delete("/clients/{client_id}/wordpress")
async def disconnect_wordpress(
    client_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect WordPress for a client."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Verify client ownership
    client_result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Delete WordPress config
    from app.models.platform_config import PlatformConfig

    config_result = await db.execute(
        select(PlatformConfig)
        .where(PlatformConfig.client_id == client_id)
        .where(PlatformConfig.platform == "wordpress")
    )
    config = config_result.scalar_one_or_none()

    if config:
        await db.delete(config)
        await db.commit()

    return {"success": True, "message": "WordPress disconnected successfully"}


@router.post("/content/create")
async def create_new_content(
    content_request: ContentCreateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create new content from admin dashboard."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Verify client ownership
    client_result = await db.execute(
        select(Client)
        .where(Client.id == content_request.client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check monthly post limit
    if client.posts_this_month >= client.monthly_post_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Monthly post limit reached ({client.monthly_post_limit})",
        )

    # Map content_type string to enum
    from app.models.content import ContentType

    try:
        content_type_enum = ContentType[content_request.content_type.upper()]
    except KeyError:
        content_type_enum = ContentType.OTHER

    # Create content record
    content = Content(
        client_id=client.id,
        topic=content_request.topic,
        content_type=content_type_enum,
        focus_location=content_request.focus_location,
        notes=content_request.notes,
        platforms=client.platforms_enabled or [],
        status=ContentStatus.DRAFT,
    )

    db.add(content)
    await db.commit()
    await db.refresh(content)

    # Generate content in background
    background_tasks.add_task(
        generate_content_with_options,
        content_id=content.id,
        client=client,
        generate_blog=content_request.generate_blog,
        auto_approve=content_request.auto_approve,
    )

    return {
        "success": True,
        "content_id": content.id,
        "message": "Content created successfully!",
    }


async def generate_content_with_options(
    content_id: int,
    client: Client,
    generate_blog: bool = False,
    auto_approve: bool = False,
):
    """Background task to generate content with options."""
    from app.core.database import AsyncSessionLocal
    from app.services.ai import ai_service

    async with AsyncSessionLocal() as db:
        # Get content
        content_result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()

        if not content:
            return

        try:
            # Generate social post
            ai_result = await ai_service.generate_social_post(
                business_name=client.business_name,
                industry=client.industry or "local business",
                topic=content.topic,
                location=content.focus_location or f"{client.city}, {client.state}",
                content_type=content.content_type.value,
                brand_voice=client.brand_voice,
                notes=content.notes,
            )

            # Update content
            content.caption = ai_result["caption"]
            content.hashtags = ai_result["hashtags"]
            content.cta = ai_result["cta"]
            content.ai_model_used = "gpt-4-turbo-preview"

            # Generate platform-specific variations
            if content.platforms:
                try:
                    variations = await ai_service.generate_platform_variations(
                        base_caption=content.caption,
                        hashtags=content.hashtags,
                        cta=content.cta,
                        business_name=client.business_name,
                        location=content.focus_location or f"{client.city}, {client.state}",
                        platforms=content.platforms,
                    )
                    content.platform_captions = variations
                except Exception as e:
                    print(f"⚠️ Failed to generate platform variations: {e}")

            # Generate blog if requested
            if generate_blog:
                try:
                    blog_result = await ai_service.generate_blog_post(
                        business_name=client.business_name,
                        industry=client.industry or "local business",
                        topic=content.topic,
                        location=content.focus_location or f"{client.city}, {client.state}",
                        website_url=client.website_url or "",
                        short_caption=content.caption,
                        brand_voice=client.brand_voice,
                    )

                    content.blog_title = blog_result["title"]
                    content.blog_meta_title = blog_result["meta_title"]
                    content.blog_meta_description = blog_result["meta_description"]
                    content.blog_content = blog_result["content"]
                except Exception as e:
                    print(f"⚠️ Failed to generate blog: {e}")

            # Generate image automatically
            try:
                from app.services.image_generator import image_generator
                
                print(f"🎨 Generating image for content {content_id}...")
                image_url = await image_generator.generate_image(
                    topic=content.topic,
                    business_name=client.business_name,
                    industry=client.industry or "local business",
                    template_id=client.placid_template_id,
                )
                
                if image_url:
                    content.media_urls = [image_url]
                    content.featured_image_url = image_url
                    print(f"✅ Image generated: {image_url}")
                else:
                    print(f"⚠️ No image generated, proceeding without image")
                    
            except Exception as e:
                print(f"⚠️ Image generation failed, continuing without image: {e}")
                # Continue without image - not a critical failure

            # Set status
            if auto_approve:
                content.status = ContentStatus.APPROVED
            else:
                content.status = ContentStatus.PENDING_APPROVAL

            # Increment client's post count
            client.posts_this_month += 1

            await db.commit()

            # Send email notification if not auto-approved
            if not auto_approve:
                from app.models.user import User

                owner_result = await db.execute(
                    select(User).where(User.id == client.owner_id)
                )
                owner = owner_result.scalar_one_or_none()

                if owner and owner.email:
                    from app.services.email import email_service

                    await email_service.notify_content_ready_for_review(
                        team_email=owner.email,
                        client_name=client.business_name,
                        content_id=content.id,
                        topic=content.topic,
                        caption_preview=content.caption,
                    )

            print(f"✅ Generated content for {content_id}")

        except Exception as e:
            content.status = ContentStatus.FAILED
            content.error_message = str(e)
            await db.commit()
            print(f"❌ Failed to generate content for {content_id}: {str(e)}")


@router.get("/signups", response_class=HTMLResponse)
async def signups_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show pending client signups page."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get pending signups
    signups_result = await db.execute(
        select(ClientSignup)
        .where(ClientSignup.status == "pending")
        .order_by(ClientSignup.created_at.desc())
    )
    signups = signups_result.scalars().all()

    # Format for template
    signups_list = []
    for signup in signups:
        signups_list.append({
            "id": signup.id,
            "business_name": signup.business_name,
            "email": signup.email,
            "contact_person_name": signup.contact_person_name or "N/A",
            "business_industry": ", ".join(signup.business_industry) if signup.business_industry else "N/A",
            "preferred_platforms": ", ".join(signup.preferred_platforms) if signup.preferred_platforms else "N/A",
            "created_at": signup.created_at.strftime("%b %d, %Y %I:%M %p") if signup.created_at else "N/A",
            "media_count": len(signup.media_urls) if signup.media_urls else 0,
        })

    return templates.TemplateResponse(
        "signups.html",
        {
            "request": request,
            "user": user,
            "signups": signups_list,
        },
    )


@router.get("/signups/{signup_id}", response_class=HTMLResponse)
async def signup_detail(
    signup_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show detailed view of a signup request."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get signup
    result = await db.execute(
        select(ClientSignup).where(ClientSignup.id == signup_id)
    )
    signup = result.scalar_one_or_none()

    if not signup:
        raise HTTPException(status_code=404, detail="Signup not found")

    return templates.TemplateResponse(
        "signup_detail.html",
        {
            "request": request,
            "user": user,
            "signup": signup,
        },
    )


@router.post("/signups/{signup_id}/approve")
async def approve_signup(
    signup_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Approve a signup and automatically create a Client."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Get signup
    result = await db.execute(
        select(ClientSignup).where(ClientSignup.id == signup_id)
    )
    signup = result.scalar_one_or_none()

    if not signup:
        raise HTTPException(status_code=404, detail="Signup not found")

    # Check if already approved and client created
    if signup.status == "onboarded" and signup.onboarded_client_id:
        return RedirectResponse(url=f"/admin/clients/{signup.onboarded_client_id}", status_code=303)

    # Generate unique intake token
    intake_token = secrets.token_urlsafe(32)

    # Create Client from signup data
    new_client = Client(
        business_name=signup.business_name,
        email=signup.email,  # Main email for login
        industry=signup.business_industry[0] if signup.business_industry else None,
        website_url=signup.business_website,
        platforms_enabled=signup.preferred_platforms or [],
        intake_token=intake_token,
        owner_id=user.id,
        is_active=True,
        monthly_post_limit=8,  # Default
        auto_post=False,
        # Contact info
        primary_contact_name=signup.contact_person_name,
        primary_contact_email=signup.contact_person_email or signup.email,
        primary_contact_phone=signup.contact_person_phone,
        # Copy password from signup (client set their own password during signup)
        password_hash=signup.password_hash,
    )
    
    db.add(new_client)
    await db.flush()  # Get the client.id

    # Update signup status
    signup.status = "onboarded"
    signup.reviewed_at = datetime.utcnow()
    signup.onboarded_client_id = new_client.id

    await db.commit()
    await db.refresh(new_client)

    # Redirect to the new client's detail page
    return RedirectResponse(url=f"/admin/clients/{new_client.id}", status_code=303)


@router.post("/signups/{signup_id}/reject")
async def reject_signup(
    signup_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Reject a signup request."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")

    # Update signup status
    result = await db.execute(
        select(ClientSignup).where(ClientSignup.id == signup_id)
    )
    signup = result.scalar_one_or_none()

    if not signup:
        raise HTTPException(status_code=404, detail="Signup not found")

    signup.status = "rejected"
    signup.reviewed_at = datetime.utcnow()
    await db.commit()

    return RedirectResponse(url="/admin/signups", status_code=303)


class SetPasswordRequest(BaseModel):
    password: str


@router.post("/clients/{client_id}/set-password")
async def set_client_password(
    client_id: int,
    password_request: SetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Set or reset client portal password."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Verify client ownership
    client_result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Hash and set password
    from app.core.security import get_password_hash

    client.password_hash = get_password_hash(password_request.password)
    await db.commit()

    return {"success": True, "message": "Client portal password set successfully!"}



class ClientSettingsUpdate(BaseModel):
    publer_workspace_id: Optional[str] = None
    placid_template_id: Optional[str] = None
    auto_post: Optional[bool] = None


@router.patch("/clients/{client_id}/settings")
async def update_client_settings(
    client_id: int,
    settings: ClientSettingsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update client integration settings (Publer workspace, Placid template, auto-post)."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Verify client ownership
    client_result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Update fields
    if settings.publer_workspace_id is not None:
        client.publer_workspace_id = settings.publer_workspace_id if settings.publer_workspace_id else None
    
    if settings.placid_template_id is not None:
        client.placid_template_id = settings.placid_template_id if settings.placid_template_id else None
    
    if settings.auto_post is not None:
        client.auto_post = settings.auto_post

    await db.commit()

    return {
        "success": True,
        "message": "Client settings updated successfully!",
        "publer_workspace_id": client.publer_workspace_id,
        "placid_template_id": client.placid_template_id,
        "auto_post": client.auto_post
    }


@router.post("/clients/{client_id}/toggle-access")
async def toggle_client_access(
    client_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Toggle client portal access (revoke or restore)."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Verify client ownership
    client_result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Toggle is_active status
    client.is_active = not client.is_active
    await db.commit()

    action = "revoked" if not client.is_active else "restored"
    print(f"✅ Client access {action}: {client.business_name} (ID: {client.id})")

    return {
        "success": True,
        "message": f"Client portal access {action} successfully",
        "is_active": client.is_active
    }


@router.delete("/clients/{client_id}/delete")
async def delete_client(
    client_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a client and all their content."""

    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401)

    # Verify client ownership
    client_result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .where(Client.owner_id == user.id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    business_name = client.business_name

    # Delete all associated content first
    await db.execute(
        select(Content).where(Content.client_id == client_id)
    )
    await db.execute(
        Content.__table__.delete().where(Content.client_id == client_id)
    )

    # Delete the client
    await db.delete(client)
    await db.commit()

    print(f"🗑️ Client deleted: {business_name} (ID: {client_id})")

    return {
        "success": True,
        "message": f"Client {business_name} deleted successfully"
    }
