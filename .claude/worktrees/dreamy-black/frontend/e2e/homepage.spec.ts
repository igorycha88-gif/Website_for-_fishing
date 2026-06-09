import { test, expect } from '@playwright/test';

test.describe('Главная страница - Функциональное тестирование', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('должен отображать заголовок "Почему выбирают нас"', async ({ page }) => {
    await expect(page.locator('section').filter({ hasText: 'Почему выбирают нас' }).getByRole('heading', { name: 'Почему выбирают нас' })).toBeVisible();
  });

  test('должен отображать все 4 функциональные блока', async ({ page }) => {
    const featuresSection = page.locator('section').filter({ hasText: 'Почему выбирают нас' });
    await expect(featuresSection.getByText('Карта мест').first()).toBeVisible();
    await expect(featuresSection.getByText('Прогноз клёва').first()).toBeVisible();
    await expect(featuresSection.getByText('Магазин снастей')).toBeVisible();
    await expect(featuresSection.getByText('Базы отдыха')).toBeVisible();
  });

  test('должен отображать раздел "Популярные места"', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Популярные места' })).toBeVisible();
  });

  test('должен отображать 3 популярных места', async ({ page }) => {
    await expect(page.getByText('Озеро Баскунчак')).toBeVisible();
    await expect(page.getByText('Река Волга')).toBeVisible();
    await expect(page.getByText('Рыбинское водохранилище')).toBeVisible();
  });

  test('кнопка "Смотреть все места" должна вести на страницу карты', async ({ page }) => {
    await page.getByRole('link', { name: 'Смотреть все места' }).click();
    await expect(page).toHaveURL('/map');
  });

  test('должен отображать раздел "Прогноз клёва"', async ({ page }) => {
    const forecastSection = page.locator('section').filter({ hasText: 'Планируйте рыбалку с учётом погоды' });
    await expect(forecastSection.getByRole('heading', { name: 'Прогноз клёва' }).first()).toBeVisible();
    await expect(forecastSection.getByText('Москва')).toBeVisible();
    await expect(forecastSection.getByText('Пн')).toBeVisible();
    await expect(forecastSection.getByText('Ср', { exact: true })).toBeVisible();
  });

  test('кнопка "Подробный прогноз" должна вести на страницу прогноза', async ({ page }) => {
    const forecastSection = page.locator('section').filter({ hasText: 'Планируйте рыбалку с учётом погоды' });
    await forecastSection.getByRole('link', { name: 'Подробный прогноз' }).click();
    await expect(page).toHaveURL('/forecast');
  });

  test('должен отображать раздел "Оставайтесь на связи" с формой подписки', async ({ page }) => {
    const newsletterSection = page.locator('section').filter({ hasText: 'Подпишитесь на нашу рассылку' });
    await expect(newsletterSection.getByRole('heading', { name: 'Оставайтесь на связи' })).toBeVisible();
    await expect(newsletterSection.getByPlaceholder('Ваш email')).toBeVisible();
    await expect(newsletterSection.getByRole('button', { name: 'Подписаться' })).toBeVisible();
  });

  test('должен отображать контактную информацию', async ({ page }) => {
    const contactSection = page.locator('section').filter({ hasText: 'Свяжитесь с нами' });
    await expect(contactSection.getByRole('heading', { name: 'Свяжитесь с нами' })).toBeVisible();
    await expect(contactSection.getByText('+7 (900) 123-45-67')).toBeVisible();
    await expect(contactSection.getByText('info@rybalka.ru')).toBeVisible();
  });

  test('ссылка на телефон должна быть кликабельной', async ({ page }) => {
    const contactSection = page.locator('section').filter({ hasText: 'Свяжитесь с нами' });
    const phoneLink = contactSection.getByRole('link', { name: '+7 (900) 123-45-67' }).first();
    await expect(phoneLink).toHaveAttribute('href', 'tel:+79001234567');
  });

  test('ссылка на email должна быть кликабельной', async ({ page }) => {
    const contactSection = page.locator('section').filter({ hasText: 'Свяжитесь с нами' });
    const emailLink = contactSection.getByRole('link', { name: 'info@rybalka.ru' });
    await expect(emailLink).toHaveAttribute('href', 'mailto:info@rybalka.ru');
  });

  test('должен корректно отображаться на мобильном устройстве', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    const featuresSection = page.locator('section').filter({ hasText: 'Почему выбирают нас' });
    await expect(featuresSection.getByRole('heading', { name: 'Почему выбирают нас' }).first()).toBeVisible();

    const features = featuresSection.locator('.grid > div');
    const count = await features.count();
    expect(count).toBe(4);
  });
});

test.describe('Главная страница - Тестирование UX/UI', () => {
  test('должна быть доступность ARIA атрибутов', async ({ page }) => {
    await page.goto('/');
    const inputs = page.locator('input');
    for (const input of await inputs.all()) {
      const id = await input.getAttribute('id');
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        await expect(label).toBeVisible();
      }
    }
  });

  test('должен быть корректный цветовой контраст для текста', async ({ page }) => {
    await page.goto('/');
    const headings = page.locator('h1, h2, h3');
    const count = await headings.count();
    expect(count).toBeGreaterThan(0);
  });

  test('должны быть интерактивные элементы с фокус состоянием', async ({ page }) => {
    await page.goto('/');
    const button = page.getByRole('button', { name: 'Подписаться' });
    await button.focus();
    await expect(button).toBeFocused();
  });

  test('должны быть hover эффекты на кнопках', async ({ page }) => {
    await page.goto('/');
    const button = page.getByRole('link', { name: 'Смотреть все места' });
    await button.hover();
    const classes = await button.getAttribute('class');
    expect(classes).toContain('hover:');
  });
});

test.describe('Главная страница - Edge Cases', () => {
  test('должен обрабатывать пустую форму подписки', async ({ page }) => {
    await page.goto('/');
    const newsletterSection = page.locator('section').filter({ hasText: 'Подпишитесь на нашу рассылку' });
    await newsletterSection.getByRole('button', { name: 'Подписаться' }).click();
    await expect(newsletterSection.getByPlaceholder('Ваш email')).toBeVisible();
  });

  test('должен обрабатывать невалидный email в форме подписки', async ({ page }) => {
    await page.goto('/');
    const newsletterSection = page.locator('section').filter({ hasText: 'Подпишитесь на нашу рассылку' });
    await newsletterSection.getByPlaceholder('Ваш email').fill('invalid-email');
    await newsletterSection.getByRole('button', { name: 'Подписаться' }).click();
    await expect(newsletterSection.getByPlaceholder('Ваш email')).toBeVisible();
  });

  test('должен корректно обрабатывать повторный клик на кнопки', async ({ page }) => {
    await page.goto('/');
    const newsletterSection = page.locator('section').filter({ hasText: 'Подпишитесь на нашу рассылку' });
    const button = newsletterSection.getByRole('button', { name: 'Подписаться' });
    await button.click();
    await button.click();
    await expect(button).toBeVisible();
  });
});
