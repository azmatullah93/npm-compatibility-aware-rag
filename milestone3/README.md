# Assignment #3: Preliminary Results and Methodology

**Azmat Ullah, 26i-7841, i267841@isb.nu.edu.pk**

This directory extends the prior Assignment #2 research prototype. The Classroom description requires at least **50-80% of the proposed work** to be implemented. We have completed and evaluated the retrieval-specific modules; the full original-paper reproduction and live LLM-generated/npm-executed experiments **are not complete**. Do not describe this as a fully implemented final research system.

## What actually ran

- **39** author-paraphrased API document entries and **42** target-version retrieval tasks, based on three npm libraries and 18 known migration cases plus three hypothesized stable APIs.
- Six paired BM25/LSA retrieval settings: no compatibility filter, exact metadata match, and manually annotated API applicability ranges.
- Six new Python tests and ten earlier tests (**16 total**), plus **12/12** local Node subprocess API-emulation self-tests. The Node self-tests use **local simplified emulations, not installed npm packages**.
- Raw results, six-method chart, and API-family cluster-bootstrap / exact McNemar analysis.
- Four model input prompts generated in **dry-run mode**; **zero actual LLM API calls**.
- A Docker runner for real version-pinned code execution. It was syntax-checked but **not executed** because Docker and npm registry access were unavailable. The original DocPrompting benchmark has **not** been reproduced.

## Install and reproduce the measured offline results

Use Python >=3.10 (experiment was run with Python 3.13.5) and Node.js 22+:

```bash
python -m pip install -r requirements.txt
python src/build_dataset.py
python milestone3/build_extended_dataset.py
python -m unittest discover -s tests -v
python -m unittest discover -s milestone3 -p 'test_*.py' -v
python milestone3/evaluate_stage3.py
python milestone3/paired_analysis.py
python milestone3/plot_stage3.py
node milestone3/fixture_execution_selftest.cjs
node --check milestone3/run_generated_code.cjs
```

All generated measurements are under `milestone3/`. The paper is at `paper/milestone3.pdf` with its LaTeX source at `paper/milestone3.tex`.

## Tested retrieval outcomes

| Method | Correct-document Top-1 | Compatible@1 |
|---|---:|---:|
| BM25 | 18/42 (42.9%) | 61.9% |
| BM25 + exact | 28/42 (66.7%) | 100% |
| BM25 + API range | 28/42 (66.7%) | 100% |
| LSA | 15/42 (35.7%) | 52.4% |
| LSA + exact | 24/42 (57.1%) | 100% |
| LSA + API range | 24/42 (57.1%) | 100% |

The compatibility result uses *hand-supplied* applicability metadata. The experimental improvement is **not evidence of automatic version inference**. Across 42 tasks, the API-range method **does not beat the exact metadata match overall**. Its value on stable APIs is a hypothesis to validate with authentic documents and installed package versions. The three stable APIs are annotated based on author assessments, not package-execution ground truth.

## Optional live LLM code-generation prompts

The following creates input prompts only, **not LLM responses**:

```bash
python milestone3/generate_code.py --dry-run --retriever bm25 --compatibility range --output milestone3/prompts_dry_run.jsonl
```

To actually generate code, set an API key in your local environment and select a real accessible compatible model:

```bash
# Linux/macOS: set OPENAI_API_KEY in the shell (do not put it in this repository)
python milestone3/generate_code.py --model YOUR_MODEL_ID --api-url https://api.openai.com/v1 \
  --retriever bm25 --compatibility range --output milestone3/generated_actual.jsonl
```

This uses an OpenAI-compatible chat-completions endpoint; endpoint support depends on your provider and model. **Never commit `generated_actual.jsonl` if it contains sensitive prompts or data**. The API key is not stored by our program.

## Optional real npm execution: requires Docker and npm internet

Review task specs in `milestone3/execution_specs.json`. The runner installs pinned packages for known tasks. It never executes generated code on the host; when `--run` is used, generated files execute inside a constrained Docker container.

```bash
node milestone3/run_generated_code.cjs --generated milestone3/generated_actual.jsonl --prepare
node milestone3/run_generated_code.cjs --generated milestone3/generated_actual.jsonl --run
```

The result would be saved in `milestone3/actual_execution_results.json`. **Those results do not currently exist in this archive**. Docker is not an absolute security guarantee; run under a disposable development account/VM, without credentials or private folders.

Alternatively, the existing `node execution/npm_version_probes.cjs` checks selected author-specified API differences after installing exact Express and Mongoose versions; these are **not model-generated solutions**.

## Next-stage real npm validation and end-to-end experiment setup (2026-11-27)

An added [GitHub Actions workflow](../.github/workflows/npm-real-api-probes.yml) can download and load **real published releases** of Express 4.21.2 / 5.1.0 and Mongoose 6.13.8 / 7.8.7. It runs the actual probes, checks eight documented behavior expectations, and uploads the raw JSON observations, environment metadata, and dependency lockfiles. The workflow only tests trusted probe code; **it never runs LLM-generated programs on the GitHub runner**.

