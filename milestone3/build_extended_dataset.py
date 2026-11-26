"""Construct a controlled migration + stable API test corpus.

All snippets are author-written paraphrases of vendor docs; validity ranges are
manually declared hypotheses, not automatically validated against installed npm.
"""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]

# Old and new major-version migration boundaries are restricted to the pairs
# present in this pilot, not assertions of validity on every release.
LIMITS={
  'express': ('4.0.0','5.0.0','6.0.0'),
  'mongoose': ('6.0.0','7.0.0','8.0.0'),
  'react-router-dom': ('5.0.0','6.0.0','7.0.0'),
}
STABLE=[
 ('express','express-basic-route','Register a simple GET health route in an Express app',
  "A basic GET route may use app.get('/health', (req,res) => res.send('ok')).",
  'https://expressjs.com/en/guide/routing.html'),
 ('mongoose','mongoose-findbyid','Find a MongoDB record by identifier using a Mongoose model',
  "Model.findById(id) retrieves a document by its identifier and returns a query object.",
  'https://mongoosejs.com/docs/queries.html'),
 ('react-router-dom','router-useparams','Read dynamic route parameters inside a React Router component',
  "useParams() reads URL route parameter values in a routed component.",
  'https://reactrouter.com/en/main/hooks/use-params'),
]

def build():
    docs=json.loads((ROOT/'data/documents.json').read_text())
    tasks=json.loads((ROOT/'data/tasks.json').read_text())
    for d in docs:
        low,cut,high=LIMITS[d['package']]
        if d['id'].endswith('-old'):
            d['valid_range']=f'>={low} <{cut}'
        elif d['id'].endswith('-new'):
            d['valid_range']=f'>={cut} <{high}'
        else:
            raise ValueError(d['id'])
        d['validity_provenance']='author-assigned migration-boundary metadata; not independently executed'
    for pkg,api_id,query,desc,url in STABLE:
        low,cut,high=LIMITS[pkg]
        old=next(d['version'] for d in docs if d['package']==pkg and d['id'].endswith('-old'))
        new=next(d['version'] for d in docs if d['package']==pkg and d['id'].endswith('-new'))
        did=api_id+'-shared'
        docs.append(dict(id=did,api_id=api_id,package=pkg,version=old,valid_versions=[old,new],
            valid_range=f'>={low} <{high}',text=desc,source=url,
            provenance='author-written stable API paraphrase; cross-version status not yet tested against real packages',
            validity_provenance='author-assigned cross-version stability hypothesis'))
        for label,v in [('old',old),('new',new)]:
            tasks.append(dict(id=f'{api_id}-task-{label}',api_id=api_id,package=pkg,target_version=v,
                query=query,correct_doc_id=did,source=url,
                package_json={'dependencies':{pkg:'^'+v}},
                package_lock={'lockfileVersion':3,'packages':{'node_modules/'+pkg:{'version':v}}},
                task_type='stable_cross_version'))
    for t in tasks:
        t.setdefault('task_type','breaking_change')
    out=ROOT/'milestone3'
    (out/'documents.json').write_text(json.dumps(docs,indent=2)+'\n')
    (out/'tasks.json').write_text(json.dumps(tasks,indent=2)+'\n')
    return len(docs),len(tasks)

if __name__=='__main__':
    print('Extended pilot corpus:',build())
