"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Spinner } from "@/components/ui";
import { useAuth } from "@/lib/useAuth";

export function AuthGate({ children }: { children: ReactNode }) {
  const { token, isReady } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isReady && !token) {
      router.replace("/login");
    }
  }, [isReady, token, router]);

  if (!isReady || !token) {
    return (
      <main className="grid min-h-screen place-items-center px-6">
        <div className="flex items-center gap-2 text-sm text-foreground-muted">
          <Spinner />
          <span>{isReady ? "Redirecting…" : "Loading…"}</span>
        </div>
      </main>
    );
  }

  return <>{children}</>;
}
