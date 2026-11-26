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

## Baseline reproduction status

We reimplemented the BM25 scoring component used by DocPrompting, but **not** its official Elasticsearch/tldr pipeline or original generation benchmark scores. See [`BASELINE_REPRODUCTION.md`](../BASELINE_REPRODUCTION.md). Reproducing the published baseline remains required by the instructor's full rubric. The official source is https://github.com/shuyanzhou/docprompting.

## Repository and submission

Keep these files in the existing project repository: https://github.com/azmatullah93/npm-compatibility-aware-rag. Include `milestone3/`, updated `requirements.txt`, and both `paper/milestone3.tex` and `paper/milestone3.pdf`. Upload the updated research **PDF** to Google Classroom. The repository link is the final line of the abstract.
