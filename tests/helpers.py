import httpx
from fastapi.testclient import TestClient


class CartApi:
    """Calls the cart API for one cart, so tests read like the spec."""

    def __init__(self, client: TestClient, cart_id: str) -> None:
        self.client = client
        self.cart_id = cart_id
        self.base = f"/api/carts/{cart_id}"

    def get(self) -> httpx.Response:
        return self.client.get(self.base)

    def add(self, product_id: int, qty: int = 1) -> httpx.Response:
        return self.client.post(f"{self.base}/items", json={"product_id": product_id, "qty": qty})

    def set_qty(self, product_id: int, qty: int) -> httpx.Response:
        return self.client.patch(f"{self.base}/items/{product_id}", json={"qty": qty})

    def remove(self, product_id: int) -> httpx.Response:
        return self.client.delete(f"{self.base}/items/{product_id}")

    def apply_code(self, code: str) -> httpx.Response:
        return self.client.put(f"{self.base}/discount", json={"code": code})
