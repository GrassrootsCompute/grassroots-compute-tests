import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal as D

from ledger import store
from ledger.cli import main
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


class CategoryModel(unittest.TestCase):
    def test_default_category(self):
        t = Txn(date(2026, 1, 1), D("10"))
        self.assertEqual(t.category, "uncategorized")

    def test_explicit_category(self):
        t = Txn(date(2026, 1, 1), D("10"), "note", "food")
        self.assertEqual(t.category, "food")


class CategoryStore(unittest.TestCase):
    def test_roundtrip_with_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("-12.50"), "lunch", "food"))
            self.assertEqual(store.load(p)[0].category, "food")

    def test_load_old_file_no_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "old.json")
            with open(p, "w") as f:
                json.dump([{"when": "2026-01-05", "amount": "-12.50", "note": "lunch"}], f)
            self.assertEqual(store.load(p)[0].category, "uncategorized")


class CategoryReport(unittest.TestCase):
    def test_by_category_in_summary(self):
        ts = [
            Txn(date(2026, 1, 1), D("100"), "", "salary"),
            Txn(date(2026, 1, 9), D("-30"), "", "food"),
            Txn(date(2026, 1, 15), D("-20"), "", "food"),
        ]
        s = summary(ts, 2026, 1)
        self.assertIn("by_category", s)
        self.assertEqual(s["by_category"]["salary"], D("100"))
        self.assertEqual(s["by_category"]["food"], D("-50"))

    def test_by_category_default_key(self):
        ts = [Txn(date(2026, 1, 1), D("50"))]
        s = summary(ts, 2026, 1)
        self.assertEqual(s["by_category"]["uncategorized"], D("50"))

    def test_by_category_only_in_month(self):
        ts = [
            Txn(date(2026, 1, 1), D("40"), "", "food"),
            Txn(date(2026, 2, 15), D("10"), "", "food"),  # clearly outside January
        ]
        s = summary(ts, 2026, 1)
        self.assertEqual(s["by_category"]["food"], D("40"))


class CategoryCLI(unittest.TestCase):
    def test_add_with_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            main(["--file", p, "add", "2026-01-05", "100", "--category", "salary"])
            self.assertEqual(store.load(p)[0].category, "salary")

    def test_add_default_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            main(["--file", p, "add", "2026-01-05", "100"])
            self.assertEqual(store.load(p)[0].category, "uncategorized")

    def test_report_includes_by_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            main(["--file", p, "add", "2026-01-05", "100", "--category", "salary"])
            main(["--file", p, "add", "2026-01-10", "-40", "--category", "food"])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main(["--file", p, "report", "2026", "1"])
            result = json.loads(buf.getvalue())
            self.assertIn("by_category", result)
            self.assertEqual(result["by_category"]["salary"], "100.00")
            self.assertEqual(result["by_category"]["food"], "-40.00")


class CurrencyModel(unittest.TestCase):
    def test_default_currency(self):
        t = Txn(date(2026, 1, 1), D("10"))
        self.assertEqual(t.currency, "XBS")

    def test_explicit_currency(self):
        t = Txn(date(2026, 1, 1), D("10"), "", "food", "USD")
        self.assertEqual(t.currency, "USD")


class CurrencyStore(unittest.TestCase):
    def test_roundtrip_with_currency(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("100"), "", "salary", "USD"))
            self.assertEqual(store.load(p)[0].currency, "USD")

    def test_load_old_file_no_currency(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "old.json")
            with open(p, "w") as f:
                json.dump([{"when": "2026-01-05", "amount": "100", "note": ""}], f)
            self.assertEqual(store.load(p)[0].currency, "XBS")


