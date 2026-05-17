from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from .events import AssetRegistered, DomainEvent
from .value_objects import IpfsHash


@dataclass(slots=True)
class Asset:
    """A physical asset under vault custody (allocated bullion, in the worked example).

    Identity is `asset_id`. `lab_cert_number` is the off-chain ground-truth
    reference — the assay certificate number from an LBMA-accredited assayer
    (Metalor / PAMP / Valcambi / Argor-Heraeus etc). Global uniqueness is
    enforced at the persistence layer, not here.
    """

    asset_id: UUID
    asset_type: str
    lab_cert_number: str
    vault_location: str
    owner_user_id: UUID
    grade: str | None = None
    weight_troy_oz: Decimal | None = None
    photo_ipfs_hash: IpfsHash | None = None
    _uncommitted: list[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def register(  # noqa: PLR0913
        cls,
        *,
        asset_id: UUID,
        asset_type: str,
        lab_cert_number: str,
        vault_location: str,
        owner_user_id: UUID,
        grade: str | None = None,
        weight_troy_oz: Decimal | None = None,
        photo_ipfs_hash: IpfsHash | None = None,
    ) -> Asset:
        if not asset_type.strip():
            raise ValueError("asset_type must not be blank")
        if not lab_cert_number.strip():
            raise ValueError("lab_cert_number must not be blank")
        if not vault_location.strip():
            raise ValueError("vault_location must not be blank")
        if weight_troy_oz is not None and weight_troy_oz <= 0:
            raise ValueError(f"weight_troy_oz must be positive: {weight_troy_oz}")

        asset = cls(
            asset_id=asset_id,
            asset_type=asset_type,
            lab_cert_number=lab_cert_number,
            vault_location=vault_location,
            owner_user_id=owner_user_id,
            grade=grade,
            weight_troy_oz=weight_troy_oz,
            photo_ipfs_hash=photo_ipfs_hash,
        )
        asset._uncommitted.append(
            AssetRegistered(
                asset_id=asset_id,
                asset_type=asset_type,
                lab_cert_number=lab_cert_number,
                vault_location=vault_location,
                owner_user_id=owner_user_id,
            )
        )
        return asset

    def transfer_ownership(self, new_owner_id: UUID) -> None:
        self.owner_user_id = new_owner_id

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._uncommitted)
        self._uncommitted.clear()
        return events
