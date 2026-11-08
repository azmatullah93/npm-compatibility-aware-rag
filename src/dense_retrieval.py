"""Dense *latent-semantic-analysis* retrieval baseline.

NOT a pretrained neural encoder: this fits a TF-IDF + truncated-SVD semantic
vector space on the experimental document corpus. Fully offline and deterministic.
"""
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

class LSARetriever:
    def __init__(self, documents, dimensions=16):
        self.documents = list(documents)
        self.vectorizer = TfidfVectorizer(
            lowercase=True, token_pattern=r'(?u)\b\w+\b',
            ngram_range=(1,2), sublinear_tf=True
        )
        x = self.vectorizer.fit_transform([d['text'] for d in self.documents])
        n = min(dimensions, min(x.shape)-1)
        if n < 1:
            raise ValueError('LSA requires at least 2 documents and features')
        self.svd = TruncatedSVD(n_components=n, random_state=0)
        self.embeddings = normalize(self.svd.fit_transform(x))

    def rank(self, query, pool=None):
        query_bow = self.vectorizer.transform([query])
        query_embedding = normalize(self.svd.transform(query_bow))[0]
        scores = self.embeddings @ query_embedding
        indices = range(len(self.documents)) if pool is None else pool
        return sorted(
            [(self.documents[i], float(scores[i])) for i in indices],
            key=lambda pair: (-pair[1], pair[0]['id'])
        )
