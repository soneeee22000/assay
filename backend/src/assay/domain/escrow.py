from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

from .errors import InvalidEscrowParticipants, InvalidStateTransition
from .events import (
    CertificateMinted,
    DomainEvent,
    EscrowCancelled,
    EscrowOpened,
    EscrowRefunded,
    EscrowReleased,
    FundsLocked,
    VaultAttested,
)
from .value_objects import IpfsHash, Money, TokenId, TxHash


class EscrowState(StrEnum):
    PENDING = "PENDING"
    FUNDS_LOCKED = "FUNDS_LOCKED"
    VAULT_ATTESTED = "VAULT_ATTESTED"
    CERTIFICATE_MINTED = "CERTIFICATE_MINTED"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


_TERMINAL_STATES = frozenset({EscrowState.RELEASED, EscrowState.CANCELLED, EscrowState.REFUNDED})


@dataclass(slots=True)
class Escrow:
    """Escrow aggregate. Owns the lifecycle from PENDING through RELEASED.

    Every state transition emits a domain event. State is a projection of
    the event stream — never mutated outside a transition method.
    """

    escrow_id: UUID
    buyer_id: UUID
    seller_id: UUID
    asset_id: UUID
    amount: Money
    state: EscrowState
    _uncommitted: list[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def open(
        cls,
        *,
        escrow_id: UUID,
        buyer_id: UUID,
        seller_id: UUID,
        asset_id: UUID,
        amount: Money,
    ) -> Escrow:
        if buyer_id == seller_id:
            raise InvalidEscrowParticipants("buyer and seller must differ")
        if amount.is_zero():
            raise InvalidEscrowParticipants("escrow amount must be > 0")

        escrow = cls(
            escrow_id=escrow_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            asset_id=asset_id,
            amount=amount,
            state=EscrowState.PENDING,
        )
        escrow._record(
            EscrowOpened(
                escrow_id=escrow_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                asset_id=asset_id,
                amount=amount.amount,
            )
        )
        return escrow

    def lock_funds(self) -> None:
        self._require_state(EscrowState.PENDING)
        self.state = EscrowState.FUNDS_LOCKED
        self._record(FundsLocked(escrow_id=self.escrow_id))

    def record_vault_attestation(self, *, attestation_id: UUID, payload_hash: str) -> None:
        self._require_state(EscrowState.FUNDS_LOCKED)
        self.state = EscrowState.VAULT_ATTESTED
        self._record(
            VaultAttested(
                escrow_id=self.escrow_id,
                attestation_id=attestation_id,
                payload_hash=payload_hash,
            )
        )

    def record_certificate_mint(
        self,
        *,
        certificate_id: UUID,
        token_id: TokenId,
        tx_hash: TxHash,
        ipfs_hash: IpfsHash,
    ) -> None:
        self._require_state(EscrowState.VAULT_ATTESTED)
        self.state = EscrowState.CERTIFICATE_MINTED
        self._record(
            CertificateMinted(
                escrow_id=self.escrow_id,
                certificate_id=certificate_id,
                token_id=token_id.value,
                tx_hash=tx_hash.value,
                ipfs_hash=ipfs_hash.value,
            )
        )

    def release(self) -> None:
        self._require_state(EscrowState.CERTIFICATE_MINTED)
        self.state = EscrowState.RELEASED
        self._record(EscrowReleased(escrow_id=self.escrow_id))

    def cancel(self, reason: str) -> None:
        if self.state != EscrowState.PENDING:
            raise InvalidStateTransition(f"cancel requires PENDING, got {self.state}")
        self.state = EscrowState.CANCELLED
        self._record(EscrowCancelled(escrow_id=self.escrow_id, reason=reason))

    def refund(self, reason: str) -> None:
        refundable = {EscrowState.FUNDS_LOCKED, EscrowState.VAULT_ATTESTED}
        if self.state not in refundable:
            raise InvalidStateTransition(
                f"refund requires one of {sorted(s.value for s in refundable)}, got {self.state}"
            )
        self.state = EscrowState.REFUNDED
        self._record(
            EscrowRefunded(escrow_id=self.escrow_id, amount=self.amount.amount, reason=reason)
        )

    def is_terminal(self) -> bool:
        return self.state in _TERMINAL_STATES

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._uncommitted)
        self._uncommitted.clear()
        return events

    def _require_state(self, expected: EscrowState) -> None:
        if self.state != expected:
            raise InvalidStateTransition(f"required state {expected.value}, got {self.state.value}")

    def _record(self, event: DomainEvent) -> None:
        self._uncommitted.append(event)
