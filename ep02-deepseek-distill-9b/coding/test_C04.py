import unittest
from solution import merge_intervals


class T(unittest.TestCase):
    def test_cases(self):
        cases = [
            ([], 0, []),
            ([[1, 3], [2, 6], [8, 10], [15, 18]], 0, [[1, 6], [8, 10], [15, 18]]),
            ([[1, 4], [4, 5]], 0, [[1, 5]]),
            ([[1, 2], [3, 4]], 0, [[1, 2], [3, 4]]),
            ([[1, 2], [3, 4]], 1, [[1, 4]]),
            ([[5, 1], [2, 3]], 0, [[2, 3]]),
            ([[8, 10], [1, 3], [2, 6]], 0, [[1, 6], [8, 10]]),
            ([[1, 10], [2, 3], [4, 5]], 0, [[1, 10]]),
            ([[1, 2], [4, 5], [7, 8]], 2, [[1, 8]]),
            ([[3, 2]], 0, []),
        ]
        for iv, g, want in cases:
            with self.subTest(iv=iv, g=g):
                self.assertEqual(merge_intervals(iv, g), want)

    def test_no_mutation(self):
        x = [[5, 6], [1, 2]]
        merge_intervals(x)
        self.assertEqual(x, [[5, 6], [1, 2]])

if __name__ == '__main__':
    unittest.main()
