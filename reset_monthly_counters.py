#!/usr/bin/env python3
"""
Reset monthly post counters for all clients.
Run this on the 1st of each month via cron or manually.

Usage:
    python reset_monthly_counters.py
    
Or via Fly.io:
    flyctl ssh console --app social-automation-saas -C "cd /app && python reset_monthly_counters.py"
"""

import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from sqlalchemy import update, select
from app.models.client import Client


async def reset_all_counters():
    """Reset posts_this_month to 0 for all clients"""
    print("🔄 Resetting monthly post counters...")
    
    async with AsyncSessionLocal() as db:
        # Get count before reset
        result = await db.execute(select(Client))
        total_clients = len(result.scalars().all())
        
        # Reset all counters
        await db.execute(
            update(Client).values(posts_this_month=0)
        )
        await db.commit()
        
        print(f"✅ Successfully reset counters for {total_clients} clients")
        print(f"   All clients now have posts_this_month = 0")
        
        return total_clients


if __name__ == "__main__":
    try:
        count = asyncio.run(reset_all_counters())
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error resetting counters: {e}")
        sys.exit(1)
