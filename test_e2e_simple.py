"""
Simple E2E Test: Create Client → Assign Publer Accounts → Submit Content → Verify Posting
"""

import asyncio
from datetime import datetime
from app.core.database import AsyncSessionLocal
from app.models.client import Client
from app.models.user import User
from app.models.content import Content
from sqlalchemy import select
import secrets


async def test_e2e_workflow():
    """Test end-to-end workflow."""
    
    print("=" * 70)
    print("END-TO-END WORKFLOW TEST")
    print("=" * 70)
    print()
    
    async with AsyncSessionLocal() as db:
        
        # Step 1: Get or create test user
        print("Step 1: Getting admin user...")
        result = await db.execute(select(User).where(User.email == "admin@test.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Admin user not found")
            return False
        
        print(f"✅ Found user: {user.email}")
        print()
        
        # Step 2: Create test client
        print("Step 2: Creating test client...")
        
        # Check if test client exists
        result = await db.execute(select(Client).where(Client.business_name == "Test Landscaping Co"))
        existing_client = result.scalar_one_or_none()
        
        if existing_client:
            print("⚠️ Test client already exists, using existing...")
            test_client = existing_client
        else:
            test_client = Client(
                business_name="Test Landscaping Co",
                industry="landscaping",
                city="Brewster",
                state="NY",
                service_area="Putnam County, NY",
                monthly_post_limit=10,
                auto_post=True,  # Enable auto-posting
                platforms_enabled=["facebook", "instagram"],
                primary_contact_email="test@landscaping.com",
                intake_token=secrets.token_urlsafe(16),
                owner_id=user.id,
            )
            db.add(test_client)
            await db.commit()
            await db.refresh(test_client)
            print(f"✅ Created test client: {test_client.business_name}")
        
        print(f"   Client ID: {test_client.id}")
        print(f"   Auto-post enabled: {test_client.auto_post}")
        print()
        
        # Step 3: Assign Publer accounts
        print("Step 3: Assigning Publer account IDs...")
        test_client.publer_account_ids = [
            "68ff8b28dbe5ada5b0944612",  # Facebook
            "68ff8a6b3dcf47a98fa11eb8",  # Instagram
        ]
        await db.commit()
        print(f"✅ Assigned {len(test_client.publer_account_ids)} Publer accounts")
        print()
        
        # Step 4: Create content manually (simulating intake form)
        print("Step 4: Creating content...")
        content = Content(
            client_id=test_client.id,
            topic="Beautiful lawn renovation completed in Brewster",
            content_type="project_showcase",
            focus_location="Brewster, NY",
            notes="Customer loved the results. Quick 2-day turnaround.",
            platforms=["facebook", "instagram"],
            status="draft",
        )
        db.add(content)
        await db.commit()
        await db.refresh(content)
        print(f"✅ Created content (ID: {content.id})")
        print()
        
        #Step 5: Import and run content generation
        print("Step 5: Running content generation workflow...")
        print("   This will:")
        print("   - Generate AI content")
        print("   - Polish the caption")
        print("   - Generate hashtags")
        print("   - Create platform variations")
        print("   - Post to Publer (since auto_post=True)")
        print()
        
        from app.api.routes.intake import generate_and_process_content
        
        try:
            await generate_and_process_content(
                content_id=content.id,
                client_id=test_client.id,
                auto_post=True,
            )
            
            # Refresh content to see results
            await db.refresh(content)
            
            print()
            print("=" * 70)
            print("RESULTS")
            print("=" * 70)
            print()
            print(f"Content ID: {content.id}")
            print(f"Status: {content.status}")
            print()
            
            if content.caption:
                print("Caption (preview):")
                print(f"  {content.caption[:200]}...")
                print()
            
            if content.hashtags:
                print(f"Hashtags: {' '.join(content.hashtags[:5])}...")
                print()
            
            if content.platform_captions:
                print("Platform Variations Created:")
                for platform in content.platform_captions.keys():
                    print(f"  ✅ {platform}")
                print()
            
            if content.platform_post_ids:
                print("✅ POSTED TO PUBLER!")
                print("Platform Post IDs:")
                for platform, post_id in content.platform_post_ids.items():
                    print(f"  {platform}: {post_id}")
                print()
            
            if content.published_at:
                print(f"Published at: {content.published_at}")
                print()
            
            if content.error_message:
                print(f"⚠️ Error: {content.error_message}")
                print()
            
            # Final verdict
            if content.status == "published":
                print("=" * 70)
                print("🎉 SUCCESS! Content generated and posted to social media!")
                print("=" * 70)
                return True
            elif content.status == "failed":
                print("=" * 70)
                print(f"❌ FAILED: {content.error_message}")
                print("=" * 70)
                return False
            else:
                print("=" * 70)
                print(f"⏳ Status: {content.status}")
                print("=" * 70)
                return False
        
        except Exception as e:
            print(f"\n❌ Error during workflow: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_e2e_workflow())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