* [Actions workflow](https://github.com/azmatullah93/npm-compatibility-aware-rag/actions/workflows/npm-real-api-probes.yml)
* Local alternative on an npm-enabled machine:

```bash
node execution/npm_version_probes.cjs
node execution/check_real_probes.cjs
```

The existing 12 Node checks are still **emulations**, not evidence of real package execution. The new `execution/test_probe_checker.cjs` is a checker unit test with synthetic inputs, also not real package evidence. Treat the GitHub Actions run as real only after verifying its result and archived observations. Passing the eight probes validates selected API changes, **not an LLM-generated-code success rate**.

The code-generation harness has also been tightened:

* `--stage` saves candidate code and per-task tests into **separate directories**, but never executes it.
* `--prepare` installs packages with exact versions and scripts disabled.
* `--run` evaluates each candidate within Docker using read-only mounts, no outbound network, bounded CPU/memory, and no secrets. This is for a disposable VM, not a security guarantee.
* `milestone3/test_runner_isolation.cjs` checks that two variants of the same task cannot overwrite one another.
* Express generation tests now send real HTTP requests to a listening app in the container. Mongoose tests use the installed library but spy on the database-facing method calls to avoid requiring a live MongoDB; they therefore **do not test database persistence**.

Prepare one generation output per condition, using a *single* fixed model and matching tasks:

```bash
# These generate prompts only (no LLM API call); remove --dry-run for actual outputs.
python milestone3/generate_code.py --compatibility none --dry-run --output /tmp/no_context.jsonl
python milestone3/generate_code.py --compatibility unconstrained --dry-run --output /tmp/unconstrained.jsonl
python milestone3/generate_code.py --compatibility exact --dry-run --output /tmp/exact.jsonl
python milestone3/generate_code.py --compatibility range --dry-run --output /tmp/range.jsonl
python milestone3/generate_code.py --compatibility oracle --dry-run --output /tmp/oracle.jsonl
```

For **actual generated code**, provide a supported model ID and `OPENAI_API_KEY` in your local environment, remove `--dry-run`, and use distinct output files. Combine these genuine JSONL results (e.g. shell `cat` or Windows PowerShell `Get-Content`) into one file. Then:

```bash
node milestone3/test_runner_isolation.cjs
node milestone3/run_generated_code.cjs --generated REAL_MODEL_OUTPUT.jsonl --stage
node milestone3/run_generated_code.cjs --generated REAL_MODEL_OUTPUT.jsonl --prepare
node milestone3/run_generated_code.cjs --generated REAL_MODEL_OUTPUT.jsonl --run
python milestone3/summarize_execution.py milestone3/actual_execution_results.json
```

The summarizer **refuses to calculate Pass@1** when trials are staged, missing, affected by installation errors, or have different task coverage across retrieval methods. Do not call a synthetic, prompt-only, or staged run an LLM execution experiment. A real-paper evaluation additionally needs multiple models, verified task fixtures, and wider npm package coverage.

## Baseline reproduction status

We reimplemented the BM25 scoring component used by DocPrompting, but **not** its official Elasticsearch/tldr pipeline or original generation benchmark scores. See [`BASELINE_REPRODUCTION.md`](../BASELINE_REPRODUCTION.md). Reproducing the published baseline remains required by the instructor's full rubric. The official source is https://github.com/shuyanzhou/docprompting.

## Repository and submission

Keep these files in the existing project repository: https://github.com/azmatullah93/npm-compatibility-aware-rag. Include `milestone3/`, updated `requirements.txt`, and both `paper/milestone3.tex` and `paper/milestone3.pdf`. Upload the updated research **PDF** to Google Classroom. The repository link is the final line of the abstract.

## Express evaluation harness fix (2026-11-28)

During the first Gemini-generated Express 5.1.0 trial, the researcher observed an initial Docker daemon connection failure, then a `DOCKER_TIMEOUT`, then a trusted manual Docker diagnostic failed with `TypeError: Cannot read properties of null (reading 'port')`. The latter error came from **the test harness** calling `server.address().port` immediately after `app.listen()`, before the asynchronous `'listening'` event. This is **not an LLM failure** and neither trial is a valid Pass@1 observation.

Both Express task specifications now await `once(server, 'listening')`, verify the assigned port, and bound localhost HTTP requests to 5 seconds. The trusted regression check `node milestone3/test_http_spec_contract.cjs` verifies source ordering and native HTTP readiness, but **does not run a model-generated solution**.

After pulling this fix, rerun the **unchanged existing** `milestone3/generated_actual.jsonl` through `--run` (and `--prepare` only if dependencies have gone missing). Record success or failure solely from the fixed harness results. Keep the earlier infrastructure/test failures out of generated-code correctness statistics.
