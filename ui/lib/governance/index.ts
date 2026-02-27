/**
 * Governance library barrel export.
 *
 * Re-exports all governance types, utilities, and API client functions
 * for convenient single-import usage:
 *
 *   import { fetchStatus, buildTree, PacketStatus } from "@/lib/governance";
 */

// Types and core interfaces
export type {
  PacketStatus,
  WbsPacketRow,
  RolePermissions,
} from "./types";

// Grid configuration
export {
  STATUS_HEATMAP_COLORS,
  WBS_GRID_COLUMNS,
  buildQuickFilterValue,
} from "./grid-config";

// Grid actions (inline edit & bulk operations)
export type { BulkActionRequest } from "./grid-actions";
export {
  canEditCell,
  applyInlineEdit,
  applyBulkAction,
} from "./grid-actions";

// Tree grid hierarchy
export type { TreeNode } from "./tree-grid";
export { buildTree } from "./tree-grid";

// Dependency graph analysis
export type { DependencyEdge, GraphNodeState } from "./dependency-graph";
export {
  detectCycles,
  buildGraphNodeState,
  resolvePacketNavigation,
} from "./dependency-graph";

// Audit viewer
export type { AuditFilter, AuditRow } from "./audit-viewer";
export { buildAuditQueryParams } from "./audit-viewer";

// Risk register
export type { RiskGridRow, RiskFilter } from "./risk-register";
export { filterRiskRows, linkedPacketPath } from "./risk-register";

// Optional shell hook system
export type { OptionalShellConfig, ShellHookContext, ShellHook } from "./shell";
export { OptionalShell } from "./shell";

// API client — response types
export type {
  SessionUser,
  AuthSessionResponse,
  StatusPacket,
  StatusArea,
  StatusResponse,
  ReadyPacket,
  ReadyResponse,
  ProgressCounts,
  ProgressResponse,
  LogEntry,
  LogResponse,
  PacketDocument,
  PacketDetail,
  PacketResponse,
  DepsGraphNode,
  DepsGraphEdge,
  DepsGraphResponse,
  DocsDocument,
  DocsIndexResponse,
  TerminalMetrics,
  TerminalMetricsResponse,
  AuthLoginResponse,
  AuthLogoutResponse,
  MutationResponse,
  TerminalExecuteResponse,
} from "./api-client";

// API client — request body types
export type {
  LoginBody,
  ClaimBody,
  DoneBody,
  FailBody,
  NoteBody,
  ResetBody,
  AddPacketBody,
  AddAreaBody,
  TerminalExecuteBody,
  CloseoutL2Body,
  DocsIndexParams,
} from "./api-client";

// API client — fetch functions
export {
  fetchAuthSession,
  fetchStatus,
  fetchReady,
  fetchProgress,
  fetchLog,
  fetchPacket,
  fetchDepsGraph,
  fetchDocsIndex,
  fetchTerminalMetrics,
  login,
  logout,
  claimPacket,
  completePacket,
  failPacket,
  addNote,
  resetPacket,
  addPacket,
  addArea,
  executeTerminalCommand,
  closeoutL2,
} from "./api-client";
