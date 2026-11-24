"""Usage:
  python3 -m ledger.cli --file PATH add DATE AMOUNT [--note NOTE]
  python3 -m ledger.cli --file PATH list
  python3 -m ledger.cli --file PATH report YEAR MONTH     (prints the summary as JSON, numbers as strings)
  python3 -m ledger.cli --file PATH export YEAR MONTH     (prints that month's transactions as CSV)
"""
import argparse
import csv
import json
import sys
from datetime import date
from decimal import Decimal

from . import store
from .models import Txn
from .report import in_month, summary


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
    r.add_argument("--rates", default=None)
    e = sub.add_parser("export")
    e.add_argument("year", type=int)
    e.add_argument("month", type=int)
    args = p.parse_args(argv)

    if args.cmd == "add":
        store.add(args.file, Txn(date.fromisoformat(args.date), Decimal(args.amount), args.note, args.category, args.currency))
    elif args.cmd == "list":
        for t in store.load(args.file):
            print(t.when.isoformat(), t.amount, t.note)
    elif args.cmd == "report":
        rates = None
        if args.rates:
            with open(args.rates) as f:
                raw = json.load(f)
            rates = {k: Decimal(v) for k, v in raw.items()}
        s = summary(store.load(args.file), args.year, args.month, rates)
        out = {k: str(v) for k, v in s.items() if k != "by_category"}
        out["by_category"] = {cat: str(amt) for cat, amt in s["by_category"].items()}
        print(json.dumps(out, sort_keys=True))
    elif args.cmd == "export":
        ts = sorted(in_month(store.load(args.file), args.year, args.month), key=lambda t: t.when)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["date", "amount", "currency", "category", "note"])
        for t in ts:
            writer.writerow([t.when.isoformat(), str(t.amount), t.currency, t.category, t.note])


if __name__ == "__main__":
    main()
