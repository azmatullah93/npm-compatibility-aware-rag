# Official DocPrompting baseline: what has and has not been reproduced

Paper: *DocPrompting: Generating Code by Retrieving the Docs* (Shuyan Zhou, Uri Alon, Frank F. Xu, Zhiruo Wang, Zhengbao Jiang, Graham Neubig), ICLR 2023.

Official implementation: https://github.com/shuyanzhou/docprompting
Official README: https://github.com/shuyanzhou/docprompting/blob/main/README.md

## Published methodology

1. Retrieve relevant API documentation from the natural-language request. The paper explores sparse BM25 (on the Bash tldr benchmark) and CodeT5 dense retrieval (on Python CoNaLa).
2. Add retrieved documentation to the prompt / code generation architecture.
3. Measure generator success on its original benchmarks (execution-based Python Pass@k / Bash exact match).

Official implementation of BM25 uses an Elasticsearch index (`retriever/bm25/main.py` and indexer), not the compact pure-Python BM25 in this project. Its installation expects the original `data/tldr` manuals, a running Elasticsearch instance, and relevant dependency versions. Reproducing the published generation scores also requires the original generator settings and model checkpoints.

## What was done

We implemented the BM25 scoring principle independently, evaluated this on a new 36-question npm retrieval corpus, and added a version compatibility gate. This is a valid *related baseline-component reimplementation* but **NOT a reproduction of DocPrompting's original quantitative results**.

## Why full original reproduction is still pending

- The original Hugging Face / project downloads and npm package registry could not be reached from the authoring environment.
- No Elasticsearch instance was used.
- No original CoNaLa/tldr retriever/generator evaluation or checkpoints were run.
- Our Top-1 and MRR@3 retrieval metrics on a custom corpus are not the same as the paper's published Pass@k or exact-match metrics.

## Required next steps on an internet-enabled research machine

1. Clone `https://github.com/shuyanzhou/docprompting` and check out a recorded revision.
2. Download the datasets, original model checkpoints and tools linked in its README. Record exact package/model versions and downloaded artifact hashes.
3. Run the paper's retrieval pipeline on original tldr or CoNaLa splits, including its original indexer and evaluation method.
4. Reproduce the corresponding original generation experiment when hardware allows.
5. Compare **same** metrics and original dataset/splits against the numbers printed in the paper, and report any deviations.
6. Only after this, report "baseline reproduction" as completed in the paper.

If resources prevent exact replication, write a defensible deviation report and identify the resulting result as an *adaptation*, not a published-score reproduction.
