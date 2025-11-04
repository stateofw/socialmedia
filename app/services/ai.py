try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    AsyncOpenAI = None

from app.core.config import settings
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import json
from app.services.hashtag_generator import hashtag_generator


# Pydantic models for structured AI output
class SocialPostOutput(BaseModel):
    """Structured output model for social media posts."""
    caption: str = Field(..., description="The main social media caption (100-150 words)")
    hashtags: List[str] = Field(..., description="List of 5 relevant hashtags")
    cta: str = Field(..., description="Call-to-action text")


class BlogPostOutput(BaseModel):
    """Structured output model for blog posts."""
    title: str = Field(..., max_length=60, description="Blog post title under 60 characters")
    meta_title: str = Field(..., max_length=60, description="SEO title under 60 characters")
    meta_description: str = Field(..., max_length=160, description="SEO description under 160 characters")
    content: str = Field(..., description="Full blog post content in markdown (600-900 words)")


class ContentIdea(BaseModel):
    """Structured output model for a content idea."""
    topic: str = Field(..., description="Specific, engaging topic title")
    content_type: str = Field(..., description="Type of content (before_after, testimonial, offer, tip, etc.)")
    description: str = Field(..., description="Brief description of what the post would cover")


class AIService:
    """Service for AI content generation using OpenAI or OpenRouter with structured outputs."""

    def __init__(self):
        if HAS_OPENAI:
            # Check if we should use Gemini via OpenRouter
            use_gemini = getattr(settings, 'USE_GEMINI', False)
            use_openrouter = getattr(settings, 'USE_OPENROUTER', False)
            openrouter_key = getattr(settings, 'OPENROUTER_API_KEY', None)

            if use_gemini and openrouter_key:
                # Use Gemini via OpenRouter
                self.client = AsyncOpenAI(
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                self.model = getattr(settings, 'GEMINI_MODEL', 'google/gemini-pro-1.5')
                self.provider = "Gemini"
                print(f"✅ AI Service initialized with Gemini via OpenRouter ({self.model})")
            elif use_openrouter and openrouter_key:
                # Use OpenRouter with OpenAI-compatible API
                self.client = AsyncOpenAI(
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                self.model = getattr(settings, 'OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
                self.provider = "OpenRouter"
                print(f"✅ AI Service initialized with OpenRouter ({self.model})")
            elif hasattr(settings, 'OPENAI_API_KEY'):
                # Use OpenAI
                self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview')
                self.provider = "OpenAI"
                print(f"✅ AI Service initialized with OpenAI ({self.model})")
            else:
                self.client = None
                self.model = None
                self.provider = None
                print("⚠️ No AI provider configured")
        else:
            self.client = None
            self.model = None
            self.provider = None

    async def generate_social_post(
        self,
        business_name: str,
        industry: str,
        topic: str,
        location: str,
        content_type: str,
        brand_voice: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Generate expert-level social media post with human tone.

        Returns:
            Dict with 'caption', 'hashtags', and 'cta'
        """

        # Return demo content if OpenAI is not available
        if not self.client:
            return {
                "caption": f"[DEMO] Check out what's happening at {business_name} in {location}! {topic}",
                "hashtags": ["#localbusiness", f"#{industry}", f"#{location.replace(' ', '').replace(',', '')}"],
                "cta": f"Visit {business_name} today and see for yourself!"
            }

        # Build the prompt
        prompt = self._build_social_prompt(
            business_name=business_name,
            industry=industry,
            topic=topic,
            location=location,
            content_type=content_type,
            brand_voice=brand_voice,
            notes=notes,
        )

        try:
            # OpenRouter/Gemini doesn't support structured outputs, use manual parsing
            if self.provider in ["OpenRouter", "Gemini"]:
                # Use higher temperature for more natural, human-like content
                temp = 0.9 if self.provider == "Gemini" else 0.8

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a real local business owner and industry expert. Write as you would naturally speak—casual, confident, and authentic. NOT like a marketing AI.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temp,
                    max_tokens=500,
                )

                content = response.choices[0].message.content
                parsed = self._parse_social_response(content)
                return parsed

            # Try using structured outputs for OpenAI
            try:
                response = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert social media content writer for local businesses. Your writing sounds human, professional, and industry-smart—never robotic or AI-generated.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format=SocialPostOutput,
                    temperature=0.7,
                    max_tokens=500,
                )

                # Parse using Pydantic model
                parsed_output = response.choices[0].message.parsed
                return {
                    "caption": parsed_output.caption,
                    "hashtags": parsed_output.hashtags,
                    "cta": parsed_output.cta,
                }

            except (AttributeError, TypeError):
                # Fallback to traditional prompting + manual parsing
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert social media content writer for local businesses. Your writing sounds human, professional, and industry-smart—never robotic or AI-generated.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=500,
                )

                content = response.choices[0].message.content
                parsed = self._parse_social_response(content)
                return parsed

        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")

    async def generate_blog_post(
        self,
        business_name: str,
        industry: str,
        topic: str,
        location: str,
        website_url: str,
        short_caption: str,
        brand_voice: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate SEO-optimized blog post from social media content.

        Returns:
            Dict with 'title', 'meta_title', 'meta_description', 'content'
        """

        # Return demo content if OpenAI is not available
        if not self.client:
            return {
                "title": f"[DEMO] {topic} - {business_name}",
                "meta_title": f"{topic} | {business_name} in {location}",
                "meta_description": f"Learn about {topic} from {business_name}, your local {industry} experts in {location}.",
                "content": f"<p>[DEMO] This is where the full blog post would appear about {topic}.</p>"
            }

        prompt = self._build_blog_prompt(
            business_name=business_name,
            industry=industry,
            topic=topic,
            location=location,
            website_url=website_url,
            short_caption=short_caption,
            brand_voice=brand_voice,
        )

        try:
            # OpenRouter doesn't support structured outputs, use manual parsing
            if self.provider == "OpenRouter":
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert SEO content writer for local businesses. Write human-sounding, authoritative blog posts optimized for local search.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )

                content = response.choices[0].message.content
                parsed = self._parse_blog_response(content)
                return parsed

            # Try using structured outputs for OpenAI
            try:
                response = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert SEO content writer for local businesses. Write human-sounding, authoritative blog posts optimized for local search.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format=BlogPostOutput,
                    temperature=0.7,
                    max_tokens=2000,
                )

                # Parse using Pydantic model
                parsed_output = response.choices[0].message.parsed
                return {
                    "title": parsed_output.title,
                    "meta_title": parsed_output.meta_title,
                    "meta_description": parsed_output.meta_description,
                    "content": parsed_output.content,
                }

            except (AttributeError, TypeError):
                # Fallback to traditional prompting + manual parsing
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert SEO content writer for local businesses. Write human-sounding, authoritative blog posts optimized for local search.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )

                content = response.choices[0].message.content
                parsed = self._parse_blog_response(content)
                return parsed

        except Exception as e:
            raise Exception(f"Blog generation failed: {str(e)}")

    def _build_social_prompt(
        self,
        business_name: str,
        industry: str,
        topic: str,
        location: str,
        content_type: str,
        brand_voice: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Build the prompt for social media post generation with local expert tone."""

        # Extract city and state from location
        city = location.split(',')[0].strip() if ',' in location else location
        state = location.split(',')[-1].strip() if ',' in location else ""

        voice_instruction = (
            f"Brand voice: {brand_voice}" if brand_voice else "Confident, practical, conversational."
        )
        notes_instruction = f"Special notes: {notes}" if notes else ""

        # Build "local expert" system prompt
        prompt = f"""Write a social media post as if you are an experienced {industry} professional based in {city}, {state}.

Business: {business_name}
Topic: {topic}
Post Type: {content_type}
{voice_instruction}
{notes_instruction}

CRITICAL TONE REQUIREMENTS (Make it sound human, NOT AI):
- Write like a real {industry} expert from {location}, not a marketing bot
- Use contractions naturally (you'll, we're, it's, don't)
- Include ONE relevant local detail (weather, season, local regulation, regional concern)
- Add practical professional advice or insight about the topic
- Vary sentence length - mix short and long sentences
- Avoid corporate buzzwords: "excited," "thrilled," "delighted," "leverage," "solutions"
- NO AI-perfect grammar - write conversationally like a text message
- Be direct and helpful, not salesy
- NEVER use em dashes (—) - use regular hyphens (-) or commas instead

CONTENT STRUCTURE:
- Length: 80-120 words (natural, not exactly 100)
- Start with a relatable hook or observation
- Middle: practical tip or insight from your {industry} experience
- End with casual, helpful CTA

Format your response EXACTLY like this:

CAPTION:
[Your natural, human-sounding caption here - as if texting a neighbor]

HASHTAGS:
[5 local + industry hashtags like #{city.replace(' ', '')}{industry.replace(' ', '')} #{state}{industry.replace(' ', '')}]

CTA:
[Short, conversational call-to-action - "Give us a call" not "Reach out today!"]
"""
        return prompt

    def _build_blog_prompt(
        self,
        business_name: str,
        industry: str,
        topic: str,
        location: str,
        website_url: str,
        short_caption: str,
        brand_voice: Optional[str] = None,
    ) -> str:
        """Build the prompt for blog post generation."""

        voice_instruction = (
            f"Brand voice: {brand_voice}" if brand_voice else "Use a professional, authoritative tone."
        )

        prompt = f"""Write a blog post for {business_name}, a {industry} business in {location}.

Topic: {topic}
Based on this social post: "{short_caption}"

{voice_instruction}

Structure:
1. Intro: Hook + mention location and service
2. Body: 2-3 short paragraphs with practical tips or insights
3. Section: How this service helps local customers in {location}
4. Conclusion: Subtle call-to-action linking to {website_url}

SEO Keywords: {industry} {location}, local {industry} company

Format your response EXACTLY like this:

TITLE:
[Blog title, under 60 characters]

META_TITLE:
[SEO title, under 60 characters]

META_DESCRIPTION:
[SEO description, under 160 characters]

CONTENT:
[Full blog post content, 600-900 words, in markdown format]
"""
        return prompt

    def _parse_social_response(self, content: str) -> Dict[str, any]:
        """Parse AI response for social post."""
        lines = content.strip().split("\n")

        result = {"caption": "", "hashtags": [], "cta": ""}

        current_section = None
        caption_lines = []

        for line in lines:
            line = line.strip()
            if line.startswith("CAPTION:"):
                current_section = "caption"
                continue
            elif line.startswith("HASHTAGS:"):
                current_section = "hashtags"
                continue
            elif line.startswith("CTA:"):
                current_section = "cta"
                continue

            if current_section == "caption" and line:
                caption_lines.append(line)
            elif current_section == "hashtags" and line:
                # Extract hashtags
                hashtags = [tag.strip() for tag in line.split() if tag.startswith("#")]
                result["hashtags"] = hashtags
            elif current_section == "cta" and line:
                result["cta"] = line

        result["caption"] = "\n".join(caption_lines)

        return result

    def _parse_blog_response(self, content: str) -> Dict[str, str]:
        """Parse AI response for blog post."""
        lines = content.strip().split("\n")

        result = {
            "title": "",
            "meta_title": "",
            "meta_description": "",
            "content": "",
        }

        current_section = None
        content_lines = []

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith("TITLE:"):
                current_section = "title"
                continue
            elif line_stripped.startswith("META_TITLE:"):
                current_section = "meta_title"
                continue
            elif line_stripped.startswith("META_DESCRIPTION:"):
                current_section = "meta_description"
                continue
            elif line_stripped.startswith("CONTENT:"):
                current_section = "content"
                continue

            if current_section == "title" and line_stripped:
                result["title"] = line_stripped
            elif current_section == "meta_title" and line_stripped:
                result["meta_title"] = line_stripped
            elif current_section == "meta_description" and line_stripped:
                result["meta_description"] = line_stripped
            elif current_section == "content":
                content_lines.append(line)

        result["content"] = "\n".join(content_lines).strip()

        return result

    async def generate_platform_variations(
        self,
        base_caption: str,
        hashtags: List[str],
        cta: str,
        business_name: str,
        location: str,
        platforms: List[str],
    ) -> Dict[str, str]:
        """
        Generate platform-specific caption variations.

        Each platform has different best practices:
        - Facebook: Longer, conversational, storytelling
        - Instagram: Shorter, emoji-heavy, hashtags inline
        - LinkedIn: Professional, industry insights, no emojis
        - Google Business: Location-first, local SEO focused

        Returns:
            Dict with platform names as keys and optimized captions as values
        """

        # Return simple variations if OpenAI is not available
        if not self.client:
            hashtags_str = " ".join(hashtags)
            return {
                platform: f"[DEMO-{platform.upper()}] {base_caption}\n\n{hashtags_str}\n\n{cta}"
                for platform in platforms
            }

        platform_captions = {}

        for platform in platforms:
            if platform == "facebook":
                prompt = f"""Adapt this social media post for Facebook.

Base caption: {base_caption}

Make it:
- Slightly longer and more conversational
- Add storytelling elements
- Keep it friendly and engaging
- Don't include hashtags (they perform poorly on FB)
- End with: {cta}
- NEVER use em dashes (—) - use regular hyphens (-) or commas instead

Return ONLY the adapted caption, no labels."""

            elif platform == "instagram":
                prompt = f"""Adapt this social media post for Instagram.

Base caption: {base_caption}

Make it:
- Shorter and punchier
- Add 2-3 relevant emojis naturally
- Very engaging first line (for preview)
- End with: {cta}
- Include hashtags: {' '.join(hashtags[:5])}
- NEVER use em dashes (—) - use regular hyphens (-) or commas instead

Return ONLY the adapted caption with hashtags at the end, no labels."""

            elif platform == "linkedin":
                prompt = f"""Adapt this social media post for LinkedIn.

Base caption: {base_caption}

Make it:
- More professional and business-focused
- Add industry insights or expertise
- Use formal tone (no emojis)
- Focus on business value
- End with: {cta}
- NEVER use em dashes (—) - use regular hyphens (-) or commas instead

Return ONLY the adapted caption, no labels or hashtags."""

            elif platform == "google_business":
                prompt = f"""Adapt this social media post for Google Business Profile.

Base caption: {base_caption}

Make it:
- Start with: "In {location}, " (location-first for local SEO)
- Include service keywords naturally
- Keep under 1500 characters
- Engaging and helpful
- End with: {cta}
- NEVER use em dashes (—) - use regular hyphens (-) or commas instead

Return ONLY the adapted caption, no labels."""

            else:
                # Default: use base caption
                platform_captions[platform] = f"{base_caption}\n\n{cta}"
                continue

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert social media marketer who adapts content for different platforms.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=500,
                )

                adapted_caption = response.choices[0].message.content.strip()
                platform_captions[platform] = adapted_caption

            except Exception as e:
                # Fallback to base caption if generation fails
                print(f"⚠️ Failed to generate {platform} variation: {str(e)}")
                platform_captions[platform] = f"{base_caption}\n\n{cta}"

        return platform_captions

    async def generate_image(
        self,
        business_name: str,
        industry: str,
        topic: str,
        caption: str,
        style: str = "photographic",
    ) -> Dict[str, str]:
        """
        Generate AI image using DALL-E based on content topic.

        Args:
            business_name: Name of the business
            industry: Business industry
            topic: Content topic
            caption: Social media caption for context
            style: Image style - "photographic", "digital art", "minimalist", "professional"

        Returns:
            Dict with 'url' and 'revised_prompt'
        """

        # Return demo URL if OpenAI is not available
        if not self.client:
            return {
                "url": "https://via.placeholder.com/1024x1024.png?text=AI+Image+Generation+Demo",
                "revised_prompt": f"[DEMO] Image for {topic} - {business_name}",
            }

        # Build DALL-E prompt
        prompt = self._build_image_prompt(
            business_name=business_name,
            industry=industry,
            topic=topic,
            caption=caption,
            style=style,
        )

        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt

            return {
                "url": image_url,
                "revised_prompt": revised_prompt,
            }

        except Exception as e:
            raise Exception(f"Image generation failed: {str(e)}")

    def _build_image_prompt(
        self,
        business_name: str,
        industry: str,
        topic: str,
        caption: str,
        style: str,
    ) -> str:
        """Build the prompt for DALL-E image generation."""

        # Style modifiers
        style_descriptions = {
            "photographic": "high-quality professional photograph, realistic lighting, sharp focus",
            "digital art": "modern digital art style, vibrant colors, clean composition",
            "minimalist": "minimalist design, simple clean aesthetic, professional",
            "professional": "corporate professional style, polished, business-appropriate",
        }

        style_modifier = style_descriptions.get(style, style_descriptions["photographic"])

        # Build prompt focusing on the business context
        prompt = f"""Create a {style_modifier} image for a social media post about {topic}.

Business context: {business_name}, a {industry} company.
Post caption: {caption}

Requirements:
- Professional, high-quality imagery suitable for social media
- No text or words in the image
- {industry}-appropriate visual style
- Engaging and eye-catching composition
- Brand-safe and appropriate for business use

Style: {style_modifier}"""

        # Limit prompt length for DALL-E
        if len(prompt) > 1000:
            prompt = prompt[:997] + "..."

        return prompt

    async def generate_content_ideas(
        self,
        business_name: str,
        industry: str,
        location: str,
        brand_voice: Optional[str] = None,
        num_ideas: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Generate content topic ideas for a business.

        Args:
            business_name: Name of the business
            industry: Business industry
            location: Business location
            brand_voice: Optional brand voice/tone
            num_ideas: Number of ideas to generate

        Returns:
            List of dicts with 'topic', 'content_type', and 'description'
        """

        # Return demo ideas if OpenAI is not available
        if not self.client:
            return [
                {
                    "topic": f"[DEMO] 5 Signs You Need {industry} Services",
                    "content_type": "tip",
                    "description": "Educational post about common issues customers face"
                },
                {
                    "topic": f"[DEMO] Behind the Scenes at {business_name}",
                    "content_type": "team_update",
                    "description": "Show your team at work to build trust"
                },
                {
                    "topic": f"[DEMO] Customer Success Story from {location}",
                    "content_type": "testimonial",
                    "description": "Share a recent happy customer experience"
                },
            ]

        prompt = f"""Generate {num_ideas} content topic ideas for social media posts.

Business: {business_name}
Industry: {industry}
Location: {location}
{f'Brand Voice: {brand_voice}' if brand_voice else ''}

For each idea, provide:
1. A specific, engaging topic title
2. Content type (choose from: before_after, testimonial, offer, tip, team_update, project_showcase, seasonal, other)
3. Brief description of what the post would cover

Focus on:
- Local relevance to {location}
- {industry}-specific insights
- Mix of educational, promotional, and storytelling content
- Timely and seasonal topics
- Customer pain points and solutions

Format your response EXACTLY like this:

IDEA 1:
TOPIC: [Topic title]
TYPE: [content_type]
DESCRIPTION: [Brief description]

IDEA 2:
TOPIC: [Topic title]
TYPE: [content_type]
DESCRIPTION: [Brief description]

(Continue for all {num_ideas} ideas)
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative social media strategist helping local businesses generate engaging content ideas.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,  # Higher temperature for more creative ideas
                max_tokens=1500,
            )

            content = response.choices[0].message.content
            ideas = self._parse_ideas_response(content)

            return ideas

        except Exception as e:
            raise Exception(f"Content ideas generation failed: {str(e)}")

    def _parse_ideas_response(self, content: str) -> List[Dict[str, str]]:
        """Parse AI response for content ideas."""
        lines = content.strip().split("\n")

        ideas = []
        current_idea = {}

        for line in lines:
            line = line.strip()

            if line.startswith("IDEA"):
                if current_idea:
                    ideas.append(current_idea)
                current_idea = {}
            elif line.startswith("TOPIC:"):
                current_idea["topic"] = line.replace("TOPIC:", "").strip()
            elif line.startswith("TYPE:"):
                current_idea["content_type"] = line.replace("TYPE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                current_idea["description"] = line.replace("DESCRIPTION:", "").strip()

        # Add last idea
        if current_idea:
            ideas.append(current_idea)

        return ideas

    async def analyze_image_for_post(
        self,
        image_url: str,
        business_name: str,
        industry: str,
        location: str,
        notes: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Analyze an image and generate post topic, content type, and description.

        Uses GPT-4 Vision to understand what's in the image and suggest
        appropriate social media content.

        Returns:
            Dict with 'topic', 'content_type', 'description'
        """

        # Return demo content if OpenAI is not available
        if not self.client:
            return {
                "topic": f"[DEMO] Recent work for {business_name}",
                "content_type": "project_showcase",
                "description": f"Great project completed in {location}",
            }

        # OpenRouter doesn't support vision models, so this only works with OpenAI
        if self.provider != "OpenAI":
            # Fallback: return basic description
            return {
                "topic": f"Recent project in {location}",
                "content_type": "project_showcase",
                "description": f"Professional {industry} work showcased",
            }

        notes_context = f"\nClient notes: {notes}" if notes else ""

        prompt = f"""Analyze this image for {business_name}, a {industry} business in {location}.{notes_context}

Based on what you see in the image, provide:

1. **TOPIC**: A specific, engaging topic for a social media post (1-2 sentences describing what's shown)
2. **CONTENT_TYPE**: Choose ONE of these: before_after, testimonial, offer, tip, project_showcase, behind_scenes, announcement, educational, seasonal, other
3. **DESCRIPTION**: Brief description of what makes this image interesting for social media (2-3 sentences)

Consider:
- What is the main subject/focus of the image?
- What story does it tell about the business?
- What would make followers engage with this?
- Is this a before/after, a finished project, equipment, team at work, etc?

Format your response EXACTLY like this:

TOPIC:
[Your specific topic here]

CONTENT_TYPE:
[Your content type here]

DESCRIPTION:
[Your description here]"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-vision-preview",  # or gpt-4o for multimodal
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url},
                            },
                        ],
                    }
                ],
                temperature=0.7,
                max_tokens=500,
            )

            content = response.choices[0].message.content

            # Parse the response
            result = {"topic": "", "content_type": "project_showcase", "description": ""}

            lines = content.strip().split("\n")
            current_section = None

            for line in lines:
                line_stripped = line.strip()

                if line_stripped.startswith("TOPIC:"):
                    current_section = "topic"
                    continue
                elif line_stripped.startswith("CONTENT_TYPE:"):
                    current_section = "content_type"
                    continue
                elif line_stripped.startswith("DESCRIPTION:"):
                    current_section = "description"
                    continue

                if current_section and line_stripped:
                    if current_section == "topic":
                        result["topic"] = line_stripped
                    elif current_section == "content_type":
                        result["content_type"] = line_stripped
                    elif current_section == "description":
                        if result["description"]:
                            result["description"] += " " + line_stripped
                        else:
                            result["description"] = line_stripped

            return result

        except Exception as e:
            print(f"⚠️ Image analysis failed: {e}")
            # Fallback to basic description
            return {
                "topic": f"Recent project in {location}",
                "content_type": "project_showcase",
                "description": f"Professional {industry} work completed",
            }


# Singleton instance
ai_service = AIService()
