import { defineConfig, devices } from '@playwright/test';

// E2E tests drive a real browser as a user against a running frontend + backend.
// By default we start an isolated dev server on :3100 (so it won't clash with a
// dev server you already have on :3000/:3001). The backend must be running on
// :8000 (the frontend's .env.local NEXT_PUBLIC_API_URL points there), and its
// dev CORS rule allows any localhost port.
//
// To run against an already-running frontend instead, set PLAYWRIGHT_BASE_URL,
// e.g.  PLAYWRIGHT_BASE_URL=http://localhost:3001 npx playwright test
const PORT = 3100;
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: BASE_URL,
    headless: true,
    actionTimeout: 20_000,
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        command: `npm run dev -- -p ${PORT}`,
        url: BASE_URL,
        timeout: 120_000,
        reuseExistingServer: true,
        stdout: 'ignore',
        stderr: 'pipe',
      },
});
