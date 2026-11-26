# Submission audit: Assignment #3 (preliminary)

Verified on November 18, 2026.

## Implemented and measured

- 42-task controlled version-sensitive retrieval corpus (36 migrated cases and 6 stable API cases) from 39 author-authored documentation paraphrases.
- BM25, offline LSA, lockfile version resolver, exact-version filter and explicit per-API range filter.
- Six retrieval conditions on identical tasks; raw outputs, chart, paired exact McNemar tests, cluster-bootstrap intervals.
- 16 Python tests passed; 12 local Node API-emulation cases matched author-specified expectations.
- Provider-compatible prompt/LLM adapter, isolated Docker execution runner implementation and test specifications.
- IEEE conference-format milestone paper with title, abstract, keywords, related work, algorithms and formulas, methodology, experiments, critical limitations, conclusion and full listed author names in references.

## Not implemented/validated (do not claim as completed)

- Faithful published-results reproduction of DocPrompting on original tldr/CoNaLa data.
- Actual model-generated code (only prompt dry-run was completed).
- Real installed-npm test execution; Docker and npm registry unavailable in authoring runtime.
- Independent ground-truth confirmation of stable APIs across target versions.
- Controlled RQ1 code-generation sensitivity to incompatible context, complete RQ3 execution success.
- Neural pretrained dense retriever and broad held-out dataset.

This is a **partial milestone**, with genuine retrieval evidence but not a finished 50-80%-verified end-to-end research system. The count of implemented software modules is not a scientifically meaningful estimate of research completion, so no arbitrary percent-complete claim is made.

## Publishing

The connected GitHub session previously had read-only access to azmatullah93/npm-compatibility-aware-rag; upload these files using the azmatullah93 account or connect with correct write permissions. After upload, confirm the paper link resolves to actual repository contents before submitting its PDF to Google Classroom.
