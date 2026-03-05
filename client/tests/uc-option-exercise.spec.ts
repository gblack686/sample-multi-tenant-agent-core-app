import { test, expect } from '@playwright/test';

/**
 * UC-03: Option Exercise Package Preparation
 *
 * Simulates a contracting officer preparing an annual option exercise
 * package for an existing contract. Verifies the agent acknowledges
 * the option exercise scenario, asks about cost escalation / COR changes,
 * and produces package guidance after follow-up details.
 */
test.describe('UC-03: Option Exercise Package Preparation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/chat/');
    await page.getByRole('button', { name: 'New Chat' }).click();
    await expect(page.getByRole('heading', { name: /Welcome to EAGLE/i })).toBeVisible();
  });

  test('option exercise request → package guidance with follow-up', async ({ page }) => {
    test.slow(); // 90s budget for agent streaming

    // Send option exercise message
    const textarea = page.getByPlaceholder(/Ask EAGLE/i);
    await textarea.fill(
      'I need to exercise Option Year 3 on contract NCI-2024-0847. The base period was $1.2M for IT support services. I have the previous year\'s package.'
    );
    await expect(page.getByRole('button', { name: '➤' })).toBeEnabled();
    await page.getByRole('button', { name: '➤' }).click();

    // Agent responds acknowledging the option exercise scenario
    await expect(page.locator('main').getByText('🦅 EAGLE')).toHaveCount(1, { timeout: 60000 });
    await expect(page.locator('main')).toContainText(
      /option|exercise|contract|NCI-2024-0847|option year/i
    );

    // Response should ask about cost escalation, COR changes, or scope updates
    await expect(page.locator('main')).toContainText(
      /escalation|cost|COR|scope|change|update|modification|pricing/i
    );

    // Send follow-up with details
    await textarea.fill(
      '3% cost escalation per the contract terms. New COR is Dr. Sarah Chen. No scope changes.'
    );
    await expect(page.getByRole('button', { name: '➤' })).toBeEnabled();
    await page.getByRole('button', { name: '➤' }).click();

    // Agent responds with package updates or document generation guidance
    await expect(page.locator('main').getByText('🦅 EAGLE')).toHaveCount(2, { timeout: 60000 });
    await expect(page.locator('main')).toContainText(
      /package|document|letter|determination|D&F|justification|memorandum|generate|update/i
    );
  });
});
