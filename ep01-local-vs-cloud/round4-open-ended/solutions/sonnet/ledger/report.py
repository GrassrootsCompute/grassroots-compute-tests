import calendar
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


def summary(txns, year, month, rates=None):
    ts = in_month(txns, year, month); inc = sp = Decimal(0); bc = {}
    for t in ts:
        v = to_xbs(t, rates)
        if v > 0: inc += v
        else: sp += -v
        bc[t.category] = bc.get(t.category, Decimal(0)) + v
    i, s = r2(inc), r2(sp)
    return {"income": i, "spend": s, "net": i - s, "count": len(ts), "by_category": {k: r2(v) for k, v in bc.items()}}


def budget_status(txns, budgets, year, month, today=None, rates=None):
    """
    Returns a dict with per-category pace information for the given month.

    Each category row contains:
      spent      – amount spent so far (positive)
      budget     – monthly limit, or None if unset
      remaining  – budget - spent, or None
      projected  – linear extrapolation to end-of-month, or None
      on_pace    – projected <= budget, or None if no budget

    days_elapsed is capped at days_in_month for past months.
    """
    if today is None:
        today = date.today()

    ts = in_month(txns, year, month)
    total_days = calendar.monthrange(year, month)[1]

    if today.year == year and today.month == month:
        days_elapsed = today.day
    else:
        days_elapsed = total_days

    by_cat = {}
    for t in ts:
        v = to_xbs(t, rates)
        if v < 0:
            by_cat[t.category] = by_cat.get(t.category, Decimal(0)) + (-v)

    rows = []
    for cat in sorted(set(by_cat) | set(budgets)):
        spent = r2(by_cat.get(cat, Decimal(0)))
        budget = budgets.get(cat)

        if budget is not None:
            budget = r2(Decimal(str(budget)))
            remaining = r2(budget - spent)
            if days_elapsed > 0:
                projected = r2(spent / Decimal(days_elapsed) * Decimal(total_days))
            else:
                projected = spent
            on_pace = projected <= budget
        else:
            remaining = projected = on_pace = None

        rows.append({
            "category": cat,
            "spent": spent,
            "budget": budget,
            "remaining": remaining,
            "projected": projected,
            "on_pace": on_pace,
        })

    return {
        "year": year,
        "month": month,
        "days_elapsed": days_elapsed,
        "days_in_month": total_days,
        "total_spend": r2(sum(by_cat.values(), Decimal(0))),
        "categories": rows,
    }
