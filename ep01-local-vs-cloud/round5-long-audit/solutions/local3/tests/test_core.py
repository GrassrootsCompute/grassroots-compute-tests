import unittest
from datetime import date
from decimal import Decimal as D
from core.dates import in_period, month_bounds
from core.money import round_cents


class Core(unittest.TestCase):
    def test_round(self):
        self.assertEqual(round_cents(D("0.125")), D("0.13"))

    def test_bounds(self):
        s, e = month_bounds(2026, 12)
        self.assertTrue(in_period(date(2026, 12, 31), s, e))
        self.assertFalse(in_period(e, s, e))


if __name__ == "__main__":
    unittest.main()
