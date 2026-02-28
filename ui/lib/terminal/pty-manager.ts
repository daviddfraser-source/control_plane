import path from "path";
import { randomUUID } from "crypto";

export interface PtyEvent {
  seq: number;
  data: string;
}

interface PtyExitInfo {
  exitCode: number;
}

interface PtyProcess {
  onData(handler: (data: string) => void): void;
  onExit(handler: (info: PtyExitInfo) => void): void;
  write(data: string): void;
  resize(cols: number, rows: number): void;
  kill(): void;
}

interface PtySession {
  id: string;
  accessToken: string;
  pty: PtyProcess;
  events: PtyEvent[];
  waiters: Array<() => void>;
  nextSeq: number;
  closed: boolean;
  createdAt: number;
  updatedAt: number;
}

const MAX_EVENTS = 8000;
const SESSION_TTL_MS = 30 * 60 * 1000;
const DEFAULT_COLS = 120;
const DEFAULT_ROWS = 34;

const ROOT_DIR = path.resolve(process.cwd(), "..", "..");
const DEFAULT_CWD = ROOT_DIR;
const NODE_PTY_IMPORT = "node-pty";

let ptySpawn:
  | ((file: string, args?: string[], options?: Record<string, unknown>) => PtyProcess)
  | null
  | undefined;

declare global {
  var __ptySessions: Map<string, PtySession> | undefined;
}

function sessions(): Map<string, PtySession> {
  if (!globalThis.__ptySessions) {
    globalThis.__ptySessions = new Map<string, PtySession>();
  }
  return globalThis.__ptySessions;
}

function appendEvent(session: PtySession, data: string) {
  session.events.push({ seq: session.nextSeq++, data });
  session.updatedAt = Date.now();
  if (session.events.length > MAX_EVENTS) {
    session.events.splice(0, session.events.length - MAX_EVENTS);
  }
  if (session.waiters.length > 0) {
    const waiters = session.waiters.splice(0, session.waiters.length);
    for (const notify of waiters) notify();
  }
}

function sanitizeCwd(input?: string): string {
  if (!input) return DEFAULT_CWD;
  const requested = path.resolve(ROOT_DIR, input);
  if (!requested.startsWith(ROOT_DIR)) {
    return DEFAULT_CWD;
  }
  return requested;
}

async function loadPtySpawn() {
  if (ptySpawn !== undefined) return ptySpawn;
  try {
    const importer = new Function("m", "return import(m)");
    const mod = (await importer(NODE_PTY_IMPORT)) as {
      spawn: (file: string, args?: string[], options?: Record<string, unknown>) => PtyProcess;
    };
    ptySpawn = mod.spawn;
  } catch {
    ptySpawn = null;
  }
  return ptySpawn;
}

function cleanupExpiredSessions() {
  const now = Date.now();
  for (const [id, sess] of sessions().entries()) {
    if (now - sess.updatedAt > SESSION_TTL_MS) {
      try {
        sess.pty.kill();
      } catch {
        // no-op
      }
      sessions().delete(id);
    }
  }
}

export async function createPtySession(options?: { cwd?: string; shell?: string; cols?: number; rows?: number }) {
  cleanupExpiredSessions();
  const spawn = await loadPtySpawn();
  if (!spawn) {
    throw new Error(
      "Terminal backend unavailable (feature not installed). Run `npm run feature:terminal:enable`.",
    );
  }
  const id = randomUUID();
  const shell = options?.shell || process.env.SHELL || "/bin/bash";
  const cwd = sanitizeCwd(options?.cwd);
  const cols = Math.max(40, options?.cols || DEFAULT_COLS);
  const rows = Math.max(10, options?.rows || DEFAULT_ROWS);

  const ptyProc = spawn(shell, ["-l"], {
    name: "xterm-color",
    cols,
    rows,
    cwd,
    env: process.env as Record<string, string>,
  });

  const session: PtySession = {
    id,
    accessToken: randomUUID(),
    pty: ptyProc,
    events: [],
    waiters: [],
    nextSeq: 1,
    closed: false,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  appendEvent(session, `\r\n[system] PTY session started: ${id}\r\n`);

  ptyProc.onData((data) => {
    appendEvent(session, data);
  });

  ptyProc.onExit(({ exitCode }) => {
    session.closed = true;
    appendEvent(session, `\r\n[system] PTY exited (${exitCode})\r\n`);
  });

  sessions().set(id, session);
  return {
    sessionId: id,
    accessToken: session.accessToken,
    nextSeq: session.nextSeq,
    events: session.events,
    cwd,
    shell,
  };
}

export function authorizePtySession(sessionId: string, accessToken: string) {
  const session = sessions().get(sessionId);
  if (!session || !accessToken) return false;
  return session.accessToken === accessToken;
}

export function readPtyStream(sessionId: string, since: number) {
  const session = sessions().get(sessionId);
  if (!session) return { found: false as const };
  session.updatedAt = Date.now();
  const events = session.events.filter((evt) => evt.seq > since);
  return {
    found: true as const,
    events,
    nextSeq: session.nextSeq,
    closed: session.closed,
  };
}

export async function readPtyStreamLongPoll(sessionId: string, since: number, waitMs: number) {
  const session = sessions().get(sessionId);
  if (!session) return { found: false as const };
  session.updatedAt = Date.now();

  const immediate = session.events.filter((evt) => evt.seq > since);
  if (immediate.length > 0 || session.closed || waitMs <= 0) {
    return {
      found: true as const,
      events: immediate,
      nextSeq: session.nextSeq,
      closed: session.closed,
    };
  }

  await new Promise<void>((resolve) => {
    let done = false;
    const complete = () => {
      if (done) return;
      done = true;
      resolve();
    };
    const timeout = setTimeout(complete, waitMs);
    const waiter = () => {
      clearTimeout(timeout);
      complete();
    };
    session.waiters.push(waiter);
  });

  const events = session.events.filter((evt) => evt.seq > since);
  return {
    found: true as const,
    events,
    nextSeq: session.nextSeq,
    closed: session.closed,
  };
}

export function writePtyInput(sessionId: string, data: string) {
  const session = sessions().get(sessionId);
  if (!session || session.closed) return false;
  session.pty.write(data);
  session.updatedAt = Date.now();
  return true;
}

export function resizePty(sessionId: string, cols: number, rows: number) {
  const session = sessions().get(sessionId);
  if (!session || session.closed) return false;
  session.pty.resize(Math.max(20, cols), Math.max(5, rows));
  session.updatedAt = Date.now();
  return true;
}

export function closePtySession(sessionId: string) {
  const session = sessions().get(sessionId);
  if (!session) return false;
  try {
    session.pty.kill();
  } catch {
    // no-op
  }
  if (session.waiters.length > 0) {
    const waiters = session.waiters.splice(0, session.waiters.length);
    for (const notify of waiters) notify();
  }
  sessions().delete(sessionId);
  return true;
}
