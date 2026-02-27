import { authorizePtySession, resizePty } from "@/lib/terminal/pty-manager";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const params = await context.params;
  const accessToken = request.headers.get("x-substrate-pty-token") || "";
  if (!authorizePtySession(params.id, accessToken)) {
    return Response.json({ success: false, message: "Unauthorized terminal session" }, { status: 401 });
  }
  let body: any = {};
  try {
    body = await request.json();
  } catch {
    return Response.json({ success: false, message: "Invalid JSON" }, { status: 400 });
  }

  const cols = Number(body?.cols);
  const rows = Number(body?.rows);
  if (!Number.isFinite(cols) || !Number.isFinite(rows)) {
    return Response.json({ success: false, message: "Invalid cols/rows" }, { status: 400 });
  }

  const ok = resizePty(params.id, cols, rows);
  if (!ok) {
    return Response.json({ success: false, message: "Session not found or closed" }, { status: 404 });
  }

  return Response.json({ success: true });
}
