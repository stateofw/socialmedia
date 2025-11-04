from typing import Dict, Optional
import httpx
from app.core.config import settings


class PlacidService:
    """Minimal Placid API integration to render branded images from a template.

    When PLACID_API_KEY or PLACID_TEMPLATE_ID is missing, acts as a no-op.
    """

    BASE_URL = "https://api.placid.app/u/creatives"

    async def generate_asset(
        self,
        text_fields: Dict[str, str],
        image_url: Optional[str] = None,
        template_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Render an image and return its URL. Returns None if not configured.
        """
        api_key = settings.PLACID_API_KEY
        template = template_id or settings.PLACID_TEMPLATE_ID
        if not api_key or not template:
            print("ℹ️ Placid not configured; skipping image generation.")
            return None

        payload: Dict = {
            "template_uuid": template,
            "modifications": [],
        }

        for key, value in text_fields.items():
            payload["modifications"].append({
                "name": key,
                "text": value,
            })

        if image_url:
            payload["modifications"].append({
                "name": "image",
                "image": image_url,
            })

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(self.BASE_URL, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data.get("url") or data.get("image_url")
            except Exception as e:
                print(f"❌ Placid generation failed: {e}")
                return None

    async def generate_social_post_image(
        self,
        title: str,
        business_name: str,
        subtitle: Optional[str] = None,
        industry: Optional[str] = None,
        template_id: Optional[str] = None,
        client_template_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a branded social media post image for when no user media is provided.

        Args:
            title: Main headline/title for the post (max 60 chars)
            business_name: Business name to display
            subtitle: Optional subtitle or description (max 100 chars)
            industry: Optional industry (used for color theming)
            template_id: Optional specific template to use (deprecated, use client_template_id)
            client_template_id: Client-specific template ID (takes priority over template_id)

        Returns:
            Image URL string or None if failed

        Example:
            url = await placid_service.generate_social_post_image(
                title="5 Tips for Perfect Lawn Care",
                business_name="Joe's Landscaping",
                subtitle="Keep your lawn green all season",
                industry="landscaping",
                client_template_id=client.placid_template_id
            )
        """
        # Priority: client_template_id > template_id > global default
        final_template_id = client_template_id or template_id
        # Map industry to brand colors
        industry_colors = {
            "landscaping": "#4CAF50",
            "construction": "#FF9800",
            "restaurant": "#E91E63",
            "retail": "#9C27B0",
            "healthcare": "#2196F3",
            "fitness": "#F44336",
            "real_estate": "#3F51B5",
            "automotive": "#607D8B",
            "beauty": "#E91E63",
            "home_services": "#FF5722",
        }

        background_color = industry_colors.get(
            industry.lower().replace(" ", "_") if industry else "",
            "#2196F3"  # Default blue
        )

        text_fields = {
            "title": title[:60],  # Limit title length
            "business_name": business_name,
            "background_color": background_color,
        }

        if subtitle:
            text_fields["subtitle"] = subtitle[:100]  # Limit subtitle length

        return await self.generate_asset(
            text_fields=text_fields,
            template_id=final_template_id,
        )


placid_service = PlacidService()

