import { test, expect } from '@playwright/test';
import { BACKEND_URL, FRONTEND_URL, login } from './helpers';

// Requires the running demo stack (scripts/start_demo.ps1). Every assertion targets real pages
// and real backend responses; nothing is mocked or intercepted.

test.describe('TIDES-AI access control and core pages', () => {
  test('login page renders and rejects invalid credentials', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);
    await expect(page.getByRole('heading', { name: 'TIDES-AI' })).toBeVisible();
    // Password is never prefilled
    await expect(page.locator('input[type="password"]')).toHaveValue('');
    await page.locator('input[type="email"]').fill('nobody@tides.ai');
    await page.locator('input[type="password"]').fill('definitely-wrong-password');
    await page.locator('button[type="submit"]').click();
    await expect(page.locator('text=/invalid|incorrect|failed|credentials/i').first()).toBeVisible({ timeout: 10000 });
    await expect(page).toHaveURL(/\/login/);
  });

  test('protected pages redirect to login when signed out', async ({ page }) => {
    for (const route of ['/dashboard', '/applications', '/applications/new']) {
      await page.goto(`${FRONTEND_URL}${route}`);
      await page.waitForURL('**/login', { timeout: 10000 });
    }
  });

  test('backend API refuses unauthenticated access to applications', async ({ request }) => {
    const res = await request.get(`${BACKEND_URL}/api/v1/applications`);
    expect(res.status()).toBe(401);
  });

  test('dashboard shows database-backed statistics after login', async ({ page }) => {
    const dashboardResponse = page.waitForResponse((r) => r.url().startsWith(`${BACKEND_URL}/api/v1/applications-dashboard`) && r.status() === 200);
    await login(page);
    const body = await (await dashboardResponse).json();
    await expect(page.getByTestId('stat-total')).toHaveText(String(body.total_applications));
    await expect(page.getByTestId('stat-completed')).toHaveText(String(body.completed_evaluations));
  });
});
