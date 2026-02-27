import { createPtySession } from "@/lib/terminal/pty-manager";
import { requireDeveloper } from "@/lib/terminal/auth";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const auth = await requireDeveloper(request);
  if (!auth.ok) return auth.response;

  let body: any = {};
  try {
    body = await request.json();
  } catch {
    // no-op
  }

  let sess;
  try {
    sess = await createPtySession({
      cwd: typeof body?.cwd === "string" ? body.cwd : undefined,
      shell: typeof body?.shell === "string" ? body.shell : undefined,
      cols: typeof body?.cols === "number" ? body.cols : undefined,
      rows: typeof body?.rows === "number" ? body.rows : undefined,
    });
  } catch (error) {
    return Response.json(
      {
        success: false,
        message: error instanceof Error ? error.message : "Failed to initialize terminal backend",
      },
      { status: 501 },
    );
  }

  return Response.json({
    success: true,
    sessionId: sess.sessionId,
    accessToken: sess.accessToken,
    events: sess.events,
    nextSeq: sess.nextSeq,
    cwd: sess.cwd,
    shell: sess.shell,
  });
}
