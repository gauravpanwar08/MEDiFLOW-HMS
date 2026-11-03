from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

def get_engine(url: str):
    kwargs = {"echo": settings.DEBUG}
    if not url.startswith("sqlite"):
        kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        })
    return create_async_engine(url, **kwargs)


engine = get_engine(settings.DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession,
    expire_on_commit=False, autoflush=False, autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
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
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        if "postgresql" in settings.DATABASE_URL:
            import structlog
            logger = structlog.get_logger()
            fallback_url = "sqlite+aiosqlite:///./hms.db"
            logger.warning(
                "PostgreSQL unreachable. Falling back to local SQLite database.",
                configured_url=settings.DATABASE_URL,
                fallback_url=fallback_url,
                error=str(exc),
            )
            engine = get_engine(fallback_url)
            AsyncSessionLocal.configure(bind=engine)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            raise
