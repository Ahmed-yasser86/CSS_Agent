import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000';

test('channel workspace Network tab renders the network graph', async ({ page }) => {
  test.setTimeout(180000);
  await page.goto(`${BASE_URL}/channels/UC-1rx8j9Ggp8mp4uD0ZdEIA`);
  await page.getByRole('tab', { name: 'Network' }).click();
  await expect(page.locator('canvas').first()).toBeVisible({ timeout: 120000 });
  await expect(page.getByLabel('Search nodes')).toBeVisible({ timeout: 10000 });
  await expect(page.getByLabel('Minimum degree')).toBeVisible({ timeout: 10000 });
});

test('video workspace Network tab renders the ego graph', async ({ page }) => {
  test.setTimeout(180000);
  await page.goto(`${BASE_URL}/videos/aqz-KE-bpKQ`);
  await page.getByRole('tab', { name: 'Network' }).click();
  await expect(page.locator('canvas').first()).toBeVisible({ timeout: 120000 });
});
