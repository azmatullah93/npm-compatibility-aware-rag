"""Plot measured retrieval-only outcomes."""
from pathlib import Path
import json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent
s=json.loads((p/'summary.json').read_text())
keys=['bm25_unconstrained','bm25_exact','bm25_range','lsa_unconstrained','lsa_exact','lsa_range']
labels=['BM25','BM25\nExact','BM25\nRange','LSA','LSA\nExact','LSA\nRange']
fig,ax=plt.subplots(figsize=(8.3,4.1))
y=[100*s[k]['top1_accuracy'] for k in keys]
bars=ax.bar(labels,y)
for b,v in zip(bars,y):ax.text(b.get_x()+b.get_width()/2,v+1,f'{v:.1f}%',ha='center',va='bottom',fontsize=8)
ax.set(ylim=(0,110),ylabel='Correct-document Top-1 (%)',title='Extended pilot: 42 version-conditioned retrieval tasks')
ax.grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(p/'retrieval_six_methods.png',dpi=165);plt.close(fig)
