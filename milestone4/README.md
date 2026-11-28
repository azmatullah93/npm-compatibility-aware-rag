# Milestone 4: cross-version benchmark extension

This is a **controlled expansion from 4 to 12 executable tasks**, *not* a completed new model evaluation. See [PROTOCOL.md](PROTOCOL.md) for the research question, provenance, evaluation contract, and validity limitations.

## A. Preflight: REQUIRED before calling any LLM

From the repository root in Git Bash on Windows:

```bash
git pull --ff-only origin research/gemini-cross-version-resume-2026-11-28
python -m unittest discover -s tests -v
python -m unittest discover -s milestone3 -p "test_*.py" -v
python -m unittest discover -s milestone4 -p "test_*.py" -v
node --check milestone4/build_reference_trials.cjs
node --check milestone3/run_generated_code.cjs
node milestone3/test_export_contract.cjs
node milestone3/test_http_spec_contract.cjs
docker info --format '{{.ServerVersion}}'
node milestone4/build_reference_trials.cjs
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/reference12/golden.jsonl --stage --accept-named-export --output milestone3/npm_workspaces/reference12/staged.json
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/reference12/golden.jsonl --prepare --accept-named-export --output milestone3/npm_workspaces/reference12/prepared.json
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/reference12/golden.jsonl --run --accept-named-export --output milestone3/npm_workspaces/reference12/results.json
```

The final run must show exactly **12 PASS and no other status**. If not, stop and diagnose the particular reference task before generating model code. These are *human-authored fixtures* and must never be counted toward Pass@1 of any model.

## B. Generate with Gemini (only after a clean preflight)

The Gemini key belongs only in the current private Git Bash environment. Never paste, commit, log or share it.

```bash
read -r -s -p "Gemini API key: " OPENAI_API_KEY
echo
export OPENAI_API_KEY

mkdir -p milestone3/npm_workspaces/cross_version12
for mode in none unconstrained exact range oracle; do
  echo "Generating condition: $mode"
  python milestone3/generate_code.py --suite cross_version12 --model gemini-3.5-flash --api-url https://generativelanguage.googleapis.com/v1beta/openai --retriever bm25 --compatibility "$mode" --resume --output "milestone3/npm_workspaces/cross_version12/${mode}.jsonl" || break
done
```

