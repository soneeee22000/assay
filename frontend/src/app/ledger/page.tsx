"use client";

import {
  Activity,
  ArrowDownToLine,
  ArrowUpFromLine,
  Award,
  CheckCircle2,
  Coins,
  FileSignature,
  Inbox,
  Lock,
  RefreshCw,
  ShieldCheck,
  UserPlus,
  Workflow,
} from "lucide-react";
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
  type AuditExport,
  type DomainEvent,
} from "@/lib/api";
import { formatTimestamp, truncateMiddle } from "@/lib/format";

const WINDOW_HOURS = 24;

const EVENT_ICONS: Record<
  string,
  { icon: typeof Activity; tone: "primary" | "accent" | "success" | "neutral" }
> = {
  UserRegistered: { icon: UserPlus, tone: "neutral" },
  KycApproved: { icon: ShieldCheck, tone: "success" },
  KycRejected: { icon: ShieldCheck, tone: "neutral" },
  FundsDeposited: { icon: ArrowDownToLine, tone: "primary" },
  FundsWithdrawn: { icon: ArrowUpFromLine, tone: "neutral" },
  AssetRegistered: { icon: Coins, tone: "accent" },
  EscrowOpened: { icon: Workflow, tone: "primary" },
  FundsLocked: { icon: Lock, tone: "primary" },
  VaultAttested: { icon: FileSignature, tone: "primary" },
  CertificateMinted: { icon: Award, tone: "accent" },
  EscrowReleased: { icon: CheckCircle2, tone: "success" },
};

export default function LedgerPage() {
  return (
    <AuthGate>
      <LedgerView />
    </AuthGate>
  );
}

function LedgerView() {
  const [data, setData] = useState<AuditExport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const to = new Date();
    const from = new Date(to.getTime() - WINDOW_HOURS * 60 * 60 * 1000);
    fetchAuditExport({ from: from.toISOString(), to: to.toISOString() })
      .then((res) => setData(res))
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
    if (!data) return null;
    const types = new Set(data.events.map((e) => e.event_type));
    const streams = new Set(data.events.map((e) => e.stream_id));
    return {
      total: data.count,
      types: types.size,
      streams: streams.size,
    };
  }, [data]);

  return (
    <DashboardShell
      title="Event ledger"
      description={`Append-only audit trail. Showing the last ${WINDOW_HOURS} hours from the event store.`}
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
      <div className="grid gap-3 sm:grid-cols-3">
        <KpiCard
          label="Total events"
          value={stats?.total ?? "—"}
          hint={`last ${WINDOW_HOURS}h`}
          icon={Activity}
          tone="primary"
        />
        <KpiCard
          label="Event types"
          value={stats?.types ?? "—"}
          hint="distinct kinds"
          icon={FileSignature}
          tone="accent"
        />
        <KpiCard
          label="Streams touched"
          value={stats?.streams ?? "—"}
          hint="aggregates"
          icon={Workflow}
          tone="neutral"
        />
      </div>

      <Card className="mt-6 overflow-hidden">
        <CardHeader>
          <h2 className="text-sm font-semibold text-foreground">Timeline</h2>
          {stats ? <Badge tone="neutral">{stats.total} events</Badge> : null}
        </CardHeader>

        {loading ? (
          <LoadingRow label="Loading events…" />
        ) : error ? (
          <div className="p-4">
            <ErrorRow title="Failed to load events" detail={error} />
          </div>
        ) : !data || data.events.length === 0 ? (
          <div className="p-4">
            <EmptyState
              icon={Inbox}
              title="No events in this window"
              description={
                <>
                  Drive the backend via{" "}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                    POST /api/v1/users
                  </code>
                  ,{" "}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                    POST /api/v1/escrows
                  </code>
                  , then refresh.
                </>
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-muted/50 font-mono text-[10px] uppercase tracking-wider text-foreground-muted">
                <tr>
                  <th className="px-4 py-2.5">Event</th>
                  <th className="px-4 py-2.5">Stream</th>
                  <th className="px-4 py-2.5">Version</th>
                  <th className="px-4 py-2.5">Time</th>
                  <th className="hidden px-4 py-2.5 md:table-cell">Payload</th>
                </tr>
              </thead>
              <tbody>
                {data.events.map((event) => (
                  <EventRow key={event.event_id} event={event} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </DashboardShell>
  );
}

function EventRow({ event }: { event: DomainEvent }) {
  const meta = EVENT_ICONS[event.event_type] ?? {
    icon: Activity,
    tone: "neutral" as const,
  };
  const Icon = meta.icon;
  const toneClasses: Record<typeof meta.tone, string> = {
    primary: "bg-primary-soft text-primary-soft-foreground",
    accent: "bg-accent-soft text-accent-soft-foreground",
    success: "bg-success-soft text-success",
    neutral: "bg-muted text-foreground-muted",
  };

  return (
    <tr className="border-b border-border last:border-b-0 transition-colors hover:bg-muted/40">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span
            className={`grid h-7 w-7 shrink-0 place-items-center rounded-md ${toneClasses[meta.tone]}`}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden />
          </span>
          <span className="text-sm font-medium text-foreground">
            {event.event_type}
          </span>
        </div>
      </td>
      <td className="px-4 py-3 font-mono text-xs text-foreground-muted">
        {event.stream_type}/{truncateMiddle(event.stream_id)}
      </td>
      <td className="px-4 py-3 font-mono text-xs tabular-nums text-foreground-muted">
        v{event.version}
      </td>
      <td className="px-4 py-3 font-mono text-xs tabular-nums text-foreground-muted">
        {formatTimestamp(event.ts)}
      </td>
      <td className="hidden max-w-md px-4 py-3 md:table-cell">
        <code className="block truncate font-mono text-[11px] text-foreground-subtle">
          {JSON.stringify(event.payload)}
        </code>
      </td>
    </tr>
  );
}
