from dataclasses import dataclass

DISCOUNT_RATES = {"SAVE10": 10}
MIN_SUBTOTAL_FOR_DISCOUNT = 50_000
FREE_SHIPPING_THRESHOLD = 100_000
SHIPPING_FEE = 5_000


@dataclass(frozen=True)
class CartTotals:
    subtotal_satang: int
    discount_satang: int
    shipping_satang: int
    total_satang: int


def calc_cart_totals(
    lines: list[tuple[int, int]], discount_code: str | None
) -> CartTotals:
    """Calculate totals for validated cart lines and an optional saved code."""
    if discount_code is not None and discount_code not in DISCOUNT_RATES:
        raise ValueError("INVALID_CODE")

    subtotal_satang = sum(unit_price_satang * qty for unit_price_satang, qty in lines)
    discount_satang = 0
    if discount_code is not None and subtotal_satang >= MIN_SUBTOTAL_FOR_DISCOUNT:
        discount_satang = (subtotal_satang * DISCOUNT_RATES[discount_code] + 50) // 100

    net_satang = subtotal_satang - discount_satang
    shipping_satang = (
        SHIPPING_FEE if lines and net_satang < FREE_SHIPPING_THRESHOLD else 0
    )
    return CartTotals(
        subtotal_satang=subtotal_satang,
        discount_satang=discount_satang,
        shipping_satang=shipping_satang,
        total_satang=net_satang + shipping_satang,
    )
