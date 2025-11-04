"""
Test Complete Content Generation and Publer Posting Workflow

This script tests the full end-to-end workflow:
1. Get existing client or create new one
2. Assign Publer account IDs to client
3. Submit content via intake form with auto_post=True
4. Verify content gets generated and posted to Publer
"""

import asyncio
import httpx
from datetime import datetime


API_BASE = "http://localhost:8000/api/v1"


async def test_full_workflow():
    """Test the complete workflow."""
    
    print("=" * 70)
    print("FULL WORKFLOW TEST: Content Generation → Publer Posting")
    print("=" * 70)
    print()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # Step 1: Login as admin
        print("Step 1: Authenticating as admin...")
        login_response = await client.post(
            f"{API_BASE}/auth/login",
            data={
                "username": "admin@test.com",  # OAuth2 uses 'username' field
                "password": "admin123",
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authenticated successfully")
        print()
        
        # Step 2: Get existing clients
        print("Step 2: Checking for existing clients...")
        clients_response = await client.get(
            f"{API_BASE}/clients",
            headers=headers
        )
        
        clients = clients_response.json()
        
        if not clients:
            print("⚠️ No clients found. Please create a client first.")
            return False
        
        # Use first client
        test_client = clients[0]
        client_id = test_client["id"]
        business_name = test_client["business_name"]
        
        print(f"✅ Using client: {business_name} (ID: {client_id})")
        print()
        
        # Step 3: Assign Publer account IDs
        print("Step 3: Assigning Publer account IDs to client...")
        
        # Use the Facebook and Instagram accounts from our test
        publer_accounts = [
            "68ff8b28dbe5ada5b0944612",  # Facebook - Easy Tech Web Design
            "68ff8a6b3dcf47a98fa11eb8",  # Instagram - Easy Tech Web Design
        ]
        
        assign_response = await client.post(
            f"{API_BASE}/clients/{client_id}/publer-accounts",
            json=publer_accounts,
            headers=headers
        )
        
        if assign_response.status_code != 200:
            print(f"❌ Failed to assign Publer accounts: {assign_response.status_code}")
            print(assign_response.text)
            return False
        
        print(f"✅ Assigned {len(publer_accounts)} Publer accounts")
        print()
        
        # Step 4: Submit content via intake form with auto_post=True
        print("Step 4: Submitting content via intake form...")
        print(f"   Topic: Test landscaping project showcase")
        print(f"   Auto-post: YES")
        print()
        
        # Get the client's intake token
        intake_token = test_client.get("intake_token")
        
        if not intake_token:
            print("❌ Client has no intake token")
            return False
        
        intake_data = {
            "topic": "Completed a beautiful lawn renovation in Brewster, NY",
            "content_type": "project_showcase",
            "focus_location": "Brewster, NY",
            "notes": "Customer was thrilled with the new lawn. Professional work, quick turnaround.",
            "media_urls": [],
            "auto_post": True,  # This will trigger immediate posting
        }
        
        intake_response = await client.post(
            f"{API_BASE}/intake/{intake_token}/submit",
            json=intake_data
        )
        
        if intake_response.status_code != 201:
            print(f"❌ Failed to submit intake form: {intake_response.status_code}")
            print(intake_response.text)
            return False
        
        result = intake_response.json()
        content_id = result["content_id"]
        
        print(f"✅ Content submitted (ID: {content_id})")
        print(f"   Status: {result['status']}")
        print()
        
        # Step 5: Wait for background processing
        print("Step 5: Waiting for AI generation and Publer posting...")
        print("   This may take 30-60 seconds...")
        print()
        
        await asyncio.sleep(45)  # Wait for processing
        
        # Step 6: Check content status
        print("Step 6: Checking final content status...")
        
        content_response = await client.get(
            f"{API_BASE}/content/{content_id}",
            headers=headers
        )
        
        if content_response.status_code != 200:
            print(f"❌ Failed to get content: {content_response.status_code}")
            return False
        
        content = content_response.json()
        
        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()
        print(f"Content ID: {content['id']}")
        print(f"Topic: {content['topic']}")
        print(f"Status: {content['status']}")
        print()
        
        if content.get("caption"):
            print("Generated Caption (preview):")
            print(f"  {content['caption'][:200]}...")
            print()
        
        if content.get("hashtags"):
            print(f"Hashtags: {', '.join(content['hashtags'][:5])}...")
            print()
        
        if content.get("platform_captions"):
            print("Platform Variations:")
            for platform, caption in content["platform_captions"].items():
                print(f"  {platform}: {caption[:80]}...")
            print()
        
        if content.get("platform_post_ids"):
            print("✅ POSTED TO SOCIAL MEDIA!")
            print("Platform Post IDs:")
            for platform, post_id in content["platform_post_ids"].items():
                print(f"  {platform}: {post_id}")
            print()
        
        if content.get("published_at"):
            print(f"Published at: {content['published_at']}")
            print()
        
        if content.get("error_message"):
            print(f"⚠️ Error: {content['error_message']}")
            print()
        
        # Final verdict
        if content["status"] == "published":
            print("=" * 70)
            print("🎉 SUCCESS! Content was generated and posted to Publer!")
            print("=" * 70)
            print()
            print("Check your Facebook and Instagram pages to see the post!")
            return True
        elif content["status"] == "failed":
            print("=" * 70)
            print("❌ FAILED: Content generation or posting failed")
            print("=" * 70)
            return False
        else:
            print("=" * 70)
            print(f"⚠️ UNEXPECTED STATUS: {content['status']}")
            print("=" * 70)
            return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_full_workflow())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
