"use client";

import {
  ArrowRight,
  Award,
  BookOpen,
  CheckCircle2,
  ExternalLink,
  type LucideIcon,
  ShieldCheck,
  Workflow,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { BrandMark, Button, Card, Spinner } from "@/components/ui";
import { fetchHealth } from "@/lib/api";
import { cn } from "@/lib/cn";
import { useAuth } from "@/lib/useAuth";

type HealthStatus =
  | { kind: "loading" }
  | { kind: "ok"; version: string }
  | { kind: "down" };

export default function Home() {
  const { token, isReady } = useAuth();
  const [health, setHealth] = useState<HealthStatus>({ kind: "loading" });

  useEffect(() => {
    fetchHealth()
      .then((res) => setHealth({ kind: "ok", version: res.version }))
      .catch(() => setHealth({ kind: "down" }));
  }, []);

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-surface/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <BrandMark />
          <div className="flex items-center gap-2">
            <a
              href="https://github.com/soneeee22000/assay"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-foreground-muted transition-colors hover:bg-muted hover:text-foreground"
            >
              GitHub
              <ExternalLink className="h-3.5 w-3.5" aria-hidden />
            </a>
            {isReady && token ? (
              <Link
                href="/ledger"
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary-hover"
              >
                Open dashboard
                <ArrowRight className="h-3.5 w-3.5" aria-hidden />
              </Link>
            ) : (
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary-hover"
              >
                Sign in
                <ArrowRight className="h-3.5 w-3.5" aria-hidden />
              </Link>
            )}
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-20">
        <div className="space-y-6">
          <span className="inline-flex items-center gap-2 rounded-full border border-primary-soft bg-primary-soft px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-primary-soft-foreground">
            <ShieldCheck className="h-3 w-3" aria-hidden />
            RWA fintech reference architecture
          </span>
          <h1 className="max-w-3xl text-4xl font-semibold leading-tight tracking-tight text-foreground sm:text-5xl">
            Event-sourced ledger meets on-chain certificates of authenticity.
          </h1>
          <p className="max-w-2xl text-base leading-relaxed text-foreground-muted sm:text-lg">
            Vaulted precious metals tokenised as ERC-721 certificates,
            settled through a custodian-backed escrow lifecycle, on a
            financial-grade event-sourced ledger. Built end-to-end across
            Solidity, Python, and TypeScript.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              href={isReady && token ? "/ledger" : "/login"}
              className="inline-flex h-11 items-center gap-2 rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary-hover"
            >
              {isReady && token ? "Open dashboard" : "Sign in to dashboard"}
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-11 items-center gap-2 rounded-md border border-border bg-surface px-5 text-sm font-medium text-foreground transition-colors hover:border-border-strong hover:bg-muted"
            >
              API docs
              <ExternalLink className="h-4 w-4" aria-hidden />
            </a>
          </div>

          <BackendStatusBadge status={health} />
        </div>

        <div className="mt-14 grid gap-4 sm:grid-cols-3">
          <FeatureCard
            href="/ledger"
            icon={BookOpen}
            title="Ledger"
            description="Append-only event store. Deterministic replay, signed audit exports, full correlation tracing."
          />
          <FeatureCard
            href="/escrows"
            icon={Workflow}
            title="Escrows"
            description="Seven-state lifecycle from PENDING through RELEASED. Vault attestation gates every transfer."
          />
          <FeatureCard
            href="/certificates"
            icon={Award}
            title="Certificates"
            description="ERC-721 with attestation gate on Base. IPFS-pinned metadata, Basescan-verified source."
          />
        </div>

        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Backend tests", value: "91", hint: "passing on CI" },
            { label: "API endpoints", value: "11", hint: "FastAPI surface" },
            { label: "Domain events", value: "13", hint: "audit-grade log" },
            { label: "Escrow states", value: "7", hint: "with vault gate" },
          ].map((stat) => (
            <Card key={stat.label} className="px-4 py-4">
              <p className="font-mono text-[10px] uppercase tracking-wider text-foreground-muted">
                {stat.label}
              </p>
              <p className="mt-1 font-mono text-2xl font-semibold tabular-nums tracking-tight text-foreground">
                {stat.value}
              </p>
              <p className="text-xs text-foreground-muted">{stat.hint}</p>
            </Card>
          ))}
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-2 px-4 py-6 font-mono text-[11px] text-foreground-subtle sm:flex-row sm:items-center sm:px-6">
          <span>MIT · open-source · built by Pyae Sone Kyaw</span>
          <span>v0.1.0 · 2026-05-12</span>
        </div>
      </footer>
    </main>
  );
}

function FeatureCard({
  href,
  icon: Icon,
  title,
  description,
}: {
  href: string;
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <Link href={href} className="group block">
      <Card className="h-full p-5 transition-all duration-150 hover:-translate-y-0.5 hover:border-border-strong hover:shadow-md">
        <div className="flex items-center justify-between">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-primary-soft text-primary-soft-foreground transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
            <Icon className="h-4 w-4" aria-hidden />
          </span>
          <ArrowRight
            className="h-4 w-4 text-foreground-subtle transition-transform group-hover:translate-x-0.5 group-hover:text-foreground"
            aria-hidden
          />
        </div>
        <h3 className="mt-4 text-base font-semibold tracking-tight text-foreground">
          {title}
        </h3>
        <p className="mt-1.5 text-sm leading-relaxed text-foreground-muted">
          {description}
        </p>
      </Card>
    </Link>
  );
}

function BackendStatusBadge({ status }: { status: HealthStatus }) {
  const config = {
    loading: {
      icon: Spinner,
      tone: "border-border bg-muted text-foreground-muted",
      label: "Checking backend…",
    },
    ok: {
      icon: CheckCircle2,
      tone: "border-success-soft bg-success-soft text-success",
      label: status.kind === "ok" ? `Backend healthy · v${status.version}` : "",
    },
    down: {
      icon: XCircle,
      tone: "border-danger-soft bg-danger-soft text-danger",
      label: "Backend unreachable — start uvicorn on :8000",
    },
  } as const;

  const c = config[status.kind];
  const Icon = c.icon;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-md border px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider",
        c.tone,
      )}
    >
      {status.kind === "loading" ? (
        <Spinner className="h-3.5 w-3.5" />
      ) : (
        <Icon className="h-3.5 w-3.5" aria-hidden />
      )}
      {c.label}
    </div>
  );
}
