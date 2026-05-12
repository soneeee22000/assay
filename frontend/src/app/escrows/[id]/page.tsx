"use client";

import {
  ArrowLeft,
  Award,
  Calendar,
  CheckCircle2,
  Coins,
  FileSignature,
  Lock,
  Workflow,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { DashboardShell } from "@/components/dashboard-shell";
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  ErrorRow,
  LoadingRow,
} from "@/components/ui";
import { ApiError, fetchEscrow, type Escrow } from "@/lib/api";
import { cn } from "@/lib/cn";
import { formatTimestamp, truncateMiddle } from "@/lib/format";

type Step = {
  state: Escrow["state"];
  label: string;
  description: string;
  at: string | null;
  icon: typeof Workflow;
};

const STATE_META: Record<
  Escrow["state"],
  {
    tone: "neutral" | "primary" | "accent" | "success" | "danger";
    label: string;
  }
> = {
  PENDING: { tone: "neutral", label: "Pending" },
  FUNDS_LOCKED: { tone: "primary", label: "Funds locked" },
  VAULT_ATTESTED: { tone: "primary", label: "Vault attested" },
  CERTIFICATE_MINTED: { tone: "accent", label: "Certificate minted" },
  RELEASED: { tone: "success", label: "Released" },
  CANCELLED: { tone: "neutral", label: "Cancelled" },
  REFUNDED: { tone: "danger", label: "Refunded" },
};

export default function EscrowDetailPage() {
  return (
    <AuthGate>
      <EscrowDetail />
    </AuthGate>
  );
}

function EscrowDetail() {
  const { id } = useParams<{ id: string }>();
  const [escrow, setEscrow] = useState<Escrow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    fetchEscrow(id)
      .then(setEscrow)
      .catch((err) => {
        if (err instanceof ApiError) setError(err.detail);
        else setError(String(err));
      })
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <DashboardShell
      title="Escrow detail"
      description="Step-by-step lifecycle for a single escrow. Every transition stamped from the projection."
      actions={
        <Link
          href="/escrows"
          className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:border-border-strong hover:bg-muted"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          All escrows
        </Link>
      }
    >
      {loading ? (
        <LoadingRow label="Loading escrow…" />
      ) : error ? (
        <ErrorRow title="Failed to load escrow" detail={error} />
      ) : !escrow ? null : (
        <EscrowBody escrow={escrow} />
      )}
    </DashboardShell>
  );
}

function EscrowBody({ escrow }: { escrow: Escrow }) {
  const meta = STATE_META[escrow.state];

  const steps: Step[] = [
    {
      state: "PENDING",
      label: "Opened",
      description: "Escrow created; awaiting buyer funds.",
      at: escrow.opened_at,
      icon: Workflow,
    },
    {
      state: "FUNDS_LOCKED",
      label: "Funds locked",
      description: "Buyer's USDC moved into locked balance.",
      at: escrow.locked_at,
      icon: Lock,
    },
    {
      state: "VAULT_ATTESTED",
      label: "Vault attested",
      description: "Custodian HMAC-signed the custody handoff.",
      at: escrow.attested_at,
      icon: FileSignature,
    },
    {
      state: "CERTIFICATE_MINTED",
      label: "Certificate minted",
      description: "ERC-721 certificate minted on Base.",
      at: escrow.minted_at,
      icon: Award,
    },
    {
      state: "RELEASED",
      label: "Released",
      description: "Seller credited; buyer owns the cert.",
      at: escrow.released_at,
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <code className="font-mono text-sm font-semibold text-foreground">
                {truncateMiddle(escrow.escrow_id, 12, 8)}
              </code>
              <Badge tone={meta.tone}>{meta.label}</Badge>
            </div>
            <p className="text-xs text-foreground-muted">
              {escrow.amount_usdc} USDC · buyer{" "}
              {truncateMiddle(escrow.buyer_id)} → seller{" "}
              {truncateMiddle(escrow.seller_id)}
            </p>
          </div>
        </CardHeader>
        <CardBody className="px-6 py-6">
          <ol className="space-y-5">
            {steps.map((step, idx) => (
              <TimelineStep
                key={step.state}
                index={idx + 1}
                step={step}
                isLast={idx === steps.length - 1}
              />
            ))}
          </ol>
        </CardBody>
      </Card>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-foreground">Metadata</h3>
          </CardHeader>
          <CardBody className="space-y-3 text-sm">
            <Field label="Escrow ID" value={escrow.escrow_id} mono />
            <Field label="Asset ID" value={escrow.asset_id} mono />
            <Field label="Buyer" value={escrow.buyer_id} mono />
            <Field label="Seller" value={escrow.seller_id} mono />
            <Field label="Amount" value={`${escrow.amount_usdc} USDC`} />
          </CardBody>
        </Card>

        <Card className="bg-muted/40">
          <CardBody className="space-y-1.5">
            <div className="flex items-center gap-2 text-xs text-foreground-muted">
              <Coins className="h-3.5 w-3.5" aria-hidden />
              <span className="font-mono uppercase tracking-wider">
                Settlement
              </span>
            </div>
            <p className="text-sm text-foreground">
              USDC moves through the buyer's locked balance to the seller's
              available balance only after the on-chain certificate mints.
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function TimelineStep({
  index,
  step,
  isLast,
}: {
  index: number;
  step: Step;
  isLast: boolean;
}) {
  const reached = step.at !== null;
  const Icon = step.icon;
  return (
    <li className="relative flex gap-4">
      {isLast ? null : (
        <span
          aria-hidden
          className={cn(
            "absolute left-[14px] top-9 bottom-[-20px] w-px",
            reached ? "bg-primary/50" : "bg-border",
          )}
        />
      )}
      <span
        className={cn(
          "z-10 grid h-7 w-7 shrink-0 place-items-center rounded-full border transition-colors",
          reached
            ? "border-primary bg-primary text-primary-foreground"
            : "border-border bg-surface text-foreground-subtle",
        )}
      >
        <Icon className="h-3.5 w-3.5" aria-hidden />
      </span>
      <div className="flex-1 space-y-0.5 pb-1">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <p
            className={cn(
              "text-sm font-medium",
              reached ? "text-foreground" : "text-foreground-muted",
            )}
          >
            {index}. {step.label}
          </p>
          <span className="inline-flex items-center gap-1 font-mono text-[11px] tabular-nums text-foreground-muted">
            <Calendar className="h-3 w-3" aria-hidden />
            {step.at ? formatTimestamp(step.at) : "—"}
          </span>
        </div>
        <p
          className={cn(
            "text-xs",
            reached ? "text-foreground-muted" : "text-foreground-subtle",
          )}
        >
          {step.description}
        </p>
      </div>
    </li>
  );
}

function Field({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[10px] uppercase tracking-wider text-foreground-muted">
        {label}
      </span>
      <span
        className={cn(
          "break-all text-sm text-foreground",
          mono && "font-mono text-xs",
        )}
      >
        {value}
      </span>
    </div>
  );
}
