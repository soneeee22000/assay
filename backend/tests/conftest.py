from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from assay.adapters.persistence import Base, get_sessionmaker

try:
    from testcontainers.postgres import PostgresContainer
except Exception:  # pragma: no cover - import error implies skip
    PostgresContainer = None  # type: ignore[assignment, misc]


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[object]:
    """Spin up a Postgres container for the session. Skips cleanly if Docker is unreachable."""
    if PostgresContainer is None:
        pytest.skip("testcontainers not importable")
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except Exception as exc:
        pytest.skip(f"docker unavailable for integration tests: {exc}")
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def database_url(postgres_container: object) -> str:
    raw_url: str = postgres_container.get_connection_url()  # type: ignore[attr-defined]
    return raw_url.replace("postgresql+psycopg2", "postgresql+asyncpg").replace(
        "postgresql://", "postgresql+asyncpg://"
    )


@pytest.fixture(scope="session")
def schema_ready(database_url: str) -> bool:
    """Create the schema once per session via a sync psycopg connection.

    Doing this once-per-session via a *non-async* path avoids the pytest-asyncio
    cross-loop pain entirely. The async engine each test builds afterwards just
    connects to a DB that already has its schema.
    """

    async def _create() -> None:
        engine = create_async_engine(database_url)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        finally:
            await engine.dispose()

    asyncio.run(_create())
    return True


@pytest_asyncio.fixture
async def engine(database_url: str, schema_ready: bool) -> AsyncIterator[AsyncEngine]:  # noqa: ARG001
    eng = create_async_engine(database_url)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def sessions(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return get_sessionmaker(engine)


async def truncate_all(engine: AsyncEngine) -> None:
    tables = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
