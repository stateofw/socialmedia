"""
Fix script to activate all clients
Run this ONCE on your database
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def fix_clients():
    """Set all clients to active"""

    async with engine.begin() as conn:
        # Update any inactive or null clients to be active
        result = await conn.execute(text("""
            UPDATE clients
            SET is_active = true
            WHERE is_active IS NULL OR is_active = false
            RETURNING id, business_name;
        """))

        updated_clients = result.fetchall()

        if updated_clients:
            print(f"✅ Updated {len(updated_clients)} clients to active status:")
            for client in updated_clients:
                print(f"   - ID {client[0]}: {client[1]}")
        else:
            print("✅ All clients are already active")

if __name__ == "__main__":
    asyncio.run(fix_clients())
