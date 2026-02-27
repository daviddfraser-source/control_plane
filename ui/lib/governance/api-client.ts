/**
 * Typed fetch wrappers for the Python governance backend API.
 *
 * Base URL is configurable via the GOVERNANCE_API_URL environment variable.
 * If unset, the client auto-uses the current browser hostname on port 8080
 * so auth cookies remain same-site (localhost vs 127.0.0.1 mismatch safe).
 *
 * All functions throw on network errors and return typed response objects.
 */

import type { PacketStatus } from "./types";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

function getDefaultBaseUrl(): string {
  if (typeof window !== "undefined" && window.location?.hostname) {
    return `${window.location.protocol}//${window.location.hostname}:8080`;
  }
  return "http://127.0.0.1:8080";
}

const BASE_URL: string =
  typeof process !== "undefined" && process.env?.GOVERNANCE_API_URL
    ? process.env.GOVERNANCE_API_URL
    : getDefaultBaseUrl();

// ---------------------------------------------------------------------------
// Response types — GET endpoints
// ---------------------------------------------------------------------------

export interface SessionUser {
  name: string;
  email: string;
  role: string;
  roles: string[];
}

export interface AuthSessionResponse {
  success: boolean;
  authenticated: boolean;
  user?: SessionUser;
}

export interface StatusPacket {
  id: string;
  wbs_ref: string;
  title: string;
  scope: string;
  status: PacketStatus;
  assigned_to: string | null;
  notes: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface StatusArea {
  id: string;
  title: string;
  description: string;
  packets: StatusPacket[];
  closeout: Record<string, unknown> | null;
}

export interface StatusResponse {
  metadata: Record<string, unknown>;
  areas: StatusArea[];
  area_closeouts: Record<string, unknown>;
  dependencies: Record<string, string[]>;
  counts: Record<string, number>;
  timestamp: string;
}

export interface ReadyPacket {
  id: string;
  wbs_ref: string;
  title: string;
}

export interface ReadyResponse {
  ready: ReadyPacket[];
}

export interface ProgressCounts {
  pending: number;
  in_progress: number;
  done: number;
  failed: number;
  blocked: number;
}

export interface ProgressResponse {
  counts: ProgressCounts;
  total: number;
}

export interface LogEntry {
  packet_id: string;
  event: string;
  agent: string;
  timestamp: string;
  notes?: string;
  [key: string]: unknown;
}

export interface LogResponse {
  log: LogEntry[];
}

export interface PacketDocument {
  path: string;
  exists: boolean;
}

export interface PacketDetail {
  id: string;
  wbs_ref: string;
  area_id: string;
  area_title: string;
  title: string;
  scope: string;
  status: PacketStatus;
  assigned_to: string | null;
  started_at: string | null;
  completed_at: string | null;
  notes: string | null;
  dependencies: string[];
  dependents: string[];
}

export interface PacketResponse {
  success: boolean;
  packet: PacketDetail;
  packet_definition: Record<string, unknown>;
  events: LogEntry[];
  documents: PacketDocument[];
}

export interface DepsGraphNode {
  id: string;
  title: string;
  wbs_ref: string;
  status: PacketStatus;
}

export interface DepsGraphEdge {
  from: string;
  to: string;
}

export interface DepsGraphResponse {
  nodes: DepsGraphNode[];
  edges: DepsGraphEdge[];
}

export interface DocsDocument {
  path: string;
  name: string;
  title: string;
  summary: string;
  category: string;
  kind: string;
  ext: string;
  size: number;
  updated_at: string;
}

export interface DocsIndexResponse {
  success: boolean;
  documents: DocsDocument[];
  categories: string[];
  kinds: string[];
  total: number;
  returned: number;
  query: {
    q: string;
    kind: string;
    category: string;
    limit: number;
  };
}

export interface TerminalMetrics {
  terminal_commands_total: number;
  terminal_failures_total: number;
  terminal_latency_avg_ms: number;
  terminal_latency_p95_ms: number;
  terminal_sandbox_mode: string;
}

export interface TerminalMetricsResponse {
  success: boolean;
  metrics: TerminalMetrics;
}

// ---------------------------------------------------------------------------
// Response types — POST endpoints
// ---------------------------------------------------------------------------

export interface AuthLoginResponse {
  success: boolean;
  authenticated: boolean;
  user?: SessionUser;
  message?: string;
}

export interface AuthLogoutResponse {
  success: boolean;
  authenticated: boolean;
}

export interface MutationResponse {
  success: boolean;
  message: string;
}

export interface TerminalExecuteResponse {
  success: boolean;
  output: string;
  exit_code: number;
  entry: Record<string, unknown>;
  sandbox_mode: string;
  message?: string;
}

// ---------------------------------------------------------------------------
// Request body types — POST endpoints
// ---------------------------------------------------------------------------

export interface LoginBody {
  name: string;
  email: string;
  password: string;
}

export interface ClaimBody {
  packet_id: string;
  agent_name: string;
}

export interface DoneBody {
  packet_id: string;
  agent_name: string;
  notes: string;
  residual_risk_ack: "none" | "declared";
  residual_risk_json?: Record<string, unknown> | Record<string, unknown>[];
}

export interface FailBody {
  packet_id: string;
  agent_name: string;
  reason: string;
}

export interface NoteBody {
  packet_id: string;
  agent_name: string;
  notes: string;
}

export interface ResetBody {
  packet_id: string;
}

export interface AddPacketBody {
  area_id: string;
  title: string;
  scope?: string;
  id?: string;
  wbs_ref?: string;
}

export interface AddAreaBody {
  id: string;
  title: string;
  description?: string;
}

export interface TerminalExecuteBody {
  command: string;
}

export interface CloseoutL2Body {
  area_id: string;
  agent_name: string;
  assessment_path: string;
  notes?: string;
}

// ---------------------------------------------------------------------------
// Docs index query parameters
// ---------------------------------------------------------------------------

export interface DocsIndexParams {
  q?: string;
  kind?: string;
  category?: string;
  limit?: number;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "GET",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (res.status === 401) {
    throw new Error("Authentication required. Open Settings and sign in.");
  }
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    throw new Error("Authentication required. Open Settings and sign in.");
  }
  if (!res.ok) {
    throw new Error(`POST ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

function qs(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(
    (kv): kv is [string, string | number] => kv[1] !== undefined,
  );
  if (entries.length === 0) return "";
  return "?" + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");
}

// ---------------------------------------------------------------------------
// GET endpoints
// ---------------------------------------------------------------------------

/** GET /api/auth/session - Check current authentication state. */
export function fetchAuthSession(): Promise<AuthSessionResponse> {
  return get<AuthSessionResponse>("/api/auth/session");
}

/** GET /api/status - Full dashboard state (areas, packets, counts, deps). */
export function fetchStatus(): Promise<StatusResponse> {
  return get<StatusResponse>("/api/status");
}

/** GET /api/ready - Packets that are pending and dependency-ready. */
export function fetchReady(): Promise<ReadyResponse> {
  return get<ReadyResponse>("/api/ready");
}

/** GET /api/progress - Aggregate packet status counts. */
export function fetchProgress(): Promise<ProgressResponse> {
  return get<ProgressResponse>("/api/progress");
}

/** GET /api/log?limit=N - Recent lifecycle log entries. */
export function fetchLog(limit: number = 20): Promise<LogResponse> {
  return get<LogResponse>(`/api/log${qs({ limit })}`);
}

/** GET /api/packet?id=X - Full packet detail with events and documents. */
export function fetchPacket(id: string): Promise<PacketResponse> {
  return get<PacketResponse>(`/api/packet${qs({ id })}`);
}

/** GET /api/deps-graph - Dependency graph nodes and edges. */
export function fetchDepsGraph(): Promise<DepsGraphResponse> {
  return get<DepsGraphResponse>("/api/deps-graph");
}

/** GET /api/docs-index - Project documentation index with optional filters. */
export function fetchDocsIndex(params: DocsIndexParams = {}): Promise<DocsIndexResponse> {
  return get<DocsIndexResponse>(`/api/docs-index${qs(params as Record<string, string | number | undefined>)}`);
}

/** GET /api/terminal/metrics - Terminal command execution metrics. */
export function fetchTerminalMetrics(): Promise<TerminalMetricsResponse> {
  return get<TerminalMetricsResponse>("/api/terminal/metrics");
}

// ---------------------------------------------------------------------------
// POST endpoints
// ---------------------------------------------------------------------------

/** POST /api/auth/login - Authenticate a user. */
export function login(body: LoginBody): Promise<AuthLoginResponse> {
  return post<AuthLoginResponse>("/api/auth/login", body);
}

/** POST /api/auth/logout - End the current session. */
export function logout(): Promise<AuthLogoutResponse> {
  return post<AuthLogoutResponse>("/api/auth/logout", {});
}

/** POST /api/claim - Claim a packet for an agent. */
export function claimPacket(body: ClaimBody): Promise<MutationResponse> {
  return post<MutationResponse>("/api/claim", body);
}

/** POST /api/done - Mark a packet as done with evidence. */
export function completePacket(body: DoneBody): Promise<MutationResponse> {
  return post<MutationResponse>("/api/done", body);
}

/** POST /api/fail - Mark a packet as failed with a reason. */
export function failPacket(body: FailBody): Promise<MutationResponse> {
  return post<MutationResponse>("/api/fail", body);
}

/** POST /api/note - Add a note to a packet. */
export function addNote(body: NoteBody): Promise<MutationResponse> {
  return post<MutationResponse>("/api/note", body);
}

/** POST /api/reset - Reset a packet to pending. */
export function resetPacket(body: ResetBody): Promise<MutationResponse> {
  return post<MutationResponse>("/api/reset", body);
}

/** POST /api/add-packet - Add a new packet to a work area. */
export function addPacket(body: AddPacketBody): Promise<MutationResponse> {
  return post<MutationResponse>("/api/add-packet", body);
}

/** POST /api/add-area - Add a new work area. */
export function addArea(body: AddAreaBody): Promise<MutationResponse> {
  return post<MutationResponse>("/api/add-area", body);
}

/** POST /api/terminal/execute - Execute a terminal command. */
export function executeTerminalCommand(body: TerminalExecuteBody): Promise<TerminalExecuteResponse> {
  return post<TerminalExecuteResponse>("/api/terminal/execute", body);
}

/** POST /api/closeout-l2 - Close out a level-2 work area. */
export function closeoutL2(body: CloseoutL2Body): Promise<MutationResponse> {
  return post<MutationResponse>("/api/closeout-l2", body);
}
