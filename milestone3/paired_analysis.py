"""Paired McNemar exact tests and cluster bootstrap at the API-family level.

Each version-paired migration shares a query. Bootstrap resamples API families,
not individual task rows, so versions of the same family stay together.
"""
from pathlib import Path
import csv,json,random,statistics
from scipy.stats import binomtest
ROOT=Path(__file__).resolve().parent
ROWS=list(csv.DictReader((ROOT/'retrieval_results.csv').open()))
TASKS={t['id']:t for t in json.loads((ROOT/'tasks.json').read_text())}
D={}
for r in ROWS:D[(r['task_id'],r['method'])]=int(r['top1_correct'])
methods=[('bm25_unconstrained','bm25_exact'),('bm25_exact','bm25_range'),
         ('lsa_unconstrained','lsa_exact'),('lsa_exact','lsa_range')]
api_ids=sorted(set(t['api_id'] for t in TASKS.values()))
rng=random.Random(2687841)
RESULTS=[]
for a,b in methods:
    task_ids=sorted(TASKS)
    differences=[D[(t,b)]-D[(t,a)] for t in task_ids]
    gains=sum(x==1 for x in differences)
    losses=sum(x==-1 for x in differences)
    discordant=gains+losses
    exact_p=binomtest(min(gains,losses),discordant,0.5,alternative='two-sided').pvalue if discordant else 1.0
    by_api={api:[t['id'] for t in TASKS.values() if t['api_id']==api] for api in api_ids}
    cluster_samples=[]
    for _ in range(10000):
        sample=[rng.choice(api_ids) for __ in range(len(api_ids))]
        s=[D[(t,b)]-D[(t,a)] for api in sample for t in by_api[api]]
        cluster_samples.append(statistics.mean(s))
    cluster_samples.sort()
    RESULTS.append(dict(method_a=a,method_b=b,paired_task_count=len(task_ids),
        top1_gain_count=gains,top1_loss_count=losses,
        difference_percentage_points=round(100*statistics.mean(differences),2),
        bootstrap_95ci_pp=[round(100*cluster_samples[249],2),round(100*cluster_samples[9749],2)],
        exact_mcnemar_p=round(exact_p,6),
        note='Pilot constructed with paired version tasks and researcher-labeled ranges; not independent real-world generalization'))
(ROOT/'paired_statistics.json').write_text(json.dumps(RESULTS,indent=2)+'\n')
print(json.dumps(RESULTS,indent=2))
