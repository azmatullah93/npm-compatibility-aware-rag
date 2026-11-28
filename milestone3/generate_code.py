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

def describe_quota_error(error):
    """Summarize only safe, relevant Gemini quota fields; never echo a key."""
    def limited(value):
        import re
        return re.sub(r'[^a-zA-Z0-9_.:/-]', '', str(value))[:140]

    lines = [
        'HTTP 429: Gemini rejected the request due to a rate limit or quota.',
        'Your completed JSONL responses were saved. Resume with --resume after the quota permits requests.',
        'See https://aistudio.google.com/rate-limit for project-specific RPM/TPM/RPD limits.'
    ]
    retry = error.headers.get('Retry-After') if error.headers else None
    if retry:
        lines.append('Retry-After header: ' + limited(retry))
    try:
        body = json.loads(error.read(32768).decode('utf-8'))
        details = (body.get('error') or {}).get('details') or []
        for detail in details:
            if not isinstance(detail,dict):
                continue
            if detail.get('@type','').endswith('QuotaFailure'):
                for violation in detail.get('violations',[])[:8]:
                    quota_id = violation.get('quotaId')
                    metric = violation.get('quotaMetric')
                    if quota_id:
                        lines.append('Quota ID: ' + limited(quota_id))
                    if metric:
                        lines.append('Quota metric: ' + limited(metric))
            elif detail.get('@type','').endswith('RetryInfo'):
                delay = detail.get('retryDelay')
                if delay:
                    lines.append('Provider suggested retry delay: ' + limited(delay))
    except (OSError,ValueError,UnicodeError,AttributeError,TypeError):
        pass
    return '\n'.join(lines)


def describe_forbidden_error(error):
    """Classify Gemini 403 response safely, without printing credentials or raw messages."""
    lines=[
        'HTTP 403: Google refused API access; this is not a model-generation failure.',
        'Preserved all successful JSONL responses; do not overwrite them.',
        'Check the selected project status, model entitlement, key restrictions and Google AI Studio billing.',
    ]
    try:
        body=json.loads(error.read(32768).decode('utf-8'))
        payload=body.get('error') or {}
        status=payload.get('status')
        if status in ('PERMISSION_DENIED','UNAUTHENTICATED','FAILED_PRECONDITION'):
            lines.append('Google error status: '+status)
        msg=str(payload.get('message','')).lower()
        if 'project has been denied access' in msg:
            lines.append('Reason: Google explicitly denied this project access. Check AI Studio project banners and request a review from Google support.')
        elif 'api_key_service_blocked' in msg or ('requests to this api' in msg and 'blocked' in msg):
            lines.append('Reason: the API key is not authorized for this Google API. Check the key\'s API restrictions and endpoint.')
        elif 'billing' in msg or 'payment' in msg:
            lines.append('Reason: billing or payment restrictions mentioned by Google. Check your project billing settings.')
        elif 'not supported' in msg or 'not available' in msg or 'model' in msg and 'access' in msg:
            lines.append('Reason: a model entitlement or availability restriction may apply.')
        for detail in payload.get('details',[]) or []:
            if not isinstance(detail,dict):
                continue
            reason=(detail.get('reason') or '')
            if reason in ('API_KEY_SERVICE_BLOCKED','API_KEY_HTTP_REFERRER_BLOCKED',
                          'API_KEY_IP_ADDRESS_BLOCKED','API_KEY_INVALID',
                          'SERVICE_DISABLED','CONSUMER_INVALID','ACCESS_TOKEN_SCOPE_INSUFFICIENT'):
                lines.append('Google detail reason: '+reason)
    except (OSError,ValueError,UnicodeError,AttributeError,TypeError):
        pass
    lines.append('Do not rotate keys or create new projects to bypass an access restriction.')
    return '\n'.join(lines)


def openai_chat(prompt,model,url,key):
    data=json.dumps({'model':model,'messages':[{'role':'user','content':prompt}], 'temperature':0}).encode()
    req=urllib.request.Request(url.rstrip('/')+'/chat/completions',data=data,
      headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=90) as resp:
            body=json.load(resp)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise SystemExit(describe_quota_error(error)) from None
        if error.code == 403:
            raise SystemExit(describe_forbidden_error(error)) from None
        raise
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

