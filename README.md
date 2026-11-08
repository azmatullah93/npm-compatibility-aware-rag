# Compatibility-Aware Retrieval for Evolving npm APIs

**Azmat Ullah | Registration 26i-7841 | Research Methodology | Assignment #2, first scheduled milestone**

This repository contains an IEEE-style methodology manuscript, a working retrieval-stage pilot, the small controlled dataset, tests, and a prepared Node.js probe script. **It is a preliminary implementation, not a finished LLM code-generation system or a reproduction of DocPrompting's published benchmark scores.**

## What was actually executed

- Built 18 hand-curated breaking-API examples (6 each from Express, Mongoose, React Router), represented as 36 tasks and 36 author-written documentation paraphrases. Source URLs are provided in the dataset.
- Ran four retrieval configurations on all 36 tasks: pure BM25, BM25 plus exact annotated version compatibility, offline LSA latent-semantic retriever, LSA plus the same compatibility gate.
- Executed **10 automated Python unit tests**, all passed at the time of packaging.
- Generated `outputs/extended_results.csv`, `extended_summary.json`, per-task original results, and the actual comparison plot.
- Compiled the IEEE paper with LaTeX.
- `execution/npm_version_probes.cjs` passed `node --check` but **was not executed against installed npm libraries** because the environment cannot download dependencies.

| Retrieval configuration | Correct-document Top-1 | Version-compatible Top-1 |
|---|---:|---:|
| BM25 | 47.2% (17/36) | 50.0% (18/36) |
| BM25 + version gate | 80.6% (29/36) | 100% (36/36) |
| LSA (TF-IDF + truncated SVD) | 41.7% (15/36) | 50.0% (18/36) |
| LSA + version gate | 77.8% (28/36) | 100% (36/36) |

**IMPORTANT:** These results are measured on a small, deliberately version-conflicting, author-labeled retrieval corpus. Version validity is explicitly annotated, not automatically discovered. These are **not** LLM code Pass@1 or real npm API execution results. LSA is a corpus-fitted offline dense-vector baseline, not a pretrained transformer encoder. Our BM25 is a **principle reimplementation** rather than a faithful reproduction of DocPrompting's Elasticsearch system and original CoNaLa/tldr published scores.

## Project layout

```
src/
  build_dataset.py       controlled fixture generation
  retrieval.py           DocPrompting-inspired BM25 and exact-version gate
  dense_retrieval.py     TF-IDF + SVD dense-vector (LSA) retrieval
  metadata.py            exact resolved version from package-lock.json
  evaluate.py            original two-method BM25 pilot
  evaluate_extended.py   four-method paired retrieval comparison
  plot_results.py        original two-method figure
  plot_extended.py       four-method comparison figure

data/
  documents.json         36 author-paraphrased API entries with explicit validity
  tasks.json             36 version-conditioned retrieval questions

tests/
  test_retrieval.py       six original unit tests
  test_extended.py        four additional unit tests

execution/
  npm_version_probes.cjs real pinned npm API probe script: NOT YET RUN

outputs/
  summary.json, retrieval_results.csv, experiment_environment.json
  extended_summary.json, extended_results.csv
  retrieval_comparison.png, retrieval_four_methods.png

paper/
  milestone1.tex         IEEE LaTeX manuscript
  milestone1.pdf         compiled IEEE PDF with repository URL and institutional email

scripts/
  finalize_paper.py      insert real GitHub repo/email and recompile

BASELINE_REPRODUCTION.md
SUBMISSION_STATUS.md
```

## Reproduce retrieval experiments

Python 3.10+ is recommended (the reported experiment used Python 3.13.5, NumPy 2.3.5, scikit-learn 1.8.0). Use a virtual environment for consistency.

```bash
python -m pip install -r requirements.txt
python src/build_dataset.py
python -m unittest discover -s tests -v
python src/evaluate.py
python src/evaluate_extended.py
python src/plot_results.py
python src/plot_extended.py
cd paper
pdflatex -interaction=nonstopmode -halt-on-error milestone1.tex
pdflatex -interaction=nonstopmode -halt-on-error milestone1.tex
```

### Optional: genuine npm package probes

With a working npm internet connection, use Node.js 18+:

```bash
node execution/npm_version_probes.cjs
```

The script installs Express 4.21.2 / 5.1.0 and Mongoose 6.13.8 / 7.8.7 in isolated temporary directories and attempts documented version-sensitive API calls. The output goes to `outputs/npm_version_probe_results.json`. **Do not include those results in a manuscript until the script actually runs.** These probes are not LLM-generated programs.

## First milestone versus the full assignment

The manuscript implements a substantial retrieval-stage component and presents authentic preliminary measurements. The assignment's **full original-paper benchmark reproduction requirement is still open**, and there is no measured LLM generation or installed-npm execution yet. The later scheduled milestones must address these, as explained in `SUBMISSION_STATUS.md` and `BASELINE_REPRODUCTION.md`. Do not state the full Assignment #2 rubric is satisfied.

## Author and repository

Author: **Azmat Ullah**, registration **26i-7841**, institutional email **i267841@isb.nu.edu.pk**.

Source repository: **https://github.com/azmatullah93/npm-compatibility-aware-rag**

The accompanying `paper/milestone1.tex` and `paper/milestone1.pdf` already contain the verified repository URL on the last line of the abstract. **Important:** the files supplied in this archive must actually be uploaded to that GitHub repository before submitting the PDF, and the remote upload has not been performed through this account. See `UPLOAD_TO_GITHUB.md`.

For future changes, the paper can be regenerated with:

```bash
python scripts/finalize_paper.py --github https://github.com/azmatullah93/npm-compatibility-aware-rag --email i267841@isb.nu.edu.pk
```

Upload the **research PDF only** to Google Classroom as requested in the assignment. Keep the code and supporting materials in GitHub.

## Source provenance

Vendor migration guides were used to construct paraphrased fixtures; they are not an independently curated external benchmark or verbatim official doc corpus.

- Express v5 migration: https://expressjs.com/en/guide/migrating-5/
- Mongoose 6 -> 7 migration: https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html
- React Router v5 -> v6: https://reactrouter.com/docs/en/v6/upgrading/v5
- DocPrompting official implementation: https://github.com/shuyanzhou/docprompting
