"""
Analytics Dashboard Service

Reads data from Google Sheets publish logs and generates analytics insights.

Metrics:
- Total posts published
- Posts by platform
- Posts by client
- Success rate
- Content performance over time
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings
import json
import csv
from pathlib import Path


class AnalyticsService:
    """
    Dashboard analytics reading from Google Sheets or local CSV.

    Provides insights on:
    - Publishing activity
    - Platform distribution
    - Client activity
    - Success/failure rates
    - Time-based trends
    """

    def __init__(self):
        self.sheet_id = settings.GOOGLE_SHEETS_ID
        self.service_account_json = settings.GOOGLE_SERVICE_ACCOUNT_JSON
        self.csv_path = Path("logs/publish_log.csv")
        self._sheets_service = None

    def _get_sheets_service(self):
        """Initialize Google Sheets API service."""
        if self._sheets_service:
            return self._sheets_service

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            credentials_info = json.loads(self.service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )

            self._sheets_service = build('sheets', 'v4', credentials=credentials)
            return self._sheets_service

        except Exception as e:
            print(f"⚠️ Failed to initialize Sheets API: {e}")
            return None

    async def fetch_publish_logs(
        self,
        days: int = 30,
        client_name: Optional[str] = None,
    ) -> List[Dict]:
        """
        Fetch publish logs from Google Sheets or local CSV.

        Args:
            days: Number of days to look back
            client_name: Optional filter by client

        Returns:
            List of log entries
        """

        # Try Google Sheets first
        if self.sheet_id and self.service_account_json:
            logs = await self._fetch_from_sheets()
            if logs:
                return self._filter_logs(logs, days, client_name)

        # Fallback to CSV
        return await self._fetch_from_csv(days, client_name)

    async def _fetch_from_sheets(self) -> List[Dict]:
        """Fetch logs from Google Sheets."""
        service = self._get_sheets_service()
        if not service:
            return []

        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='A:G'  # All columns
            ).execute()

            rows = result.get('values', [])

            if not rows or len(rows) < 2:
                return []

            # Parse header and data
            header = rows[0]
            logs = []

            for row in rows[1:]:
                if len(row) >= 7:
                    log = {
                        "timestamp": row[0],
                        "client_name": row[1],
                        "content_id": row[2],
                        "status": row[3],
                        "final_caption": row[4],
                        "final_image_url": row[5],
                        "platform_post_ids": row[6],
                    }
                    logs.append(log)

            print(f"📊 Fetched {len(logs)} logs from Google Sheets")
            return logs

        except Exception as e:
            print(f"❌ Failed to fetch from Sheets: {e}")
            return []

    async def _fetch_from_csv(self, days: int, client_name: Optional[str]) -> List[Dict]:
        """Fetch logs from local CSV."""
        if not self.csv_path.exists():
            return []

        logs = []
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        try:
            with self.csv_path.open('r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Filter by date
                    try:
                        log_date = datetime.fromisoformat(row['timestamp'])
                        if log_date < cutoff_date:
                            continue
                    except:
                        pass

                    # Filter by client
                    if client_name and row.get('client_name') != client_name:
                        continue

                    logs.append(row)

            print(f"📊 Fetched {len(logs)} logs from CSV")
            return logs

        except Exception as e:
            print(f"❌ Failed to read CSV: {e}")
            return []

    def _filter_logs(
        self,
        logs: List[Dict],
        days: int,
        client_name: Optional[str]
    ) -> List[Dict]:
        """Filter logs by date and client."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        filtered = []

        for log in logs:
            # Filter by date
            try:
                log_date = datetime.fromisoformat(log['timestamp'])
                if log_date < cutoff_date:
                    continue
            except:
                pass

            # Filter by client
            if client_name and log.get('client_name') != client_name:
                continue

            filtered.append(log)

        return filtered

    async def get_dashboard_stats(self, days: int = 30) -> Dict:
        """
        Get overall dashboard statistics.

        Returns:
            Dict with key metrics
        """

        logs = await self.fetch_publish_logs(days=days)

        if not logs:
            return {
                "total_posts": 0,
                "successful_posts": 0,
                "failed_posts": 0,
                "success_rate": 0.0,
                "platforms": {},
                "clients": {},
                "period_days": days,
            }

        # Calculate metrics
        total = len(logs)
        successful = sum(1 for log in logs if log.get('status') in ['published', 'scheduled'])
        failed = total - successful

        # Platform breakdown
        platform_counts = {}
        for log in logs:
            # Parse platform_post_ids JSON
            try:
                platform_data = json.loads(log.get('platform_post_ids', '{}'))
                for platform in platform_data.keys():
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1
            except:
                pass

        # Client breakdown
        client_counts = {}
        for log in logs:
            client = log.get('client_name', 'Unknown')
            client_counts[client] = client_counts.get(client, 0) + 1

        return {
            "total_posts": total,
            "successful_posts": successful,
            "failed_posts": failed,
            "success_rate": round((successful / total * 100) if total > 0 else 0, 2),
            "platforms": platform_counts,
            "clients": client_counts,
            "period_days": days,
        }

    async def get_client_analytics(self, client_name: str, days: int = 30) -> Dict:
        """
        Get analytics for a specific client.

        Args:
            client_name: Client business name
            days: Number of days to analyze

        Returns:
            Dict with client-specific metrics
        """

        logs = await self.fetch_publish_logs(days=days, client_name=client_name)

        if not logs:
            return {
                "client_name": client_name,
                "total_posts": 0,
                "period_days": days,
            }

        total = len(logs)
        successful = sum(1 for log in logs if log.get('status') in ['published', 'scheduled'])

        # Platform distribution
        platforms = {}
        for log in logs:
            try:
                platform_data = json.loads(log.get('platform_post_ids', '{}'))
                for platform in platform_data.keys():
                    platforms[platform] = platforms.get(platform, 0) + 1
            except:
                pass

        # Time series (posts per week)
        weekly_counts = {}
        for log in logs:
            try:
                log_date = datetime.fromisoformat(log['timestamp'])
                week = log_date.strftime('%Y-W%W')
                weekly_counts[week] = weekly_counts.get(week, 0) + 1
            except:
                pass

        return {
            "client_name": client_name,
            "total_posts": total,
            "successful_posts": successful,
            "failed_posts": total - successful,
            "success_rate": round((successful / total * 100) if total > 0 else 0, 2),
            "platforms": platforms,
            "weekly_activity": weekly_counts,
            "period_days": days,
        }

    async def get_platform_analytics(self, days: int = 30) -> Dict:
        """
        Get analytics broken down by platform.

        Returns:
            Dict with platform-specific metrics
        """

        logs = await self.fetch_publish_logs(days=days)

        platform_stats = {}

        for log in logs:
            try:
                platform_data = json.loads(log.get('platform_post_ids', '{}'))
                status = log.get('status', 'unknown')

                for platform in platform_data.keys():
                    if platform not in platform_stats:
                        platform_stats[platform] = {
                            "total": 0,
                            "successful": 0,
                            "failed": 0,
                        }

                    platform_stats[platform]["total"] += 1

                    if status in ['published', 'scheduled']:
                        platform_stats[platform]["successful"] += 1
                    else:
                        platform_stats[platform]["failed"] += 1

            except:
                pass

        # Calculate success rates
        for platform, stats in platform_stats.items():
            total = stats["total"]
            stats["success_rate"] = round((stats["successful"] / total * 100) if total > 0 else 0, 2)

        return {
            "platforms": platform_stats,
            "period_days": days,
        }

    async def get_time_series_data(self, days: int = 30, interval: str = "daily") -> Dict:
        """
        Get time-series posting data.

        Args:
            days: Number of days to analyze
            interval: "daily" or "weekly"

        Returns:
            Dict with time-series data
        """

        logs = await self.fetch_publish_logs(days=days)

        time_series = {}

        for log in logs:
            try:
                log_date = datetime.fromisoformat(log['timestamp'])

                if interval == "daily":
                    key = log_date.strftime('%Y-%m-%d')
                else:  # weekly
                    key = log_date.strftime('%Y-W%W')

                if key not in time_series:
                    time_series[key] = {"total": 0, "successful": 0, "failed": 0}

                time_series[key]["total"] += 1

                if log.get('status') in ['published', 'scheduled']:
                    time_series[key]["successful"] += 1
                else:
                    time_series[key]["failed"] += 1

            except:
                pass

        # Sort by date
        sorted_series = dict(sorted(time_series.items()))

        return {
            "interval": interval,
            "data": sorted_series,
            "period_days": days,
        }


# Singleton instance
analytics_service = AnalyticsService()
