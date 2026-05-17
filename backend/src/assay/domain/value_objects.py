from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal, InvalidOperation
from typing import Final

from .errors import InvalidMoney

USDC_DECIMAL_PLACES: Final[int] = 6
USDC_QUANTUM: Final[Decimal] = Decimal("0.000001")
TOKEN_ID_MAX: Final[int] = 2**256 - 1
IPFS_CID_MIN_LENGTH: Final[int] = 4
HMAC_NONCE_MIN_LENGTH: Final[int] = 16
HMAC_NONCE_MAX_LENGTH: Final[int] = 128
EVM_TX_HASH_LENGTH: Final[int] = 66


@dataclass(frozen=True, slots=True, order=True)
class Money:
    """Non-negative USDC amount with 6-decimal precision.

    USDC has 6 decimals on-chain. Using Decimal (never float) keeps arithmetic
    exact and matches what the contract sees byte-for-byte.
    """

    amount: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise InvalidMoney(f"Money.amount must be Decimal, got {type(self.amount).__name__}")
        if self.amount.is_nan() or self.amount.is_infinite():
            raise InvalidMoney(f"Money cannot be NaN or infinite: {self.amount}")
        if self.amount < 0:
            raise InvalidMoney(f"Money cannot be negative: {self.amount}")
        if self.amount != self.amount.quantize(USDC_QUANTUM, rounding=ROUND_DOWN):
            raise InvalidMoney(f"Money exceeds USDC precision (6 decimals): {self.amount}")

    @classmethod
    def zero(cls) -> Money:
        return cls(Decimal(0))

    @classmethod
    def from_str(cls, value: str) -> Money:
        try:
            amount = Decimal(value)
        except InvalidOperation as exc:
            raise InvalidMoney(f"Cannot parse Money from {value!r}") from exc
        return cls(amount.quantize(USDC_QUANTUM, rounding=ROUND_DOWN))

    def __add__(self, other: Money) -> Money:
        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        if self.amount < other.amount:
            raise InvalidMoney(
                f"Money subtraction would go negative: {self.amount} - {other.amount}"
            )
        return Money(self.amount - other.amount)

    def is_zero(self) -> bool:
        return self.amount == 0

    def __str__(self) -> str:
        return f"{self.amount:.6f}"


@dataclass(frozen=True, slots=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        if "@" not in self.value:
            raise ValueError(f"Invalid email (no @): {self.value!r}")
        local, _, domain = self.value.rpartition("@")
        if not local or "." not in domain:
            raise ValueError(f"Invalid email shape: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class IpfsHash:
    """An IPFS content identifier. Accepts CIDv0 (`Qm...`) and CIDv1 (`b...`)."""

    value: str

    def __post_init__(self) -> None:
        if len(self.value) < IPFS_CID_MIN_LENGTH:
            raise ValueError(f"IPFS CID too short: {self.value!r}")
        if not (self.value.startswith("Qm") or self.value.startswith("b")):
            raise ValueError(f"Unrecognised IPFS CID prefix: {self.value!r}")

    def to_uri(self) -> str:
        return f"ipfs://{self.value}"


@dataclass(frozen=True, slots=True, order=True)
class TokenId:
    """An ERC-721 token id. Must fit in uint256."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"TokenId must be non-negative: {self.value}")
        if self.value > TOKEN_ID_MAX:
            raise ValueError(f"TokenId exceeds uint256: {self.value}")


@dataclass(frozen=True, slots=True)
class HmacNonce:
    """A nonce supplied by a vault operator for webhook replay protection."""

    value: str

    def __post_init__(self) -> None:
        if len(self.value) < HMAC_NONCE_MIN_LENGTH:
            raise ValueError(
                f"HmacNonce must be at least {HMAC_NONCE_MIN_LENGTH} chars: got {len(self.value)}"
            )
        if len(self.value) > HMAC_NONCE_MAX_LENGTH:
            raise ValueError(
                f"HmacNonce must be at most {HMAC_NONCE_MAX_LENGTH} chars: got {len(self.value)}"
            )


@dataclass(frozen=True, slots=True)
class TxHash:
    """An EVM transaction hash. 0x-prefixed, 32 bytes (66 chars including 0x)."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.startswith("0x"):
            raise ValueError(f"TxHash must start with 0x: {self.value!r}")
        if len(self.value) != EVM_TX_HASH_LENGTH:
            raise ValueError(f"TxHash must be {EVM_TX_HASH_LENGTH} chars: got {len(self.value)}")
        try:
            int(self.value, 16)
        except ValueError as exc:
            raise ValueError(f"TxHash is not valid hex: {self.value!r}") from exc
