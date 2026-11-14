# Appuscholar randomisation engine

Reference implementation for the randomisation methods used in the study
record (see `claude/appuscholar-randomisation-sequence-and-software-plan-2026-11-14.md`
and `claude/appuscholar-randomisation-placement-in-app-2026-11-14.md` in the
project docs, outside this repo).

- `randomise.py` — the Python engine: commitment, simple, permuted blocks,
  stratified blocks, minimisation, matched pairs, constrained randomisation,
  Williams rows and cross-over, plus the audit record and verification.
- `alloc.js` — a JavaScript port with the same algorithm (HMAC-keyed counter
  stream, rejection sampling, Fisher–Yates), checked against the same test
  vectors as the Python engine.
- `test_randomise.py`, `test_alloc.js`, `vectors.json` — the shared test
  vectors. Run `python3 test_randomise.py` and `node test_alloc.js`; both
  must pass before either file changes.

`index.html` carries its own small copy of the simple and permuted-block
methods (functions prefixed `al`), used by the in-app allocation runner.
That copy is checked against these same vectors in
`tests/test_allocation_runner.py`. The other methods here (stratified
blocks, minimisation, matched pairs, constrained randomisation, Williams
rows, cross-over) are not yet in the app and still have to be run from the
command line with this engine.

Commitment is versioned:
- v1: `SHA-256("appuscholar-commit-v1:" + seed)`.
- v2: `SHA-256("appuscholar-commit-v2:" + seed + plan_sha256)`, binding the
  registered plan into the commitment. This is what `index.html` writes now.
  `verify()` in `randomise.py` reads `record["commitment_version"]` and
  checks whichever formula the record used, so old v1 records still verify.

The seed must never be committed, logged, or stored in the study record.
Keep it in a file outside this repository and outside the app's storage.
