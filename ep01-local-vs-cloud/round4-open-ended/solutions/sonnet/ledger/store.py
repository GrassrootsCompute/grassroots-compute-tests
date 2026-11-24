import json
from datetime import date
from decimal import Decimal
from .models import Txn


def _load_raw(path):
    """Returns (list-of-txn-dicts, budgets-dict-of-str). Handles old flat-list format."""
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        return [], {}
    if isinstance(data, list):
        return data, {}
    return data.get("txns", []), data.get("budgets", {})


def _txn_from_dict(d):
    return Txn(
        date.fromisoformat(d["when"]),
        Decimal(d["amount"]),
        d.get("note", ""),
        d.get("category", "uncategorized"),
        d.get("currency", "XBS"),
    )


def load(path):
    raw, _ = _load_raw(path)
    return [_txn_from_dict(d) for d in raw]


def load_budgets(path):
    _, raw = _load_raw(path)
    return {k: Decimal(v) for k, v in raw.items()}


def save(path, txns, budgets=None):
    if budgets is None:
        budgets = load_budgets(path)
    with open(path, "w") as f:
        json.dump(
            {
                "txns": [
                    {
                        "when": t.when.isoformat(),
                        "amount": str(t.amount),
                        "note": t.note,
                        "category": t.category,
                        "currency": t.currency,
                    }
                    for t in txns
                ],
                "budgets": {k: str(v) for k, v in budgets.items()},
            },
            f,
            indent=1,
        )


def add(path, txn):
    txns = load(path)
    budgets = load_budgets(path)
    txns.append(txn)
    save(path, txns, budgets)


def set_budget(path, category, amount):
    txns = load(path)
    budgets = load_budgets(path)
    budgets[category] = amount
    save(path, txns, budgets)
