/**
 * Playwright video recording of the GemVault demo flow.
 *
 * Records a walk-through of the deployed dashboard: landing page, sign-in,
 * and the Ledger / Escrows / Certificates views with seeded escrow data.
 *
 * Run against the live deploy:
 *   cd frontend
 *   FRONTEND_URL=https://gemvault-delta.vercel.app npx playwright test
 *
 * The video lands in `frontend/e2e/.artifacts/`. Convert to GIF with:
 *   ffmpeg -i video.webm -vf "fps=12,scale=960:-1" docs/demo.gif
 *
 * Waits are on navigation + network idle rather than exact UI copy, so the
 * recording does not break when page text is reworded.
 */

import { test } from "@playwright/test";

const FRONTEND = process.env.FRONTEND_URL ?? "http://localhost:3000";
const ADMIN_EMAIL = process.env.GEMVAULT_ADMIN_EMAIL ?? "admin@example.com";
const ADMIN_PASSWORD = process.env.GEMVAULT_ADMIN_PASSWORD ?? "adminpass1234";

test.use({
  viewport: { width: 1280, height: 800 },
  video: "on",
});

/**
 * Pause on a page long enough for its client-side data fetch to finish.
 * The dashboard fetches after mount, so: let React mount and fire the
 * request, wait for that request to settle, then hold for the camera.
 */
async function settle(page: import("@playwright/test").Page): Promise<void> {
  await page.waitForTimeout(1600);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(2800);
}

test("GemVault demo walk-through", async ({ page }) => {
  // Landing page
  await page.goto(FRONTEND, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);

  // Sign in
  await page.goto(`${FRONTEND}/login`, { waitUntil: "networkidle" });
  await page.getByLabel("Email").fill(ADMIN_EMAIL);
  await page.getByLabel("Password").fill(ADMIN_PASSWORD);
  await page.waitForTimeout(900);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL(/\/ledger$/);
  await settle(page);

  // Escrows list
  await page.getByRole("link", { name: "Escrows" }).click();
  await page.waitForURL(/\/escrows$/);
  await settle(page);

  // First escrow detail, if one is seeded
  const firstEscrow = page.locator('a[href^="/escrows/"]').first();
  if (await firstEscrow.count()) {
    await firstEscrow.click();
    await settle(page);
    await page.goto(`${FRONTEND}/escrows`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
  }

  // Certificates
  await page.getByRole("link", { name: "Certificates" }).click();
  await page.waitForURL(/\/certificates$/);
  await settle(page);

  // Back to the ledger
  await page.getByRole("link", { name: "Ledger" }).click();
  await page.waitForURL(/\/ledger$/);
  await settle(page);
});
