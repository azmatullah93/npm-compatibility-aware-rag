"""Pure validation tests; these fixtures are NOT actual model experiments."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize_execution import summarize


class SummaryTests(unittest.TestCase):
    def test_valid_paired_results(self):
        rows = [
            dict(model='test-model', method=m, task_id=t, status=s)
            for m, outcomes in [('none', [('a','FAIL'),('b','PASS')]),
                                ('compatible', [('a','PASS'),('b','PASS')])]
            for t,s in outcomes
        ]
        summary=summarize(rows)
        self.assertEqual([x['pass_at_1'] for x in summary], [1.0, 0.5])

    def test_reject_staged_as_executed(self):
        with self.assertRaises(ValueError):
            summarize([dict(model='m',method='x',task_id='a',status='STAGED_NOT_EXECUTED')])

    def test_reject_missing_task_in_comparison(self):
        with self.assertRaises(ValueError):
            summarize([dict(model='m',method='x',task_id='a',status='PASS'),
                       dict(model='m',method='y',task_id='b',status='PASS')])

    def test_reject_duplicate_trials(self):
        rows=[dict(model='m',method='x',task_id='a',status='PASS')]*2
        with self.assertRaises(ValueError):
            summarize(rows)

if __name__ == '__main__':
    unittest.main()
