import { test, expect } from "@playwright/test";

test.describe("Layers Panel — UI Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/map");
    await page.waitForTimeout(3000);
  });

  test("Layers panel has correct heading", async ({ page }) => {
    await expect(page.locator("text=Слои карты")).toBeVisible({ timeout: 10000 });
  });

  test("Layers panel has Waves icon for depth", async ({ page }) => {
    await expect(page.locator("text=Глубины")).toBeVisible({ timeout: 10000 });
  });

  test("Depth toggle has aria-label for accessibility", async ({ page }) => {
    const toggle = page.locator('button[aria-label="Toggle depth layer"]');
    await expect(toggle).toBeVisible({ timeout: 10000 });
  });

  test("Responsive: panel works on mobile viewport (375px)", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000);

    await expect(page.locator("text=Слои карты")).toBeVisible({ timeout: 10000 });
  });

  test("Responsive: panel works on desktop viewport (1280px)", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.waitForTimeout(1000);

    await expect(page.locator("text=Слои карты")).toBeVisible({ timeout: 10000 });
  });

  test("Color scheme buttons have correct labels", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    const navionicsBtn = page.locator("button:has-text('Navionics')");
    await expect(navionicsBtn).toBeVisible();
    await expect(navionicsBtn).toHaveClass(/bg-primary-sea/);
  });

  test("Legend color swatches have background colors", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    const swatches = page.locator(".rounded.border.border-gray-200");
    await expect(swatches.first()).toBeVisible();
    const count = await swatches.count();
    expect(count).toBe(6);
  });

  test("Labels toggle is on by default", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    const toggle = page.locator('button[aria-label="Toggle depth labels"]');
    await expect(toggle).toHaveClass(/bg-primary-sea/);
  });

  test("Isobaths toggle is off by default", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    const toggle = page.locator('button[aria-label="Toggle isobaths"]');
    await expect(toggle).toHaveClass(/bg-gray-300/);
  });

  test("Opacity default is 60%", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    await expect(page.locator("text=60%")).toBeVisible();
  });

  test("Toggling labels updates UI state", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    const labelsToggle = page.locator('button[aria-label="Toggle depth labels"]');
    await expect(labelsToggle).toHaveClass(/bg-primary-sea/);

    await labelsToggle.click();
    await page.waitForTimeout(300);
    await expect(labelsToggle).toHaveClass(/bg-gray-300/);
  });

  test("Toggling isobaths updates UI state", async ({ page }) => {
    await page.locator('button[aria-label="Toggle depth layer"]').click();
    await page.waitForTimeout(500);

    const isobathsToggle = page.locator('button[aria-label="Toggle isobaths"]');
    await expect(isobathsToggle).toHaveClass(/bg-gray-300/);

    await isobathsToggle.click();
    await page.waitForTimeout(300);
    await expect(isobathsToggle).toHaveClass(/bg-primary-sea/);
  });
});
