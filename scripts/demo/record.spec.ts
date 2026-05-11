/**
 * Playwright video recording of the GemVault demo flow.
 *
 * Prereqs:
 *   1. Backend running on :8000 (`uvicorn gemvault.main:app --reload`).
 *   2. Frontend running on :3000 (`npm run dev`).
 *   3. Seed data loaded (`python scripts/demo/seed.py`).
 *
 * Run:
 *   cd frontend && npx playwright test ../scripts/demo/record.spec.ts --headed
 *
 * The video lands in `playwright-report/` or `test-results/`. Convert to GIF
 * with: `ffmpeg -i video.webm -vf "fps=12,scale=960:-1" demo.gif`.
 */

import { test, expect } from "@playwright/test";

const FRONTEND = process.env.FRONTEND_URL ?? "http://localhost:3000";
const ADMIN_EMAIL = process.env.GEMVAULT_ADMIN_EMAIL ?? "admin@example.com";
const ADMIN_PASSWORD = process.env.GEMVAULT_ADMIN_PASSWORD ?? "adminpass1234";

test.use({
  viewport: { width: 1280, height: 800 },
  video: "on",
  trace: "on",
});

test("GemVault demo walk-through", async ({ page }) => {
  await page.goto(FRONTEND);
  await expect(page.getByText("Reference RWA Fintech")).toBeVisible();
  await page.waitForTimeout(1500);

  await page.goto(`${FRONTEND}/login`);
  await page.getByLabel("Email").fill(ADMIN_EMAIL);
  await page.getByLabel("Password").fill(ADMIN_PASSWORD);
  await page.waitForTimeout(800);
  await page.getByRole("button", { name: /sign in/i }).click();

  await page.waitForURL(/\/ledger$/);
  await expect(page.getByText("Event ledger")).toBeVisible();
  await page.waitForTimeout(2500);

  await page.getByRole("link", { name: "Escrows" }).click();
  await page.waitForURL(/\/escrows$/);
  await expect(page.getByText(/Escrows$/)).toBeVisible();
  await page.waitForTimeout(2000);

  const firstEscrowLink = page.locator('a[href^="/escrows/"]').first();
  if (await firstEscrowLink.count()) {
    await firstEscrowLink.click();
    await page.waitForTimeout(2500);
    await page.getByRole("link", { name: /all escrows/i }).click();
  }

  await page.getByRole("link", { name: "Certificates" }).click();
  await page.waitForURL(/\/certificates$/);
  await expect(page.getByText(/Certificates/)).toBeVisible();
  await page.waitForTimeout(2500);

  await page.getByRole("link", { name: "Ledger" }).click();
  await page.waitForTimeout(2000);
});
