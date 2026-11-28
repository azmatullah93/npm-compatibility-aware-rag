"""Generate version-specific JS solutions using an OpenAI-compatible API.

Never fabricates model output. --dry-run writes only prompts, not solutions.
The API key is read from the environment; it is never persisted in outputs.
"""
import argparse,json,os,sys,urllib.request,urllib.error
from datetime import datetime, timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(HERE))
from retrieval import BM25
from dense_retrieval import LSARetriever
from metadata import resolve_version
from api_compatibility import rank_for_version

# A small subset has executable specifications. The schema is deliberately fixed.
EXEC_TASKS={
 'express-wildcard-task-new': "Export a CommonJS function setup(express). It must create an Express app and register a GET catch-all route that also matches '/' and nested URLs. The handler must respond with HTTP 200. Return the app. Do not call listen().",
 'express-del-task-new': "Export a CommonJS function setup(express). Create an Express app, register a DELETE route at '/item' whose handler responds with HTTP 200, and return the app. Do not call listen().",
 'mongoose-remove-task-new': "Export a CommonJS function setup(mongoose). Create a unique Mongoose model called ExampleRecord with {name:String}, and return a function that deletes all matching records using a method supported by this installed version. Do not connect to any DB.",
 'mongoose-update-task-new': "Export a CommonJS function setup(mongoose). Create a unique Mongoose model called ExampleRecord with {name:String}, and return a function that updates exactly one matching record using a method supported by this installed version. Do not connect to any DB.",
}

# Fixed ordered suites: never silently change task membership in a prior experiment.
PILOT4 = (
 'express-wildcard-task-new',
 'express-del-task-new',
 'mongoose-remove-task-new',
 'mongoose-update-task-new',
)
CROSS_VERSION12 = PILOT4 + (
 'express-wildcard-task-old',
 'express-del-task-old',
 'express-basic-route-task-old',
 'express-basic-route-task-new',
 'mongoose-remove-task-old',
 'mongoose-update-task-old',
 'mongoose-findbyid-task-old',
 'mongoose-findbyid-task-new',
)
SUITES = {'pilot4': PILOT4, 'cross_version12': CROSS_VERSION12}

# New tasks are independently evaluated under the same installed-package harness.
EXEC_TASKS.update({
 'express-wildcard-task-old': "Export a CommonJS function setup(express). Create an Express app with a GET catch-all handler that returns HTTP 200 for the root path and nested paths on the installed version. Return the app. Do not call listen().",
 'express-del-task-old': "Export a CommonJS function setup(express). Create an Express app and register a DELETE endpoint at '/item' that responds with HTTP 200. Return the app. Do not call listen().",
 'express-basic-route-task-old': "Export a CommonJS function setup(express). Create an Express app with GET '/health' that returns the exact text 'ok' and HTTP 200. Return the app. Do not call listen().",
 'express-basic-route-task-new': "Export a CommonJS function setup(express). Create an Express app with GET '/health' that returns the exact text 'ok' and HTTP 200. Return the app. Do not call listen().",
 'mongoose-remove-task-old': "Export a CommonJS function setup(mongoose). Create a Mongoose model called ExampleRecord with {name:String}; return a function that deletes ALL matching records via an API available in the installed version. Do not connect to a DB.",
 'mongoose-update-task-old': "Export a CommonJS function setup(mongoose). Create a Mongoose model called ExampleRecord with {name:String}; return a function that updates exactly ONE matching record, using a method available in the installed version. Do not connect to a DB.",
 'mongoose-findbyid-task-old': "Export a CommonJS function setup(mongoose). Create a Mongoose model called ExampleRecord with {name:String}; return a function lookup(id) that retrieves the document using Model.findById(id). Do not connect to a DB.",
 'mongoose-findbyid-task-new': "Export a CommonJS function setup(mongoose). Create a Mongoose model called ExampleRecord with {name:String}; return a function lookup(id) that retrieves the document using Model.findById(id). Do not connect to a DB.",
})

