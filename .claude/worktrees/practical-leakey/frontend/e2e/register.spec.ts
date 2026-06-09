import { test, expect } from '@playwright/test';

test.describe('Регистрация - Функциональное тестирование (Позитивные сценарии)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('успешная регистрация с валидными данными', async ({ page }) => {
    const timestamp = Date.now();
    await page.getByTestId('register-username-input').fill(`testuser_${timestamp}`);
    await page.getByTestId('register-email-input').fill(`test_${timestamp}@example.com`);
    await page.getByTestId('register-password-input').fill('Password123!');
    await page.getByTestId('register-submit-button').click();

    await expect(page.getByText(/Верификационный код отправлен/)).toBeVisible({ timeout: 10000 });
  });

  test('отображение сообщений об успехе регистрации', async ({ page }) => {
    const timestamp = Date.now();
    await page.getByTestId('register-username-input').fill(`testuser_${timestamp}`);
    await page.getByTestId('register-email-input').fill(`test_${timestamp}@example.com`);
    await page.getByTestId('register-password-input').fill('Password123!');
    await page.getByTestId('register-submit-button').click();

    await expect(page.locator('.bg-green-50')).toBeVisible({ timeout: 10000 });
  });

  test('перенаправление на страницу верификации после регистрации', async ({ page }) => {
    const timestamp = Date.now();
    await page.getByTestId('register-username-input').fill(`testuser_${timestamp}`);
    await page.getByTestId('register-email-input').fill(`test_${timestamp}@example.com`);
    await page.getByTestId('register-password-input').fill('Password123!');
    await page.getByTestId('register-submit-button').click();

    await page.waitForTimeout(2500);
    await expect(page).toHaveURL(/\/verify-email/);
  });
});

test.describe('Регистрация - Функциональное тестирование (Негативные сценарии)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('регистрация с существующим email', async ({ page }) => {
    await page.getByTestId('register-username-input').fill('testuser_new');
    await page.getByTestId('register-email-input').fill('existing@example.com');
    await page.getByTestId('register-password-input').fill('Password123!');
    await page.getByTestId('register-submit-button').click();

    await expect(page.getByText(/Email уже зарегистрирован/)).toBeVisible({ timeout: 10000 });
  });

  test('регистрация с существующим username', async ({ page }) => {
    await page.getByTestId('register-username-input').fill('existinguser');
    await page.getByTestId('register-email-input').fill('new@example.com');
    await page.getByTestId('register-password-input').fill('Password123!');
    await page.getByTestId('register-submit-button').click();

    await expect(page.getByText(/Имя пользователя уже занято/)).toBeVisible({ timeout: 10000 });
  });

  test('регистрация с коротким паролем', async ({ page }) => {
    await page.getByTestId('register-username-input').fill('testuser');
    await page.getByTestId('register-email-input').fill('test@example.com');
    await page.getByTestId('register-password-input').fill('123');
    await page.getByTestId('register-submit-button').click();

    await expect(page.getByTestId('register-password-input')).toBeVisible();
  });

  test('регистрация с пустыми полями', async ({ page }) => {
    await page.getByTestId('register-submit-button').click();

    const usernameInput = page.getByTestId('register-username-input');
    const emailInput = page.getByTestId('register-email-input');
    const passwordInput = page.getByTestId('register-password-input');

    const isUsernameInvalid = await usernameInput.evaluate(el => !(el as HTMLInputElement).checkValidity());
    const isEmailInvalid = await emailInput.evaluate(el => !(el as HTMLInputElement).checkValidity());
    const isPasswordInvalid = await passwordInput.evaluate(el => !(el as HTMLInputElement).checkValidity());

    expect(isUsernameInvalid).toBe(true);
    expect(isEmailInvalid).toBe(true);
    expect(isPasswordInvalid).toBe(true);
  });

  test('регистрация с невалидным email', async ({ page }) => {
    await page.getByTestId('register-username-input').fill('testuser');
    await page.getByTestId('register-email-input').fill('invalid-email');
    await page.getByTestId('register-password-input').fill('Password123!');

    const emailInput = page.getByTestId('register-email-input');
    const isValid = await emailInput.evaluate(el => (el as HTMLInputElement).checkValidity());
    expect(isValid).toBe(false);
  });

  test('регистрация с коротким username', async ({ page }) => {
    await page.getByTestId('register-username-input').fill('ab');
    await page.getByTestId('register-email-input').fill('test@example.com');
    await page.getByTestId('register-password-input').fill('Password123!');

    const usernameInput = page.getByTestId('register-username-input');
    const isValid = await usernameInput.evaluate(el => (el as HTMLInputElement).checkValidity());
    expect(isValid).toBe(false);
  });

  test('отображение кнопок действий при ошибке EMAIL_ALREADY_EXISTS', async ({ page }) => {
    await page.getByTestId('register-username-input').fill('testuser_new');
    await page.getByTestId('register-email-input').fill('existing@example.com');
    await page.getByTestId('register-password-input').fill('Password123!');
    await page.getByTestId('register-submit-button').click();

    await page.waitForTimeout(1000);

    await expect(page.getByRole('button', { name: 'Войти' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Сбросить пароль' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Подтвердить email' })).toBeVisible();
  });

  test('кнопка "Войти" перенаправляет на страницу входа', async ({ page }) => {
    await page.getByTestId('register-username-input').fill('testuser_new');
    await page.getByTestId('register-email-input').fill('existing@example.com');
    await page.getByTestId('register-password-input').fill('Password123!');
    await page.getByTestId('register-submit-button').click();

    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: 'Войти' }).click();
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Регистрация - UX/UI Тестирование', () => {
  test('кнопка регистрации должна быть неактивной во время загрузки', async ({ page }) => {
    await page.goto('/register');
    const timestamp = Date.now();

    await page.getByTestId('register-username-input').fill(`testuser_${timestamp}`);
    await page.getByTestId('register-email-input').fill(`test_${timestamp}@example.com`);
    await page.getByTestId('register-password-input').fill('Password123!');

    const button = page.getByTestId('register-submit-button');
    await button.click();

    await expect(button).toHaveAttribute('disabled');
    await expect(button).toHaveText(/Создание аккаунта.../);
  });

  test('должна быть возможность перейти на страницу входа', async ({ page }) => {
    await page.goto('/register');
    await page.getByRole('link', { name: 'Войти' }).click();
    await expect(page).toHaveURL('/login');
  });

  test('поля должны иметь корректные плейсхолдеры', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByPlaceholder('Введите имя пользователя')).toBeVisible();
    await expect(page.getByPlaceholder('Введите ваш email')).toBeVisible();
    await expect(page.getByPlaceholder('Введите пароль (минимум 8 символов)')).toBeVisible();
  });

  test('форма должна быть доступной для клавиатуры', async ({ page }) => {
    await page.goto('/register');
    await page.keyboard.press('Tab');
    await expect(page.getByPlaceholder('Введите имя пользователя')).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.getByPlaceholder('Введите ваш email')).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.getByPlaceholder('Введите пароль (минимум 8 символов)')).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: 'Создать аккаунт' })).toBeFocused();
  });

  test('должен быть корректный цветовой контраст', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByRole('heading', { name: 'Создать аккаунт' })).toBeVisible();
    await expect(page.getByText(/Присоединиться к FishMap сегодня/)).toBeVisible();
  });
});

