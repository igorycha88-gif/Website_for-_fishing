import { test, expect } from '@playwright/test';

test.describe('Профиль - Функциональное тестирование', () => {
  test.use({ storageState: 'e2e/.auth/user.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/profile');
  });

  test('должен отображать информацию о пользователе', async ({ page }) => {
    await expect(page.getByRole('heading')).toBeVisible();
  });

  test('должен отображать все вкладки в навигации', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Профиль' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Мои места' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Корзина' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Заказы' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Уведомления' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Отчеты' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Бронирования' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Настройки' })).toBeVisible();
  });

  test('должен переключаться между вкладками', async ({ page }) => {
    await page.getByRole('button', { name: 'Мои места' }).click();
    await expect(page.getByText('Мои места рыбалки')).toBeVisible();

    await page.getByRole('button', { name: 'Настройки' }).click();
    await expect(page.getByText('Настройки')).toBeVisible();
  });

  test('кнопка "Выйти из аккаунта" должна работать', async ({ page }) => {
    page.on('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: 'Выйти из аккаунта' }).click();
    await expect(page).toHaveURL('/');
  });

  test('кнопка "Вернуться на главную" должна работать', async ({ page }) => {
    await page.getByRole('link', { name: /Вернуться на главную/ }).click();
    await expect(page).toHaveURL('/');
  });
});

test.describe('Вкладка "Мои места" - Функциональное тестирование', () => {
  test.use({ storageState: 'e2e/.auth/user.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
  });

  test('должен отображать заголовок "Мои места рыбалки"', async ({ page }) => {
    await expect(page.getByText('Мои места рыбалки')).toBeVisible();
  });

  test('должна быть кнопка "Добавить место"', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Добавить место' })).toBeVisible();
  });

  test('должен открываться форма добавления места', async ({ page }) => {
    await page.getByRole('button', { name: 'Добавить место' }).click();
    await expect(page.getByText('Новое место')).toBeVisible();
  });

  test('форма должна иметь все необходимые поля', async ({ page }) => {
    await page.getByRole('button', { name: 'Добавить место' }).click();
    
    await expect(page.getByLabel('Название *')).toBeVisible();
    await expect(page.getByLabel('Адрес *')).toBeVisible();
    await expect(page.getByLabel('Широта *')).toBeVisible();
    await expect(page.getByLabel('Долгота *')).toBeVisible();
    await expect(page.getByLabel('Описание *')).toBeVisible();
    await expect(page.getByLabel('Виды рыб *')).toBeVisible();
  });

  test('форма должна закрываться при нажатии на кнопку отмены', async ({ page }) => {
    await page.getByRole('button', { name: 'Добавить место' }).click();
    await page.getByRole('button', { name: 'Отмена' }).click();
    
    await expect(page.getByText('Новое место')).not.toBeVisible();
  });

  test('должен отображать список мест если они есть', async ({ page }) => {
    const places = page.locator('.space-y-6 > .grid > div');
    const count = await places.count();
    
    if (count > 0) {
      await expect(places.first()).toBeVisible();
    } else {
      await expect(page.getByText('Нет сохраненных мест')).toBeVisible();
    }
  });

  test('должен отображать сообщение если мест нет', async ({ page }) => {
    const places = page.locator('.space-y-6 > .grid > div');
    const count = await places.count();
    
    if (count === 0) {
      await expect(page.getByText('Нет сохраненных мест')).toBeVisible();
      await expect(page.getByText('Добавьте свое первое место для рыбалки')).toBeVisible();
    }
  });
});

