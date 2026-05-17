from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from assay.domain import (
    EmailAddress,
    FundsDeposited,
    FundsWithdrawn,
    InsufficientBalance,
    KycApproved,
    KycNotApproved,
    KycRejected,
    KycStatus,
    Money,
    TxHash,
    User,
    UserRegistered,
)

VALID_TX = TxHash("0x" + "ab" * 32)


def _make_user() -> User:
    return User.register(user_id=uuid4(), email=EmailAddress("alice@example.com"))


class TestRegister:
    def test_creates_pending_user_with_zero_balances(self) -> None:
        user = _make_user()
        assert user.kyc_status == KycStatus.PENDING
        assert user.available_balance.is_zero()
        assert user.locked_balance.is_zero()
        events = user.pull_events()
        assert isinstance(events[0], UserRegistered)


class TestKyc:
    def test_approve_pending(self) -> None:
        user = _make_user()
        user.pull_events()
        user.approve_kyc()
        assert user.kyc_status == KycStatus.APPROVED
        events = user.pull_events()
        assert isinstance(events[0], KycApproved)

    def test_approve_is_idempotent(self) -> None:
        user = _make_user()
        user.approve_kyc()
        user.pull_events()
        user.approve_kyc()
        assert user.pull_events() == []

    def test_reject_records_reason(self) -> None:
        user = _make_user()
        user.pull_events()
        user.reject_kyc("docs invalid")
        events = user.pull_events()
        assert isinstance(events[0], KycRejected)
        assert events[0].reason == "docs invalid"


class TestDeposit:
    def test_requires_kyc(self) -> None:
        user = _make_user()
        with pytest.raises(KycNotApproved):
            user.deposit(Money(Decimal("10.0")), VALID_TX)

    def test_increments_available_balance(self, kyc_approved_user: User) -> None:
        kyc_approved_user.deposit(Money(Decimal("25.0")), VALID_TX)
        assert kyc_approved_user.available_balance.amount == Decimal("25.0")
        events = kyc_approved_user.pull_events()
        assert isinstance(events[0], FundsDeposited)

    def test_rejects_zero(self, kyc_approved_user: User) -> None:
        with pytest.raises(InsufficientBalance):
            kyc_approved_user.deposit(Money.zero(), VALID_TX)


class TestLockFunds:
    def test_moves_available_to_locked(self, kyc_approved_user: User) -> None:
        kyc_approved_user.deposit(Money(Decimal("100.0")), VALID_TX)
        kyc_approved_user.lock_funds(Money(Decimal("40.0")))
        assert kyc_approved_user.available_balance.amount == Decimal("60.0")
        assert kyc_approved_user.locked_balance.amount == Decimal("40.0")

    def test_requires_kyc(self) -> None:
        user = _make_user()
        with pytest.raises(KycNotApproved):
            user.lock_funds(Money(Decimal("10.0")))

    def test_rejects_insufficient(self, kyc_approved_user: User) -> None:
        with pytest.raises(InsufficientBalance):
            kyc_approved_user.lock_funds(Money(Decimal("1.0")))


class TestReleaseLocked:
    def test_decrements_locked(self, kyc_approved_user: User) -> None:
        kyc_approved_user.deposit(Money(Decimal("50.0")), VALID_TX)
        kyc_approved_user.lock_funds(Money(Decimal("50.0")))
        kyc_approved_user.release_locked(Money(Decimal("50.0")))
        assert kyc_approved_user.locked_balance.is_zero()

    def test_rejects_insufficient_locked(self, kyc_approved_user: User) -> None:
        with pytest.raises(InsufficientBalance):
            kyc_approved_user.release_locked(Money(Decimal("1.0")))


class TestCredit:
    def test_increments_available_with_no_kyc_gate(self) -> None:
        user = _make_user()
        user.credit(Money(Decimal("99.0")))
        assert user.available_balance.amount == Decimal("99.0")


class TestRefundLocked:
    def test_moves_locked_back_to_available(self, kyc_approved_user: User) -> None:
        kyc_approved_user.deposit(Money(Decimal("80.0")), VALID_TX)
        kyc_approved_user.lock_funds(Money(Decimal("30.0")))
        kyc_approved_user.refund_locked(Money(Decimal("30.0")))
        assert kyc_approved_user.locked_balance.is_zero()
        assert kyc_approved_user.available_balance.amount == Decimal("80.0")

    def test_rejects_more_than_locked(self, kyc_approved_user: User) -> None:
        with pytest.raises(InsufficientBalance):
            kyc_approved_user.refund_locked(Money(Decimal("1.0")))


class TestWithdraw:
    def test_decrements_available(self, kyc_approved_user: User) -> None:
        kyc_approved_user.deposit(Money(Decimal("70.0")), VALID_TX)
        kyc_approved_user.pull_events()
        kyc_approved_user.withdraw(Money(Decimal("20.0")), VALID_TX)
        assert kyc_approved_user.available_balance.amount == Decimal("50.0")
        events = kyc_approved_user.pull_events()
        assert isinstance(events[0], FundsWithdrawn)

    def test_requires_kyc(self) -> None:
        user = _make_user()
        with pytest.raises(KycNotApproved):
            user.withdraw(Money(Decimal("1.0")), VALID_TX)

    def test_rejects_insufficient(self, kyc_approved_user: User) -> None:
        with pytest.raises(InsufficientBalance):
            kyc_approved_user.withdraw(Money(Decimal("1.0")), VALID_TX)


class TestEventDraining:
    def test_pull_events_clears(self) -> None:
        user = _make_user()
        first = user.pull_events()
        assert len(first) == 1
        assert user.pull_events() == []
