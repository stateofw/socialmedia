from app.tasks import celery_app
from sqlalchemy import select, func
from app.models.content import Content, ContentStatus
from app.models.client import Client
from app.models.user import User
from app.services.email import email_service
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


@celery_app.task(name="generate_monthly_reports")
def generate_monthly_reports_task():
    """
    Celery task to generate monthly reports for all active clients.
    Run this on the 1st of each month.
    """
    import asyncio

    asyncio.run(_generate_all_monthly_reports())


async def _generate_all_monthly_reports():
    """Generate reports for all active clients."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get all active clients
        result = await db.execute(
            select(Client).where(Client.is_active == True)
        )
        clients = result.scalars().all()

        for client in clients:
            await _generate_client_monthly_report(db, client)

        print(f"✅ Generated monthly reports for {len(clients)} clients")


async def _generate_client_monthly_report(db, client: Client):
    """Generate monthly report for a single client."""

    # Get last month's date range
    today = datetime.utcnow()
    last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_month_end = today.replace(day=1) - timedelta(days=1)

    month_name = last_month_start.strftime("%B %Y")

    # Get published posts from last month
    result = await db.execute(
        select(Content).where(
            Content.client_id == client.id,
            Content.status == ContentStatus.PUBLISHED,
            Content.published_at >= last_month_start,
            Content.published_at <= last_month_end,
        )
    )
    posts = result.scalars().all()

    total_posts = len(posts)

    if total_posts == 0:
        print(f"⚠️  No posts for {client.business_name} in {month_name}")
        return

    # Find top performing post (for now, just use most recent)
    # TODO: Integrate with analytics APIs to get actual engagement data
    top_post = posts[0] if posts else None
    top_post_url = None

    if top_post and top_post.platform_post_ids:
        # Get first available post URL
        for platform, post_id in top_post.platform_post_ids.items():
            if platform == "facebook":
                top_post_url = f"https://www.facebook.com/{post_id}"
                break
            elif platform == "instagram":
                top_post_url = f"https://www.instagram.com/p/{post_id}"
                break

    # TODO: Get actual engagement stats from platform APIs
    engagement_stats = {
        "total_likes": 0,
        "total_comments": 0,
    }

    # Get owner email (or client email if available)
    owner_result = await db.execute(
        select(User).where(User.id == client.owner_id)
    )
    owner = owner_result.scalar_one_or_none()

    if not owner or not owner.email:
        print(f"⚠️  No email for {client.business_name}")
        return

    # Send report email
    await email_service.send_monthly_report(
        client_email=owner.email,  # TODO: Use client.email when added
        client_name=client.business_name,
        month=month_name,
        total_posts=total_posts,
        top_post_url=top_post_url,
        engagement_stats=engagement_stats,
    )

    print(f"✅ Sent monthly report to {client.business_name}")


@celery_app.task(name="reset_monthly_post_counts")
def reset_monthly_post_counts_task():
    """
    Reset posts_this_month counter for all clients.
    Run this on the 1st of each month (before generating reports).
    """
    import asyncio

    asyncio.run(_reset_all_post_counts())


async def _reset_all_post_counts():
    """Reset post counts for all clients."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get all clients
        result = await db.execute(select(Client))
        clients = result.scalars().all()

        for client in clients:
            client.posts_this_month = 0

        await db.commit()

        print(f"✅ Reset post counts for {len(clients)} clients")


@celery_app.task(name="send_weekly_digest")
def send_weekly_digest_task():
    """
    Send weekly digest to team showing pending content, scheduled posts, etc.
    Run this every Monday morning.
    """
    import asyncio

    asyncio.run(_send_weekly_digest())


async def _send_weekly_digest():
    """Send weekly digest email to team."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get pending content count
        result = await db.execute(
            select(func.count(Content.id)).where(
                Content.status == ContentStatus.PENDING_APPROVAL
            )
        )
        pending_count = result.scalar()

        # Get scheduled content for this week
        today = datetime.utcnow()
        week_end = today + timedelta(days=7)

        result = await db.execute(
            select(func.count(Content.id)).where(
                Content.status == ContentStatus.SCHEDULED,
                Content.scheduled_at >= today,
                Content.scheduled_at <= week_end,
            )
        )
        scheduled_count = result.scalar()

        # Get all admin users
        result = await db.execute(
            select(User).where(User.is_superuser == True)
        )
        admins = result.scalars().all()

        # Send digest to each admin
        for admin in admins:
            # TODO: Create weekly digest email template
            print(f"📊 Weekly digest: {pending_count} pending, {scheduled_count} scheduled")
            # await email_service.send_weekly_digest(admin.email, pending_count, scheduled_count)
