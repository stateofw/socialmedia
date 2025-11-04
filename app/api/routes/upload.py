"""
File upload routes for media handling.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import os
import shutil
from pathlib import Path
import secrets
from datetime import datetime
from app.core.config import settings

router = APIRouter()

# Create media directory if it doesn't exist
MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)

# Create clients subdirectory
CLIENTS_DIR = MEDIA_DIR / "clients"
CLIENTS_DIR.mkdir(exist_ok=True)


def get_client_media_dir(client_id: int) -> Path:
    """Get or create media directory for a specific client."""
    client_dir = CLIENTS_DIR / str(client_id)
    client_dir.mkdir(exist_ok=True)
    return client_dir


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving the extension."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = secrets.token_hex(4)
    extension = Path(original_filename).suffix
    return f"{timestamp}_{random_suffix}{extension}"


@router.post("/upload/{intake_token}")
async def upload_media(
    intake_token: str,
    files: List[UploadFile] = File(...),
):
    """
    Upload media files for a client's content submission.

    Args:
        intake_token: The client's unique intake form token
        files: List of uploaded files (images, videos)

    Returns:
        List of URLs to access the uploaded files
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from app.core.database import get_db
    from app.models.client import Client

    # Get database session
    async for db in get_db():
        # Lookup client by intake token
        result = await db.execute(
            select(Client).where(Client.intake_token == intake_token)
        )
        client = result.scalar_one_or_none()

        if not client:
            raise HTTPException(status_code=404, detail="Invalid intake token")

        # Validate file types and sizes
        ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi"}
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

        uploaded_urls = []

        try:
            for file in files:
                # Check file extension
                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in ALLOWED_EXTENSIONS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
                    )

                # Read file content
                content = await file.read()
                file_size = len(content)

                # Check file size
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {file.filename} exceeds maximum size of {MAX_FILE_SIZE / 1024 / 1024}MB"
                    )

                # Generate unique filename
                unique_filename = generate_unique_filename(file.filename)

                # Get client's media directory
                client_media_dir = get_client_media_dir(client.id)
                file_path = client_media_dir / unique_filename

                # Save file
                with open(file_path, "wb") as f:
                    f.write(content)

                # Generate URL
                # In production, you might use a CDN or cloud storage URL
                file_url = f"/media/clients/{client.id}/{unique_filename}"
                uploaded_urls.append(file_url)

                print(f"✅ Uploaded {file.filename} → {file_url}")

            return {
                "message": f"Successfully uploaded {len(files)} file(s)",
                "media_urls": uploaded_urls,
                "count": len(uploaded_urls)
            }

        except Exception as e:
            # Clean up any partially uploaded files
            for url in uploaded_urls:
                try:
                    file_path = Path(url.lstrip('/'))
                    if file_path.exists():
                        file_path.unlink()
                except:
                    pass
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/media/clients/{client_id}/{filename}")
async def serve_media(client_id: int, filename: str):
    """
    Serve uploaded media files.

    In production, you'd use a CDN or cloud storage,
    but for development we'll serve directly.
    """
    from fastapi.responses import FileResponse

    file_path = CLIENTS_DIR / str(client_id) / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
