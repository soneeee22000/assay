from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

from .errors import InsufficientBalance, KycNotApproved
from .events import (
    DomainEvent,
    FundsDeposited,
    FundsWithdrawn,
    KycApproved,
    KycRejected,
    UserRegistered,
)
from .value_objects import EmailAddress, Money, TxHash


class KycStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(slots=True)
class User:
    """User aggregate. Owns KYC status and the two-bucket balance (available, locked).

    Locked balance moves out of available when an escrow is opened against the
    user as buyer; it returns to available on refund, or transfers to the seller
    on release. The aggregate guards the invariant available >= 0, locked >= 0
    via the Money value object.
    """

    user_id: UUID
    email: EmailAddress
    kyc_status: KycStatus
    available_balance: Money
    locked_balance: Money
    wallet_address: str | None = None
    _uncommitted: list[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def register(
        cls, *, user_id: UUID, email: EmailAddress, wallet_address: str | None = None
    ) -> User:
        user = cls(
            user_id=user_id,
            email=email,
            kyc_status=KycStatus.PENDING,
            available_balance=Money.zero(),
            locked_balance=Money.zero(),
            wallet_address=wallet_address,
        )
        user._record(UserRegistered(user_id=user_id, email=email.value))
        return user

    def approve_kyc(self) -> None:
        if self.kyc_status == KycStatus.APPROVED:
            return
        self.kyc_status = KycStatus.APPROVED
        self._record(KycApproved(user_id=self.user_id))

    def reject_kyc(self, reason: str) -> None:
        self.kyc_status = KycStatus.REJECTED
        self._record(KycRejected(user_id=self.user_id, reason=reason))

    def deposit(self, amount: Money, tx_hash: TxHash) -> None:
        self._require_kyc()
        if amount.is_zero():
            raise InsufficientBalance("deposit must be positive")
        self.available_balance = self.available_balance + amount
        self._record(
            FundsDeposited(user_id=self.user_id, amount=amount.amount, tx_hash=tx_hash.value)
        )

    def lock_funds(self, amount: Money) -> None:
        self._require_kyc()
        if self.available_balance < amount:
            raise InsufficientBalance(f"available {self.available_balance} < required {amount}")
        self.available_balance = self.available_balance - amount
        self.locked_balance = self.locked_balance + amount

    def release_locked(self, amount: Money) -> None:
        if self.locked_balance < amount:
            raise InsufficientBalance(f"locked {self.locked_balance} < release {amount}")
        self.locked_balance = self.locked_balance - amount

    def credit(self, amount: Money) -> None:
        self.available_balance = self.available_balance + amount

    def refund_locked(self, amount: Money) -> None:
        if self.locked_balance < amount:
            raise InsufficientBalance(f"locked {self.locked_balance} < refund {amount}")
        self.locked_balance = self.locked_balance - amount
        self.available_balance = self.available_balance + amount

    def withdraw(self, amount: Money, tx_hash: TxHash) -> None:
        self._require_kyc()
        if self.available_balance < amount:
            raise InsufficientBalance(f"available {self.available_balance} < withdraw {amount}")
        self.available_balance = self.available_balance - amount
        self._record(
            FundsWithdrawn(user_id=self.user_id, amount=amount.amount, tx_hash=tx_hash.value)
        )

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._uncommitted)
        self._uncommitted.clear()
        return events

    def _require_kyc(self) -> None:
        if self.kyc_status != KycStatus.APPROVED:
            raise KycNotApproved(f"user {self.user_id} kyc_status={self.kyc_status.value}")

    def _record(self, event: DomainEvent) -> None:
        self._uncommitted.append(event)
