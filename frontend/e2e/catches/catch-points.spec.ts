import { test, expect } from "@playwright/test";

test.describe("Рыбные точки (catch points) — E2E", () => {
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
            {
              id: "22222222-2222-2222-2222-222222222222",
              latitude: 56.86,
              longitude: 35.92,
              fish_type: {
                id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                name: "Щука",
                icon: "🐟",
                category: "predatory",
              },
              river: "volga",
              name: "Верхняя Волга — Тверь",
              description: "Закоряженные ямы.",
              season: ["summer", "autumn"],
              depth: 3.5,
              bait: "Воблер",
              weight_avg: 2.1,
              is_demo: true,
              source_label: "Демонстрационные данные",
              created_at: "2024-01-02T00:00:00",
            },
          ],
          total: 2,
          page: 1,
          page_size: 200,
        }),
      })
    );
  });

  test("Карта /map: подгружаются рыбные точки и подсказка о них", async ({ page }) => {
    await page.goto("/map");
    await expect(
      page.locator("text=рыбных точек").first()
    ).toBeVisible({ timeout: 15000 });
  });

  test("Главная: секция «Где ловили рыбу» рендерится со статистикой", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Где ловили рыбу" })
    ).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=река Волга")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=река Ока")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=демонстрационные данные")).toBeVisible({ timeout: 10000 });
  });

  test("Главная: кликабельная карта с рыбными точками рендерится", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("heading", { name: "Где ловили рыбу" }).waitFor({ timeout: 15000 });
    await page.waitForTimeout(3000);
    const mapSection = page
      .locator("section")
      .filter({ hasText: "Где ловили рыбу" });
    await expect(mapSection.locator("ymaps").first()).toBeVisible({ timeout: 15000 });
  });
});
