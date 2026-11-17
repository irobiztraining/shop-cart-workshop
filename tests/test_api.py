import importlib
import os
import subprocess
import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app import api, main
from app.seed import SEED_PRODUCTS


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    with monkeypatch.context() as environment:
        environment.setenv("DB_PATH", str(tmp_path / "api.db"))
        environment.setenv("APP_ENV", "test")
        importlib.reload(api)
        importlib.reload(main)
        with TestClient(main.app) as client:
            assert client.post("/api/test/reset").status_code == 200
            yield client
    importlib.reload(api)
    importlib.reload(main)


@pytest.fixture
def cart_id(client: TestClient) -> str:
    response = client.post("/api/carts")
    assert response.status_code == 201
    cart = response.json()
    assert str(UUID(cart["cart_id"])) == cart["cart_id"]
    assert cart == {
        "cart_id": cart["cart_id"],
        "items": [],
        "discount_code": None,
        "subtotal_satang": 0,
        "discount_satang": 0,
        "shipping_satang": 0,
        "total_satang": 0,
    }
    return cart["cart_id"]


def test_cart_endpoints_share_response_model(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    for path, methods in paths.items():
        if path.startswith("/api/carts"):
            for operation in methods.values():
                status = "201" if path == "/api/carts" else "200"
                schema = operation["responses"][status]["content"]["application/json"]["schema"]
                assert schema == {"$ref": "#/components/schemas/CartOut"}


def test_products_match_seed(client: TestClient) -> None:
    response = client.get("/api/products")
    assert response.status_code == 200
    assert response.json() == [
        dict(zip(("id", "sku", "name", "price_satang", "stock"), product))
        for product in SEED_PRODUCTS
    ]


def test_cart_item_lifecycle_and_persistence(client: TestClient, cart_id: str) -> None:
    url = f"/api/carts/{cart_id}"
    response = client.post(f"{url}/items", json={"product_id": 6})
    assert response.status_code == 200
    cart = response.json()
    assert cart["subtotal_satang"] == 49_900
    assert cart["discount_satang"] == 0
    assert cart["shipping_satang"] == 5_000
    assert cart["total_satang"] == 54_900
    assert cart["items"][0]["qty"] == 1
    assert cart["items"][0]["unit_price_satang"] == 49_900
    assert cart["items"][0]["line_total_satang"] == 49_900
    assert client.get(url).json() == cart

    response = client.post(f"{url}/items", json={"product_id": 6, "qty": 2})
    assert response.status_code == 200
    assert response.json()["items"][0]["qty"] == 3
    assert response.json()["items"][0]["line_total_satang"] == 149_700
    assert response.json()["total_satang"] == 149_700
    response = client.patch(f"{url}/items/6", json={"qty": 2})
    assert response.status_code == 200
    assert response.json()["items"][0]["qty"] == 2
    assert response.json()["items"][0]["line_total_satang"] == 99_800
    assert response.json()["subtotal_satang"] == 99_800
    assert response.json()["shipping_satang"] == 5_000
    assert client.get("/api/products").json()[5]["stock"] == 10
    response = client.delete(f"{url}/items/6")
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total_satang"] == 0


def test_discount_lifecycle(client: TestClient, cart_id: str) -> None:
    url = f"/api/carts/{cart_id}"
    client.post(f"{url}/items", json={"product_id": 6})
    before = client.get(url).json()
    response = client.put(f"{url}/discount", json={"code": "SAVE10"})
    assert response.status_code == 409
    assert response.json() == {"detail": "ยอดซื้อขั้นต่ำ ฿500.00", "code": "MIN_SUBTOTAL"}
    assert client.get(url).json() == before

    client.post(f"{url}/items", json={"product_id": 5})
    response = client.put(f"{url}/discount", json={"code": "SAVE10"})
    assert response.status_code == 200
    cart = response.json()
    assert cart["discount_code"] == "SAVE10"
    assert cart["subtotal_satang"] == 50_000
    assert cart["discount_satang"] == 5_000
    assert cart["shipping_satang"] == 5_000
    assert cart["total_satang"] == 50_000

    cart = client.delete(f"{url}/items/5").json()
    assert cart["discount_code"] == "SAVE10"
    assert cart["discount_satang"] == 0
    cart = client.post(f"{url}/items", json={"product_id": 5}).json()
    assert cart["discount_satang"] == 5_000
    before = client.get(url).json()
    response = client.put(f"{url}/discount", json={"code": "' OR 1=1 --"})
    assert response.status_code == 422
    assert response.json() == {"detail": "รหัสส่วนลดไม่ถูกต้อง", "code": "INVALID_CODE"}
    assert client.get(url).json() == before

    response = client.delete(f"{url}/discount")
    assert response.status_code == 200
    assert response.json()["discount_code"] is None
    assert response.json()["discount_satang"] == 0
    assert response.json()["total_satang"] == 55_000


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [
        ("get", "", None),
        ("post", "/items", {"product_id": 1}),
        ("patch", "/items/1", {"qty": 1}),
        ("delete", "/items/1", None),
        ("put", "/discount", {"code": "SAVE10"}),
        ("delete", "/discount", None),
    ],
)
def test_missing_cart(
    client: TestClient, method: str, suffix: str, body: dict[str, object] | None
) -> None:
    response = client.request(method, f"/api/carts/missing{suffix}", json=body)
    assert response.status_code == 404
    assert response.json() == {"detail": "ไม่พบตะกร้าสินค้า", "code": "CART_NOT_FOUND"}


