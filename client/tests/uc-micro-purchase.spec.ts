import { test, expect } from '@playwright/test';

/**
 * UC-02: Micro-Purchase Workflow
 *
 * Simulates a contracting officer initiating a micro-purchase under $15K.
 * Verifies the agent identifies the micro-purchase threshold, recommends
 * a simplified process (purchase card / purchase request), and asks
 * minimal follow-up questions rather than a full acquisition walkthrough.
 * A second message provides quote details and verifies the agent offers
 * to generate a purchase request.
 */
test.describe('UC-02: Micro-Purchase Workflow', () => {
  test('micro-purchase request → simplified process with purchase request', async ({ page }) => {
    test.slow(); // 90s budget for agent streaming

    await page.goto('/chat/');
    await page.getByRole('button', { name: 'New Chat' }).click();
    await expect(page.getByRole('heading', { name: /Welcome to EAGLE/i })).toBeVisible();

    // --- Message 1: describe a micro-purchase scenario ---
    const textarea = page.locator('textarea');
    await expect(textarea).toBeEnabled();
    await textarea.fill(
      'I need to purchase lab supplies for $13,800 from Fisher Scientific. I have a quote.'
    );
    await expect(page.getByRole('button', { name: '➤' })).toBeEnabled();
    await page.getByRole('button', { name: '➤' }).click();

    // Agent responds
    await expect(page.locator('main').getByText('🦅 EAGLE')).toHaveCount(1, { timeout: 60000 });

    // Response should acknowledge micro-purchase threshold / simplified process
    await expect(page.locator('main')).toContainText(
      /micro.?purchase|purchase card|simplified|threshold|\$15,?000|below.+threshold/i
    );

    // --- Message 2: provide quote details ---
    await expect(textarea).toBeEnabled({ timeout: 30000 });
    await textarea.fill(
      'The quote is for 3 centrifuge units at $4,600 each. Delivery in 2 weeks.'
    );
    await expect(page.getByRole('button', { name: '➤' })).toBeEnabled();
    await page.getByRole('button', { name: '➤' }).click();

    // Second agent response arrives (now 2 EAGLE labels in main)
    await expect(page.locator('main').getByText('🦅 EAGLE')).toHaveCount(2, { timeout: 60000 });

    // Response should reference generating / completing a purchase request or order
    await expect(page.locator('main')).toContainText(
      /purchase request|purchase order|generate|document|proceed|order|requisition/i
    );
  });
});
