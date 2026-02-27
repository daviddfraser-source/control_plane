import { readPtyStream } from "@/lib/terminal/pty-manager";
import { requireDeveloper } from "@/lib/terminal/auth";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function sleep(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const auth = await requireDeveloper(request);
  if (!auth.ok) return auth.response;

  const params = await context.params;
  const id = params.id;
  const url = new URL(request.url);
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
