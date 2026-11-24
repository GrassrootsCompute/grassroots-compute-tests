import unittest
from decimal import Decimal as D
from shop.cart import Cart

class CartTests(unittest.TestCase):
    def test_add_accumulates_qty(self):
        c = Cart(); c.add("a", "2.50", 2); c.add("a", "2.50", 3)
        self.assertEqual(c.subtotal(), D("12.50"))
    def test_total_with_tax_rounded(self):
        c = Cart(); c.add("a", "0.99", 3)
        self.assertEqual(c.total(), D("3.42"))
    def test_save10_lowercase(self):
        c = Cart(); c.add("a", "10.00")
        self.assertEqual(c.total("save10"), D("10.35"))
    def test_flat5_not_negative(self):
        c = Cart(); c.add("a", "3.00")
        self.assertEqual(c.total("FLAT5"), D("0.00"))
    def test_half_up_rounding(self):
        c = Cart(); c.add("a", "0.05")
        self.assertEqual(c.total(), D("0.06"))
    def test_bad_qty(self):
        with self.assertRaises(ValueError):
            Cart().add("a", "1", 0)

if __name__ == "__main__":
    unittest.main()
