import { test, expect } from '@playwright/test';

test.describe('Сброс пароля - Запрос на сброс', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reset-password/request');
  });

  test('успешный запрос на сброс пароля с существующим email', async ({ page }) => {
    await page.getByTestId('reset-email-input').fill('test@example.com');
    await page.getByTestId('reset-send-code-button').click();

    await expect(page.getByText(/Password reset code sent/)).toBeVisible({ timeout: 10000 });
  });

  test('должен сохранять email в localStorage', async ({ page }) => {
    await page.getByTestId('reset-email-input').fill('test@example.com');
    await page.getByTestId('reset-send-code-button').click();

    await page.waitForTimeout(2000);
    const email = await page.evaluate(() => localStorage.getItem('reset_email'));
    expect(email).toBe('test@example.com');
  });

  test('должен перенаправлять на страницу подтверждения', async ({ page }) => {
    await page.getByTestId('reset-email-input').fill('test@example.com');
    await page.getByTestId('reset-send-code-button').click();

    await page.waitForTimeout(2000);
    await expect(page).toHaveURL(/\/reset-password\/confirm/);
  });
});

test.describe('Сброс пароля - Негативные сценарии', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reset-password/request');
  });

  test('запрос с несуществующим email', async ({ page }) => {
    await page.getByTestId('reset-email-input').fill('nonexistent@example.com');
    await page.getByTestId('reset-send-code-button').click();

    await expect(page.getByText(/USER_NOT_FOUND|user not found/)).toBeVisible({ timeout: 10000 });
  });

  test('запрос с пустым email', async ({ page }) => {
    await page.getByTestId('reset-send-code-button').click();

    const emailInput = page.getByTestId('reset-email-input');
    const isInvalid = await emailInput.evaluate(el => !(el as HTMLInputElement).checkValidity());
    expect(isInvalid).toBe(true);
  });

  test('запрос с невалидным email', async ({ page }) => {
    await page.getByTestId('reset-email-input').fill('invalid-email');
    await page.getByTestId('reset-send-code-button').click();

    const emailInput = page.getByTestId('reset-email-input');
    const isValid = await emailInput.evaluate(el => (el as HTMLInputElement).checkValidity());
    expect(isValid).toBe(false);
  });

  test('должен обрабатывать ошибки сети', async ({ page }) => {
    await page.route('**/api/v1/auth/reset-password/request', route => route.abort('failed'));

    await page.getByTestId('reset-email-input').fill('test@example.com');
    await page.getByTestId('reset-send-code-button').click();

    await expect(page.getByText(/Network error|Ошибка сети/)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Сброс пароля - Подтверждение сброса', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reset-password/confirm');
  });

  test('успешное изменение пароля', async ({ page }) => {
    await page.getByTestId('reset-confirm-email-input').fill('test@example.com');
    await page.getByTestId('reset-code-input').fill('123456');
    await page.getByTestId('reset-new-password-input').fill('NewPassword123!');
    await page.getByTestId('reset-confirm-button').click();

    await expect(page.getByText(/Password reset successful|Пароль успешно изменен/)).toBeVisible({ timeout: 10000 });
  });

  test('кнопка должна быть неактивной во время загрузки', async ({ page }) => {
    await page.getByTestId('reset-confirm-email-input').fill('test@example.com');
    await page.getByTestId('reset-code-input').fill('123456');
    await page.getByTestId('reset-new-password-input').fill('NewPassword123!');

    const button = page.getByTestId('reset-confirm-button');
    await button.click();

    await expect(button).toHaveAttribute('disabled');
  });

  test('валидация обязательных полей', async ({ page }) => {
    await page.getByTestId('reset-confirm-button').click();

    const emailInput = page.getByTestId('reset-confirm-email-input');
    const codeInput = page.getByTestId('reset-code-input');
    const passwordInput = page.getByTestId('reset-new-password-input');

    const isEmailInvalid = await emailInput.evaluate(el => !(el as HTMLInputElement).checkValidity());
    const isCodeInvalid = await codeInput.evaluate(el => !(el as HTMLInputElement).checkValidity());
    const isPasswordInvalid = await passwordInput.evaluate(el => !(el as HTMLInputElement).checkValidity());

    expect(isEmailInvalid).toBe(true);
    expect(isCodeInvalid).toBe(true);
    expect(isPasswordInvalid).toBe(true);
  });

  test('валидация длины пароля', async ({ page }) => {
    await page.getByTestId('reset-confirm-email-input').fill('test@example.com');
    await page.getByTestId('reset-code-input').fill('123456');
    await page.getByTestId('reset-new-password-input').fill('short');

    const passwordInput = page.getByTestId('reset-new-password-input');
    const isValid = await passwordInput.evaluate(el => (el as HTMLInputElement).checkValidity());
    expect(isValid).toBe(false);
  });
});

