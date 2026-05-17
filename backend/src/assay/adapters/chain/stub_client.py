from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, frozen=True)
class MintResult:
    token_id: int
    tx_hash: str
    contract_address: str


class ChainClient(Protocol):
    """Port for the chain interactions the application needs.

    A real Base/EVM client implementation lives in `base_client.py` (deferred to
    Sprint 6). The stub below produces deterministic-ish fake results good
    enough for end-to-end demos and CI.
    """

    async def mint_certificate(
        self, *, owner_wallet: str, ipfs_hash: str, idempotency_key: str
    ) -> MintResult: ...

    async def attest_vault(self, *, token_id: int, vault_ref: str) -> str:  # tx hash
        ...


class StubChainClient:
    """In-memory chain stub. Used in dev + CI until the real Base client lands."""

    def __init__(self, *, contract_address: str) -> None:
        self._contract = contract_address
        self._next_token_id = 1
        self._minted: dict[int, str] = {}
        self._attested: set[int] = set()

    async def mint_certificate(
        self, *, owner_wallet: str, ipfs_hash: str, idempotency_key: str
    ) -> MintResult:
        token_id = self._next_token_id
        self._next_token_id += 1
        digest = hashlib.sha256(
            f"{owner_wallet}|{ipfs_hash}|{idempotency_key}|{secrets.token_hex(8)}".encode()
        ).hexdigest()
        tx_hash = "0x" + digest
        self._minted[token_id] = tx_hash
        return MintResult(token_id=token_id, tx_hash=tx_hash, contract_address=self._contract)

    async def attest_vault(self, *, token_id: int, vault_ref: str) -> str:
        if token_id not in self._minted:
            raise ValueError(f"token {token_id} has not been minted")
        self._attested.add(token_id)
        digest = hashlib.sha256(f"attest|{token_id}|{vault_ref}".encode()).hexdigest()
        return "0x" + digest
