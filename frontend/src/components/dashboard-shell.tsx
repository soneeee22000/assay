"use client";

import {
  type LucideIcon,
  Award,
  BookOpen,
  LogOut,
  Workflow,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode } from "react";

import { BrandMark, Button } from "@/components/ui";
import { cn } from "@/lib/cn";
import { useAuth } from "@/lib/useAuth";

type NavItem = { href: string; label: string; icon: LucideIcon };

const NAV: NavItem[] = [
  { href: "/ledger", label: "Ledger", icon: BookOpen },
  { href: "/escrows", label: "Escrows", icon: Workflow },
  { href: "/certificates", label: "Certificates", icon: Award },
];

export function DashboardShell({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const { signOut } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-20 border-b border-border bg-surface/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link
            href="/"
            className="rounded-md transition-opacity hover:opacity-80"
          >
            <BrandMark />
          </Link>

          <nav className="hidden items-center gap-1 sm:flex">
            {NAV.map((item) => {
              const active = pathname?.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150",
                    active
                      ? "bg-primary-soft text-primary-soft-foreground"
                      : "text-foreground-muted hover:bg-muted hover:text-foreground",
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <Button
            variant="ghost"
            size="sm"
            leadingIcon={LogOut}
            onClick={signOut}
            aria-label="Sign out"
          >
            <span className="hidden sm:inline">Sign out</span>
          </Button>
        </div>

        <nav className="flex gap-1 overflow-x-auto border-t border-border px-4 py-2 sm:hidden">
          {NAV.map((item) => {
            const active = pathname?.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "inline-flex shrink-0 items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150",
                  active
                    ? "bg-primary-soft text-primary-soft-foreground"
                    : "text-foreground-muted hover:bg-muted hover:text-foreground",
                )}
              >
                <Icon className="h-4 w-4" aria-hidden />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-10">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between sm:gap-6">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
              {title}
            </h1>
            {description ? (
              <p className="max-w-2xl text-sm text-foreground-muted">
                {description}
              </p>
            ) : null}
          </div>
          {actions ? (
            <div className="flex shrink-0 gap-2">{actions}</div>
          ) : null}
        </div>

        {children}

        <footer className="mt-12 border-t border-border pt-4 font-mono text-[11px] text-foreground-subtle">
          Read-only · powered by the Assay FastAPI backend ·{" "}
          <a
            href="https://github.com/soneeee22000/assay"
            target="_blank"
            rel="noopener noreferrer"
            className="text-foreground-muted hover:text-foreground"
          >
            github.com/soneeee22000/assay
          </a>
        </footer>
      </main>
    </div>
  );
}
