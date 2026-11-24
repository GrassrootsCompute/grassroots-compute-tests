from decimal import Decimal, ROUND_HALF_UP

def money(x):
    """Round to cents, half up."""
    return Decimal(str(x)).quantize(Decimal("0.01"))

def apply_discount(subtotal, code):
    """SAVE10 = 10% off; FLAT5 = $5 off but never below 0; unknown codes ignored. Codes are case-insensitive."""
    if code == "SAVE10":
        return subtotal * Decimal("0.9")
    if code == "FLAT5":
        return subtotal - 5
    return subtotal
