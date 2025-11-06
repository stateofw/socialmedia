"""
Migration script to add email column to clients table
Run this ONCE on your database
"""
import asyncio
from sqlalchemy import text
from app.core.database import get_db_engine

async def run_migration():
    """Add email column to clients table"""
    engine = get_db_engine()

    async with engine.begin() as conn:
        # Check if column already exists
        check_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='clients' AND column_name='email';
        """
        result = await conn.execute(text(check_query))
        exists = result.first()

        if exists:
            print("✅ Email column already exists")
            return

        # Add email column
        print("Adding email column to clients table...")
        await conn.execute(text("""
            ALTER TABLE clients
            ADD COLUMN email VARCHAR UNIQUE;
        """))

        # Create index
        print("Creating index on email column...")
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_clients_email ON clients(email);
        """))

        print("✅ Migration completed successfully!")
        print("⚠️  Important: Update existing clients to have email addresses")

if __name__ == "__main__":
    asyncio.run(run_migration())
