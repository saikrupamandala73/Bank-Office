import { test, expect, request as pwRequest } from "@playwright/test";

const LIVE_API = "http://localhost:8000";
const TEMP_API = "http://localhost:8001";

async function routeToTemp(page) {
  await page.route(LIVE_API + "/**", async (route) => {
    const url = route.request().url().replace(LIVE_API, TEMP_API);
    const response = await route.fetch({ url });
    await route.fulfill({ response });
  });
}

const invoiceRows = (page) => page.locator(".panels table").nth(0).locator("tbody tr");
const billRows = (page) => page.locator(".panels table").nth(1).locator("tbody tr");
const displayCurrencySelect = (page) => page.locator(".settings-card select");

test.describe.configure({ mode: "serial" });

test.afterEach(async ({ page }) => {
  await page.unrouteAll({ behavior: "ignoreErrors" });
});

let ctx;

test.beforeAll(async () => {
  ctx = await pwRequest.newContext({ baseURL: TEMP_API });
});

test.afterAll(async () => {
  await ctx.dispose();
});

test.beforeEach(async () => {
  const reset = await ctx.post("/demo/reset");
  expect(reset.ok()).toBeTruthy();
  const settings = await ctx.patch("/settings", { data: { display_currency: "USD" } });
  expect(settings.ok()).toBeTruthy();
});

test("USD to INR switch updates financial displays", async ({ page }) => {
  await routeToTemp(page);
  await page.goto("/");
  await displayCurrencySelect(page).selectOption("INR");
  await expect(displayCurrencySelect(page)).toHaveValue("INR");

  const cardValues = await page.locator(".snapshot-grid .card-value").allTextContents();
  expect(cardValues).toHaveLength(3);
  for (const text of cardValues) {
    expect(text).toContain("₹");
    expect(text).not.toContain("$");
  }

  const invoiceAmounts = await invoiceRows(page).locator("td:nth-child(2)").allTextContents();
  expect(invoiceAmounts.length).toBeGreaterThan(0);
  for (const text of invoiceAmounts) expect(text).toContain("₹");

  const billAmounts = await billRows(page).locator("td:nth-child(2)").allTextContents();
  expect(billAmounts.length).toBeGreaterThan(0);
  for (const text of billAmounts) expect(text).toContain("₹");

  const originals = await page.locator("td .muted").filter({ hasText: "Original:" }).allTextContents();
  expect(originals.length).toBeGreaterThan(0);
  for (const text of originals) expect(text).toContain("$");

  const dashboard = await (await ctx.get("/dashboard/today")).json();
  const expected =
    "₹" +
    Number(dashboard.expected_inflows).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  await expect(
    page.locator(".snapshot-grid .card").filter({ hasText: "Expected inflows" }).locator(".card-value")
  ).toContainText(expected);
});

test("selected currency persists after reload", async ({ page }) => {
  await routeToTemp(page);
  await page.goto("/");
  await displayCurrencySelect(page).selectOption("INR");
  await expect(displayCurrencySelect(page)).toHaveValue("INR");

  await page.reload();
  await expect(displayCurrencySelect(page)).toHaveValue("INR");
  await expect(page.locator(".snapshot-grid")).toContainText("₹");
});

test("offline view when exchange rates unavailable (mocked 503)", async ({ page }) => {
  const settings = await ctx.patch("/settings", { data: { display_currency: "INR" } });
  expect(settings.ok()).toBeTruthy();

  await routeToTemp(page);
  const unavailable = {
    status: 503,
    contentType: "application/json",
    body: '{"detail":"Exchange rates unavailable; try again later"}',
  };
  // Registered after routeToTemp so these take precedence.
  await page.route("**/fx/rates", (route) => route.fulfill(unavailable));
  await page.route("**/dashboard/today", (route) => route.fulfill(unavailable));

  await page.goto("/");
  await expect(page.getByText("Totals in the selected currency are unavailable")).toBeVisible();
  await expect(page.locator(".snapshot-grid .card-value")).toHaveText(["—", "—", "—"]);
  await expect(page.locator(".snapshot-grid")).not.toContainText("₹");

  await expect(invoiceRows(page).first()).toBeVisible();
  const invoiceAmounts = await invoiceRows(page).locator("td:nth-child(2)").allTextContents();
  expect(invoiceAmounts.length).toBeGreaterThan(0);
  for (const text of invoiceAmounts) {
    expect(text).toMatch(/[₹$]/);
  }
  const invoiceOriginals = await invoiceRows(page)
    .locator("td .muted")
    .filter({ hasText: "Original:" })
    .allTextContents();
  for (const text of invoiceOriginals) expect(text).toContain("$");

  await expect(
    page.getByText("Exchange rates could not be loaded, so totals are not converted.")
  ).toBeVisible();
  await expect(page.getByText("shown in their original currency")).toHaveCount(0);
});
