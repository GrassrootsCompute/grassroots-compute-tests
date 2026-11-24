import unittest
from datetime import date
from decimal import Decimal as D

from ledger.models import Txn
from ledger.report import summary


class MonthBoundary(unittest.TestCase):
    def test_first_day_of_next_month_is_excluded(self):
        # Regression: `report 2026 2` used to include a transaction dated 2026-03-01.
        ts = [Txn(date(2026, 2, 15), D("-10")), Txn(date(2026, 3, 1), D("-999"))]
        s = summary(ts, 2026, 2)
        self.assertEqual((s["spend"], s["net"], s["count"]), (D("10.00"), D("-10.00"), 1))

    def test_first_day_of_current_month_is_included(self):
        s = summary([Txn(date(2026, 2, 1), D("5"))], 2026, 2)
        self.assertEqual((s["income"], s["count"]), (D("5.00"), 1))

    def test_december_rollover_to_january(self):
        ts = [Txn(date(2026, 12, 31), D("-20")), Txn(date(2027, 1, 1), D("-999"))]
        s = summary(ts, 2026, 12)
        self.assertEqual((s["spend"], s["net"], s["count"]), (D("20.00"), D("-20.00"), 1))
        # The Jan 1 transaction belongs to the January 2027 report instead.
        s = summary(ts, 2027, 1)
        self.assertEqual((s["spend"], s["count"]), (D("999.00"), 1))

    def test_by_category_respects_boundary(self):
        ts = [Txn(date(2026, 2, 20), D("-5"), "", "food"), Txn(date(2026, 3, 1), D("-7"), "", "food")]
        self.assertEqual(summary(ts, 2026, 2)["by_category"], {"food": D("-5.00")})


if __name__ == "__main__":
    unittest.main()
