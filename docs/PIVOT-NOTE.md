# Pivot Note — 2026-05-11

## What changed

The active project direction pivoted from an autonomous DeFi trading agent (codename **Whale-Sense**) to a regulated-grade RWA fintech reference architecture (codename **Assay**).

## Why

The first direction was scoped against a guess about the target reader's space (DeFi / DeFAI). Better signal subsequently established that the target reader operates in a different category — **digital-banking-meets-asset-tokenisation**, where the open engineering work is a financial-grade ledger backend with on-chain certificates of authenticity, vault custody integration, and audit-trail compliance.

DeFAI signals (multi-agent reasoning, ERC-4337 spending caps, sentiment fusion, autonomous execution) have effectively zero overlap with what an RWA fintech needs to ship in its first six months. The right wedge is regulated-grade backend depth plus the smart-contract layer that anchors the certification model — not autonomous trading.

## What carries over

- The structured selection process (`/brainstorm` → `/moat-check` → `/prfaq`) — applied to the original direction and is retained as evidence of how decisions get made here
- The Base testnet choice — agent-native L2 mattered for the original direction, but Base also has the strongest tooling story for the new direction (Coinbase Developer Platform, AgentKit-compatible smart wallet primitives, Basescan verification, mature faucets)
- The Anthropic API + Python primary backend stack
- Hexagonal architecture as the backend pattern of choice
- The five-minute reviewer-experience design principle

## What was retired

- Multi-step LangGraph agent state machine
- Farcaster sentiment ingestion (and the X-API pricing research that led to that pivot)
- ERC-4337 account abstraction + daily spending caps
- 30-day backtest replay mode

All of these are reusable patterns; none of them serve the current target reader.

## What was newly added

- Double-entry event-sourced ledger as the backend backbone
- ERC-721 certificate-of-authenticity contract with a vault-attestation transfer gate
- Escrow lifecycle state machine (FundsLocked → VaultAttested → Released)
- HMAC-protected vault webhook + replay-protection nonce
- Signed audit-trail export endpoint
- Admin dashboard built around audit visibility, not trade visualisation

## What the user is doing differently this time

Reading the target reader's published material _before_ scoping the project, rather than guessing the space from second-hand signal. The new direction maps to specific, observable gaps in the target reader's current product surface — not to a fashionable narrative.

## Decision artefacts

- Original direction artefacts: [`docs/archive/`](./archive/)
- Active spec: [`docs/PRD-ASSAY.md`](./PRD-ASSAY.md)
- Active root: [`../README.md`](../README.md)
