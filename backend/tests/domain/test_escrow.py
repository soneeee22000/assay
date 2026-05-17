from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from assay.domain import (
    Escrow,
    EscrowCancelled,
    EscrowOpened,
    EscrowRefunded,
    EscrowReleased,
    EscrowState,
    FundsLocked,
    InvalidEscrowParticipants,
    InvalidStateTransition,
    IpfsHash,
    Money,
    TokenId,
    TxHash,
    VaultAttested,
)
from assay.domain.events import CertificateMinted


class TestEscrowOpen:
    def test_happy_path(self, buyer_id, seller_id, asset_id, usdc_100) -> None:
        escrow = Escrow.open(
            escrow_id=uuid4(),
            buyer_id=buyer_id,
            seller_id=seller_id,
            asset_id=asset_id,
            amount=usdc_100,
        )
        assert escrow.state == EscrowState.PENDING
        events = escrow.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], EscrowOpened)
        assert events[0].buyer_id == buyer_id
        assert events[0].amount == Decimal("100.000000")

    def test_rejects_self_trade(self, asset_id, usdc_100) -> None:
        same = uuid4()
        with pytest.raises(InvalidEscrowParticipants):
            Escrow.open(
                escrow_id=uuid4(),
                buyer_id=same,
                seller_id=same,
                asset_id=asset_id,
                amount=usdc_100,
            )

    def test_rejects_zero_amount(self, buyer_id, seller_id, asset_id) -> None:
        with pytest.raises(InvalidEscrowParticipants):
            Escrow.open(
                escrow_id=uuid4(),
                buyer_id=buyer_id,
                seller_id=seller_id,
                asset_id=asset_id,
                amount=Money.zero(),
            )


class TestLockFunds:
    def test_pending_transitions_to_funds_locked(self, pending_escrow: Escrow) -> None:
        pending_escrow.lock_funds()
        assert pending_escrow.state == EscrowState.FUNDS_LOCKED
        events = pending_escrow.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], FundsLocked)

    def test_rejects_from_non_pending(self, funds_locked_escrow: Escrow) -> None:
        with pytest.raises(InvalidStateTransition):
            funds_locked_escrow.lock_funds()


class TestRecordVaultAttestation:
    def test_funds_locked_transitions_to_attested(self, funds_locked_escrow: Escrow) -> None:
        attestation_id = uuid4()
        funds_locked_escrow.record_vault_attestation(
            attestation_id=attestation_id,
            payload_hash="payload-hash-xyz",
        )
        assert funds_locked_escrow.state == EscrowState.VAULT_ATTESTED
        events = funds_locked_escrow.pull_events()
        assert isinstance(events[0], VaultAttested)
        assert events[0].attestation_id == attestation_id

    def test_rejects_from_pending(self, pending_escrow: Escrow) -> None:
        with pytest.raises(InvalidStateTransition):
            pending_escrow.record_vault_attestation(attestation_id=uuid4(), payload_hash="x")


class TestRecordCertificateMint:
    def test_attested_transitions_to_minted(self, vault_attested_escrow: Escrow) -> None:
        vault_attested_escrow.record_certificate_mint(
            certificate_id=uuid4(),
            token_id=TokenId(42),
            tx_hash=TxHash("0x" + "ab" * 32),
            ipfs_hash=IpfsHash("QmTestCertMetadataHash"),
        )
        assert vault_attested_escrow.state == EscrowState.CERTIFICATE_MINTED
        events = vault_attested_escrow.pull_events()
        assert isinstance(events[0], CertificateMinted)
        assert events[0].token_id == 42

    def test_rejects_from_funds_locked(self, funds_locked_escrow: Escrow) -> None:
        with pytest.raises(InvalidStateTransition):
            funds_locked_escrow.record_certificate_mint(
                certificate_id=uuid4(),
                token_id=TokenId(1),
                tx_hash=TxHash("0x" + "ab" * 32),
                ipfs_hash=IpfsHash("QmHash"),
            )


class TestRelease:
    def test_minted_transitions_to_released(self, minted_escrow: Escrow) -> None:
        minted_escrow.release()
        assert minted_escrow.state == EscrowState.RELEASED
        events = minted_escrow.pull_events()
        assert isinstance(events[0], EscrowReleased)

    def test_rejects_from_pending(self, pending_escrow: Escrow) -> None:
        with pytest.raises(InvalidStateTransition):
            pending_escrow.release()


class TestCancel:
    def test_pending_transitions_to_cancelled(self, pending_escrow: Escrow) -> None:
        pending_escrow.cancel("user requested")
        assert pending_escrow.state == EscrowState.CANCELLED
        events = pending_escrow.pull_events()
        assert isinstance(events[0], EscrowCancelled)
        assert events[0].reason == "user requested"

    def test_rejects_from_funds_locked(self, funds_locked_escrow: Escrow) -> None:
        with pytest.raises(InvalidStateTransition):
            funds_locked_escrow.cancel("nope")


class TestRefund:
    def test_funds_locked_transitions_to_refunded(self, funds_locked_escrow: Escrow) -> None:
        funds_locked_escrow.refund("vault timeout")
        assert funds_locked_escrow.state == EscrowState.REFUNDED
        events = funds_locked_escrow.pull_events()
        assert isinstance(events[0], EscrowRefunded)
        assert events[0].amount == Decimal("100.000000")

    def test_vault_attested_transitions_to_refunded(self, vault_attested_escrow: Escrow) -> None:
        vault_attested_escrow.refund("vault revoked attestation")
        assert vault_attested_escrow.state == EscrowState.REFUNDED

    def test_rejects_from_pending(self, pending_escrow: Escrow) -> None:
        with pytest.raises(InvalidStateTransition):
            pending_escrow.refund("nope")

    def test_rejects_from_minted(self, minted_escrow: Escrow) -> None:
        with pytest.raises(InvalidStateTransition):
            minted_escrow.refund("nope")


class TestTerminalStates:
    def test_released_is_terminal(self, minted_escrow: Escrow) -> None:
        minted_escrow.release()
        assert minted_escrow.is_terminal()

    def test_cancelled_is_terminal(self, pending_escrow: Escrow) -> None:
        pending_escrow.cancel("x")
        assert pending_escrow.is_terminal()

    def test_refunded_is_terminal(self, funds_locked_escrow: Escrow) -> None:
        funds_locked_escrow.refund("x")
        assert funds_locked_escrow.is_terminal()

    def test_pending_is_not_terminal(self, pending_escrow: Escrow) -> None:
        assert not pending_escrow.is_terminal()


class TestEventDraining:
    def test_pull_events_returns_and_clears(self, pending_escrow: Escrow) -> None:
        pending_escrow.lock_funds()
        first = pending_escrow.pull_events()
        assert len(first) == 1
        second = pending_escrow.pull_events()
        assert second == []
