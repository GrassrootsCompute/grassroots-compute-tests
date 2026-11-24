import json, os, tempfile, unittest
from datetime import date
from decimal import Decimal as D
from ledger import store
from ledger.models import Txn
from ledger.report import summary
from tests._common_hidden import cli

class H1(unittest.TestCase):
    def test_default_and_positional(self):
        t = Txn(date(2026, 1, 1), D("1"), "n")
        self.assertEqual(t.category, "uncategorized")
    def test_old_file_loads(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            json.dump([{"when": "2026-01-02", "amount": "-5", "note": "old"}], open(p, "w"))
            t = store.load(p)[0]
            self.assertEqual((t.category, t.amount, t.note), ("uncategorized", D("-5"), "old"))
    def test_roundtrip_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("-12.50"), "lunch", category="food"))
            self.assertEqual(store.load(p)[0].category, "food")
    def test_by_category(self):
        ts = [Txn(date(2026, 1, 3), D("-30.25"), category="food"), Txn(date(2026, 1, 4), D("-10"), category="food"),
              Txn(date(2026, 1, 5), D("100"), category="salary"), Txn(date(2026, 1, 6), D("-1"))]
        bc = summary(ts, 2026, 1)["by_category"]
        self.assertEqual(bc, {"food": D("-40.25"), "salary": D("100"), "uncategorized": D("-1")})
    def test_cli_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            cli(p, "add", "2026-01-05", "-12.50", "--note", "x", "--category", "food")
            cli(p, "add", "2026-01-06", "20", "--category", "gift")
            out = json.loads(cli(p, "report", "2026", "1"))
            self.assertEqual(D(out["by_category"]["food"]), D("-12.50"))
            self.assertEqual(D(out["by_category"]["gift"]), D("20"))
            self.assertEqual(D(out["net"]), D("7.50"))
