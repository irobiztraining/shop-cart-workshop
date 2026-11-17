import os
import sqlite3
from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app import repository
from app.db import get_db
from app.pricing import (
    DISCOUNT_RATES,
    MIN_SUBTOTAL_FOR_DISCOUNT,
    calc_cart_totals,
)
from app.seed import SEED_PRODUCTS

router = APIRouter(prefix="/api")


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    price_satang: int
    stock: int


class CartItemOut(BaseModel):
    product_id: int
    sku: str
    name: str
    unit_price_satang: int
    line_total_satang: int
    stock: int
    qty: int


class CartOut(BaseModel):
    cart_id: str
    items: list[CartItemOut]
    discount_code: str | None
    subtotal_satang: int
    discount_satang: int
    shipping_satang: int
    total_satang: int


class AddItemIn(BaseModel):
    model_config = ConfigDict(strict=True)

    product_id: int
    qty: int = Field(default=1, ge=1)


class UpdateItemIn(BaseModel):
    model_config = ConfigDict(strict=True)

    qty: int = Field(ge=1)


class DiscountIn(BaseModel):
    model_config = ConfigDict(strict=True)

    code: str


Database = Annotated[sqlite3.Connection, Depends(get_db, scope="function")]


def cart_out(connection: sqlite3.Connection, cart_id: str) -> CartOut:
    cart = repository.get_cart(connection, cart_id)
    items = [
        CartItemOut(
            **dict(row),
            line_total_satang=calc_cart_totals(
                [(row["unit_price_satang"], row["qty"])], None
            ).subtotal_satang,
        )
        for row in repository.list_cart_items(connection, cart_id)
    ]
    totals = calc_cart_totals(
        [(item.unit_price_satang, item.qty) for item in items], cart["discount_code"]
    )
    return CartOut(
        cart_id=cart["id"],
        items=items,
        discount_code=cart["discount_code"],
        subtotal_satang=totals.subtotal_satang,
        discount_satang=totals.discount_satang,
        shipping_satang=totals.shipping_satang,
        total_satang=totals.total_satang,
    )


@router.get("/products")
def list_products(connection: Database) -> list[ProductOut]:
    return [
        ProductOut.model_validate(dict(row))
        for row in repository.list_products(connection)
    ]


@router.post("/carts", status_code=201)
def create_cart(connection: Database) -> CartOut:
    cart_id = str(uuid4())
    repository.create_cart(
        connection, cart_id, datetime.now(timezone.utc).isoformat()
    )
    return cart_out(connection, cart_id)


@router.get("/carts/{cart_id}")
def get_cart(cart_id: str, connection: Database) -> CartOut:
    return cart_out(connection, cart_id)


@router.post("/carts/{cart_id}/items")
def add_item(cart_id: str, body: AddItemIn, connection: Database) -> CartOut:
    repository.set_item_quantity(
        connection, cart_id, body.product_id, body.qty, adding=True
    )
    return cart_out(connection, cart_id)


@router.patch("/carts/{cart_id}/items/{product_id}")
def update_item(
    cart_id: str, product_id: int, body: UpdateItemIn, connection: Database
) -> CartOut:
    repository.set_item_quantity(
        connection, cart_id, product_id, body.qty, adding=False
    )
    return cart_out(connection, cart_id)


@router.delete("/carts/{cart_id}/items/{product_id}")
def delete_item(cart_id: str, product_id: int, connection: Database) -> CartOut:
    repository.delete_cart_item(connection, cart_id, product_id)
    return cart_out(connection, cart_id)


@router.put("/carts/{cart_id}/discount")
def apply_discount(
    cart_id: str, body: DiscountIn, connection: Database
) -> CartOut:
    cart = cart_out(connection, cart_id)
    if body.code not in DISCOUNT_RATES:
        raise repository.CartError(422, "INVALID_CODE", "รหัสส่วนลดไม่ถูกต้อง")
    if cart.subtotal_satang < MIN_SUBTOTAL_FOR_DISCOUNT:
        raise repository.CartError(409, "MIN_SUBTOTAL", "ยอดซื้อขั้นต่ำ ฿500.00")
    repository.set_discount_code(connection, cart_id, body.code)
    return cart_out(connection, cart_id)


@router.delete("/carts/{cart_id}/discount")
def remove_discount(cart_id: str, connection: Database) -> CartOut:
    repository.set_discount_code(connection, cart_id, None)
    return cart_out(connection, cart_id)


if os.environ.get("APP_ENV") == "test":
    @router.post("/test/reset")
    def reset_test_database(connection: Database) -> dict[str, str]:
        repository.reset_db(connection)
        repository.insert_products(connection, SEED_PRODUCTS)
        return {"status": "ok"}
