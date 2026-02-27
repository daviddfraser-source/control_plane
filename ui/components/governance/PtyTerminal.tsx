"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type StreamEvent = { seq: number; data: string };

interface SessionCreateResponse {
  success: boolean;
  sessionId: string;
  accessToken: string;
  events: StreamEvent[];
  nextSeq: number;
  cwd: string;
  shell: string;
}

export function PtyTerminal() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const terminalRef = useRef<any | null>(null);
  const fitAddonRef = useRef<any | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const accessTokenRef = useRef<string>("");
  const nextSeqRef = useRef<number>(0);
  const pollBusyRef = useRef(false);
  const stoppedRef = useRef(false);
  const inputBufferRef = useRef("");
  const inputFlushTimerRef = useRef<number | null>(null);
  const inputSendingRef = useRef(false);
  const inputFlushPendingRef = useRef(false);

  const [status, setStatus] = useState<"connecting" | "connected" | "closed" | "error">("connecting");
  const [meta, setMeta] = useState<{ cwd: string; shell: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const stopPolling = useCallback(() => {
    stoppedRef.current = true;
    inputSendingRef.current = false;
    inputFlushPendingRef.current = false;
    if (inputFlushTimerRef.current) {
      window.clearTimeout(inputFlushTimerRef.current);
      inputFlushTimerRef.current = null;
    }
  }, []);

  const closeSession = useCallback(async () => {
    stopPolling();
    const id = sessionIdRef.current;
    if (!id) return;
    sessionIdRef.current = null;
    const accessToken = accessTokenRef.current;
    accessTokenRef.current = "";
    try {
      await fetch(`/api/terminal/session/${id}`, {
        method: "DELETE",
        headers: { "x-substrate-pty-token": accessToken },
      });
    } catch {
      // no-op
    }
  }, [stopPolling]);

  const sendInputChunk = useCallback(async (data: string) => {
    const id = sessionIdRef.current;
    const accessToken = accessTokenRef.current;
    if (!id) return;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 4000);
    try {
      await fetch(`/api/terminal/session/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-substrate-pty-token": accessToken },
        body: JSON.stringify({ op: "input", data }),
        signal: controller.signal,
      });
    } catch {
      // no-op
    } finally {
      window.clearTimeout(timeout);
    }
  }, []);

  const flushBufferedInput = useCallback(async () => {
    inputFlushTimerRef.current = null;
    if (inputSendingRef.current) {
      inputFlushPendingRef.current = true;
      return;
    }
    inputSendingRef.current = true;
    try {
      while (true) {
        const chunk = inputBufferRef.current;
        inputBufferRef.current = "";
        if (!chunk) break;
        await sendInputChunk(chunk);
      }
    } finally {
      inputSendingRef.current = false;
      if (inputFlushPendingRef.current || inputBufferRef.current) {
        inputFlushPendingRef.current = false;
        void flushBufferedInput();
      }
    }
  }, [sendInputChunk]);

  const writeInput = useCallback((data: string) => {
    inputBufferRef.current += data;
    // Coalesce keystrokes to avoid per-key HTTP pressure while keeping interaction responsive.
    if (!inputFlushTimerRef.current) {
      inputFlushTimerRef.current = window.setTimeout(() => {
        void flushBufferedInput();
      }, 33);
    }
  }, [flushBufferedInput]);

  const sendResize = useCallback(async () => {
    const id = sessionIdRef.current;
    const accessToken = accessTokenRef.current;
    const term = terminalRef.current;
    if (!id || !term) return;
    try {
      await fetch(`/api/terminal/session/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-substrate-pty-token": accessToken },
        body: JSON.stringify({ op: "resize", cols: term.cols, rows: term.rows }),
      });
    } catch {
      // no-op
    }
  }, []);

  const prewarmInputRoute = useCallback(async () => {
    const id = sessionIdRef.current;
    const accessToken = accessTokenRef.current;
    if (!id) return;
    try {
      await fetch(`/api/terminal/session/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-substrate-pty-token": accessToken },
        // Intentionally empty payload to force route compile on first connect in dev mode.
        body: JSON.stringify({ op: "input", data: "" }),
      });
    } catch {
      // no-op
    }
  }, []);

  const pollStream = useCallback(async () => {
    const id = sessionIdRef.current;
    const accessToken = accessTokenRef.current;
    const term = terminalRef.current;
    if (!id || !term || pollBusyRef.current) return;
    pollBusyRef.current = true;
    try {
      const res = await fetch(`/api/terminal/session/${id}?since=${nextSeqRef.current}&wait=25000`, {
        cache: "no-store",
        headers: { "x-substrate-pty-token": accessToken },
      });
      if (!res.ok) {
        if (res.status === 401 || res.status === 403) {
          setStatus("error");
          setError("Authentication required. Open Settings and sign in as Developer/Admin.");
        } else if (res.status === 404) {
          setStatus("closed");
        }
        return;
      }
      const payload = await res.json();
      const events: StreamEvent[] = payload.events || [];
      for (const evt of events) {
        term.write(evt.data);
      }
      nextSeqRef.current = payload.nextSeq || nextSeqRef.current;
      if (payload.closed) {
        setStatus("closed");
        stopPolling();
      }
    } catch {
      if (!stoppedRef.current) {
        setStatus("error");
        setError("Terminal stream disconnected.");
        stopPolling();
      }
    } finally {
      pollBusyRef.current = false;
    }
  }, [stopPolling]);

  const runPollLoop = useCallback(async () => {
    while (!stoppedRef.current && sessionIdRef.current) {
      await pollStream();
    }
  }, [pollStream]);

  const connect = useCallback(async () => {
    setError(null);
    setStatus("connecting");
    await closeSession();
    stoppedRef.current = false;

    const term = terminalRef.current;
    const fit = fitAddonRef.current;
    if (!term || !fit) return;
    term.clear();
    term.writeln("\x1b[90m[system] connecting to PTY...\x1b[0m");

    try {
      fit.fit();
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 6000);
      let res: Response;
      try {
        res = await fetch("/api/terminal/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cols: term.cols, rows: term.rows }),
          signal: controller.signal,
        });
      } finally {
        window.clearTimeout(timeout);
      }
      if (!res.ok) {
        let apiMessage = "";
        try {
          const payload = await res.json();
          apiMessage = typeof payload?.message === "string" ? payload.message : "";
        } catch {
          // no-op
        }
        const message = res.status === 401 || res.status === 403
          ? "Authentication required. Open Settings and sign in as Developer/Admin."
          : apiMessage || `Failed to start terminal (${res.status})`;
        setStatus("error");
        setError(message);
        term.writeln(`\r\n\x1b[31m[error] ${message}\x1b[0m`);
        return;
      }
      const payload: SessionCreateResponse = await res.json();
      sessionIdRef.current = payload.sessionId;
      accessTokenRef.current = payload.accessToken;
      nextSeqRef.current = payload.nextSeq || 0;
      setMeta({ cwd: payload.cwd, shell: payload.shell });
      setStatus("connected");

      for (const evt of payload.events || []) {
        term.write(evt.data);
      }

      void runPollLoop();

      await sendResize();
      void prewarmInputRoute();
    } catch {
      setStatus("error");
      setError("Failed to connect terminal session.");
      term.writeln("\r\n\x1b[31m[error] Failed to connect terminal session.\x1b[0m");
    }
  }, [closeSession, prewarmInputRoute, runPollLoop, sendResize]);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;
    let disposed = false;
    let onDataDisposable: { dispose: () => void } | null = null;
    let onWindowResize: (() => void) | null = null;
    let term: any;

    (async () => {
      const xtermMod = await import("@xterm/xterm");
      const fitMod = await import("@xterm/addon-fit");
      if (disposed) return;

      term = new xtermMod.Terminal({
        cursorBlink: true,
        convertEol: false,
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        fontSize: 13,
        lineHeight: 1.3,
        theme: {
          background: "#0b1020",
          foreground: "#d6def8",
          cursor: "#94a3b8",
        },
      });
      const fit = new fitMod.FitAddon();
      term.loadAddon(fit);
      term.open(node);
      fit.fit();

      onDataDisposable = term.onData((data: string) => {
        writeInput(data);
      });

      terminalRef.current = term;
      fitAddonRef.current = fit;
      void connect();

      onWindowResize = () => {
        fit.fit();
        void sendResize();
      };
      window.addEventListener("resize", onWindowResize);
    })();

    return () => {
      disposed = true;
      if (onWindowResize) window.removeEventListener("resize", onWindowResize);
      if (onDataDisposable) onDataDisposable.dispose();
      void flushBufferedInput();
      void closeSession();
      if (term) term.dispose();
      terminalRef.current = null;
      fitAddonRef.current = null;
    };
  }, [closeSession, connect, flushBufferedInput, sendResize, writeInput]);

  return (
    <div className="h-full flex flex-col bg-token-elevated border border-token-border-default rounded-lg overflow-hidden">
      <div className="px-3 py-2 border-b border-token-border-default bg-token-inset flex items-center justify-between gap-3">
        <div className="text-xs text-token-secondary">
          <span className="mr-3">Status: <strong className="text-token-primary">{status}</strong></span>
          {meta && (
            <span className="mr-3">Shell: <strong className="text-token-primary font-mono">{meta.shell}</strong></span>
          )}
          {meta && (
            <span>CWD: <strong className="text-token-primary font-mono">{meta.cwd}</strong></span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              terminalRef.current?.clear();
            }}
            className="px-2 py-1 text-xs bg-token-canvas border border-token-border-default rounded text-token-secondary hover:text-token-primary"
          >
            Clear
          </button>
          <button
            onClick={() => void connect()}
            className="px-2 py-1 text-xs bg-token-primary text-white rounded"
          >
            Reconnect
          </button>
        </div>
      </div>
      {error && (
        <div className="px-3 py-2 text-xs text-status-danger border-b border-token-border-default">
          {error}
        </div>
      )}
      <div ref={containerRef} className="flex-1 min-h-[500px]" />
    </div>
  );
}
