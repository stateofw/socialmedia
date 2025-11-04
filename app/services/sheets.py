from typing import Dict, Optional
from datetime import datetime
from app.core.config import settings
import csv
import json
from pathlib import Path


class SheetsService:
    """Append publish logs to Google Sheets if configured; otherwise CSV fallback.

    Uses google-api-python-client with service account credentials.
    Falls back to CSV if credentials are not configured.
    """

    def __init__(self) -> None:
        self.sheet_id = settings.GOOGLE_SHEETS_ID
        self.service_account_json = settings.GOOGLE_SERVICE_ACCOUNT_JSON
        self.csv_path = Path("logs/publish_log.csv")
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self._sheets_service = None

    def _get_sheets_service(self):
        """Initialize and return Google Sheets API service."""
        if self._sheets_service:
            return self._sheets_service

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            # Parse service account JSON
            credentials_info = json.loads(self.service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

            self._sheets_service = build('sheets', 'v4', credentials=credentials)
            return self._sheets_service

        except Exception as e:
            print(f"⚠️ Failed to initialize Google Sheets API: {e}")
            return None

    async def append_publish_log(
        self,
        client_name: str,
        content_id: int,
        status: str,
        final_caption: Optional[str],
        final_image_url: Optional[str],
        platform_post_ids: Dict[str, str],
    ) -> None:
        timestamp = datetime.utcnow().isoformat()
        row_data = [
            timestamp,
            client_name,
            str(content_id),
            status,
            final_caption or "",
            final_image_url or "",
            json.dumps(platform_post_ids)
        ]

        # If not configured, write to CSV fallback
        if not (self.sheet_id and self.service_account_json):
            self._append_to_csv(row_data)
            print("ℹ️ Sheets not configured; wrote to CSV log.")
            return

        # Try to append to Google Sheets
        try:
            service = self._get_sheets_service()
            if not service:
                raise Exception("Could not initialize Sheets service")

            # Append row to the sheet
            body = {
                'values': [row_data]
            }

            result = service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='A:G',  # Columns A through G
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

            print(f"✅ Logged to Google Sheets: {result.get('updates', {}).get('updatedCells', 0)} cells updated")

        except Exception as e:
            # Fallback to CSV on any error
            print(f"⚠️ Google Sheets logging failed ({e}), falling back to CSV")
            self._append_to_csv(row_data)

    def _append_to_csv(self, row):
        write_header = not self.csv_path.exists()
        with self.csv_path.open("a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["timestamp", "client_name", "content_id", "status", "final_caption", "final_image_url", "platform_post_ids"])
            writer.writerow(row)


sheets_service = SheetsService()

