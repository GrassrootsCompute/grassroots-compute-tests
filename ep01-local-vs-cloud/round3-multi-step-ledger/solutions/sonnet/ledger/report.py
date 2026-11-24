from datetime import date
from decimal import Decimal, ROUND_HALF_UP

_CENT = Decimal("0.01")


def month_range(year, month):
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1)
    return start, end


def in_month(txns, year, month):
    start, end = month_range(year, month)
    return [t for t in txns if start <= t.when < end]


def _to_xbs(amount, currency, rates):
    if currency == "XBS":
        return amount
    if rates is None or currency not in rates:
        raise ValueError(f"No rate for currency: {currency}")
    return amount * rates[currency]


def summary(txns, year, month, rates=None):
    ts = in_month(txns, year, month)
    income = Decimal(0)
    spend = Decimal(0)
    by_category = {}
    for t in ts:
        xbs = _to_xbs(t.amount, t.currency, rates)
        if xbs > 0:
            income += xbs
        else:
            spend += (-xbs)
        by_category[t.category] = by_category.get(t.category, Decimal(0)) + xbs
    income = income.quantize(_CENT, rounding=ROUND_HALF_UP)
    spend = spend.quantize(_CENT, rounding=ROUND_HALF_UP)
    net = income - spend
    by_category = {cat: amt.quantize(_CENT, rounding=ROUND_HALF_UP) for cat, amt in by_category.items()}
    return {"income": income, "spend": spend, "net": net, "count": len(ts), "by_category": by_category}
