// e2e/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  workers: 1, // ทุก test ใช้ DB เดียวกันและ reset ใน beforeEach
  use: { baseURL: 'http://localhost:8081', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'cd .. && APP_ENV=test DB_PATH=/tmp/shop-e2e.db .venv/bin/uvicorn app.main:app --port 8081',
    url: 'http://localhost:8081/health',
    reuseExistingServer: false,
    timeout: 30_000,
  },
});

