import { createBrowserClient } from "@supabase/ssr";

/**
 * Browser-side Supabase client factory.
 *
 * CRITICAL: Returns a new client instance per call.
 * Do NOT cache or module-scope this client — module-scoped Supabase
 * clients leak sessions across users on serverless runtimes
 * (Vercel Fluid Compute). See design doc §9.3.
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
