# Assay Contracts

Solidity 0.8.28 · Foundry · OpenZeppelin v5

## Quick start

```bash
cd contracts

# install Foundry if needed
curl -L https://foundry.paradigm.xyz | bash && foundryup

# install dependencies
forge install OpenZeppelin/openzeppelin-contracts --no-commit
forge install foundry-rs/forge-std --no-commit

# run tests
forge test -vv

# fuzz + invariant tests
FOUNDRY_PROFILE=ci forge test -vv

# deploy to Base Sepolia (requires env vars from ../backend/.env)
source ../backend/.env
forge script script/Deploy.s.sol --rpc-url $BASE_RPC_URL --broadcast --verify
```

## Layout

```
src/
└── AssayCertificate.sol    ERC-721 cert with vault-attestation transfer gate
script/
└── Deploy.s.sol               Foundry deploy script for Base Sepolia
test/
└── AssayCertificate.t.sol  Unit + invariant tests
```

## Design notes

- `MINTER_ROLE` and `ATTESTER_ROLE` are held by the platform admin on the demo deploy. In production they would be split across separate operational accounts or guarded by a multisig.
- `_update` override enforces the vault-attestation gate on every transfer. Mints (transfers from `address(0)`) and burns (to `address(0)`) bypass the gate.
- `Pausable` is included for emergency stop. The pauser role is held by the same admin in the demo.

Decision rationale in [`../docs/adr/decisions.md`](../docs/adr/decisions.md).
