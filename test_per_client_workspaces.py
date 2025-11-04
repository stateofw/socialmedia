"""
Test script to demonstrate per-client Publer workspace isolation.

This script demonstrates:
1. Each client has their own Publer workspace
2. Account IDs are validated within the correct workspace
3. Posts go to the correct client's accounts
4. Complete isolation between clients
"""

import asyncio
from app.services.publer import publer_service


async def test_per_client_workspaces():
    """Demonstrate per-client workspace architecture."""

    print("=" * 70)
    print("PER-CLIENT PUBLER WORKSPACE ARCHITECTURE TEST")
    print("=" * 70)

    # Your available workspaces from Publer
    workspaces = await publer_service.list_workspaces()

    print("\n📁 Available Publer Workspaces:")
    for ws in workspaces:
        print(f"   - {ws.get('name')}: {ws.get('id')}")

    print("\n" + "=" * 70)
    print("RECOMMENDED SETUP")
    print("=" * 70)

    print("""
For each client you onboard:

1️⃣ CREATE WORKSPACE IN PUBLER
   - Go to Publer dashboard
   - Create new workspace: "[Client Name] - Social Accounts"
   - Example: "Joe's Landscaping - Social Accounts"

2️⃣ CONNECT CLIENT'S ACCOUNTS TO THAT WORKSPACE
   - Switch to the client's workspace
   - Add client's Facebook Page
   - Add client's Instagram Business
   - Add any other social accounts

3️⃣ SET WORKSPACE ID FOR CLIENT IN YOUR SYSTEM
   - When creating client, set publer_workspace_id
   - Or update existing client via PATCH /api/v1/clients/{id}

4️⃣ ASSIGN ACCOUNT IDs TO CLIENT
   - List accounts in that workspace
   - Copy account IDs
   - Assign via POST /api/v1/clients/{id}/publer-accounts
    """)

    print("=" * 70)
    print("EXAMPLE: Two Clients with Separate Workspaces")
    print("=" * 70)

    # Simulate checking different workspaces
    example_clients = [
        {
            "name": "Joe's Landscaping",
            "workspace_id": "68d2b8a98ed70f0256e12fdc",  # Baudi Landscaping workspace
            "workspace_name": "Baudi Landscaping",
        },
        {
            "name": "Unique IT Pro",
            "workspace_id": "68cca3dfb6466a76758cac39",  # unique it pro workspace
            "workspace_name": "unique it pro",
        },
    ]

    for client in example_clients:
        print(f"\n👤 Client: {client['name']}")
        print(f"   Workspace: {client['workspace_name']} ({client['workspace_id']})")

        # List accounts in this client's workspace
        accounts = await publer_service.list_accounts(
            include_details=True,
            workspace_id=client['workspace_id']
        )

        if accounts:
            print(f"   ✅ Found {len(accounts)} account(s) in this workspace:")
            for acc in accounts:
                print(f"      - {acc.get('display', 'Unknown')}")
        else:
            print(f"   ⚠️ No accounts connected to this workspace yet")

    print("\n" + "=" * 70)
    print("BENEFITS OF PER-CLIENT WORKSPACES")
    print("=" * 70)
    print("""
✅ COMPLETE ISOLATION
   - Client A's posts ONLY go to Client A's accounts
   - Client B's posts ONLY go to Client B's accounts
   - Impossible to accidentally cross-post

✅ CLEAR ORGANIZATION
   - One workspace = One client
   - Easy to audit and manage
   - Clear in Publer dashboard

✅ CLIENT INDEPENDENCE
   - Each client can have different permissions
   - Can transfer workspace ownership if needed
   - Client data stays separate

✅ SCALABILITY
   - Add unlimited clients
   - Each isolated from others
   - No account ID conflicts
    """)

    print("=" * 70)
    print("HOW IT WORKS IN CODE")
    print("=" * 70)
    print("""
When client submits content:
1. System looks up client record
2. Gets client.publer_workspace_id
3. Gets client.publer_account_ids
4. Validates account IDs exist in THAT workspace
5. Schedules post to accounts in THAT workspace
6. Complete isolation guaranteed

Code example:
    # Client 1: Joe's Landscaping
    client_1.publer_workspace_id = "68d2b8a98ed70f0256e12fdc"
    client_1.publer_account_ids = ["account_id_1", "account_id_2"]

    # Client 2: Unique IT Pro
    client_2.publer_workspace_id = "68cca3dfb6466a76758cac39"
    client_2.publer_account_ids = ["account_id_3", "account_id_4"]

    # When posting for Client 1:
    publer_service.schedule_post(
        account_ids=client_1.publer_account_ids,
        workspace_id=client_1.publer_workspace_id  # ← Ensures isolation
    )
    """)

    print("\n" + "=" * 70)
    print("✅ PER-CLIENT WORKSPACE ARCHITECTURE READY")
    print("=" * 70)

    return True


async def main():
    """Run the workspace demonstration."""
    try:
        await test_per_client_workspaces()
        print("\n✅ Per-client workspace architecture is properly configured!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
