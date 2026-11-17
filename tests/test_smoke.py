from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app
from app.seed import seed


@pytest.fixture
def client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    init_db()
    seed()
    with TestClient(app) as test_client:
        yield test_client


def test_add_tote_calculates_shipping_and_total(client: TestClient) -> None:
    cart_response = client.post("/api/carts")
    assert cart_response.status_code == 201
    cart_id = cart_response.json()["cart_id"]

    response = client.post(
        f"/api/carts/{cart_id}/items", json={"product_id": 6}
    )

    assert response.status_code == 200
    cart = response.json()
    assert cart["subtotal_satang"] == 49_900
    assert cart["shipping_satang"] == 5_000
    assert cart["total_satang"] == 54_900


def test_apply_discount_below_minimum_returns_error_without_changing_total(
    client: TestClient,
) -> None:
    cart_id = client.post("/api/carts").json()["cart_id"]
    cart_url = f"/api/carts/{cart_id}"
    before = client.post(
        f"{cart_url}/items", json={"product_id": 6}
    ).json()

    response = client.put(f"{cart_url}/discount", json={"code": "SAVE10"})

    assert response.status_code == 409
    assert response.json() == {
        "detail": "ยอดซื้อขั้นต่ำ ฿500.00",
        "code": "MIN_SUBTOTAL",
    }
    after = client.get(cart_url).json()
    assert after["total_satang"] == before["total_satang"]


def test_increase_cable_over_stock_returns_error_and_keeps_quantity(
    client: TestClient,
) -> None:
    cart_id = client.post("/api/carts").json()["cart_id"]
    cart_url = f"/api/carts/{cart_id}"
    added_cart = client.post(
        f"{cart_url}/items", json={"product_id": 4, "qty": 2}
    ).json()
    assert added_cart["items"][0]["qty"] == 2

    response = client.patch(f"{cart_url}/items/4", json={"qty": 3})

    assert response.status_code == 409
    assert response.json() == {"detail": "สินค้าไม่พอ", "code": "OUT_OF_STOCK"}
    assert client.get(cart_url).json()["items"][0]["qty"] == 2
