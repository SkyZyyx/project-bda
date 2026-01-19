# ==============================================================================
# DATABASE CONNECTION MODULE
# ==============================================================================
# This module sets up the async database connection using SQLAlchemy 2.0.
# We use async for better performance with concurrent requests.
# ==============================================================================

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.core.config import get_settings

# Get our settings
settings = get_settings()

# Create the async engine
# The engine is the starting point for any SQLAlchemy application.
# It's a "home base" for the actual database and its connection pool.
# Configure engine arguments based on database type
engine_args = {
    "echo": settings.debug,
    "pool_pre_ping": True,
}

# SQLite doesn't support pool_size/max_overflow with NullPool (default)
if "sqlite" not in settings.database_url:
    engine_args["pool_size"] = 5
    engine_args["max_overflow"] = 10

engine = create_async_engine(
    settings.database_url,
    **engine_args
)

# Create a session factory
# Sessions are how we interact with the database.
# We use async_sessionmaker to create async sessions.
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit (common pattern)
    autocommit=False,
    autoflush=False,
)


# Base class for all our ORM models
# All models will inherit from this class
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    
    By inheriting from DeclarativeBase, we get:
    - Automatic table creation from class definitions
    - Relationship handling
    - Type annotations support
    """
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    This is used with FastAPI's dependency injection system.
    Each request gets its own session, and the session is
    automatically closed when the request is done.
    
    Usage in a route:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            # Use db here
            pass
    
    Yields:
        AsyncSession: A database session for the current request
    """
    async with async_session_maker() as session:
        try:
            yield session
            # If no exceptions, commit any pending changes
            await session.commit()
        except Exception:
            # If there was an error, rollback any changes
            await session.rollback()
            raise
        finally:
            # Always close the session
            await session.close()


async def init_db():
    """
    Initialize the database by creating all tables.
    
    Note: In production, you'd use Alembic migrations instead.
    This is mainly for development/testing.
    """
    async with engine.begin() as conn:
        # This creates all tables defined by models that inherit from Base
        await conn.run_sync(Base.metadata.create_all)
