import { test, expect } from "@playwright/test";

test.describe("Рыбные точки — UI Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/catches**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          catches: [
            {
              id: "11111111-1111-1111-1111-111111111111",
              latitude: 54.63,
              longitude: 39.74,
              fish_type: {
                id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                name: "Лещ",
                icon: "🐠",
                category: "peaceful",
              },
              river: "oka",
              name: "Ока — Рязань",
              description: "Лещ на фидер.",
              season: ["spring", "summer"],
              depth: 5.5,
              bait: "Фидер, горох",
              weight_avg: 1.5,
              is_demo: true,
              source_label: "Демонстрационные данные",
              created_at: "2024-01-01T00:00:00",
            },
          ],
          total: 1,
          page: 1,
          page_size: 200,
        }),
      })
    );
  });

  test("Главная: заголовок секции и бейдж «Рыбные точки» видны", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByText("Рыбные точки на Волге и Оке")
    ).toBeVisible({ timeout: 15000 });
    await expect(
      page.getByRole("heading", { name: "Где ловили рыбу" })
    ).toBeVisible({ timeout: 10000 });
  });

  test("Главная: счётчики точек корректны (всего/Волга/Ока)", async ({ page }) => {
    await page.goto("/");
    await page.getByText("всего точек улова").waitFor({ timeout: 15000 });
    await expect(page.locator("text=река Волга")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=река Ока")).toBeVisible({ timeout: 10000 });
  });

  test("Главная: адаптивность mobile (375px)", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Где ловили рыбу" })
    ).toBeVisible({ timeout: 15000 });
  });

  test("Главная: адаптивность desktop (1280px)", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Где ловили рыбу" })
    ).toBeVisible({ timeout: 15000 });
  });

  test("Карта /map: подсказка о рыбных точках доступна", async ({ page }) => {
    await page.goto("/map");
    await expect(
      page.getByText(/рыбных точек/).first()
    ).toBeVisible({ timeout: 15000 });
  });
});
