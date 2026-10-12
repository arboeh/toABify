import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  reporter: "list",
  retries: 0,
  timeout: 15000,
  use: { ...devices["Desktop Chrome"], trace: "retain-on-failure" },
});
