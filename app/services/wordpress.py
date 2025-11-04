import httpx
from typing import Dict, Optional


class WordPressService:
    """Service for publishing blog posts to WordPress."""

    async def publish_post(
        self,
        site_url: str,
        username: str,
        app_password: str,
        title: str,
        content: str,
        meta_title: Optional[str] = None,
        meta_description: Optional[str] = None,
        featured_image_url: Optional[str] = None,
        status: str = "draft",
        categories: Optional[list] = None,
    ) -> Dict[str, any]:
        """
        Publish a post to WordPress via REST API.

        Args:
            site_url: WordPress site URL (e.g., https://example.com)
            username: WordPress username
            app_password: WordPress application password
            title: Post title
            content: Post content (HTML or markdown)
            meta_title: SEO meta title
            meta_description: SEO meta description
            featured_image_url: URL of featured image
            status: 'draft' or 'publish'
            categories: List of category IDs

        Returns:
            Dict with post data including 'id' and 'link'
        """

        api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"

        # Prepare post data
        post_data = {
            "title": title,
            "content": content,
            "status": status,
        }

        if categories:
            post_data["categories"] = categories

        # TODO: Add featured image upload if featured_image_url is provided
        # TODO: Add Rank Math SEO meta fields if plugin is installed

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    json=post_data,
                    auth=(username, app_password),
                    timeout=30.0,
                )
                response.raise_for_status()

                post = response.json()

                return {
                    "id": post.get("id"),
                    "url": post.get("link"),
                    "status": post.get("status"),
                }

        except httpx.HTTPError as e:
            raise Exception(f"WordPress API error: {str(e)}")

    async def upload_media(
        self,
        site_url: str,
        username: str,
        app_password: str,
        file_url: str,
    ) -> Dict[str, any]:
        """Upload media to WordPress media library."""
        # TODO: Implement media upload
        pass


# Singleton instance
wordpress_service = WordPressService()