class CurrencyReport(unittest.TestCase):
    def test_xbs_only_no_rates_needed(self):
        ts = [Txn(date(2026, 1, 1), D("100")), Txn(date(2026, 1, 2), D("-40"))]
        s = summary(ts, 2026, 1)
        self.assertEqual(s["income"], D("100.00"))
        self.assertEqual(s["spend"], D("40.00"))
        self.assertEqual(s["net"], D("60.00"))

    def test_foreign_currency_converted(self):
        # 50 USD × 1.70 = 85.00 XBS
        rates = {"USD": D("1.70")}
        ts = [Txn(date(2026, 1, 1), D("50"), "", "uncategorized", "USD")]
        s = summary(ts, 2026, 1, rates)
        self.assertEqual(s["income"], D("85.00"))

    def test_xbs_always_rate_1(self):
        # XBS is never looked up in rates, even if rates is {}
        ts = [Txn(date(2026, 1, 1), D("10"))]
        s = summary(ts, 2026, 1, {})
        self.assertEqual(s["income"], D("10.00"))

    def test_missing_rate_raises_value_error(self):
        ts = [Txn(date(2026, 1, 1), D("100"), "", "uncategorized", "USD")]
        with self.assertRaises(ValueError) as ctx:
            summary(ts, 2026, 1, {})
        self.assertIn("USD", str(ctx.exception))

    def test_no_rates_with_foreign_currency_raises_value_error(self):
        ts = [Txn(date(2026, 1, 1), D("100"), "", "uncategorized", "GBP")]
        with self.assertRaises(ValueError) as ctx:
            summary(ts, 2026, 1)
        self.assertIn("GBP", str(ctx.exception))

    def test_rounding_to_cents(self):
        # 1 USD × 1.333 = 1.333 XBS → rounds to 1.33
        rates = {"USD": D("1.333")}
        ts = [Txn(date(2026, 1, 1), D("1"), "", "uncategorized", "USD")]
        s = summary(ts, 2026, 1, rates)
        self.assertEqual(s["income"], D("1.33"))

    def test_net_equals_rounded_income_minus_rounded_spend(self):
        # 2 USD income × 0.666 = 1.332 XBS → rounds to 1.33
        # 1 USD spend × 0.666 = 0.666 XBS → rounds to 0.67
        # net = 1.33 - 0.67 = 0.66  (not round(1.332 - 0.666) = round(0.666) = 0.67)
        rates = {"USD": D("0.666")}
        ts = [
            Txn(date(2026, 1, 1), D("2"), "", "income", "USD"),
            Txn(date(2026, 1, 2), D("-1"), "", "food", "USD"),
        ]
        s = summary(ts, 2026, 1, rates)
        self.assertEqual(s["income"], D("1.33"))
        self.assertEqual(s["spend"], D("0.67"))
        self.assertEqual(s["net"], D("0.66"))

    def test_by_category_converted_and_rounded(self):
        rates = {"USD": D("1.70")}
        ts = [
            Txn(date(2026, 1, 1), D("100"), "", "salary", "USD"),
            Txn(date(2026, 1, 2), D("-10"), "", "food", "USD"),
        ]
        s = summary(ts, 2026, 1, rates)
        self.assertEqual(s["by_category"]["salary"], D("170.00"))
        self.assertEqual(s["by_category"]["food"], D("-17.00"))


