"""
Client Signup Routes

Public signup page for new clients to request onboarding.
Admin reviews and approves/rejects signups from admin dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from pathlib import Path
import secrets

from app.core.database import get_db
from app.models.client_signup import ClientSignup

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


class ClientSignupRequest(BaseModel):
    """Schema for client signup request."""
    email: EmailStr
    business_name: str
    password: str  # Client-chosen password for portal access
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[EmailStr] = None
    contact_person_phone: Optional[str] = None
    business_industry: List[str] = []
    business_website: Optional[str] = None
    preferred_platforms: List[str] = []
    additional_notes: Optional[str] = None
    media_urls: List[str] = []


@router.get("/", response_class=HTMLResponse)
async def show_signup_page(request: Request):
    """Show the professional client signup page."""
    return templates.TemplateResponse(
        "signup.html",
        {"request": request}
    )


@router.post("/upload-media")
async def upload_signup_media(
    file: UploadFile = File(...),
):
    """
    Upload media files during signup.
    Stores in a temporary location until admin approves.
    """
    # Use signup media directory
    MEDIA_DIR = Path("media/signups")
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

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
    file_url = f"/media/signups/{unique_filename}"

    print(f"✅ Signup media uploaded: {file.filename} → {file_url}")

    return {
        "url": file_url,
        "filename": file.filename,
        "content_type": file.content_type,
    }


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_signup(
    signup_data: ClientSignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit client signup request.
    Creates a pending signup that admin must review and approve.
    """
    # Check if business name or email already exists in PENDING signups only
    # (Exclude "onboarded" and "rejected" - those can sign up again)
    existing_signup = await db.execute(
        select(ClientSignup).where(
            (ClientSignup.business_name == signup_data.business_name) |
            (ClientSignup.email == signup_data.email)
        ).where(
            ClientSignup.status == "pending"  # Only check pending signups
        )
    )
    if existing_signup.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="A signup request with this business name or email already exists. Please contact support if you need assistance."
        )

    # Hash the password
    from app.core.security import get_password_hash
    hashed_password = get_password_hash(signup_data.password)

    # Create signup record
    signup = ClientSignup(
        email=signup_data.email,
        business_name=signup_data.business_name,
        password_hash=hashed_password,  # Store hashed password
        contact_person_name=signup_data.contact_person_name,
        contact_person_email=signup_data.contact_person_email,
        contact_person_phone=signup_data.contact_person_phone,
        business_industry=signup_data.business_industry,
        business_website=signup_data.business_website,
        preferred_platforms=signup_data.preferred_platforms,
        additional_notes=signup_data.additional_notes,
        media_urls=signup_data.media_urls,
        status="pending",
    )

    db.add(signup)
    await db.commit()
    await db.refresh(signup)

    print(f"✅ New client signup: {signup.business_name} (ID: {signup.id})")

    # TODO: Send notification email to admin

    return {
        "message": "Thank you for your interest! We'll review your information and get back to you within 24 hours.",
        "signup_id": signup.id,
        "status": "pending",
        "business_name": signup.business_name,
    }


@router.get("/list")
async def list_signups(
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    List all client signups (admin only - add auth later).
    Filter by status: pending, approved, rejected, onboarded.
    """
    query = select(ClientSignup).order_by(ClientSignup.created_at.desc())

    if status_filter:
        query = query.where(ClientSignup.status == status_filter)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    signups = result.scalars().all()

    return {
        "total": len(signups),
        "signups": [
            {
                "id": s.id,
                "business_name": s.business_name,
                "email": s.email,
                "contact_person_name": s.contact_person_name,
                "business_industry": s.business_industry,
                "preferred_platforms": s.preferred_platforms,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "media_count": len(s.media_urls) if s.media_urls else 0,
            }
            for s in signups
        ],
    }


@router.get("/{signup_id}")
async def get_signup_details(
    signup_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a signup request (admin only)."""
    result = await db.execute(
        select(ClientSignup).where(ClientSignup.id == signup_id)
    )
    signup = result.scalar_one_or_none()

    if not signup:
        raise HTTPException(status_code=404, detail="Signup request not found")

    return {
        "id": signup.id,
        "email": signup.email,
        "business_name": signup.business_name,
        "contact_person_name": signup.contact_person_name,
        "contact_person_email": signup.contact_person_email,
        "contact_person_phone": signup.contact_person_phone,
        "business_industry": signup.business_industry,
        "business_website": signup.business_website,
        "preferred_platforms": signup.preferred_platforms,
        "additional_notes": signup.additional_notes,
        "media_urls": signup.media_urls,
        "status": signup.status,
        "admin_notes": signup.admin_notes,
        "onboarded_client_id": signup.onboarded_client_id,
        "created_at": signup.created_at.isoformat() if signup.created_at else None,
        "reviewed_at": signup.reviewed_at.isoformat() if signup.reviewed_at else None,
    }


@router.patch("/{signup_id}/status")
async def update_signup_status(
    signup_id: int,
    status: str,
    admin_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Update signup status (admin only).
    Status options: pending, approved, rejected, onboarded
    """
    valid_statuses = ["pending", "approved", "rejected", "onboarded"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    result = await db.execute(
        select(ClientSignup).where(ClientSignup.id == signup_id)
    )
    signup = result.scalar_one_or_none()

    if not signup:
        raise HTTPException(status_code=404, detail="Signup request not found")

    signup.status = status
    signup.reviewed_at = datetime.utcnow()
    if admin_notes:
        signup.admin_notes = admin_notes

    await db.commit()

    print(f"📝 Signup {signup_id} ({signup.business_name}) status updated to: {status}")

    return {
        "message": f"Signup status updated to {status}",
        "signup_id": signup.id,
        "status": signup.status,
    }
