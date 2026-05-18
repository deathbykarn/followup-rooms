import { test, expect } from "@playwright/test";
import path from "node:path";

/**
 * Plan 3 happy-path: operator uploads a text transcript → backend skips
 * transcription, runs extraction → operator sees facts on the Facts tab.
 *
 * Requires (locally, not CI):
 *  - Supabase project + migrations 0001-0012 applied
 *  - Backend FastAPI on http://localhost:8000 with real ANTHROPIC_API_KEY
 *    in backend/.env (this spec uses a text transcript so AssemblyAI is
 *    NOT exercised; the multi-party audio path is verified manually for
 *    now since it needs a real audio fixture and a real key)
 *  - web/.env.local with NEXT_PUBLIC_SUPABASE_URL,
 *    NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_BACKEND_API_URL
 *  - Email confirmations OFF in Supabase auth settings
 */
test.describe("upload transcript → extraction → facts visible", () => {
  test("operator uploads text transcript, sees status flip to Done, then facts appear", async ({
    page,
  }) => {
    test.skip(
      !process.env.NEXT_PUBLIC_SUPABASE_URL ||
        !process.env.NEXT_PUBLIC_BACKEND_API_URL ||
        process.env.NEXT_PUBLIC_SUPABASE_URL.includes("ci.supabase.co"),
      "Requires local Supabase + backend with real ANTHROPIC_API_KEY",
    );

    const email = `upload-${Date.now()}@e2e.followroom.dev`;
    const password = "SecurePassword123!";

    // Sign up + log in
    await page.goto("/signup");
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("**/login*");

    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("/dashboard", { timeout: 10000 });

    // Create client
    await page.click("text=Add your first client");
    await page.waitForURL("**/dashboard/clients/new");
    await page.fill("#client_name", "Sarah Tan (upload E2E)");
    await page.fill(
      "#short_context",
      "HDB upgrade looking around Marine Parade. Budget ~$1.8M. Decision involves husband.",
    );
    await page.click("button[type=submit]:has-text('Create client')");
    await page.waitForURL("/dashboard", { timeout: 10000 });

    // Open client detail → Upload tab
    await page.click("text=Sarah Tan (upload E2E)");
    await page.click("nav >> text=Upload");
    await expect(page.getByRole("heading", { name: /Upload transcript or voice memo/i })).toBeVisible();

    // Pick the text-transcript radio (default) and attach the fixture
    const fixturePath = path.join(__dirname, "..", "fixtures", "sample-transcript.txt");
    await page.locator('input[type="file"]').setInputFiles(fixturePath);
    await expect(page.getByText("sample-transcript.txt")).toBeVisible();

    await page.click('button:has-text("Upload")');

    // The status card should appear within seconds, walking states
    const card = page.locator("article").first();
    await expect(card).toBeVisible({ timeout: 10000 });

    // Wait for terminal state. Text transcripts skip transcription, so it's
    // queued → extracting → done. Generous timeout for Claude latency.
    await expect(card.getByText(/Done/i)).toBeVisible({ timeout: 90000 });

    // Click the Facts link from the status card
    await card.getByRole("link", { name: /Review on Facts tab/i }).click();
    await expect(page.locator("article").first()).toBeVisible({ timeout: 10000 });
  });
});
