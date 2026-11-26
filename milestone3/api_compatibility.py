"""Explicit API applicability ranges, distinct from matching doc release tags.

This is NOT an automatic compatibility inference model. It uses hand-declared
range annotations that would need independent verification in a full benchmark.
"""
import re

SEMVER=re.compile(r'^([0-9]+)\.([0-9]+)\.([0-9]+)(?:[-+][0-9A-Za-z.-]+)?$')

def parts(version):
    m=SEMVER.fullmatch(str(version).strip())
    if not m:raise ValueError(f'Unsupported exact semver: {version!r}')
    return tuple(map(int,m.groups()))

def in_range(version,range_expr):
    """Conjunction of lower/upper numeric semver comparators: >=,>,<=,<,=."""
    actual=parts(version)
    if not range_expr: return False
    checks=range_expr.split()
    for term in checks:
        m=re.fullmatch(r'(>=|<=|>|<|=)(\d+\.\d+\.\d+)',term)
        if not m:raise ValueError(f'Invalid range token: {term}')
        op,ver=m.groups();target=parts(ver)
        good={'<':actual<target,'<=':actual<=target,'>':actual>target,
              '>=':actual>=target,'=':actual==target}[op]
        if not good:return False
    return True

def is_compatible(doc,target,method):
    if method=='exact':return doc.get('version')==target
    if method=='range':return in_range(target,doc.get('valid_range'))
    if method=='oracle_labels':return target in doc.get('valid_versions',[])
    if method=='unconstrained':return True
    raise ValueError(method)

def rank_for_version(retriever,query,package,target,mode,k=3):
    pool=[i for i,d in enumerate(retriever.documents) if d['package']==package]
    ranked=retriever.rank(query,pool)
    return [(d,s) for d,s in ranked if is_compatible(d,target,mode)][:k]
