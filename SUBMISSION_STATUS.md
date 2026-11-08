# Assignment #2, first scheduled milestone: submission audit

Date: 2026-11-08. Name: **Azmat Ullah**, 26i-7841.

## Verified complete now

- IEEE-style 5-page research methodology / preliminary results manuscript, PDF and editable LaTeX.
- Abstract, five keywords, introduction, gaps / RQ / objectives alignment, critical related-work comparison, dataset methods, formal retrieval equations, architecture figure, metrics and actual results, limitations, conclusion and complete-author references.
- 18 selected migration examples for three npm packages, 36 authored documentation paraphrases and 36 paired tasks.
- One implemented sparse baseline inspired by DocPrompting's BM25 stage; additional offline dense LSA retriever.
- Dependency metadata resolver and version gate, four-condition evaluation, charts, raw evaluation results.
- 10 passing unit tests; Node.js probe source syntax verified.

## Missing for full formal compliance

1. **Required reproduction of the base paper's actual published results is not complete.** We reimplemented an analogous BM25 stage on a different dataset, not the original Elasticsearch BM25 + tldr/CoNaLa, so no published benchmark number was reproduced. This is the largest academic gap in the original 6-page rubric.
2. The Node.js npm probes were written but NOT executed on real installed npm packages because this environment cannot download packages; no LLM was called or measured.
3. We have not demonstrated an original algorithm beyond exact annotated version metadata filtering; technical novelty still needs to be developed and demonstrated against existing version-aware tools.
4. **Repository URL is now inserted**, but the repository must still be populated with the project files. The connected GitHub account `Mustafa7Khan` has read-only permissions for `azmatullah93/npm-compatibility-aware-rag`, so direct upload through that connection is blocked. Upload via `azmatullah93` or grant collaborator access.
5. **Institutional email added**: `i267841@isb.nu.edu.pk`. The final paper has been recompiled.

## Honest submission description

This is an initial methodology, baseline-component reimplementation, and preliminary retrieval evaluation. It provides genuine evidence for a component of RQ2. RQ1 conflict-sensitivity and RQ3 end-to-end LLM code execution remain planned. It is not correct to claim the full Assignment #2 instructions have been entirely satisfied yet.

## Original DocPrompting comparison

Paper: Shuyan Zhou, Uri Alon, Frank F. Xu, Zhiruo Wang, Zhengbao Jiang, and Graham Neubig. "DocPrompting: Generating Code by Retrieving the Docs", ICLR 2023.

The original paper reports an improvement in generated-code Pass@1 of 2.85 percentage points and Pass@10 of 4.39 percentage points for one Python CoNaLa CodeT5 setting. These **cannot be compared numerically** with our Top-1 retrieval percentages because tasks, measures and model conditions differ.

See `BASELINE_REPRODUCTION.md` for what a true reproduction requires.
