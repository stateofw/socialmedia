"""
Automated Content Generator

Generates complete social media posts from scratch:
- AI-generated text (captions, hashtags)
- Placid-generated images (branded graphics)

Used when:
1. Client doesn't provide content/media
2. All provided images have been used already
3. Need fresh content for consistent posting
"""

from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.services.ai import ai_service
from app.services.image_generator import image_generator
from app.services.content_polisher import content_polisher
from app.models.client import Client
from app.models.content import Content, ContentType


class AutoContentGenerator:
    """
    Generates complete social media posts from scratch using AI + Placid.
    """

    # Topic ideas by industry for when we need to generate from scratch
    INDUSTRY_TOPICS = {
        "landscaping": [
            "5 Tips for a Lush Green Lawn This Season",
            "Transform Your Backyard: Before & After Inspiration",
            "Essential Lawn Care Tools Every Homeowner Needs",
            "Why Fall is the Best Time for Lawn Aeration",
            "How to Choose the Right Mulch for Your Garden",
            "Common Lawn Problems and How to Fix Them",
            "The Benefits of Professional Landscape Maintenance",
            "Water-Saving Tips for Your Lawn and Garden",
        ],
        "construction": [
            "Top Construction Trends for This Year",
            "How to Choose the Right Contractor for Your Project",
            "Safety First: Construction Site Best Practices",
            "The Importance of Quality Materials in Construction",
            "Renovation vs. New Build: What's Right for You?",
            "Behind the Scenes: A Day in Construction",
            "How We Ensure Quality in Every Project",
        ],
        "restaurant": [
            "Chef's Special: This Week's Featured Dish",
            "Behind the Scenes in Our Kitchen",
            "What Makes Our [Dish] So Special",
            "Fresh Ingredients, Fresh Flavors",
            "Join Us for Happy Hour Specials",
            "Meet Our Chef: Passion for Food",
            "Customer Favorites: Top 5 Dishes",
        ],
        "real_estate": [
            "First-Time Homebuyer Tips",
            "How to Stage Your Home for a Quick Sale",
            "Top Neighborhoods to Watch This Year",
            "The Home Buying Process Simplified",
            "Investment Properties: What to Look For",
            "Market Update: Local Real Estate Trends",
        ],
        "fitness": [
            "5 Exercises for a Full-Body Workout",
            "How to Stay Motivated on Your Fitness Journey",
            "Nutrition Tips for Better Performance",
            "Member Spotlight: Transformation Stories",
            "The Benefits of Group Fitness Classes",
            "Recovery Tips for Active Lifestyles",
        ],
        "healthcare": [
            "Tips for Staying Healthy This Season",
            "When to See a Doctor: Warning Signs",
            "The Importance of Regular Check-ups",
            "Meet Our Team: Dedicated to Your Health",
            "Patient Success Stories",
            "Understanding Your Health Insurance Options",
        ],
    }

    async def check_image_usage(
        self,
        client_id: int,
        db: AsyncSession,
    ) -> Dict[str, int]:
        """
        Check how many times each image has been used for this client.

        Returns:
            Dict mapping image URLs to usage counts
        """
        # Get all content for this client
        result = await db.execute(
            select(Content).where(Content.client_id == client_id)
        )
        all_content = result.scalars().all()

        # Count image usage
        image_usage = {}
        for content in all_content:
            if content.media_urls:
                for url in content.media_urls:
                    image_usage[url] = image_usage.get(url, 0) + 1

        return image_usage

    async def has_fresh_images(
        self,
        client_id: int,
        db: AsyncSession,
        max_uses: int = 3,
    ) -> bool:
        """
        Check if client has any images that haven't been overused.

        Args:
            client_id: Client ID
            db: Database session
            max_uses: Maximum times an image should be used before considering it "overused"

        Returns:
            True if fresh images are available, False otherwise
        """
        image_usage = await self.check_image_usage(client_id, db)

        # Check if any images are under the max usage threshold
        for count in image_usage.values():
            if count < max_uses:
                return True

        return False

    def get_topic_for_industry(self, industry: Optional[str] = None) -> str:
        """
        Get a random topic idea based on industry.

        Args:
            industry: Industry name (e.g., "landscaping", "construction")

        Returns:
            Topic string
        """
        import random

        if not industry:
            industry = "general"

        topics = self.INDUSTRY_TOPICS.get(
            industry.lower(),
            [
                "Customer Success Story",
                "Behind the Scenes at Our Business",
                "Why Choose Us",
                "Meet Our Team",
                "Tips and Tricks from the Pros",
                "What Makes Us Different",
            ]
        )

        return random.choice(topics)

    async def generate_complete_post(
        self,
        client: Client,
        topic: Optional[str] = None,
        content_type: Optional[ContentType] = None,
    ) -> Dict:
        """
        Generate a complete social media post from scratch:
        - AI-generated text (caption, hashtags, variations)
        - Placid-generated branded image

        Args:
            client: Client object
            topic: Optional topic (will generate if not provided)
            content_type: Optional content type

        Returns:
            Dict with all content fields ready for Content model
        """
        # Generate topic if not provided
        if not topic:
            topic = self.get_topic_for_industry(client.industry)

        # Generate caption with AI
        print(f"🤖 Generating AI caption for topic: {topic}")
        ai_result = await ai_service.generate_social_post(
            business_name=client.business_name,
            industry=client.industry or "local business",
            location=client.service_area or f"{client.city}, {client.state}",
            topic=topic,
            content_type=content_type.value if content_type else None,
            platforms=client.platforms_enabled or ["facebook", "instagram"],
            brand_voice=client.brand_voice,
            tone_preference=client.tone_preference,
        )

        if not ai_result or "error" in ai_result:
            print(f"❌ AI generation failed: {ai_result}")
            return {"error": "AI generation failed", "status": "failed"}

        # Polish the caption
        caption = ai_result.get("caption", "")
        if caption:
            print(f"✨ Polishing caption...")
            polished = await content_polisher.polish_caption(
                caption=caption,
                business_name=client.business_name,
                industry=client.industry,
            )
            if polished and polished.get("polished_caption"):
                caption = polished["polished_caption"]

        # Generate branded image (Placid with Fal AI backup)
        print(f"🎨 Generating image for: {topic}")
        image_url = await image_generator.generate_post_image(
            title=topic,
            business_name=client.business_name,
            subtitle=caption[:100] if caption else None,  # First 100 chars as subtitle
            industry=client.industry,
            client_placid_template=client.placid_template_id,  # Use client-specific template
        )

        media_urls = []
        if image_url:
            media_urls = [image_url]
            print(f"✅ Image generated: {image_url}")
        else:
            print(f"⚠️ Image generation failed (no providers configured)")

        return {
            "topic": topic,
            "caption": caption,
            "hashtags": ai_result.get("hashtags", []),
            "cta": ai_result.get("cta"),
            "platform_captions": ai_result.get("platform_captions", {}),
            "media_urls": media_urls,
            "media_type": "image" if media_urls else None,
            "generated_by_ai": True,
            "status": "success",
        }


# Singleton instance
auto_content_generator = AutoContentGenerator()
