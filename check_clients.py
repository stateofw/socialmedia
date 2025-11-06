"""
Check clients in database
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_clients():
    """Check all clients"""

    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT id, business_name, email, is_active, owner_id
            FROM clients
            ORDER BY id;
        """))

        clients = result.fetchall()

        print(f"\nTotal clients in database: {len(clients)}")
        print("\nClient Details:")
        print("-" * 80)
        for client in clients:
            print(f"ID: {client[0]}")
            print(f"  Business: {client[1]}")
            print(f"  Email: {client[2] or '(NULL)'}")
            print(f"  Active: {client[3]}")
            print(f"  Owner ID: {client[4]}")
            print()

if __name__ == "__main__":
    asyncio.run(check_clients())
