import { test, expect } from "@playwright/test";

test("current Bank Office page loads read-only", async ({ page }) => {
  const writes = [];
  page.on("request", (req) => {
    const m = req.method();
    if (req.url().startsWith("http://localhost:8000") && m !== "GET") {
      writes.push(`${m} ${req.url()}`);
    }
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Bank Office" })).toBeVisible();
  await expect(page.getByText("Expected inflows")).toBeVisible();
  await expect(page.getByText("Projected net outlook")).toBeVisible();
  await expect(page.locator(".settings-card select")).toBeVisible();

  expect(writes).toEqual([]);
});
