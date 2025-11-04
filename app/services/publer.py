"""
Publer API Integration Service

Official API Documentation: https://publer.com/docs
API Reference: https://publer.com/docs/api-reference/introduction
"""

from typing import Dict, List, Optional
from datetime import datetime
import httpx
import asyncio
from app.core.config import settings


class PublerService:
    """
    Publer API integration for publishing to social media platforms.

    Supports scheduling posts across multiple platforms:
    - Facebook, Instagram, Twitter/X, LinkedIn, Pinterest
    - YouTube, TikTok, Google Business Profile
    - WordPress, Telegram, Mastodon, Threads, Bluesky
    """

    def __init__(self):
        self.api_key = settings.PUBLER_API_KEY
        self.workspace_id = settings.PUBLER_WORKSPACE_ID
        self.base_url = settings.PUBLER_BASE_URL
        self._workspace_cache = None

    async def get_user_info(self) -> Optional[Dict]:
        """
        Get current user information.

        Returns:
            User info dict with id, email, name, etc., or None if failed
        """
        if not self.api_key:
            print("⚠️ Publer API key not configured")
            return None

        headers = {
            "Authorization": f"Bearer-API {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/users/me",
                    headers=headers,
                )
                response.raise_for_status()
                user_info = response.json()
                print(f"✅ Retrieved Publer user info")
                return user_info

        except Exception as e:
            print(f"❌ Failed to get Publer user info: {e}")
            return None

    async def list_workspaces(self) -> List[Dict]:
        """
        List all workspaces accessible to the user.

        Returns:
            List of workspace objects
        """
        if not self.api_key:
            print("⚠️ Publer API key not configured")
            return []

        headers = {
            "Authorization": f"Bearer-API {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/workspaces",
                    headers=headers,
                )
                response.raise_for_status()
                workspaces = response.json()
                print(f"✅ Retrieved {len(workspaces)} Publer workspace(s)")
                return workspaces

        except Exception as e:
            print(f"❌ Failed to list Publer workspaces: {e}")
            return []

    async def get_workspace_id(self) -> Optional[str]:
        """
        Get the workspace ID. Uses cached value or fetches from API.

        Returns:
            Workspace ID string or None
        """
        # Return configured workspace ID if available
        if self.workspace_id:
            return self.workspace_id

        # Return cached workspace ID
        if self._workspace_cache:
            return self._workspace_cache

        # Fetch workspaces from API
        workspaces = await self.list_workspaces()
        if not workspaces:
            return None

        # Use first workspace ID
        workspace_id = workspaces[0].get("id")
        if workspace_id:
            self._workspace_cache = workspace_id
            print(f"✅ Using workspace ID: {workspace_id}")
            return workspace_id

        print("⚠️ No workspaces found in user account")
        return None

    async def list_accounts(self, include_details: bool = True, workspace_id: Optional[str] = None) -> List[Dict]:
        """
        List all connected social media accounts in the workspace.

        Args:
            include_details: If True, includes human-readable account info for verification
            workspace_id: Optional client-specific workspace ID (overrides global setting)

        Returns:
            List of account objects with id, provider, name, type, etc.
            Example: [
                {
                    "id": "68ff8b28dbe5ada5b0944612",
                    "provider": "facebook",
                    "name": "Joe's Landscaping",
                    "type": "page",
                    "username": "joeslandscaping",
                    "display": "Facebook: Joe's Landscaping (@joeslandscaping)"
                }
            ]
        """
        if not self.api_key:
            print("⚠️ Publer API key not configured")
            return []

        # Use provided workspace_id or auto-fetch
        if not workspace_id:
            workspace_id = await self.get_workspace_id()
        if not workspace_id:
            print("⚠️ Could not determine workspace ID")
            return []

        headers = self._get_headers(workspace_id)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/accounts",
                    headers=headers,
                )
                response.raise_for_status()
                accounts = response.json()

                # Add human-readable display names for verification
                if include_details:
                    for account in accounts:
                        provider = account.get('provider', 'unknown').title()
                        name = account.get('name', 'Unknown')
                        username = account.get('username', '')
                        account_type = account.get('type', '')

                        # Build display string
                        display = f"{provider}: {name}"
                        if username:
                            display += f" (@{username})"
                        if account_type:
                            display += f" [{account_type}]"

                        account['display'] = display

                print(f"✅ Retrieved {len(accounts)} Publer accounts")
                return accounts

        except Exception as e:
            print(f"❌ Failed to list Publer accounts: {e}")
            return []

    async def get_account_details(self, account_ids: List[str], workspace_id: Optional[str] = None) -> Dict[str, Dict]:
        """
        Get details for specific account IDs for verification.

        Args:
            account_ids: List of Publer account IDs to look up
            workspace_id: Optional client-specific workspace ID

        Returns:
            Dict mapping account_id -> account details
            Example: {
                "68ff8b28...": {
                    "provider": "facebook",
                    "name": "Joe's Landscaping",
                    "display": "Facebook: Joe's Landscaping"
                }
            }
        """
        all_accounts = await self.list_accounts(include_details=True, workspace_id=workspace_id)

        account_map = {}
        for account in all_accounts:
            if account.get('id') in account_ids:
                account_map[account['id']] = {
                    'provider': account.get('provider', 'unknown'),
                    'name': account.get('name', 'Unknown'),
                    'username': account.get('username'),
                    'type': account.get('type'),
                    'display': account.get('display', 'Unknown Account')
                }

        return account_map

    async def validate_account_ids(self, account_ids: List[str], workspace_id: Optional[str] = None) -> Dict[str, bool]:
        """
        Validate that account IDs exist in Publer workspace.

        Args:
            account_ids: List of account IDs to validate
            workspace_id: Optional client-specific workspace ID

        Returns:
            Dict mapping account_id -> is_valid (True/False)
        """
        all_accounts = await self.list_accounts(include_details=False, workspace_id=workspace_id)
        valid_ids = {acc.get('id') for acc in all_accounts}

        return {
            account_id: account_id in valid_ids
            for account_id in account_ids
        }

    async def schedule_post(
        self,
        account_ids: List[str],
        content_dict: Dict[str, Dict],
        scheduled_time: datetime,
        media_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
    ) -> Dict:
        """
        Schedule a post to multiple social accounts.

        Args:
            account_ids: List of Publer account IDs to post to
            content_dict: Dict mapping platform names to content config
                Example: {
                    "facebook": {"type": "status", "text": "Post content"},
                    "instagram": {"type": "photo", "text": "Post content", "media": [...]}
                }
            scheduled_time: When to publish the post
            media_ids: Optional list of pre-uploaded media IDs
            workspace_id: Optional client-specific workspace ID

        Returns:
            Dict with job_id for tracking or error info
        """
        if not self.api_key:
            print("⚠️ Publer API key not configured")
            return {"error": "Publer not configured", "status": "failed"}

        # Use provided workspace_id or auto-fetch
        if not workspace_id:
            workspace_id = await self.get_workspace_id()
        if not workspace_id:
            print("⚠️ Could not determine workspace ID")
            return {"error": "Workspace ID not found", "status": "failed"}

        headers = self._get_headers(workspace_id)

        # Build accounts array with schedule times
        accounts = [
            {
                "id": account_id,
                "scheduled_at": scheduled_time.isoformat() if scheduled_time else None,
            }
            for account_id in account_ids
        ]

        # Build the request payload in Publer's expected format
        payload = {
            "bulk": {
                "state": "scheduled",
                "posts": [
                    {
                        "networks": content_dict,
                        "accounts": accounts,
                    }
                ]
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/posts/schedule",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                job_id = data.get("job_id")
                if job_id:
                    print(f"✅ Post scheduled via Publer (job: {job_id})")
                    # Poll job status
                    final_status = await self._poll_job_status(job_id)
                    return final_status
                else:
                    print(f"✅ Post scheduled via Publer")
                    return {
                        "status": "success",
                        "data": data,
                    }

        except httpx.HTTPStatusError as e:
            error_msg = f"Publer API error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {e.response.text}"

            print(f"❌ {error_msg}")
            return {
                "error": error_msg,
                "status": "failed",
            }

        except Exception as e:
            print(f"❌ Publer scheduling failed: {e}")
            return {
                "error": str(e),
                "status": "failed",
            }

    async def publish_now(
        self,
        account_ids: List[str],
        content_dict: Dict[str, Dict],
        media_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
    ) -> Dict:
        """
        Publish a post immediately to multiple social accounts.

        Args:
            account_ids: List of Publer account IDs
            content_dict: Platform-specific content configuration
            media_ids: Optional list of pre-uploaded media IDs
            workspace_id: Optional client-specific workspace ID

        Returns:
            Dict with job_id or error info
        """
        if not self.api_key:
            print("⚠️ Publer API key not configured")
            return {"error": "Publer not configured", "status": "failed"}

        # Use provided workspace_id or auto-fetch
        if not workspace_id:
            workspace_id = await self.get_workspace_id()
        if not workspace_id:
            print("⚠️ Could not determine workspace ID")
            return {"error": "Workspace ID not found", "status": "failed"}

        headers = self._get_headers(workspace_id)

        # Build accounts array for immediate publishing
        accounts = [{"id": account_id} for account_id in account_ids]

        payload = {
            "bulk": {
                "state": "scheduled",  # Still use "scheduled" but no scheduled_at
                "posts": [
                    {
                        "networks": content_dict,
                        "accounts": accounts,
                    }
                ]
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/posts/schedule/publish",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                job_id = data.get("job_id")
                if job_id:
                    print(f"✅ Post published via Publer (job: {job_id})")
                    final_status = await self._poll_job_status(job_id)
                    return final_status
                else:
                    print(f"✅ Post published via Publer")
                    return {"status": "success", "data": data}

        except Exception as e:
            print(f"❌ Publer publishing failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def update_post_schedule(
        self,
        post_id: str,
        new_scheduled_time: datetime,
        workspace_id: Optional[str] = None,
    ) -> Dict:
        """
        Update the scheduled time for an existing post in Publer.

        Args:
            post_id: The Publer post ID to update
            new_scheduled_time: New datetime to schedule the post
            workspace_id: Optional client-specific workspace ID

        Returns:
            Dict with success status or error info
        """
        if not self.api_key:
            print("⚠️ Publer API key not configured")
            return {"error": "Publer not configured", "status": "failed"}

        # Use provided workspace_id or auto-fetch
        if not workspace_id:
            workspace_id = await self.get_workspace_id()
        if not workspace_id:
            print("⚠️ Could not determine workspace ID")
            return {"error": "Workspace ID not found", "status": "failed"}

        headers = self._get_headers(workspace_id)

        # Convert datetime to Unix timestamp (Publer expects Unix timestamp)
        scheduled_timestamp = int(new_scheduled_time.timestamp())

        payload = {
            "scheduled_at": scheduled_timestamp,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.base_url}/posts/{post_id}",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                print(f"✅ Post {post_id} rescheduled in Publer to {new_scheduled_time}")
                return {"status": "success", "data": data}

        except httpx.HTTPStatusError as e:
            print(f"❌ Publer reschedule failed: {e.response.status_code} - {e.response.text}")
            return {
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "status": "failed",
            }
        except Exception as e:
            print(f"❌ Publer reschedule failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _poll_job_status(self, job_id: str, max_attempts: int = 10) -> Dict:
        """
        Poll job status until completion.

        Args:
            job_id: The job ID returned from the API
            max_attempts: Maximum number of polling attempts

        Returns:
            Final job status dict
        """
        workspace_id = await self.get_workspace_id()
        headers = self._get_headers(workspace_id)

        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{self.base_url}/job_status/{job_id}",
                        headers=headers,
                    )
                    response.raise_for_status()
                    status_data = response.json()

                    job_status = status_data.get("status")

                    # Publer uses "complete" (not "completed")
                    if job_status in ["completed", "complete"]:
                        print(f"✅ Job {job_id} completed successfully")
                        return {
                            "status": "success",
                            "job_id": job_id,
                            "payload": status_data.get("payload"),
                            "data": status_data,
                        }
                    elif job_status == "failed":
                        print(f"❌ Job {job_id} failed")
                        return {
                            "status": "failed",
                            "job_id": job_id,
                            "errors": status_data.get("payload", {}).get("errors", []),
                        }
                    elif job_status == "working":
                        print(f"⏳ Job {job_id} still processing (attempt {attempt + 1}/{max_attempts})")
                        await asyncio.sleep(2)  # Wait 2 seconds before next poll
                        continue
                    else:
                        print(f"⚠️ Unknown job status: {job_status}")
                        return {"status": "unknown", "job_id": job_id, "data": status_data}

            except Exception as e:
                print(f"❌ Error polling job status: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                    continue
                return {"status": "error", "error": str(e)}

        # Max attempts reached
        return {
            "status": "timeout",
            "job_id": job_id,
            "message": "Job polling timed out",
        }

    async def upload_media(self, file_url: str, workspace_id: Optional[str] = None) -> Optional[str]:
        """
        Upload media to Publer and return the media ID.

        Args:
            file_url: URL of the media file to upload
            workspace_id: Optional client-specific workspace ID

        Returns:
            Media ID if successful, None otherwise
        """
        if not self.api_key:
            print("⚠️ Publer API key not configured")
            return None

        # Use provided workspace_id or auto-fetch
        if not workspace_id:
            workspace_id = await self.get_workspace_id()
        if not workspace_id:
            print("⚠️ Could not determine workspace ID")
            return None

        headers = self._get_headers(workspace_id)

        payload = {"url": file_url}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/media",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                media_id = data.get("id")
                print(f"✅ Media uploaded to Publer: {media_id}")
                return media_id

        except Exception as e:
            print(f"❌ Media upload failed: {e}")
            return None

    def _get_headers(self, workspace_id: Optional[str] = None) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Authorization": f"Bearer-API {self.api_key}",
            "Content-Type": "application/json",
        }

        # Use provided workspace_id, or fall back to configured/cached
        ws_id = workspace_id or self.workspace_id or self._workspace_cache
        if ws_id:
            headers["Publer-Workspace-Id"] = ws_id

        return headers

    def build_platform_content(
        self,
        platform: str,
        text: str,
        content_type: str = "status",
        media: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Build platform-specific content configuration.

        Args:
            platform: Platform name (facebook, instagram, linkedin, etc.)
            text: Post text/caption
            content_type: Content type (status, photo, video, link, etc.)
            media: List of media dicts with id, type, alt_text

        Returns:
            Platform content dict
        """
        content = {
            "type": content_type,
            "text": text,
        }

        if media:
            content["media"] = media

        return content


# Singleton instance
publer_service = PublerService()
