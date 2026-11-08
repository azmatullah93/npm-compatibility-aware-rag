from pathlib import Path
import json
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parents[1]
s=json.loads((BASE/'outputs'/'summary.json').read_text())
labels=['BM25 (DocPrompting-style)','BM25 + version gate']
y=[s['bm25']['top1_accuracy'],s['version_aware']['top1_accuracy']]
fig,ax=plt.subplots(figsize=(7.3,4.1))
ax.bar(labels,y)
ax.set_ylim(0,1.10);ax.set_ylabel('Correct-document Top-1 rate')
ax.set_title('Retrieval-only pilot on 36 controlled tasks')
for i,v in enumerate(y):ax.text(i,v+.02,f'{100*v:.1f}%',ha='center',fontsize=10)
ax.text(.5,-.21,'Not LLM code success. Manually curated, version-labeled corpus.',ha='center',transform=ax.transAxes,fontsize=8)
fig.tight_layout()
fig.savefig(BASE/'outputs'/'retrieval_comparison.png',dpi=190,bbox_inches='tight')
print('Saved outputs/retrieval_comparison.png')
