"""
Image Generation Service with Fallback Support
Placid (primary) → Fal AI SeeDream (backup)
"""

import httpx
from typing import Optional
from app.core.config import settings


class ImageGeneratorService:
    """Unified image generation with multiple providers as fallbacks"""

    async def generate_post_image(
        self,
        title: str,
        business_name: str,
        subtitle: Optional[str] = None,
        industry: Optional[str] = None,
        client_placid_template: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate branded image for social post.
        Tries Placid first, falls back to Fal AI if Placid fails.
        
        Returns:
            Image URL or None if all providers fail
        """
        
        # Try Placid first (branded templates)
        if settings.PLACID_API_KEY:
            try:
                from app.services.placid import placid_service
                placid_url = await placid_service.generate_social_post_image(
                    title=title,
                    business_name=business_name,
                    subtitle=subtitle,
                    industry=industry,
                    client_template_id=client_placid_template,
                )
                if placid_url:
                    print(f"✅ Placid generated image: {placid_url}")
                    return placid_url
            except Exception as e:
                print(f"⚠️ Placid failed: {e}, trying backup...")
        
        # Fallback to Fal AI SeeDream
        return await self._generate_with_fal_ai(
            title=title,
            business_name=business_name,
            subtitle=subtitle,
            industry=industry,
        )

    async def _generate_with_fal_ai(
        self,
        title: str,
        business_name: str,
        subtitle: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate image using Fal AI SeeDream V4 (fast & cheap)
        
        Model: fal-ai/bytedance/seedream/v4/text-to-image
        Speed: ~2 seconds
        Cost: Very cheap
        """
        
        fal_api_key = settings.FAL_API_KEY
        if not fal_api_key:
            print("❌ No FAL_API_KEY configured, cannot generate backup image")
            return None
        
        # Build prompt for business post using caption content for relevance
        prompt_parts = []
        
        # Extract key concepts from caption/subtitle for relevant imagery
        if subtitle:
            # Remove emojis and extract meaningful content
            import re
            clean_subtitle = re.sub(r'[^\w\s\-,.]', '', subtitle)
            # Take first 100 chars for relevance
            main_content = clean_subtitle[:100] if len(clean_subtitle) > 100 else clean_subtitle
            prompt_parts.append(f"Professional social media image depicting: {main_content}")
        else:
            prompt_parts.append(f"Professional social media post image for {business_name}")
            prompt_parts.append(f"featuring: {title}")
        
        # Add industry-specific visual style
        if industry:
            industry_styles = {
                "landscaping": "outdoor setting, lush green landscape, natural garden, vibrant plants",
                "construction": "construction site, professional workers, modern building, architectural elements",
                "hvac": "modern interior, clean home environment, comfortable living space, professional service",
                "restaurant": "delicious food presentation, elegant dining atmosphere, culinary artistry",
                "fitness": "dynamic workout scene, energetic people exercising, health and wellness focus",
                "real_estate": "beautiful modern home exterior, welcoming property, professional real estate",
                "education": "learning environment, students engaged, educational setting, bright classroom",
                "technology": "modern tech workspace, digital devices, innovative technology, clean design",
            }
            style = industry_styles.get(industry, "professional business setting, clean modern aesthetic")
            prompt_parts.append(style)
        
        # Add visual quality requirements
        prompt_parts.append("photorealistic, professional photography, bright and inviting, high quality, well-lit, 16:9 aspect ratio, perfect for social media")
        
        full_prompt = ", ".join(prompt_parts)
        
        print(f"🎨 Generating backup image with Fal AI...")
        print(f"   Prompt: {full_prompt[:100]}...")
        
        headers = {
            "Authorization": f"Key {fal_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "prompt": full_prompt,
            "image_size": "landscape_16_9",  # 1024x576, perfect for social
            "num_inference_steps": 4,  # Fast generation
            "num_images": 1,
            "enable_safety_checker": True,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://fal.run/fal-ai/bytedance/seedream/v4/text-to-image",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract image URL from response
                if "images" in data and len(data["images"]) > 0:
                    image_url = data["images"][0]["url"]
                    print(f"✅ Fal AI generated image: {image_url}")
                    return image_url
                
                print(f"⚠️ Fal AI response missing images: {data}")
                return None
                
        except httpx.HTTPStatusError as e:
            print(f"❌ Fal AI HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Fal AI generation failed: {e}")
            return None


# Singleton instance
image_generator = ImageGeneratorService()