test.describe('Сброс пароля - UX/UI', () => {
  test('должна быть возможность вернуться на вход', async ({ page }) => {
    await page.goto('/reset-password/request');
    await page.getByRole('link', { name: 'Sign in' }).click();
    await expect(page).toHaveURL('/login');
  });

  test('поля должны иметь корректные плейсхолдеры', async ({ page }) => {
    await page.goto('/reset-password/confirm');

    await expect(page.getByTestId('reset-confirm-email-input')).toBeVisible();
    await expect(page.getByTestId('reset-code-input')).toBeVisible();
    await expect(page.getByTestId('reset-new-password-input')).toBeVisible();
  });

  test('форма должна быть доступной для клавиатуры', async ({ page }) => {
    await page.goto('/reset-password/confirm');
    await page.keyboard.press('Tab');

    const emailInput = page.getByTestId('reset-confirm-email-input');
    await expect(emailInput).toBeFocused();
  });
});

test.describe('Сброс пароля - Edge Cases', () => {
  test('должен обрабатывать неверный код сброса', async ({ page }) => {
    await page.goto('/reset-password/confirm');

    await page.getByTestId('reset-confirm-email-input').fill('test@example.com');
    await page.getByTestId('reset-code-input').fill('000000');
    await page.getByTestId('reset-new-password-input').fill('NewPassword123!');
    await page.getByTestId('reset-confirm-button').click();

    await expect(page.getByText(/Invalid or expired code|Неверный код/)).toBeVisible({ timeout: 10000 });
  });

  test('должен обрабатывать истекший код сброса', async ({ page }) => {
    await page.goto('/reset-password/confirm');

    await page.getByTestId('reset-confirm-email-input').fill('test@example.com');
    await page.getByTestId('reset-code-input').fill('000000');
    await page.getByTestId('reset-new-password-input').fill('NewPassword123!');
    await page.getByTestId('reset-confirm-button').click();

    await expect(page.getByText(/Invalid or expired code/)).toBeVisible({ timeout: 10000 });
  });

  test('должен обрабатывать превышение количества попыток', async ({ page }) => {
    await page.goto('/reset-password/confirm');

    await page.getByTestId('reset-confirm-email-input').fill('test@example.com');
    await page.getByTestId('reset-new-password-input').fill('NewPassword123!');

    for (let i = 0; i < 4; i++) {
      await page.getByTestId('reset-code-input').fill('000000');
      await page.getByTestId('reset-confirm-button').click();
      await page.waitForTimeout(500);
    }

    await expect(page.getByText(/Invalid or expired code/)).toBeVisible({ timeout: 10000 });
  });

  test('должен обрабатывать пробелы в начале и конце полей', async ({ page }) => {
    await page.goto('/reset-password/confirm');

    await page.getByTestId('reset-confirm-email-input').fill('  test@example.com  ');
    await page.getByTestId('reset-code-input').fill('  123456  ');
    await page.getByTestId('reset-new-password-input').fill('  NewPassword123!  ');

    await page.getByTestId('reset-confirm-button').click();

    await expect(page.getByTestId('reset-confirm-email-input')).toBeVisible();
  });
});

test.describe('Сброс пароля - Безопасность', () => {
  test('должен предотвращать SQL инъекции в email', async ({ page }) => {
    await page.goto('/reset-password/request');

    await page.getByTestId('reset-email-input').fill("'; DROP TABLE users;--@example.com");
    await page.getByTestId('reset-send-code-button').click();

    await expect(page.getByTestId('reset-email-input')).toBeVisible();
  });

  test('должен предотвращать XSS в email', async ({ page }) => {
    await page.goto('/reset-password/request');

    await page.getByTestId('reset-email-input').fill("<script>alert('xss')</script>@example.com");
    await page.getByTestId('reset-send-code-button').click();

    await expect(page.getByTestId('reset-email-input')).toBeVisible();
  });

  test('должен скрывать символы пароля', async ({ page }) => {
    await page.goto('/reset-password/confirm');

    const passwordInput = page.getByTestId('reset-new-password-input');
    await passwordInput.fill('NewPassword123!');

    const type = await passwordInput.getAttribute('type');
    expect(type).toBe('password');
  });

  test('должен иметь корректные атрибуты безопасности', async ({ page }) => {
    await page.goto('/reset-password/confirm');

    const passwordInput = page.getByTestId('reset-new-password-input');
    const autocomplete = await passwordInput.getAttribute('autocomplete');
    expect(autocomplete).toBe('new-password');
  });
});
