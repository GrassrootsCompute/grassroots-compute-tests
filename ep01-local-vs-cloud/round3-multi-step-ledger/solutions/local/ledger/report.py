from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def month_range(year, month):
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1)
    return start, end


def in_month(txns, year, month):
    # end is the first day of the next month, so the comparison must be exclusive:
    # `<=` would pull in the first day of the following month (e.g. 2026-03-01 in a Feb report).
    start, end = month_range(year, month)
    return [t for t in txns if start <= t.when < end]


def to_xbs(amount, currency, rates):
    if currency == "XBS":
        return amount
    if rates is None or currency not in rates:
        raise ValueError(f"no exchange rate for currency {currency}")
    return amount * rates[currency]


def round_cents(value):
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def summary(txns, year, month, rates=None):
    ts = in_month(txns, year, month)
    # Convert every amount to XBS first; accumulate at full precision, round only at the end.
    xbs = [to_xbs(t.amount, t.currency, rates) for t in ts]
    income = sum((a for a in xbs if a > 0), Decimal(0))
    spend = sum((-a for a in xbs if a < 0), Decimal(0))
    by_category = {}
    for t, a in zip(ts, xbs):
        by_category[t.category] = by_category.get(t.category, Decimal(0)) + a
    income = round_cents(income)
    spend = round_cents(spend)
    by_category = {cat: round_cents(net) for cat, net in by_category.items()}
    return {"income": income, "spend": spend, "net": income - spend, "count": len(ts), "by_category": by_category}
