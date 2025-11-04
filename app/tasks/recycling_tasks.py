"""
Content Recycling System

Automatically recycles successful content after 30 days with:
- Refreshed captions (new local details, seasonal references)
- Same or similar images
- Updated scheduling

Triggered daily via Celery beat schedule.
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.core.database import AsyncSessionLocal
from app.models.content import Content, ContentStatus, ContentType
from app.models.client import Client
from app.services.ai import ai_service
from app.services.placid import placid_service


async def find_recyclable_content() -> List[Content]:
    """
    Find content eligible for recycling.

    Criteria:
    - Status: PUBLISHED
    - Published at least 30 days ago
    - Client is still active
    - Was successful (no errors)
    """
    async with AsyncSessionLocal() as db:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        result = await db.execute(
            select(Content)
            .join(Client)
            .where(
                and_(
                    Content.status == ContentStatus.PUBLISHED,
                    Content.published_at <= thirty_days_ago,
                    Content.error_message.is_(None),
                    Client.is_active == True,
                )
            )
            .limit(50)  # Process 50 at a time
        )

        return result.scalars().all()


async def recycle_content(original_content_id: int) -> int:
    """
    Recycle a single piece of content.

    Process:
    1. Load original content
    2. Generate fresh caption with new local/seasonal references
    3. Reuse media or generate new Placid image
    4. Create new content record
    5. Set to pending approval or auto-approve based on client settings

    Returns:
        New content ID
    """
    async with AsyncSessionLocal() as db:
        # Get original content
        original_result = await db.execute(
            select(Content).where(Content.id == original_content_id)
        )
        original = original_result.scalar_one_or_none()

        if not original:
            print(f"⚠️ Original content {original_content_id} not found")
            return None

        # Get client
        client_result = await db.execute(
            select(Client).where(Client.id == original.client_id)
        )
        client = client_result.scalar_one_or_none()

        if not client or not client.is_active:
            print(f"⚠️ Client inactive or not found for content {original_content_id}")
            return None

        # Check if client hasn't exceeded monthly limit
        if client.posts_this_month >= client.monthly_post_limit:
            print(f"⚠️ Client {client.business_name} has reached monthly limit")
            return None

        try:
            # Generate fresh caption with seasonal/local updates
            location = original.focus_location or client.service_area or f"{client.city}, {client.state}"

            # Add recycling note to prompt
            recycling_note = f"This is a refreshed version of previous content about '{original.topic}'. Use NEW seasonal references, local details, or current events. Make it feel timely and relevant to today."

            ai_result = await ai_service.generate_social_post(
                business_name=client.business_name,
                industry=client.industry or "local business",
                topic=original.topic,
                location=location,
                content_type=original.content_type.value,
                brand_voice=client.brand_voice,
                notes=recycling_note,
            )

            # Create new content record (duplicate with fresh caption)
            new_content = Content(
                client_id=client.id,
                topic=f"[RECYCLED] {original.topic}",
                content_type=original.content_type,
                focus_location=original.focus_location,
                notes=f"Recycled from content #{original.id}",
                caption=ai_result["caption"],
                hashtags=ai_result["hashtags"],
                cta=ai_result["cta"],
                media_urls=original.media_urls,  # Reuse original media
                platforms=original.platforms,
                status=ContentStatus.APPROVED if client.auto_post else ContentStatus.PENDING_APPROVAL,
                ai_model_used=ai_result.get("model", "recycled"),
            )

            # Generate platform variations
            if new_content.platforms:
                platform_variations = await ai_service.generate_platform_variations(
                    base_caption=new_content.caption,
                    hashtags=new_content.hashtags,
                    cta=new_content.cta,
                    business_name=client.business_name,
                    location=location,
                    platforms=new_content.platforms,
                )
                new_content.platform_captions = platform_variations

            db.add(new_content)

            # Increment client's post count
            client.posts_this_month += 1

            await db.commit()
            await db.refresh(new_content)

            print(f"♻️ Recycled content {original_content_id} → new content {new_content.id}")

            return new_content.id

        except Exception as e:
            print(f"❌ Failed to recycle content {original_content_id}: {e}")
            return None


async def run_daily_recycling():
    """
    Daily task to find and recycle eligible content.

    Add to Celery beat schedule:
    ```python
    'daily-content-recycling': {
        'task': 'app.tasks.recycling_tasks.run_daily_recycling',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    }
    ```
    """
    print("🔄 Starting daily content recycling...")

    recyclable = await find_recyclable_content()

    if not recyclable:
        print("✅ No content eligible for recycling today")
        return

    print(f"📦 Found {len(recyclable)} pieces of content to recycle")

    recycled_count = 0
    for content in recyclable:
        new_id = await recycle_content(content.id)
        if new_id:
            recycled_count += 1

    print(f"♻️ Recycled {recycled_count}/{len(recyclable)} pieces of content")


async def recycle_content_by_client(client_id: int, max_count: int = 5) -> List[int]:
    """
    Manually recycle top-performing content for a specific client.

    Useful for:
    - Filling content gaps
    - Onboarding new clients with sample content
    - Emergency content needs

    Returns:
        List of new content IDs
    """
    async with AsyncSessionLocal() as db:
        # Find client's best-performing published content
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        result = await db.execute(
            select(Content)
            .where(
                and_(
                    Content.client_id == client_id,
                    Content.status == ContentStatus.PUBLISHED,
                    Content.published_at <= thirty_days_ago,
                    Content.error_message.is_(None),
                )
            )
            .order_by(Content.published_at.desc())
            .limit(max_count)
        )

        eligible = result.scalars().all()

        new_ids = []
        for content in eligible:
            new_id = await recycle_content(content.id)
            if new_id:
                new_ids.append(new_id)

        print(f"♻️ Manually recycled {len(new_ids)} pieces for client {client_id}")

        return new_ids
