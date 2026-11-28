# Cross-version 12-task expansion: experiment protocol

**Status:** Preliminary protocol and code fixtures prepared on 2026-11-28, after the four-task exploratory pilot. **No cross_version12 LLM generation or Docker results have been observed yet.** Treat this as a prospective small benchmark pilot, not as a registered complete conference evaluation.

## Research question

Does API-range-aware retrieval reduce genuine cross-version npm API errors relative to (i) no retrieved documentation, (ii) unconstrained BM25, and (iii) exact document-release filtering, with (iv) oracle-document retrieval only as a reference condition? The primary reported outcome is **behavioral executable correctness on pinned package versions**, not merely whether the method retrieves its own author-written label.

## Fixed suite and package versions

`--suite pilot4` preserves the four tasks used in the 2026-11-28 Gemini pilot. `--suite cross_version12` expands to twelve fixed IDs in the order defined in `milestone3/generate_code.py`:

- **Express 4.21.2 / 5.1.0:** wildcard catch-all paths, DELETE routes, stable `GET /health` endpoint (six tasks).
- **Mongoose 6.13.8 / 7.8.7:** deletion of all matching records, update of exactly one record, stable `Model.findById` (six tasks).

Four of the twelve are stable-API targets. The `express-basic-route-shared` and `mongoose-findbyid-shared` author-paraphrased documents have an **older** document version tag but manually assigned ranges spanning both major versions. These are intentionally diagnostic of the **exact-tag vs applicability-range** distinction. They are not randomly sampled from the npm ecosystem and should not be used to claim population-level effects.

The package-lock version fields in the dataset are *target-version declarations*, not independently downloaded full lockfile evidence. The Docker `--prepare` and `--run` stages check that the installed library's own `package.json` matches the target version; save actual generated npm lockfiles and environment metadata before publication.

## Methods and primary evaluation

1. No retrieval (`bm25_none`).
2. Ordinary unfiltered BM25 (`bm25_unconstrained`).
3. Exact-version BM25 (`bm25_exact`).
4. Author-labeled API-applicability-range BM25 (`bm25_range`).
5. Oracle selected document (`bm25_oracle`); not a deployable method.

For every condition, use the **same twelve tasks, one fixed model ID, a fixed prompt and retrieval configuration, and the same test suite**. The Gemini API requests temperature zero, which does **not** guarantee bitwise deterministic outputs. Record model ID, actual model response, condition, document IDs, target version, generation settings and timestamp; retain failed solutions unmodified.

**Primary outcome for this expansion:** correct execution in Docker with the **predeclared, export-compatible** interface rule `--accept-named-export` (a directly callable CommonJS function or an object containing a callable `setup`). Do not mix primary export-compatible numbers with historical strict-only pilot numbers. Keep strict-only scoring as a documented sensitivity comparison if rerun. Do not modify candidates after generation.

**Report separately:** incorrect/missing exports, syntax errors, runtime API incompatibilities, assertion failures, and infrastructure errors; do not count infrastructure errors as model failures. The current runner's `PASS`/`FAIL` covers executable behavior, not a fully automated taxonomy; inspect errors before categorizing.

All untrusted model-generated source runs **only in isolated Docker containers**, never through host Node or the shell. Docker is defense-in-depth and not a complete security boundary; prefer a disposable VM and never mount credentials. The trusted human-authored preflight fixtures are NOT LLM results.

## Preflight gate before spending model quota

```bash
python -m unittest discover -s milestone3 -p "test_*.py" -v
node milestone3/test_export_contract.cjs
node milestone4/build_reference_trials.cjs
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/reference12/golden.jsonl --prepare --accept-named-export --output milestone3/npm_workspaces/reference12/prepared.json
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/reference12/golden.jsonl --run --accept-named-export --output milestone3/npm_workspaces/reference12/results.json
```

**Require 12/12 reference fixture `PASS` with no timeout before running any cross_version12 model generation.** If fixtures fail, inspect the preflight results and fix problems with the test harness while retaining the change history. Reference fixtures may be flawed and are not independently verified solely by having been written.

## Model-generated run

Generate one condition per file with:
`python milestone3/generate_code.py --suite cross_version12 --model gemini-3.5-flash --api-url https://generativelanguage.googleapis.com/v1beta/openai --retriever bm25 --compatibility RANGE_OR_BASELINE --output milestone3/npm_workspaces/cross_version12/METHOD.jsonl`.
Do not use `--dry-run` for real generation. Respect API quota; don't repeatedly retry completed calls without recording the resulting extra sample. Combine only after exactly twelve genuine responses for each of five conditions, 60 distinct (method,task) pairs; then `--stage`, `--prepare`, `--run --accept-named-export`, and `summarize_execution.py` on the full results. Archive raw outputs, package/version lockfiles, code hashes, environment and dates before conference submission.

## Scientific limits and next stages

- **Source fidelity:** current 39 document snippets are **author paraphrases**, not an authentic versioned documentation corpus. `valid_range` values are **hand-labelled**, not automatically inferred. The next benchmark must extract traceable, version-specific documents and independently validate compatibility claims.
- **Behavioral strength:** Express checks send real HTTP requests against installed Express; Mongoose tests use installed Mongoose methods with database-facing spies and therefore do **not** establish MongoDB persistence. Add database-backed tests for representative Mongoose tasks.
- **Selection:** twelve curated tasks are a targeted pilot and may favor the mechanism under test; diversify to additional libraries, patch releases, and naturally occurring migrations, including *negative controls* and situations where range retrieval is wrong.
- **Replication:** a full-paper study should preregister the metric and experiment split, use multiple model families and repeated generations, report paired task-level deltas with clustered/bootstrapped confidence intervals, and reproduce a published retrieval baseline where feasible. Do not claim statistical significance on 12 tasks.
- **Outcomes:** preserve results whether range-aware BM25 wins, ties or loses. A well-supported null or mixed finding is preferable to selective reporting.

Relevant vendor documentation consulted to define candidate migration tasks:
- https://expressjs.com/en/guide/migrating-5/
- https://expressjs.com/en/4x/guide/routing/
- https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html