def prompt_for(task,docs):
    return ("You are producing JavaScript CommonJS code for a controlled API-version experiment.\n"
       f"Installed npm package: {task['package']}@{task['target_version']}\n"
       f"Task: {EXEC_TASKS[task['id']]}\n\n"
       "Retrieved documentation (may contain wrong-version material):\n"+
       '\n\n'.join(f"Document {i+1}, labeled {d['version']}: {d['text']}" for i,d in enumerate(docs))+
       "\n\nReturn only the JavaScript source file without Markdown fences. Export a setup function as described. Do not execute anything at module import time.")

def openai_chat(prompt,model,url,key):
    data=json.dumps({'model':model,'messages':[{'role':'user','content':prompt}], 'temperature':0}).encode()
    req=urllib.request.Request(url.rstrip('/')+'/chat/completions',data=data,
      headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=90) as resp:
        body=json.load(resp)
    result=body['choices'][0]['message']['content']
    if not isinstance(result,str) or not result.strip():raise ValueError('Empty response')
    s=result.strip()
    if s.startswith('```'):
        parts=s.split('```')
        s='\n'.join(parts[1].splitlines()[1:] if parts[1].splitlines()[0].strip() in ('js','javascript') else parts[1].splitlines())
    return s, {'provider_response_id':body.get('id'),
               'provider_reported_model':body.get('model'),
               'provider_created_epoch':body.get('created'),
               'provider_usage':body.get('usage'),
               'finish_reason':body['choices'][0].get('finish_reason'),
               'raw_response_content':result,
               'received_at_utc':datetime.now(timezone.utc).isoformat()}

def run(args):
    tasks=json.loads((HERE/'tasks.json').read_text())
    docs=json.loads((HERE/'documents.json').read_text())
    models={'bm25':BM25(docs),'lsa':LSARetriever(docs,dimensions=16)}
    model_name,mode=args.retriever,args.compatibility
    model=models[model_name]
    by_id={t['id']:t for t in tasks}
    ids=SUITES[args.suite]
    if len(set(ids)) != len(ids) or any(i not in by_id or i not in EXEC_TASKS for i in ids):
        raise ValueError('Missing or duplicate suite task definitions')
    if args.limit is not None and args.limit < 1:
        raise ValueError('--limit must be positive')
    selected=[by_id[i] for i in ids[:args.limit]]
    if not args.dry_run and not os.environ.get('OPENAI_API_KEY'):
        raise SystemExit('OPENAI_API_KEY not set; no LLM generation has been run.')
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w') as f:
        for t in selected:
            ver=resolve_version(t['package'],t['package_json'],t['package_lock'])
            if mode=='none':
                context=[]
            elif mode=='oracle':
                context=[next(d for d in docs if d['id']==t['correct_doc_id'])]
            else:
                hits=rank_for_version(model,t['query'],t['package'],ver,mode,k=3)
                context=[d for d,_ in hits]
            prompt=prompt_for(t,context)
            row={'task_id':t['id'],'package':t['package'],'target_version':ver,'method':f'{model_name}_{mode}',
                 'retrieved_ids':[d['id'] for d in context], 'model':args.model,'prompt':prompt,
                 'provider':'prompt_only' if args.dry_run else 'openai_compatible_chat_api',
                 'suite':args.suite, 'temperature_requested':0}
            if not args.dry_run:
                row['code'],row['generation_response']=openai_chat(prompt,args.model,args.api_url,os.environ['OPENAI_API_KEY'])
            f.write(json.dumps(row)+'\n')
    print(f"Wrote {len(selected)} {'prompts only' if args.dry_run else 'genuine API responses'} to {path}")

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--retriever',choices=['bm25','lsa'],default='bm25')
    p.add_argument('--compatibility',choices=['none','unconstrained','exact','range','oracle'],default='range')
    p.add_argument('--model',default='SET_MODEL_ID')
    p.add_argument('--api-url',default='https://api.openai.com/v1')
    p.add_argument('--suite',choices=sorted(SUITES),default='pilot4')
    p.add_argument('--limit',type=int,default=None)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--output',default=str(HERE/'prompts_dry_run.jsonl'))
    run(p.parse_args())
