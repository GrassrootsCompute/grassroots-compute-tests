import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal as D

from ledger import store
from ledger.models import Txn
from ledger.report import summary


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


if __name__ == "__main__":
    unittest.main()
