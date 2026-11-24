import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal as D

from ledger import cli, store
from ledger.models import Txn
from ledger.report import summary


class Category(unittest.TestCase):
    def test_category_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("-12.50"), "lunch", "food"))
            self.assertEqual(store.load(p), [Txn(date(2026, 1, 5), D("-12.50"), "lunch", "food")])
            with open(p) as f:
                self.assertEqual(json.load(f)[0]["category"], "food")

    def test_default_category_is_uncategorized(self):
        self.assertEqual(Txn(date(2026, 1, 1), D("10")).category, "uncategorized")

    def test_load_older_file_without_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            with open(p, "w") as f:
                json.dump([{"when": "2025-06-01", "amount": "50.00", "note": "legacy"}], f)
            self.assertEqual(store.load(p), [Txn(date(2025, 6, 1), D("50.00"), "legacy", "uncategorized")])

    def test_summary_by_category(self):
        ts = [
            Txn(date(2026, 1, 1), D("100"), "salary", "income"),
            Txn(date(2026, 1, 9), D("-30.25"), "lunch", "food"),
            Txn(date(2026, 1, 15), D("-5.00"), "snack", "food"),
            Txn(date(2026, 1, 20), D(-20), "rent", "housing"),
        ]
        s = summary(ts, 2026, 1)
        self.assertEqual(
            s["by_category"],
            {"income": D("100"), "food": D("-35.25"), "housing": D("-20")},
        )

    def test_cli_add_category_and_report(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            cli.main(["--file", p, "add", "2026-02-01", "250", "--category", "income"])
            cli.main(["--file", p, "add", "2026-02-03", "-100", "--note", "groceries", "--category", "food"])
            out = io.StringIO()
            with redirect_stdout(out):
                cli.main(["--file", p, "report", "2026", "2"])
            s = json.loads(out.getvalue())
            self.assertEqual(s["by_category"], {"income": "250.00", "food": "-100.00"})

    def test_cli_default_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            cli.main(["--file", p, "add", "2026-03-01", "42"])
            out = io.StringIO()
            with redirect_stdout(out):
                cli.main(["--file", p, "report", "2026", "3"])
            s = json.loads(out.getvalue())
            self.assertEqual(s["by_category"], {"uncategorized": "42.00"})


if __name__ == "__main__":
    unittest.main()
