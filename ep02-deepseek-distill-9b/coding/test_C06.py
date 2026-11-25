import unittest
from solution import compare_versions


class T(unittest.TestCase):
    def test_cases(self):
        cases = [
            ("1.2.10", "1.2.9", 1), ("1.2", "1.2.0", 0), ("v1.0", "1.0", 0),
            ("1.0-rc1", "1.0", -1), ("1.0-alpha", "1.0-beta", -1),
            ("2.0", "10.0", -1), ("1.0.0.1", "1.0", 1),
            ("1.0-rc2", "1.0-rc10", 1), ("1.0-rc1", "1.0-rc1", 0),
            ("0.9.9", "1.0-rc1", -1), ("1.01", "1.1", 0), ("V3", "3.0.0", 0),
        ]
        for a, b, want in cases:
            with self.subTest(a=a, b=b):
                self.assertEqual(compare_versions(a, b), want)


if __name__ == '__main__':
    unittest.main()
