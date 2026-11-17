from contextlib import closing

from app.db import get_connection, init_db
from app.repository import insert_products

SEED_PRODUCTS = [
    (1, "TSHIRT-01", "เสื้อยืดนักพัฒนา", 29900, 20),
    (2, "MUG-01", "แก้วกาแฟ", 15900, 15),
    (3, "EARBUD-01", "หูฟังไร้สาย", 129000, 5),
    (4, "CABLE-01", "สายชาร์จ USB-C", 19900, 2),
    (5, "STICKER-01", "สติกเกอร์", 100, 100),
    (6, "TOTE-01", "กระเป๋าผ้า", 49900, 10),
    (7, "KEYBOARD-01", "คีย์บอร์ด", 249000, 0),
    (8, "MOUSE-01", "เมาส์", 59000, 8),
]


def seed() -> None:
    init_db()
    with closing(get_connection()) as connection, connection:
        insert_products(connection, SEED_PRODUCTS)


if __name__ == "__main__":
    seed()
