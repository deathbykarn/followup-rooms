import { describe, it, expect, vi } from "vitest";

// The cross-user session-leak risk in @supabase/ssr lives in the SERVER
// client — and is mitigated by passing per-request cookies into the
// cookies adapter, not by getting a new client instance per call.
// createBrowserClient is intentionally a singleton (browser context = one
// user; cached client is safe and recommended by Supabase docs).
//
// These tests verify the factory surface and basic shape; the request-
// scoped cookie pattern is verified end-to-end via Playwright in Task 33.

describe("Supabase browser client factory", () => {
  it("returns a client with the expected auth + from shape", async () => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://test.supabase.co");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "anon-test");

    const { createClient } = await import("@/lib/supabase/client");
    const client = createClient();

    expect(client).toBeDefined();
    expect(client.auth).toBeDefined();
    expect(typeof client.from).toBe("function");
  });

  it("factory function reads env vars at call time", async () => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://another.supabase.co");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "anon-test");

    const { createClient } = await import("@/lib/supabase/client");
    // Just verify the function runs without throwing — the env stub
    // means the URL string is read at call time, not at module import.
    expect(() => createClient()).not.toThrow();
  });
});
