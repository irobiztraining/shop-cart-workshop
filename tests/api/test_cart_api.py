from tests import catalog
from tests.helpers import CartApi


def test_ac01_add_tote_calculates_shipping_and_total(cart: CartApi) -> None:
    response = cart.add(catalog.TOTE)

    assert response.status_code == 200
    result = response.json()
    assert result["subtotal_satang"] == catalog.PRICE[catalog.TOTE]
    assert result["shipping_satang"] == 5_000
    assert result["total_satang"] == 54_900
    assert result["items"][0]["product_id"] == catalog.TOTE
    assert result["items"][0]["qty"] == 1


def test_ac02_reject_save10_below_minimum_without_changing_total(
    cart: CartApi,
) -> None:
    added = cart.add(catalog.TOTE)
    assert added.status_code == 200
    before = added.json()

    response = cart.apply_code("SAVE10")
    after = cart.get()

    assert response.status_code == 409
    assert response.json()["code"] == "MIN_SUBTOTAL"
    assert response.json()["detail"] == "ยอดซื้อขั้นต่ำ ฿500.00"
    assert after.status_code == 200
    assert after.json()["total_satang"] == before["total_satang"]


def test_ac03_apply_save10_at_minimum_subtotal(cart: CartApi) -> None:
    tote = cart.add(catalog.TOTE)
    assert tote.status_code == 200
    sticker = cart.add(catalog.STICKER)
    assert sticker.status_code == 200

    response = cart.apply_code("SAVE10")

    assert response.status_code == 200
    result = response.json()
    assert result["subtotal_satang"] == 50_000
    assert result["discount_satang"] == 5_000
    assert result["shipping_satang"] == 5_000
    assert result["total_satang"] == 50_000
    assert result["discount_code"] == "SAVE10"
    assert result["items"][0]["qty"] == 1


def test_ac04_increase_cable_over_stock_keeps_quantity(cart: CartApi) -> None:
    added = cart.add(catalog.CABLE, qty=2)
    assert added.status_code == 200
    assert added.json()["items"][0]["qty"] == 2

    response = cart.set_qty(catalog.CABLE, 3)
    unchanged = cart.get()

    assert response.status_code == 409
    assert response.json()["code"] == "OUT_OF_STOCK"
    assert unchanged.status_code == 200
    assert unchanged.json()["items"][0]["qty"] == 2


def test_ac05_adding_keyboard_with_no_stock_returns_out_of_stock(
    cart: CartApi,
) -> None:
    response = cart.add(catalog.KEYBOARD)
    unchanged = cart.get()

    assert response.status_code == 409
    assert response.json()["code"] == "OUT_OF_STOCK"
    assert unchanged.status_code == 200
    assert unchanged.json()["items"] == []
    assert unchanged.json()["total_satang"] == 0


def test_ac06_cart_items_are_unchanged_on_repeated_get(cart: CartApi) -> None:
    tote = cart.add(catalog.TOTE)
    assert tote.status_code == 200
    sticker = cart.add(catalog.STICKER)
    assert sticker.status_code == 200

    first_read = cart.get()
    second_read = cart.get()

    assert first_read.status_code == 200
    assert second_read.status_code == 200
    assert second_read.json()["items"] == first_read.json()["items"]


def test_br02_adding_same_product_increases_quantity(cart: CartApi) -> None:
    first_add = cart.add(catalog.TOTE)
    assert first_add.status_code == 200

    second_add = cart.add(catalog.TOTE, qty=2)

    assert second_add.status_code == 200
    result = second_add.json()
    assert result["items"][0]["qty"] == 3
    assert result["items"][0]["line_total_satang"] == 149_700
    assert result["subtotal_satang"] == 149_700


def test_br03_quantity_11_returns_qty_limit_without_changing_cart(
    cart: CartApi,
) -> None:
    before = cart.get()
    assert before.status_code == 200

    response = cart.add(catalog.STICKER, qty=11)
    after = cart.get()

    assert response.status_code == 409
    assert response.json()["code"] == "QTY_LIMIT"
    assert after.status_code == 200
    assert after.json() == before.json()


def test_br05_invalid_discount_code_does_not_change_cart(cart: CartApi) -> None:
    added = cart.add(catalog.TOTE)
    assert added.status_code == 200
    before = added.json()

    response = cart.apply_code("INVALID")
    after = cart.get()

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_CODE"
    assert after.status_code == 200
    assert after.json()["discount_code"] is None
    assert after.json()["total_satang"] == before["total_satang"]


def test_br05_discount_remains_but_is_zero_below_minimum(cart: CartApi) -> None:
    tote = cart.add(catalog.TOTE)
    assert tote.status_code == 200
    sticker = cart.add(catalog.STICKER)
    assert sticker.status_code == 200
    discounted = cart.apply_code("SAVE10")
    assert discounted.status_code == 200
    assert discounted.json()["discount_satang"] == 5_000

    response = cart.remove(catalog.STICKER)

    assert response.status_code == 200
    result = response.json()
    assert result["discount_code"] == "SAVE10"
    assert result["subtotal_satang"] == catalog.PRICE[catalog.TOTE]
    assert result["discount_satang"] == 0
    assert result["total_satang"] == 54_900


def test_missing_cart_returns_not_found(cart: CartApi) -> None:
    missing_cart = CartApi(cart.client, "missing")

    response = missing_cart.get()
    unchanged = cart.get()

    assert response.status_code == 404
    assert response.json()["code"] == "CART_NOT_FOUND"
    assert unchanged.status_code == 200
    assert unchanged.json()["items"] == []
