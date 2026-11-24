from decimal import Decimal, ROUND_HALF_UP
C = Decimal("0.01")
def r(x): return Decimal(x).quantize(C, rounding=ROUND_HALF_UP)
def checkout(items, codes):
    merged = {}
    for sku, p, q in items:
        if sku in merged: merged[sku][1] += q
        else: merged[sku] = [Decimal(str(p)), q]
    seen, pct, flat, free, bogo = set(), Decimal(0), False, False, set()
    for raw in codes:
        c = raw.strip()
        if c.upper().startswith("BOGO:"):
            bogo.add(c[5:]); continue
        u = c.upper()
        if u == "SAVE10": pct = max(pct, Decimal("0.10"))
        elif u == "SAVE20": pct = max(pct, Decimal("0.20"))
        elif u == "FLAT5": flat = True
        elif u == "FREESHIP": free = True
        else: raise ValueError(f"unknown code: {c}")
    before = sum(p * q for p, q in merged.values()) if merged else Decimal(0)
    g = sum(p * (q - (q // 2 if s in bogo else 0)) for s, (p, q) in merged.items()) if merged else Decimal(0)
    g = g * (1 - pct)
    if flat: g = max(g - 5, Decimal(0))
    ship = Decimal(0) if (not merged or free or g >= 50) else Decimal("7.50")
    tax = (g + ship) * Decimal("0.15")
    G, S, T = r(g), r(ship), r(tax)
    return {"goods": G, "discount": r(before - g), "shipping": S, "tax": T, "total": G + S + T}
