# Deploy Guide

End-to-end recipe to take GemVault from local to a live demo URL.

## 1. Smart contract (Base Sepolia)

Use the `Deploy Contract` GitHub Action (manual dispatch) so we don't need
Foundry on the dev box. Add three repository secrets first:

| Secret              | Value                                                       |
| ------------------- | ----------------------------------------------------------- |
| `BASE_RPC_URL`      | Alchemy / CDP Base Sepolia RPC URL                          |
| `ADMIN_PRIVATE_KEY` | 0x-prefixed private key for the deployer EOA (Base Sepolia) |
| `BASESCAN_API_KEY`  | Basescan v2 API key for source verification                 |

Fund the deployer with Base Sepolia ETH from
<https://portal.cdp.coinbase.com/products/faucet> (0.05–0.1 ETH/day is plenty).

Trigger the action:

```bash
gh workflow run deploy-contract.yml
```

The workflow runs `forge script Deploy --broadcast --verify` and prints the
contract address in its log. Copy it.

## 2. Backend (Railway)

```bash
cd backend
railway login
railway init                    # creates a Railway project
railway add --plugin postgresql # attaches a managed Postgres
railway up                       # builds + deploys via the Dockerfile
```

Set env vars in the Railway dashboard (Settings → Variables):

| Variable                       | Value                                                                                         |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| `DATABASE_URL`                 | Auto-populated by the Postgres plugin (use the `postgresql+asyncpg://` form)                  |
| `JWT_SECRET`                   | A 32+ char random string (e.g. `python -c "import secrets;print(secrets.token_urlsafe(32))"`) |
| `BASE_RPC_URL`                 | Same as the contract deploy                                                                   |
| `CERTIFICATE_CONTRACT_ADDRESS` | Address from step 1                                                                           |
| `ADMIN_PRIVATE_KEY`            | Same as the contract deploy                                                                   |
| `VAULT_HMAC_SECRETS`           | `vault-prod-01:<32-byte-secret>`                                                              |
| `BASESCAN_API_KEY`             | Same as step 1                                                                                |

The `railway.toml` start command runs `alembic upgrade head` before the API
boots, so first deploy creates the schema.

Public URL: shown in Railway → Service → Settings → Public Networking.

## 3. Frontend (Vercel)

```bash
cd frontend
vercel login
vercel link                     # connects this dir to a Vercel project
vercel --prod
```

Set one env var in Vercel (Project → Settings → Environment Variables):

| Variable                   | Value                                       |
| -------------------------- | ------------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL` | Backend public URL from step 2              |
| `NEXT_PUBLIC_BASESCAN_TX`  | `https://sepolia.basescan.org/tx` (default) |
| `NEXT_PUBLIC_IPFS_GATEWAY` | `https://gateway.pinata.cloud/ipfs`         |

After the first deploy, copy the Vercel URL into the backend's CORS
allowlist (`src/gemvault/main.py` → `allow_origins`) and redeploy the
backend. The current list already includes `https://gemvault.vercel.app`
as a default.

## 4. Seed demo data

Once the backend is reachable, drive a full escrow lifecycle so the
dashboard has something to show:

```bash
# Locally pointed at the live backend:
GEMVAULT_API_BASE=https://<your-railway-url> \
DATABASE_URL_SYNC=postgresql://<railway-postgres-conn> \
python scripts/demo/seed.py
```

`DATABASE_URL_SYNC` is the non-async psycopg DSN used to flip the admin's
KYC status to APPROVED directly (the admin can't approve their own KYC
because of the chicken-and-egg auth model — ADR-004 covers the prod swap-in).

## 5. Record the demo GIF

With both deploys up and seed data loaded:

```bash
cd frontend
npx playwright install chromium  # one-time
FRONTEND_URL=https://<your-vercel-url> npx playwright test
```

The spec is `frontend/e2e/record.spec.ts` (config: `frontend/playwright.config.ts`).
Convert the resulting WebM to GIF for the README:

```bash
ffmpeg -i e2e/.artifacts/*/video.webm -vf "fps=12,scale=960:-1:flags=lanczos" ../docs/demo.gif
```

## 6. Update README

Edit the top-level `README.md` to:

- Replace `<your-vercel-url>` in the live-demo section
- Embed `docs/demo.gif` near the top
- Add the Basescan link to the deployed contract
- Add a green CI badge:
  `![CI](https://github.com/soneeee22000/gemvault/actions/workflows/ci.yml/badge.svg)`

Commit + push.

## Rollback

- **Frontend:** `vercel rollback` from the Vercel CLI or via the dashboard.
- **Backend:** Railway keeps the last 3 deployments; redeploy from the
  service's Deployments tab.
- **Contract:** there is no rollback — deploy a fresh contract and update
  `CERTIFICATE_CONTRACT_ADDRESS` on Railway. The on-chain certs of the
  retired contract stay on Basescan as part of the audit trail.

## Cost estimate

For a portfolio piece running 24/7 with minimal traffic:

- Vercel — free tier, $0
- Railway — Hobby plan $5/month covers backend + Postgres
- Base Sepolia — free testnet
- Pinata — free tier (1 GB, 100 pins)
- Total: **~$5/month**
