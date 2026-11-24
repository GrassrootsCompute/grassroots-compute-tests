import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal as D

from ledger import cli, store
from ledger.models import Txn


def run_export(path, year, month):
    out = io.StringIO()
    with redirect_stdout(out):
        cli.main(["--file", path, "export", str(year), str(month)])
    return out.getvalue()


class Export(unittest.TestCase):
    def test_basic_export(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 2, 10), D("-5.00"), "lunch", "food", "XBS"))
            store.add(p, Txn(date(2026, 2, 5), D("10"), "salary", "income", "USD"))
            csv_text = run_export(p, 2026, 2)
            expected = (
                "date,amount,currency,category,note\n"
                "2026-02-05,10,USD,income,salary\n"
                "2026-02-10,-5.00,XBS,food,lunch\n"
            )
            self.assertEqual(csv_text, expected)
            self.assertNotIn("\r", csv_text)

    def test_sorts_by_date_ties_keep_stored_order(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 2, 3), D("1"), "second-in-store", "a", "XBS"))
            store.add(p, Txn(date(2026, 2, 1), D("2"), "earlier-date", "b", "XBS"))
            store.add(p, Txn(date(2026, 2, 3), D("3"), "third-in-store", "c", "XBS"))
            csv_text = run_export(p, 2026, 2)
            notes = [line.split(",")[4] for line in csv_text.splitlines()[1:]]
            self.assertEqual(notes, ["earlier-date", "second-in-store", "third-in-store"])

    def test_quotes_and_commas_in_note(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 2, 1), D("1"), 'he said "hi, there"', "misc", "XBS"))
            csv_text = run_export(p, 2026, 2)
            expected = (
                "date,amount,currency,category,note\n"
                '2026-02-01,1,XBS,misc,"he said ""hi, there"""\n'
            )
            self.assertEqual(csv_text, expected)

    def test_amount_is_original_currency_not_converted(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 2, 1), D("100"), "", "travel", "USD"))
            csv_text = run_export(p, 2026, 2)
            self.assertIn("100,USD", csv_text)
            self.assertNotIn("170", csv_text)

    def test_only_that_month_is_exported(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 2, 1), D("1"), "feb", "a", "XBS"))
            store.add(p, Txn(date(2026, 3, 1), D("2"), "march", "b", "XBS"))
            csv_text = run_export(p, 2026, 2)
            self.assertIn("feb", csv_text)
            self.assertNotIn("march", csv_text)


if __name__ == "__main__":
    unittest.main()
