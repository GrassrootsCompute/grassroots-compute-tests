import unittest
from solution import parse_duration


class T(unittest.TestCase):
    def test_cases(self):
        cases = [
            ("1h30m", 5400), ("2d", 172800), ("45s", 45), ("1h 5m 3s", 3903),
            ("0s", 0), ("", -1), ("30m1h", -1), ("1h1h", -1),
            ("1d2h3m4s", 93784), ("  90m ", 5400), ("1H", -1),
            ("1 h", -1),
        ]
        for s, want in cases:
            with self.subTest(s=s):
                self.assertEqual(parse_duration(s), want)


if __name__ == '__main__':
    unittest.main()
