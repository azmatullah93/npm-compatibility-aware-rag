"""Offline integrity checks for cross-version generation combination.

Everything is synthetic data; this is NOT a Gemini result.
"""
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parent/'milestone3'))
from generate_code import planned_rows
from validate_generated import combine, MODES


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.tasks=json.loads((HERE.parent/'milestone3'/'tasks.json').read_text())
        self.docs=json.loads((HERE.parent/'milestone3'/'documents.json').read_text())
        self.model='FAKE_TEST_MODEL'
        for mode in MODES:
            args=Namespace(suite='cross_version12',limit=None,retriever='bm25',
                           compatibility=mode,model=self.model,dry_run=False)
            rows=planned_rows(args,self.tasks,self.docs)
            self.assertEqual(len(rows),12)
            for i,row in enumerate(rows):
                row['code'] = f'module.exports = () => {i};'
                row['generation_response']={'provider_response_id':f'synthetic-{mode}-{i}'}
            self.write(mode,rows)

    def write(self,mode,rows):
        (self.directory/(mode+'.jsonl')).write_text(
            ''.join(json.dumps(row)+'\n' for row in rows),encoding='utf-8')

    def read(self,mode):
        return [json.loads(x) for x in (self.directory/(mode+'.jsonl')).read_text().splitlines()]

    def test_balanced_60_and_idempotent(self):
        manifest=combine(self.directory,self.model)
        self.assertEqual(sum(x['trials'] for x in manifest['methods'].values()),60)
        self.assertEqual(combine(self.directory,self.model),manifest)

    def test_missing_response_rejected(self):
        self.write('range',self.read('range')[:-1])
        with self.assertRaisesRegex(ValueError,'expected 12'):
            combine(self.directory,self.model)

    def test_wrong_version_rejected(self):
        rows=self.read('exact')
        rows[0]['target_version']='0.0.0'
        self.write('exact',rows)
        with self.assertRaisesRegex(ValueError,'wrong experiment identity'):
            combine(self.directory,self.model)

    def test_rejects_modified_combination(self):
        combine(self.directory,self.model)
        (self.directory/'all_generated.jsonl').write_text('MODIFIED')
        with self.assertRaisesRegex(ValueError,'Refusing to overwrite'):
            combine(self.directory,self.model)


if __name__=='__main__':
    unittest.main()
