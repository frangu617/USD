"""Numerical checks against independent formulas and SciPy reference tests."""
import sys
from pathlib import Path
import unittest

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis import analyze, compare, mean_interval


class AnalysisTests(unittest.TestCase):
    def test_mean_interval(self):
        result = mean_interval([0, 0, 1, 1, 1, 2, 2, 3, 3, 4])
        self.assertAlmostEqual(result['Mean'], 1.7)
        # Sum of squared observations = 45; centered sum = 45 - 10 * 1.7**2.
        margin = 2.262157162854 * np.sqrt((45 - 10 * 1.7 ** 2) / 90)
        self.assertAlmostEqual(result['CI lower'], 1.7 - margin)
        self.assertAlmostEqual(result['CI upper'], 1.7 + margin)

    def test_welch_reference(self):
        a, b = [2, 3, 5, 7], [1, 2, 2, 3, 4]
        result = compare(a, b)
        reference = stats.ttest_ind(a, b, equal_var=False)
        self.assertAlmostEqual(result['t'], reference.statistic)
        self.assertAlmostEqual(result['p-value (two-sided)'], reference.pvalue)
        self.assertAlmostEqual((result['CI lower'] + result['CI upper']) / 2, np.mean(a) - np.mean(b))

    def test_simulation_precision(self):
        result = analyze({'mode': 'precision', 'seed': 42})
        self.assertLess(abs(result['rows'][1]['SD'] - .1), .002)
        self.assertGreater(result['rows'][0]['SD'], .1)

    def test_polls_and_likelihood(self):
        likelihood = analyze({'mode': 'likelihood'})
        self.assertEqual(likelihood['rows'][0]['MLE p'], 1 / 3)
        polls = analyze({'mode': 'polls'})['rows']
        self.assertAlmostEqual(polls[0]['z'], 1.8)
        self.assertEqual(polls[0]['Posterior alpha'], 109)
        self.assertEqual(polls[1]['Posterior beta'], 525)

    def test_ai_exact_starter_sequence(self):
        result = analyze({'mode': 'ai'})
        frame = result['tables'][-1]['rows']
        np.random.seed(2024)
        sentiment = np.random.choice(['Positive', 'Neutral', 'Negative'], 300, p=[.44, .33, .23])
        gender = np.random.choice(['Male', 'Female', 'Other'], 300, p=[.49, .48, .03])
        self.assertEqual([r['sentiment'] for r in frame], sentiment.tolist())
        self.assertEqual([r['gender'] for r in frame], gender.tolist())
        self.assertEqual(sum(sum(v for k, v in row.items() if k != 'Sentiment') for row in result['tables'][0]['rows']), 300)

    def test_all_csv_exercises_and_invalid_input(self):
        raw = 'measurement,group\n1,0\n2,0\n4,0\n4,1\n6,1\n8,1\nbad,1\n'
        for mode in ['students_mean', 'students_compare', 'houses', 'ideology', 'sheep']:
            with self.subTest(mode=mode):
                result = analyze({'mode': mode, 'csv': raw, 'value': 'measurement', 'group': 'group', 'a': '1', 'b': '0'})
                self.assertTrue(result['rows'])
        with self.assertRaises(ValueError):
            analyze({'mode': 'houses'})
        with self.assertRaises(ValueError):
            compare([1], [2, 3])


if __name__ == '__main__':
    unittest.main()
