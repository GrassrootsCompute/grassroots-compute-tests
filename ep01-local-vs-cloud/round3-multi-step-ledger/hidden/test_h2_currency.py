import json, os, tempfile, unittest
from datetime import date
from decimal import Decimal as D
from ledger import store
from ledger.models import Txn
from ledger.report import summary
from tests._common_hidden import cli

d0 = date(2026, 1, 10)
class H2(unittest.TestCase):
    def test_default_currency_old_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            json.dump([{"when": "2026-01-02", "amount": "-5", "note": "old"}], open(p, "w"))
            self.assertEqual(store.load(p)[0].currency, "XBS")
            store.add(p, Txn(d0, D("3"), currency="USD", category="x"))
            t = store.load(p)[1]
            self.assertEqual((t.currency, t.category), ("USD", "x"))
    def test_conversion_and_rounding(self):
        ts = [Txn(d0, D("100"), currency="USD"), Txn(d0, D("-3.333"), category="food"), Txn(d0, D("-3.333"), category="food")]
        s = summary(ts, 2026, 1, rates={"USD": D("1.70")})
        self.assertEqual((s["income"], s["spend"], s["net"]), (D("170.00"), D("6.67"), D("163.33")))
        self.assertEqual(s["by_category"], {"food": D("-6.67"), "uncategorized": D("170.00")})
    def test_net_from_rounded_parts(self):
        s = summary([Txn(d0, D("0.005")), Txn(d0, D("-0.004"))], 2026, 1)
        self.assertEqual((s["income"], s["spend"], s["net"]), (D("0.01"), D("0.00"), D("0.01")))
    def test_missing_rate(self):
        with self.assertRaises(ValueError) as cm:
            summary([Txn(d0, D("5"), currency="JPY")], 2026, 1, rates={"USD": D("1.7")})
        self.assertIn("JPY", str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            summary([Txn(d0, D("5"), currency="USD")], 2026, 1)
        self.assertIn("USD", str(cm.exception))
    def test_xbs_without_rates(self):
        self.assertEqual(summary([Txn(d0, D("5"))], 2026, 1)["net"], D("5.00"))
    def test_cli_currency(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json"); r = os.path.join(d, "rates.json")
            json.dump({"AUD": "1.10"}, open(r, "w"))
            cli(p, "add", "2026-01-05", "10", "--currency", "AUD")
            cli(p, "add", "2026-01-06", "-2.50", "--category", "food")
            out = json.loads(cli(p, "report", "2026", "1", "--rates", r))
            self.assertEqual(D(out["net"]), D("8.50"))
            self.assertEqual(D(out["by_category"]["food"]), D("-2.50"))
