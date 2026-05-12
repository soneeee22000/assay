"use client";

import {
  Award,
  ExternalLink,
  HardDrive,
  Inbox,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { DashboardShell } from "@/components/dashboard-shell";
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  ErrorRow,
  KpiCard,
  LoadingRow,
} from "@/components/ui";
import { ApiError, fetchAuditExport, type DomainEvent } from "@/lib/api";
import { formatTimestamp, truncateMiddle } from "@/lib/format";

const WINDOW_HOURS = 24;
const IPFS_GATEWAY =
  process.env.NEXT_PUBLIC_IPFS_GATEWAY ?? "https://gateway.pinata.cloud/ipfs";
const BASESCAN_TX =
  process.env.NEXT_PUBLIC_BASESCAN_TX ?? "https://sepolia.basescan.org/tx";

type CertificateSummary = {
  certificate_id: string;
  token_id: string;
  tx_hash: string;
  ipfs_hash: string;
  escrow_id: string;
  minted_at: string;
};

export default function CertificatesPage() {
  return (
    <AuthGate>
      <CertificatesGallery />
    </AuthGate>
  );
}

function CertificatesGallery() {
  const [certificates, setCertificates] = useState<CertificateSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const to = new Date();
    const from = new Date(to.getTime() - WINDOW_HOURS * 60 * 60 * 1000);
    fetchAuditExport({ from: from.toISOString(), to: to.toISOString() })
      .then((res) => setCertificates(deriveCertificates(res.events)))
      .catch((err) => {
        if (err instanceof ApiError) setError(err.detail);
        else setError(String(err));
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const stats = useMemo(
    () => ({
      total: certificates.length,
      latest: certificates[0]?.minted_at
        ? formatTimestamp(certificates[0].minted_at)
        : "—",
    }),
    [certificates],
  );

  return (
    <DashboardShell
      title="Certificates of authenticity"
      description="ERC-721 certificates minted to Base. Each one is anchored to a physical asset and the escrow that paid for it."
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
          label="Total certificates"
          value={stats.total}
          hint={`last ${WINDOW_HOURS}h`}
          icon={Award}
          tone="accent"
        />
        <KpiCard
          label="Latest mint"
          value={stats.latest}
          hint="UTC"
          icon={Sparkles}
          tone="primary"
        />
        <KpiCard
          label="Storage"
          value="IPFS"
          hint="via Pinata"
          icon={HardDrive}
          tone="neutral"
        />
      </div>

      <Card className="mt-6">
        <CardHeader>
          <h2 className="text-sm font-semibold text-foreground">
            Minted certificates
          </h2>
          <Badge tone="neutral">{certificates.length}</Badge>
        </CardHeader>

        {loading ? (
          <LoadingRow label="Loading certificates…" />
        ) : error ? (
          <CardBody>
            <ErrorRow title="Failed to load certificates" detail={error} />
          </CardBody>
        ) : certificates.length === 0 ? (
          <CardBody>
            <EmptyState
              icon={Inbox}
              title="No certificates yet"
              description={
                <>
                  Drive an escrow through{" "}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                    POST /escrows/&#123;id&#125;/mint
                  </code>{" "}
                  to mint one.
                </>
              }
            />
          </CardBody>
        ) : (
          <CardBody className="px-4 py-4 sm:px-5 sm:py-5">
            <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {certificates.map((cert) => (
                <CertificateCard key={cert.certificate_id} cert={cert} />
              ))}
            </ul>
          </CardBody>
        )}
      </Card>
    </DashboardShell>
  );
}

function CertificateCard({ cert }: { cert: CertificateSummary }) {
  return (
    <li>
      <Card className="h-full transition-shadow hover:shadow-md">
        <div className="relative overflow-hidden rounded-t-lg border-b border-border bg-muted/60 px-5 py-6">
          <div className="flex items-start justify-between">
            <div className="flex h-11 w-11 items-center justify-center rounded-full border border-border bg-surface shadow-sm">
              <Award className="h-5 w-5 text-primary" aria-hidden />
            </div>
            <Badge tone="accent">Token #{cert.token_id}</Badge>
          </div>
          <p className="mt-4 font-mono text-[10px] uppercase tracking-wider text-foreground-muted">
            Certificate of authenticity
          </p>
          <p className="mt-1 font-mono text-xs font-medium text-foreground">
            {truncateMiddle(cert.certificate_id, 8, 6)}
          </p>
        </div>

        <CardBody className="space-y-3">
          <div className="space-y-1">
            <p className="font-mono text-[10px] uppercase tracking-wider text-foreground-muted">
              Escrow
            </p>
            <p className="font-mono text-xs text-foreground">
              {truncateMiddle(cert.escrow_id, 8, 6)}
            </p>
          </div>

          <div className="space-y-1">
            <p className="font-mono text-[10px] uppercase tracking-wider text-foreground-muted">
              Minted
            </p>
            <p className="font-mono text-xs tabular-nums text-foreground">
              {formatTimestamp(cert.minted_at)}
            </p>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            <ExternalChip href={`${BASESCAN_TX}/${cert.tx_hash}`}>
              Basescan
            </ExternalChip>
            <ExternalChip href={`${IPFS_GATEWAY}/${cert.ipfs_hash}`}>
              IPFS
            </ExternalChip>
          </div>
        </CardBody>
      </Card>
    </li>
  );
}

function ExternalChip({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2.5 py-1 font-mono text-[11px] font-medium text-foreground transition-colors hover:border-primary hover:bg-primary-soft hover:text-primary-soft-foreground"
    >
      {children}
      <ExternalLink className="h-3 w-3" aria-hidden />
    </a>
  );
}

function deriveCertificates(events: DomainEvent[]): CertificateSummary[] {
  const minted = events.filter((e) => e.event_type === "CertificateMinted");
  return minted
    .map((event) => {
      const payload = event.payload as Record<string, unknown>;
      return {
        certificate_id: String(payload.certificate_id ?? event.event_id),
        token_id: String(payload.token_id ?? "?"),
        tx_hash: String(payload.tx_hash ?? ""),
        ipfs_hash: String(payload.ipfs_hash ?? ""),
        escrow_id: String(payload.escrow_id ?? event.stream_id),
        minted_at: event.ts,
      };
    })
    .sort(
      (a, b) =>
        new Date(b.minted_at).getTime() - new Date(a.minted_at).getTime(),
    );
}
