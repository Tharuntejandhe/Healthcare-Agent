import { test, expect, type Page } from '@playwright/test';
import path from 'node:path';

const PASSWORD = 'testpass12345';
const REPORT_PDF = path.join(__dirname, 'fixtures', 'report.pdf');

function uniqueEmail(): string {
  return `e2e-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
}

/** Sign up a fresh account through the real UI and land on the dashboard. */
async function signupAndLand(page: Page): Promise<string> {
  const email = uniqueEmail();
  await page.goto('/signup');
  await page.getByPlaceholder('Dr. Jane Smith').fill('E2E User');
  await page.getByPlaceholder('you@clinic.com').fill(email);
  await page.getByPlaceholder('At least 8 characters').fill(PASSWORD);
  await page.getByRole('button', { name: 'Create account' }).click();
  await page.waitForURL('**/dashboard', { timeout: 30_000 });
  return email;
}

test('landing page loads', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/MediHealth/i);
});

test('protected route redirects unauthenticated user to /login', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForURL('**/login', { timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
});

test('signup → dashboard with empty state', async ({ page }) => {
  await signupAndLand(page);
  await expect(page.getByRole('heading', { name: 'Patient Dashboard' })).toBeVisible();
  await expect(page.getByText('Your clinical vault is empty')).toBeVisible();
});

test('login flow works for an existing account', async ({ page }) => {
  // create an account, sign out, then sign back in via the login form
  const email = await signupAndLand(page);
  await page.getByRole('button', { name: /sign out/i }).first().click();
  await page.waitForURL('**/login', { timeout: 15_000 });

  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('**/dashboard', { timeout: 30_000 });
  await expect(page.getByRole('heading', { name: 'Patient Dashboard' })).toBeVisible();
});

test('upload a PDF report → it appears on the dashboard', async ({ page }) => {
  await signupAndLand(page);
  // The file input is hidden behind a styled label; setInputFiles works regardless.
  await page.locator('#report-upload').setInputFiles(REPORT_PDF);
  // Card shows the uploaded filename once stored/indexed.
  await expect(page.getByText('report.pdf')).toBeVisible({ timeout: 60_000 });
});

test('chat round-trip: send a message and get an AI reply with disclaimer', async ({ page }) => {
  await signupAndLand(page);
  await page.goto('/chat');
  await expect(page.getByPlaceholder('Ask your medical query…')).toBeVisible();
  await page.getByPlaceholder('Ask your medical query…').fill('What does a high fasting glucose mean?');
  await page.getByRole('button', { name: 'Send message' }).click();
  // Every AI health response carries the standardized safety disclaimer — its
  // presence proves the full vision/graph/Groq round-trip succeeded.
  await expect(page.getByText(/not a substitute for professional medical/i)).toBeVisible({ timeout: 45_000 });
});

test('logout clears the session and re-protects the dashboard', async ({ page }) => {
  await signupAndLand(page);
  await page.getByRole('button', { name: /sign out/i }).first().click();
  await page.waitForURL('**/login', { timeout: 15_000 });
  // Token gone → visiting a protected page bounces back to login.
  await page.goto('/dashboard');
  await page.waitForURL('**/login', { timeout: 15_000 });
});
