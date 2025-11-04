"""
Test Publer Post Scheduling

This script tests scheduling a post to Facebook via Publer API.
"""

import asyncio
from datetime import datetime, timedelta
from app.services.publer import publer_service


async def test_schedule_facebook_post():
    """Test scheduling a post to Facebook."""
    
    print("=" * 60)
    print("PUBLER POST SCHEDULING TEST")
    print("=" * 60)
    print()
    
    # Facebook account ID from our earlier test
    facebook_account_id = "68ff8b28dbe5ada5b0944612"
    
    # Schedule for 5 minutes from now
    scheduled_time = datetime.utcnow() + timedelta(minutes=5)
    
    print(f"📅 Scheduling post for: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"📱 Platform: Facebook")
    print(f"🏢 Account: Easy Tech Web Design")
    print()
    
    # Build platform-specific content
    # For Facebook, we use a simple status post
    content_dict = {
        "facebook": {
            "type": "status",
            "text": "🚀 Test post from Social Automation SaaS!\n\nThis is an automated test post scheduled via Publer API. If you're seeing this, our integration is working perfectly!\n\n#AutomationTest #SocialMediaManagement"
        }
    }
    
    print("📝 Post content:")
    print(content_dict["facebook"]["text"])
    print()
    print("-" * 60)
    print("Sending request to Publer API...")
    print("-" * 60)
    print()
    
    # Schedule the post
    result = await publer_service.schedule_post(
        account_ids=[facebook_account_id],
        content_dict=content_dict,
        scheduled_time=scheduled_time,
    )
    
    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)
    print()
    
    if result.get("status") == "success":
        print("✅ POST SCHEDULED SUCCESSFULLY!")
        print()
        print(f"Job ID: {result.get('job_id', 'N/A')}")
        print(f"Status: {result.get('status')}")
        
        if result.get("payload"):
            payload = result.get("payload", {})
            print()
            print("Response payload:")
            print(f"  Posts created: {len(payload.get('posts', []))}")
            
            for idx, post in enumerate(payload.get("posts", []), 1):
                print(f"\n  Post #{idx}:")
                print(f"    ID: {post.get('id', 'N/A')}")
                print(f"    Status: {post.get('state', 'N/A')}")
                print(f"    Scheduled: {post.get('scheduled_at', 'N/A')}")
        
        print()
        print("🎉 Check your Facebook page in 5 minutes to see the post!")
        return True
        
    elif result.get("status") == "failed":
        print("❌ POST SCHEDULING FAILED")
        print()
        print(f"Status: {result.get('status')}")
        print(f"Errors: {result.get('errors', 'No error details')}")
        return False
        
    else:
        print("⚠️ UNKNOWN STATUS")
        print()
        print(f"Result: {result}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_schedule_facebook_post())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
