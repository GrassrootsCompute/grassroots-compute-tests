import json
from datetime import date
from decimal import Decimal
from .models import Txn

def _txn(d):
    return Txn(date.fromisoformat(d["when"]), Decimal(d["amount"]), d.get("note", ""), d.get("category", "uncategorized"), d.get("currency", "XBS"))

def _read(path):
    """Return (txns, budgets). Accepts the legacy plain-list format as well as
    {"transactions": [...], "budgets": {"YYYY-MM": "amount", ...}}."""
    try:
        with open(path) as f: data = json.load(f)
    except FileNotFoundError:
        return [], {}
    if isinstance(data, list):
        return [_txn(d) for d in data], {}
    return [_txn(d) for d in data.get("transactions", [])], {k: Decimal(v) for k, v in data.get("budgets", {}).items()}

def load(path):
    return _read(path)[0]

def load_budgets(path):
    return _read(path)[1]

def save(path, txns, budgets=None):
    budgets = budgets or {}
    rows = [{"when": t.when.isoformat(), "amount": str(t.amount), "note": t.note, "category": t.category, "currency": t.currency} for t in txns]
    # Keep the old plain-list format while there are no budgets, so files stay
    # byte-for-byte compatible with earlier versions of the tool.
    data = {"transactions": rows, "budgets": {k: str(v) for k, v in budgets.items()}} if budgets else rows
    with open(path, "w") as f:
        json.dump(data, f, indent=1)

def add(path, txn):
    txns, budgets = _read(path)
    txns.append(txn)
    save(path, txns, budgets)

def budget_key(year, month):
    return f"{year:04d}-{month:02d}"

def set_budget(path, year, month, amount):
    """Set a monthly spend limit; amount <= 0 removes it."""
    txns, budgets = _read(path)
    key = budget_key(year, month)
    if amount > 0:
        budgets[key] = amount
    else:
        budgets.pop(key, None)
    save(path, txns, budgets)
