"""Offline regression for safe, exact-prefix LLM generation resumption.

All API calls are patched. No real network traffic or model tokens are used.
"""
import json
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_code


class GenerationResumeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / 'responses.jsonl'

    def args(self, **options):
        base = dict(suite='pilot4', limit=2, retriever='bm25', compatibility='none',
                    model='TEST_MODEL_ONLY', api_url='http://unreachable.invalid',
                    dry_run=False, output=str(self.output), resume=True, overwrite=False)
        base.update(options)
        return Namespace(**base)

    def read_rows(self):
        return [json.loads(x) for x in self.output.read_text().splitlines() if x.strip()]

    @patch.dict(os.environ, {'OPENAI_API_KEY':'FAKE_LOCAL_TEST_KEY'})
    def test_interrupted_call_preserves_first_and_resumes_exactly_once(self):
        calls = [0]
        def interrupted(prompt, model, url, key):
            calls[0] += 1
            if calls[0] == 2:
                raise TimeoutError('Synthetic upstream interruption')
            return 'module.exports = () => 1;', {'provider_response_id':'synthetic-one'}
        with patch.object(generate_code, 'openai_chat', side_effect=interrupted):
            with self.assertRaises(TimeoutError):
                generate_code.run(self.args())
        self.assertEqual(len(self.read_rows()),1)
        first = self.read_rows()[0]
        with patch.object(generate_code, 'openai_chat',
                          return_value=('module.exports = () => 2;', {'provider_response_id':'synthetic-two'})) as mock:
            generate_code.run(self.args())
        mock.assert_called_once()
        rows = self.read_rows()
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0],first)
        self.assertNotEqual(rows[0]['task_id'],rows[1]['task_id'])
        self.assertEqual(rows[1]['generation_response']['provider_response_id'],'synthetic-two')
        with patch.object(generate_code,'openai_chat') as mock:
            generate_code.run(self.args())
        mock.assert_not_called()
        self.assertEqual(self.read_rows(),rows)

    @patch.dict(os.environ, {'OPENAI_API_KEY':'FAKE_LOCAL_TEST_KEY'})
    def test_refuses_mismatched_method_without_calls(self):
        with patch.object(generate_code,'openai_chat',
                          return_value=('module.exports = () => 1;',{})):
            generate_code.run(self.args(limit=1))
        with patch.object(generate_code,'openai_chat') as mock:
            with self.assertRaisesRegex(ValueError, 'Resume mismatch'):
                generate_code.run(self.args(compatibility='exact'))
        mock.assert_not_called()
        self.assertEqual(len(self.read_rows()),1)

    @patch.dict(os.environ, {'OPENAI_API_KEY':'FAKE_LOCAL_TEST_KEY'})
    def test_default_never_overwrites_existing_results(self):
        with patch.object(generate_code,'openai_chat',
                          return_value=('module.exports = () => 1;',{})):
            generate_code.run(self.args(limit=1))
        before = self.output.read_bytes()
        with patch.object(generate_code,'openai_chat') as mock:
            with self.assertRaises(FileExistsError):
                generate_code.run(self.args(limit=1,resume=False))
        mock.assert_not_called()
        self.assertEqual(self.output.read_bytes(),before)

    def test_rejects_corrupted_jsonl(self):
        self.output.write_text('{"task_id":\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Corrupt JSONL'):
            generate_code.run(self.args())

    def test_dry_run_requires_no_key(self):
        with patch.dict(os.environ, {}, clear=True):
            generate_code.run(self.args(limit=2,dry_run=True))
        rows=self.read_rows()
        self.assertEqual(len(rows),2)
        self.assertTrue(all(row['provider']=='prompt_only' for row in rows))
        self.assertTrue(all('code' not in row for row in rows))


if __name__ == '__main__':
    unittest.main()
