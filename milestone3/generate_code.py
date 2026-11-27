"""Generate version-specific JS solutions using an OpenAI-compatible API.

Never fabricates model output. --dry-run writes only prompts, not solutions.
The API key is read from the environment; it is never persisted in outputs.
"""
import argparse,json,os,sys,urllib.request,urllib.error
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
    return s

def run(args):
    tasks=json.loads((HERE/'tasks.json').read_text())
    docs=json.loads((HERE/'documents.json').read_text())
    models={'bm25':BM25(docs),'lsa':LSARetriever(docs,dimensions=16)}
    model_name,mode=args.retriever,args.compatibility
    model=models[model_name]
    selected=[t for t in tasks if t['id'] in EXEC_TASKS][:args.limit]
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
                 'provider':'prompt_only' if args.dry_run else 'openai_compatible_chat_api'}
            if not args.dry_run:
                row['code']=openai_chat(prompt,args.model,args.api_url,os.environ['OPENAI_API_KEY'])
            f.write(json.dumps(row)+'\n')
    print(f"Wrote {len(selected)} {'prompts only' if args.dry_run else 'genuine API responses'} to {path}")

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--retriever',choices=['bm25','lsa'],default='bm25')
    p.add_argument('--compatibility',choices=['none','unconstrained','exact','range','oracle'],default='range')
    p.add_argument('--model',default='SET_MODEL_ID')
    p.add_argument('--api-url',default='https://api.openai.com/v1')
    p.add_argument('--limit',type=int,default=4)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--output',default=str(HERE/'prompts_dry_run.jsonl'))
    run(p.parse_args())
