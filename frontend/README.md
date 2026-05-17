# Assay Frontend

Next.js 15 · React 19 · TypeScript (strict) · Tailwind 4 · shadcn-style design tokens

Read-only admin dashboard for the Assay backend. See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).

## Quick start

```bash
cd frontend
pnpm install         # or `npm install` / `yarn`
pnpm dev             # http://localhost:3000
pnpm typecheck       # strict TS
pnpm lint            # next-lint
```

## Conventions (per global standards)

- Mobile-first; 44px minimum touch targets; 16px minimum input font size
- Design tokens in `globals.css` (oklch); never use raw colors like `bg-white` — use `bg-primary`, `text-foreground`, etc.
- 3-5 colors total; 2 font families max (Inter + JetBrains Mono)
- shadcn components customised in-place with `cva()` variants
- No emojis as icons — Lucide React only
- No gradient backgrounds on UI elements
- Prefer `gap-*` over `space-*`; prefer Tailwind scale (`p-4`) over arbitrary values

## Layout

```
src/
└── app/
    ├── layout.tsx         Root layout
    ├── page.tsx           Dashboard home
    ├── globals.css        Tailwind + design tokens
    ├── ledger/            Sprint 5 — event audit trail
    ├── certificates/      Sprint 5 — minted certs gallery
    └── escrows/           Sprint 5 — escrow timelines
```

## Sprint 0 status

The scaffold ships with a static placeholder home page. Real dashboard views land in Sprint 5 after the backend exposes them.
