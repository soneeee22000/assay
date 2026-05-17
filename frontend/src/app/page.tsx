"use client";

import {
  ArrowRight,
  Award,
  BookOpen,
  CheckCircle2,
  ExternalLink,
  EyeOff,
  FileWarning,
  Handshake,
  Layers,
  Lock,
  type LucideIcon,
  ScrollText,
  ShieldCheck,
  Workflow,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { BrandMark, Card, Spinner } from "@/components/ui";
import { fetchHealth } from "@/lib/api";
import { cn } from "@/lib/cn";
import { useAuth } from "@/lib/useAuth";

const API_DOCS_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL != null
    ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/docs`
    : "http://localhost:8000/docs";

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

  const dashboardHref = isReady && token ? "/ledger" : "/login";

  return (
    <main className="min-h-screen bg-background">
      <SiteHeader signedIn={isReady && token != null} />
      <Hero health={health} dashboardHref={dashboardHref} />
      <ProblemSection />
      <SolutionSection />
      <LifecycleSection />
      <ExploreSection />
      <ProofSection />
      <ClosingCta dashboardHref={dashboardHref} />
      <SiteFooter />
    </main>
  );
}

function SiteHeader({ signedIn }: { signedIn: boolean }) {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-surface/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <BrandMark />
        <div className="flex items-center gap-2">
          <a
            href="https://github.com/soneeee22000/assay"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-foreground-muted transition-colors hover:bg-muted hover:text-foreground sm:inline-flex"
          >
            GitHub
            <ExternalLink className="h-3.5 w-3.5" aria-hidden />
          </a>
          <Link
            href={signedIn ? "/ledger" : "/login"}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary-hover"
          >
            {signedIn ? "Open dashboard" : "Sign in"}
            <ArrowRight className="h-3.5 w-3.5" aria-hidden />
          </Link>
        </div>
      </div>
    </header>
  );
}

function Hero({
  health,
  dashboardHref,
}: {
  health: HealthStatus;
  dashboardHref: string;
}) {
  return (
    <section className="mx-auto max-w-6xl px-4 pt-14 pb-16 sm:px-6 sm:pt-20 sm:pb-20">
      <span className="inline-flex items-center gap-2 rounded-full border border-primary-soft bg-primary-soft px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-primary-soft-foreground">
        <ShieldCheck className="h-3 w-3" aria-hidden />
        RWA fintech reference architecture
      </span>
      <h1 className="mt-5 max-w-3xl text-pretty text-4xl font-semibold leading-[1.12] tracking-tight text-foreground sm:text-5xl">
        Vaulted metal you can prove you own — and transfer without moving it.
      </h1>
      <p className="mt-5 max-w-2xl text-base leading-relaxed text-foreground-muted sm:text-lg">
        Allocated gold and silver sit in a custodian&rsquo;s vault for years on
        end. Assay makes that ownership real on-chain: every bar gets an ERC-721
        certificate of authenticity, every sale settles through custodian-backed
        escrow, and every state change lands on an event-sourced ledger a
        regulator could audit end to end.
      </p>
      <div className="mt-7 flex flex-wrap items-center gap-3">
        <Link
          href={dashboardHref}
          className="inline-flex h-11 items-center gap-2 rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary-hover"
        >
          Walk the live dashboard
          <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
        <a
          href={API_DOCS_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-11 items-center gap-2 rounded-md border border-border bg-surface px-5 text-sm font-medium text-foreground transition-colors hover:border-border-strong hover:bg-muted"
        >
          API docs
          <ExternalLink className="h-4 w-4" aria-hidden />
        </a>
      </div>
      <div className="mt-6">
        <BackendStatusBadge status={health} />
      </div>
    </section>
  );
}

function ProblemSection() {
  return (
    <section className="border-t border-border bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <SectionHeading
          eyebrow="The problem"
          title="Paper-based ownership doesn't survive contact with finance"
          lede="The metal is real. The trust around it is the weak link — and it always has been."
        />
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          <PointCard
            tone="danger"
            icon={FileWarning}
            title="Proof that can be forged"
            body="Title to a bar lives in a PDF or a custodian's spreadsheet. It can be lost, duplicated, or quietly pledged as collateral twice over."
          />
          <PointCard
            tone="danger"
            icon={Handshake}
            title="Settlement on a handshake"
            body="A buyer wires the money and hopes. A seller signs over title and hopes. Every trade leans on an intermediary nobody gets to audit."
          />
          <PointCard
            tone="danger"
            icon={EyeOff}
            title="Provenance you can't see"
            body="Where the bar has been, who attested it, when it last changed hands — scattered across systems, reconstructable only after something goes wrong."
          />
        </div>
      </div>
    </section>
  );
}

function SolutionSection() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <SectionHeading
        eyebrow="The approach"
        title="How Assay closes the gap"
        lede="Three layers that rarely ship together — and only matter when they do."
      />
      <div className="mt-10 grid gap-4 md:grid-cols-3">
        <PointCard
          tone="primary"
          icon={Award}
          title="On-chain certificate of authenticity"
          body="Each bar mints as an ERC-721 on Base. Tamper-evident, independently verifiable, and transferable without a courier or a notary."
        />
        <PointCard
          tone="primary"
          icon={Lock}
          title="Custodian-backed escrow"
          body="Funds lock first. The vault cryptographically attests it still holds the bar. Only then does the certificate mint and settle — neither party has to trust the other."
        />
        <PointCard
          tone="primary"
          icon={ScrollText}
          title="Event-sourced ledger"
          body="Every action is an immutable event. The full history replays deterministically — a double-entry audit trail built in from the first line, not bolted on for the regulator later."
        />
      </div>
    </section>
  );
}

const LIFECYCLE: { title: string; body: string }[] = [
  {
    title: "Asset registered",
    body: "A vault custodian records a bar with its assay-certificate reference, weight, and fineness.",
  },
  {
    title: "Escrow opened",
    body: "A buyer and seller enter a custodian-backed escrow against that specific bar.",
  },
  {
    title: "Funds locked",
    body: "The buyer's balance moves into the escrow's locked bucket — no party can walk away with both.",
  },
  {
    title: "Vault attested",
    body: "The custodian signs an HMAC-verified webhook confirming it still physically holds the bar.",
  },
  {
    title: "Certificate minted & released",
    body: "The ERC-721 mints on Base, the seller is credited, and on-chain ownership settles to the buyer.",
  },
];

function LifecycleSection() {
  return (
    <section className="border-t border-border bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <SectionHeading
          eyebrow="How it works"
          title="One sale, end to end"
          lede="The escrow state machine is the product. A transfer cannot skip a step — the vault attestation gates the mint, and the mint gates release."
        />
        <ol className="mt-10 grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-2 lg:grid-cols-5">
          {LIFECYCLE.map((step, index) => (
            <li key={step.title} className="flex flex-col gap-3 bg-surface p-5">
              <div className="flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-primary-soft font-mono text-xs font-semibold text-primary-soft-foreground">
                  {index + 1}
                </span>
                {index < LIFECYCLE.length - 1 && (
                  <ArrowRight
                    className="h-3.5 w-3.5 text-foreground-subtle"
                    aria-hidden
                  />
                )}
              </div>
              <h3 className="text-sm font-semibold tracking-tight text-foreground">
                {step.title}
              </h3>
              <p className="text-sm leading-relaxed text-foreground-muted">
                {step.body}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function ExploreSection() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <SectionHeading
        eyebrow="See it running"
        title="Three surfaces, one live system"
        lede="The dashboard is pre-seeded with a full escrow lifecycle. Sign in with admin@example.com / adminpass1234 and follow a real bar from registration to release."
      />
      <div className="mt-10 grid gap-4 sm:grid-cols-3">
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
          description="The seven-state lifecycle from PENDING through RELEASED. Vault attestation gates every transfer."
        />
        <FeatureCard
          href="/certificates"
          icon={Award}
          title="Certificates"
          description="ERC-721 with an attestation gate on Base. IPFS-pinned metadata, Basescan-verified source."
        />
      </div>
    </section>
  );
}

const PROOF_STATS: { label: string; value: string; hint: string }[] = [
  { label: "Backend tests", value: "100", hint: "passing on CI" },
  { label: "API endpoints", value: "11", hint: "typed FastAPI surface" },
  { label: "Domain events", value: "13", hint: "audit-grade log" },
  { label: "Escrow states", value: "7", hint: "with a vault gate" },
];

function ProofSection() {
  return (
    <section className="border-t border-border bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <SectionHeading
          eyebrow="Built to a standard you can check"
          title="Financial-grade, not demo-grade"
          lede="Solidity, Python, and TypeScript end to end — every layer a fintech-meets-RWA platform actually needs to ship, with the contract source verified on Base."
        />
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PROOF_STATS.map((stat) => (
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
      </div>
    </section>
  );
}

function ClosingCta({ dashboardHref }: { dashboardHref: string }) {
  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <Card className="flex flex-col items-start gap-5 p-8 sm:p-10">
        <Layers className="h-7 w-7 text-primary" aria-hidden />
        <h2 className="max-w-2xl text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Follow a gold bar from the vault floor to on-chain settlement.
        </h2>
        <p className="max-w-2xl text-sm leading-relaxed text-foreground-muted sm:text-base">
          The fastest way to understand Assay is to walk it. Open the dashboard,
          read the ledger, step through a seeded escrow, and verify the
          certificate on Basescan yourself.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={dashboardHref}
            className="inline-flex h-11 items-center gap-2 rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary-hover"
          >
            Walk the live dashboard
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
          <a
            href="https://github.com/soneeee22000/assay"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-11 items-center gap-2 rounded-md border border-border bg-surface px-5 text-sm font-medium text-foreground transition-colors hover:border-border-strong hover:bg-muted"
          >
            Read the source
            <ExternalLink className="h-4 w-4" aria-hidden />
          </a>
        </div>
      </Card>
    </section>
  );
}

function SiteFooter() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 font-mono text-[11px] text-foreground-subtle sm:px-6">
        <span>
          Assay is an open-source reference architecture — a portfolio piece,
          not a regulated product.
        </span>
        <div className="flex flex-col gap-1 sm:flex-row sm:justify-between">
          <span>MIT · open-source · built by Pyae Sone Kyaw</span>
          <span>Solidity · FastAPI · Next.js</span>
        </div>
      </div>
    </footer>
  );
}

function SectionHeading({
  eyebrow,
  title,
  lede,
}: {
  eyebrow: string;
  title: string;
  lede: string;
}) {
  return (
    <div className="max-w-2xl">
      <p className="font-mono text-[11px] uppercase tracking-wider text-primary">
        {eyebrow}
      </p>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
        {title}
      </h2>
      <p className="mt-3 text-sm leading-relaxed text-foreground-muted sm:text-base">
        {lede}
      </p>
    </div>
  );
}

function PointCard({
  tone,
  icon: Icon,
  title,
  body,
}: {
  tone: "danger" | "primary";
  icon: LucideIcon;
  title: string;
  body: string;
}) {
  const toneClass =
    tone === "danger"
      ? "bg-danger-soft text-danger"
      : "bg-primary-soft text-primary-soft-foreground";
  return (
    <Card className="h-full p-5">
      <span
        className={cn("grid h-9 w-9 place-items-center rounded-md", toneClass)}
      >
        <Icon className="h-4 w-4" aria-hidden />
      </span>
      <h3 className="mt-4 text-base font-semibold tracking-tight text-foreground">
        {title}
      </h3>
      <p className="mt-1.5 text-sm leading-relaxed text-foreground-muted">
        {body}
      </p>
    </Card>
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
      tone: "border-border bg-muted text-foreground-muted",
      label: "Checking backend…",
    },
    ok: {
      tone: "border-success-soft bg-success-soft text-success",
      label: status.kind === "ok" ? `Backend healthy · v${status.version}` : "",
    },
    down: {
      tone: "border-danger-soft bg-danger-soft text-danger",
      label: "Backend unreachable",
    },
  } as const;

  const c = config[status.kind];

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-md border px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider",
        c.tone,
      )}
    >
      {status.kind === "loading" ? (
        <Spinner className="h-3.5 w-3.5" />
      ) : status.kind === "ok" ? (
        <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
      ) : (
        <XCircle className="h-3.5 w-3.5" aria-hidden />
      )}
      {c.label}
    </div>
  );
}
