import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  testMatch: "currency.verify.spec.js",
  timeout: 60000,
  reporter: "list",
  use: { baseURL: "http://localhost:5175", headless: true },
});
