#!/usr/bin/env python3
"""
Fix existing clients who don't have email set.
Copies primary_contact_email to email field for login.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.client import Client


async def fix_client_emails():
    """Fix clients with missing email field"""
    print("🔄 Fixing client emails...")
    
    async with AsyncSessionLocal() as db:
        # Get all clients
        result = await db.execute(select(Client))
        clients = result.scalars().all()
        
        fixed_count = 0
        for client in clients:
            if not client.email and client.primary_contact_email:
                print(f"   Fixing {client.business_name}: {client.primary_contact_email}")
                client.email = client.primary_contact_email
                fixed_count += 1
            elif not client.email:
                print(f"   ⚠️ {client.business_name}: No email available to set")
        
        await db.commit()
        
        print(f"✅ Fixed {fixed_count} clients")
        return fixed_count


if __name__ == "__main__":
    try:
        count = asyncio.run(fix_client_emails())
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
