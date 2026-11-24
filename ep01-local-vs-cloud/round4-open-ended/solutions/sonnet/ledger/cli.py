"""Usage:
  python3 -m ledger.cli --file PATH add DATE AMOUNT [--note NOTE] [--category CAT]
  python3 -m ledger.cli --file PATH list
  python3 -m ledger.cli --file PATH report YEAR MONTH     (prints summary as JSON)
  python3 -m ledger.cli --file PATH export YEAR MONTH     (prints CSV)
  python3 -m ledger.cli --file PATH budget set CATEGORY AMOUNT
  python3 -m ledger.cli --file PATH budget list
  python3 -m ledger.cli --file PATH status [YEAR MONTH]   (mid-month pace vs budgets)
"""
import argparse
import calendar
import csv
import sys
import json
from datetime import date
from decimal import Decimal

from . import store
from .models import Txn
from .report import summary, budget_status


def _fmt(val):
    """Format a Decimal as a right-aligned dollar amount string."""
    if val is None:
        return "—"
    if val < 0:
        return f"-${abs(val):.2f}"
    return f"${val:.2f}"


def _print_status(st):
    year, month = st["year"], st["month"]
    month_name = calendar.month_name[month]
    pct = st["days_elapsed"] / st["days_in_month"] * 100
    print(f"\n{month_name} {year}  —  day {st['days_elapsed']} of {st['days_in_month']} ({pct:.0f}% through)\n")

    rows = st["categories"]
    if not rows:
        print("  No transactions this month.")
        print()
        return

    COL = 18
    header = f"{'CATEGORY':<{COL}} {'SPENT':>10} {'BUDGET':>10} {'LEFT':>10} {'PROJECTED':>10}  STATUS"
    rule = "─" * len(header)
    print(header)
    print(rule)

    warnings = []
    for row in rows:
        cat = row["category"]
        spent = _fmt(row["spent"])
        budget = _fmt(row["budget"])
        left = _fmt(row["remaining"])
        proj = _fmt(row["projected"])

        if row["on_pace"] is None:
            status_str = ""
        elif row["on_pace"]:
            status_str = "✓ ok"
        else:
            status_str = "✗ OVER"
            warnings.append(cat)

        print(f"{cat:<{COL}} {spent:>10} {budget:>10} {left:>10} {proj:>10}  {status_str}")

    print(rule)
    print(f"{'Total spend':<{COL}} {_fmt(st['total_spend']):>10}")

    if warnings:
        print(f"\n  ⚠  On track to exceed budget: {', '.join(warnings)}")
    print()


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

    bud = sub.add_parser("budget")
    bud_sub = bud.add_subparsers(dest="budget_cmd", required=True)
    bs = bud_sub.add_parser("set")
    bs.add_argument("category")
    bs.add_argument("amount")
    bud_sub.add_parser("list")

    st = sub.add_parser("status")
    st.add_argument("year", type=int, nargs="?")
    st.add_argument("month", type=int, nargs="?")
    st.add_argument("--rates")

    args = p.parse_args(argv)

    if args.cmd == "add":
        store.add(args.file, Txn(date.fromisoformat(args.date), Decimal(args.amount), args.note, args.category, args.currency))

    elif args.cmd == "list":
        for t in store.load(args.file):
            print(t.when.isoformat(), t.amount, t.note)

    elif args.cmd == "report":
        rates = {k: Decimal(v) for k, v in json.load(open(args.rates)).items()} if args.rates else None
        s = summary(store.load(args.file), args.year, args.month, rates)
        s["by_category"] = {k: str(v) for k, v in s["by_category"].items()}
        print(json.dumps({k: (v if isinstance(v, dict) else str(v)) for k, v in s.items()}, sort_keys=True))

    elif args.cmd == "export":
        from .report import in_month
        ts = sorted(in_month(store.load(args.file), args.year, args.month), key=lambda t: t.when)
        w = csv.writer(sys.stdout, lineterminator="\n")
        w.writerow(["date", "amount", "currency", "category", "note"])
        for t in ts:
            w.writerow([t.when.isoformat(), str(t.amount), t.currency, t.category, t.note])

    elif args.cmd == "budget":
        if args.budget_cmd == "set":
            store.set_budget(args.file, args.category, Decimal(args.amount))
            print(f"Budget for '{args.category}' set to {args.amount}")
        elif args.budget_cmd == "list":
            budgets = store.load_budgets(args.file)
            if not budgets:
                print("No budgets set.")
            else:
                for cat, amt in sorted(budgets.items()):
                    print(f"  {cat}: {amt:.2f}")

    elif args.cmd == "status":
        today = date.today()
        year = args.year if args.year is not None else today.year
        month = args.month if args.month is not None else today.month
        rates = {k: Decimal(v) for k, v in json.load(open(args.rates)).items()} if args.rates else None
        budgets = store.load_budgets(args.file)
        txns = store.load(args.file)
        st = budget_status(txns, budgets, year, month, today=today, rates=rates)
        _print_status(st)


if __name__ == "__main__":
    main()
