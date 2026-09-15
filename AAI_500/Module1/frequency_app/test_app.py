import math
import unittest
from app import analyze, csv_columns, parse_numbers, parse_data, box_summary, pasted_table, compare_groups


class StatisticsTests(unittest.TestCase):
    def test_group_comparison_shared_bins_and_missing(self):
        table = pasted_table('income education race 16 10 B 18 7 B 32 16 H NA 12 H 120 18 W')
        result = compare_groups(table, 0, 2, ['B', 'H'], 4)
        self.assertEqual([g['summary']['n'] for g in result['groups']], [2, 1])
        self.assertEqual([g['summary']['mean'] for g in result['groups']], [17, 32])
        self.assertEqual(result['groups'][1]['missing'], 1)
        self.assertEqual(result['overall']['n'], 3)
        self.assertEqual(result['overall']['maximum'], 32)
        for group in result['groups']:
            rows = group['summary']['rows']
            self.assertEqual([(r['lower'], r['upper']) for r in rows],
                             [(r['lower'], r['upper']) for r in result['overall']['rows']])
            self.assertAlmostEqual(sum(r['relative'] for r in rows), 1)
            self.assertEqual(sum(r['frequency'] for r in rows), group['summary']['n'])
        education = compare_groups(table, 1, 2, ['B', 'H'])
        self.assertEqual(education['groups'][0]['summary']['mean'], 8.5)
        for selected in [['B'], ['B', 'unknown']]:
            with self.assertRaises(ValueError):
                compare_groups(table, 0, 2, selected)

    def test_income_education_race_table(self):
        raw = '''&#x20; income education race
        16 10 B 18 7 B 26 9 B 16 11 B 34 14 B 22 12 B 42 16 B 42 16 B
        16 9 B 20 10 B 66 16 B 26 12 B 20 10 B 30 15 B 20 10 B 30 19 B
        32 16 H 16 11 H 20 10 H 58 16 H 30 12 H 26 10 H 20 8 H
        40 12 H 32 10 H 22 11 H 20 10 H 56 14 H 32 12 H 30 11 H
        30 14 W 48 14 W 40 7 W 84 18 W 50 10 W 38 12 W 30 12 W
        76 16 W 48 16 W 36 11 W 40 11 W 44 12 W 30 10 W 60 15 W
        24 9 W 88 17 W 46 16 W 50 16 W 50 14 W 22 11 W 26 12 W
        46 16 W 22 9 W 24 9 W 64 14 W 62 16 W 24 10 W 50 13 W
        32 10 W 34 16 W 52 18 W 24 12 W 22 14 W 20 13 W 30 14 W
        24 13 W 120 18 W 22 10 W 82 16 W 18 12 W 26 12 W 104 14 W
        28 12 W 32 12 W 38 14 W 44 12 W 22 12 W 18 10 W 24 12 W 56 20 W &#x20;'''
        for text in [raw, ' '.join(raw.split())]:
            table = pasted_table(text)
            self.assertEqual(table['headers'], ['income', 'education', 'race'])
            self.assertEqual(table['numeric'], [0, 1])
            self.assertEqual(len(table['rows']), 80)
            self.assertEqual([sum(row[2] == group for row in table['rows']) for group in ['B', 'H', 'W']], [16, 14, 50])
            self.assertEqual(max(float(row[0]) for row in table['rows']), 120)
            self.assertEqual(max(float(row[1]) for row in table['rows']), 20)

    def test_table_validation_and_legacy_detection(self):
        self.assertIsNone(pasted_table('Nation CO2 Albania 2.0 Australia 15.4'))
        self.assertIsNone(pasted_table('1 2 3 4'))
        for text in ['income education race 16 10 B 18 7',
                     'income education race 16 10 B oops 7 H',
                     'income education race 16 10 B inf 7 H']:
            with self.assertRaises(ValueError):
                pasted_table(text)
        table = pasted_table('income education race 16 10 B NA 7 H')
        self.assertEqual(table['numeric'], [0, 1])
        self.assertEqual(table['rows'][1], ['NA', '7', 'H'])

    def test_five_number_summary(self):
        for values, expected in [([1, 2, 3, 4, 5], [1, 1.5, 3, 4.5, 5]),
                                 ([1, 2, 3, 4, 5, 6], [1, 2, 3.5, 5, 6]),
                                 ([7], [7, 7, 7, 7, 7]),
                                 ([2, 4], [2, 2, 3, 4, 4])]:
            summary = box_summary(list(reversed(values)))
            self.assertEqual([summary[k] for k in ('minimum', 'q1', 'median', 'q3', 'maximum')], expected)

    def test_boxplot_outliers_and_whiskers(self):
        summary = box_summary([1, 2, 3, 4, 5, 6, 7, 100])
        self.assertEqual(summary['iqr'], 4)
        self.assertEqual(summary['lower_whisker'], 1)
        self.assertEqual(summary['upper_whisker'], 7)
        self.assertEqual(summary['outliers'], [100])
        summary = box_summary([1, 1, 1, 1, 1, 1, 9])
        self.assertEqual(summary['iqr'], 0)
        self.assertEqual(summary['upper_whisker'], 1)
        self.assertEqual(summary['outliers'], [9])
        self.assertEqual(box_summary([3, 3, 3])['outliers'], [])

    def test_clean_histogram_boundaries(self):
        result = analyze([2.0, 5.9, 8.3, 15.4, 16.5], 7)
        edges = [r['lower'] for r in result['rows']] + [result['rows'][-1]['upper']]
        self.assertEqual(edges, [0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5])
        self.assertEqual(sum(r['frequency'] for r in result['rows']), 5)
        self.assertEqual(analyze([0, 2.5, 5], 2)['rows'][1]['frequency'], 2)

    def test_clean_bins_small_values_and_zero_crossing(self):
        for values, bins in [([0.1, 0.2, 0.3], 4), ([-3.7, 8.2], 1),
                             ([-8.2, -3.7], 5), ([-0.3, 0.3], 10)]:
            rows = analyze(values, bins)['rows']
            self.assertEqual(len(rows), bins)
            self.assertLessEqual(rows[0]['lower'], min(values))
            self.assertGreaterEqual(rows[-1]['upper'], max(values))
            self.assertEqual(sum(r['frequency'] for r in rows), len(values))
            width = rows[0]['upper'] - rows[0]['lower']
            for row in rows:
                self.assertAlmostEqual(row['upper'] - row['lower'], width)

    def test_nation_co2_paste(self):
        raw = '''Nation CO2 Albania 2.0 Australia 15.4 Austria 6.9 Belgium 8.3
        Bosnia 6.2 Bulgaria 5.9 Canada 15.1 Croatia 4.0 Cyprus 5.3 Czech 9.2
        Denmark 5.9 Finland 8.7 France 4.6 Germany 8.9 Greece 6.2 Hungary 4.3
        Ireland 7.3 Italy 5.3 Latvia 3.5 Lithuania 4.4 Malta 5.4 Montenegro 3.6
        Netherlands 9.9 NewZealand 7.7 Norway 9.3 Portugal 4.3 Romania 3.5
        Serbia 5.3 Slovak 5.7 Slovenia 6.2 Spain 5.0 Sweden 4.5
        Switzerland 4.3 UK 6.5 US 16.5'''
        for text in [raw, ' '.join(raw.split())]:
            values, labeled = parse_data(text)
            self.assertTrue(labeled)
            self.assertEqual(len(values), 35)
            self.assertEqual(values[:3], [2.0, 15.4, 6.9])
            self.assertEqual(values[-1], 16.5)
            result = analyze(values)
            self.assertEqual(result['median'], 5.9)
            self.assertAlmostEqual(sum(values), 235.1)

    def test_labeled_variants(self):
        for text in ['Nation,CO2\nNew Zealand,7.7\nUnited States,16.5',
                     'New Zealand\t7.7\nUnited States\t16.5',
                     'New Zealand;7.7;United States;16.5']:
            self.assertEqual(parse_data(text), ([7.7, 16.5], True))
        self.assertEqual(parse_data('Group Value A -2.5 B +3 C 4e2'),
                         ([-2.5, 3, 400], True))
        self.assertEqual(parse_data('1, 2;3'), ([1, 2, 3], False))

    def test_labeled_invalid_input(self):
        for text in ['Nation CO2', 'A NaN', 'A inf', 'A 2 B',
                     'A 2 3', 'A 2.3.4', '1 oops 2']:
            with self.assertRaises(ValueError, msg=text):
                parse_data(text)

    def test_known_statistics_and_boundary_assignment(self):
        result = analyze([1, 2, 3, 4, 5], 2)
        self.assertEqual(result['mean'], 3)
        self.assertEqual(result['median'], 3)
        self.assertAlmostEqual(result['sample_sd'], math.sqrt(2.5))
        self.assertAlmostEqual(result['population_sd'], math.sqrt(2))
        self.assertEqual([r['frequency'] for r in result['rows']], [2, 3])
        self.assertEqual(result['rows'][-1]['cumulative'], 5)
        self.assertAlmostEqual(sum(r['relative'] for r in result['rows']), 1)

    def test_single_and_constant(self):
        self.assertIsNone(analyze([7])['sample_sd'])
        self.assertEqual(analyze([7])['population_sd'], 0)
        self.assertEqual(analyze([7, 7], 10)['rows'][0]['frequency'], 2)

    def test_negative_decimal_and_empty_bins(self):
        result = analyze([-1.5, 0, 0, 1.5], 6)
        self.assertEqual(result['median'], 0)
        self.assertEqual(sum(r['frequency'] for r in result['rows']), 4)
        self.assertTrue(any(r['frequency'] == 0 for r in result['rows']))

    def test_input_validation(self):
        self.assertEqual(parse_numbers('1, 2;\n-3.5 4e2'), [1, 2, -3.5, 400])
        for raw in ['', ',;', 'NaN', 'inf', 'one']:
            with self.assertRaises(ValueError):
                parse_numbers(raw)
        for bins in [0, 101, 1.5, True]:
            with self.assertRaises(ValueError):
                analyze([1, 2], bins)

    def test_csv_exclusions_and_no_header(self):
        columns = csv_columns('Name,Score\nA,12\nB,\nC,no\nD,18\n')
        self.assertEqual(columns[1]['values'], [12, 18])
        self.assertEqual(columns[1]['missing'], 1)
        self.assertEqual(columns[1]['invalid'], 1)
        self.assertEqual(csv_columns('1;2\n3;4', False)[1]['values'], [2, 4])


if __name__ == '__main__':
    unittest.main()
