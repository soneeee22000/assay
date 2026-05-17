from __future__ import annotations


class DomainError(Exception):
    """Root of every error the domain layer can raise."""


class InvalidStateTransition(DomainError):
    """Aggregate refused a transition because it does not apply in its current state."""


class InsufficientBalance(DomainError):
    """Attempted to lock or withdraw more than the user has available."""


class KycNotApproved(DomainError):
    """A KYC-gated operation was attempted by a user who is not approved."""


class InvalidEscrowParticipants(DomainError):
    """Escrow buyer/seller/amount combination is invalid (self-trade, zero amount, etc.)."""


class CertificateAlreadyMinted(DomainError):
    """Attempted to mint a second certificate for an asset that already has one."""


class InvalidMoney(DomainError):
    """A Money construction or arithmetic produced an invalid amount."""