class CurrencyCLI(unittest.TestCase):
    def test_add_with_currency(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            main(["--file", p, "add", "2026-01-05", "100", "--currency", "USD"])
            self.assertEqual(store.load(p)[0].currency, "USD")

    def test_add_default_currency(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            main(["--file", p, "add", "2026-01-05", "100"])
            self.assertEqual(store.load(p)[0].currency, "XBS")

    def test_report_with_rates_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            rf = os.path.join(d, "rates.json")
            with open(rf, "w") as f:
                json.dump({"USD": "1.70"}, f)
            main(["--file", p, "add", "2026-01-05", "100", "--currency", "USD"])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main(["--file", p, "report", "2026", "1", "--rates", rf])
            result = json.loads(buf.getvalue())
            # 100 USD × 1.70 = 170.00 XBS
            self.assertEqual(result["income"], "170.00")
            self.assertEqual(result["by_category"]["uncategorized"], "170.00")


class BoundaryRegression(unittest.TestCase):
    def test_first_of_next_month_excluded_feb_march(self):
        # Regression: 2026-03-01 must NOT appear in report 2026 2
        ts = [Txn(date(2026, 2, 28), D("10")), Txn(date(2026, 3, 1), D("99"))]
        s = summary(ts, 2026, 2)
        self.assertEqual(s["count"], 1)
        self.assertEqual(s["income"], D("10.00"))

    def test_first_of_next_month_excluded_dec_jan(self):
        # Regression: 2027-01-01 must NOT appear in report 2026 12
        ts = [Txn(date(2026, 12, 31), D("10")), Txn(date(2027, 1, 1), D("99"))]
        s = summary(ts, 2026, 12)
        self.assertEqual(s["count"], 1)
        self.assertEqual(s["income"], D("10.00"))

    def test_last_day_of_month_included(self):
        ts = [Txn(date(2026, 2, 28), D("5"))]
        s = summary(ts, 2026, 2)
        self.assertEqual(s["count"], 1)

    def test_first_day_of_month_included(self):
        ts = [Txn(date(2026, 2, 1), D("5"))]
        s = summary(ts, 2026, 2)
        self.assertEqual(s["count"], 1)


class ExportCLI(unittest.TestCase):
    def _export(self, path, year, month):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(["--file", path, "export", str(year), str(month)])
        return buf.getvalue()

    def test_header(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            out = self._export(p, 2026, 1)
            self.assertEqual(out.splitlines()[0], "date,amount,currency,category,note")

    def test_basic_row(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("-12.50"), "lunch", "food", "XBS"))
            lines = self._export(p, 2026, 1).splitlines()
            self.assertEqual(lines[1], "2026-01-05,-12.50,XBS,food,lunch")

    def test_sorted_by_date(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 15), D("20"), "", "food"))
            store.add(p, Txn(date(2026, 1, 5), D("10"), "", "income"))
            lines = self._export(p, 2026, 1).splitlines()
            self.assertEqual(lines[1].split(",")[0], "2026-01-05")
            self.assertEqual(lines[2].split(",")[0], "2026-01-15")

    def test_stable_sort_ties_keep_stored_order(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("10"), "first", "a"))
            store.add(p, Txn(date(2026, 1, 5), D("20"), "second", "b"))
            lines = self._export(p, 2026, 1).splitlines()
            self.assertIn("first", lines[1])
            self.assertIn("second", lines[2])

    def test_only_in_month(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("10")))
            store.add(p, Txn(date(2026, 2, 5), D("20")))
            lines = self._export(p, 2026, 1).splitlines()
            self.assertEqual(len(lines), 2)  # header + 1 row

    def test_original_currency_not_converted(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("100"), "", "salary", "USD"))
            lines = self._export(p, 2026, 1).splitlines()
            fields = lines[1].split(",")
            self.assertEqual(fields[1], "100")     # original amount
            self.assertEqual(fields[2], "USD")     # original currency

    def test_note_with_comma_quoted(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("10"), "eggs, bread", "food"))
            lines = self._export(p, 2026, 1).splitlines()
            self.assertEqual(lines[1], '2026-01-05,10,XBS,food,"eggs, bread"')

    def test_note_with_double_quote_escaped(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("10"), 'say "hi"', "misc"))
            lines = self._export(p, 2026, 1).splitlines()
            self.assertEqual(lines[1], '2026-01-05,10,XBS,misc,"say ""hi"""')

    def test_lf_line_endings(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            store.add(p, Txn(date(2026, 1, 5), D("10")))
            out = self._export(p, 2026, 1)
            self.assertNotIn("\r", out)

    def test_empty_month_header_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            out = self._export(p, 2026, 1)
            self.assertEqual(out.strip(), "date,amount,currency,category,note")


if __name__ == "__main__":
    unittest.main()
