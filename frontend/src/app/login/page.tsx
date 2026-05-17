"use client";

import { ArrowRight, KeyRound, Mail } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { BrandMark, Button, ErrorRow } from "@/components/ui";
import { ApiError, login } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { setToken } = useAuth();
  const router = useRouter();

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const token = await login({ email, password });
      setToken(token.access_token);
      router.replace("/ledger");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError("Unexpected error. Confirm the backend is running on :8000.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      <section className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-sm space-y-8">
          <Link href="/" className="inline-block">
            <BrandMark />
          </Link>

          <div className="space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Sign in
            </h1>
            <p className="text-sm text-foreground-muted">
              Stub auth per{" "}
              <a
                href="https://github.com/soneeee22000/assay/blob/main/docs/adr/decisions.md"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                ADR-004
              </a>
              . Production would swap in Clerk, Auth0, or Supabase Auth at this
              integration point.
            </p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <label className="block space-y-1.5">
              <span className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
                Email
              </span>
              <span className="relative block">
                <Mail
                  aria-hidden
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-subtle"
                />
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@example.com"
                  className="h-11 w-full rounded-md border border-border bg-surface pl-9 pr-3 text-base text-foreground placeholder:text-foreground-subtle transition-colors hover:border-border-strong focus:border-primary focus:outline-none"
                />
              </span>
            </label>

            <label className="block space-y-1.5">
              <span className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
                Password
              </span>
              <span className="relative block">
                <KeyRound
                  aria-hidden
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-subtle"
                />
                <input
                  type="password"
                  required
                  autoComplete="current-password"
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-11 w-full rounded-md border border-border bg-surface pl-9 pr-3 text-base text-foreground transition-colors hover:border-border-strong focus:border-primary focus:outline-none"
                />
              </span>
            </label>

            {error ? <ErrorRow title="Sign-in failed" detail={error} /> : null}

            <Button
              type="submit"
              size="lg"
              trailingIcon={submitting ? undefined : ArrowRight}
              disabled={submitting}
              className="w-full"
            >
              {submitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="rounded-md border border-border bg-muted/60 px-3 py-2 font-mono text-[11px] text-foreground-muted">
            Demo creds:{" "}
            <span className="text-foreground">admin@example.com</span> ·{" "}
            <span className="text-foreground">adminpass1234</span>
          </p>
        </div>
      </section>

      <aside className="hidden border-l border-border bg-muted/40 lg:flex lg:items-center lg:justify-center">
        <div className="max-w-md space-y-5 px-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-primary-soft bg-primary-soft px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-primary-soft-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            Reference architecture
          </span>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground">
            RWA fintech control surface
          </h2>
          <p className="text-sm leading-relaxed text-foreground-muted">
            Event-sourced ledger, on-chain certificates of authenticity, and a
            custodian-backed escrow lifecycle — built end-to-end across
            Solidity, Python, and TypeScript.
          </p>
          <ul className="space-y-2 text-sm text-foreground-muted">
            {[
              "Append-only event store with deterministic replay",
              "ERC-721 certificate with vault-attestation transfer gate",
              "HMAC-signed vault webhook + signed audit-trail export",
            ].map((line) => (
              <li key={line} className="flex items-start gap-2">
                <span
                  aria-hidden
                  className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary"
                />
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </main>
  );
}
