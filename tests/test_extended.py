"""Tests added for LSA and isolated actual-library probe source readiness."""
import json,unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from dense_retrieval import LSARetriever
from retrieval import retrieve

class ExtendedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=json.loads((ROOT/'data'/'documents.json').read_text())
        cls.tasks=json.loads((ROOT/'data'/'tasks.json').read_text())
        cls.model=LSARetriever(cls.docs)
    def test_lsa_returns_ranked_documents(self):
        t=self.tasks[0]
        assert len(retrieve(self.model,t['query'],t['package'],t['target_version'],'bm25',3))==3
    def test_lsa_version_gate_never_returns_incompatible(self):
        for t in self.tasks:
            hits=retrieve(self.model,t['query'],t['package'],t['target_version'],'version_aware',3)
            self.assertTrue(all(t['target_version'] in d['valid_versions'] for d,_ in hits))
    def test_lsa_abstains_for_unseen_version(self):
        r=retrieve(self.model,'catch-all route','express','5.99.0','version_aware',3)
        self.assertEqual(r,[])
    def test_node_probe_is_real_module_loader(self):
        source=(ROOT/'execution'/'npm_version_probes.cjs').read_text()
        self.assertIn("createRequire",source)
        self.assertIn("npm",source)
        self.assertNotIn("mock",source.lower().split('*/')[-1])

if __name__=='__main__': unittest.main()
