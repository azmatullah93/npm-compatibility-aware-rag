"""Recreate the plotted four-condition retrieval comparison from result JSON."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
s=json.loads((ROOT/'outputs'/'extended_summary.json').read_text())
methods=['bm25','bm25_version','lsa','lsa_version']
names=['BM25','BM25 + version','LSA (dense)','LSA + version']
values=[s[x]['top1_accuracy']*100 for x in methods]
fig,ax=plt.subplots(figsize=(8.2,3.2))
bar=ax.bar(names,values,color=['#6F8FA6','#1B709B','#8695A6','#318E7E'],width=.65)
for rect,v in zip(bar,values):
    ax.text(rect.get_x()+rect.get_width()/2,v+1.5,f'{v:.1f}%',ha='center',fontsize=10)
ax.set_ylim(0,100)
ax.set_title('Controlled retrieval-only evaluation (36 tasks)')
ax.set_ylabel('Correct document at rank 1 (%)')
ax.spines[['right','top']].set_visible(False)
ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
plt.xticks(rotation=12,ha='right')
fig.tight_layout()
fig.savefig(ROOT/'outputs'/'retrieval_four_methods.png',dpi=180,bbox_inches='tight')
plt.close(fig)
