import os
import sqlite3
from contextlib import closing


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(os.environ.get("DB_PATH", "cart.db"))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with closing(get_connection()) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                price_satang INTEGER NOT NULL CHECK(price_satang >= 0),
                stock INTEGER NOT NULL CHECK(stock >= 0)
            );
            CREATE TABLE IF NOT EXISTS carts (
                id TEXT PRIMARY KEY,
                discount_code TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cart_items (
                cart_id TEXT NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id),
                qty INTEGER NOT NULL CHECK(qty BETWEEN 1 AND 10),
                PRIMARY KEY(cart_id, product_id)
            );
            """
        )
