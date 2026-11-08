"""DocPrompting-inspired BM25 baseline and API-version compatibility stage.
No external model weights or network connection needed.
"""
import math,re
from collections import Counter


def tokens(s):
    return re.findall(r'[a-z]+|\d+',s.lower())


class BM25:
    def __init__(self, documents, k1=1.5, b=0.75):
        self.documents=list(documents)
        self.k1=k1;self.b=b
        self.words=[tokens(d['text']) for d in self.documents]
        self.counts=[Counter(w) for w in self.words]
        self.avgdl=sum(map(len,self.words))/max(1,len(self.words))
        counts=Counter(t for w in self.words for t in set(w))
        self.idf={w: math.log(1 + (len(self.words)-freq+0.5)/(freq+0.5)) for w,freq in counts.items()}

    def score(self, query, index):
        counts=self.counts[index];dl=len(self.words[index]);result=0.0
        for word in set(tokens(query)):
            freq=counts.get(word,0)
            if freq:
                result+=self.idf.get(word,0.0)*freq*(self.k1+1)/(freq+self.k1*(1-self.b+self.b*dl/self.avgdl))
        return result

    def rank(self, query, pool=None):
        indices=range(len(self.documents)) if pool is None else pool
        return sorted([(self.documents[i],self.score(query,i)) for i in indices],
                      key=lambda x:(-x[1],x[0]['id']))


def compatible(doc, target_version):
    """For the pilot, only explicitly labeled valid versions are accepted.
    We make NO unsupported inference about undocumented patch/minor ranges.
    """
    return target_version in doc.get('valid_versions',[])


def retrieve(model, query, package, target, mode, k=1):
    # Baseline gets known package name, which keeps task constraints FAIR.
    indices=[i for i,d in enumerate(model.documents) if d['package']==package]
    ranked=model.rank(query,indices)
    if mode=='bm25':
        return ranked[:k]
    if mode=='version_aware':
        valid=[pair for pair in ranked if compatible(pair[0],target)]
        return valid[:k]  # no wrong-version fallback, abstain if no suitable evidence
    raise ValueError('unknown retrieval mode')