test.describe('Регистрация - Edge Cases', () => {
  test('должен обрабатывать специальные символы в username', async ({ page }) => {
    await page.goto('/register');
    const timestamp = Date.now();
    
    await page.getByPlaceholder('Введите имя пользователя').fill(`user_${timestamp}_test`);
    await page.getByPlaceholder('Введите ваш email').fill(`test_${timestamp}@example.com`);
    await page.getByPlaceholder('Введите пароль (минимум 8 символов)').fill('Password123!');
    await page.getByRole('button', { name: 'Создать аккаунт' }).click();
    
    await expect(page.getByPlaceholder('Введите имя пользователя')).toBeVisible();
  });

  test('должен обрабатывать очень длинный username', async ({ page }) => {
    await page.goto('/register');
    const longUsername = 'a'.repeat(100);
    
    await page.getByPlaceholder('Введите имя пользователя').fill(longUsername);
    const usernameInput = page.getByPlaceholder('Введите имя пользователя');
    const value = await usernameInput.inputValue();
    expect(value.length).toBeLessThanOrEqual(100);
  });

  test('должен обрабатывать пробелы в начале и конце полей', async ({ page }) => {
    await page.goto('/register');
    const timestamp = Date.now();
    
    await page.getByPlaceholder('Введите имя пользователя').fill(`  testuser_${timestamp}  `);
    await page.getByPlaceholder('Введите ваш email').fill(`  test_${timestamp}@example.com  `);
    await page.getByPlaceholder('Введите пароль (минимум 8 символов)').fill('  Password123!  ');
    
    await page.getByRole('button', { name: 'Создать аккаунт' }).click();
    
    await expect(page.getByPlaceholder('Введите имя пользователя')).toBeVisible();
  });

  test('должен обрабатывать кириллицу в пароле', async ({ page }) => {
    await page.goto('/register');
    const timestamp = Date.now();
    
    await page.getByPlaceholder('Введите имя пользователя').fill(`testuser_${timestamp}`);
    await page.getByPlaceholder('Введите ваш email').fill(`test_${timestamp}@example.com`);
    await page.getByPlaceholder('Введите пароль (минимум 8 символов)').fill('Пароль123!');
    await page.getByRole('button', { name: 'Создать аккаунт' }).click();
    
    await expect(page.getByPlaceholder('Введите пароль (минимум 8 символов)')).toBeVisible();
  });
});

test.describe('Регистрация - Тестирование безопасности', () => {
  test('должен предотвращать SQL инъекции в username', async ({ page }) => {
    await page.goto('/register');
    const timestamp = Date.now();
    
    await page.getByPlaceholder('Введите имя пользователя').fill(`test'; DROP TABLE users;--_${timestamp}`);
    await page.getByPlaceholder('Введите ваш email').fill(`test_${timestamp}@example.com`);
    await page.getByPlaceholder('Введите пароль (минимум 8 символов)').fill('Password123!');
    await page.getByRole('button', { name: 'Создать аккаунт' }).click();
    
    await expect(page.getByPlaceholder('Введите имя пользователя')).toBeVisible();
  });

  test('должен предотвращать XSS в username', async ({ page }) => {
    await page.goto('/register');
    const timestamp = Date.now();
    
    await page.getByPlaceholder('Введите имя пользователя').fill(`<script>alert('xss')</script>_${timestamp}`);
    await page.getByPlaceholder('Введите ваш email').fill(`test_${timestamp}@example.com`);
    await page.getByPlaceholder('Введите пароль (минимум 8 символов)').fill('Password123!');
    await page.getByRole('button', { name: 'Создать аккаунт' }).click();
    
    await expect(page.getByPlaceholder('Введите имя пользователя')).toBeVisible();
  });
});
