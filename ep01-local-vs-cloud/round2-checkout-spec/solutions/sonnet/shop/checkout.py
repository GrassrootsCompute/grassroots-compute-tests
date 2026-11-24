from decimal import Decimal, ROUND_HALF_UP


def checkout(items, codes):
    CENT = Decimal("0.01")

    def _round(d):
        return d.quantize(CENT, rounding=ROUND_HALF_UP)

    # Parse and validate codes
    seen = set()
    has_save10 = False
    has_save20 = False
    has_flat5 = False
    has_freeship = False
    bogo_skus = set()

    for code in codes:
        stripped = code.strip()
        upper = stripped.upper()

        # Determine dedup key: BOGO uses uppercase prefix + original sku
        if upper.startswith("BOGO:"):
            sku = stripped[5:]
            dedup_key = "BOGO:" + sku
        else:
            dedup_key = upper

        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        if upper == "SAVE10":
            has_save10 = True
        elif upper == "SAVE20":
            has_save20 = True
        elif upper == "FLAT5":
            has_flat5 = True
        elif upper == "FREESHIP":
            has_freeship = True
        elif upper.startswith("BOGO:"):
            bogo_skus.add(sku)
        else:
            raise ValueError(f"Unknown promo code: {code}")

    # Merge items: first unit_price wins for duplicate skus
    sku_map = {}
    for sku, unit_price, qty in items:
        price = Decimal(str(unit_price))
        if sku in sku_map:
            old_price, old_qty = sku_map[sku]
            sku_map[sku] = (old_price, old_qty + qty)
        else:
            sku_map[sku] = (price, qty)

    # Goods before any discount
    goods_before = sum(price * qty for price, qty in sku_map.values()) if sku_map else Decimal("0")

    # Apply BOGO
    goods = Decimal("0")
    for sku, (price, qty) in sku_map.items():
        if sku in bogo_skus:
            paid = qty - qty // 2
        else:
            paid = qty
        goods += price * paid

    # Apply percentage discount (use larger if both given)
    if has_save20:
        goods *= Decimal("0.80")
    elif has_save10:
        goods *= Decimal("0.90")

    # Apply FLAT5
    if has_flat5:
        goods = max(Decimal("0"), goods - Decimal("5"))

    # Shipping
    if not sku_map:
        shipping = Decimal("0")
    elif has_freeship or goods >= Decimal("50"):
        shipping = Decimal("0")
    else:
        shipping = Decimal("7.50")

    # TAX 15%
    tax = (goods + shipping) * Decimal("0.15")

    r_goods = _round(goods)
    r_discount = _round(goods_before - goods)
    r_shipping = _round(shipping)
    r_tax = _round(tax)
    r_total = r_goods + r_shipping + r_tax

    return {
        "goods": r_goods,
        "discount": r_discount,
        "shipping": r_shipping,
        "tax": r_tax,
        "total": r_total,
    }
