"""Offline unit tests for evidence bundle validation and non-overwriting output."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import archive_pilot_evidence as evidence


class EvidenceArchiveTests(unittest.TestCase):
    def test_jsonl_missing_trailing_newline_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'rows.jsonl'
            path.write_text('{"a": 1}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'trailing newline'):
                evidence.read_jsonl(path)

    def test_jsonl_object_rows_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'rows.jsonl'
            path.write_text('{"a": 1}\n',encoding='utf-8')
            self.assertEqual(evidence.read_jsonl(path),[{'a':1}])
            path.write_text('1\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Non-object'):
                evidence.read_jsonl(path)

    def test_archive_does_not_overwrite_previous_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'evidence.zip'
            with patch.object(evidence,'validate',return_value={'test_only':True}):
                with patch.object(evidence,'BASE',['milestone3/tasks.json']):
                    saved=evidence.archive(file)
                    self.assertEqual(saved['included_files'],1)
                    before=file.read_bytes()
                    with zipfile.ZipFile(file) as z:
                        manifest=json.loads(z.read('EVIDENCE_MANIFEST.json'))
                        self.assertTrue(manifest['test_only'])
                        self.assertIn('milestone3/tasks.json',z.namelist())
                        self.assertIn('sha256',manifest['files']['milestone3/tasks.json'])
                    with self.assertRaises(FileExistsError):
                        evidence.archive(file)
                    self.assertEqual(file.read_bytes(),before)

    def test_missing_local_evidence_rejected(self):
        with patch.object(evidence,'BASE',['__evidence_test_missing__/not_here.json']):
            with self.assertRaisesRegex(ValueError,'Missing required evidence'):
                evidence.validate()


if __name__=='__main__':
    unittest.main()
