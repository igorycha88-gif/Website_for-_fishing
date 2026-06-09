import { FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const { baseURL, storageState } = config.projects[0].use;
  console.log('Global setup: authenticating...');

  const { chromium } = await import('@playwright/test');
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto(`${baseURL}/login`);

  const timestamp = Date.now();
  const email = `test_${timestamp}@example.com`;
  const password = 'Password123!';

  await page.getByPlaceholder('your@email.com').fill(email);
  await page.getByPlaceholder('••••••••').fill(password);
  await page.getByRole('main').getByRole('button', { name: 'Войти' }).click();

  await page.waitForURL('/profile');

  await context.storageState({ path: 'e2e/.auth/user.json' });

  await context.close();
  await browser.close();
}

export default globalSetup;
