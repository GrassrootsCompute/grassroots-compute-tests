import unittest
from solution import split_bill


class T(unittest.TestCase):
    def test_cases(self):
        cases = [
            (100, [1, 1, 1], [34, 33, 33]),
            (10, [1, 2, 3], [2, 3, 5]),
            (0, [1, 2], [0, 0]),
            (5, [0, 1, 1], [0, 3, 2]),
            (1, [1, 1], [1, 0]),
            (100, [], []),
            (1000, [3, 3, 3], [334, 333, 333]),
            (2, [1, 1, 1], [1, 1, 0]),
            (100, [1, 2, 4], [14, 29, 57]),
        ]
        for t, w, want in cases:
            with self.subTest(t=t, w=w):
                got = split_bill(t, w)
                self.assertEqual(got, want)
                self.assertEqual(sum(got), t if w else 0)

    def test_errors(self):
        with self.assertRaises(ValueError):
            split_bill(100, [0, 0])
        with self.assertRaises(ValueError):
            split_bill(100, [1, -1])


if __name__ == '__main__':
    unittest.main()
