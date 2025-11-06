#!/usr/bin/env python3
"""
Migration: Add password_hash field to client_signups table

Run this once to add the password_hash column for client-chosen passwords
during signup.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


async def add_password_column():
    """Add password_hash column to client_signups table"""
    print("🔄 Adding password_hash column to client_signups...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Add password_hash column (nullable for existing records)
            await db.execute(text(
                "ALTER TABLE client_signups ADD COLUMN IF NOT EXISTS password_hash VARCHAR"
            ))
            await db.commit()
            print("✅ Successfully added password_hash column to client_signups")
            
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            print("   (This is OK if column already exists)")
            return False
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(add_password_column())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
