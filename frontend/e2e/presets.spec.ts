import { test, expect } from '@playwright/test';

test.describe('SevaDristi Document Verification Presets', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Preset RED: Income Mismatch triggers REJECTED status', async ({ page }) => {
    // Click Preset: Income Mismatch (Red)
    const redBtn = page.locator('button', { hasText: /Income Mismatch/i });
    await expect(redBtn).toBeVisible();
    await redBtn.click();

    // Verify Audit Certificate Card renders
    await expect(page.locator('text=VERIFICATION REPORT')).toBeVisible({ timeout: 10000 });

    // Expect status badge REJECTED
    const statusBadge = page.locator('span', { hasText: /REJECTED/i }).first();
    await expect(statusBadge).toBeVisible();
    await expect(page.locator('text=ACTION REQUIRED')).toBeVisible();
  });

  test('Preset YELLOW: Blurred Document triggers NEEDS_REVIEW status', async ({ page }) => {
    // Click Preset: Blurred Document (Yellow)
    const yellowBtn = page.locator('button', { hasText: /Blurred Document/i });
    await expect(yellowBtn).toBeVisible();
    await yellowBtn.click();

    // Verify Audit Certificate Card renders
    await expect(page.locator('text=VERIFICATION REPORT')).toBeVisible({ timeout: 10000 });

    // Expect status badge NEEDS_REVIEW
    const statusBadge = page.locator('span', { hasText: /NEEDS_REVIEW/i }).first();
    await expect(statusBadge).toBeVisible();
    // Vision gate flagged blur
    await expect(page.locator('text=Image Quality Assessment')).toBeVisible();
  });

  test('Preset GREEN: Authentic Document triggers READY status with QR code', async ({ page }) => {
    // Click Preset: Authentic Document (Green)
    const greenBtn = page.locator('button', { hasText: /Authentic Document/i });
    await expect(greenBtn).toBeVisible();
    await greenBtn.click();

    // Verify Audit Certificate Card renders
    await expect(page.locator('text=VERIFICATION REPORT')).toBeVisible({ timeout: 10000 });

    // Expect status badge READY
    const statusBadge = page.locator('span', { hasText: /READY/i }).first();
    await expect(statusBadge).toBeVisible();

    // QR Token must be rendered
    await expect(page.locator('text=SECURE OPERATOR TOKEN')).toBeVisible();
    await expect(page.locator('text=HMAC-SHA256 SIGNED')).toBeVisible();
  });

  test('Preset GLARE: High Flash Glare triggers NEEDS_REVIEW status', async ({ page }) => {
    // Click Preset: High Glare (Yellow)
    const glareBtn = page.locator('button', { hasText: /High Glare/i });
    await expect(glareBtn).toBeVisible();
    await glareBtn.click();

    // Verify Audit Certificate Card renders
    await expect(page.locator('text=VERIFICATION REPORT')).toBeVisible({ timeout: 10000 });

    // Expect status badge NEEDS_REVIEW
    const statusBadge = page.locator('span', { hasText: /NEEDS_REVIEW/i }).first();
    await expect(statusBadge).toBeVisible();
  });
});
