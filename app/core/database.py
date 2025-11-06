from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from urllib.parse import urlparse, parse_qs
import re
from app.core.config import settings

# Normalize DATABASE_URL to asyncpg dialect
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Decide SSL behavior:
# - Disable SSL for Fly.io internal Postgres (".internal" host)
# - Disable SSL for obvious local/dev hosts (localhost, 127.0.0.1, docker service "db")
# - Otherwise enable SSL for public/managed endpoints
parsed = urlparse(database_url)
host = (parsed.hostname or "").lower()
query = parse_qs(parsed.query)

# Respect explicit URL flag if present (e.g., ?ssl=true/false)
explicit_ssl = None
if "ssl" in query:
    val = (query.get("ssl", [""])[0] or "").lower()
    explicit_ssl = val in ("1", "true", "t", "yes", "y", "on", "require")

internal_hosts = (
    host.endswith(".internal")
    or host in {"localhost", "127.0.0.1", "::1", "db"}
)

if explicit_ssl is not None:
    use_ssl = explicit_ssl
else:
    # Default: production => enable SSL unless internal; non-prod => disable unless explicitly requested
    if settings.ENV.lower() == "production":
        use_ssl = not internal_hosts
    else:
        use_ssl = False

# Create async engine with conditional SSL
connect_args = {"ssl": use_ssl}

engine = create_async_engine(
    # Remove unsupported psycopg-style sslmode param for asyncpg
    re.sub(r"[?&]sslmode=[^&]*", "", database_url).rstrip("?&"),
    echo=settings.DEBUG,
    future=True,
    connect_args=connect_args,
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
