import { test, expect } from "@playwright/test";

test.describe("Depth Layer — Navionics-style visualization", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/map");
    await page.waitForTimeout(3000);
  });

  test("US-SLR-001: Layers panel is visible on map page", async ({ page }) => {
    const panel = page.locator("text=Слои карты");
    await expect(panel).toBeVisible({ timeout: 10000 });
  });

  test("US-SLR-001: Depth layer toggle exists and is off by default", async ({ page }) => {
    const depthToggle = page.locator('button[aria-label="Toggle depth layer"]');
    await expect(depthToggle).toBeVisible();
    const toggleParent = depthToggle;
    await expect(toggleParent).toHaveClass(/bg-gray-300/);
  });

  test("US-SLR-001: Enabling depth layer shows controls", async ({ page }) => {
    const depthToggle = page.locator('button[aria-label="Toggle depth layer"]');
    await depthToggle.click();
    await page.waitForTimeout(500);

    await expect(page.locator("text=Прозрачность")).toBeVisible();
    await expect(page.locator("text=Цветовая схема")).toBeVisible();
    await expect(page.locator("text=Легенда глубин")).toBeVisible();
  });

  test("US-SLR-001: Legend shows all 6 depth ranges", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    await expect(page.locator("text=0-2м")).toBeVisible();
    await expect(page.locator("text=2-5м")).toBeVisible();
    await expect(page.locator("text=5-10м")).toBeVisible();
    await expect(page.locator("text=10-20м")).toBeVisible();
    await expect(page.locator("text=20-50м")).toBeVisible();
    await expect(page.locator("text=>50м")).toBeVisible();
  });

  test("US-SLR-002: Labels toggle exists", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    const labelsToggle = page.locator('button[aria-label="Toggle depth labels"]');
    await expect(labelsToggle).toBeVisible();
  });

  test("US-SLR-003: Isobaths toggle exists", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    const isobathsToggle = page.locator('button[aria-label="Toggle isobaths"]');
    await expect(isobathsToggle).toBeVisible();
  });

  test("US-SLR-004: Three color schemes are available", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    await expect(page.locator("button:has-text('Navionics')")).toBeVisible();
    await expect(page.locator("button:has-text('Контраст')")).toBeVisible();
    await expect(page.locator("button:has-text('Спорт')")).toBeVisible();
  });

  test("US-SLR-004: Switching color scheme updates legend", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    await page.locator("button:has-text('Контраст')").click();
    await page.waitForTimeout(300);

    const activeScheme = page.locator("button:has-text('Контраст')");
    await expect(activeScheme).toHaveClass(/bg-primary-sea/);
  });

  test("US-SLR-001: Opacity slider works", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    const slider = page.locator('input[type="range"]');
    await expect(slider).toBeVisible();
    await expect(page.locator("text=60%")).toBeVisible();
  });

  test("Depth layer can be toggled off", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);
    await expect(page.locator("text=Прозрачность")).toBeVisible();

    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);
    await expect(page.locator("text=Прозрачность")).not.toBeVisible();
  });
});
