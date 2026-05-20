from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")


def to_decimal(value) -> Decimal:
    """Convert a value to Decimal, handling float/string/Decimal inputs.

    SQLite with aiosqlite returns float for Numeric columns instead of Decimal,
    so we need to explicitly convert.
    """
    if isinstance(value, Decimal):
        return value
    if value is None:
        return ZERO
    return Decimal(str(value))
