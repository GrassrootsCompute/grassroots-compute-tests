"""Share of the month's spending that went to 'groceries', as a percentage.

Used by the small business dashboard to review spending month by month. It replaced a spreadsheet that drifted out of date.
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

NAME = "r031_share"


def _select(txns, year, month):
    """Transactions that fall inside the requested month."""
    start, end = month_bounds(year, month)
    return [t for t in txns if in_period(t.when, start, end)]


def _validate(txns):
    """Refuse corrupt records up front (CONVENTIONS.md section 3)."""
    for t in txns:
        if t.amount is None:
            raise ReportError("E_AMOUNT", f"{NAME}: transaction on {t.when} has no amount")

CATEGORY = "groceries"


def compute(txns, year, month):
    """Return {"spent": money, "total": money, "percent": Decimal}. percent is unrounded (it is not money)."""
    _validate(txns)
    sel = _select(txns, year, month)
    spend = [t for t in sel if t.amount < 0]
    total = sum((-t.amount for t in spend), Decimal(0))
    spent = sum((-t.amount for t in spend if t.category == CATEGORY), Decimal(0))
    pct = (spent * 100 / total) if total else Decimal(0)
    return {"spent": round_cents(spent), "total": round_cents(total), "percent": pct}
