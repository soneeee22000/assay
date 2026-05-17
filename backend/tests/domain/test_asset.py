from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from assay.domain import Asset, AssetRegistered, IpfsHash


class TestAssetRegister:
    def test_happy_path(self) -> None:
        owner = uuid4()
        asset = Asset.register(
            asset_id=uuid4(),
            asset_type="silver-bar",
            lab_cert_number="METALOR-2026-007",
            vault_location="PAR-VAULT-B",
            owner_user_id=owner,
            grade="AA",
            weight_troy_oz=Decimal("2.150"),
            photo_ipfs_hash=IpfsHash("QmAssetPhotoHash"),
        )
        assert asset.asset_type == "silver-bar"
        events = asset.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], AssetRegistered)
        assert events[0].owner_user_id == owner

    @pytest.mark.parametrize(
        "field,value",
        [
            ("asset_type", ""),
            ("asset_type", "   "),
            ("lab_cert_number", ""),
            ("vault_location", ""),
        ],
    )
    def test_rejects_blank_required_field(self, field: str, value: str) -> None:
        kwargs = {
            "asset_id": uuid4(),
            "asset_type": "silver-bar",
            "lab_cert_number": "LBMA-1",
            "vault_location": "ZUR-A",
            "owner_user_id": uuid4(),
        }
        kwargs[field] = value
        with pytest.raises(ValueError):
            Asset.register(**kwargs)  # type: ignore[arg-type]

    def test_rejects_non_positive_weight(self) -> None:
        with pytest.raises(ValueError):
            Asset.register(
                asset_id=uuid4(),
                asset_type="silver-bar",
                lab_cert_number="LBMA-1",
                vault_location="ZUR-A",
                owner_user_id=uuid4(),
                weight_troy_oz=Decimal("0"),
            )


class TestTransferOwnership:
    def test_updates_owner(self, sample_asset: Asset) -> None:
        new_owner = uuid4()
        sample_asset.transfer_ownership(new_owner)
        assert sample_asset.owner_user_id == new_owner
