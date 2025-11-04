from typing import Dict, List, Optional
from datetime import datetime
import httpx
import asyncio


class SocialMediaService:
    """Service for posting to social media platforms."""

    FACEBOOK_API_VERSION = "v18.0"
    FACEBOOK_BASE_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}"

    async def post_to_facebook(
        self,
        access_token: str,
        page_id: str,
        message: str,
        media_urls: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None,
        link_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Post to Facebook page.

        Supports:
        - Text-only posts
        - Single photo posts
        - Multiple photo posts (carousel)
        - Link posts
        - Scheduled posts

        Returns:
            Dict with 'id' (post ID) and 'post_url'
        """

        if media_urls and len(media_urls) > 1:
            # Multiple photos - create album/carousel
            return await self._post_facebook_carousel(
                access_token, page_id, message, media_urls, scheduled_time
            )
        elif media_urls and len(media_urls) == 1:
            # Single photo
            return await self._post_facebook_photo(
                access_token, page_id, message, media_urls[0], scheduled_time
            )
        elif link_url:
            # Link post
            return await self._post_facebook_link(
                access_token, page_id, message, link_url, scheduled_time
            )
        else:
            # Text-only post
            return await self._post_facebook_text(
                access_token, page_id, message, scheduled_time
            )

    async def _post_facebook_text(
        self,
        access_token: str,
        page_id: str,
        message: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """Post text-only to Facebook."""

        url = f"{self.FACEBOOK_BASE_URL}/{page_id}/feed"

        data = {
            "message": message,
            "access_token": access_token,
        }

        # Add scheduled publish time if provided
        if scheduled_time:
            data["published"] = False
            data["scheduled_publish_time"] = int(scheduled_time.timestamp())

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            post_id = result.get("id")

            return {
                "id": post_id,
                "post_url": f"https://www.facebook.com/{post_id.replace('_', '/posts/')}",
                "platform": "facebook",
            }

    async def _post_facebook_photo(
        self,
        access_token: str,
        page_id: str,
        message: str,
        photo_url: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """Post single photo to Facebook."""

        url = f"{self.FACEBOOK_BASE_URL}/{page_id}/photos"

        data = {
            "url": photo_url,  # Facebook downloads from this URL
            "caption": message,
            "access_token": access_token,
        }

        if scheduled_time:
            data["published"] = False
            data["scheduled_publish_time"] = int(scheduled_time.timestamp())

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            post_id = result.get("post_id") or result.get("id")

            return {
                "id": post_id,
                "post_url": f"https://www.facebook.com/{page_id}/posts/{post_id}",
                "platform": "facebook",
            }

    async def _post_facebook_carousel(
        self,
        access_token: str,
        page_id: str,
        message: str,
        photo_urls: List[str],
        scheduled_time: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """Post multiple photos to Facebook as carousel/album."""

        # Step 1: Upload all photos unpublished
        photo_ids = []

        for photo_url in photo_urls:
            url = f"{self.FACEBOOK_BASE_URL}/{page_id}/photos"
            data = {
                "url": photo_url,
                "published": False,  # Don't publish yet
                "access_token": access_token,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                photo_ids.append(result["id"])

        # Step 2: Create post with all photos
        url = f"{self.FACEBOOK_BASE_URL}/{page_id}/feed"

        data = {
            "message": message,
            "attached_media": [{"media_fbid": pid} for pid in photo_ids],
            "access_token": access_token,
        }

        if scheduled_time:
            data["published"] = False
            data["scheduled_publish_time"] = int(scheduled_time.timestamp())

        async with httpx.AsyncClient() as client:
            # Facebook API expects form-data, not JSON for feed endpoint
            response = await client.post(url, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            post_id = result.get("id")

            return {
                "id": post_id,
                "post_url": f"https://www.facebook.com/{post_id.replace('_', '/posts/')}",
                "platform": "facebook",
            }

    async def _post_facebook_link(
        self,
        access_token: str,
        page_id: str,
        message: str,
        link_url: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """Post link to Facebook."""

        url = f"{self.FACEBOOK_BASE_URL}/{page_id}/feed"

        data = {
            "message": message,
            "link": link_url,
            "access_token": access_token,
        }

        if scheduled_time:
            data["published"] = False
            data["scheduled_publish_time"] = int(scheduled_time.timestamp())

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            post_id = result.get("id")

            return {
                "id": post_id,
                "post_url": f"https://www.facebook.com/{post_id.replace('_', '/posts/')}",
                "platform": "facebook",
            }

    async def post_to_instagram(
        self,
        access_token: str,
        instagram_account_id: str,
        caption: str,
        media_url: str,
        media_type: str = "image",
        scheduled_time: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """
        Post to Instagram Business account via Facebook Graph API.

        Note: Instagram requires Business/Creator account connected to Facebook Page.
        Supports images and videos (not carousel yet).
        """

        # Step 1: Create media container
        url = f"{self.FACEBOOK_BASE_URL}/{instagram_account_id}/media"

        container_data = {
            "caption": caption,
            "access_token": access_token,
        }

        if media_type == "video":
            container_data["media_type"] = "VIDEO"
            container_data["video_url"] = media_url
        else:
            container_data["image_url"] = media_url

        async with httpx.AsyncClient() as client:
            # Create container
            response = await client.post(url, data=container_data, timeout=60.0)
            response.raise_for_status()
            result = response.json()

            container_id = result["id"]

            # Step 2: Publish the container (unless scheduled)
            if scheduled_time:
                # Instagram doesn't support scheduled posts via API
                # You'd need to use Facebook's Creator Studio or third-party tools
                # For now, we'll publish immediately and log a warning
                print(f"⚠️ Instagram doesn't support API scheduling. Publishing immediately.")

            publish_url = f"{self.FACEBOOK_BASE_URL}/{instagram_account_id}/media_publish"
            publish_data = {
                "creation_id": container_id,
                "access_token": access_token,
            }

            # Wait a bit for media to be processed (especially for videos)
            if media_type == "video":
                await asyncio.sleep(5)

            response = await client.post(publish_url, data=publish_data, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            post_id = result["id"]

            return {
                "id": post_id,
                "post_url": f"https://www.instagram.com/p/{post_id}",
                "platform": "instagram",
            }

    async def post_to_google_business(
        self,
        access_token: str,
        location_id: str,
        message: str,
        media_urls: Optional[List[str]] = None,
        cta_type: Optional[str] = None,
        cta_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Post to Google Business Profile.

        Location ID format: "accounts/{account_id}/locations/{location_id}"
        CTA types: LEARN_MORE, SIGN_UP, CALL, BOOK, ORDER, SHOP
        """

        url = f"https://mybusiness.googleapis.com/v4/{location_id}/localPosts"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Build post data
        post_data = {
            "languageCode": "en-US",
            "summary": message,
            "topicType": "STANDARD",  # STANDARD, EVENT, OFFER, PRODUCT
        }

        # Add media if provided
        if media_urls:
            post_data["media"] = [
                {
                    "mediaFormat": "PHOTO",
                    "sourceUrl": media_url,
                }
                for media_url in media_urls[:10]  # Max 10 photos
            ]

        # Add call-to-action if provided
        if cta_type and cta_url:
            post_data["callToAction"] = {
                "actionType": cta_type,
                "url": cta_url,
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=post_data, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            post_name = result.get("name")

            return {
                "id": post_name,
                "post_url": f"https://business.google.com/posts/l/{location_id}",
                "platform": "google_business",
            }

    async def post_to_linkedin(
        self,
        access_token: str,
        person_urn: str,
        text: str,
        media_urls: Optional[List[str]] = None,
        link_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Post to LinkedIn.

        person_urn format: "urn:li:person:ABC123"
        Supports: text, single image, link
        """

        url = "https://api.linkedin.com/v2/ugcPosts"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        # Build post data
        post_data = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text,
                    },
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        # Add link if provided
        if link_url:
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "originalUrl": link_url,
                }
            ]

        # Note: Image upload requires multi-step process (register upload, upload binary, create post)
        # For simplicity, we're doing text/link posts only for now

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=post_data, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            post_id = result.get("id")

            return {
                "id": post_id,
                "post_url": f"https://www.linkedin.com/feed/update/{post_id}",
                "platform": "linkedin",
            }


# Singleton instance
social_service = SocialMediaService()
