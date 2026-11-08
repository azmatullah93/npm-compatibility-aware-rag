"""Paired retrieval benchmark with BM25 and LSA (offline) and a version gate.

Results compare retrieval only, NEVER generated-code execution success.
"""
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from retrieval import BM25, compatible, retrieve
from dense_retrieval import LSARetriever
from metadata import resolve_version

METHODS = ('bm25','bm25_version','lsa','lsa_version')

def evaluate():
    docs=json.loads((ROOT/'data'/'documents.json').read_text())
    tasks=json.loads((ROOT/'data'/'tasks.json').read_text())
    models={'bm25':BM25(docs), 'lsa':LSARetriever(docs,dimensions=16)}
    rows=[]
    for task in tasks:
        version=resolve_version(task['package'],task['package_json'],task['package_lock'])
        assert version==task['target_version']
        for method in METHODS:
            model=models['bm25' if method.startswith('bm25') else 'lsa']
            mode='version_aware' if method.endswith('_version') else 'bm25'
            begin=time.perf_counter_ns()
            hits=retrieve(model, task['query'], task['package'], version, mode, k=3)
            elapsed=(time.perf_counter_ns()-begin)/1e6
            gold=task['correct_doc_id']
            r=next((j+1 for j,(d,_) in enumerate(hits) if d['id']==gold),0)
            topdoc=hits[0][0] if hits else None
            rows.append({
                'task_id':task['id'],'package':task['package'],'target_version':version,
                'method':method,'top1_id':topdoc['id'] if topdoc else '',
                'gold':gold,'top1_correct':int(bool(topdoc) and topdoc['id']==gold),
                'top1_compatible':int(bool(topdoc) and compatible(topdoc,version)),
                'recall3':int(r>0),'mrr3':round(1/r,6) if r else 0,
                'returned':len(hits),'latency_ms':round(elapsed,6),
                'ranked_ids':'|'.join(d['id'] for d,_ in hits)
            })
    out=ROOT/'outputs'
    with (out/'extended_results.csv').open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    summary={}
    for method in METHODS:
        sel=[r for r in rows if r['method']==method]
        summary[method]={
            'tasks':len(sel),
            'top1_hits':sum(r['top1_correct'] for r in sel),
            'top1_accuracy':round(mean(r['top1_correct'] for r in sel),4),
            'compatible_top1_hits':sum(r['top1_compatible'] for r in sel),
            'compatible_at1':round(mean(r['top1_compatible'] for r in sel),4),
            'recall3':round(mean(r['recall3'] for r in sel),4),
            'mrr3':round(mean(r['mrr3'] for r in sel),4),
            'avg_latency_ms':round(mean(r['latency_ms'] for r in sel),4)
        }
    (out/'extended_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return summary

if __name__=='__main__':evaluate()
