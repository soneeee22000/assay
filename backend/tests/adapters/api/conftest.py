from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any

# Test env must be set before importing the app so Settings() picks it up.
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-16-chars-long-1234567890")
os.environ.setdefault("VAULT_HMAC_SECRETS", "vault-test:supersecret-vault-key")
os.environ.setdefault("CERTIFICATE_CONTRACT_ADDRESS", "0xDEADBEEF" + "00" * 17)

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncEngine  # noqa: E402

from assay.adapters.api.dependencies import _database, db_session, settings  # noqa: E402
from assay.adapters.persistence import get_sessionmaker  # noqa: E402
from assay.main import app  # noqa: E402
from tests.conftest import truncate_all  # noqa: E402


@pytest_asyncio.fixture
async def client(engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """Per-test app client wired to the testcontainer Postgres engine.

    The dependency overrides last only for the lifetime of the fixture; the
    `lru_cache`-d singletons are cleared so a fresh `Settings`/`Database` is
    built whenever the suite mutates env state. The DB is truncated after the
    test so each API test starts from a clean slate.
    """
    _database.cache_clear()
    settings.cache_clear()

    test_sessions = get_sessionmaker(engine)

    async def _override_session() -> AsyncIterator[Any]:
        async with test_sessions() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[db_session] = _override_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        await truncate_all(engine)
