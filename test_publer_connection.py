"""
Test Publer API Connection

This script tests the Publer API integration by:
1. Listing all connected social media accounts
2. Displaying account details (provider, name, type)
"""

import asyncio
import sys
from app.services.publer import publer_service


async def test_publer_connection():
    """Test Publer API connection and list accounts."""

    print("=" * 60)
    print("PUBLER API CONNECTION TEST")
    print("=" * 60)
    print()

    # Check if API is configured
    if not publer_service.api_key:
        print("❌ PUBLER_API_KEY not configured in .env")
        return False

    if not publer_service.workspace_id:
        print("⚠️ PUBLER_WORKSPACE_ID not set (will use from first request)")

    print(f"✅ API Key: {publer_service.api_key[:20]}...")
    print(f"✅ Base URL: {publer_service.base_url}")
    if publer_service.workspace_id:
        print(f"✅ Workspace ID: {publer_service.workspace_id}")
    print()

    # List connected accounts
    print("Fetching connected social media accounts...")
    print("-" * 60)

    accounts = await publer_service.list_accounts()

    if not accounts:
        print("❌ No accounts found or API error occurred")
        print()
        print("TROUBLESHOOTING:")
        print("1. Verify PUBLER_API_KEY is correct")
        print("2. Ensure PUBLER_WORKSPACE_ID is set (if required)")
        print("3. Check that accounts are connected in Publer dashboard")
        print("4. Verify API has proper scopes (posts, media, accounts)")
        return False

    print(f"\n✅ Found {len(accounts)} connected account(s):\n")

    # Display account details
    for i, account in enumerate(accounts, 1):
        print(f"Account #{i}:")
        print(f"  ID: {account.get('id')}")
        print(f"  Provider: {account.get('provider', 'N/A')}")
        print(f"  Name: {account.get('name', 'N/A')}")
        print(f"  Type: {account.get('type', 'N/A')}")
        print(f"  Social ID: {account.get('social_id', 'N/A')}")
        if account.get('picture'):
            print(f"  Picture: {account.get('picture')[:50]}...")
        print()

    print("=" * 60)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("NEXT STEPS:")
    print("1. Copy account IDs from above")
    print("2. Store them in your Client model's publer_account_ids field")
    print("3. Use these IDs when scheduling posts via Publer")
    print()

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_publer_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
