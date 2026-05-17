import { defineConfig } from "@playwright/test";

/**
 * Playwright config for the Assay demo recording.
 *
 *   cd frontend
 *   FRONTEND_URL=https://assay-delta.vercel.app npx playwright test
 */
export default defineConfig({
  testDir: "./e2e",
  testMatch: "record.spec.ts",
  timeout: 120_000,
  outputDir: "./e2e/.artifacts",
  reporter: "list",
  use: { video: "on" },
});
