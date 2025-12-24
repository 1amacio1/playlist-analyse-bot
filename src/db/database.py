from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import logging
from src.config.settings import config

logger = logging.getLogger(__name__)

def get_database_url() -> str:
    return (
        f"postgresql+asyncpg://{config.DB_USERNAME}:{config.DB_PASSWORD}"
        f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    )

engine = create_async_engine(
    get_database_url(),
    echo=False,
    poolclass=NullPool,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    from src.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")

async def close_db():
    await engine.dispose()
    logger.info("Database connections closed")

