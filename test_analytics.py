import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analytics import prepare, pipeline_sql, safe_csv


class AnalyticsTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([dict(funder='Test', program='Pilot', type='Foundation', status='Qualified', amount=1000, fit_score=80, deadline='2026-11-08')])

    def test_score_and_sql(self):
        df, issues = prepare(self.frame(), '2026-10-29')
        self.assertEqual(len(issues), 0)
        self.assertEqual(df.days_left[0], 10)
        self.assertAlmostEqual(df.priority[0], 81.8)
        self.assertEqual(pipeline_sql(df).potential_amount[0], 1000)

    def test_duplicates_excluded(self):
        df, issues = prepare(pd.concat([self.frame(), self.frame()]), '2026-10-29')
        self.assertEqual(df.eligible_for_metrics.sum(), 0)
        self.assertEqual(len(issues), 2)

    def test_unknown_values_not_zero(self):
        raw = self.frame().assign(amount='unknown', fit_score=101, deadline='bad')
        df, issues = prepare(raw, '2026-10-29')
        self.assertTrue(df.amount.isna().all())
        self.assertTrue(df.priority.isna().all())
        self.assertEqual(df.next_action[0], 'Verify deadline')
        self.assertEqual(len(issues), 3)
        self.assertTrue(pd.isna(pipeline_sql(df).potential_amount[0]))

    def test_closed_and_overdue_not_ranked(self):
        for raw in [self.frame().assign(status='Awarded'), self.frame().assign(deadline='2026-10-28')]:
            df, _ = prepare(raw, '2026-10-29')
            self.assertTrue(df.priority.isna().all())

    def test_schema_and_export(self):
        with self.assertRaises(ValueError):
            prepare(pd.DataFrame(), '2026-10-29')
        self.assertIn(b"'=HYPERLINK", safe_csv(pd.DataFrame({'name':['=HYPERLINK()']})))
