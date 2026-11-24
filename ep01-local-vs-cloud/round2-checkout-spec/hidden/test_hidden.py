import unittest
from decimal import Decimal as D
from shop.checkout import checkout

class Hidden(unittest.TestCase):
    def test_merge_first_price_wins(self):
        r = checkout([("a", "2.00", 1), ("b", "1.00", 1), ("a", "9.99", 2)], [])
        self.assertEqual(r["goods"], D("7.00"))
    def test_both_percent_use_larger(self):
        r = checkout([("a", "100.00", 1)], ["SAVE10", "save20"])
        self.assertEqual(r["goods"], D("80.00"))
    def test_flat5_floor(self):
        r = checkout([("a", "3.00", 1)], ["FLAT5"])
        self.assertEqual(r["goods"], D("0.00")); self.assertEqual(r["discount"], D("3.00"))
        self.assertEqual(r["shipping"], D("7.50")); self.assertEqual(r["total"], D("8.63"))
    def test_order_bogo_percent_flat(self):
        r = checkout([("a", "10.00", 2), ("b", "50.00", 1)], ["FLAT5", "BOGO:a", "SAVE10"])
        # (10 + 50) * 0.9 - 5 = 49 -> below 50, shipping applies
        self.assertEqual(r["goods"], D("49.00")); self.assertEqual(r["shipping"], D("7.50"))
    def test_whitespace_dupes_and_prefix_case(self):
        r = checkout([("Ab", "5.00", 4)], ["  bogo:Ab ", "BOGO:Ab", " flat5"])
        self.assertEqual(r["goods"], D("5.00"))
    def test_bogo_sku_case_sensitive(self):
        r = checkout([("ab", "5.00", 2)], ["BOGO:AB"])
        self.assertEqual(r["goods"], D("10.00"))
    def test_full_precision_then_round(self):
        r = checkout([("a", "0.335", 3)], ["FREESHIP"])
        # goods 1.005 -> 1.01 ; tax 0.15075 -> 0.15 ; total 1.16
        self.assertEqual(r["goods"], D("1.01")); self.assertEqual(r["tax"], D("0.15")); self.assertEqual(r["total"], D("1.16"))
    def test_empty_cart(self):
        r = checkout([], [])
        self.assertEqual(r["shipping"], D("0.00")); self.assertEqual(r["total"], D("0.00"))
    def test_exactly_50_free_ship(self):
        r = checkout([("a", "25.00", 2)], [])
        self.assertEqual(r["shipping"], D("0.00")); self.assertEqual(r["total"], D("57.50"))
    def test_unknown_code_original_text(self):
        with self.assertRaises(ValueError) as cm:
            checkout([("a", "1.00", 1)], ["  Save15 "])
        self.assertIn("Save15", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
