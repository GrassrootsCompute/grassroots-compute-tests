from datetime import date
from decimal import Decimal


def month_range(year, month):
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1)
    return start, end


def in_month(txns, year, month):
    start, end = month_range(year, month)
    return [t for t in txns if start <= t.when <= end]


def summary(txns, year, month):
    ts = in_month(txns, year, month)
    income = sum((t.amount for t in ts if t.amount > 0), Decimal(0))
    spend = sum((-t.amount for t in ts if t.amount < 0), Decimal(0))
    return {"income": income, "spend": spend, "net": income - spend, "count": len(ts)}
