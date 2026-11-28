"""Preserve the actual 24-trial Gemini pilot, retrieval audit and npm release evidence.

No Gemini calls, npm installs, Docker, or generated-code execution.
Aborts on missing/inconsistent evidence and never overwrites an existing archive.
The source JSONL files include *raw model-generated content*: review before sharing.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT / 'milestone3'))
from generate_code import CROSS_VERSION12

WS = ROOT / 'milestone3' / 'npm_workspaces'
BASE = [
 'milestone3/tasks.json',
 'milestone3/documents.json',
 'milestone3/execution_specs.json',
 'milestone3/generate_code.py',
 'milestone3/api_compatibility.py',
 'src/dense_retrieval.py',
 'milestone3/export_contract.cjs',
 'src/retrieval.py',
 'src/metadata.py',
 'milestone4/build_reference_trials.cjs',
 'milestone4/test_release_behavior.cjs',
 'milestone4/PROTOCOL.md',
 'milestone3/run_generated_code.cjs',
 'milestone3/summarize_execution.py',
 'milestone4/audit_retrieval.py',
 'milestone4/probe_release_behavior.cjs',
 'milestone4/EXPLORATORY_FINDINGS_2026-11-28.md',
 'milestone3/npm_workspaces/cross_version12/none.jsonl',
 'milestone3/npm_workspaces/cross_version12/unconstrained.jsonl',
 'milestone3/npm_workspaces/partial24/all_generated.jsonl',
 'milestone3/npm_workspaces/partial24/results.json',
 'milestone3/npm_workspaces/retrieval_preview/unconstrained.jsonl',
 'milestone3/npm_workspaces/retrieval_preview/exact.jsonl',
 'milestone3/npm_workspaces/retrieval_preview/range.jsonl',
 'milestone3/npm_workspaces/retrieval_preview/audit.json',
 'milestone3/npm_workspaces/release_behavior_probes.json',
]
PINNED={
 'express':'4.21.2',
 'express-new':'5.1.0',
 'mongoose':'6.13.8',
 'mongoose-new':'7.8.7',
}
for key,version in PINNED.items():
    package=key.split('-')[0]
    folder=(package+'-'+version).replace('.','_')
    BASE.append('milestone3/npm_workspaces/'+folder+'/package-lock.json')
BASE.extend([
 'milestone3/npm_workspaces/reference12/golden.jsonl',
 'milestone3/npm_workspaces/reference12/results.json',
])
MODES=('none','unconstrained')
RETRIEVAL_MODES=('unconstrained','exact','range')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path):
    raw=path.read_bytes()
    if not raw.endswith(b'\n'):
        raise ValueError('Missing JSONL trailing newline: '+str(path))
    data=[json.loads(line) for line in raw.decode('utf-8').splitlines()]
    if not all(isinstance(row,dict) for row in data):
        raise ValueError('Non-object JSONL row in '+str(path))
    return data


def validate():
    paths=[ROOT / name for name in BASE]
    missing=[str(p.relative_to(ROOT)) for p in paths if not p.is_file()]
    if missing:
        raise ValueError('Missing required evidence files: '+repr(missing))
    original={m:read_jsonl(WS/'cross_version12'/(m+'.jsonl')) for m in MODES}
    for mode,rows in original.items():
        if len(rows)!=12 or [r.get('task_id') for r in rows]!=list(CROSS_VERSION12):
            raise ValueError(mode+': not the complete frozen twelve-task suite')
        if any(r.get('method')!='bm25_'+mode or r.get('model')!='gemini-3.5-flash'
               or r.get('suite')!='cross_version12' or
               not isinstance(r.get('generation_response'),dict) for r in rows):
            raise ValueError(mode+': unexpected method/model/provenance')
    left=(WS/'cross_version12'/'none.jsonl').read_bytes()
    right=(WS/'cross_version12'/'unconstrained.jsonl').read_bytes()
    combined_path=WS/'partial24'/'all_generated.jsonl'
    if combined_path.read_bytes()!=left+right:
        raise ValueError('Combined 24-trial JSONL does not match unmodified originals')
    executions=read_json(WS/'partial24'/'results.json')
    if not isinstance(executions,list) or len(executions)!=24:
        raise ValueError('Expected exactly 24 executed observations')
    seen=set()
    success={m:0 for m in MODES}
    for row in executions:
        if not isinstance(row,dict):
            raise ValueError('Invalid execution row')
        method=row.get('method','').removeprefix('bm25_')
        key=(method,row.get('task_id'))
        if method not in MODES or key in seen:
            raise ValueError('Duplicate or unknown execution pair: '+repr(key))
        seen.add(key)
        matching=next((x for x in original[method] if x['task_id']==row['task_id']),None)
        if matching is None:
            raise ValueError('Unexpected task in execution results: '+repr(key))
        if row.get('model')!=matching.get('model') or row.get('target_version')!=matching.get('target_version'):
            raise ValueError('Model/package version mismatch for '+repr(key))
        if row.get('export_contract')!='direct_or_named_setup':
            raise ValueError('Wrong primary evaluation export contract in '+repr(key))
        codehash=sha256(matching['code'].encode('utf-8'))
        if row.get('code_sha256')!=codehash:
            raise ValueError('Generated code differs from executed code in '+repr(key))
        if row.get('status') not in ('PASS','FAIL'):
            raise ValueError('Not a successful Docker execution: '+repr(row.get('status')))
        success[method]+=int(row['status']=='PASS')
    if len(seen)!=24:
        raise ValueError('Missing executed task/condition pairs')
    audit=read_json(WS/'retrieval_preview'/'audit.json')
    if audit.get('basis')!='author_assigned_document_gold_and_version_validity' or not audit.get('no_llm_calls'):
        raise ValueError('Retrieval audit provenance mismatch')
    for name in ('tasks','documents'):
        path=ROOT/'milestone3'/(name+'.json')
        if audit.get(name+'_sha256')!=sha256(path.read_bytes()):
            raise ValueError(name+' source hashes disagree with retrieval audit')
    for mode in RETRIEVAL_MODES:
        stats=audit['methods'][mode]
        preview=WS/'retrieval_preview'/(mode+'.jsonl')
        if stats['preview_sha256']!=sha256(preview.read_bytes()) or stats['n_tasks']!=12:
            raise ValueError('Retrieval preview does not match audited evidence for '+mode)
    probe=read_json(WS/'release_behavior_probes.json')
    observations=probe.get('observations')
    if (not isinstance(observations,list) or len(observations)!=26
        or any(not isinstance(x.get('observed'),bool) or
               not isinstance(x.get('expected'),bool) or
               x['observed']!=x['expected'] or
               x.get('passed') is not True for x in observations)
        or probe.get('summary')!={'passed':26,'failed':0,'total':26}):
        raise ValueError('Independent exact-release capability checks not all passing')
    locks=probe['environment'].get('release_locks')
    expected_versions={('express','4.21.2'),('express','5.1.0'),
                       ('mongoose','6.13.8'),('mongoose','7.8.7')}
    if (not isinstance(locks,list) or
        {(x.get('package'),x.get('version')) for x in locks}!=expected_versions or
        len(locks)!=4):
        raise ValueError('Missing pinned npm versions in release probe')
    for pin in locks:
        folder=(pin['package']+'-'+pin['version']).replace('.','_')
        path=WS/folder/'package-lock.json'
        if pin.get('lockfile_sha256')!=sha256(path.read_bytes()):
            raise ValueError('Pinned npm lockfile changed: '+str(path))
    return {
        'evidence_type':'2026-11-28_exploratory_pilot_not_conference_final',
        'experiment':'Gemini 3.5 Flash cross_version12, partial two-of-five methods',
        'trials_executed':len(executions),
        'execution_by_method':{
            'bm25_'+mode:{'passed':success[mode],'total':12}
            for mode in MODES
        },
        'retrieval_metrics_author_labeled':{
            mode:{name:audit['methods'][mode][name] for name in
                ('gold_at_1','gold_at_3','hits_outside_author_validity')}
            for mode in RETRIEVAL_MODES
        },
        'release_checks':probe['summary'],
        'four_installed_releases':locks,
        'model_api_project_changed':True,
        'scope_notes':[
            'Author-assigned retrieval gold and validity labels are not external truth.',
            'Mongoose release probes do not establish database persistence.',
            'One generated candidate per task/method; three more methods unfinished.',
            'Generation used multiple Google API projects; provider metadata is retained in raw JSONL.',
            'Duplicate release-probe invocation is not independent replication.',
            'Do not treat human-authored reference trials as model outputs.'
        ],
    }


def archive(destination):
    if destination.exists():
        raise FileExistsError('Refusing to overwrite an existing research archive: '+str(destination))
    result=validate()
    generated=datetime.now(timezone.utc).isoformat()
    file_hashes={
        name:{'sha256':sha256((ROOT/name).read_bytes()),
              'bytes':(ROOT/name).stat().st_size}
        for name in sorted(BASE)
    }
    manifest={'created_at_utc':generated,**result,'files':file_hashes}
    destination.parent.mkdir(parents=True,exist_ok=True)
    created = False
    try:
        with zipfile.ZipFile(destination,mode='x',compression=zipfile.ZIP_DEFLATED) as z:
            created = True
            for name in sorted(BASE):
                z.write(ROOT/name,arcname=name)
            z.writestr('EVIDENCE_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    except Exception:
        if created:
            destination.unlink(missing_ok=True)
        raise
    return {'path':str(destination),'sha256':sha256(destination.read_bytes()),
            'included_files':len(BASE),'summary':result}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,
      default=WS/'archives'/'gemini_pilot_evidence_2026-11-28.zip')
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    print(json.dumps(validate() if args.check_only else archive(args.output),indent=2))
