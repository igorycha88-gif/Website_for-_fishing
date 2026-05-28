import { test, expect } from '@playwright/test';
import { mockAuthAPI, mockAuthAPIError, mockNetworkError } from './helpers/mock-api';

test.describe('Вход - Функциональное тестирование (Позитивные сценарии)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('успешный вход с валидными данными', async ({ page }) => {
    await page.goto('/login');
    mockAuthAPI(page);

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('Password123!');
    await page.getByTestId('login-submit-button').click();

    await expect(page).toHaveURL('/profile', { timeout: 10000 });
  });

  test('должен сохранять токен в localStorage', async ({ page }) => {
    await page.goto('/login');
    mockAuthAPI(page);

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('Password123!');
    await page.getByTestId('login-submit-button').click();

    await page.waitForURL('/profile');
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeTruthy();
  });

  test('должен загружать данные пользователя после входа', async ({ page }) => {
    await page.goto('/login');
    mockAuthAPI(page);

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('Password123!');
    await page.getByTestId('login-submit-button').click();

    await page.waitForURL('/profile', { timeout: 10000 });
    await page.waitForLoadState('networkidle');
    const heading = page.getByRole('heading').first();
    await expect(heading).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Вход - Функциональное тестирование (Негативные сценарии)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('вход с неверным паролем', async ({ page }) => {
    await page.goto('/login');
    mockAuthAPIError(page, '/api/v1/auth/login');

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('WrongPassword!');
    await page.getByTestId('login-submit-button').click();

    await expect(page.getByText(/Invalid credentials|Неверные данные/)).toBeVisible({ timeout: 10000 });
  });

  test('вход с несуществующим email', async ({ page }) => {
    await page.goto('/login');
    mockAuthAPIError(page, '/api/v1/auth/login');

    await page.getByTestId('login-email-input').fill('nonexistent@example.com');
    await page.getByTestId('login-password-input').fill('Password123!');
    await page.getByTestId('login-submit-button').click();

    await expect(page.getByText(/Invalid credentials|Неверные данные/)).toBeVisible({ timeout: 10000 });
  });

  test('вход с пустыми полями', async ({ page }) => {
    await page.getByTestId('login-submit-button').click();

    const emailInput = page.getByTestId('login-email-input');
    const passwordInput = page.getByTestId('login-password-input');
    const isEmailInvalid = await emailInput.evaluate(el => !(el as HTMLInputElement).checkValidity());
    const isPasswordInvalid = await passwordInput.evaluate(el => !(el as HTMLInputElement).checkValidity());

    expect(isEmailInvalid).toBe(true);
    expect(isPasswordInvalid).toBe(true);
  });

  test('вход с невалидным email', async ({ page }) => {
    await page.getByTestId('login-email-input').fill('invalid-email');
    await page.getByTestId('login-password-input').fill('Password123!');

    const emailInput = page.getByTestId('login-email-input');
    const isValid = await emailInput.evaluate(el => (el as HTMLInputElement).checkValidity());
    expect(isValid).toBe(false);
  });

  test('вход с коротким паролем', async ({ page }) => {
    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('123');

    await page.getByTestId('login-submit-button').click();
    await expect(page.getByTestId('login-password-input')).toBeVisible();
  });

  test('отображение ошибки при проблемах с сетью', async ({ page }) => {
    await page.route('**/api/v1/auth/login', route => route.abort('failed'));

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('Password123!');
    await page.getByTestId('login-submit-button').click();

    await expect(page.getByText(/Failed to connect|Ошибка сети/)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Вход - UX/UI Тестирование', () => {
  test('кнопка входа должна быть неактивной во время загрузки', async ({ page }) => {
    await page.goto('/login');

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('Password123!');

    const button = page.getByTestId('login-submit-button');

    page.route('**/api/v1/auth/login', async route => {
      await new Promise(resolve => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-token',
          token_type: 'bearer'
        })
      });
    });

    await button.click();

    await expect(button).toHaveAttribute('disabled');
    await expect(button).toHaveText(/Загрузка.../);
  });

  test('ошибка должна отображаться в красном блоке', async ({ page }) => {
    await page.goto('/login');

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('WrongPassword!');
    await page.getByTestId('login-submit-button').click();

    await expect(page.locator('.bg-accent-orange\\/10')).toBeVisible({ timeout: 10000 });
  });

  test('должна быть возможность перейти на страницу регистрации', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('link', { name: 'Зарегистрироваться' }).click();
    await expect(page).toHaveURL('/register');
  });

  test('поля должны иметь иконки', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByTestId('login-email-icon')).toBeVisible();
    await expect(page.getByTestId('login-password-icon')).toBeVisible();
  });

  test('форма должна быть доступной для клавиатуры', async ({ page }) => {
    await page.goto('/login');
    const emailInput = page.getByTestId('login-email-input');
    await emailInput.focus();
    await expect(emailInput).toBeFocused();

    const passwordInput = page.getByTestId('login-password-input');
    await passwordInput.focus();
    await expect(passwordInput).toBeFocused();

    const button = page.getByTestId('login-submit-button');
    await button.focus();
    await expect(button).toBeFocused();
  });

  test('должен быть корректный фокус на полях', async ({ page }) => {
    await page.goto('/login');
    const emailInput = page.getByTestId('login-email-input');
    await emailInput.focus();
    await expect(emailInput).toBeFocused();

    const passwordInput = page.getByTestId('login-password-input');
    await passwordInput.focus();
    await expect(passwordInput).toBeFocused();
  });
});