def planned_rows(args, tasks, docs):
    """Build all expected prompts before any paid API calls; freeze trial identities."""
    models = {'bm25':BM25(docs), 'lsa':LSARetriever(docs, dimensions=16)}
    model_name, mode = args.retriever, args.compatibility
    model = models[model_name]
    by_id = {t['id']:t for t in tasks}
    ids = SUITES[args.suite]
    if len(set(ids)) != len(ids) or any(i not in by_id or i not in EXEC_TASKS for i in ids):
        raise ValueError('Missing or duplicate suite task definitions')
    if args.limit is not None and args.limit < 1:
        raise ValueError('--limit must be positive')
    rows = []
    for tid in ids[:args.limit]:
        task = by_id[tid]
        version = resolve_version(task['package'], task['package_json'], task['package_lock'])
        if mode == 'none':
            context = []
        elif mode == 'oracle':
            context = [next(d for d in docs if d['id'] == task['correct_doc_id'])]
        else:
            hits = rank_for_version(model, task['query'], task['package'], version, mode, k=3)
            context = [d for d, _ in hits]
        rows.append({
            'task_id':tid, 'package':task['package'], 'target_version':version,
            'method':f'{model_name}_{mode}', 'retrieved_ids':[d['id'] for d in context],
            'model':args.model, 'prompt':prompt_for(task, context),
            'provider':'prompt_only' if args.dry_run else 'openai_compatible_chat_api',
            'suite':args.suite, 'temperature_requested':0
        })
    return rows


def load_resume_rows(path, planned, dry_run):
    """Reject stale, corrupt or non-prefix trials; never silently change a result."""
    if not path.exists():
        return []
    existing = []
    for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            raise ValueError(f'Blank row in existing JSONL at line {lineno}; refusing unsafe resume')
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f'Corrupt JSONL row {lineno}; fix from a backup, not regeneration') from error
        if not isinstance(row, dict) or len(existing) >= len(planned):
            raise ValueError('Existing file contains unexpected trials; refusing unsafe resume')
        expected = planned[len(existing)]
        for key, value in expected.items():
            if row.get(key) != value:
                raise ValueError(f'Resume mismatch line {lineno}, field {key}; refusing to overwrite or mix experiments')
        if not dry_run and (not isinstance(row.get('code'), str) or not row['code'].strip()):
            raise ValueError(f'Missing genuine code on existing line {lineno}; refusing unsafe resume')
        existing.append(row)
    return existing


def run(args):
    tasks=json.loads((HERE/'tasks.json').read_text(encoding='utf-8'))
    docs=json.loads((HERE/'documents.json').read_text(encoding='utf-8'))
    planned=planned_rows(args,tasks,docs)
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    if args.resume and args.overwrite:
        raise ValueError('Use either --resume or --overwrite, never both')
    if args.resume:
        existing=load_resume_rows(path,planned,args.dry_run)
        file_mode='a'
    elif args.overwrite:
        existing=[]
        file_mode='w'
    else:
        existing=[]
        file_mode='x' # default: fail if an output exists rather than destroy research data

    remaining=planned[len(existing):]
    if remaining and not args.dry_run and not os.environ.get('OPENAI_API_KEY'):
        raise SystemExit('OPENAI_API_KEY not set; no new LLM generation has been run.')
    if not remaining:
        print(f'Already complete: {len(existing)}/{len(planned)} responses in {path}; no new API calls')
        return

    with path.open(file_mode,encoding='utf-8') as f:
        for row in remaining:
            row=row.copy()
            if not args.dry_run:
                row['code'],row['generation_response']=openai_chat(
                    row['prompt'],args.model,args.api_url,os.environ['OPENAI_API_KEY'])
            f.write(json.dumps(row)+'\n')
            f.flush()
            os.fsync(f.fileno())
    print(f'Completed {len(planned)}/{len(planned)} '
          f'{"prompts only" if args.dry_run else "genuine API responses"} at {path} '
          f'({len(existing)} reused, {len(remaining)} new)')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--retriever',choices=['bm25','lsa'],default='bm25')
    p.add_argument('--compatibility',choices=['none','unconstrained','exact','range','oracle'],default='range')
    p.add_argument('--model',default='SET_MODEL_ID')
    p.add_argument('--api-url',default='https://api.openai.com/v1')
    p.add_argument('--suite',choices=sorted(SUITES),default='pilot4')
    p.add_argument('--limit',type=int,default=None)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--resume',action='store_true',help='Append only missing trials after verifying previously saved rows')
    p.add_argument('--overwrite',action='store_true',help='Explicitly replace a previously created output (not for research runs)')
    p.add_argument('--output',default=str(HERE/'prompts_dry_run.jsonl'))
    run(p.parse_args())
