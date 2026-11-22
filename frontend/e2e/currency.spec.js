import { test, expect, request as pwRequest } from "@playwright/test";

const API = "http://localhost:8000";
const TIMEOUT = { timeout: 10000 };

async function setCurrency(code) {
  const ctx = await pwRequest.newContext();
  await ctx.patch(`${API}/settings`, { data: { display_currency: code } });
  await ctx.dispose();
}

const currencySelect = (page) => page.getByLabel("Display currency");
const inflowsValue = (page) =>
  page.locator(".snapshot-grid .card").filter({ hasText: "Expected inflows" }).locator(".card-value");
const invoiceBody = (page) => page.locator(".panels table").first().locator("tbody");

async function openHome(page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Bank Office" })).toBeVisible(TIMEOUT);
}

test("USD to INR switch updates dashboard, actions and tables", async ({ page }) => {
  await setCurrency("USD");
  await openHome(page);
  await currencySelect(page).selectOption("INR");

  await expect(inflowsValue(page)).toContainText("₹", TIMEOUT);
  await expect(inflowsValue(page)).not.toContainText("$", TIMEOUT);
  await expect(page.getByRole("heading", { name: "Today's priority actions" })).toBeVisible(TIMEOUT);
  await expect(invoiceBody(page)).toContainText("₹", TIMEOUT);

  const originals = invoiceBody(page).locator(".muted", { hasText: "Original:" });
  const count = await originals.count();
  expect(count).toBeGreaterThan(0);
  for (let i = 0; i < count; i++) {
    await expect(originals.nth(i)).toContainText("$");
  }
  await expect(page.locator(".snapshot-grid")).not.toContainText("$", TIMEOUT);
});

test("selected currency persists after reload", async ({ page }) => {
  await setCurrency("INR");
  await openHome(page);
  await expect(currencySelect(page)).toHaveValue("INR", TIMEOUT);

  await page.reload();
  await expect(currencySelect(page)).toHaveValue("INR", TIMEOUT);
  await expect(inflowsValue(page)).toContainText("₹", TIMEOUT);
});

test("offline fallback shows dash cards and warning", async ({ page }) => {
  await setCurrency("INR");
  const failure = {
    status: 503,
    contentType: "application/json",
    body: '{"detail":"Exchange rates unavailable; try again later"}',
  };
  await page.route("**/dashboard/today", (r) => r.fulfill(failure));
  await page.route("**/fx/rates", (r) => r.fulfill(failure));
  await openHome(page);

  await expect(page.getByText("Totals in the selected currency are unavailable")).toBeVisible(TIMEOUT);
  await expect(page.locator(".snapshot-grid .card-value")).toHaveText(["—", "—", "—"], TIMEOUT);
  await expect(page.locator(".settings-card .warning")).toContainText(
    "Exchange rates unavailable. Amounts are shown in their original currency.",
    TIMEOUT
  );
  await expect
    .poll(async () => invoiceBody(page).locator("tr").count(), TIMEOUT)
    .toBeGreaterThan(0);
});

test("stale rates flag is shown", async ({ page }) => {
  await setCurrency("INR");
  const ctx = await pwRequest.newContext();
  const res = await ctx.get(`${API}/fx/rates`);
  expect(res.ok()).toBeTruthy();
  const body = JSON.parse(await res.text());
  await ctx.dispose();
  body.stale = true;

  await page.route("**/fx/rates", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) })
  );
  await openHome(page);
  await expect(page.getByText("Showing last saved rates; live update failed.")).toBeVisible(TIMEOUT);
});

test("invoices and bills show converted amount with original", async ({ page }) => {
  await setCurrency("INR");
  await openHome(page);

  const amountCell = invoiceBody(page).locator("tr").first().locator("td").nth(1);
  await expect(amountCell).toContainText("₹", TIMEOUT);
  await expect(amountCell.locator(".muted", { hasText: "Original:" })).toContainText("$", TIMEOUT);
});
