import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal as D

from ledger import store
from ledger.cli import main
from ledger.models import Txn
from ledger.report import pace


class BudgetStore(unittest.TestCase):
    def test_set_and_reload_budget(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 11, 3), D("-20"), "bus"))
            store.set_budget(p, 2026, 11, D("100"))
            self.assertEqual(store.load(p), [Txn(date(2026, 11, 3), D("-20"), "bus")])
            self.assertEqual(store.load_budgets(p), {"2026-11": D("100")})

    def test_add_preserves_budgets(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.set_budget(p, 2026, 12, D("50"))
            store.add(p, Txn(date(2026, 12, 1), D("-10")))
            self.assertEqual(store.load_budgets(p), {"2026-12": D("50")})
            self.assertEqual(len(store.load(p)), 1)

    def test_remove_budget(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 11, 1), D("-5")))
            store.set_budget(p, 2026, 11, D("100"))
            store.set_budget(p, 2026, 11, D("0"))
            self.assertEqual(store.load_budgets(p), {})

    def test_no_budget_file_stays_legacy_list_format(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 1), D("7")))
            with open(p) as f:
                self.assertIsInstance(json.load(f), list)

    def test_legacy_list_format_still_loads(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            with open(p, "w") as f:
                json.dump([{"when": "2026-01-01", "amount": "-3.50"}], f)
            self.assertEqual(store.load(p), [Txn(date(2026, 1, 1), D("-3.50"))])
            self.assertEqual(store.load_budgets(p), {})


class Pace(unittest.TestCase):
    def test_mid_month_projection(self):
        ts = [Txn(date(2026, 11, 5), D("-30"))]
        p = pace(ts, 2026, 11, D("100"), today=date(2026, 11, 10))
        self.assertEqual((p["spend"], p["projected"], p["remaining"], p["days_used"], p["days_total"]),
                         (D("30"), D("90"), D("70"), 10, 30))
        self.assertEqual(p["status"], "ok")

    def test_pace_over_budget_is_warning(self):
        ts = [Txn(date(2026, 11, 5), D("-30"))]
        p = pace(ts, 2026, 11, D("80"), today=date(2026, 11, 10))
        self.assertEqual(p["projected"], D("90"))
        self.assertEqual(p["status"], "warning")

    def test_spend_above_limit_is_over(self):
        ts = [Txn(date(2026, 11, 5), D("-120"))]
        p = pace(ts, 2026, 11, D("100"), today=date(2026, 11, 10))
        self.assertEqual(p["status"], "over")
        self.assertEqual(p["remaining"], D("-20"))

    def test_completed_month_projects_actual_spend(self):
        ts = [Txn(date(2026, 11, 20), D("-40"))]
        p = pace(ts, 2026, 11, D("100"), today=date(2026, 12, 1))
        self.assertEqual((p["projected"], p["days_used"]), (D("40"), 30))
        self.assertEqual(p["status"], "ok")

    def test_no_limit(self):
        ts = [Txn(date(2026, 11, 2), D("-15"))]
        p = pace(ts, 2026, 11, None, today=date(2026, 11, 10))
        self.assertEqual(p["status"], "no budget")
        self.assertIsNone(p["limit"])
        self.assertEqual(p["projected"], D("45"))

    def test_future_month(self):
        p = pace([Txn(date(2026, 12, 31), D("-500"))], 2027, 1, D("100"), today=date(2026, 12, 15))
        self.assertEqual((p["spend"], p["projected"], p["days_used"], p["status"]),
                         (D("0"), D("0"), 0, "ok"))

    def test_income_does_not_count_as_spend(self):
        ts = [Txn(date(2026, 11, 3), D("500")), Txn(date(2026, 11, 4), D("-10"))]
        p = pace(ts, 2026, 11, D("20"), today=date(2026, 11, 10))
        self.assertEqual(p["spend"], D("10"))
        self.assertEqual(p["status"], "warning")  # 10 in 10 days projects 30 > 20


class Cli(unittest.TestCase):
    def test_check_with_saved_budget(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(["--file", p, "add", "2026-11-05", "-60", "--note", "rent"]), 0)
                self.assertEqual(main(["--file", p, "budget", "2026", "11", "100"]), 0)
                rc = main(["--file", p, "check", "2026", "11", "--today", "2026-11-20"])
            self.assertEqual(rc, 0)
            self.assertIn("spent 60.00", out.getvalue())
            self.assertIn("projected month-end: 90.00", out.getvalue())

    def test_check_over_budget_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            main(["--file", p, "add", "2026-11-05", "-60"])
            out = io.StringIO()
            with redirect_stdout(out):
                rc = main(["--file", p, "check", "2026", "11", "--limit", "50", "--today", "2026-11-10"])
            self.assertEqual(rc, 1)
            self.assertIn("OVER budget by 10.00", out.getvalue())

    def test_check_defaults_to_current_month(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            today = date.today()
            main(["--file", p, "add", today.isoformat(), "-10"])
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(["--file", p, "check"]), 0)
            self.assertIn(f"{today.year:04d}-{today.month:02d}", out.getvalue())
            self.assertIn("no budget set", out.getvalue())

    def test_budgets_listing(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            main(["--file", p, "budget", "2026", "11", "100"])
            main(["--file", p, "budget", "2026", "12", "200"])
            out = io.StringIO()
            with redirect_stdout(out):
                main(["--file", p, "budgets"])
            self.assertIn("2026-11", out.getvalue())
            self.assertIn("2026-12", out.getvalue())

    def test_negative_budget_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            self.assertEqual(main(["--file", p, "budget", "2026", "11", "-5"]), 2)


if __name__ == "__main__":
    unittest.main()
