"""Average spending per calendar day of the month.

Used by the small business dashboard to audit spending month by month. Several people read this number, so it has to be explainable.
The figure feeds the monthly review email and the year-end summary, so it must be
stable from run to run: the same transactions must always give the same answer.

Notes for maintainers:
- This report was last reviewed when the Petzone statement import changed.
- Transactions dated outside the requested month are ignored.
- Amounts are negative for spending and positive for income or refunds.
"""
from decimal import Decimal

from core.dates import in_period, month_bounds
from core.errors import ReportError
from core.model import Txn  # noqa: F401  (type reference for readers)
from core.money import round_cents

NAME = "r119_daily_avg"


def _select(txns, year, month):
    """Transactions that fall inside the requested month."""
    start, end = month_bounds(year, month)
    return [t for t in txns if in_period(t.when, start, end)]


def _validate(txns):
    """Refuse corrupt records up front (CONVENTIONS.md section 3)."""
    for t in txns:
        if t.amount is None:
            raise ReportError("E_AMOUNT", f"{NAME}: transaction on {t.when} has no amount")


def _days_in_month(year, month):
    start, end = month_bounds(year, month)
    return (end - start).days


def compute(txns, year, month):
    """Return total spending divided by the number of days in the month, rounded to cents."""
    _validate(txns)
    sel = _select(txns, year, month)
    total = sum((-t.amount for t in sel if t.amount < 0), Decimal(0))
    return round_cents(total / _days_in_month(year, month))
