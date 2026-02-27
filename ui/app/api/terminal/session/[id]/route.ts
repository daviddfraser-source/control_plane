import { authorizePtySession, closePtySession, readPtyStream, resizePty, writePtyInput } from "@/lib/terminal/pty-manager";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function sleep(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const params = await context.params;
  const id = params.id;
  const url = new URL(request.url);
  const accessToken = request.headers.get("x-substrate-pty-token") || "";
  if (!authorizePtySession(id, accessToken)) {
    return Response.json({ success: false, message: "Unauthorized terminal session" }, { status: 401 });
  }
  const since = Number(url.searchParams.get("since") || "0");
  const wait = Number(url.searchParams.get("wait") || "0");
  const waitMs = Number.isFinite(wait) ? Math.max(0, Math.min(wait, 30000)) : 0;
  const sinceSeq = Number.isFinite(since) ? since : 0;

  const start = Date.now();
  let stream = readPtyStream(id, sinceSeq);
  while (stream.found && waitMs > 0 && !stream.closed && stream.events.length === 0) {
    const elapsed = Date.now() - start;
    if (elapsed >= waitMs) break;
    await sleep(25);
    stream = readPtyStream(id, sinceSeq);
  }

  if (!stream.found) {
    return Response.json({ success: false, message: "Session not found" }, { status: 404 });
  }

  return Response.json({
    success: true,
    events: stream.events,
    nextSeq: stream.nextSeq,
    closed: stream.closed,
  });
}

export async function POST(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const params = await context.params;
  const id = params.id;
  const accessToken = request.headers.get("x-substrate-pty-token") || "";
  if (!authorizePtySession(id, accessToken)) {
    return Response.json({ success: false, message: "Unauthorized terminal session" }, { status: 401 });
  }

  let body: any = {};
  try {
    body = await request.json();
  } catch {
    return Response.json({ success: false, message: "Invalid JSON" }, { status: 400 });
  }

  const op = String(body?.op || "input").toLowerCase();
  if (op === "resize") {
    const cols = Number(body?.cols);
    const rows = Number(body?.rows);
    if (!Number.isFinite(cols) || !Number.isFinite(rows)) {
      return Response.json({ success: false, message: "Invalid cols/rows" }, { status: 400 });
    }
    const ok = resizePty(id, cols, rows);
    if (!ok) {
      return Response.json({ success: false, message: "Session not found or closed" }, { status: 404 });
    }
    return Response.json({ success: true });
  }

  const data = typeof body?.data === "string" ? body.data : "";
  if (!data) {
    return Response.json({ success: false, message: "Missing data" }, { status: 400 });
  }
  const ok = writePtyInput(id, data);
  if (!ok) {
    return Response.json({ success: false, message: "Session not found or closed" }, { status: 404 });
  }
  return Response.json({ success: true });
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const params = await context.params;
  const accessToken = request.headers.get("x-substrate-pty-token") || "";
  if (!authorizePtySession(params.id, accessToken)) {
    return Response.json({ success: false, message: "Unauthorized terminal session" }, { status: 401 });
  }
  const ok = closePtySession(params.id);
  if (!ok) {
    return Response.json({ success: false, message: "Session not found" }, { status: 404 });
  }
  return Response.json({ success: true });
}