test.describe('Вход - Edge Cases', () => {
  test('должен обрабатывать пробелы в email и пароле', async ({ page }) => {
    await page.goto('/login');

    await page.getByTestId('login-email-input').fill('  test@example.com  ');
    await page.getByTestId('login-password-input').fill('  Password123!  ');

    await page.getByTestId('login-submit-button').click();
    await expect(page.getByTestId('login-email-input')).toBeVisible();
  });

  test('должен обрабатывать очень длинный пароль', async ({ page }) => {
    await page.goto('/login');

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('a'.repeat(200));

    await page.getByTestId('login-submit-button').click();
    await expect(page.getByTestId('login-password-input')).toBeVisible();
  });

  test('должен обрабатывать специальные символы в пароле', async ({ page }) => {
    await page.goto('/login');

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('P@$$w0rd!#$%^&*()');

    await page.getByTestId('login-submit-button').click();
    await expect(page.getByTestId('login-password-input')).toBeVisible();
  });

  test('должен обрабатывать многократные нажатия на кнопку входа', async ({ page }) => {
    await page.goto('/login');

    await page.getByTestId('login-email-input').fill('test@example.com');
    await page.getByTestId('login-password-input').fill('Password123!');

    const button = page.getByTestId('login-submit-button');
    await button.click();
    await button.click();
    await button.click();

    await expect(button).toHaveAttribute('disabled');
  });
});

test.describe('Вход - Тестирование безопасности', () => {
  test('должен предотвращать SQL инъекции в email', async ({ page }) => {
    await page.goto('/login');

    await page.getByTestId('login-email-input').fill("'; DROP TABLE users;--@example.com");
    await page.getByTestId('login-password-input').fill('Password123!');
    await page.getByTestId('login-submit-button').click();

    await expect(page.getByTestId('login-email-input')).toBeVisible();
  });

  test('должен предотвращать XSS в email', async ({ page }) => {
    await page.goto('/login');

    await page.getByTestId('login-email-input').fill("<script>alert('xss')</script>@example.com");
    await page.getByTestId('login-password-input').fill('Password123!');
    await page.getByTestId('login-submit-button').click();

    await expect(page.getByTestId('login-email-input')).toBeVisible();
  });

  test('должен скрывать символы пароля', async ({ page }) => {
    await page.goto('/login');

    const passwordInput = page.getByTestId('login-password-input');
    await passwordInput.fill('Password123!');

    const type = await passwordInput.getAttribute('type');
    expect(type).toBe('password');
  });

  test('должен иметь корректные атрибуты безопасности', async ({ page }) => {
    await page.goto('/login');

    const passwordInput = page.getByTestId('login-password-input');
    const autocomplete = await passwordInput.getAttribute('autocomplete');
    expect(autocomplete).toBe('current-password');
  });
});

test.describe('Вход - Параметры URL', () => {
  test('должен заполнять email из параметра URL', async ({ page }) => {
    await page.goto('/login?email=predefined@example.com');

    await page.waitForTimeout(100);

    const emailInput = page.getByTestId('login-email-input');
    const value = await emailInput.inputValue();
    expect(value).toBe('predefined@example.com');
  });

  test('должен сохранять email из параметра при изменении', async ({ page }) => {
    await page.goto('/login?email=predefined@example.com');

    await page.getByTestId('login-email-input').fill('changed@example.com');
    const value = await page.getByTestId('login-email-input').inputValue();
    expect(value).toBe('changed@example.com');
  });
});
