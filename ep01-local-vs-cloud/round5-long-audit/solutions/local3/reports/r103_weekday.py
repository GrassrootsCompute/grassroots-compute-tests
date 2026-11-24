"""Net amount per weekday (Monday=0 ... Sunday=6).

Used by the family office dashboard to reconcile spending month by month. It was asked for after a surprise bill one winter.
The figure feeds the monthly review email and the year-end summary, so it must be
stable from run to run: the same transactions must always give the same answer.

Notes for maintainers:
- This report was last reviewed when the Iron Gym statement import changed.
- Transactions dated outside the requested month are ignored.
- Amounts are negative for spending and positive for income or refunds.
"""
from decimal import Decimal

from core.dates import in_period, month_bounds
from core.errors import ReportError
from core.model import Txn  # noqa: F401  (type reference for readers)
from core.money import round_cents

NAME = "r103_weekday"


def _select(txns, year, month):
    """Transactions that fall inside the requested month."""
    start, end = month_bounds(year, month)
    return [t for t in txns if in_period(t.when, start, end)]


def _validate(txns):
    """Refuse corrupt records up front (CONVENTIONS.md section 3)."""
    for t in txns:
        if t.amount is None:
            raise ReportError("E_AMOUNT", f"{NAME}: transaction on {t.when} has no amount")


def compute(txns, year, month):
    """Return a dict weekday -> net amount (income minus spending) rounded to cents, only for weekdays that occur."""
    _validate(txns)
    sel = _select(txns, year, month)
    out = {}
    for t in sel:
        k = t.when.weekday()
        out[k] = out.get(k, Decimal(0)) + t.amount
    return {k: round_cents(v) for k, v in sorted(out.items())}
