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


class Currency(unittest.TestCase):
    def test_currency_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 4, 2), D("100"), "hotel", "travel", "USD"))
            self.assertEqual(store.load(p), [Txn(date(2026, 4, 2), D("100"), "hotel", "travel", "USD")])
            with open(p) as f:
                self.assertEqual(json.load(f)[0]["currency"], "USD")

    def test_default_currency_is_xbs(self):
        self.assertEqual(Txn(date(2026, 1, 1), D("10")).currency, "XBS")

    def test_load_older_file_without_currency(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            with open(p, "w") as f:
                json.dump([{"when": "2025-06-01", "amount": "50.00", "note": "legacy", "category": "fun"}], f)
            self.assertEqual(store.load(p), [Txn(date(2025, 6, 1), D("50.00"), "legacy", "fun", "XBS")])

    def test_conversion_to_xbs(self):
        rates = {"USD": D("1.70")}
        ts = [
            Txn(date(2026, 5, 1), D("100"), "pay", "income", "USD"),
            Txn(date(2026, 5, 2), D("-50"), "coffee", "food", "XBS"),
        ]
        s = summary(ts, 2026, 5, rates)
        self.assertEqual((s["income"], s["spend"], s["net"]), (D("170"), D("50"), D("120")))
        self.assertEqual(s["by_category"], {"income": D("170.00"), "food": D("-50.00")})

    def test_xbs_rate_1_even_if_missing(self):
        s = summary([Txn(date(2026, 5, 1), D("25"), "", "misc", "XBS")], 2026, 5, {})
        self.assertEqual(s["net"], D("25"))
        s = summary([Txn(date(2026, 5, 1), D("25"))], 2026, 5, None)
        self.assertEqual(s["net"], D("25"))

    def test_missing_rate_raises(self):
        ts = [Txn(date(2026, 5, 1), D("10"), "", "misc", "EUR")]
        with self.assertRaises(ValueError) as cm:
            summary(ts, 2026, 5, {"USD": D("1.70")})
        self.assertIn("EUR", str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            summary(ts, 2026, 5)
        self.assertIn("EUR", str(cm.exception))

    def test_full_precision_until_final_rounding(self):
        # Each 0.005 would round to 0.01 individually (half-up), but summing first gives 0.010 -> 0.01.
        ts = [Txn(date(2026, 5, 1), D("0.005")), Txn(date(2026, 5, 2), D("0.005"))]
        s = summary(ts, 2026, 5)
        self.assertEqual(s["income"], D("0.01"))

    def test_half_up_rounding(self):
        s = summary([Txn(date(2026, 5, 1), D("1.005"))], 2026, 5)
        self.assertEqual(s["income"], D("1.01"))  # half-up, not half-even (1.00)

    def test_net_is_rounded_income_minus_rounded_spend(self):
        # Raw net = 0.001 -> would be 0.00; derived from rounded income/spend it is 0.01.
        ts = [Txn(date(2026, 5, 1), D("1.005")), Txn(date(2026, 5, 2), D("-1.004"))]
        s = summary(ts, 2026, 5)
        self.assertEqual((s["income"], s["spend"], s["net"]), (D("1.01"), D("1.00"), D("0.01")))
        self.assertEqual(s["net"], s["income"] - s["spend"])

    def test_cli_add_currency_and_report_with_rates(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            rp = os.path.join(d, "rates.json")
            with open(rp, "w") as f:
                json.dump({"USD": "1.70"}, f)
            cli.main(["--file", p, "add", "2026-06-01", "100", "--currency", "USD", "--category", "travel"])
            cli.main(["--file", p, "add", "2026-06-02", "-12.34"])
            out = io.StringIO()
            with redirect_stdout(out):
                cli.main(["--file", p, "report", "2026", "6", "--rates", rp])
            s = json.loads(out.getvalue())
            self.assertEqual(s["income"], "170.00")
            self.assertEqual(s["by_category"], {"travel": "170.00", "uncategorized": "-12.34"})

    def test_cli_report_without_rates_is_fine_for_xbs(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            cli.main(["--file", p, "add", "2026-07-01", "42"])
            out = io.StringIO()
            with redirect_stdout(out):
                cli.main(["--file", p, "report", "2026", "7"])
            s = json.loads(out.getvalue())
            self.assertEqual(s["net"], "42.00")


if __name__ == "__main__":
    unittest.main()
