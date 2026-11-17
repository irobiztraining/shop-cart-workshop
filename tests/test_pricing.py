import pytest

from app.pricing import CartTotals, calc_cart_totals


@pytest.mark.parametrize(
    ("lines", "discount_code", "expected"),
    [
        ([(49_900, 1)], None, CartTotals(49_900, 0, 5_000, 54_900)),
        ([(49_900, 1), (100, 1)], "SAVE10", CartTotals(50_000, 5_000, 5_000, 50_000)),
        ([], None, CartTotals(0, 0, 0, 0)),
        ([], "SAVE10", CartTotals(0, 0, 0, 0)),
        ([(0, 1)], None, CartTotals(0, 0, 5_000, 5_000)),
        ([(29_900, 2), (100, 3)], None, CartTotals(60_100, 0, 5_000, 65_100)),
        ([(49_999, 1)], "SAVE10", CartTotals(49_999, 0, 5_000, 54_999)),
        ([(50_004, 1)], "SAVE10", CartTotals(50_004, 5_000, 5_000, 50_004)),
        ([(50_005, 1)], "SAVE10", CartTotals(50_005, 5_001, 5_000, 50_004)),
        ([(50_006, 1)], "SAVE10", CartTotals(50_006, 5_001, 5_000, 50_005)),
        ([(99_999, 1)], None, CartTotals(99_999, 0, 5_000, 104_999)),
        ([(100_000, 1)], None, CartTotals(100_000, 0, 0, 100_000)),
        ([(100_000, 1)], "SAVE10", CartTotals(100_000, 10_000, 5_000, 95_000)),
        ([(111_110, 1)], "SAVE10", CartTotals(111_110, 11_111, 5_000, 104_999)),
        ([(111_111, 1)], "SAVE10", CartTotals(111_111, 11_111, 0, 100_000)),
    ],
)
def test_cart_totals(
    lines: list[tuple[int, int]],
    discount_code: str | None,
    expected: CartTotals,
) -> None:
    assert calc_cart_totals(lines, discount_code) == expected


def test_discount_rounds_subtotal_instead_of_each_line() -> None:
    assert calc_cart_totals([(25_005, 1), (25_005, 1)], "SAVE10") == CartTotals(
        50_010, 5_001, 5_000, 50_009
    )


def test_unknown_code_is_rejected() -> None:
    with pytest.raises(ValueError, match="INVALID_CODE"):
        calc_cart_totals([(50_000, 1)], "UNKNOWN")
