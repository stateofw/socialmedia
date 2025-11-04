from app.tasks import celery_app
from sqlalchemy import select
from app.models.content import Content, ContentStatus
from app.models.client import Client
from app.models.platform_config import PlatformConfig
from app.services.social import social_service
from app.services.wordpress import wordpress_service
from app.services.email import email_service
from app.services.placid import placid_service
from app.services.sheets import sheets_service
from app.core.config import settings
from datetime import datetime
import asyncio


@celery_app.task(name="publish_content")
def publish_content_task(content_id: int):
    """
    Celery task to publish content to all configured platforms.
    """
    import asyncio

    asyncio.run(_publish_content(content_id))


async def _publish_content(content_id: int):
    """Internal async function to publish content."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get content
        content_result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()

        if not content or content.status != ContentStatus.APPROVED:
            print(f"⚠️ Content {content_id} not ready for publishing")
            return

        # Get client
        client_result = await db.execute(
            select(Client).where(Client.id == content.client_id)
        )
        client = client_result.scalar_one_or_none()

        if not client:
            return

        # Get platform configs
        platform_configs_result = await db.execute(
            select(PlatformConfig).where(
                PlatformConfig.client_id == client.id,
                PlatformConfig.is_active == True,
            )
        )
        platform_configs = platform_configs_result.scalars().all()

        # Optionally render a branded image via Placid before posting
        final_media_urls = content.media_urls or []
        if final_media_urls:
            try:
                placid_url = await placid_service.generate_asset(
                    text_fields={
                        "title": content.topic[:80] if content.topic else "",
                        "caption": (content.caption or "")[:180],
                    },
                    image_url=final_media_urls[0],
                )
                if placid_url:
                    final_media_urls = [placid_url]
            except Exception as e:
                print(f"⚠️ Placid step skipped: {e}")

        # Publish to each platform with retries
        post_ids = {}
        errors = []

        for platform_config in platform_configs:
            platform = platform_config.platform

            if platform not in content.platforms:
                continue

            # Get platform-specific caption or fallback to base caption
            platform_caption = content.platform_captions.get(platform) if content.platform_captions else None
            if not platform_caption:
                # Fallback to base caption with CTA and hashtags
                platform_caption = f"{content.caption}\n\n{content.cta}"
                if platform in ["instagram", "linkedin"]:
                    platform_caption += f"\n\n{' '.join(content.hashtags or [])}"

            # Use configurable retry settings
            max_retries = settings.MAX_RETRY_ATTEMPTS
            retry_delay = settings.RETRY_DELAY_SECONDS

            for attempt in range(1, max_retries + 1):
                try:
                    if platform == "facebook":
                        result = await social_service.post_to_facebook(
                            access_token=platform_config.access_token,
                            page_id=platform_config.platform_user_id,
                            message=platform_caption,
                            media_urls=final_media_urls,
                            scheduled_time=content.scheduled_at,
                        )
                        post_ids["facebook"] = result.get("id")

                    elif platform == "instagram":
                        # Instagram requires media - validate before attempting
                        if not final_media_urls:
                            error_msg = f"instagram: Instagram posts require at least one image or video"
                            errors.append(error_msg)
                            print(f"❌ {error_msg}")
                            break  # Skip retries, this is a validation error

                        result = await social_service.post_to_instagram(
                            access_token=platform_config.access_token,
                            instagram_account_id=platform_config.platform_user_id,
                            caption=platform_caption,
                            media_url=final_media_urls[0],
                            scheduled_time=content.scheduled_at,
                        )
                        post_ids["instagram"] = result.get("id")

                    elif platform == "google_business":
                        result = await social_service.post_to_google_business(
                            access_token=platform_config.access_token,
                            location_id=platform_config.platform_user_id,
                            message=platform_caption,
                            media_urls=final_media_urls,
                            cta_url=client.website_url,
                        )
                        post_ids["google_business"] = result.get("name")

                    elif platform == "linkedin":
                        result = await social_service.post_to_linkedin(
                            access_token=platform_config.access_token,
                            person_urn=platform_config.platform_user_id,
                            text=platform_caption,
                            media_urls=final_media_urls,
                        )
                        post_ids["linkedin"] = result.get("id")

                    print(f"✅ Published to {platform} for content {content_id}")
                    break

                except Exception as e:
                    # Track retry attempts in database
                    content.retry_count = attempt
                    await db.commit()

                    if attempt < max_retries:
                        print(f"🔁 Retry {attempt}/{max_retries} for {platform}: {e}")
                        await asyncio.sleep(retry_delay)
                        continue

                    # Max retries exhausted
                    error_msg = f"{platform}: {str(e)}"
                    errors.append(error_msg)
                    print(f"❌ Failed to publish to {platform} after {max_retries} retries: {str(e)}")

                    # Send notification email if retry limit reached
                    from app.models.user import User
                    if client.owner_id:
                        owner_result = await db.execute(
                            select(User).where(User.id == client.owner_id)
                        )
                        owner = owner_result.scalar_one_or_none()
                        if owner and owner.email:
                            try:
                                await email_service.notify_retry_limit_reached(
                                    team_email=owner.email,
                                    client_name=client.business_name,
                                    content_id=content_id,
                                    platform=platform,
                                    error_message=str(e),
                                    retry_count=max_retries,
                                )
                            except Exception as email_error:
                                print(f"⚠️ Failed to send retry exhaustion email: {email_error}")

        # Update content status
        if post_ids:
            content.platform_post_ids = post_ids
            content.status = ContentStatus.PUBLISHED
            content.published_at = datetime.utcnow()
        else:
            content.status = ContentStatus.FAILED

        if errors:
            content.error_message = "; ".join(errors)

        await db.commit()

        # Send notification email to client if published successfully
        if post_ids and client.website_url:  # Assuming we'd store client email
            # Build post URLs from post_ids
            post_urls = {}
            for platform, post_id in post_ids.items():
                if platform == "facebook":
                    post_urls[platform] = f"https://www.facebook.com/{post_id}"
                elif platform == "instagram":
                    post_urls[platform] = f"https://www.instagram.com/p/{post_id}"
                elif platform == "google_business":
                    post_urls[platform] = f"https://business.google.com"
                elif platform == "linkedin":
                    post_urls[platform] = f"https://www.linkedin.com/feed/update/{post_id}"

            # TODO: Add client email field to Client model
            # For now, we can send to owner
            # await email_service.notify_content_published(
            #     client_email=client_email,
            #     client_name=client.business_name,
            #     topic=content.topic,
            #     platforms=list(post_ids.keys()),
            #     post_urls=post_urls,
            # )

        # Log to Google Sheets or CSV fallback
        try:
            await sheets_service.append_publish_log(
                client_name=client.business_name,
                content_id=content_id,
                status=content.status.value,
                final_caption=content.caption,
                final_image_url=(final_media_urls[0] if final_media_urls else None),
                platform_post_ids=post_ids,
            )
        except Exception as e:
            print(f"⚠️ Logging skipped: {e}")


@celery_app.task(name="publish_blog")
def publish_blog_task(content_id: int):
    """
    Celery task to publish blog post to WordPress.
    """
    import asyncio

    asyncio.run(_publish_blog(content_id))


async def _publish_blog(content_id: int):
    """Internal async function to publish blog."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get content
        content_result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()

        if not content or not content.blog_content:
            return

        # Get client
        client_result = await db.execute(
            select(Client).where(Client.id == content.client_id)
        )
        client = client_result.scalar_one_or_none()

        if not client:
            return

        # Get WordPress config
        wp_config_result = await db.execute(
            select(PlatformConfig).where(
                PlatformConfig.client_id == client.id,
                PlatformConfig.platform == "wordpress",
                PlatformConfig.is_active == True,
            )
        )
        wp_config = wp_config_result.scalar_one_or_none()

        if not wp_config:
            print(f"⚠️ No WordPress config for client {client.id}")
            return

        try:
            # Publish to WordPress
            result = await wordpress_service.publish_post(
                site_url=wp_config.config.get("site_url"),
                username=wp_config.config.get("username"),
                app_password=wp_config.access_token,
                title=content.blog_title,
                content=content.blog_content,
                meta_title=content.blog_meta_title,
                meta_description=content.blog_meta_description,
                featured_image_url=content.media_urls[0] if content.media_urls else None,
                status="draft",  # Always create as draft first
            )

            content.blog_url = result.get("url")
            await db.commit()

            print(f"✅ Published blog to WordPress for content {content_id}")

        except Exception as e:
            print(f"❌ Failed to publish blog: {str(e)}")
