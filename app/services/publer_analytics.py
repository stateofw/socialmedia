"""
Publer Analytics Service
Fetches real engagement data from Publer API
"""

import httpx
from typing import Optional, Dict, List
from app.core.config import settings


class PublerAnalyticsService:
    """Service to fetch analytics from Publer API"""

    BASE_URL = "https://api.publer.io/v1"

    async def get_post_analytics(self, post_id: str) -> Optional[Dict]:
        """
        Get analytics for a single post from Publer.
        
        Args:
            post_id: The Publer post ID
            
        Returns:
            Dict with engagement metrics or None if failed
        """
        
        if not settings.PUBLER_API_KEY:
            print("⚠️ PUBLER_API_KEY not configured")
            return None
        
        headers = {
            "Authorization": f"Bearer {settings.PUBLER_API_KEY}",
            "Content-Type": "application/json",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/posts/{post_id}/analytics",
                    headers=headers,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "likes": data.get("likes", 0),
                        "comments": data.get("comments", 0),
                        "shares": data.get("shares", 0),
                        "impressions": data.get("impressions", 0),
                        "reach": data.get("reach", 0),
                        "engagement_rate": data.get("engagement_rate", 0),
                    }
                else:
                    print(f"⚠️ Publer analytics API returned {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ Failed to fetch Publer analytics: {e}")
            return None

    async def get_posts_analytics(self, post_ids: List[str]) -> Dict[str, Dict]:
        """
        Get analytics for multiple posts.
        
        Args:
            post_ids: List of Publer post IDs
            
        Returns:
            Dict mapping post_id to analytics data
        """
        
        results = {}
        
        for post_id in post_ids:
            analytics = await self.get_post_analytics(post_id)
            if analytics:
                results[post_id] = analytics
        
        return results

    async def get_workspace_analytics(
        self, 
        workspace_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get overall analytics for a workspace.
        
        Args:
            workspace_id: Publer workspace ID (uses default if not provided)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dict with aggregate metrics or None if failed
        """
        
        if not settings.PUBLER_API_KEY:
            return None
        
        workspace = workspace_id or settings.PUBLER_WORKSPACE_ID
        if not workspace:
            return None
        
        headers = {
            "Authorization": f"Bearer {settings.PUBLER_API_KEY}",
            "Content-Type": "application/json",
        }
        
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/workspaces/{workspace}/analytics",
                    headers=headers,
                    params=params,
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"⚠️ Publer workspace analytics returned {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ Failed to fetch workspace analytics: {e}")
            return None

    def calculate_total_engagement(self, analytics: Dict) -> int:
        """Calculate total engagement from analytics dict"""
        return (
            analytics.get("likes", 0) +
            analytics.get("comments", 0) +
            analytics.get("shares", 0)
        )


# Singleton instance
publer_analytics = PublerAnalyticsService()
