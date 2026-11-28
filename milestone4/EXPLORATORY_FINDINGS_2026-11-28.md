# Exploratory findings, 2026-11-28: Gemini cross-version 12-task pilot

**Source:** Researcher's local Git Bash outputs in the project conversation, supplied on 2026-11-28. These are **reported observations** from the researcher's machine, not results reproduced in CI or independently executed in the GitHub environment. The raw candidate JSONL and Docker result JSON remain **local in ignored `milestone3/npm_workspaces/` directories** and should be archived with checksums before any paper submission.

**Status:** Exploratory pilot only. The five-condition, 60-trial code-generation comparison is INCOMPLETE. The older four-task 20-trial pilot is separate and uses a different originally strict export contract; do not pool its outcomes with these.

## A. Preflight and generated-code execution (observed)

- Python regression suites: 10 existing tests passed, 22 milestone3 tests passed, and 4 milestone4 synthetic validation tests passed (at the time of observation). All 12 human-authored reference implementations passed against real, pinned npm packages in Docker, with the preregistered `--accept-named-export` runner option.
- Gemini requested model ID: `gemini-3.5-flash`. Model outputs came through Google's OpenAI-compatible endpoint. The Google API **project/key changed partway through the generation process**, and several requests returned HTTP 429 and 403. Do not claim fully identical provider configuration across samples until model-reported metadata is reviewed.
- Exactly two completed twelve-task conditions were executed unchanged in Docker with the export-compatible contract:

| Method | Executable passes | Reported success rate |
| --- | ---: | ---: |
| No retrieved evidence (`bm25_none`) | 11/12 | 91.67% |
| Unfiltered BM25 (`bm25_unconstrained`) | 12/12 | 100% |

This is **one paired generation per task and method**, not repeated independent trials. These samples are too few for a claim of significance. There is no completed `exact`, `range`, or `oracle` code-generation score yet.

The one failing program used Express 5.1.0 and a catch-all route registered as `app.get('(.*)', ...)`. Real Express 5 rejected this **string** route with `PathError: Unexpected ( at index 0: (.*)`. The corresponding unfiltered BM25 program generated `app.get('/{*splat}', ...)` and passed. Both exports met the accepted interface. The BM25 prompt contained three retrieved snippets: `express-wildcard-old`, `express-wildcard-new`, and `express-basic-route-shared`. This supports a specific observed mismatch, **not** causation or superiority of range-based retrieval.

## B. Offline retrieval-only audit (observed)

Twelve predefined tasks, retrieved three documents per task and condition. The benchmark corpus contains **39 author-written/paraphrased document snippets** and **42 author-designed retrieval tasks** (only 12 are executable in this expansion).

| Retrieval method | Author-selected gold at rank 1 | Gold in top 3 | Hits outside author-labeled valid versions | Missing gold in top 3 |
| --- | ---: | ---: | ---: | ---: |
| Unfiltered BM25 | 7/12 | 11/12 | 15 | 1 task: `mongoose-remove-task-old` |
| Exact-version BM25 | 8/12 | 10/12 | 0 | 2 tasks: `express-basic-route-task-new`, `mongoose-findbyid-task-new` |
| Author-annotated API-range BM25 | 10/12 | 12/12 | 0 | none |

**Validity caveat:** The `valid_versions` labels, `valid_range` annotations, and `correct_doc_id` labels are authored in the same controlled corpus. Range filtering explicitly uses authored validity ranges. Accordingly, **zero invalid hits are partly a construction property, not an external assessment**. Some test cases deliberately use shared old-release documentation where range-aware retrieval should beat an exact-release-tag filter. Metrics should be described as controlled/diagnostic behavior, not independent evidence of a deployable automatic compatibility inference algorithm. Compare to externally verified npm versions and genuine versioned docs in a later benchmark.

## C. Requirements before conference claims

1. Preserve raw local generated outputs, retrieval previews, Docker logs, lockfiles and environment metadata; compute SHA-256 hashes. The scripts in this branch can create a reproducible retrieval audit and paired 60-response generation manifest when available.
2. Finish all three remaining `exact`, `range`, `oracle` code-generation conditions without substituting models or silent re-generation. Keep primary outcomes separate from post-hoc changes.
3. Use **authentic traceable documentation** with independent validity testing on real packages; add versions where exact-version docs are available and cases where cross-version reuse is not beneficial.
4. Add more independent npm packages, realistic tasks, and harder tests including database-backed Mongoose semantics. Prevent exposure to test assertions or gold labels through model prompts.
5. Repeat runs for each model, maintain identical prompts/retrieval configurations across providers where feasible, report per-task matched differences and confidence intervals. Quantify model variance and ceiling effects. Reproduce and properly attribute one published retrieval baseline.
6. Report mixed or null results faithfully. **Neither scientific quality nor publishability requires the proposed method to win in every comparison.**

Official background: https://expressjs.com/en/guide/migrating-5/ ; https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html
