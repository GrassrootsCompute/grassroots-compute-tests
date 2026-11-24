import os, random, json, shutil, sys
from textwrap import dedent
R = random.Random(7)
OUT = sys.argv[1]
def w(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(s)

CORE = {
"core/__init__.py": "",
"core/money.py": '''from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def round_cents(x):
    """The ONLY sanctioned way to round money: to cents, half-up. See CONVENTIONS.md section 1."""
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)
''',
"core/dates.py": '''from datetime import date


def month_bounds(year, month):
    """Return (first day of the month, first day of the NEXT month). The end bound is exclusive."""
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1)
    return start, end


def in_period(d, start, end):
    """True when start <= d < end. Use this for every period filter (CONVENTIONS.md section 2)."""
    return start <= d < end
''',
"core/errors.py": '''class ReportError(Exception):
    """Raised by report modules for bad input. `code` is a short machine-readable string (CONVENTIONS.md section 3)."""

    def __init__(self, code, message):
        super().__init__(f"[{code}] {message}")
        self.code = code
''',
"core/model.py": '''from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Txn:
    when: date
    amount: Optional[Decimal]  # negative = spending; None = corrupted record
    category: str = "other"
    merchant: str = ""
''',
}
CONV = '''# Report module conventions

Every module in `reports/` exposes `compute(txns, year, month)` and must follow these rules.

## 1. Money rounding
Every money value a report returns (including values inside dicts) must be rounded with
`core.money.round_cents` (to cents, half-up), applied once to the final value. Do not use
`round()`, bare `Decimal.quantize()` without the rounding mode, or string formatting for rounding.
Percentages are not money: return them unrounded as Decimal.

## 2. Period filtering
Selecting the transactions of a month must use `core.dates.month_bounds` together with
`core.dates.in_period` (end bound exclusive). Never hand-write the comparison.

## 3. Bad input
A transaction whose `amount` is None is corrupt. `compute` must raise
`core.errors.ReportError` with code `"E_AMOUNT"` before doing anything else - never skip the
record, never return None, never raise a different exception type.

## 4. Everything else
Keep each report's business logic exactly as it is. Only fix violations of rules 1-3.
'''
CATS = ["groceries","dining","transport","rent","utilities","health","travel","gifts","education","fitness","pets","books","coffee","subscriptions","insurance"]
MERCH = ["Marketa","SaveMart","Rideo","Zed Fuel","Sparko","Mercuro","Air Nine","Shopmart","Depot Store","Maple Books","Petzone","Iron Gym","Netflix","Spotify","Shield Health"]
TEAMS = ["household","family office","personal","shared flat","small business"]
VERBS = ["monitor","review","budget","forecast","audit","reconcile"]

def doc(title, extra):
    team = R.choice(TEAMS); v = R.choice(VERBS)
    lines = [f'"""{title}', "",
             f"Used by the {team} dashboard to {v} spending month by month. {extra}",
             "The figure feeds the monthly review email and the year-end summary, so it must be",
             "stable from run to run: the same transactions must always give the same answer.",
             "",
             "Notes for maintainers:",
             f"- This report was last reviewed when the {R.choice(MERCH)} statement import changed.",
             "- Transactions dated outside the requested month are ignored.",
             "- Amounts are negative for spending and positive for income or refunds.",
             '"""']
    return "\n".join(lines)

FAMILIES = []
def fam(f): FAMILIES.append(f); return f

@fam
def cat_spend(i):
    c = R.choice(CATS)
    return f"Total spending in the '{c}' category.", f'''
CATEGORY = "{c}"


def _matches(t):
    """A transaction counts when it is spending in CATEGORY."""
    return t.category == CATEGORY and t.amount < 0


def compute(txns, year, month):
    """Return the total spending (a positive Decimal, rounded to cents) in CATEGORY for the month."""
    _validate(txns)
    sel = _select(txns, year, month)
    total = sum((-t.amount for t in sel if _matches(t)), Decimal(0))
    return {{MONEY}}(total)
'''

@fam
def merchant_avg(i):
    m = R.choice(MERCH)
    return f"Average size of a purchase at {m}.", f'''
MERCHANT = "{m}"


def _purchases(sel):
    """Spending transactions at MERCHANT (case-insensitive match on the merchant name)."""
    return [-t.amount for t in sel if t.merchant.lower() == MERCHANT.lower() and t.amount < 0]


def compute(txns, year, month):
    """Return the average purchase at MERCHANT, rounded to cents; Decimal('0.00') when there were none."""
    _validate(txns)
    sel = _select(txns, year, month)
    p = _purchases(sel)
    if not p:
        return {{MONEY}}(Decimal(0))
    return {{MONEY}}(sum(p, Decimal(0)) / len(p))
'''

@fam
def share(i):
    c = R.choice(CATS)
    return f"Share of the month's spending that went to '{c}', as a percentage.", f'''
CATEGORY = "{c}"


def compute(txns, year, month):
    """Return {{"spent": money, "total": money, "percent": Decimal}}. percent is unrounded (it is not money)."""
    _validate(txns)
    sel = _select(txns, year, month)
    spend = [t for t in sel if t.amount < 0]
    total = sum((-t.amount for t in spend), Decimal(0))
    spent = sum((-t.amount for t in spend if t.category == CATEGORY), Decimal(0))
    pct = (spent * 100 / total) if total else Decimal(0)
    return {{"spent": {{MONEY}}(spent), "total": {{MONEY}}(total), "percent": pct}}
'''

@fam
def biggest(i):
    return "The single largest spending transaction of the month.", '''

def compute(txns, year, month):
    """Return {"amount": money, "merchant": str} for the biggest spend, or {"amount": Decimal("0.00"), "merchant": ""}."""
    _validate(txns)
    sel = _select(txns, year, month)
    spend = [t for t in sel if t.amount < 0]
    if not spend:
        return {"amount": {MONEY}(Decimal(0)), "merchant": ""}
    top = min(spend, key=lambda t: t.amount)
    return {"amount": {MONEY}(-top.amount), "merchant": top.merchant}
'''

@fam
def weekday(i):
    return "Net amount per weekday (Monday=0 ... Sunday=6).", '''

def compute(txns, year, month):
    """Return a dict weekday -> net amount (income minus spending) rounded to cents, only for weekdays that occur."""
    _validate(txns)
    sel = _select(txns, year, month)
    out = {}
    for t in sel:
        k = t.when.weekday()
        out[k] = out.get(k, Decimal(0)) + t.amount
    return {k: {MONEY}(v) for k, v in sorted(out.items())}
'''

@fam
def daily_avg(i):
    return "Average spending per calendar day of the month.", '''

def _days_in_month(year, month):
    start, end = month_bounds(year, month)
    return (end - start).days


def compute(txns, year, month):
    """Return total spending divided by the number of days in the month, rounded to cents."""
    _validate(txns)
    sel = _select(txns, year, month)
    total = sum((-t.amount for t in sel if t.amount < 0), Decimal(0))
    return {MONEY}(total / _days_in_month(year, month))
'''

@fam
def refunds(i):
    m = R.choice(MERCH)
    return f"Refunds and income received from {m}.", f'''
MERCHANT = "{m}"


def compute(txns, year, month):
    """Return {{"count": int, "total": money}} of positive amounts from MERCHANT."""
    _validate(txns)
    sel = _select(txns, year, month)
    got = [t.amount for t in sel if t.merchant == MERCHANT and t.amount > 0]
    return {{"count": len(got), "total": {{MONEY}}(sum(got, Decimal(0)))}}
'''

HEAD = '''from decimal import Decimal

from core.dates import in_period, month_bounds
from core.errors import ReportError
from core.model import Txn  # noqa: F401  (type reference for readers)
from core.money import round_cents

NAME = "{name}"
'''
SELECT_OK = '''

def _select(txns, year, month):
    """Transactions that fall inside the requested month."""
    start, end = month_bounds(year, month)
    return [t for t in txns if in_period(t.when, start, end)]
'''
SELECT_BAD = [
'''

def _select(txns, year, month):
    """Transactions that fall inside the requested month."""
    start, end = month_bounds(year, month)
    return [t for t in txns if start <= t.when <= end]
''',
'''

def _select(txns, year, month):
    """Transactions that fall inside the requested month."""
    start, end = month_bounds(year, month)
    out = []
    for t in txns:
        if t.when < start:
            continue
        if t.when > end:
            continue
        out.append(t)
    return out
''',
'''

def _select(txns, year, month):
    """Transactions that fall inside the requested month."""
    lo, hi = month_bounds(year, month)
    return [t for t in txns if not (t.when < lo or t.when > hi)]
''']
VAL_OK = '''

def _validate(txns):
    """Refuse corrupt records up front (CONVENTIONS.md section 3)."""
    for t in txns:
        if t.amount is None:
            raise ReportError("E_AMOUNT", f"{NAME}: transaction on {t.when} has no amount")
'''
VAL_BAD = [
'''

def _validate(txns):
    """Refuse corrupt records up front."""
    for t in txns:
        if t.amount is None:
            raise ValueError(f"{NAME}: transaction on {t.when} has no amount")
''',
'''

def _validate(txns):
    """Drop corrupt records so one bad import line does not break the whole report."""
    txns[:] = [t for t in txns if t.amount is not None]
''',
'''

def _validate(txns):
    """Refuse corrupt records up front."""
    for t in txns:
        if t.amount is None:
            raise ReportError("E_MISSING", f"{NAME}: transaction on {t.when} has no amount")
''']
MONEY_BAD = ['_q', '_r2', '_cents']
MONEY_BAD_DEF = {
 '_q': '''

def _q(x):
    """Round to cents."""
    return Decimal(x).quantize(Decimal("0.01"))
''',
 '_r2': '''

def _r2(x):
    """Round to cents."""
    return Decimal(str(round(x, 2)))
''',
 '_cents': '''

def _cents(x):
    """Round to cents for display and storage."""
    return Decimal(f"{x:.2f}")
'''}

N = 120
kinds = [FAMILIES[i % len(FAMILIES)] for i in range(N)]
R.shuffle(kinds)
viol_idx = R.sample(range(N), 12)
viol = {}
for j, idx in enumerate(viol_idx):
    viol[idx] = ("money", "date", "error")[j % 3], (j // 3) % 3
names = []
for side in ("ref", "task"):
    base = os.path.join(OUT, side)
    shutil.rmtree(base, ignore_errors=True)
    for p, s in CORE.items(): w(os.path.join(base, p), s)
    w(os.path.join(base, "CONVENTIONS.md"), CONV)
    w(os.path.join(base, "reports/__init__.py"), "")
R2 = random.Random(11)
for i in range(N):
    R.seed(1000 + i)
    title, body = kinds[i](i)
    name = f"r{i+1:03d}_{kinds[i].__name__}"
    names.append(name)
    d = doc(title, R.choice(["Small differences matter because people compare months side by side.",
                             "Several people read this number, so it has to be explainable.",
                             "It was asked for after a surprise bill one winter.",
                             "It replaced a spreadsheet that drifted out of date."]))
    head = HEAD.format(name=name)
    for side in ("ref", "task"):
        money, select, val, extra = "round_cents", SELECT_OK, VAL_OK, ""
        if side == "task" and i in viol:
            kind, v = viol[i]
            if kind == "money": money = MONEY_BAD[v]; extra = MONEY_BAD_DEF[money]
            if kind == "date": select = SELECT_BAD[v]
            if kind == "error": val = VAL_BAD[v]
        src = d + "\n" + head + select + val + extra + body.replace("{MONEY}", money).replace("{{MONEY}}", money)
        w(os.path.join(OUT, side, "reports", name + ".py"), src)
json.dump({"modules": names, "violations": {names[k]: f"{viol[k][0]}#{viol[k][1]}" for k in viol}}, open(os.path.join(OUT, "answer.json"), "w"), indent=1)
w(os.path.join(OUT, "task", "tests", "__init__.py"), "")
w(os.path.join(OUT, "task", "tests", "test_core.py"), '''import unittest
from datetime import date
from decimal import Decimal as D
from core.dates import in_period, month_bounds
from core.money import round_cents


class Core(unittest.TestCase):
    def test_round(self):
        self.assertEqual(round_cents(D("0.125")), D("0.13"))

    def test_bounds(self):
        s, e = month_bounds(2026, 12)
        self.assertTrue(in_period(date(2026, 12, 31), s, e))
        self.assertFalse(in_period(e, s, e))


if __name__ == "__main__":
    unittest.main()
''')
print(len(names), "modules; violations:", {names[k]: viol[k] for k in viol})
