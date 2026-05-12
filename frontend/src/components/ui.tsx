"use client";

import { type LucideIcon } from "lucide-react";
import {
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type ReactNode,
} from "react";

import { cn } from "@/lib/cn";

/* ──────────────────────────── Button ──────────────────────────── */

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

const BUTTON_VARIANTS: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-primary-foreground hover:bg-primary-hover shadow-sm",
  secondary:
    "bg-surface text-foreground border border-border hover:border-border-strong hover:bg-muted",
  ghost:
    "bg-transparent text-foreground-muted hover:bg-muted hover:text-foreground",
  danger: "bg-danger text-white hover:opacity-90 shadow-sm",
};

const BUTTON_SIZES: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  lg: "h-11 px-5 text-base gap-2",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leadingIcon?: LucideIcon;
  trailingIcon?: LucideIcon;
};

export function Button({
  variant = "primary",
  size = "md",
  leadingIcon: LeadingIcon,
  trailingIcon: TrailingIcon,
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors duration-150 focus-visible:outline-none disabled:opacity-50 disabled:pointer-events-none",
        BUTTON_VARIANTS[variant],
        BUTTON_SIZES[size],
        className,
      )}
    >
      {LeadingIcon ? <LeadingIcon className="h-4 w-4" aria-hidden /> : null}
      {children}
      {TrailingIcon ? <TrailingIcon className="h-4 w-4" aria-hidden /> : null}
    </button>
  );
}

/* ──────────────────────────── Badge ──────────────────────────── */

type BadgeTone =
  | "neutral"
  | "primary"
  | "accent"
  | "success"
  | "warning"
  | "danger";

const BADGE_TONES: Record<BadgeTone, string> = {
  neutral: "bg-muted text-foreground-muted border-border",
  primary: "bg-primary-soft text-primary-soft-foreground border-primary-soft",
  accent: "bg-accent-soft text-accent-soft-foreground border-accent-soft",
  success: "bg-success-soft text-success border-success-soft",
  warning: "bg-warning-soft text-warning border-warning-soft",
  danger: "bg-danger-soft text-danger border-danger-soft",
};

export function Badge({
  tone = "neutral",
  className,
  children,
}: {
  tone?: BadgeTone;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-wider",
        BADGE_TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/* ──────────────────────────── Card ──────────────────────────── */

export function Card({
  className,
  children,
  ...rest
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...rest}
      className={cn(
        "rounded-lg border border-border bg-surface shadow-xs transition-shadow",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-between border-b border-border px-4 py-3",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardBody({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={cn("px-4 py-3", className)}>{children}</div>;
}

/* ──────────────────────────── KpiCard ──────────────────────────── */

export function KpiCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "primary",
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon?: LucideIcon;
  tone?: "primary" | "accent" | "success" | "neutral";
}) {
  const toneClasses: Record<typeof tone, string> = {
    primary: "text-primary bg-primary-soft",
    accent: "text-accent-soft-foreground bg-accent-soft",
    success: "text-success bg-success-soft",
    neutral: "text-foreground-muted bg-muted",
  };

  return (
    <Card className="overflow-hidden">
      <div className="flex items-start justify-between gap-3 p-4">
        <div className="space-y-1.5">
          <p className="font-mono text-[10px] uppercase tracking-wider text-foreground-muted">
            {label}
          </p>
          <p className="font-mono text-2xl font-semibold tabular-nums tracking-tight text-foreground">
            {value}
          </p>
          {hint ? (
            <p className="text-xs text-foreground-muted">{hint}</p>
          ) : null}
        </div>
        {Icon ? (
          <div
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-md",
              toneClasses[tone],
            )}
          >
            <Icon className="h-4 w-4" aria-hidden />
          </div>
        ) : null}
      </div>
    </Card>
  );
}

/* ──────────────────────────── EmptyState ──────────────────────────── */

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: ReactNode;
  action?: ReactNode;
}) {
  return (
    <Card className="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center">
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-primary-soft text-primary">
        <Icon className="h-5 w-5" aria-hidden />
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <div className="max-w-md text-sm text-foreground-muted">
        {description}
      </div>
      {action ? <div className="mt-2">{action}</div> : null}
    </Card>
  );
}

/* ──────────────────────────── Spinner ──────────────────────────── */

export function Spinner({ className }: { className?: string }) {
  return (
    <svg
      role="status"
      aria-label="Loading"
      viewBox="0 0 24 24"
      className={cn("h-4 w-4 animate-spin text-foreground-muted", className)}
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeOpacity="0.2"
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M22 12a10 10 0 0 0-10-10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

/* ──────────────────────────── LoadingRow ──────────────────────────── */

export function LoadingRow({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-sm text-foreground-muted">
      <Spinner />
      <span>{label}</span>
    </div>
  );
}

/* ──────────────────────────── ErrorRow ──────────────────────────── */

export function ErrorRow({ title, detail }: { title: string; detail: string }) {
  return (
    <Card className="border-danger-soft bg-danger-soft/60 px-4 py-3">
      <p className="text-sm font-medium text-danger">{title}</p>
      <p className="mt-1 font-mono text-xs text-danger/80">{detail}</p>
    </Card>
  );
}

/* ──────────────────────────── Brand mark ──────────────────────────── */

export function BrandMark({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 font-mono text-sm font-semibold tracking-tight",
        className,
      )}
    >
      <span
        aria-hidden
        className="grid h-7 w-7 place-items-center rounded-md bg-primary text-primary-foreground shadow-sm"
      >
        <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5">
          <path
            d="M12 2L4 9l8 13 8-13-8-7z"
            fill="currentColor"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinejoin="round"
          />
          <path
            d="M4 9l8 4 8-4M12 13v9"
            stroke="oklch(1 0 0 / 0.45)"
            strokeWidth="1.2"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span className="text-foreground">GemVault</span>
    </div>
  );
}
