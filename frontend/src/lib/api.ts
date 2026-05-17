const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const TOKEN_STORAGE_KEY = "assay_jwt";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(`API ${status}: ${detail}`);
  }
}

type FetchOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  authenticated?: boolean;
};

export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (options.authenticated !== false) {
    const token = getStoredToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const problem = await response.json();
      detail = problem.detail ?? problem.title ?? detail;
    } catch {
      // body wasn't JSON, keep the statusText
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export type LoginRequest = { email: string; password: string };
export type AuthToken = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type DomainEvent = {
  event_id: string;
  stream_id: string;
  stream_type: string;
  version: number;
  event_type: string;
  payload: Record<string, unknown>;
  correlation_id: string;
  ts: string;
};

export type AuditExport = {
  from: string;
  to: string;
  count: number;
  events: DomainEvent[];
};

export type Escrow = {
  escrow_id: string;
  buyer_id: string;
  seller_id: string;
  asset_id: string;
  amount_usdc: string;
  state:
    | "PENDING"
    | "FUNDS_LOCKED"
    | "VAULT_ATTESTED"
    | "CERTIFICATE_MINTED"
    | "RELEASED"
    | "CANCELLED"
    | "REFUNDED";
  opened_at: string;
  locked_at: string | null;
  attested_at: string | null;
  minted_at: string | null;
  released_at: string | null;
};

export async function login(body: LoginRequest): Promise<AuthToken> {
  return apiFetch<AuthToken>("/api/v1/auth/login", {
    method: "POST",
    body,
    authenticated: false,
  });
}

export async function fetchAuditExport(params: {
  from: string;
  to: string;
}): Promise<AuditExport> {
  const search = new URLSearchParams({ from: params.from, to: params.to });
  return apiFetch<AuditExport>(`/api/v1/audit/export?${search.toString()}`);
}

export async function fetchEscrow(escrowId: string): Promise<Escrow> {
  return apiFetch<Escrow>(`/api/v1/escrows/${escrowId}`);
}

export async function fetchHealth(): Promise<{
  status: string;
  version: string;
}> {
  return apiFetch("/health", { authenticated: false });
}
