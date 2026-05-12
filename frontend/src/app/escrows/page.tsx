"use client";

import {
  CheckCircle2,
  ChevronRight,
  Coins,
  Inbox,
  Lock,
  RefreshCw,
  Workflow,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { DashboardShell } from "@/components/dashboard-shell";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  ErrorRow,
  KpiCard,
  LoadingRow,
} from "@/components/ui";
import {
  ApiError,
  fetchAuditExport,
  type DomainEvent,
  type Escrow,
} from "@/lib/api";
import { formatRelative, truncateMiddle } from "@/lib/format";

const WINDOW_HOURS = 24;

const STATE_ORDER: Escrow["state"][] = [
  "PENDING",
  "FUNDS_LOCKED",
  "VAULT_ATTESTED",
  "CERTIFICATE_MINTED",
  "RELEASED",
  "CANCELLED",
  "REFUNDED",
];

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

type EscrowSummary = {
  escrow_id: string;
  amount?: string;
  state: Escrow["state"];
  buyer_id?: string;
  seller_id?: string;
  asset_id?: string;
  opened_at: string;
  last_event_at: string;
};

export default function EscrowsPage() {
  return (
    <AuthGate>
      <EscrowsList />
    </AuthGate>
  );
}

function EscrowsList() {
  const [escrows, setEscrows] = useState<EscrowSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const to = new Date();
    const from = new Date(to.getTime() - WINDOW_HOURS * 60 * 60 * 1000);
    fetchAuditExport({ from: from.toISOString(), to: to.toISOString() })
      .then((res) => setEscrows(deriveEscrows(res.events)))
      .catch((err) => {
        if (err instanceof ApiError) setError(err.detail);
        else setError(String(err));
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const stats = useMemo(() => {
    const released = escrows.filter((e) => e.state === "RELEASED").length;
    const active = escrows.filter(
      (e) =>
        e.state !== "RELEASED" &&
        e.state !== "CANCELLED" &&
        e.state !== "REFUNDED",
    ).length;
    const totalUsdc = escrows.reduce(
      (sum, e) => sum + Number.parseFloat(e.amount ?? "0"),
      0,
    );
    return { total: escrows.length, released, active, totalUsdc };
  }, [escrows]);

  return (
    <DashboardShell
      title="Escrows"
      description={`Custodian-backed escrow lifecycle. Showing escrows opened in the last ${WINDOW_HOURS} hours.`}
      actions={
        <Button
          variant="secondary"
          size="sm"
          leadingIcon={RefreshCw}
          onClick={load}
          disabled={loading}
        >
          Refresh
        </Button>
      }
    >
      <div className="grid gap-3 sm:grid-cols-4">
        <KpiCard
          label="Total escrows"
          value={stats.total}
          hint={`last ${WINDOW_HOURS}h`}
          icon={Workflow}
          tone="primary"
        />
        <KpiCard
          label="In flight"
          value={stats.active}
          hint="non-terminal"
          icon={Lock}
          tone="primary"
        />
        <KpiCard
          label="Released"
          value={stats.released}
          hint="terminal"
          icon={CheckCircle2}
          tone="success"
        />
        <KpiCard
          label="Volume"
          value={`${stats.totalUsdc.toFixed(2)} USDC`}
          hint="across all escrows"
          icon={Coins}
          tone="accent"
        />
      </div>

      <Card className="mt-6">
        <CardHeader>
          <h2 className="text-sm font-semibold text-foreground">Escrow list</h2>
          <Badge tone="neutral">{escrows.length}</Badge>
        </CardHeader>

        {loading ? (
          <LoadingRow label="Loading escrows…" />
        ) : error ? (
          <div className="p-4">
            <ErrorRow title="Failed to load escrows" detail={error} />
          </div>
        ) : escrows.length === 0 ? (
          <div className="p-4">
            <EmptyState
              icon={Inbox}
              title="No escrows in this window"
              description={
                <>
                  Open one via{" "}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                    POST /api/v1/escrows
                  </code>{" "}
                  or run the seed script.
                </>
              }
            />
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {escrows.map((escrow) => (
              <EscrowRow key={escrow.escrow_id} escrow={escrow} />
            ))}
          </ul>
        )}
      </Card>
    </DashboardShell>
  );
}

function EscrowRow({ escrow }: { escrow: EscrowSummary }) {
  const meta = STATE_META[escrow.state];
  return (
    <li>
      <Link
        href={`/escrows/${escrow.escrow_id}`}
        className="group flex items-center gap-4 px-4 py-3 transition-colors hover:bg-muted/40"
      >
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <code className="font-mono text-sm font-medium text-foreground">
              {truncateMiddle(escrow.escrow_id, 10, 6)}
            </code>
            <Badge tone={meta.tone}>{meta.label}</Badge>
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[11px] text-foreground-muted">
            {escrow.amount ? (
              <span className="text-foreground">
                <span className="text-foreground-muted">amount </span>
                <span className="tabular-nums">{escrow.amount}</span> USDC
              </span>
            ) : null}
            {escrow.buyer_id ? (
              <span>buyer {truncateMiddle(escrow.buyer_id)}</span>
            ) : null}
            {escrow.seller_id ? (
              <span>seller {truncateMiddle(escrow.seller_id)}</span>
            ) : null}
            <span>updated {formatRelative(escrow.last_event_at)}</span>
          </div>
        </div>
        <ChevronRight
          className="h-4 w-4 shrink-0 text-foreground-subtle transition-transform group-hover:translate-x-0.5 group-hover:text-foreground"
          aria-hidden
        />
      </Link>
    </li>
  );
}

function deriveEscrows(events: DomainEvent[]): EscrowSummary[] {
  const byId = new Map<string, EscrowSummary>();

  for (const event of events) {
    if (event.stream_type !== "escrow") continue;
    const id = event.stream_id;
    const existing = byId.get(id) ?? {
      escrow_id: id,
      state: "PENDING" as Escrow["state"],
      opened_at: event.ts,
      last_event_at: event.ts,
    };

    if (event.event_type === "EscrowOpened") {
      const payload = event.payload as Record<string, string>;
      existing.amount = String(payload.amount ?? "");
      existing.buyer_id = String(payload.buyer_id ?? "");
      existing.seller_id = String(payload.seller_id ?? "");
      existing.asset_id = String(payload.asset_id ?? "");
      existing.opened_at = event.ts;
    }

    const nextState = stateFromEvent(event.event_type);
    if (
      nextState &&
      STATE_ORDER.indexOf(nextState) >= STATE_ORDER.indexOf(existing.state)
    ) {
      existing.state = nextState;
    }

    if (
      new Date(event.ts).getTime() > new Date(existing.last_event_at).getTime()
    ) {
      existing.last_event_at = event.ts;
    }

    byId.set(id, existing);
  }

  return [...byId.values()].sort(
    (a, b) =>
      new Date(b.last_event_at).getTime() - new Date(a.last_event_at).getTime(),
  );
}

function stateFromEvent(eventType: string): Escrow["state"] | null {
  switch (eventType) {
    case "EscrowOpened":
      return "PENDING";
    case "FundsLocked":
      return "FUNDS_LOCKED";
    case "VaultAttested":
      return "VAULT_ATTESTED";
    case "CertificateMinted":
      return "CERTIFICATE_MINTED";
    case "EscrowReleased":
      return "RELEASED";
    case "EscrowCancelled":
      return "CANCELLED";
    case "EscrowRefunded":
      return "REFUNDED";
    default:
      return null;
  }
}
