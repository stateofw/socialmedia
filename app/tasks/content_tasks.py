from app.tasks import celery_app
from sqlalchemy import select
from app.models.content import Content, ContentStatus
from app.models.client import Client
from app.services.ai import ai_service


@celery_app.task(name="generate_content")
def generate_content_task(content_id: int):
    """
    Celery task to generate AI content for a post.
    This runs asynchronously in the background.
    """
    import asyncio

    asyncio.run(_generate_content(content_id))


async def _generate_content(content_id: int):
    """Internal async function to generate content."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get content and client
        content_result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()

        if not content:
            return

        client_result = await db.execute(
            select(Client).where(Client.id == content.client_id)
        )
        client = client_result.scalar_one_or_none()

        if not client:
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

            # Update content
            content.caption = ai_result["caption"]
            content.hashtags = ai_result["hashtags"]
            content.cta = ai_result["cta"]
            content.status = ContentStatus.PENDING_APPROVAL
            content.ai_model_used = "gpt-4-turbo-preview"

            # Generate platform-specific caption variations
            try:
                if content.platforms:
                    variations = await ai_service.generate_platform_variations(
                        base_caption=content.caption or "",
                        hashtags=content.hashtags or [],
                        cta=content.cta or "",
                        business_name=client.business_name,
                        location=content.focus_location or client.city or "",
                        platforms=content.platforms,
                    )
                    content.platform_captions = variations
            except Exception as e:
                print(f"⚠️ Failed to generate platform variations: {e}")

            await db.commit()

            print(f"✅ Generated content for {content_id}")

        except Exception as e:
            content.status = ContentStatus.FAILED
            content.error_message = str(e)
            await db.commit()
            print(f"❌ Failed to generate content for {content_id}: {str(e)}")


@celery_app.task(name="generate_blog")
def generate_blog_task(content_id: int):
    """
    Celery task to generate a blog post from social content.
    """
    import asyncio

    asyncio.run(_generate_blog(content_id))


async def _generate_blog(content_id: int):
    """Internal async function to generate blog post."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get content and client
        content_result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()

        if not content:
            return

        client_result = await db.execute(
            select(Client).where(Client.id == content.client_id)
        )
        client = client_result.scalar_one_or_none()

        if not client or not content.caption:
            return

        try:
            # Generate blog post
            blog_result = await ai_service.generate_blog_post(
                business_name=client.business_name,
                industry=client.industry or "local business",
                topic=content.topic,
                location=content.focus_location or client.service_area or f"{client.city}, {client.state}",
                website_url=client.website_url or "",
                short_caption=content.caption,
                brand_voice=client.brand_voice,
            )

            # Update content
            content.blog_title = blog_result["title"]
            content.blog_meta_title = blog_result["meta_title"]
            content.blog_meta_description = blog_result["meta_description"]
            content.blog_content = blog_result["content"]

            await db.commit()

            print(f"✅ Generated blog for content {content_id}")

        except Exception as e:
            print(f"❌ Failed to generate blog for {content_id}: {str(e)}")


@celery_app.task(name="publish_blog_to_wordpress")
def publish_blog_to_wordpress_task(content_id: int, publish_status: str = "draft"):
    """
    Celery task to publish a blog post to WordPress.

    Args:
        content_id: The content ID with blog content
        publish_status: "draft" or "publish"
    """
    import asyncio

    asyncio.run(_publish_blog_to_wordpress(content_id, publish_status))


async def _publish_blog_to_wordpress(content_id: int, publish_status: str):
    """Internal async function to publish blog to WordPress."""
    from app.core.database import AsyncSessionLocal
    from app.models.platform_config import PlatformConfig
    from app.services.wordpress import wordpress_service

    async with AsyncSessionLocal() as db:
        # Get content and client
        content_result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()

        if not content or not content.blog_title or not content.blog_content:
            print(f"❌ Content {content_id} has no blog content to publish")
            return

        client_result = await db.execute(
            select(Client).where(Client.id == content.client_id)
        )
        client = client_result.scalar_one_or_none()

        if not client:
            return

        # Get WordPress configuration
        wp_config_result = await db.execute(
            select(PlatformConfig)
            .where(PlatformConfig.client_id == client.id)
            .where(PlatformConfig.platform == "wordpress")
            .where(PlatformConfig.is_active == True)
        )
        wp_config = wp_config_result.scalar_one_or_none()

        if not wp_config:
            print(f"❌ No WordPress configuration found for client {client.id}")
            return

        try:
            # Get WordPress credentials from config
            site_url = wp_config.config.get("site_url")
            username = wp_config.config.get("username")
            password = wp_config.access_token  # Stored in access_token field

            if not all([site_url, username, password]):
                print(f"❌ Incomplete WordPress credentials for client {client.id}")
                return

            # Prepare featured image URL (use first media URL if available)
            featured_image_url = content.media_urls[0] if content.media_urls else None

            # Publish to WordPress
            result = await wordpress_service.publish_post(
                site_url=site_url,
                username=username,
                app_password=password,
                title=content.blog_title,
                content=content.blog_content,
                status=publish_status,
                featured_image_url=featured_image_url,
                meta_title=content.blog_meta_title,
                meta_description=content.blog_meta_description,
            )

            # Update content with WordPress URL
            content.blog_url = result.get("url")

            await db.commit()

            print(f"✅ Published blog to WordPress for content {content_id}: {result.get('url')}")

        except Exception as e:
            print(f"❌ Failed to publish blog to WordPress for {content_id}: {str(e)}")
