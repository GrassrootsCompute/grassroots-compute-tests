from datetime import date
from decimal import Decimal, ROUND_HALF_UP
C = Decimal("0.01")
def r2(x): return x.quantize(C, rounding=ROUND_HALF_UP)
def month_range(year, month):
    return date(year, month, 1), date(year + (month == 12), month % 12 + 1, 1)
def in_month(txns, year, month):
    s, e = month_range(year, month)
    return [t for t in txns if s <= t.when < e]
def to_xbs(t, rates):
    if t.currency == "XBS": return t.amount
    if not rates or t.currency not in rates: raise ValueError(f"no rate for {t.currency}")
    return t.amount * Decimal(str(rates[t.currency]))
def pace(txns, year, month, limit=None, rates=None, today=None):
    """How much has been spent so far in the month, and where that pace
    projects the month to end, compared with a (optional) spend limit."""
    today = today or date.today()
    s, e = month_range(year, month)
    spend = Decimal(0); n = 0
    for t in txns:
        if s <= t.when < e:
            n += 1
            v = to_xbs(t, rates)
            if v < 0: spend += -v
    spend = r2(spend)
    days = (e - s).days
    if today < s: elapsed = 0
    elif today >= e: elapsed = days
    else: elapsed = (today - s).days + 1
    projected = spend if elapsed == 0 or elapsed >= days else r2(spend * days / Decimal(elapsed))
    if limit is None: status = "no budget"
    elif spend > limit: status = "over"
    elif projected > limit: status = "warning"
    else: status = "ok"
    return {"spend": spend, "count": n, "limit": r2(limit) if limit is not None else None,
            "remaining": r2(limit - spend) if limit is not None else None,
            "projected": projected, "days_used": elapsed, "days_total": days, "status": status}

def summary(txns, year, month, rates=None):
    ts = in_month(txns, year, month); inc = sp = Decimal(0); bc = {}
    for t in ts:
        v = to_xbs(t, rates)
        if v > 0: inc += v
        else: sp += -v
        bc[t.category] = bc.get(t.category, Decimal(0)) + v
    i, s = r2(inc), r2(sp)
    return {"income": i, "spend": s, "net": i - s, "count": len(ts), "by_category": {k: r2(v) for k, v in bc.items()}}