@pytest.mark.parametrize(
    ("method", "suffix", "body", "code"),
    [
        ("post", "/items", {"product_id": 999}, "PRODUCT_NOT_FOUND"),
        ("patch", "/items/999", {"qty": 1}, "PRODUCT_NOT_FOUND"),
        ("delete", "/items/999", None, "PRODUCT_NOT_FOUND"),
        ("patch", "/items/1", {"qty": 1}, "CART_ITEM_NOT_FOUND"),
        ("delete", "/items/1", None, "CART_ITEM_NOT_FOUND"),
    ],
)
def test_missing_product_or_cart_item(
    client: TestClient,
    cart_id: str,
    method: str,
    suffix: str,
    body: dict[str, object] | None,
    code: str,
) -> None:
    response = client.request(method, f"/api/carts/{cart_id}{suffix}", json=body)
    assert response.status_code == 404
    assert response.json() == {
        "detail": "ไม่พบสินค้า" if code == "PRODUCT_NOT_FOUND" else "ไม่พบสินค้าในตะกร้า",
        "code": code,
    }


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [
        ("post", "/items", {}),
        ("post", "/items", {"product_id": 1, "qty": 0}),
        ("post", "/items", {"product_id": 1, "qty": -1}),
        ("post", "/items", {"product_id": 1, "qty": "2"}),
        ("post", "/items", {"product_id": 1, "qty": True}),
        ("post", "/items", {"product_id": 1, "qty": 2.5}),
        ("patch", "/items/1", {"qty": 0}),
        ("patch", "/items/not-an-int", {"qty": 1}),
        ("put", "/discount", {"code": 10}),
    ],
)
def test_invalid_input(
    client: TestClient,
    cart_id: str,
    method: str,
    suffix: str,
    body: dict[str, object],
) -> None:
    before = client.get(f"/api/carts/{cart_id}").json()
    response = client.request(method, f"/api/carts/{cart_id}{suffix}", json=body)
    assert response.status_code == 422
    assert response.json() == {"detail": "ข้อมูลที่ส่งมาไม่ถูกต้อง", "code": "INVALID_INPUT"}
    assert client.get(f"/api/carts/{cart_id}").json() == before


def test_quantity_errors_leave_cart_unchanged(client: TestClient, cart_id: str) -> None:
    url = f"/api/carts/{cart_id}"
    client.post(f"{url}/items", json={"product_id": 4, "qty": 2})
    before = client.get(url).json()
    for method, suffix, body, code in [
        ("post", "/items", {"product_id": 4}, "OUT_OF_STOCK"),
        ("patch", "/items/4", {"qty": 3}, "OUT_OF_STOCK"),
        ("post", "/items", {"product_id": 4, "qty": 9}, "QTY_LIMIT"),
        ("patch", "/items/4", {"qty": 11}, "QTY_LIMIT"),
        ("post", "/items", {"product_id": 7}, "OUT_OF_STOCK"),
    ]:
        response = client.request(method, f"{url}{suffix}", json=body)
        assert response.status_code == 409
        assert response.json() == {
            "detail": "สินค้าไม่พอ" if code == "OUT_OF_STOCK"
            else "จำนวนสินค้าต่อรายการต้องไม่เกิน 10 ชิ้น",
            "code": code,
        }
        assert client.get(url).json() == before


def test_concurrent_additions_respect_quantity_limit(
    client: TestClient, cart_id: str
) -> None:
    def add_sticker(_: int) -> int:
        return client.post(
            f"/api/carts/{cart_id}/items", json={"product_id": 5}
        ).status_code

    with ThreadPoolExecutor(max_workers=6) as executor:
        statuses = list(executor.map(add_sticker, range(12)))
    assert statuses.count(200) == 10
    assert statuses.count(409) == 2
    cart = client.get(f"/api/carts/{cart_id}").json()
    assert cart["items"][0]["qty"] == 10
    assert cart["subtotal_satang"] == 1_000


def test_reset_recreates_and_seeds_database(client: TestClient, cart_id: str) -> None:
    client.post(f"/api/carts/{cart_id}/items", json={"product_id": 1})
    for _ in range(2):
        response = client.post("/api/test/reset")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert len(client.get("/api/products").json()) == 8
    assert client.get(f"/api/carts/{cart_id}").status_code == 404


@pytest.mark.parametrize("environment", [None, "production", "test"])
def test_reset_registration(environment: str | None) -> None:
    env = os.environ.copy()
    env.pop("APP_ENV", None)
    if environment is not None:
        env["APP_ENV"] = environment
    script = (
        "from app.main import app; "
        "assert ('/api/test/reset' in app.openapi()['paths']) "
        f"is {environment == 'test'!r}"
    )
    subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        check=True,
    )
