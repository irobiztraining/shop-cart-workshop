import sqlite3
from collections.abc import Sequence


class CartError(Exception):
    def __init__(self, status_code: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail


def enable_foreign_keys(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")


def init_schema(connection: sqlite3.Connection) -> None:
    for statement in (
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            price_satang INTEGER NOT NULL CHECK(price_satang >= 0),
            stock INTEGER NOT NULL CHECK(stock >= 0)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS carts (
            id TEXT PRIMARY KEY,
            discount_code TEXT,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS cart_items (
            cart_id TEXT NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            qty INTEGER NOT NULL CHECK(qty BETWEEN 1 AND 10),
            PRIMARY KEY(cart_id, product_id)
        )
        """,
    ):
        connection.execute(statement)


def insert_products(
    connection: sqlite3.Connection,
    products: Sequence[tuple[int, str, str, int, int]],
) -> None:
    connection.executemany(
        """
        INSERT INTO products (id, sku, name, price_satang, stock)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO NOTHING
        """,
        products,
    )


def begin_transaction(connection: sqlite3.Connection) -> None:
    connection.execute("BEGIN IMMEDIATE")


def reset_db(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS cart_items")
    connection.execute("DROP TABLE IF EXISTS carts")
    connection.execute("DROP TABLE IF EXISTS products")
    init_schema(connection)


def list_products(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT id, sku, name, price_satang, stock FROM products ORDER BY id"
    ).fetchall()


def get_product(connection: sqlite3.Connection, product_id: int) -> sqlite3.Row:
    row = connection.execute(
        "SELECT id, sku, name, price_satang, stock FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()
    if row is None:
        raise CartError(404, "PRODUCT_NOT_FOUND", "ไม่พบสินค้า")
    return row


def create_cart(connection: sqlite3.Connection, cart_id: str, created_at: str) -> None:
    connection.execute(
        "INSERT INTO carts (id, created_at) VALUES (?, ?)", (cart_id, created_at)
    )


def get_cart(connection: sqlite3.Connection, cart_id: str) -> sqlite3.Row:
    row = connection.execute(
        "SELECT id, discount_code, created_at FROM carts WHERE id = ?", (cart_id,)
    ).fetchone()
    if row is None:
        raise CartError(404, "CART_NOT_FOUND", "ไม่พบตะกร้าสินค้า")
    return row


def list_cart_items(connection: sqlite3.Connection, cart_id: str) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT p.id AS product_id, p.sku, p.name,
               p.price_satang AS unit_price_satang, p.stock, ci.qty
        FROM cart_items AS ci
        JOIN products AS p ON p.id = ci.product_id
        WHERE ci.cart_id = ?
        ORDER BY p.id
        """,
        (cart_id,),
    ).fetchall()


def get_cart_item(
    connection: sqlite3.Connection, cart_id: str, product_id: int
) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT qty FROM cart_items WHERE cart_id = ? AND product_id = ?",
        (cart_id, product_id),
    ).fetchone()


def set_item_quantity(
    connection: sqlite3.Connection,
    cart_id: str,
    product_id: int,
    qty: int,
    *,
    adding: bool,
) -> None:
    get_cart(connection, cart_id)
    product = get_product(connection, product_id)
    item = get_cart_item(connection, cart_id, product_id)
    if not adding and item is None:
        raise CartError(404, "CART_ITEM_NOT_FOUND", "ไม่พบสินค้าในตะกร้า")
    resulting_qty = qty + item["qty"] if adding and item is not None else qty
    if resulting_qty > 10:
        raise CartError(409, "QTY_LIMIT", "จำนวนสินค้าต่อรายการต้องไม่เกิน 10 ชิ้น")
    if resulting_qty > product["stock"]:
        raise CartError(409, "OUT_OF_STOCK", "สินค้าไม่พอ")
    connection.execute(
        """
        INSERT INTO cart_items (cart_id, product_id, qty) VALUES (?, ?, ?)
        ON CONFLICT(cart_id, product_id) DO UPDATE SET qty = excluded.qty
        """,
        (cart_id, product_id, resulting_qty),
    )


def delete_cart_item(
    connection: sqlite3.Connection, cart_id: str, product_id: int
) -> None:
    get_cart(connection, cart_id)
    get_product(connection, product_id)
    if get_cart_item(connection, cart_id, product_id) is None:
        raise CartError(404, "CART_ITEM_NOT_FOUND", "ไม่พบสินค้าในตะกร้า")
    connection.execute(
        "DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?",
        (cart_id, product_id),
    )


def set_discount_code(
    connection: sqlite3.Connection, cart_id: str, code: str | None
) -> None:
    get_cart(connection, cart_id)
    connection.execute(
        "UPDATE carts SET discount_code = ? WHERE id = ?", (code, cart_id)
    )
