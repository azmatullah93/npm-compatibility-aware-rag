import json,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from retrieval import BM25,compatible,retrieve
from metadata import resolve_version

class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=json.loads((root/'data'/'documents.json').read_text())
        cls.tasks=json.loads((root/'data'/'tasks.json').read_text())
        cls.model=BM25(cls.docs)

    def test_dataset_size(self):
        self.assertEqual(len(self.docs),36)
        self.assertEqual(len(self.tasks),36)
    def test_gold_in_corpus(self):
        mapping={d['id']:d for d in self.docs}
        for t in self.tasks:
            self.assertIn(t['correct_doc_id'],mapping)
            self.assertTrue(compatible(mapping[t['correct_doc_id']],t['target_version']))
    def test_wrong_version_always_rejected(self):
        for task in self.tasks:
            ret=retrieve(self.model,task['query'],task['package'],task['target_version'],'version_aware',k=5)
            self.assertTrue(ret)
            self.assertTrue(all(compatible(d,task['target_version']) for d,_ in ret))
    def test_lockfile_resolves_exact_version(self):
        self.assertEqual(resolve_version('express', {'dependencies':{'express':'^5.0.0'}},
                         {'packages':{'node_modules/express':{'version':'5.1.0'}}}), '5.1.0')

    def test_caret_without_lock_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_version('express', {'dependencies':{'express':'^5.0.0'}})

    def test_unknown_version_abstains(self):
        self.assertEqual(retrieve(self.model,'create catch all route','express','99.99.99','version_aware'),[])

if __name__=='__main__':unittest.main()
