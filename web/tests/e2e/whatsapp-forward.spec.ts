import { test, expect } from "@playwright/test";
import { createClient } from "@supabase/supabase-js";

/**
 * Plan 4 UI happy-path (no Meta dependency): a fake "operator forwarded
 * a WhatsApp message" pending_forwards row is inserted via the operator's
 * own anon session (RLS permits since operator_id = auth.uid()). The spec
 * then exercises the dashboard tray: see the pending forward → confirm
 * to a client → land on Facts tab with extracted facts.
 *
 * The webhook signing path is unit-tested separately (test_whatsapp_webhook_api).
 * Full live integration (real Meta inbound → backend webhook → pending row)
 * is validated by the manual smoke test in Task 9 of the plan.
 *
 * Requires (locally, not CI):
 *  - Supabase project + migrations 0001-0014 applied
 *  - Backend FastAPI on http://localhost:8000 with real ANTHROPIC_API_KEY
 *  - web/.env.local with NEXT_PUBLIC_SUPABASE_URL, _ANON_KEY,
 *    NEXT_PUBLIC_BACKEND_API_URL
 *  - Email confirmations OFF in Supabase auth settings
 */
test.describe("WhatsApp pending forward → confirm → facts visible", () => {
  test("operator confirms a pending forward; extraction runs; facts appear", async ({
    page,
    request,
  }) => {
    test.skip(
      !process.env.NEXT_PUBLIC_SUPABASE_URL ||
        !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
        !process.env.NEXT_PUBLIC_BACKEND_API_URL ||
        process.env.NEXT_PUBLIC_SUPABASE_URL.includes("ci.supabase.co"),
      "Requires local Supabase + backend running with real ANTHROPIC_API_KEY",
    );

    const email = `whatsapp-${Date.now()}@e2e.followroom.dev`;
    const password = "SecurePassword123!";

    // 1. Sign up + log in via the UI (matches Plan 2/3 specs)
    await page.goto("/signup");
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("**/login*");

    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("/dashboard", { timeout: 10000 });

    // 2. Create a client to attribute the forward to
    await page.click("text=Add your first client");
    await page.waitForURL("**/dashboard/clients/new");
    await page.fill("#client_name", "Sarah Tan (whatsapp E2E)");
    await page.fill(
      "#short_context",
      "HDB upgrade looking around Marine Parade. Budget ~$1.8M.",
    );
    await page.click("button[type=submit]:has-text('Create client')");
    await page.waitForURL("/dashboard", { timeout: 10000 });

    // 3. Insert a fake pending_forwards row via the operator's own session.
    // RLS permits because the WITH CHECK clause is operator_id = auth.uid().
    // We use the same anon credentials the browser does, with the operator's
    // password sign-in to get a valid session token.
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL as string,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string,
    );
    const {
      data: { user },
      error: signinErr,
    } = await supabase.auth.signInWithPassword({ email, password });
    expect(signinErr).toBeNull();
    expect(user).not.toBeNull();
    const operatorId = user!.id;

    // Find the client id we just created
    const { data: clientRows } = await supabase
      .from("clients")
      .select("id, client_name")
      .eq("client_name", "Sarah Tan (whatsapp E2E)")
      .limit(1);
    expect(clientRows && clientRows.length).toBe(1);
    const clientId = clientRows![0].id;

    // Insert the pending forward as if a real webhook delivered it
    const wamid = `wamid.e2e-${Date.now()}`;
    const { error: insertErr } = await supabase
      .from("pending_forwards")
      .insert({
        operator_id: operatorId,
        wa_message_id: wamid,
        sender_wa_id: "6591234567",
        forwarded_text:
          "Just had a quick chat with my mum — she's pushing me to go view " +
          "the Marine Parade Central unit this Saturday morning. Budget still " +
          "1.8M firm. Husband is fine with the location now.",
        caption_text: "Sarah Tan",
        wa_timestamp: new Date().toISOString(),
        suggested_client_id: clientId,
        suggested_confidence: 0.95,
        raw_payload: { e2e: true, wamid },
      });
    expect(insertErr).toBeNull();

    // 4. Reload the dashboard so the header badge picks up the new pending count
    await page.goto("/dashboard");
    await expect(page.getByText(/1 pending forward/i)).toBeVisible({ timeout: 10000 });

    // 5. Navigate to the Pending page
    await page.click("text=1 pending forward");
    await page.waitForURL("**/dashboard/pending");

    const card = page.locator("article").first();
    await expect(card).toBeVisible({ timeout: 10000 });
    await expect(card.getByText(/Marine Parade/)).toBeVisible();
    await expect(card.getByText("Sarah Tan")).toBeVisible();

    // 6. Click Confirm Sarah Tan
    await card.getByRole("button", { name: /Confirm Sarah Tan/i }).click();

    // Confirm triggers extraction synchronously. Give it generous time for
    // Claude to extract + persist + profile-regen.
    await expect(card.getByText(/confirmed/i)).toBeVisible({ timeout: 60000 });

    // 7. Go to the client's Facts tab; expect ≥1 fact extracted from the forward
    await page.goto(`/dashboard/clients/${clientId}/facts`);
    await expect(page.locator("article").first()).toBeVisible({ timeout: 10000 });
  });
});
