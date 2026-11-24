import { expect, test } from "@playwright/test";
import fs from "fs";
import path from "path";

const shotDir = path.join(__dirname, "../../docs/screenshots");

test.beforeEach(async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  (page as unknown as { __errors: string[] }).__errors = errors;
});

test.afterEach(async ({ page }) => {
  const errors = ((page as unknown as { __errors?: string[] }).__errors || []).filter(
    (item) => !item.includes("favicon") && !item.includes("404"),
  );
  expect(errors, errors.join("\n")).toEqual([]);
});

test("homepage loads and reaches an indicator", async ({ page }, info) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("把中国分省统计");
  await expect(page.getByRole("navigation")).toBeVisible();
  fs.mkdirSync(shotDir, { recursive: true });
  const width = page.viewportSize()?.width ?? 0;
  const name = width < 700 ? "home-mobile.png" : "home-desktop.png";
  await page.screenshot({ path: path.join(shotDir, name), fullPage: true });
  await page.getByRole("link", { name: "年末常住人口" }).first().click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("年末常住人口");
  await expect(page.getByTestId("national-value")).toBeVisible();
  const indicatorShot = width < 700 ? "indicator-mobile.png" : "indicator-desktop.png";
  await page.screenshot({ path: path.join(shotDir, indicatorShot), fullPage: true });
  expect(info).toBeTruthy();
});

test("year, province, ranking and csv stay consistent", async ({ page }) => {
  await page.goto("/indicators/population?year=2020&region=110000");
  await expect(page.getByTestId("national-value")).toBeVisible();
  const before = await page.getByTestId("national-value").innerText();
  await page.getByLabel("年份").selectOption("2010");
  await expect(page.getByTestId("national-value")).not.toHaveText(before);
  await page.getByRole("button", { name: /广东/ }).first().click();
  await expect(page.getByTestId("selected-province")).toHaveText("广东省");
  const rank = page.locator("[data-testid='rank-list'] [data-rank-value]").first();
  const raw = await rank.getAttribute("data-rank-value");
  const code = await rank.getAttribute("data-region");
  expect(raw).toBeTruthy();
  await rank.click();
  await page.getByLabel("筛选数据表").fill(code || "");
  const cell = page.locator("tr[data-testid='selected-row'] td[data-cell-value]");
  await expect(cell).toHaveAttribute("data-cell-value", raw || "");
  expect(code).toMatch(/^\d{6}$/);
  const response = await page.request.get("/downloads/population.csv");
  expect(response.ok()).toBeTruthy();
  const body = await response.text();
  expect(body.split("\n")[0]).toContain("indicator_id");
  expect(body).toContain("110000");
  const source = page.locator("a[href*='stats.gov.cn']").first();
  await expect(source).toBeVisible();
});

test("national-only indicator explains the missing provinces", async ({ page }) => {
  await page.goto("/indicators/physicians-per-1000");
  await expect(page.getByTestId("no-province-data")).toBeVisible();
  await expect(page.getByTestId("national-value")).not.toContainText("缺测");
});
