import pytest
from fastapi.testclient import TestClient

from tests import catalog as product_catalog
from tests.helpers import CartApi


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A fresh SQLite file per test, seeded from docs/requirements.md."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    from app.db import init_db
    from app.main import app
    from app.seed import seed

    init_db()
    seed()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def cart(client) -> CartApi:
    r = client.post("/api/carts")
    assert r.status_code == 201
    return CartApi(client, r.json()["cart_id"])


@pytest.fixture
def catalog():
    return product_catalog
