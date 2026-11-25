import unittest
from solution import sliding_median


class T(unittest.TestCase):
    def test_cases(self):
        cases = [
            ([1, 3, -1, -3, 5, 3, 6, 7], 3, [1, -1, -1, 3, 5, 6]),
            ([1, 2, 3, 4], 2, [1.5, 2.5, 3.5]),
            ([5], 1, [5]),
            ([], 1, []),
            ([1, 2], 3, []),
            ([2, 2, 2], 2, [2, 2]),
            ([1, 4], 2, [2.5]),
            ([1, 2, 3, 4], 4, [2.5]),
            ([-1, -2, -3, -4], 2, [-1.5, -2.5, -3.5]),
        ]
        for n, k, want in cases:
            with self.subTest(n=n, k=k):
                self.assertEqual(sliding_median(n, k), want)

    def test_errors(self):
        for n, k in [([1, 2, 3], 0), ([], 0)]:
            with self.subTest(n=n, k=k):
                with self.assertRaises(ValueError):
                    sliding_median(n, k)


if __name__ == '__main__':
    unittest.main()
