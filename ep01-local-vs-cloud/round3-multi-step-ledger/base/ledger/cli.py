"""Usage:
  python3 -m ledger.cli --file PATH add DATE AMOUNT [--note NOTE]
  python3 -m ledger.cli --file PATH list
  python3 -m ledger.cli --file PATH report YEAR MONTH     (prints the summary as JSON, numbers as strings)
"""
import argparse
import json
from datetime import date
from decimal import Decimal

from . import store
from .models import Txn
from .report import summary


def main(argv=None):
    p = argparse.ArgumentParser(prog="ledger")
    p.add_argument("--file", required=True)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("date")
    a.add_argument("amount")
    a.add_argument("--note", default="")
    sub.add_parser("list")
    r = sub.add_parser("report")
    r.add_argument("year", type=int)
    r.add_argument("month", type=int)
    args = p.parse_args(argv)

    if args.cmd == "add":
        store.add(args.file, Txn(date.fromisoformat(args.date), Decimal(args.amount), args.note))
    elif args.cmd == "list":
        for t in store.load(args.file):
            print(t.when.isoformat(), t.amount, t.note)
    elif args.cmd == "report":
        s = summary(store.load(args.file), args.year, args.month)
        print(json.dumps({k: str(v) for k, v in s.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
