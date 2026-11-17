import os
import sqlite3
import subprocess
import sys
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import get_connection, init_db
from app.main import app


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(path))
    return path


@pytest.fixture
def connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    init_db()
    with closing(get_connection()) as connection:
        yield connection


def test_default_connection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DB_PATH", raising=False)
    monkeypatch.chdir(tmp_path)
    with closing(get_connection()) as connection:
        assert (tmp_path / "cart.db").is_file()
        assert connection.row_factory is sqlite3.Row
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_init_db_is_repeatable(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT INTO carts (id, created_at) VALUES (?, ?)", ("cart-1", "2026-11-17")
    )
    connection.commit()
    init_db()
    assert connection.execute("SELECT id FROM carts").fetchone()["id"] == "cart-1"
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = ?", ("table",)
    ).fetchall()
    assert {row["name"] for row in tables} == {"products", "carts", "cart_items"}


@pytest.mark.parametrize(
    ("sku", "name", "price_satang", "stock"),
    [
        ("SKU", "Product", -1, 1),
        ("SKU", "Product", 100, -1),
        (None, "Product", 100, 1),
        ("SKU", None, 100, 1),
        ("SKU", "Product", None, 1),
        ("SKU", "Product", 100, None),
    ],
)
def test_product_constraints(
    connection: sqlite3.Connection,
    sku: str | None,
    name: str | None,
    price_satang: int | None,
    stock: int | None,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO products (sku, name, price_satang, stock) VALUES (?, ?, ?, ?)",
            (sku, name, price_satang, stock),
        )


def test_cart_item_constraints_and_cascade(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT INTO products (id, sku, name, price_satang, stock) VALUES (?, ?, ?, ?, ?)",
        (1, "SKU", "Product", 100, 20),
    )
    connection.execute(
        "INSERT INTO carts (id, created_at) VALUES (?, ?)", ("cart-1", "2026-11-17")
    )
    for cart_id, product_id, qty in [
        ("missing", 1, 1),
        ("cart-1", 999, 1),
        ("cart-1", 1, 0),
        ("cart-1", 1, 11),
    ]:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO cart_items (cart_id, product_id, qty) VALUES (?, ?, ?)",
                (cart_id, product_id, qty),
            )
    connection.execute(
        "INSERT INTO cart_items (cart_id, product_id, qty) VALUES (?, ?, ?)",
        ("cart-1", 1, 10),
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO cart_items (cart_id, product_id, qty) VALUES (?, ?, ?)",
            ("cart-1", 1, 1),
        )
    connection.execute("DELETE FROM carts WHERE id = ?", ("cart-1",))
    assert connection.execute("SELECT COUNT(*) FROM cart_items").fetchone()[0] == 0


def test_seed_module_is_repeatable(db_path: Path) -> None:
    for _ in range(2):
        subprocess.run(
            [sys.executable, "-m", "app.seed"],
            cwd=Path(__file__).resolve().parents[1],
            env=os.environ.copy(),
            check=True,
        )
    with closing(get_connection()) as connection:
        rows = connection.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert [tuple(row) for row in rows] == [
        (1, "TSHIRT-01", "เสื้อยืดนักพัฒนา", 29900, 20),
        (2, "MUG-01", "แก้วกาแฟ", 15900, 15),
        (3, "EARBUD-01", "หูฟังไร้สาย", 129000, 5),
        (4, "CABLE-01", "สายชาร์จ USB-C", 19900, 2),
        (5, "STICKER-01", "สติกเกอร์", 100, 100),
        (6, "TOTE-01", "กระเป๋าผ้า", 49900, 10),
        (7, "KEYBOARD-01", "คีย์บอร์ด", 249000, 0),
        (8, "MOUSE-01", "เมาส์", 59000, 8),
    ]


def test_startup_initializes_database(db_path: Path) -> None:
    assert not db_path.exists()
    with TestClient(app) as client:
        assert db_path.is_file()
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert "<h1>Shop Cart</h1>" in client.get("/").text
        with closing(get_connection()) as connection:
            assert connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0
