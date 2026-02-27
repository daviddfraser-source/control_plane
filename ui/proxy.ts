import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

function isDevControlPlaneEnabled(): boolean {
  return (
    process.env.NODE_ENV !== "production" ||
    process.env.ENABLE_DEV_CONTROL_PLANE === "1" ||
    process.env.NEXT_PUBLIC_ENABLE_DEV_CONTROL_PLANE === "1"
  );
}

export function proxy(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith("/dev") && !isDevControlPlaneEnabled()) {
    return new NextResponse("Not Found", { status: 404 });
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dev/:path*"],
};
