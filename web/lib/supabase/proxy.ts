import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Proxy (formerly middleware) helper — refreshes the user's session
 * cookie on every request that passes through proxy.ts. The returned
 * NextResponse carries the updated cookies forward.
 *
 * Next.js 16: middleware.ts → proxy.ts; export `proxy` (not `middleware`).
 */
export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  // CRITICAL: this hits the auth server to verify the token.
  // Do not skip this even if you don't need the user object here —
  // it's what refreshes expired access tokens via the refresh token.
  await supabase.auth.getUser();

  return supabaseResponse;
}
