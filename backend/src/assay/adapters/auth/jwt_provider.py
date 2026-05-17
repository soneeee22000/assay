from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt

MIN_JWT_SECRET_LENGTH = 16


class JwtError(Exception):
    """Failure to issue or verify a JWT."""


@dataclass(slots=True, frozen=True)
class AuthToken:
    access_token: str
    expires_in: int
    token_type: str = "bearer"  # noqa: S105 — OAuth2 token_type, not a secret


class JwtProvider:
    """HMAC-signed JWTs. Stub auth per ADR-004 — swap to Clerk/Auth0 by replacing this class."""

    def __init__(
        self, *, secret: str, algorithm: str = "HS256", expires_seconds: int = 3600
    ) -> None:
        if len(secret) < MIN_JWT_SECRET_LENGTH:
            raise JwtError(f"jwt secret must be at least {MIN_JWT_SECRET_LENGTH} characters")
        self._secret = secret
        self._algorithm = algorithm
        self._expires_seconds = expires_seconds

    def issue(self, *, user_id: UUID, is_admin: bool = False) -> AuthToken:
        now = datetime.now(UTC)
        claims: dict[str, Any] = {
            "sub": str(user_id),
            "admin": is_admin,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self._expires_seconds)).timestamp()),
        }
        encoded = jwt.encode(claims, self._secret, algorithm=self._algorithm)
        return AuthToken(access_token=encoded, expires_in=self._expires_seconds)

    def verify(self, token: str) -> dict[str, Any]:
        try:
            decoded: dict[str, Any] = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError as exc:
            raise JwtError(f"invalid token: {exc}") from exc
        return decoded
