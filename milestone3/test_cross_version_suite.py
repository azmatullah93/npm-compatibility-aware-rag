"""Offline design checks for the frozen cross_version12 benchmark suite.

These tests never call an LLM or execute untrusted generated code. Only
version-pinned Docker preflight can validate real behavioral test fixtures.
"""
import json
import unittest
from pathlib import Path

from generate_code import PILOT4, CROSS_VERSION12, EXEC_TASKS, SUITES
from api_compatibility import is_compatible, in_range

HERE = Path(__file__).resolve().parent


class CrossVersionSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = {x['id']:x for x in json.loads((HERE/'tasks.json').read_text())}
        cls.docs = {x['id']:x for x in json.loads((HERE/'documents.json').read_text())}
        cls.specs = json.loads((HERE/'execution_specs.json').read_text())

    def test_prior_pilot_membership_unchanged(self):
        self.assertEqual(PILOT4, (
            'express-wildcard-task-new','express-del-task-new',
            'mongoose-remove-task-new','mongoose-update-task-new'))
        self.assertEqual(SUITES['pilot4'],PILOT4)

    def test_12_predeclared_tasks_and_no_duplicates(self):
        self.assertEqual(len(CROSS_VERSION12),12)
        self.assertEqual(len(set(CROSS_VERSION12)),12)
        self.assertEqual(len(self.specs),12)
        self.assertEqual(set(CROSS_VERSION12),set(self.specs))
        self.assertEqual(set(CROSS_VERSION12),set(EXEC_TASKS))

    def test_package_version_matches_executable_spec(self):
        for tid in CROSS_VERSION12:
            with self.subTest(task=tid):
                task = self.tasks[tid]
                spec = self.specs[tid]
                self.assertEqual((task['package'],task['target_version']),
                                 (spec['package'],spec['version']))
                self.assertIn('solution.cjs',spec['test_js'])
                self.assertTrue(spec['test_js'].strip())

    def test_both_major_versions_and_stable_examples(self):
        suite=[self.tasks[tid] for tid in CROSS_VERSION12]
        by_pkg={}
        for t in suite:
            by_pkg.setdefault(t['package'],set()).add(t['target_version'])
        self.assertEqual(by_pkg['express'],{'4.21.2','5.1.0'})
        self.assertEqual(by_pkg['mongoose'],{'6.13.8','7.8.7'})
        self.assertEqual(sum(t['task_type']=='stable_cross_version' for t in suite),4)

    def test_cross_version_evidence_favors_range_when_version_tag_differs(self):
        # Distinguishing cases in the CURRENT AUTHOR-PARAPHRASED pilot corpus.
        # This is only a retrieval-metadata property, not an empirical LLM result.
        for docid,target in [
            ('express-basic-route-shared','5.1.0'),
            ('mongoose-findbyid-shared','7.8.7')]:
            with self.subTest(doc=docid):
                doc=self.docs[docid]
                self.assertFalse(is_compatible(doc,target,'exact'))
                self.assertTrue(is_compatible(doc,target,'range'))
                self.assertTrue(in_range(target,doc['valid_range']))
                self.assertIn(target,doc['valid_versions'])


if __name__ == '__main__':
    unittest.main()
