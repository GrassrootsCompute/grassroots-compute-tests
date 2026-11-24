import os, tempfile, unittest
from datetime import date
from decimal import Decimal as D
from ledger import store
from ledger.models import Txn
from ledger.report import summary
from tests._common_hidden import cli

class H3(unittest.TestCase):
    def test_month_boundary(self):
        ts = [Txn(date(2026, 2, 28), D("-1")), Txn(date(2026, 3, 1), D("-100"))]
        s = summary(ts, 2026, 2)
        self.assertEqual((s["count"], s["spend"]), (1, D("1.00")))
    def test_december(self):
        ts = [Txn(date(2026, 12, 31), D("5")), Txn(date(2027, 1, 1), D("7"))]
        self.assertEqual(summary(ts, 2026, 12)["count"], 1)
        self.assertEqual(summary(ts, 2027, 1)["count"], 1)
    def test_export(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.save(p, [
                Txn(date(2026, 2, 14), D("-12.50"), "plain", category="food"),
                Txn(date(2026, 2, 1), D("-3.00"), "a, b"),
                Txn(date(2026, 3, 1), D("-9"), "march"),
                Txn(date(2026, 2, 1), D("10"), 'say "hi"', category="salary", currency="USD"),
            ])
            out = cli(p, "export", "2026", "2").replace("\r\n", "\n").rstrip("\n")
            self.assertEqual(out, "date,amount,currency,category,note\n"
                                  '2026-02-01,-3.00,XBS,uncategorized,"a, b"\n'
                                  '2026-02-01,10,USD,salary,"say ""hi"""\n'
                                  "2026-02-14,-12.50,XBS,food,plain")
