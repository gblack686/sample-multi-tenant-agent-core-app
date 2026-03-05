import { test, expect } from '@playwright/test';

/**
 * UC-04: Contract Modification Request
 *
 * Simulates a contracting officer requesting a contract modification
 * to add funding and extend the period of performance. Verifies the
 * agent identifies the modification type, references relevant FAR
 * clauses, and produces documentation guidance after follow-up.
 */
test.describe('UC-04: Contract Modification Request', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/chat/');
    await page.getByRole('button', { name: 'New Chat' }).click();
    await expect(page.getByRole('heading', { name: /Welcome to EAGLE/i })).toBeVisible();
  });

  test('modification request → type identification and documentation guidance', async ({ page }) => {
    test.slow(); // 90s budget for agent streaming

    // Send modification request message
    const textarea = page.getByPlaceholder(/Ask EAGLE/i);
    await textarea.fill(
      'I need to modify contract NCI-2023-0542 to add $150,000 in funding and extend the period of performance by 6 months.'
    );
    await expect(page.getByRole('button', { name: '➤' })).toBeEnabled();
    await page.getByRole('button', { name: '➤' }).click();

    // Agent responds acknowledging the contract modification
    await expect(page.locator('main').getByText('🦅 EAGLE')).toHaveCount(1, { timeout: 60000 });
    await expect(page.locator('main')).toContainText(
      /modif|contract|NCI-2023-0542|funding|period of performance/i
    );

    // Response should mention modification type or FAR references
    await expect(page.locator('main')).toContainText(
      /bilateral|unilateral|FAR|modification type|SF-30|supplemental agreement/i
    );

    // Response should ask about justification or discuss required documentation
    await expect(page.locator('main')).toContainText(
      /justification|documentation|rationale|scope|requirement|approval/i
    );

    // Send follow-up with justification details
    await textarea.fill(
      'This is additional funding for expanded data analysis scope. The contractor has agreed to the changes.'
    );
    await expect(page.getByRole('button', { name: '➤' })).toBeEnabled();
    await page.getByRole('button', { name: '➤' }).click();

    // Agent responds with bilateral modification guidance or document generation
    await expect(page.locator('main').getByText('🦅 EAGLE')).toHaveCount(2, { timeout: 60000 });
    await expect(page.locator('main')).toContainText(
      /bilateral|modification|SF-30|document|generate|supplemental|mutual|agreement/i
    );
  });
});
