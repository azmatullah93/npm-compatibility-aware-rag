"""Strictly validate the 5 x 12 Gemini result files before Docker execution.

No network calls. Never changes a model response, substitutes missing rows,
or silently overwrites a previous combined output.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT/'milestone3'))
from generate_code import CROSS_VERSION12

MODES = ('none','unconstrained','exact','range','oracle')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def combine(directory: Path, model: str):
    tasks = {t['id']:t for t in json.loads((ROOT/'milestone3'/'tasks.json').read_text(encoding='utf-8'))}
    all_rows = []
    manifest = {'suite':'cross_version12','model':model,
                'methods':{},'tasks_per_method':len(CROSS_VERSION12)}
    for mode in MODES:
        file = directory / (mode+'.jsonl')
        if not file.is_file():
            raise ValueError(f'Missing method output: {file}')
        content = file.read_bytes()
        try:
            rows = [json.loads(line) for line in content.decode('utf-8').splitlines() if line.strip()]
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f'Invalid JSONL content: {file}') from error
        if len(rows) != len(CROSS_VERSION12):
            raise ValueError(f'{mode}: expected {len(CROSS_VERSION12)} complete responses; found {len(rows)}')
        for index, (row, task_id) in enumerate(zip(rows,CROSS_VERSION12),1):
            expected = tasks[task_id]
            if (row.get('task_id') != task_id or row.get('method') != 'bm25_'+mode
                or row.get('suite') != 'cross_version12' or row.get('model') != model
                or row.get('provider') != 'openai_compatible_chat_api'
                or row.get('target_version') != expected['target_version']
                or row.get('package') != expected['package']):
                raise ValueError(f'{mode}: wrong experiment identity or version at line {index}')
            if (not isinstance(row.get('code'),str) or not row['code'].strip()
                or not isinstance(row.get('prompt'),str) or not row['prompt'].strip()
                or not isinstance(row.get('retrieved_ids'),list)):
                raise ValueError(f'{mode}: incomplete generated trial line {index}')
            if row.get('temperature_requested') != 0 or not isinstance(row.get('generation_response'),dict):
                raise ValueError(f'{mode}: missing controlled generation metadata at line {index}')
        manifest['methods'][mode] = {'trials':len(rows),'source_sha256':digest(content)}
        all_rows.extend(rows)

    if len(all_rows)!=60 or len({(row['method'],row['task_id']) for row in all_rows})!=60:
        raise ValueError('Duplicate or missing experiment pair(s)')
    combined = ''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in all_rows).encode('utf-8')
    dest = directory/'all_generated.jsonl'
    if dest.exists():
        if dest.read_bytes()!=combined:
            raise ValueError(f'Refusing to overwrite existing, DIFFERENT combined result: {dest}')
    else:
        dest.write_bytes(combined)
    manifest['all_generated_sha256'] = digest(combined)
    manifest_path = directory / 'generation_manifest.json'
    serial = (json.dumps(manifest,indent=2)+'\n').encode('utf-8')
    if manifest_path.exists() and manifest_path.read_bytes()!=serial:
        raise ValueError(f'Refusing to overwrite existing, DIFFERENT manifest: {manifest_path}')
    if not manifest_path.exists():
        manifest_path.write_bytes(serial)
    print(f'VALIDATION PASS: {len(all_rows)} genuine model responses, '
          f'5 balanced methods x {len(CROSS_VERSION12)} matched tasks')
    print(f'Combined output: {dest}')
    print(f'Validation manifest: {manifest_path}')
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--directory',default='milestone3/npm_workspaces/cross_version12')
    p.add_argument('--model',default='gemini-3.5-flash')
    opts = p.parse_args()
    combine(Path(opts.directory),opts.model)
