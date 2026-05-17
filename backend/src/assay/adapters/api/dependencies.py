from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from assay.adapters.auth import JwtError, JwtProvider
from assay.adapters.chain import ChainClient, StubChainClient
from assay.adapters.persistence import Database
from assay.adapters.webhook import HmacVerifier
from assay.config import Settings


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


@lru_cache(maxsize=1)
def _database() -> Database:
    return Database.from_url(settings().database_url)


@lru_cache(maxsize=1)
def _jwt() -> JwtProvider:
    s = settings()
    return JwtProvider(
        secret=s.jwt_secret, algorithm=s.jwt_algorithm, expires_seconds=s.jwt_expires_seconds
    )


@lru_cache(maxsize=1)
def _hmac() -> HmacVerifier:
    return HmacVerifier(settings().vault_secrets())


@lru_cache(maxsize=1)
def _chain() -> ChainClient:
    return StubChainClient(contract_address=settings().certificate_contract_address)


async def db_session() -> AsyncIterator[AsyncSession]:
    db = _database()
    async with db.sessions() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def jwt_provider() -> JwtProvider:
    return _jwt()


def hmac_verifier() -> HmacVerifier:
    return _hmac()


def chain_client() -> ChainClient:
    return _chain()


SessionDep = Annotated[AsyncSession, Depends(db_session)]
JwtDep = Annotated[JwtProvider, Depends(jwt_provider)]
HmacDep = Annotated[HmacVerifier, Depends(hmac_verifier)]
ChainDep = Annotated[ChainClient, Depends(chain_client)]


def current_user(
    jwt: JwtDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> UUID:
    token = _strip_bearer(authorization)
    try:
        claims = jwt.verify(token)
    except JwtError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return UUID(str(claims["sub"]))


def admin_user(
    jwt: JwtDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> UUID:
    token = _strip_bearer(authorization)
    try:
        claims = jwt.verify(token)
    except JwtError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if not claims.get("admin"):
        raise HTTPException(status_code=403, detail="admin only")
    return UUID(str(claims["sub"]))


CurrentUserId = Annotated[UUID, Depends(current_user)]
AdminUserId = Annotated[UUID, Depends(admin_user)]


def _strip_bearer(header_value: str | None) -> str:
    if not header_value or not header_value.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return header_value[7:].strip()
