from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.content import Content, ContentStatus
from app.models.client import Client
from app.services.email import email_service
from app.services.sheets import sheets_service
from app.services.publer import publer_service
from app.services.placid import placid_service

router = APIRouter()


@router.get("/approve")
async def approve_content(
    post_id: int = Query(..., description="Content ID to approve"),
    approved: bool = Query(..., description="True to approve, False to reject"),
    rejection_reason: Optional[str] = Query(None, description="Reason for rejection"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Approve or reject content via email link.

    URL format: /api/v1/approval/approve?post_id=123&approved=true
    """

    # Get content
    result = await db.execute(
        select(Content).where(Content.id == post_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Get client
    client_result = await db.execute(
        select(Client).where(Client.id == content.client_id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if approved:
        # APPROVED - Schedule for publishing
        content.status = ContentStatus.APPROVED
        await db.commit()

        # Trigger publishing in background
        if background_tasks:
            background_tasks.add_task(
                publish_approved_content,
                content_id=content.id,
                client_id=client.id,
            )

        return {
            "message": f"Content approved for {client.business_name}!",
            "content_id": content.id,
            "status": "approved",
            "next_step": "Publishing to social media...",
        }

    else:
        # REJECTED - Mark for regeneration
        content.status = ContentStatus.REJECTED
        content.rejection_reason = rejection_reason or "No reason provided"
        content.retry_count += 1
        await db.commit()

        # Optionally trigger regeneration
        if content.retry_count < 3:  # Max 3 retries
            if background_tasks:
                background_tasks.add_task(
                    regenerate_rejected_content,
                    content_id=content.id,
                )

        return {
            "message": f"Content rejected. Reason: {rejection_reason or 'Not specified'}",
            "content_id": content.id,
            "status": "rejected",
            "retry_count": content.retry_count,
            "next_step": "Regenerating with different tone..." if content.retry_count < 3 else "Max retries reached",
        }


@router.post("/{content_id}/approve")
async def approve_content_direct(
    content_id: int,
    approved: bool,
    scheduled_time: Optional[datetime] = None,
    rejection_reason: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Direct API endpoint to approve/reject content and schedule to Publer.

    Args:
        content_id: The content ID to approve
        approved: True to approve, False to reject
        scheduled_time: Optional datetime to schedule the post (UTC). If None, schedules for 1 hour from now.
        rejection_reason: Optional reason for rejection
    """

    # Get content
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Get client
    client_result = await db.execute(
        select(Client).where(Client.id == content.client_id)
    )
    client = client_result.scalar_one_or_none()

    if approved:
        content.status = ContentStatus.APPROVED

        # Set default schedule time if not provided (1 hour from now)
        if not scheduled_time:
            from datetime import timedelta
            scheduled_time = datetime.utcnow() + timedelta(hours=1)

        content.scheduled_at = scheduled_time
        await db.commit()

        # Trigger publishing to Publer
        if background_tasks:
            background_tasks.add_task(
                publish_approved_content,
                content_id=content.id,
                client_id=client.id,
            )

        return {
            "message": "Content approved and scheduled for publishing",
            "content_id": content.id,
            "status": "approved",
            "scheduled_at": scheduled_time.isoformat(),
        }

    else:
        content.status = ContentStatus.REJECTED
        content.rejection_reason = rejection_reason or "No reason provided"
        content.retry_count += 1
        await db.commit()

        # Trigger regeneration
        if content.retry_count < 3 and background_tasks:
            background_tasks.add_task(
                regenerate_rejected_content,
                content_id=content.id,
            )

        return {
            "message": "Content rejected",
            "content_id": content.id,
            "status": "rejected",
        }


async def publish_approved_content(content_id: int, client_id: int):
    """
    Background task to schedule approved content to Publer.

    Flow:
    1. Get content and client from DB
    2. Build platform-specific content dict
    3. Schedule to Publer with scheduled_at time
    4. Update content status
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get content and client
        content_result = await db.execute(select(Content).where(Content.id == content_id))
        content = content_result.scalar_one_or_none()

        client_result = await db.execute(select(Client).where(Client.id == client_id))
        client = client_result.scalar_one_or_none()

        if not content or not client:
            print(f"❌ Content or client not found: {content_id}")
            return

        # Check if client has Publer accounts configured
        if not client.publer_account_ids or len(client.publer_account_ids) == 0:
            print(f"⚠️ No Publer accounts configured for client {client.business_name}")
            content.status = ContentStatus.FAILED
            content.error_message = "No Publer accounts configured for this client"
            await db.commit()
            return

        try:
            print(f"📤 Scheduling content {content_id} to Publer...")

            # Build platform-specific content dict
            content_dict = {}

            # Map our platform names to Publer's expected format
            platform_map = {
                "facebook": "facebook",
                "instagram": "instagram",
                "twitter": "twitter",
                "linkedin": "linkedin",
                "pinterest": "pinterest",
                "google_business": "gmb",
            }

            # Build full post text with caption, hashtags, and CTA
            def build_post_text(platform):
                """Build complete post text for a platform"""
                parts = []
                
                # Add caption
                if content.caption:
                    parts.append(content.caption)
                
                # Add CTA
                if content.cta:
                    parts.append(f"\n{content.cta}")
                
                # Add hashtags (for platforms that support them)
                if content.hashtags and platform in ["instagram", "twitter", "linkedin", "facebook"]:
                    hashtag_string = " ".join([f"#{tag}" for tag in content.hashtags])
                    parts.append(f"\n\n{hashtag_string}")
                
                return "\n".join(parts) if parts else content.topic

            # Prepare media URLs for Publer
            media_urls = content.media_urls or []

            # Use platform_captions if available, otherwise use base caption
            if content.platform_captions:
                for platform, caption_text in content.platform_captions.items():
                    publer_platform = platform_map.get(platform, platform)
                    
                    post_config = {
                        "text": caption_text,
                    }
                    
                    # Add media if available
                    if media_urls:
                        post_config["type"] = "photo" if media_urls else "status"
                        post_config["media"] = [{"url": url} for url in media_urls]
                    else:
                        post_config["type"] = "status"
                    
                    content_dict[publer_platform] = post_config
            else:
                # Fallback: use base caption for all platforms
                for platform in content.platforms or []:
                    publer_platform = platform_map.get(platform, platform)
                    
                    post_config = {
                        "text": build_post_text(platform),
                    }
                    
                    # Add media if available
                    if media_urls:
                        post_config["type"] = "photo"
                        post_config["media"] = [{"url": url} for url in media_urls]
                    else:
                        post_config["type"] = "status"
                    
                    content_dict[publer_platform] = post_config

            if not content_dict:
                raise Exception("No platforms configured")
            
            print(f"📷 Media URLs: {media_urls}")
            print(f"📝 Caption: {content.caption[:100] if content.caption else 'None'}...")
            print(f"🏷️  Hashtags: {content.hashtags}")
            print(f"📣 CTA: {content.cta}")

            print(f"📝 Scheduling to platforms: {list(content_dict.keys())}")
            print(f"📅 Scheduled time: {content.scheduled_at}")

            # Schedule to Publer using client's workspace
            result = await publer_service.schedule_post(
                account_ids=client.publer_account_ids,
                content_dict=content_dict,
                scheduled_time=content.scheduled_at,
                workspace_id=client.publer_workspace_id,
            )

            # Update content with result
            if result.get("status") == "success":
                content.status = ContentStatus.SCHEDULED
                content.platform_post_ids = result.get("platform_post_ids", {})
                print(f"✅ Scheduled content {content_id} to Publer successfully")
            else:
                content.status = ContentStatus.FAILED
                content.error_message = f"Publer scheduling failed: {result.get('error', 'Unknown error')}"
                print(f"❌ Publer scheduling failed for content {content_id}: {content.error_message}")

            await db.commit()

        except Exception as e:
            content.status = ContentStatus.FAILED
            content.error_message = f"Publishing error: {str(e)}"
            await db.commit()
            print(f"❌ Publishing failed for content {content_id}: {e}")
            import traceback
            traceback.print_exc()


async def regenerate_rejected_content(content_id: int):
    """
    Background task to regenerate rejected content with different tone/approach.
    """
    from app.core.database import AsyncSessionLocal
    from app.services.ai import ai_service

    async with AsyncSessionLocal() as db:
        content_result = await db.execute(select(Content).where(Content.id == content_id))
        content = content_result.scalar_one_or_none()

        if not content:
            return

        client_result = await db.execute(select(Client).where(Client.id == content.client_id))
        client = client_result.scalar_one_or_none()

        if not client:
            return

        try:
            # Mark as retrying
            content.status = ContentStatus.RETRYING
            await db.commit()

            # Regenerate with modified prompt (add rejection feedback)
            notes = content.notes or ""
            notes += f"\n\nPrevious attempt was rejected: {content.rejection_reason}. Try a different angle or tone."

            ai_result = await ai_service.generate_social_post(
                business_name=client.business_name,
                industry=client.industry or "local business",
                topic=content.topic,
                location=content.focus_location or client.service_area or f"{client.city}, {client.state}",
                content_type=content.content_type.value,
                brand_voice=client.brand_voice,
                notes=notes,
            )

            # Update content
            content.caption = ai_result["caption"]
            content.hashtags = ai_result["hashtags"]
            content.cta = ai_result["cta"]
            content.status = ContentStatus.PENDING_APPROVAL

            # Generate platform variations
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

            print(f"✅ Regenerated content {content_id} (retry #{content.retry_count})")

            # Send new approval email
            # TODO: Implement email notification

        except Exception as e:
            content.status = ContentStatus.FAILED
            content.error_message = f"Regeneration failed: {str(e)}"
            await db.commit()
            print(f"❌ Regeneration failed for content {content_id}: {e}")
