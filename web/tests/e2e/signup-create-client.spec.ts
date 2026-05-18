import { test, expect } from "@playwright/test";

// Skip in CI without a real Supabase instance. Run locally against
// the dev Supabase project with NEXT_PUBLIC_SUPABASE_URL set.
//
// Pre-requisites for this E2E to pass:
// 1. Supabase dashboard → Authentication → Settings → "Enable email confirmations" OFF
//    (so test emails can sign up without a real inbox).
// 2. Migrations 0001-0009 applied (operators table + handle_new_auth_user trigger).
// 3. web/.env.local populated with real NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_ANON_KEY.

test.describe("first-user flow", () => {
  test("operator can sign up, log in, create client, see client", async ({ page }) => {
    test.skip(
      !process.env.NEXT_PUBLIC_SUPABASE_URL ||
        process.env.NEXT_PUBLIC_SUPABASE_URL.includes("ci.supabase.co"),
      "Requires a real Supabase project (sets NEXT_PUBLIC_SUPABASE_URL outside CI)",
    );

    const email = `test-${Date.now()}@e2e.followroom.dev`;
    const password = "SecurePassword123!";

    // 1. Sign up
    await page.goto("/signup");
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("**/login*");

    // 2. Log in
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("/dashboard", { timeout: 10000 });

    // 3. Dashboard shows empty state
    await expect(page.getByText(/Welcome to FollowRoom/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /Add your first client/i })).toBeVisible();

    // 4. Navigate to new client form
    await page.click("text=Add your first client");
    await page.waitForURL("**/dashboard/clients/new");

    // 5. Fill in client
    await page.fill("#client_name", "Sarah Tan (E2E test)");
    await page.fill(
      "#short_context",
      "HDB upgrade, East Coast, around $1.8M, husband works in finance.",
    );
    await page.click("button[type=submit]:has-text('Create client')");

    // 6. Back on dashboard, see the client
    await page.waitForURL("/dashboard", { timeout: 10000 });
    await expect(page.getByText("Sarah Tan (E2E test)")).toBeVisible();
    await expect(page.getByText(/HDB upgrade, East Coast/i)).toBeVisible();
  });
});
