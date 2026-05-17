from __future__ import annotations

from decimal import Decimal

import pytest

from assay.domain import (
    EmailAddress,
    HmacNonce,
    InvalidMoney,
    IpfsHash,
    Money,
    TokenId,
    TxHash,
)


class TestMoney:
    def test_zero_is_zero(self) -> None:
        assert Money.zero().is_zero()
        assert Money.zero().amount == Decimal(0)

    def test_from_str_rounds_to_6_decimals(self) -> None:
        assert Money.from_str("1.123456789").amount == Decimal("1.123456")
        assert Money.from_str("0.0000001").amount == Decimal("0.000000")

    def test_rejects_negative(self) -> None:
        with pytest.raises(InvalidMoney):
            Money(Decimal("-0.000001"))

    def test_rejects_nan_and_infinity(self) -> None:
        with pytest.raises(InvalidMoney):
            Money(Decimal("NaN"))
        with pytest.raises(InvalidMoney):
            Money(Decimal("Infinity"))

    def test_rejects_precision_beyond_6_decimals(self) -> None:
        with pytest.raises(InvalidMoney):
            Money(Decimal("0.0000001"))

    def test_rejects_non_decimal_type(self) -> None:
        with pytest.raises(InvalidMoney):
            Money(1.5)  # type: ignore[arg-type]

    def test_add(self) -> None:
        result = Money(Decimal("1.5")) + Money(Decimal("2.25"))
        assert result.amount == Decimal("3.75")

    def test_sub(self) -> None:
        result = Money(Decimal("5.0")) - Money(Decimal("2.0"))
        assert result.amount == Decimal("3.0")

    def test_sub_going_negative_raises(self) -> None:
        with pytest.raises(InvalidMoney):
            Money(Decimal("1.0")) - Money(Decimal("2.0"))

    def test_comparison(self) -> None:
        a, b = Money(Decimal("1.0")), Money(Decimal("2.0"))
        assert a < b
        assert b > a
        assert a <= a
        assert a == Money(Decimal("1.0"))

    def test_str_formats_with_6_decimals(self) -> None:
        assert str(Money(Decimal("1.5"))) == "1.500000"

    def test_immutable(self) -> None:
        m = Money(Decimal("1.0"))
        with pytest.raises((AttributeError, TypeError)):
            m.amount = Decimal("2.0")  # type: ignore[misc]


class TestEmailAddress:
    def test_valid(self) -> None:
        EmailAddress("alice@example.com")
        EmailAddress("a.b+c@sub.example.co.uk")

    @pytest.mark.parametrize(
        "bad",
        ["no-at-sign.com", "@example.com", "alice@", "alice@nodot"],
    )
    def test_rejects_invalid(self, bad: str) -> None:
        with pytest.raises(ValueError):
            EmailAddress(bad)


class TestIpfsHash:
    def test_valid_cidv0(self) -> None:
        h = IpfsHash("QmTestHashAa")
        assert h.to_uri() == "ipfs://QmTestHashAa"

    def test_valid_cidv1(self) -> None:
        IpfsHash("bafkreigtestcidvonehash")

    @pytest.mark.parametrize("bad", ["", "Qm", "xyz", "X1234"])
    def test_rejects_invalid(self, bad: str) -> None:
        with pytest.raises(ValueError):
            IpfsHash(bad)


class TestTokenId:
    def test_zero_allowed(self) -> None:
        assert TokenId(0).value == 0

    def test_max_uint256_allowed(self) -> None:
        TokenId(2**256 - 1)

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValueError):
            TokenId(-1)

    def test_rejects_overflow(self) -> None:
        with pytest.raises(ValueError):
            TokenId(2**256)

    def test_ordered(self) -> None:
        assert TokenId(1) < TokenId(2)


class TestHmacNonce:
    def test_valid(self) -> None:
        HmacNonce("a" * 16)
        HmacNonce("b" * 128)

    def test_rejects_too_short(self) -> None:
        with pytest.raises(ValueError):
            HmacNonce("a" * 15)

    def test_rejects_too_long(self) -> None:
        with pytest.raises(ValueError):
            HmacNonce("a" * 129)


class TestTxHash:
    def test_valid(self) -> None:
        TxHash("0x" + "ab" * 32)

    def test_rejects_missing_prefix(self) -> None:
        with pytest.raises(ValueError):
            TxHash("ab" * 32)

    def test_rejects_wrong_length(self) -> None:
        with pytest.raises(ValueError):
            TxHash("0xabcd")

    def test_rejects_non_hex(self) -> None:
        with pytest.raises(ValueError):
            TxHash("0x" + "zz" * 32)
