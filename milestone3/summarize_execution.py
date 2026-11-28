"""Strict aggregation of genuinely executed one-sample-per-task code trials.

This program refuses to calculate Pass@1 when execution results are missing,
only staged, or affected by infrastructure errors. It cannot invent model runs.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def summarize(rows):
    if not rows:
        raise ValueError('No execution observations available')
    by_method = defaultdict(list)
    seen = set()
    for row in rows:
        status = row.get('status')
        if status not in ('PASS', 'FAIL'):
            raise ValueError(f'Unmeasured/invalid trial status {status!r} in {row.get("task_id")}; cannot report Pass@1')
        key = (row.get('model'), row.get('method'), row.get('task_id'))
        if any(not str(x) or x is None for x in key):
            raise ValueError(f'Missing trial identifiers: {key}')
        if key in seen:
            raise ValueError(f'Duplicate single-sample trial: {key}; Pass@1 would be ambiguous')
        seen.add(key)
        by_method[key[:2]].append(row)
    per_model = defaultdict(list)
    result = []
    for (model, method), samples in sorted(by_method.items()):
        tids = {r['task_id'] for r in samples}
        per_model[model].append((method, tids))
        n = len(samples)
        successes = sum(r['status'] == 'PASS' for r in samples)
        result.append({'model': model, 'method': method, 'tested_tasks': n,
                       'passing': successes, 'pass_at_1': round(successes/n, 6)})
    for model, groups in per_model.items():
        if len(groups) > 1:
            reference = groups[0][1]
            for method, tids in groups[1:]:
                if tids != reference:
                    raise ValueError(f'Unequal task coverage across retrieval methods for model {model}: {method}')
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('file', nargs='?', default=str(Path(__file__).with_name('actual_execution_results.json')))
    p.add_argument('--output', default='')
    a = p.parse_args()
    rows = json.loads(Path(a.file).read_text())
    result = summarize(rows)
    rendered = json.dumps(result, indent=2) + '\n'
    if a.output:
        Path(a.output).write_text(rendered)
    print(rendered, end='')

if __name__ == '__main__':
    main()
