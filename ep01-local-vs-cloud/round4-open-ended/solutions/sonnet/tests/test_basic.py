import io
import json
import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal as D
from unittest.mock import patch

from ledger import store
from ledger.models import Txn
from ledger.report import summary, budget_status
from ledger.cli import main


class Basic(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("-12.50"), "lunch"))
            self.assertEqual(store.load(p), [Txn(date(2026, 1, 5), D("-12.50"), "lunch")])

    def test_summary(self):
        ts = [Txn(date(2026, 1, 1), D("100")), Txn(date(2026, 1, 9), D("-30.25"))]
        s = summary(ts, 2026, 1)
        self.assertEqual((s["income"], s["spend"], s["net"], s["count"]), (D("100"), D("30.25"), D("69.75"), 2))


class BudgetStore(unittest.TestCase):
    def test_set_and_load_budgets(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.set_budget(p, "groceries", D("400"))
            store.set_budget(p, "dining", D("100"))
            budgets = store.load_budgets(p)
            self.assertEqual(budgets["groceries"], D("400"))
            self.assertEqual(budgets["dining"], D("100"))

    def test_budgets_preserved_on_add(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.set_budget(p, "groceries", D("400"))
            store.add(p, Txn(date(2026, 1, 5), D("-12.50"), "lunch", "groceries"))
            self.assertEqual(store.load_budgets(p)["groceries"], D("400"))
            self.assertEqual(len(store.load(p)), 1)

    def test_txns_preserved_on_set_budget(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("-12.50"), "lunch", "groceries"))
            store.set_budget(p, "groceries", D("400"))
            self.assertEqual(len(store.load(p)), 1)

    def test_backward_compat_old_flat_list(self):
        """Old flat-array JSON files load correctly with empty budgets."""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            with open(p, "w") as f:
                json.dump([{"when": "2026-01-05", "amount": "-12.50", "note": "lunch",
                            "category": "groceries", "currency": "XBS"}], f)
            txns = store.load(p)
            budgets = store.load_budgets(p)
            self.assertEqual(len(txns), 1)
            self.assertEqual(txns[0].category, "groceries")
            self.assertEqual(budgets, {})


class BudgetStatus(unittest.TestCase):
    def _txn(self, day, amount, cat="groceries"):
        return Txn(date(2026, 11, day), D(str(amount)), "", cat)

    def test_on_pace(self):
        # Day 15 of 30, spent $90. Projected = 90/15*30 = $180. Budget $400. On pace.
        txns = [self._txn(1, "-50"), self._txn(10, "-40")]
        st = budget_status(txns, {"groceries": D("400")}, 2026, 11, today=date(2026, 11, 15))
        row = st["categories"][0]
        self.assertEqual(row["spent"], D("90.00"))
        self.assertEqual(row["projected"], D("180.00"))
        self.assertTrue(row["on_pace"])

    def test_over_pace(self):
        # Day 15 of 30, spent $300. Projected = $600. Budget $200. Over pace.
        txns = [self._txn(1, "-200"), self._txn(10, "-100")]
        st = budget_status(txns, {"groceries": D("200")}, 2026, 11, today=date(2026, 11, 15))
        row = st["categories"][0]
        self.assertEqual(row["spent"], D("300.00"))
        self.assertFalse(row["on_pace"])

    def test_exactly_at_budget_pace(self):
        # Spent exactly on track: 100/30*30 = 100. Budget 100. On pace (<=).
        txns = [self._txn(1, "-100")]
        st = budget_status(txns, {"groceries": D("100")}, 2026, 11, today=date(2026, 11, 30))
        self.assertTrue(st["categories"][0]["on_pace"])

    def test_unbudgeted_category(self):
        txns = [self._txn(1, "-50", "transport")]
        st = budget_status(txns, {}, 2026, 11, today=date(2026, 11, 15))
        row = st["categories"][0]
        self.assertIsNone(row["budget"])
        self.assertIsNone(row["on_pace"])
        self.assertIsNone(row["remaining"])

    def test_past_month_uses_full_days(self):
        # Asking about October while today is November: days_elapsed = 31 (October)
        txns = [Txn(date(2026, 10, 15), D("-100"), "", "groceries")]
        st = budget_status(txns, {"groceries": D("400")}, 2026, 10, today=date(2026, 11, 23))
        self.assertEqual(st["days_elapsed"], 31)
        self.assertEqual(st["days_in_month"], 31)

    def test_total_spend(self):
        txns = [
            self._txn(1, "-100", "groceries"),
            self._txn(2, "-50", "dining"),
            self._txn(3, "200", "groceries"),   # income, not counted in spend
        ]
        st = budget_status(txns, {}, 2026, 11, today=date(2026, 11, 15))
        self.assertEqual(st["total_spend"], D("150.00"))

    def test_budget_category_with_no_spend(self):
        # Budget set but no transactions: spent = 0, projected = 0, on pace.
        st = budget_status([], {"groceries": D("400")}, 2026, 11, today=date(2026, 11, 15))
        row = st["categories"][0]
        self.assertEqual(row["spent"], D("0.00"))
        self.assertEqual(row["projected"], D("0.00"))
        self.assertTrue(row["on_pace"])


class BudgetCLI(unittest.TestCase):
    def _run(self, argv):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            main(argv)
        return buf.getvalue()

    def test_budget_set_and_list(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            self._run(["--file", p, "budget", "set", "groceries", "400"])
            self.assertEqual(store.load_budgets(p)["groceries"], D("400"))
            out = self._run(["--file", p, "budget", "list"])
            self.assertIn("groceries", out)
            self.assertIn("400", out)

    def test_budget_set_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            self._run(["--file", p, "budget", "set", "dining", "100"])
            self._run(["--file", p, "budget", "set", "dining", "150"])
            self.assertEqual(store.load_budgets(p)["dining"], D("150"))

    def test_budget_list_empty(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            out = self._run(["--file", p, "budget", "list"])
            self.assertIn("No budgets", out)

    def test_status_shows_category_and_budget(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 11, 10), D("-50"), "shop", "groceries"))
            store.set_budget(p, "groceries", D("400"))
            out = self._run(["--file", p, "status", "2026", "11"])
            self.assertIn("groceries", out)
            self.assertIn("400.00", out)
            self.assertIn("50.00", out)

    def test_status_flags_over_pace(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            # Spent 300 by day 1 of a 30-day month → projected 9000, budget 200
            store.add(p, Txn(date(2026, 11, 1), D("-300"), "", "dining"))
            store.set_budget(p, "dining", D("200"))
            out = self._run(["--file", p, "status", "2026", "11"])
            self.assertIn("OVER", out)

    def test_status_no_budgets(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 11, 5), D("-20"), "coffee", "dining"))
            out = self._run(["--file", p, "status", "2026", "11"])
            self.assertIn("dining", out)
            # No budget column values, no warnings
            self.assertNotIn("OVER", out)

    def test_existing_commands_unaffected(self):
        """add, list, report, export still work after store format change."""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            self._run(["--file", p, "add", "2026-11-05", "-20.00", "--category", "dining", "--note", "lunch"])
            out_list = self._run(["--file", p, "list"])
            self.assertIn("2026-11-05", out_list)
            out_report = self._run(["--file", p, "report", "2026", "11"])
            data = json.loads(out_report)
            self.assertEqual(data["spend"], "20.00")


if __name__ == "__main__":
    unittest.main()
