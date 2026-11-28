"""Audit the controlled 12-task retrieval preview.

This evaluates AUTHOR-ASSIGNED gold labels and validity annotations only.
It does not contact an LLM or execute JavaScript and must not be reported as
independent compatibility verification or generated-code Pass@1.
"""
import argparse
import hashlib
import json
import sys
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'milestone3'))
from generate_code import CROSS_VERSION12, planned_rows

MODES = ('unconstrained', 'exact', 'range')
LABEL = 'author_assigned_document_gold_and_version_validity'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def audit(directory, output=None, model='gemini-3.5-flash'):
    tasks_path = ROOT / 'milestone3' / 'tasks.json'
    docs_path = ROOT / 'milestone3' / 'documents.json'
    tasks_data = tasks_path.read_bytes()
    docs_data = docs_path.read_bytes()
    tasks = json.loads(tasks_data)
    docs = json.loads(docs_data)
    task_by_id = {t['id']:t for t in tasks}
    doc_by_id = {d['id']:d for d in docs}
    if len(task_by_id) != len(tasks) or len(doc_by_id) != len(docs):
        raise ValueError('Duplicate task or document IDs in corpus')
    report = {
        'study':'cross_version12_retrieval_preview',
        'model_for_prompt_only':'gemini-3.5-flash' if model == 'gemini-3.5-flash' else model,
        'basis':LABEL,
        'no_llm_calls':True,
        'task_ids':list(CROSS_VERSION12),
        'tasks_sha256':sha256(tasks_data),
        'documents_sha256':sha256(docs_data),
        'methods':{}
    }
    for mode in MODES:
        file = directory / (mode + '.jsonl')
        raw = file.read_bytes()
        if not raw.endswith(b'\n') or not raw.strip():
            raise ValueError(f'{mode}: missing trailing newline or empty file')
        lines = raw.decode('utf-8').splitlines()
        try:
            rows = [json.loads(line) for line in lines]
        except (ValueError, TypeError) as err:
            raise ValueError(f'{mode}: invalid JSONL') from err
        expected = planned_rows(
            Namespace(suite='cross_version12',limit=None,retriever='bm25',
                      compatibility=mode,model=model,dry_run=True),
            tasks,docs)
        if len(rows) != len(CROSS_VERSION12):
            raise ValueError(f'{mode}: expected {len(CROSS_VERSION12)} rows, got {len(rows)}')
        gold_top1 = 0
        gold_top3 = 0
        outside_validity = 0
        retrieved_count = 0
        missing_gold = []
        per_task = []
        for index, (row, exp) in enumerate(zip(rows, expected),1):
            if not isinstance(row,dict):
                raise ValueError(f'{mode}: expected object at row {index}')
            if row != exp:
                raise ValueError(
                    f'{mode}: row {index} does not match the reproducible, prompt-only '
                    f'retrieval plan (identity, retrieval, or prompts differ)')
            task_id = row['task_id']
            task = task_by_id[task_id]
            hits = row['retrieved_ids']
            if len(hits) > 3 or len(set(hits)) != len(hits):
                raise ValueError(f'{mode}: duplicate or extra retrieved documents on {task_id}')
            unknown = [doc for doc in hits if doc not in doc_by_id]
            if unknown:
                raise ValueError(f'{mode}: unknown document IDs on {task_id}: {unknown}')
            for doc_id in hits:
                if doc_by_id[doc_id]['package'] != task['package']:
                    raise ValueError(f'{mode}: wrong-package document in {task_id}')
            correct = task['correct_doc_id']
            if correct not in doc_by_id:
                raise ValueError(f'{task_id} refers to missing author-assigned gold ID')
            top1 = bool(hits and hits[0] == correct)
            top3 = correct in hits
            invalid = [doc_id for doc_id in hits
                       if task['target_version'] not in doc_by_id[doc_id].get('valid_versions',[])]
            gold_top1 += int(top1)
            gold_top3 += int(top3)
            outside_validity += len(invalid)
            retrieved_count += len(hits)
            if not top3:
                missing_gold.append(task_id)
            per_task.append({'task_id':task_id,'target_version':task['target_version'],
                             'gold_document':correct,'retrieved_ids':hits,
                             'gold_at_1':top1,'gold_at_3':top3,
                             'outside_author_validity':invalid})
        report['methods'][mode] = {
            'n_tasks':len(rows),
            'gold_at_1':gold_top1,
            'gold_at_3':gold_top3,
            'gold_at_1_rate':round(gold_top1/len(rows),6),
            'gold_at_3_rate':round(gold_top3/len(rows),6),
            'retrieved_documents_total':retrieved_count,
            'hits_outside_author_validity':outside_validity,
            'tasks_missing_gold_at_3':missing_gold,
            'preview_sha256':sha256(raw),
            'per_task':per_task
        }
    if output is not None:
        encoded = (json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
        output.parent.mkdir(parents=True,exist_ok=True)
        if output.exists():
            if output.read_bytes() != encoded:
                raise ValueError(f'Refusing to overwrite DIFFERENT retrieval audit: {output}')
        else:
            output.write_bytes(encoded)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',type=Path,
       default=Path('milestone3/npm_workspaces/retrieval_preview'))
    parser.add_argument('--output',type=Path,
       default=Path('milestone3/npm_workspaces/retrieval_preview/audit.json'))
    parser.add_argument('--model',default='gemini-3.5-flash')
    args=parser.parse_args()
    result=audit(args.directory,args.output,args.model)
    print('Retrieval audit: 12 tasks, document labels = AUTHOR-ASSIGNED (not real-API proof)')
    for mode, summary in result['methods'].items():
        print(f"{mode}: gold@1={summary['gold_at_1']}/12, "
              f"gold@3={summary['gold_at_3']}/12, "
              f"outside_author_validity={summary['hits_outside_author_validity']}/"
              f"{summary['retrieved_documents_total']}, "
              f"missing_gold={summary['tasks_missing_gold_at_3']}")
    print('Saved reproducible report:',args.output)