If the API returns HTTP 429, **stop generation immediately**. Look at [AI Studio rate limits](https://aistudio.google.com/rate-limit) for the exact project/model RPM, TPM and RPD limits. The code now prints any supplied quota ID, metric and retry hint without displaying the key. A per-minute limit may clear with time; a per-day limit resets according to Google quota policy (normally midnight Pacific). Do not work around a per-project limit by creating additional API keys in the same project or silently switching models midway through a paired experiment.

To inspect any successfully saved partial conditions without trying another API call:

```bash
python -c "from pathlib import Path; d=Path('milestone3/npm_workspaces/cross_version12'); [(print(m, sum(1 for line in (d/(m+'.jsonl')).open(encoding='utf-8') if line.strip()) if (d/(m+'.jsonl')).exists() else 0)) for m in ['none','unconstrained','exact','range','oracle']]"
```

Free-tier quota may interrupt a batch. Stop on an API error. Each finished response is flushed to disk. The new `--resume` flag checks that the saved tasks, model, retrieval setting and prompts are an exact prefix and appends only missing generations. Run the **same command** after the quota clears; do not alter the model or prompt configuration during a partial run. Without `--resume`, an existing file is protected from overwrites by default. `--overwrite` is an explicit destructive option and must not be used for primary research results.

```bash
wc -l milestone3/npm_workspaces/cross_version12/{none,unconstrained,exact,range,oracle}.jsonl
python milestone4/validate_generated.py --directory milestone3/npm_workspaces/cross_version12 --model gemini-3.5-flash
```

## C. Execute unchanged model outputs, then summarize

```bash
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/cross_version12/all_generated.jsonl --stage --accept-named-export --output milestone3/npm_workspaces/cross_version12/staged.json
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/cross_version12/all_generated.jsonl --prepare --accept-named-export --output milestone3/npm_workspaces/cross_version12/prepared.json
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/cross_version12/all_generated.jsonl --run --accept-named-export --output milestone3/npm_workspaces/cross_version12/results.json
python milestone3/summarize_execution.py milestone3/npm_workspaces/cross_version12/results.json
```

The strict summarizer refuses incomplete, missing, duplicate or infrastructure-errored trials. The model is NOT expected to pass all tasks; genuine failures are retained unchanged. The original `pilot20` directory and its 17/20 strict, 19/20 post-hoc sensitivity results remain separate and immutable.

## D. Independently audit retrieval-only preview (zero API calls)

Only run after preparing `--dry-run` previews for all three modes `unconstrained`, `exact`, and `range`. Their raw files must stay unchanged. The checker requires **exact matching task identities, model IDs, prompt text and retrieved document IDs** relative to the local frozen 39-document dataset.

```bash
python -m unittest discover -s milestone4 -p "test_*.py" -v
python milestone4/audit_retrieval.py --directory milestone3/npm_workspaces/retrieval_preview --output milestone3/npm_workspaces/retrieval_preview/audit.json --model gemini-3.5-flash
```

The report contains per-task retrieval traces, exact source SHA-256 hashes, gold-document recall and counts outside **author-assigned** valid versions. It refuses to overwrite a different existing audit. **It is not model-generated execution accuracy or independent compatibility verification.** For user-observed 2026-11-28 pilot results and limitations see [EXPLORATORY_FINDINGS_2026-11-28.md](EXPLORATORY_FINDINGS_2026-11-28.md).

## E. Independent installed-release API probes (zero Gemini calls)

After the 12 human-authored reference programs pass and the exact npm versions are
installed locally, run the following **trusted author-written** capability checks:

```bash
node --check milestone4/probe_release_behavior.cjs
node milestone4/test_release_behavior.cjs
node milestone4/probe_release_behavior.cjs
```

The probe imports the four pinned releases from the same local prepared npm
workspaces: Express `4.21.2` / `5.1.0` and Mongoose `6.13.8` / `7.8.7`.
It uses real HTTP requests to check Express old/new wildcard routes and the
stable `/health` route; verifies removed `app.del`, Mongoose `Model.remove`
and `Model.update` availability; checks the presence of `Model.findById`,
`deleteMany`, `updateOne`, and the behavior of ObjectId construction.
Each old/new release is checked for **both positive and negative controls**.
The tool neither imports any model-generated solution nor uses any source labels
from the retrieval corpus. Expected summary is **26/26 capability checks passed**;
this expectation is NOT a measured result until a real run succeeds.

Raw observation record (environment, exact versions, lockfile hashes, individual
observed values, explicit expectations, source URLs) is saved to
`milestone3/npm_workspaces/release_behavior_probes.json`; a previous differing
record is archived in `release_behavior_probe_history/` before replacement.
Do not commit or leak any secrets in captured environment data.

**Limits:** This independently probes behavior in **four exact installed npm
releases**, not every version covered by the author's `valid_range` labels;
Mongoose assertions do not connect to MongoDB or validate database persistence;
the capability cases are a deliberately curated subset of the much broader npm
API surface. Record this evidence separately from retrieval-label accuracy and
LLM executable-code accuracy. For source context see the official
[Express 5 migration guide](https://expressjs.com/en/guide/migrating-5/) and
[Mongoose 7 migration guide](https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html).

## F. Archive the partial 24-execution experiment (zero API calls)

The first two methods were both successfully executed by the researcher on 2026-11-28.
**Back up their original raw evidence immediately**, independently of completing the
other three methods. From the repo root, after generating the retrieval audit and
release behavior probe:

```bash
python -m unittest discover -s milestone4 -p "test_*.py" -v
python milestone4/archive_pilot_evidence.py --check-only
python milestone4/archive_pilot_evidence.py
```

The archive script validates all 24 model responses against task IDs, versions,
original per-condition JSONL, actual Docker result status, accepted export contract,
and generated-code SHA-256; checks the retrieval audit against original corpus
and preview hashes; and checks all 26 real-package probes and their four exact
npm lockfile hashes. The local ZIP embeds an evidence manifest and does not
overwrite an existing archive.

Output: `milestone3/npm_workspaces/archives/gemini_pilot_evidence_2026-11-28.zip`.
**Keep a separate local backup** (e.g. on an external drive) so that ignored npm
workspaces do not disappear during repo cleanups. The ZIP includes raw model
outputs, prompts, and source files: **inspect it for sensitive data before
sharing**. It does **not** include all `node_modules` trees, the external API
project configuration, Google quota state or a MongoDB service and is therefore
a portable evidence snapshot, not a fully self-contained environment image.
The three ungenerated methods remain unfilled; this archive contains no
fabricated or imputed LLM results.

## G. Longer-term conference evaluation

After the 12-task dry-run, prioritize **authentic versioned documentation**, multiple independently validated npm packages and old/new releases, database-backed Mongoose behaviors, task-level error taxonomy, at least two more model families (OpenAI and Anthropic) with the same held-out tasks, and repeated trials with paired statistics. This pilot is not itself a high-quality conference benchmark.