test.describe('Вкладка "Мои места" - Добавление места', () => {
  test.use({ storageState: 'e2e/.auth/user.json' });

  test('создание нового места с минимальными данными', async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    await page.getByRole('button', { name: 'Добавить место' }).click();

    const timestamp = Date.now();
    await page.getByLabel('Название *').fill(`Тестовое место ${timestamp}`);
    await page.getByLabel('Адрес *').fill('г. Москва, ул. Тестовая, 1');
    await page.getByLabel('Широта *').fill('55.7558');
    await page.getByLabel('Долгота *').fill('37.6173');
    await page.getByLabel('Описание *').fill('Тестовое описание места для рыбалки');
    await page.locator('button:has-text("Карась")').click();
    
    await page.getByRole('button', { name: 'Создать' }).click();
    
    await expect(page.getByText('Новое место')).not.toBeVisible();
  });

  test('валидация обязательных полей', async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    await page.getByRole('button', { name: 'Добавить место' }).click();

    await page.getByRole('button', { name: 'Создать' }).click();
    
    const requiredInputs = page.locator('input:required');
    const count = await requiredInputs.count();
    expect(count).toBeGreaterThan(0);
  });

  test('валидация длины полей', async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    await page.getByRole('button', { name: 'Добавить место' }).click();

    const longTitle = 'a'.repeat(250);
    await page.getByLabel('Название *').fill(longTitle);
    
    const value = await page.getByLabel('Название *').inputValue();
    expect(value.length).toBeLessThanOrEqual(200);
  });

  test('должен выбирать виды рыб', async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    await page.getByRole('button', { name: 'Добавить место' }).click();

    await page.locator('button:has-text("Карась")').click();
    await page.locator('button:has-text("Лещ")').click();
    await page.locator('button:has-text("Судак")').click();
    
    await expect(page.locator('button.bg-primary-sea:has-text("Карась")')).toBeVisible();
    await expect(page.locator('button.bg-primary-sea:has-text("Лещ")')).toBeVisible();
    await expect(page.locator('button.bg-primary-sea:has-text("Судак")')).toBeVisible();
  });

  test('должен выбирать удобства', async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    await page.getByRole('button', { name: 'Добавить место' }).click();

    await page.locator('button:has-text("Парковка")').click();
    await page.locator('button:has-text("Мангал")').click();
    
    await expect(page.locator('button.bg-primary-sea:has-text("Парковка")')).toBeVisible();
    await expect(page.locator('button.bg-primary-sea:has-text("Мангал")')).toBeVisible();
  });

  test('должен переключать публичность места', async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    await page.getByRole('button', { name: 'Добавить место' }).click();

    await page.getByLabel('Публичное место').check();
    await expect(page.getByText(/Публичные места требуют модерации/)).toBeVisible();
    
    await page.getByLabel('Публичное место').uncheck();
    await expect(page.getByText(/Публичные места требуют модерации/)).not.toBeVisible();
  });
});

test.describe('Профиль - UX/UI Тестирование', () => {
  test.use({ storageState: 'e2e/.auth/user.json' });

  test('должен быть корректный вид на мобильном устройстве', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/profile');
    
    await expect(page.getByRole('heading')).toBeVisible();
    const tabs = page.locator('nav button');
    const count = await tabs.count();
    expect(count).toBe(8);
  });

  test('должны быть анимации при переключении вкладок', async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    await page.getByRole('button', { name: 'Настройки' }).click();
    
    await expect(page.getByText('Настройки')).toBeVisible();
  });

  test('навигация должна быть доступной для клавиатуры', async ({ page }) => {
    await page.goto('/profile');
    await page.keyboard.press('Tab');
    
    const firstTab = page.locator('nav button').first();
    await expect(firstTab).toBeFocused();
  });
});

test.describe('Профиль - Edge Cases', () => {
  test.use({ storageState: 'e2e/.auth/user.json' });

  test('должен обрабатывать отсутствие интернета', async ({ page }) => {
    await page.route('**/api/v1/**', route => route.abort('failed'));
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    
    await page.getByRole('button', { name: 'Добавить место' }).click();
    await page.getByLabel('Название *').fill('Тест');
    await page.getByRole('button', { name: 'Создать' }).click();
    
    await expect(page.getByText('Не удалось сохранить место')).toBeVisible();
  });

  test('должен обрабатывать очень длинное описание', async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    await page.getByRole('button', { name: 'Добавить место' }).click();

    const longDescription = 'a'.repeat(6000);
    await page.getByLabel('Описание *').fill(longDescription);
    
    const value = await page.getByLabel('Описание *').inputValue();
    expect(value.length).toBeLessThanOrEqual(5000);
  });

  test('должен обрабатывать специальные символы в названии', async ({ page }) => {
    await page.goto('/profile');
    await page.getByRole('button', { name: 'Мои места' }).click();
    await page.getByRole('button', { name: 'Добавить место' }).click();

    await page.getByLabel('Название *').fill('Место "Тест" & Особое');
    const value = await page.getByLabel('Название *').inputValue();
    expect(value).toBe('Место "Тест" & Особое');
  });
});

test.describe('Профиль - Без авторизации', () => {
  test('должен перенаправлять на регистрацию без авторизации', async ({ page }) => {
    await page.goto('/profile');
    await expect(page).toHaveURL('/register');
  });
});
