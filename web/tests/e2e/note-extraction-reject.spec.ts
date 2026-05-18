import { test, expect } from "@playwright/test";

/**
 * Plan 2 happy-path: operator adds a note → backend extracts facts via
 * Claude → operator sees them on the Facts tab and can reject one.
 *
 * Requires (locally, not CI):
 *  - Supabase project provisioned + all 10 migrations applied
 *  - Backend FastAPI running on http://localhost:8000 with a real
 *    ANTHROPIC_API_KEY in backend/.env (otherwise extraction will fail)
 *  - web/.env.local with NEXT_PUBLIC_SUPABASE_URL +
 *    NEXT_PUBLIC_SUPABASE_ANON_KEY + NEXT_PUBLIC_BACKEND_API_URL
 *  - Email confirmations OFF in Supabase auth settings
 */
test.describe("note → extraction → reject", () => {
  test("operator adds a note, sees extracted facts, rejects one", async ({ page }) => {
    test.skip(
      !process.env.NEXT_PUBLIC_SUPABASE_URL ||
        !process.env.NEXT_PUBLIC_BACKEND_API_URL ||
        process.env.NEXT_PUBLIC_SUPABASE_URL.includes("ci.supabase.co"),
      "Requires local Supabase + backend running with real ANTHROPIC_API_KEY",
    );

    const email = `extract-${Date.now()}@e2e.followroom.dev`;
    const password = "SecurePassword123!";

    // Sign up + log in (relies on email confirmations being off)
    await page.goto("/signup");
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("**/login*");

    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("/dashboard", { timeout: 10000 });

    // Create a client
    await page.click("text=Add your first client");
    await page.waitForURL("**/dashboard/clients/new");
    await page.fill("#client_name", "Sarah E2E");
    await page.fill(
      "#short_context",
      "HDB upgrade looking around Marine Parade. Budget ~$1.8M. Decision involves husband.",
    );
    await page.click("button[type=submit]:has-text('Create client')");
    await page.waitForURL("/dashboard", { timeout: 10000 });

    // Open client detail
    await page.click("text=Sarah E2E");
    await expect(page.getByRole("heading", { name: "Sarah E2E" })).toBeVisible();

    // Navigate to Add note tab
    await page.click("nav >> text=Add note");
    await page.fill(
      "#raw_text",
      "Sarah confirmed they want to view Marine Parade Central this weekend. " +
        "She mentioned her husband is concerned about budget — they're firm at $1.8M max. " +
        "Wants to see at least 3 units before committing.",
    );
    await page.click("button[type=submit]:has-text('Save note')");

    // Wait for the receipt to appear (extraction is synchronous in Phase 2)
    await expect(page.getByText(/Note saved/i)).toBeVisible({ timeout: 60000 });

    // Switch to Facts tab — expect at least one extracted fact
    await page.click("nav >> text=Facts");
    await expect(page.locator("article").first()).toBeVisible({ timeout: 10000 });

    // Reject the first fact
    const firstCard = page.locator("article").first();
    await firstCard.getByRole("button", { name: /reject/i }).click();
    await expect(firstCard.getByText(/Rejected/i)).toBeVisible({ timeout: 10000 });
  });
});
