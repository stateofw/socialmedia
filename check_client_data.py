#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.client import Client
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Client))
        clients = result.scalars().all()
        for c in clients:
            print(f"{c.business_name}:")
            print(f"  city: {c.city}")
            print(f"  state: {c.state}")
            print(f"  industry: {c.industry}")
            print()

asyncio.run(check())
