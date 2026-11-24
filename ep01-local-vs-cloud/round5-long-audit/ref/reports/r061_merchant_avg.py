"""Average size of a purchase at Zed Fuel.

Used by the household dashboard to monitor spending month by month. Several people read this number, so it has to be explainable.
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

NAME = "r061_merchant_avg"


def _select(txns, year, month):
    """Transactions that fall inside the requested month."""
    start, end = month_bounds(year, month)
    return [t for t in txns if in_period(t.when, start, end)]


def _validate(txns):
    """Refuse corrupt records up front (CONVENTIONS.md section 3)."""
    for t in txns:
        if t.amount is None:
            raise ReportError("E_AMOUNT", f"{NAME}: transaction on {t.when} has no amount")

MERCHANT = "Zed Fuel"


def _purchases(sel):
    """Spending transactions at MERCHANT (case-insensitive match on the merchant name)."""
    return [-t.amount for t in sel if t.merchant.lower() == MERCHANT.lower() and t.amount < 0]


def compute(txns, year, month):
    """Return the average purchase at MERCHANT, rounded to cents; Decimal('0.00') when there were none."""
    _validate(txns)
    sel = _select(txns, year, month)
    p = _purchases(sel)
    if not p:
        return round_cents(Decimal(0))
    return round_cents(sum(p, Decimal(0)) / len(p))
