from __future__ import annotations

import binascii
import hashlib
import hmac
from base64 import b64decode, b64encode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..persistence.models import VaultAttestationRow


class InvalidSignatureError(Exception):
    """The HMAC in the request header does not match the body."""


class ReplayedNonceError(Exception):
    """The (operator_id, nonce) pair has already been seen."""


class HmacVerifier:
    """Verifies HMAC-SHA256 signatures on vault webhook payloads.

    Signature scheme: `base64(HMAC_SHA256(secret, raw_body))`. The shared secret
    per operator id is loaded from configuration. Replay protection is enforced
    via a DB unique constraint on `(operator_id, nonce)`.
    """

    def __init__(self, secrets_by_operator: dict[str, str]) -> None:
        self._secrets = secrets_by_operator

    def sign(self, *, operator_id: str, body: bytes) -> str:
        secret = self._require_secret(operator_id)
        mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
        return b64encode(mac).decode("ascii")

    def verify(self, *, operator_id: str, body: bytes, signature_b64: str) -> None:
        secret = self._require_secret(operator_id)
        try:
            received = b64decode(signature_b64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise InvalidSignatureError(f"signature not base64: {exc}") from exc
        expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
        if not hmac.compare_digest(received, expected):
            raise InvalidSignatureError("HMAC mismatch")

    def _require_secret(self, operator_id: str) -> str:
        secret = self._secrets.get(operator_id)
        if not secret:
            raise InvalidSignatureError(f"unknown operator: {operator_id}")
        return secret


class NonceCache:
    """Pre-check whether a nonce has already been used for this operator.

    Authoritative check happens at insert time via the DB unique constraint;
    this lets handlers fail fast before doing extra work."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_seen(self, *, operator_id: str, nonce: str) -> bool:
        stmt = (
            select(VaultAttestationRow.attestation_id)
            .where(
                VaultAttestationRow.vault_operator_id == operator_id,
                VaultAttestationRow.nonce == nonce,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
