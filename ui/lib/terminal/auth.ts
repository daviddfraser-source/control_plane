export async function requireDeveloper(request: Request): Promise<{ ok: true } | { ok: false; response: Response }> {
  const cookie = request.headers.get("cookie") || "";
  const host = (request.headers.get("host") || "127.0.0.1").split(":")[0].trim().toLowerCase();

  const candidates: string[] = [];
  if (process.env.GOVERNANCE_API_URL) candidates.push(process.env.GOVERNANCE_API_URL);
  if (host === "localhost" || host === "::1" || host === "[::1]") candidates.push("http://127.0.0.1:8080");
  if (host) candidates.push(`http://${host}:8080`);
  if (!candidates.includes("http://127.0.0.1:8080")) candidates.push("http://127.0.0.1:8080");

  let payload: any = null;
  let reachable = false;
  for (const base of candidates) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2500);
    try {
      const res = await fetch(`${base}/api/auth/session`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          Cookie: cookie,
        },
        cache: "no-store",
        signal: controller.signal,
      });
      reachable = true;
      payload = await res.json();
      break;
    } catch {
      // Try the next candidate.
    } finally {
      clearTimeout(timeout);
    }
  }

  if (!reachable) {
    return {
      ok: false,
      response: Response.json({ success: false, message: "Auth backend unavailable" }, { status: 503 }),
    };
  }

  if (!payload?.authenticated || !payload?.user) {
    return {
      ok: false,
      response: Response.json({ success: false, message: "Authentication required" }, { status: 401 }),
    };
  }

  const roles = (payload.user.roles || []).map((r: string) => String(r).toLowerCase());
  if (!roles.includes("developer") && !roles.includes("admin")) {
    return {
      ok: false,
      response: Response.json({ success: false, message: "Developer role required" }, { status: 403 }),
    };
  }

  return { ok: true };
}
