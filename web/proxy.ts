import { updateSession } from "@/lib/supabase/proxy";
import type { NextRequest } from "next/server";

/**
 * Next.js 16 Proxy (formerly Middleware).
 *
 * Refreshes the Supabase session cookie on every request that passes
 * through this proxy. The matcher excludes:
 *  - /r/[slug] (public client-facing rooms; no auth)
 *  - Static assets (_next/static, _next/image, favicon, etc.)
 *  - The auth callback route (which sets its own cookies)
 *
 * IMPORTANT: Server Actions on excluded paths get NO session refresh.
 * Plan 6 (client-facing room) must use Route Handlers + Anon Key, NOT
 * Server Actions on /r/* paths.
 */
export async function proxy(request: NextRequest) {
  return await updateSession(request);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|r/|api/auth/callback|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
