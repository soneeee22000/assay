from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .value_objects import IpfsHash, TokenId, TxHash


@dataclass(slots=True)
class Certificate:
    """On-chain certificate of authenticity for a physical asset.

    A certificate maps 1:1 to an Asset and to an ERC-721 token on the
    configured Base contract. `tx_hash` is the mint transaction; the platform
    treats on-chain status as the source of truth and projects it here.
    """

    certificate_id: UUID
    asset_id: UUID
    owner_user_id: UUID
    token_id: TokenId
    contract_address: str
    tx_hash: TxHash
    ipfs_metadata_hash: IpfsHash
    minted_at: datetime

    def transfer_ownership(self, new_owner_id: UUID) -> None:
        self.owner_user_id = new_owner_id
