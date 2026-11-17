import { expect, test } from '@playwright/test';
import { CartPage, PRODUCT } from '../pages/cart-page';

test.beforeEach(async ({ page, request }) => {
  await request.post('/api/test/reset');
  await new CartPage(page).goto();
});

test('should add a tote bag and calculate shipping and total', { tag: '@AC-01' }, async ({ page }) => {
  const cartPage = new CartPage(page);

  await cartPage.add(PRODUCT.TOTE);

  await expect(cartPage.subtotal).toHaveText('฿499.00');
  await expect(cartPage.shipping).toHaveText('฿50.00');
  await expect(cartPage.total).toHaveText('฿549.00');
});

test('should prevent increasing cable quantity beyond stock', { tag: '@AC-04' }, async ({ page }) => {
  const cartPage = new CartPage(page);

  await cartPage.add(PRODUCT.CABLE);
  await cartPage.add(PRODUCT.CABLE);
  await cartPage.increaseButton(PRODUCT.CABLE).click();

  await expect(cartPage.error).toHaveText('สินค้าไม่พอ');
  await expect(cartPage.qty(PRODUCT.CABLE)).toHaveText('2');
});

test('should disable the add button for an out-of-stock keyboard', { tag: '@AC-05' }, async ({ page }) => {
  const cartPage = new CartPage(page);

  await expect(cartPage.addButton(PRODUCT.KEYBOARD)).toBeDisabled();
});

test('should keep cart contents after reloading the page', { tag: '@AC-06' }, async ({ page }) => {
  const cartPage = new CartPage(page);

  await cartPage.add(PRODUCT.TOTE);
  const contents = (await cartPage.line(PRODUCT.TOTE).innerText()).replace(/\s+/g, '');

  await page.reload();

  await expect(cartPage.line(PRODUCT.TOTE)).toHaveText(contents);
});
