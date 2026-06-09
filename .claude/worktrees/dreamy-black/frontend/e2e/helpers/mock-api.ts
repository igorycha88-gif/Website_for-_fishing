import { Page } from '@playwright/test';

export const MOCK_USER = {
  id: '1',
  email: 'test@example.com',
  username: 'testuser',
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z'
};

export const MOCK_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test';

export const mockAuthAPI = (page: Page) => {
  page.route('**/api/v1/auth/login', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: MOCK_TOKEN,
        token_type: 'bearer'
      })
    });
  });

  page.route('**/api/v1/auth/register', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: 'Verification code sent to your email'
      })
    });
  });

  page.route('**/api/v1/users/me', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_USER)
    });
  });
};

export const mockAuthAPIError = (page: Page, endpoint: string, error: string = 'Invalid credentials') => {
  page.route(`**${endpoint}`, async route => {
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: {
          code: 'INVALID_CREDENTIALS',
          message: error
        }
      })
    });
  });
};

export const mockPasswordResetAPI = (page: Page) => {
  page.route('**/api/v1/auth/reset-password/request', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: 'Password reset code sent to your email!'
      })
    });
  });

  page.route('**/api/v1/auth/reset-password/confirm', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: MOCK_TOKEN,
        token_type: 'bearer'
      })
    });
  });
};

export const mockPlacesAPI = (page: Page) => {
  page.route('**/api/v1/places', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: '1',
          title: 'Тестовое место',
          description: 'Описание тестового места',
          latitude: 55.7558,
          longitude: 37.6173,
          address: 'Москва, Россия',
          city: 'Москва',
          price_per_day: 1000,
          max_people: 5,
          facilities: ['parking', 'toilet'],
          fish_types: ['carp', 'bream'],
          images: ['https://example.com/image1.jpg'],
          is_public: false
        }
      ])
    });
  });
};

export const mockNetworkError = (page: Page, pattern: string = '**/api/v1/**') => {
  page.route(pattern, route => route.abort('failed'));
};

export const setupMockAuth = async (page: Page) => {
  await page.goto('/login');
  mockAuthAPI(page);
};
