"""
Test Approval Workflow: Content → Pending → Admin Approves → Schedule to Publer
"""

import asyncio
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal
from app.models.content import Content
from app.models.client import Client
from app.models.user import User
from sqlalchemy import select


async def test_approval_workflow():
    """Test the approval workflow."""
    
    print("=" * 70)
    print("APPROVAL WORKFLOW TEST")
    print("=" * 70)
    print()
    
    async with AsyncSessionLocal() as db:
        
        # Step 1: Get test client
        print("Step 1: Getting test client...")
        result = await db.execute(select(Client).where(Client.business_name == "Test Landscaping Co"))
        client = result.scalar_one_or_none()
        
        if not client:
            print("❌ Test client not found. Run test_e2e_simple.py first.")
            return False
        
        print(f"✅ Found client: {client.business_name}")
        print(f"   Publer accounts: {len(client.publer_account_ids or [])}")
        print()
        
        # Step 2: Create content
        print("Step 2: Creating new content...")
        content = Content(
            client_id=client.id,
            topic="Fall cleanup special - Get your yard ready for winter",
            content_type="offer",
            focus_location="Brewster, NY",
            notes="Special pricing for October. Leaf removal and winterization.",
            platforms=["facebook", "instagram"],
            status="draft",
        )
        db.add(content)
        await db.commit()
        await db.refresh(content)
        print(f"✅ Created content (ID: {content.id})")
        print()
        
        # Step 3: Run content generation (without auto-posting)
        print("Step 3: Generating AI content...")
        print("   (This will set status to PENDING_APPROVAL)")
        print()
        
        from app.api.routes.intake import generate_and_process_content
        
        await generate_and_process_content(
            content_id=content.id,
            client_id=client.id,
            auto_post=False,  # Should go to pending approval
        )
        
        await db.refresh(content)
        
        print(f"✅ Content generated")
        print(f"   Status: {content.status}")
        print(f"   Caption preview: {content.caption[:100]}...")
        print()
        
        if content.status != "PENDING_APPROVAL":
            print(f"❌ Expected PENDING_APPROVAL, got {content.status}")
            return False
        
        # Step 4: Admin reviews and approves
        print("Step 4: Admin approving content...")
        print("   Scheduling for 5 minutes from now")
        print()
        
        from app.api.routes.approval import publish_approved_content
        
        # Set scheduled time to 5 minutes from now
        scheduled_time = datetime.utcnow() + timedelta(minutes=5)
        content.status = "APPROVED"
        content.scheduled_at = scheduled_time
        await db.commit()
        
        # Run the publish function
        await publish_approved_content(
            content_id=content.id,
            client_id=client.id,
        )
        
        await db.refresh(content)
        
        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()
        print(f"Content ID: {content.id}")
        print(f"Status: {content.status}")
        print(f"Scheduled At: {content.scheduled_at}")
        print()
        
        if content.caption:
            print("Caption (preview):")
            print(f"  {content.caption[:200]}...")
            print()
        
        if content.platform_captions:
            print("Platform Variations:")
            for platform in content.platform_captions.keys():
                print(f"  ✅ {platform}")
            print()
        
        if content.platform_post_ids:
            print("Platform Post IDs:")
            for platform, post_id in content.platform_post_ids.items():
                print(f"  {platform}: {post_id}")
            print()
        
        if content.error_message:
            print(f"⚠️ Error: {content.error_message}")
            print()
        
        # Final verdict
        if content.status == "SCHEDULED":
            print("=" * 70)
            print("🎉 SUCCESS! Content scheduled to Publer!")
            print("=" * 70)
            print()
            print(f"The post will go live at: {content.scheduled_at}")
            print("Check your Publer dashboard to see the scheduled post!")
            return True
        else:
            print("=" * 70)
            print(f"❌ FAILED: Status is {content.status}")
            print("=" * 70)
            return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_approval_workflow())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
