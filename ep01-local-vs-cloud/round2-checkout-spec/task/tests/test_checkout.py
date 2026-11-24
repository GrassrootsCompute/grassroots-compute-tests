import unittest
from decimal import Decimal as D
from shop.checkout import checkout

class Visible(unittest.TestCase):
    def test_plain(self):
        r = checkout([("a", "10.00", 2)], [])
        self.assertEqual(r["goods"], D("20.00")); self.assertEqual(r["shipping"], D("7.50"))
        self.assertEqual(r["tax"], D("4.13")); self.assertEqual(r["total"], D("31.63"))
    def test_save10_freeship_threshold(self):
        r = checkout([("a", "60.00", 1)], ["save10"])
        self.assertEqual(r["goods"], D("54.00")); self.assertEqual(r["shipping"], D("0.00"))
    def test_unknown_code(self):
        with self.assertRaises(ValueError) as cm:
            checkout([("a", "1.00", 1)], ["Huh42"])
        self.assertIn("Huh42", str(cm.exception))
    def test_bogo(self):
        r = checkout([("a", "4.00", 3)], ["BOGO:a"])
        self.assertEqual(r["goods"], D("8.00")); self.assertEqual(r["discount"], D("4.00"))

if __name__ == "__main__":
    unittest.main()
