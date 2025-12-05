from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.services.analytics import analytics_service

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_analytics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall dashboard analytics.

    Returns:
    - Total posts published
    - Success rate
    - Platform breakdown
    - Client activity
    """

    stats = await analytics_service.get_dashboard_stats(days=days)

    return {
        "success": True,
        "data": stats,
    }


@router.get("/client/{client_name}")
async def get_client_analytics(
    client_name: str,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics for a specific client.

    Returns:
    - Client posting activity
    - Platform distribution
    - Weekly trends
    - Success rate
    """

    stats = await analytics_service.get_client_analytics(
        client_name=client_name,
        days=days,
    )

    return {
        "success": True,
        "data": stats,
    }


@router.get("/platforms")
async def get_platform_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics broken down by platform.

    Returns:
    - Posts per platform
    - Success rates per platform
    """

    stats = await analytics_service.get_platform_analytics(days=days)

    return {
        "success": True,
        "data": stats,
    }


@router.get("/time-series")
async def get_time_series_analytics(
    days: int = Query(default=30, ge=1, le=365),
    interval: str = Query(default="daily", regex="^(daily|weekly)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get time-series posting data.

    Returns:
    - Daily or weekly posting trends
    - Success/failure counts over time
    """

    stats = await analytics_service.get_time_series_data(
        days=days,
        interval=interval,
    )

    return {
        "success": True,
        "data": stats,
    }


@router.get("/summary")
async def get_analytics_summary(
    days: int = Query(default=7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Get quick summary for dashboard header/cards.

    Returns:
    - Total posts
    - Success rate
    - Top platform
    - Most active client
    """

    dashboard = await analytics_service.get_dashboard_stats(days=days)

    # Find top platform
    platforms = dashboard.get("platforms", {})
    top_platform = max(platforms.items(), key=lambda x: x[1])[0] if platforms else "N/A"

    # Find most active client
    clients = dashboard.get("clients", {})
    top_client = max(clients.items(), key=lambda x: x[1])[0] if clients else "N/A"

    return {
        "success": True,
        "data": {
            "total_posts": dashboard["total_posts"],
            "success_rate": dashboard["success_rate"],
            "top_platform": top_platform,
            "most_active_client": top_client,
            "period_days": days,
        }
    }


@router.get("/engagement")
async def get_engagement_metrics(
    client_id: Optional[int] = Query(default=None, description="Filter by client ID"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get real engagement metrics from Publer API.

    Returns:
    - Total and average likes, comments, shares
    - Total and average impressions, reach
    - Engagement rate
    - Posts analyzed count
    """

    metrics = await analytics_service.get_engagement_metrics(
        db=db,
        client_id=client_id,
        days=days,
    )

    return {
        "success": True,
        "data": metrics,
    }


@router.get("/top-posts")
async def get_top_performing_posts(
    client_id: Optional[int] = Query(default=None, description="Filter by client ID"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of posts to return"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top performing posts based on engagement.

    Returns:
    - List of posts sorted by total engagement
    - Each post includes metrics: likes, comments, shares, impressions, reach
    """

    posts = await analytics_service.get_top_performing_posts(
        db=db,
        client_id=client_id,
        limit=limit,
        days=days,
    )

    return {
        "success": True,
        "data": posts,
    }
