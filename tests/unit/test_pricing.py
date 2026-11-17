import pytest

from app.pricing import CartTotals, calc_cart_totals
from tests import catalog


@pytest.mark.parametrize(
    ("lines", "discount_code", "expected"),
    [
        ([], None, CartTotals(0, 0, 0, 0)),
        ([(0, 1)], None, CartTotals(0, 0, 5_000, 5_000)),
        (
            [(catalog.PRICE[catalog.TOTE], 1)],
            "SAVE10",
            CartTotals(49_900, 0, 5_000, 54_900),
        ),
        (
            [(catalog.PRICE[catalog.TOTE], 1), (catalog.PRICE[catalog.STICKER], 1)],
            "SAVE10",
            CartTotals(50_000, 5_000, 5_000, 50_000),
        ),
        ([(50_005, 1)], "SAVE10", CartTotals(50_005, 5_001, 5_000, 50_004)),
        (
            [(catalog.PRICE[catalog.TOTE], 2)],
            None,
            CartTotals(99_800, 0, 5_000, 104_800),
        ),
        (
            [(catalog.PRICE[catalog.TOTE], 2), (catalog.PRICE[catalog.STICKER], 2)],
            None,
            CartTotals(100_000, 0, 0, 100_000),
        ),
        ([(111_110, 1)], "SAVE10", CartTotals(111_110, 11_111, 5_000, 104_999)),
        ([(111_111, 1)], "SAVE10", CartTotals(111_111, 11_111, 0, 100_000)),
    ],
    ids=[
        "empty-cart",
        "zero-subtotal-with-line",
        "save10-below-500",
        "save10-at-500",
        "save10-round-half-up",
        "shipping-below-1000",
        "shipping-at-1000",
        "discounted-shipping-one-satang-below-1000",
        "discounted-shipping-at-1000",
    ],
)
def test_calc_cart_totals(
    lines: list[tuple[int, int]],
    discount_code: str | None,
    expected: CartTotals,
) -> None:
    assert calc_cart_totals(lines, discount_code) == expected
