"""Six paired retrieval baselines on 42 curated tasks; no LLM results claimed."""
from pathlib import Path
import sys,json,csv,time,collections,statistics
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'milestone3'))
from retrieval import BM25
from dense_retrieval import LSARetriever
from metadata import resolve_version
from api_compatibility import rank_for_version,in_range

MODES=('unconstrained','exact','range')

def evaluate():
  p=ROOT/'milestone3'
  docs=json.loads((p/'documents.json').read_text())
  tasks=json.loads((p/'tasks.json').read_text())
  models={'bm25':BM25(docs),'lsa':LSARetriever(docs,dimensions=16)}
  rows=[]
  for t in tasks:
    version=resolve_version(t['package'],t['package_json'],t['package_lock'])
    assert version==t['target_version']
    gold=t['correct_doc_id']
    for model_name,model in models.items():
      for mode in MODES:
        start=time.perf_counter_ns()
        hits=rank_for_version(model,t['query'],t['package'],version,mode,k=3)
        ms=(time.perf_counter_ns()-start)/1e6
        topdoc=hits[0][0] if hits else None
        rank=next((j+1 for j,(d,_) in enumerate(hits) if d['id']==gold),0)
        rows.append(dict(task_id=t['id'],task_type=t['task_type'],package=t['package'],
          target_version=version,model=model_name,mode=mode,method=f'{model_name}_{mode}',
          gold=gold,top1_id=topdoc['id'] if topdoc else '',
          top1_correct=int(bool(topdoc) and topdoc['id']==gold),
          top1_range_compatible=int(bool(topdoc) and in_range(version,topdoc['valid_range'])),
          recall_at3=int(rank>0),mrr_at3=(1/rank if rank else 0),
          abstained=int(not hits),latency_ms=round(ms,6),
          ranked_ids='|'.join(d['id'] for d,_ in hits)))
  with (p/'retrieval_results.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
  summary={}
  for name in sorted({r['method'] for r in rows}):
    rr=[r for r in rows if r['method']==name]
    breakdown={}
    for typ in ('breaking_change','stable_cross_version'):
      s=[x for x in rr if x['task_type']==typ]
      breakdown[typ]={'tasks':len(s),'top1_hits':sum(x['top1_correct'] for x in s),
        'abstentions':sum(x['abstained'] for x in s)}
    summary[name]={'tasks':len(rr),'top1_hits':sum(x['top1_correct'] for x in rr),
      'top1_accuracy':round(statistics.mean(x['top1_correct'] for x in rr),4),
      'compatible_at1':round(statistics.mean(x['top1_range_compatible'] for x in rr),4),
      'recall3':round(statistics.mean(x['recall_at3'] for x in rr),4),
      'mrr3':round(statistics.mean(x['mrr_at3'] for x in rr),4),
      'abstentions':sum(x['abstained'] for x in rr),'breakdown':breakdown}
  (p/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
  print(json.dumps(summary,indent=2))
  return summary
if __name__=='__main__':evaluate()
