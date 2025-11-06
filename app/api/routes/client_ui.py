"""
Client Portal UI Routes

HTML-based client portal for clients to login and manage their content.
Similar to admin portal but for clients.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.client import Client
from app.models.content import Content, ContentStatus

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_current_client_from_cookie(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[Client]:
    """Get client from session cookie."""
    token = request.cookies.get("client_access_token")
    if not token:
        return None

    from app.core.security import decode_access_token
    payload = decode_access_token(token)
    if not payload:
        return None

    client_id = payload.get("client_id")
    if not client_id:
        return None

    result = await db.execute(select(Client).where(Client.id == int(client_id)))
    return result.scalar_one_or_none()


@router.get("/login", response_class=HTMLResponse)
async def client_login_page(request: Request):
    """Show client login page."""
    return templates.TemplateResponse("client/login.html", {"request": request})


@router.post("/login")
async def client_login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Process client login form."""

    # Find client by email
    result = await db.execute(
        select(Client).where(Client.email == email.lower())
    )
    client = result.scalar_one_or_none()

    if not client:
        return templates.TemplateResponse(
            "client/login.html",
            {"request": request, "error": "Invalid email or password"},
        )

    # Check if password is set
    if not client.password_hash:
        return templates.TemplateResponse(
            "client/login.html",
            {"request": request, "error": "Portal access not set up. Please contact support."},
        )

    # Verify password
    if not verify_password(password, client.password_hash):
        return templates.TemplateResponse(
            "client/login.html",
            {"request": request, "error": "Invalid email or password"},
        )

    if not client.is_active:
        return templates.TemplateResponse(
            "client/login.html",
            {"request": request, "error": "Account is inactive. Please contact support."},
        )

    # Update last login
    client.last_login = datetime.utcnow()
    await db.commit()

    # Create access token with client_id
    access_token = create_access_token(data={"client_id": str(client.id)})

    # Redirect to dashboard with cookie
    response = RedirectResponse(url="/client/dashboard", status_code=303)
    response.set_cookie(
        key="client_access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
    )

    return response


@router.get("/logout")
async def client_logout():
    """Logout - clear cookie and redirect to login."""
    response = RedirectResponse(url="/client/login", status_code=303)
    response.delete_cookie("client_access_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def client_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show client dashboard."""

    client = await get_current_client_from_cookie(request, db)
    if not client:
        return RedirectResponse(url="/client/login")

    # Get client stats
    content_result = await db.execute(
        select(Content).where(Content.client_id == client.id)
    )
    all_content = content_result.scalars().all()

    # Count by status
    pending_count = sum(1 for c in all_content if c.status == ContentStatus.PENDING_APPROVAL)
    scheduled_count = sum(1 for c in all_content if c.status == ContentStatus.SCHEDULED)
    published_count = sum(1 for c in all_content if c.status == ContentStatus.PUBLISHED)

    # Get recent content
    recent_content_result = await db.execute(
        select(Content)
        .where(Content.client_id == client.id)
        .order_by(Content.created_at.desc())
        .limit(5)
    )
    recent_content = recent_content_result.scalars().all()

    stats = {
        "posts_this_month": client.posts_this_month,
        "monthly_limit": client.monthly_post_limit,
        "posts_remaining": client.monthly_post_limit - client.posts_this_month,
        "pending_count": pending_count,
        "scheduled_count": scheduled_count,
        "published_count": published_count,
        "total_posts": len(all_content),
    }

    return templates.TemplateResponse(
        "client/dashboard.html",
        {
            "request": request,
            "client": client,
            "stats": stats,
            "recent_content": recent_content,
            "pending_approval": pending_count,  # Template expects this
            "scheduled_posts": scheduled_count,  # Template might expect this too
            "recent_posts": published_count,  # Template might expect this too
        },
    )


@router.get("/content", response_class=HTMLResponse)
async def client_content_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show all client content."""

    client = await get_current_client_from_cookie(request, db)
    if not client:
        return RedirectResponse(url="/client/login")

    # Get all content
    content_result = await db.execute(
        select(Content)
        .where(Content.client_id == client.id)
        .order_by(Content.created_at.desc())
    )
    content_list = content_result.scalars().all()

    return templates.TemplateResponse(
        "client/content.html",
        {
            "request": request,
            "client": client,
            "content_list": content_list,
        },
    )


@router.get("/content/{content_id}", response_class=HTMLResponse)
async def client_content_detail(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show content detail page."""

    client = await get_current_client_from_cookie(request, db)
    if not client:
        return RedirectResponse(url="/client/login")

    # Get content
    content_result = await db.execute(
        select(Content).where(
            Content.id == content_id,
            Content.client_id == client.id,
        )
    )
    content = content_result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    return templates.TemplateResponse(
        "client/content_detail.html",
        {
            "request": request,
            "client": client,
            "content": content,
        },
    )


@router.get("/media", response_class=HTMLResponse)
async def client_media_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show media library page."""

    client = await get_current_client_from_cookie(request, db)
    if not client:
        return RedirectResponse(url="/client/login")

    # Get all content with media
    content_result = await db.execute(
        select(Content)
        .where(
            Content.client_id == client.id,
            Content.media_urls.isnot(None)
        )
        .order_by(Content.created_at.desc())
    )
    content_with_media = content_result.scalars().all()

    # Extract all media URLs
    all_media = []
    for content in content_with_media:
        if content.media_urls:
            for url in content.media_urls:
                all_media.append({
                    "url": url,
                    "content_id": content.id,
                    "topic": content.topic,
                    "created_at": content.created_at,
                })

    return templates.TemplateResponse(
        "client/media.html",
        {
            "request": request,
            "client": client,
            "media_list": all_media,
        },
    )


@router.get("/calendar", response_class=HTMLResponse)
async def client_calendar_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show content calendar."""

    client = await get_current_client_from_cookie(request, db)
    if not client:
        return RedirectResponse(url="/client/login")

    # Get scheduled content
    scheduled_result = await db.execute(
        select(Content)
        .where(
            Content.client_id == client.id,
            Content.status.in_([ContentStatus.SCHEDULED, ContentStatus.APPROVED])
        )
        .order_by(Content.scheduled_at.asc())
    )
    scheduled_content = scheduled_result.scalars().all()

    return templates.TemplateResponse(
        "client/calendar.html",
        {
            "request": request,
            "client": client,
            "scheduled_content": scheduled_content,
        },
    )


@router.get("/settings", response_class=HTMLResponse)
async def client_settings_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show client settings page."""

    client = await get_current_client_from_cookie(request, db)
    if not client:
        return RedirectResponse(url="/client/login")

    return templates.TemplateResponse(
        "client/settings.html",
        {
            "request": request,
            "client": client,
        },
    )


@router.post("/settings/content-preference")
async def update_content_preference(
    request: Request,
    preference: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Update content generation preference."""

    client = await get_current_client_from_cookie(request, db)
    if not client:
        return RedirectResponse(url="/client/login")

    valid_preferences = ["own_media", "auto_generate", "mixed"]
    if preference not in valid_preferences:
        raise HTTPException(status_code=400, detail="Invalid preference")

    client.content_generation_preference = preference
    await db.commit()

    return RedirectResponse(url="/client/settings?success=true", status_code=303)
