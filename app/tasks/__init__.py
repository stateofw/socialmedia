from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "social_automation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Configure Celery Beat Schedule
celery_app.conf.beat_schedule = {
    # Reset monthly post counts on the 1st of each month at midnight
    "reset-monthly-counts": {
        "task": "reset_monthly_post_counts",
        "schedule": crontab(day_of_month="1", hour="0", minute="0"),
    },
    # Generate monthly reports on the 1st of each month at 9am
    "generate-monthly-reports": {
        "task": "generate_monthly_reports",
        "schedule": crontab(day_of_month="1", hour="9", minute="0"),
    },
    # Send weekly digest every Monday at 8am
    "send-weekly-digest": {
        "task": "send_weekly_digest",
        "schedule": crontab(day_of_week="monday", hour="8", minute="0"),
    },
}

# Import tasks
from app.tasks import content_tasks, posting_tasks, report_tasks

__all__ = ["celery_app"]
