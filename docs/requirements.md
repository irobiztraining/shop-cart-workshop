# Shopping Cart: Requirements

## Business rules
- BR-01 Product list shows name, price (THB) and stock. A product with
  stock 0 shows "สินค้าหมด" and its add button is disabled.
- BR-02 The `qty` in POST /api/carts/{cart_id}/items is the quantity to add
  (default 1). Adding a product already in the cart increases its qty by the
  submitted qty.
- BR-03 Qty per line is 1–10 and never more than stock.
  Validate the resulting line qty: over 10 -> 409 QTY_LIMIT; otherwise,
  over stock -> 409 OUT_OF_STOCK.
- BR-04 Subtotal = sum of unit price x qty.
- BR-05 Discount code SAVE10 = 10% of subtotal, rounded half up to satang.
  Needs subtotal >= 500.00 THB. Applying it below that -> 409 MIN_SUBTOTAL.
  Unknown code -> 422 INVALID_CODE. If subtotal later drops below
  500.00 THB, the code stays on the cart but the discount becomes 0. If the
  subtotal later reaches 500.00 THB again, the discount is recalculated
  automatically without reapplying the code.
- BR-06 Shipping is 50.00 THB when (subtotal - discount) < 1,000.00 THB,
  free when >= 1,000.00 THB, and 0 for an empty cart.
- BR-07 Total = subtotal - discount + shipping. Prices already include VAT.
- BR-08 The cart is saved in SQLite. The browser keeps cart_id in
  localStorage, so a page reload keeps the cart.
- BR-09 Adding to the cart does not reduce stock (stock is cut at checkout,
  which is out of scope).

## Acceptance criteria
- AC-01 Given an empty cart, when I add "กระเป๋าผ้า" (฿499.00),
  then subtotal is ฿499.00, shipping ฿50.00, total ฿549.00.
- AC-02 Given subtotal ฿499.00, when I apply SAVE10, then I see
  "ยอดซื้อขั้นต่ำ ฿500.00" and the total does not change.
- AC-03 Given subtotal ฿500.00, when I apply SAVE10, then discount is ฿50.00.
- AC-04 Given "สายชาร์จ USB-C" (stock 2) with qty 2, when I press +,
  then I see "สินค้าไม่พอ" and qty stays 2.
- AC-05 Given "คีย์บอร์ด" (stock 0), then its add button is disabled.
- AC-06 Given items in the cart, when I reload the page, the cart is the same.

## Seed products (price in THB)
| id | sku | name | price | stock |
|----|-----|------|-------|-------|
| 1 | TSHIRT-01 | เสื้อยืดนักพัฒนา | 299.00 | 20 |
| 2 | MUG-01 | แก้วกาแฟ | 159.00 | 15 |
| 3 | EARBUD-01 | หูฟังไร้สาย | 1,290.00 | 5 |
| 4 | CABLE-01 | สายชาร์จ USB-C | 199.00 | 2 |
| 5 | STICKER-01 | สติกเกอร์ | 1.00 | 100 |
| 6 | TOTE-01 | กระเป๋าผ้า | 499.00 | 10 |
| 7 | KEYBOARD-01 | คีย์บอร์ด | 2,490.00 | 0 |
| 8 | MOUSE-01 | เมาส์ | 590.00 | 8 |

## API contract
- GET    /health -> {"status": "ok"}
- GET    /api/products -> ProductOut[]
- POST   /api/carts -> 201 CartOut (includes cart_id as a UUID string)
- GET    /api/carts/{cart_id} -> items[] + subtotal_satang,
         discount_satang, shipping_satang, total_satang, discount_code
- POST   /api/carts/{cart_id}/items  body {"product_id": int, "qty": int = 1}
- PATCH  /api/carts/{cart_id}/items/{product_id}  body {"qty": int}
- DELETE /api/carts/{cart_id}/items/{product_id}
- PUT    /api/carts/{cart_id}/discount  body {"code": str}
- DELETE /api/carts/{cart_id}/discount
- POST   /api/test/reset  (only when APP_ENV=test) re-create DB + seed
- Every cart endpoint returns the full cart, so the UI renders from
  one response.
- CartOut: cart_id, items[], discount_code, subtotal_satang, discount_satang,
  shipping_satang, total_satang.
- ProductOut: id, sku, name, price_satang, stock.
- Each cart item: product_id, sku, name, unit_price_satang, line_total_satang,
  stock, qty. The API calculates line_total_satang using pricing; the browser
  only formats monetary values and never calculates cart or line totals.
- POST item qty is the quantity to add; PATCH qty replaces the line quantity.
  Both require a positive integer. Values over 10 are handled by BR-03.
- Errors use a top-level body {"detail": "<Thai message>", "code": "<CODE>"}:
  - 404 CART_NOT_FOUND, PRODUCT_NOT_FOUND.
  - 404 CART_ITEM_NOT_FOUND for PATCH/DELETE when the product exists but
    is not in the cart.
  - 409 QTY_LIMIT, OUT_OF_STOCK, MIN_SUBTOTAL.
  - 422 INVALID_CODE for unknown discount codes.
  - 422 INVALID_INPUT for malformed requests or invalid field values.
- POST /api/test/reset returns {"status": "ok"} and is registered only when
  APP_ENV=test at application import time.
