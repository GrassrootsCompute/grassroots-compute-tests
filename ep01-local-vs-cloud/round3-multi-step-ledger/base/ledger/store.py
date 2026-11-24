import json
from datetime import date
from decimal import Decimal

from .models import Txn


def load(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    return [Txn(date.fromisoformat(d["when"]), Decimal(d["amount"]), d.get("note", "")) for d in data]


def save(path, txns):
    with open(path, "w") as f:
        json.dump([{"when": t.when.isoformat(), "amount": str(t.amount), "note": t.note} for t in txns], f, indent=1)


def add(path, txn):
    txns = load(path)
    txns.append(txn)
    save(path, txns)
