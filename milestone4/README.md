# Milestone 4: cross-version benchmark extension

This is a **controlled expansion from 4 to 12 executable tasks**, *not* a completed new model evaluation. See [PROTOCOL.md](PROTOCOL.md) for the research question, provenance, evaluation contract, and validity limitations.

## A. Preflight: REQUIRED before calling any LLM

From the repository root in Git Bash on Windows:

```bash
git pull --ff-only origin research/real-npm-probes-and-llm-runner-2026-11-27
python -m unittest discover -s tests -v
python -m unittest discover -s milestone3 -p "test_*.py" -v
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
  python milestone3/generate_code.py --suite cross_version12 --model gemini-3.5-flash --api-url https://generativelanguage.googleapis.com/v1beta/openai --retriever bm25 --compatibility "$mode" --output "milestone3/npm_workspaces/cross_version12/${mode}.jsonl" || break
done
```

Free-tier quota may interrupt a batch. Stop on an API error. Check that each method has 12 valid JSONL lines before combining; **never** concatenate partial data and then call it a complete experiment. Subsequent retry attempts should be recorded as extra attempts, not quietly substituted.

```bash
wc -l milestone3/npm_workspaces/cross_version12/{none,unconstrained,exact,range,oracle}.jsonl
cat milestone3/npm_workspaces/cross_version12/{none,unconstrained,exact,range,oracle}.jsonl > milestone3/npm_workspaces/cross_version12/all_generated.jsonl
```

## C. Execute unchanged model outputs, then summarize

```bash
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/cross_version12/all_generated.jsonl --stage --accept-named-export --output milestone3/npm_workspaces/cross_version12/staged.json
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/cross_version12/all_generated.jsonl --prepare --accept-named-export --output milestone3/npm_workspaces/cross_version12/prepared.json
node milestone3/run_generated_code.cjs --generated milestone3/npm_workspaces/cross_version12/all_generated.jsonl --run --accept-named-export --output milestone3/npm_workspaces/cross_version12/results.json
python milestone3/summarize_execution.py milestone3/npm_workspaces/cross_version12/results.json
```

The strict summarizer refuses incomplete, missing, duplicate or infrastructure-errored trials. The model is NOT expected to pass all tasks; genuine failures are retained unchanged. The original `pilot20` directory and its 17/20 strict, 19/20 post-hoc sensitivity results remain separate and immutable.

## D. Longer-term conference evaluation

After the 12-task dry-run, prioritize **authentic versioned documentation**, multiple independently validated npm packages and old/new releases, database-backed Mongoose behaviors, task-level error taxonomy, at least two more model families (OpenAI and Anthropic) with the same held-out tasks, and repeated trials with paired statistics. This pilot is not itself a high-quality conference benchmark.
