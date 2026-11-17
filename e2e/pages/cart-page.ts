import { expect, type Locator, type Page } from '@playwright/test';

export const PRODUCT = { TSHIRT: 1, CABLE: 4, STICKER: 5, TOTE: 6, KEYBOARD: 7 } as const;

export class CartPage {
  constructor(readonly page: Page) {}

  async goto() {
    await this.page.goto('/');
    await expect(this.addButton(PRODUCT.TSHIRT)).toBeVisible();
  }

  addButton(id: number): Locator { return this.page.getByTestId(`add-to-cart-${id}`); }
  increaseButton(id: number): Locator { return this.page.getByTestId(`increase-${id}`); }
  qty(id: number): Locator { return this.page.getByTestId(`qty-${id}`); }
  line(id: number): Locator { return this.page.getByTestId(`cart-line-${id}`); }
  get subtotal(): Locator { return this.page.getByTestId('cart-subtotal'); }
  get discount(): Locator { return this.page.getByTestId('cart-discount'); }
  get shipping(): Locator { return this.page.getByTestId('cart-shipping'); }
  get total(): Locator { return this.page.getByTestId('cart-total'); }
  get error(): Locator { return this.page.getByTestId('error-message'); }

  async add(id: number) {
    await this.addButton(id).click();
    await expect(this.line(id)).toBeVisible();
  }

  async applyCode(code: string) {
    await this.page.getByTestId('discount-input').fill(code);
    await this.page.getByTestId('apply-discount').click();
  }
}
