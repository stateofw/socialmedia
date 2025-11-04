"""
Test script to verify Publer account mapping logic.

This script tests:
1. Publer API connection
2. Account listing with display names
3. Account validation
4. Complete flow from account discovery to assignment
"""

import asyncio
import sys
from app.services.publer import publer_service
from app.core.config import settings


async def test_publer_integration():
    """Test the complete Publer integration flow."""

    print("=" * 60)
    print("PUBLER INTEGRATION TEST")
    print("=" * 60)

    # Test 1: Check API credentials
    print("\n1️⃣ Testing API Configuration...")
    if not settings.PUBLER_API_KEY:
        print("❌ ERROR: PUBLER_API_KEY not configured in .env")
        return False
    print(f"✅ API Key configured: {settings.PUBLER_API_KEY[:10]}...")

    if settings.PUBLER_WORKSPACE_ID:
        print(f"✅ Workspace ID configured: {settings.PUBLER_WORKSPACE_ID}")
    else:
        print("⚠️ Workspace ID not configured, will auto-fetch from API")

    # Test 2: Get user info
    print("\n2️⃣ Testing API Connection...")
    user_info = await publer_service.get_user_info()
    if not user_info:
        print("❌ ERROR: Failed to connect to Publer API")
        return False
    print(f"✅ Connected as: {user_info.get('name', 'Unknown')} ({user_info.get('email', 'Unknown')})")

    # Test 3: List workspaces
    print("\n3️⃣ Testing Workspace Access...")
    workspaces = await publer_service.list_workspaces()
    if not workspaces:
        print("❌ ERROR: No workspaces found")
        return False
    print(f"✅ Found {len(workspaces)} workspace(s)")
    for ws in workspaces:
        print(f"   - {ws.get('name', 'Unnamed')} (ID: {ws.get('id')})")

    # Test 4: Get workspace ID
    print("\n4️⃣ Testing Workspace ID Resolution...")
    workspace_id = await publer_service.get_workspace_id()
    if not workspace_id:
        print("❌ ERROR: Could not determine workspace ID")
        return False
    print(f"✅ Using workspace: {workspace_id}")

    # Test 5: List accounts with display names
    print("\n5️⃣ Testing Account Listing (with human-readable names)...")
    accounts = await publer_service.list_accounts(include_details=True)
    if not accounts:
        print("⚠️ WARNING: No social accounts connected to Publer workspace")
        print("   To test account assignment:")
        print("   1. Log into Publer dashboard")
        print("   2. Connect some social media accounts")
        print("   3. Run this test again")
        return False

    print(f"✅ Found {len(accounts)} connected social account(s):")
    for account in accounts:
        print(f"\n   📱 {account.get('display', 'Unknown Account')}")
        print(f"      ID: {account.get('id')}")
        print(f"      Provider: {account.get('provider', 'unknown')}")
        print(f"      Type: {account.get('type', 'N/A')}")

    # Test 6: Validate account IDs
    print("\n6️⃣ Testing Account ID Validation...")
    if accounts:
        # Test with valid IDs
        valid_ids = [accounts[0]['id']]
        validation = await publer_service.validate_account_ids(valid_ids)
        if validation.get(valid_ids[0]):
            print(f"✅ Valid ID recognized: {valid_ids[0]}")
        else:
            print(f"❌ ERROR: Valid ID not recognized: {valid_ids[0]}")
            return False

        # Test with invalid ID
        invalid_id = "invalid_account_id_12345"
        validation = await publer_service.validate_account_ids([invalid_id])
        if not validation.get(invalid_id):
            print(f"✅ Invalid ID rejected: {invalid_id}")
        else:
            print(f"❌ ERROR: Invalid ID was accepted: {invalid_id}")
            return False

    # Test 7: Get account details
    print("\n7️⃣ Testing Account Details Retrieval...")
    if accounts:
        account_ids = [acc['id'] for acc in accounts[:2]]  # Test with first 2 accounts
        details = await publer_service.get_account_details(account_ids)
        print(f"✅ Retrieved details for {len(details)} account(s):")
        for aid, info in details.items():
            print(f"   - {info.get('display', 'Unknown')}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\n📋 ACCOUNT ASSIGNMENT WORKFLOW:")
    print("1. Admin creates client in system")
    print("2. Client's social accounts get added to this Publer workspace")
    print("3. Admin uses API: POST /api/v1/clients/{id}/publer-accounts")
    print("4. System validates account IDs exist")
    print("5. System shows human-readable names for verification")
    print("6. Admin confirms, accounts assigned to client")
    print("7. Posts to that client go to ONLY those accounts")
    print("\n🔒 SAFETY FEATURES:")
    print("✓ Account IDs validated before assignment")
    print("✓ Human-readable names shown (e.g., 'Facebook: Joe's Landscaping')")
    print("✓ Verification message shows where posts will go")
    print("✓ Admin can review assignments via GET /api/v1/clients/{id}/publer-accounts")

    return True


async def main():
    """Run the integration test."""
    try:
        success = await test_publer_integration()
        if success:
            print("\n✅ Publer integration is working correctly!")
            sys.exit(0)
        else:
            print("\n❌ Publer integration has issues that need fixing")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
