"""Runs retrieval-only pilot; does NOT claim LLM generation/execution results."""
import json,csv,random,statistics
from pathlib import Path
from retrieval import BM25, retrieve, compatible
from metadata import resolve_version

ROOT=Path(__file__).resolve().parents[1]

def evaluate_seed(documents,tasks,seed):
    docs=documents[:]
    random.Random(seed).shuffle(docs)
    model=BM25(docs)
    rows=[]
    for task in tasks:
        for mode in ('bm25','version_aware'):
            target=resolve_version(task['package'],task['package_json'],task['package_lock'])
            got=retrieve(model,task['query'],task['package'],target,mode,k=3)
            gold=task['correct_doc_id']
            rank=next((j+1 for j,(doc,_) in enumerate(got) if doc['id']==gold),None)
            rows.append(dict(seed=seed,task_id=task['id'],package=task['package'],version=task['target_version'],
                             method=mode,retrieved='|'.join(d['id'] for d,_ in got),
                             top1_hit=int(bool(got) and got[0][0]['id']==gold),
                             compatible_at1=int(bool(got) and compatible(got[0][0],task['target_version'])),
                             incompatible_at3=sum(not compatible(d,task['target_version']) for d,_ in got),
                             rr=0 if rank is None else 1/rank,
                             recall3=int(rank is not None)))
    return rows


def main():
    docs=json.loads((ROOT/'data'/'documents.json').read_text())
    tasks=json.loads((ROOT/'data'/'tasks.json').read_text())
    results=[]
    results=evaluate_seed(docs,tasks,seed=0)
    path=ROOT/'outputs'/'retrieval_results.csv'
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=results[0].keys()); writer.writeheader(); writer.writerows(results)
    summary={}
    for mode in ('bm25','version_aware'):
        r=[x for x in results if x['method']==mode]
        summary[mode]={
           'tasks':len(tasks),'seeds':1,
           'top1_accuracy':round(statistics.mean(x['top1_hit'] for x in r),4),
           'compatible_at1':round(statistics.mean(x['compatible_at1'] for x in r),4),
           'mrr_at3':round(statistics.mean(x['rr'] for x in r),4),
           'recall_at3':round(statistics.mean(x['recall3'] for x in r),4),
           'mean_incompatible_at3':round(statistics.mean(x['incompatible_at3'] for x in r),4)
        }
    (ROOT/'outputs'/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
