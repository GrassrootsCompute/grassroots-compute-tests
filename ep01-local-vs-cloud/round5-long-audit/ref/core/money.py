from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def round_cents(x):
    """The ONLY sanctioned way to round money: to cents, half-up. See CONVENTIONS.md section 1."""
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)
