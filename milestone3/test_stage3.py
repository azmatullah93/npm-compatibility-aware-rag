import unittest,sys,json
from pathlib import Path
p=Path(__file__).resolve().parent
sys.path.insert(0,str(p))
from api_compatibility import in_range,rank_for_version
from build_extended_dataset import build
root=p.parent
class TestCompatibility(unittest.TestCase):
 def test_lower_upper(self):
  self.assertTrue(in_range('5.1.0','>=5.0.0 <6.0.0'))
  self.assertFalse(in_range('4.21.2','>=5.0.0 <6.0.0'))
 def test_invalid_range_fail_closed(self):
  with self.assertRaises(ValueError):in_range('5.0.0','^5.0.0')
 def test_lower_inclusive(self):self.assertTrue(in_range('5.0.0','>=5.0.0 <6.0.0'))
 def test_build_and_stable(self):
  a,b=build();self.assertEqual((a,b),(39,42))
  docs=json.loads((p/'documents.json').read_text())
  shared=[d for d in docs if d['id'].endswith('-shared')]
  self.assertEqual(len(shared),3)
  self.assertTrue(all(len(d['valid_versions'])==2 for d in shared))
 def test_doc_integrity(self):
  build();docs=json.loads((p/'documents.json').read_text());tasks=json.loads((p/'tasks.json').read_text())
  ids={x['id'] for x in docs}
  self.assertEqual(len(ids),len(docs))
  for t in tasks:
   self.assertIn(t['correct_doc_id'],ids)
   d=next(x for x in docs if x['id']==t['correct_doc_id'])
   self.assertTrue(in_range(t['target_version'],d['valid_range']))
 def test_stable_not_exact(self):
  build();docs=json.loads((p/'documents.json').read_text());d=next(d for d in docs if d['id']=='express-basic-route-shared')
  self.assertNotEqual(d['version'],'5.1.0')
  self.assertTrue(in_range('5.1.0',d['valid_range']))
if __name__=='__main__':unittest.main()
