# Local installed-npm API probe: 27 November 2026

**Status:** User-reported successful run on a Windows machine via Git Bash. The JSON in this directory is a faithful transcription of the 10 observations supplied in the research conversation; it is **not** an independently downloaded CI artifact. The command output and eight passing expectation-checker lines were shared by the researcher.

## Execution described by the researcher

Repository branch: `research/real-npm-probes-and-llm-runner-2026-11-27`.

```bash
node execution/npm_version_probes.cjs
node execution/check_real_probes.cjs
```

Observed: 10 boolean API observations across four exact npm versions (Express 4.21.2 and 5.1.0; Mongoose 6.13.8 and 7.8.7), no reported probe errors, and **8/8** specific documented migration assertions passed.

The probe script checks installed library versions before evaluating the APIs. Four auxiliary `app.del` observations are present, but the checker only asserts eight migration behaviors; do not describe these as **10/10 checker assertions**.

## Interpretation and limitations

The observations show selected version-specific API differences on installed npm releases, not code-generation success, database persistence, model correctness, retrieval improvements, or a completed external-paper reproduction. Mongoose methods were checked for availability and ObjectId construction; no live MongoDB was used. The Express wildcard probe checks whether route registration succeeds, not full HTTP request semantics. These differences motivate but do not validate the proposed retrieval approach.

## Additional provenance to preserve

The probe script also writes these files on the researcher's machine:

- `outputs/npm_version_probe_environment.json` (Node version, OS platform, architecture, exact resolved package versions, run timestamp, and lockfile hashes).
- `outputs/npm_probe_locks/` (four package lockfiles identifying transitive dependencies).
- `outputs/npm_version_probe_results.json` (the machine-produced raw observations).

For stronger conference reproducibility, archive the **machine-produced** environment and lockfile outputs in a separate, explicitly identified capture before claiming an independently reproducible experiment. Do not replace the machine-produced `recorded_at` or hashes with guessed values.

## Hosted CI status

The GitHub Actions attempt on this branch failed **before jobs started** because GitHub reported an account billing lock. It produced no independent package-execution evidence. Local tests can proceed while that account issue is resolved.
