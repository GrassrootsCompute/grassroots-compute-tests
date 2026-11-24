from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal("0.01")
SHIPPING = Decimal("7.50")
FREE_SHIPPING_THRESHOLD = Decimal("50.00")
FLAT_OFF = Decimal("5.00")
TAX_RATE = Decimal("0.15")


def _round(amount):
    return Decimal(amount).quantize(CENTS, rounding=ROUND_HALF_UP)


def checkout(items, codes):
    # Merge duplicate skus: first unit_price wins, quantities add up.
    merged = {}
    for sku, unit_price, qty in items:
        if sku in merged:
            merged[sku][1] += qty
        else:
            merged[sku] = [Decimal(unit_price), qty]

    # Parse promo codes: case-insensitive, whitespace-trimmed, duplicates once.
    bogo_skus = set()
    percent = Decimal(0)
    flat = False
    freeship = False
    for raw in codes:
        stripped = raw.strip()
        lowered = stripped.lower()
        if lowered == "save10":
            percent = max(percent, Decimal("0.10"))
        elif lowered == "save20":
            percent = max(percent, Decimal("0.20"))
        elif lowered == "flat5":
            flat = True
        elif lowered == "freeship":
            freeship = True
        elif lowered.startswith("bogo:"):
            # sku part is case-sensitive exactly as written after the colon
            sku = stripped[len("bogo:"):]
            if sku in merged:
                bogo_skus.add(sku)
        else:
            raise ValueError(f"Unknown promo code: {raw}")

    goods_before = sum(p * q for p, q in merged.values())

    # Order: BOGO, then percentage, then FLAT5.
    goods_after = goods_before
    for sku, (unit_price, qty) in merged.items():
        if sku in bogo_skus:
            goods_after -= unit_price * (qty // 2)
    goods_after *= (Decimal(1) - percent)
    if flat:
        goods_after = max(goods_after - FLAT_OFF, Decimal(0))

    discount = goods_before - goods_after

    if not merged:
        shipping = Decimal(0)
    elif freeship or goods_after >= FREE_SHIPPING_THRESHOLD:
        shipping = Decimal(0)
    else:
        shipping = SHIPPING

    tax = (goods_after + shipping) * TAX_RATE

    goods = _round(goods_after)
    shipping = _round(shipping)
    tax = _round(tax)
    total = _round(goods + shipping + tax)

    return {
        "goods": goods,
        "discount": _round(discount),
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
