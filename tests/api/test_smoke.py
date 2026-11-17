from tests.helpers import CartApi


def test_add_tote_calculates_shipping_and_total(
    cart: CartApi, catalog
) -> None:
    response = cart.add(catalog.TOTE)

    assert response.status_code == 200
    cart = response.json()
    assert cart["subtotal_satang"] == 49_900
    assert cart["shipping_satang"] == 5_000
    assert cart["total_satang"] == 54_900


def test_apply_discount_below_minimum_returns_error_without_changing_total(
    cart: CartApi, catalog
) -> None:
    before = cart.add(catalog.TOTE).json()

    response = cart.apply_code("SAVE10")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "ยอดซื้อขั้นต่ำ ฿500.00",
        "code": "MIN_SUBTOTAL",
    }
    after = cart.get().json()
    assert after["total_satang"] == before["total_satang"]


def test_increase_cable_over_stock_returns_error_and_keeps_quantity(
    cart: CartApi, catalog
) -> None:
    added_cart = cart.add(catalog.CABLE, qty=2).json()
    assert added_cart["items"][0]["qty"] == 2

    response = cart.set_qty(catalog.CABLE, 3)

    assert response.status_code == 409
    assert response.json() == {"detail": "สินค้าไม่พอ", "code": "OUT_OF_STOCK"}
    assert cart.get().json()["items"][0]["qty"] == 2
