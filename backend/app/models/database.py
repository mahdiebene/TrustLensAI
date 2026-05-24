"""Database connection and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import get_settings

# Engine will be created on first use
_engine = None
_session_factory = None


def get_engine():
    """Get or create async database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.APP_ENV == "development",
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_factory():
    """Get or create async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncSession:
    """Dependency for FastAPI — yields a database session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
