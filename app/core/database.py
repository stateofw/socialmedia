from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Fix DATABASE_URL - convert postgres:// to postgresql+asyncpg:// and handle SSL mode
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Remove sslmode parameter - Fly.io internal connections don't need SSL
import re
database_url = re.sub(r'[?&]sslmode=[^&]*', '', database_url)
# Clean up any trailing ? or & from URL
database_url = re.sub(r'[?&]$', '', database_url)

# Create async engine without SSL for Fly.io internal connections
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
    connect_args={
        "ssl": False  # Disable SSL for Fly.io internal network
    }
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
