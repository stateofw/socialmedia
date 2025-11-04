"""
Content Polisher - Post-Generation Quality Enhancement

Uses OpenAI's GPT-4 to refine and polish AI-generated content for:
- Grammar and clarity
- Brand voice consistency
- Tone adjustments
- Removing AI-sounding phrases
- Enhancing local expertise
"""

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    AsyncOpenAI = None

from app.core.config import settings
from typing import Dict, Optional


class ContentPolisher:
    """
    Post-generation content refinement service.

    Takes raw AI-generated content and polishes it for:
    - Natural language flow
    - Brand voice consistency
    - Grammar and clarity
    - Local expert authenticity
    - Platform-specific optimization
    """

    def __init__(self):
        if HAS_OPENAI:
            # Use OpenRouter for polishing (supports GPT-4 and other models)
            openrouter_key = getattr(settings, 'OPENROUTER_API_KEY', None)

            if openrouter_key:
                self.client = AsyncOpenAI(
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                # Use GPT-4 via OpenRouter for polishing
                self.model = getattr(settings, 'POLISHER_MODEL', 'openai/gpt-4-turbo-preview')
                self.enabled = True
                print(f"✅ Content Polisher initialized with OpenRouter ({self.model})")
            else:
                self.client = None
                self.model = None
                self.enabled = False
                print("⚠️ Content Polisher disabled (OpenRouter not configured)")
        else:
            self.client = None
            self.model = None
            self.enabled = False
            print("⚠️ Content Polisher disabled (openai package not installed)")

    async def polish_caption(
        self,
        caption: str,
        industry: str,
        location: str,
        brand_voice: Optional[str] = None,
        tone_preference: str = "professional",
        platform: str = "instagram",
    ) -> str:
        """
        Polish and refine a social media caption.

        Args:
            caption: Raw AI-generated caption
            industry: Business industry
            location: City, State
            brand_voice: Optional brand voice guidelines
            tone_preference: professional, friendly, or local_expert
            platform: Target platform

        Returns:
            Polished caption
        """

        if not self.enabled:
            return caption  # Return original if polisher not enabled

        # Build polishing prompt
        prompt = self._build_polish_prompt(
            caption=caption,
            industry=industry,
            location=location,
            brand_voice=brand_voice,
            tone_preference=tone_preference,
            platform=platform,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content editor. Your job is to refine and polish social media content while maintaining its authentic voice and local expertise."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent editing
                max_tokens=500,
            )

            polished = response.choices[0].message.content.strip()

            # Remove any "Polished:" or "Edited:" prefixes
            for prefix in ["Polished:", "Edited:", "Refined:", "Updated:"]:
                if polished.startswith(prefix):
                    polished = polished[len(prefix):].strip()

            print(f"✨ Caption polished ({len(caption)} → {len(polished)} chars)")
            return polished

        except Exception as e:
            print(f"⚠️ Polishing failed, using original: {e}")
            return caption  # Fallback to original on error

    def _build_polish_prompt(
        self,
        caption: str,
        industry: str,
        location: str,
        brand_voice: Optional[str],
        tone_preference: str,
        platform: str,
    ) -> str:
        """Build the polishing prompt."""

        voice_instruction = f"Brand voice: {brand_voice}" if brand_voice else ""

        tone_map = {
            "professional": "confident and professional",
            "friendly": "warm and approachable",
            "local_expert": "knowledgeable and conversational, like a local pro"
        }
        tone_desc = tone_map.get(tone_preference, "professional")

        prompt = f"""Polish this {platform} caption for a {industry} business in {location}.

ORIGINAL CAPTION:
{caption}

{voice_instruction}

POLISHING GOALS:
1. **Grammar & Clarity**: Fix any grammatical errors, awkward phrasing, or unclear sentences
2. **Tone**: Ensure it sounds {tone_desc}
3. **Authenticity**: Remove AI-sounding phrases like "excited to announce," "delighted," "thrilled"
4. **Local Voice**: Maintain the local expert perspective from {location}
5. **Natural Flow**: Ensure sentences flow naturally with varied length
6. **Platform Fit**: Optimize for {platform} best practices

RULES:
- Keep contractions (you'll, we're, don't)
- Maintain any local references or details
- Keep it under 150 words
- Don't add emojis unless the original had them
- Don't change the core message or meaning
- NEVER use em dashes (—) - replace with regular hyphens (-) or commas
- Return ONLY the polished caption, no explanations

Polished caption:"""

        return prompt

    async def polish_multiple_captions(
        self,
        platform_captions: Dict[str, str],
        industry: str,
        location: str,
        brand_voice: Optional[str] = None,
        tone_preference: str = "professional",
    ) -> Dict[str, str]:
        """
        Polish multiple platform-specific captions.

        Args:
            platform_captions: Dict of platform -> caption
            industry: Business industry
            location: City, State
            brand_voice: Optional brand voice
            tone_preference: Tone setting

        Returns:
            Dict of platform -> polished caption
        """

        if not self.enabled:
            return platform_captions

        polished = {}

        for platform, caption in platform_captions.items():
            polished_caption = await self.polish_caption(
                caption=caption,
                industry=industry,
                location=location,
                brand_voice=brand_voice,
                tone_preference=tone_preference,
                platform=platform,
            )
            polished[platform] = polished_caption

        return polished

    async def check_content_quality(self, caption: str) -> Dict:
        """
        Analyze content quality and provide feedback.

        Returns:
            Dict with quality scores and suggestions
        """

        if not self.enabled:
            return {"error": "Polisher not enabled"}

        prompt = f"""Analyze this social media caption for quality:

CAPTION:
{caption}

Provide a quality assessment:
1. **Grammar Score** (0-10): How clean is the grammar?
2. **Authenticity Score** (0-10): How human/natural does it sound?
3. **Engagement Score** (0-10): How likely to engage readers?
4. **AI-Sounding Phrases**: List any robotic/corporate phrases
5. **Suggestions**: 1-2 specific improvements

Format your response as:
Grammar: [score]
Authenticity: [score]
Engagement: [score]
AI Phrases: [list or "none"]
Suggestions: [suggestions]
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a content quality analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300,
            )

            analysis = response.choices[0].message.content.strip()

            # Parse response (basic parsing)
            return {
                "raw_analysis": analysis,
                "caption_length": len(caption),
                "word_count": len(caption.split()),
            }

        except Exception as e:
            return {"error": str(e)}

    async def suggest_improvements(self, caption: str, feedback: str) -> str:
        """
        Generate improved version based on specific feedback.

        Args:
            caption: Original caption
            feedback: Specific feedback/rejection reason

        Returns:
            Improved caption
        """

        if not self.enabled:
            return caption

        prompt = f"""Improve this caption based on the feedback:

ORIGINAL:
{caption}

FEEDBACK:
{feedback}

Rewrite the caption addressing the feedback. Return ONLY the improved caption."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert content editor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500,
            )

            improved = response.choices[0].message.content.strip()
            print(f"✨ Caption improved based on feedback")
            return improved

        except Exception as e:
            print(f"⚠️ Improvement failed: {e}")
            return caption


# Singleton instance
content_polisher = ContentPolisher()
