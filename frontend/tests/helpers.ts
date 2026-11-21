import * as fs from 'fs';
import * as path from 'path';
import type { Page } from '@playwright/test';

export const FRONTEND_URL = process.env.TIDES_FRONTEND_URL || 'http://localhost:3000';
export const BACKEND_URL = process.env.TIDES_BACKEND_URL || 'http://127.0.0.1:8000';
export const ROOT_DIR = path.resolve(__dirname, '../..');
export const FIXTURES_DIR = path.join(ROOT_DIR, 'demo_fixtures');
export const DISCLOSURE = 'MOCK DEMONSTRATION — OFFLINE SYNTHETIC RESULTS — NOT A REAL AI EVALUATION';

/** Demo credentials come from the gitignored .env.demo written by scripts/init_demo_db.py. */
export function demoCredentials(): { email: string; password: string } {
  const envEmail = process.env.TIDES_DEMO_EMAIL;
  const envPassword = process.env.TIDES_DEMO_PASSWORD;
  if (envEmail && envPassword) return { email: envEmail, password: envPassword };
  const file = path.join(ROOT_DIR, '.env.demo');
  if (!fs.existsSync(file)) throw new Error('Run scripts/init_demo_db.py (or scripts/start_demo.ps1) first: .env.demo not found');
  const values: Record<string, string> = {};
  for (const line of fs.readFileSync(file, 'utf-8').split(/\r?\n/)) {
    const i = line.indexOf('=');
    if (i > 0 && !line.startsWith('#')) values[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  }
  return { email: values.TIDES_DEMO_EMAIL, password: values.TIDES_DEMO_PASSWORD };
}

export async function login(page: Page) {
  const { email, password } = demoCredentials();
  await page.goto(`${FRONTEND_URL}/login`);
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL('**/dashboard', { timeout: 15000 });
}
