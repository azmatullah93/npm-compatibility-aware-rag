"""Synthetic-file audit tests; no Gemini calls and no JS execution."""
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(ROOT/'milestone3'))
from generate_code import planned_rows
from audit_retrieval import MODES, audit


class RetrievalAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)
        self.out=self.directory/'audit.json'
        self.model='gemini-3.5-flash'
        self.tasks=json.loads((ROOT/'milestone3'/'tasks.json').read_text(encoding='utf-8'))
        self.docs=json.loads((ROOT/'milestone3'/'documents.json').read_text(encoding='utf-8'))
        for mode in MODES:
            rows=planned_rows(
                Namespace(suite='cross_version12',limit=None,retriever='bm25',
                          compatibility=mode,model=self.model,dry_run=True),
                self.tasks,self.docs)
            self.write(mode,rows)

    def write(self,mode,rows):
        (self.directory/(mode+'.jsonl')).write_text(
            ''.join(json.dumps(x)+'\n' for x in rows),encoding='utf-8')

    def rows(self,mode):
        return [json.loads(x) for x in
                (self.directory/(mode+'.jsonl')).read_text(encoding='utf-8').splitlines()]

    def test_frozen_retrieval_metrics_against_author_labels(self):
        result=audit(self.directory,self.out)
        expected={'unconstrained':(7,11,15,1),
                  'exact':(8,10,0,2),'range':(10,12,0,0)}
        for mode,(rank1,rank3,invalid,missing) in expected.items():
            with self.subTest(method=mode):
                stats=result['methods'][mode]
                self.assertEqual(stats['gold_at_1'],rank1)
                self.assertEqual(stats['gold_at_3'],rank3)
                self.assertEqual(stats['hits_outside_author_validity'],invalid)
                self.assertEqual(len(stats['tasks_missing_gold_at_3']),missing)
        self.assertEqual(result['basis'],'author_assigned_document_gold_and_version_validity')
        self.assertTrue(result['no_llm_calls'])
        self.assertEqual(audit(self.directory,self.out),result)

    def test_reject_changed_gold_or_retrieval_file(self):
        rows=self.rows('exact')
        rows[0]['retrieved_ids']=[]
        self.write('exact',rows)
        with self.assertRaisesRegex(ValueError,'does not match'):
            audit(self.directory)

    def test_reject_missing_task(self):
        self.write('range',self.rows('range')[:-1])
        with self.assertRaisesRegex(ValueError,'expected 12'):
            audit(self.directory)

    def test_reject_different_report_on_same_path(self):
        audit(self.directory,self.out)
        self.out.write_text('tampered report',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Refusing to overwrite'):
            audit(self.directory,self.out)


if __name__=='__main__':
    unittest.main()
