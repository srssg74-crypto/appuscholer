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
blocks, minimisation, matched pairs, constrained randomisation, the cluster methods, Williams
rows, cross-over) are not yet in the app and still have to be run from the
command line with this engine.

## Cluster trials

The units are schools, wards or clinics, and the whole list is known before
anything is allocated, so these methods allocate it in one pass. Both engines
give identical results (see the `clusters`, `constrained` and
`constrained_odd` entries in `vectors.json`).

- `stratified_clusters` — one or several factors; strata are the combinations
  of levels. Each stratum splits as evenly as its size allows; spare clusters
  go to the arms with the fewest so far, so overall counts stay within one.
- `cluster_minimisation` — Pocock and Simon style, on cluster counts and, with
  a `weight` (cluster size), on participant numbers too. Balances overall and
  within every factor level. Does not guarantee balance with few clusters.
- `constrained_clusters` — two arms; random candidates are drawn until one
  meets rules written as data (`mean_diff`, `count_diff`). For fewer than
  about 20 clusters. All `tries` candidates are drawn so the result can say how
  many different allocations qualified (`acceptable_seen`); under 100 gives the
  warning `narrow_choice`, meaning the rules leave too small a set to randomise
  from. Raises if no candidate qualifies.

Shared rules (inputs that would let the engines disagree are refused in both:
lone surrogates in text, whole numbers beyond 2^53, a non-list `arms`, a
non-numeric `p_best`; levels `1` and `"1"`, or `true` and `"true"`, are the same
level; weights are summed left to right so Python 3.12 and JavaScript agree on
fractional sizes): the result depends on the seed and the set of clusters, never on
the order they were typed (ids are sorted by UTF-8 bytes first). Numeric
factors are cut with `bins` (cut points; a value on a cut goes up). Weights
must be between 0.001 and 1e9. Results hold lists of pairs, never objects keyed
by data. Warnings (`stratum_missing_arm`, `strata_too_fine`,
`level_single_cluster`) report designs too thin to balance; read them.

Commitment is versioned:
- v1: `SHA-256("appuscholar-commit-v1:" + seed)`.
- v2: `SHA-256("appuscholar-commit-v2:" + seed + plan_sha256)`, binding the
  registered plan into the commitment. This is what `index.html` writes now.
  `verify()` in `randomise.py` reads `record["commitment_version"]` and
  checks whichever formula the record used, so old v1 records still verify.

The seed must never be committed, logged, or stored in the study record.
Keep it in a file outside this repository and outside the app's storage.
