from collections.abc import AsyncGenerator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_url = settings.sqlalchemy_database_url

_engine_kwargs: dict = {"echo": False}
if _url.startswith("postgresql+asyncpg"):
    # Supabase connections typically go through pgbouncer/Supavisor in
    # transaction mode, which breaks asyncpg's prepared-statement caching
    # (DuplicatePreparedStatementError). Disable both caches and use unique
    # statement names — the documented SQLAlchemy workaround for pgbouncer.
    _engine_kwargs["connect_args"] = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    }

engine = create_async_engine(_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
