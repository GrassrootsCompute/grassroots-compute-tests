"""Usage:
  python3 -m ledger.cli --file PATH add DATE AMOUNT [--note NOTE] [--category NAME] [--currency CODE]
  python3 -m ledger.cli --file PATH list
  python3 -m ledger.cli --file PATH report YEAR MONTH [--rates PATH]   (prints the summary as JSON, numbers as strings)
  python3 -m ledger.cli --file PATH export YEAR MONTH                   (prints that month's transactions as CSV to stdout)

  --rates PATH is a JSON file like {"USD": "1.70"}: 1 unit of that currency = that many XBS.
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
    r.add_argument("--rates", help="path to a JSON file of exchange rates, e.g. {\"USD\": \"1.70\"}")
    e = sub.add_parser("export")
    e.add_argument("year", type=int)
    e.add_argument("month", type=int)
    args = p.parse_args(argv)

    if args.cmd == "add":
        store.add(
            args.file,
            Txn(date.fromisoformat(args.date), Decimal(args.amount), args.note, args.category, args.currency),
        )
    elif args.cmd == "list":
        for t in store.load(args.file):
            print(t.when.isoformat(), t.amount, t.note)
    elif args.cmd == "report":
        rates = None
        if args.rates:
            with open(args.rates) as f:
                rates = {code: Decimal(v) for code, v in json.load(f).items()}
        s = summary(store.load(args.file), args.year, args.month, rates)
        print(json.dumps({k: str(v) if not isinstance(v, dict) else {ck: str(cv) for ck, cv in v.items()} for k, v in s.items()}, sort_keys=True))
    elif args.cmd == "export":
        ts = sorted(in_month(store.load(args.file), args.year, args.month), key=lambda t: t.when)
        w = csv.writer(sys.stdout, lineterminator="\n")
        w.writerow(["date", "amount", "currency", "category", "note"])
        for t in ts:
            w.writerow([t.when.isoformat(), str(t.amount), t.currency, t.category, t.note])


if __name__ == "__main__":
    main()
