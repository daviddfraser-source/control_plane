#!/usr/bin/env node

import http from "node:http";
import { spawn } from "node:child_process";

const APP_PORT = Number(process.env.SMOKE_APP_PORT || 3100);
const HOST = "127.0.0.1";
const BASE_URL = `http://${HOST}:${APP_PORT}`;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForServer(url, timeoutMs = 90000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (res.ok) return;
    } catch {
      // wait and retry
    }
    await sleep(1000);
  }
  throw new Error(`Timed out waiting for server: ${url}`);
}

function startAuthMockServer() {
  const server = http.createServer((req, res) => {
    if (req.url === "/api/auth/session") {
      const payload = {
        authenticated: true,
        user: { id: "smoke-user", roles: ["developer"] },
      };
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify(payload));
      return;
    }
    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: "not_found" }));
  });
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    const requestedPort = Number(process.env.SMOKE_AUTH_PORT || 0);
    server.listen(requestedPort, HOST, () => {
      const addr = server.address();
      const port = typeof addr === "object" && addr ? addr.port : requestedPort;
      resolve({ server, baseUrl: `http://${HOST}:${port}` });
    });
  });
}

function startAppServer(governanceApiUrl) {
  const child = spawn("node", ["./node_modules/next/dist/bin/next", "start", "-H", HOST, "-p", String(APP_PORT)], {
    cwd: process.cwd(),
    env: { ...process.env, NODE_ENV: "production", GOVERNANCE_API_URL: governanceApiUrl },
    stdio: ["ignore", "pipe", "pipe"],
  });
  child.stdout.on("data", (chunk) => process.stdout.write(chunk));
  child.stderr.on("data", (chunk) => process.stderr.write(chunk));
  return child;
}

async function run() {
  let authServer;
  let appServer;
  try {
    const auth = await startAuthMockServer();
    authServer = auth.server;
    appServer = startAppServer(auth.baseUrl);
    await waitForServer(`${BASE_URL}/`);

    const itemRes = await fetch(`${BASE_URL}/api/items`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ title: "fallback-check", description: "db should fallback without prisma" }),
    });
    if (itemRes.status !== 201) {
      throw new Error(`Expected 201 from /api/items, got ${itemRes.status}`);
    }
    const itemPayload = await itemRes.json();
    if (typeof itemPayload?.id !== "string" || !itemPayload.id.startsWith("local-")) {
      throw new Error(`Expected fallback local id from /api/items, got: ${JSON.stringify(itemPayload)}`);
    }

    const terminalRes = await fetch(`${BASE_URL}/api/terminal/session`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({}),
    });
    if (terminalRes.status !== 501) {
      throw new Error(`Expected 501 from /api/terminal/session, got ${terminalRes.status}`);
    }
    const terminalPayload = await terminalRes.json();
    const message = String(terminalPayload?.message || "");
    if (!message.includes("feature:terminal:enable")) {
      throw new Error(`Expected terminal fallback guidance, got: ${JSON.stringify(terminalPayload)}`);
    }

    console.log("Optional feature fallback smoke checks passed.");
  } finally {
    if (appServer && !appServer.killed) {
      appServer.kill("SIGTERM");
      await sleep(1000);
      if (!appServer.killed) {
        appServer.kill("SIGKILL");
      }
    }
    if (authServer) {
      await new Promise((resolve) => authServer.close(() => resolve()));
    }
  }
}

run().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
