#!/usr/bin/env python3
"""
Test script to verify OpenRouter integration.
"""
import sys
import asyncio

sys.path.insert(0, '.')

async def test_openrouter():
    from app.services.ai import ai_service
    from app.core.config import settings

    print("="*60)
    print("OPENROUTER CONFIGURATION TEST")
    print("="*60)
    print()

    # Check configuration
    print("Configuration:")
    print(f"  USE_OPENROUTER: {settings.USE_OPENROUTER}")
    print(f"  OPENROUTER_API_KEY: {'✅ Set' if settings.OPENROUTER_API_KEY else '❌ Not set'}")
    print(f"  OPENROUTER_MODEL: {settings.OPENROUTER_MODEL}")
    print()

    # Check AI service
    print("AI Service:")
    print(f"  Provider: {ai_service.provider}")
    print(f"  Model: {ai_service.model}")
    print(f"  Client: {'✅ Initialized' if ai_service.client else '❌ Not initialized'}")
    print()

    if not ai_service.client:
        print("❌ AI service not initialized. Check your configuration.")
        return

    # Test API call
    print("Testing API call...")
    try:
        result = await ai_service.generate_social_post(
            business_name="Test Company",
            industry="Technology",
            topic="The Future of AI in Business",
            location="San Francisco, CA",
            content_type="tip",
            brand_voice="Professional and engaging",
            notes="Make it exciting and forward-thinking"
        )

        print("✅ API call successful!")
        print()
        print("Generated Content:")
        print("-" * 60)
        print(f"Caption: {result['caption'][:100]}...")
        print(f"Hashtags: {', '.join(result['hashtags'][:3])}...")
        print(f"CTA: {result['cta']}")
        print()
        print("="*60)
        print("✅ OPENROUTER TEST PASSED!")
        print("="*60)

    except Exception as e:
        print(f"❌ API call failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check that USE_OPENROUTER=true in .env")
        print("  2. Verify OPENROUTER_API_KEY is correct")
        print("  3. Ensure you have internet connectivity")
        print("  4. Check OpenRouter service status")

if __name__ == "__main__":
    asyncio.run(test_openrouter())
