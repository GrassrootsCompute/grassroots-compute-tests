"""Usage:
  python3 -m ledger.cli --file PATH add DATE AMOUNT [--note NOTE]
  python3 -m ledger.cli --file PATH list
  python3 -m ledger.cli --file PATH report YEAR MONTH     (prints the summary as JSON, numbers as strings)
  python3 -m ledger.cli --file PATH export YEAR MONTH
  python3 -m ledger.cli --file PATH budget YEAR MONTH AMOUNT   (set a monthly spend limit; AMOUNT 0 removes it)
  python3 -m ledger.cli --file PATH budgets                    (list all monthly limits)
  python3 -m ledger.cli --file PATH check [YEAR MONTH]         (spend so far vs the limit, with a pace
                                                              projection; exits 1 if already over budget)
"""
import argparse
import csv
import sys
import json
from datetime import date
from decimal import Decimal

from . import store
from .models import Txn
from .report import summary, pace


def _rates(path):
    return {k: Decimal(v) for k, v in json.load(open(path)).items()} if path else None


def _print_pace(year, month, p):
    print(f"{year:04d}-{month:02d}: spent {p['spend']} across {p['count']} transactions")
    if p["limit"] is None:
        print(f"  no budget set — project month-end spend: {p['projected']}")
        print(f"  set one with: budget {year} {month} <amount>")
    else:
        print(f"  budget {p['limit']}, {p['remaining']} left")
        print(f"  pace: {p['days_used']}/{p['days_total']} days used, projected month-end: {p['projected']}")
        if p["status"] == "over":
            print(f"  OVER budget by {p['spend'] - p['limit']}")
        elif p["status"] == "warning":
            print(f"  WARNING: current pace projects {p['projected']}, over budget by {p['projected'] - p['limit']}")
        else:
            print("  OK — on pace")


def main(argv=None):
    p = argparse.ArgumentParser(prog="ledger")
    p.add_argument("--file", required=True)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("date")
    a.add_argument("amount")
    a.add_argument("--note", default="")
    a.add_argument("--category", default="uncategorized")
    a.add_argument("--currency", default="XBS")
    sub.add_parser("list")
    r = sub.add_parser("report")
    r.add_argument("year", type=int)
    r.add_argument("month", type=int)
    r.add_argument("--rates")
    e = sub.add_parser("export")
    e.add_argument("year", type=int)
    e.add_argument("month", type=int)
    b = sub.add_parser("budget")
    b.add_argument("year", type=int)
    b.add_argument("month", type=int)
    b.add_argument("amount")
    sub.add_parser("budgets")
    c = sub.add_parser("check")
    c.add_argument("year", type=int, nargs="?")
    c.add_argument("month", type=int, nargs="?")
    c.add_argument("--limit")
    c.add_argument("--rates")
    c.add_argument("--today")
    args = p.parse_args(argv)

    if args.cmd == "add":
        store.add(args.file, Txn(date.fromisoformat(args.date), Decimal(args.amount), args.note, args.category, args.currency))
    elif args.cmd == "list":
        for t in store.load(args.file):
            print(t.when.isoformat(), t.amount, t.note)
    elif args.cmd == "report":
        s = summary(store.load(args.file), args.year, args.month, _rates(args.rates))
        s["by_category"] = {k: str(v) for k, v in s["by_category"].items()}
        print(json.dumps({k: (v if isinstance(v, dict) else str(v)) for k, v in s.items()}, sort_keys=True))
    elif args.cmd == "export":
        from .report import in_month
        ts = sorted(in_month(store.load(args.file), args.year, args.month), key=lambda t: t.when)
        w = csv.writer(sys.stdout, lineterminator="\n")
        w.writerow(["date", "amount", "currency", "category", "note"])
        for t in ts: w.writerow([t.when.isoformat(), str(t.amount), t.currency, t.category, t.note])
    elif args.cmd == "budget":
        amount = Decimal(args.amount)
        if amount < 0:
            print("budget amount must be >= 0", file=sys.stderr)
            return 2
        store.set_budget(args.file, args.year, args.month, amount)
        verb = "removed" if amount == 0 else "set"
        print(f"budget {verb} for {store.budget_key(args.year, args.month)}")
    elif args.cmd == "budgets":
        today = date.today()
        budgets = store.load_budgets(args.file)
        if not budgets:
            print("no budgets set")
            return 0
        txns = store.load(args.file)
        for key in sorted(budgets):
            y, m = (int(x) for x in key.split("-"))
            _print_pace(y, m, pace(txns, y, m, budgets[key], None, today))
    elif args.cmd == "check":
        today = date.fromisoformat(args.today) if args.today else date.today()
        year, month = args.year or today.year, args.month or today.month
        limit = Decimal(args.limit) if args.limit is not None else store.load_budgets(args.file).get(store.budget_key(year, month))
        pl = pace(store.load(args.file), year, month, limit, _rates(args.rates), today)
        _print_pace(year, month, pl)
        return 1 if pl["status"] == "over" else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
