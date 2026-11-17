import os
import sqlite3
from collections.abc import Iterator
from contextlib import closing

from app.repository import begin_transaction, enable_foreign_keys, init_schema


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        os.environ.get("DB_PATH", "cart.db"), check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    enable_foreign_keys(connection)
    return connection


def get_db() -> Iterator[sqlite3.Connection]:
    connection = get_connection()
    try:
        with connection:
            begin_transaction(connection)
            yield connection
    finally:
        connection.close()


def init_db() -> None:
    with closing(get_connection()) as connection, connection:
        init_schema(connection)
