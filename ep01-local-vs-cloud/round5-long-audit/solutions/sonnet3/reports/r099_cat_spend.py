"""Total spending in the 'transport' category.

Used by the small business dashboard to budget spending month by month. It was asked for after a surprise bill one winter.
The figure feeds the monthly review email and the year-end summary, so it must be
stable from run to run: the same transactions must always give the same answer.

Notes for maintainers:
- This report was last reviewed when the Maple Books statement import changed.
- Transactions dated outside the requested month are ignored.
- Amounts are negative for spending and positive for income or refunds.
"""
from decimal import Decimal

from core.dates import in_period, month_bounds
from core.errors import ReportError
from core.model import Txn  # noqa: F401  (type reference for readers)
from core.money import round_cents

NAME = "r099_cat_spend"


def _select(txns, year, month):
    """Transactions that fall inside the requested month."""
    lo, hi = month_bounds(year, month)
    return [t for t in txns if not (t.when < lo or t.when > hi)]


def _validate(txns):
    """Refuse corrupt records up front (CONVENTIONS.md section 3)."""
    for t in txns:
        if t.amount is None:
            raise ReportError("E_AMOUNT", f"{NAME}: transaction on {t.when} has no amount")

CATEGORY = "transport"


def _matches(t):
    """A transaction counts when it is spending in CATEGORY."""
    return t.category == CATEGORY and t.amount < 0


def compute(txns, year, month):
    """Return the total spending (a positive Decimal, rounded to cents) in CATEGORY for the month."""
    _validate(txns)
    sel = _select(txns, year, month)
    total = sum((-t.amount for t in sel if _matches(t)), Decimal(0))
    return round_cents(total)
