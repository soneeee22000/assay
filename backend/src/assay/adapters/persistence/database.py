from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Build an async SQLAlchemy engine. Pool sizing is conservative for a single
    Railway dyno; production sizing is configured at deploy time."""
    return create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


def get_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@dataclass(slots=True)
class Database:
    """Convenience handle that owns an engine + sessionmaker and yields sessions.

    Application code asks for a session via `async with db.session() as s:`.
    """

    engine: AsyncEngine
    sessions: async_sessionmaker[AsyncSession]

    @classmethod
    def from_url(cls, database_url: str, *, echo: bool = False) -> Database:
        engine = get_engine(database_url, echo=echo)
        return cls(engine=engine, sessions=get_sessionmaker(engine))

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.sessions() as s:
            yield s
