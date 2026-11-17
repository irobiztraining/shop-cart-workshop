import os
import sqlite3
from contextlib import closing

from app.repository import enable_foreign_keys, init_schema


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        os.environ.get("DB_PATH", "cart.db"), check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    enable_foreign_keys(connection)
    return connection


def init_db() -> None:
    with closing(get_connection()) as connection, connection:
        init_schema(connection)
