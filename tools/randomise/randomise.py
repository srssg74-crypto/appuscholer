"""
Appuscholar randomisation engine, version 1.0.0.

Every allocation is derived from one secret seed. Before enrolment starts,
publish the commitment (SHA-256 of the seed). After enrolment, reveal the seed.
Anyone can then re-run the program and check that the allocation list matches
the hash in the audit record. Changing one allocation after the fact breaks
the match.

Standard library only. Python 3.9 or later.

Limits, stated plainly:
- "Proof" here means reproducible and auditable. It does not mean the trial is
  unbiased. Bias comes from how people are enrolled and how allocations are
  hidden, and the code cannot see that.
- Each allocation method reads from its own labelled stream. Changing the
  number of strata, for example, does not shift the sequence of any other stratum.
- Minimisation and constrained randomisation need the study rules fixed in the
  protocol before the first participant enrols.
"""

import csv
import hashlib
import hmac
import itertools
import json
import math
import os
import secrets
from collections import defaultdict
from datetime import datetime, timezone

VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Deterministic random stream
# ---------------------------------------------------------------------------

class HashStream:
    """Byte stream from SHA-256 in counter mode, keyed by the seed and a label.

    Same seed and label always give the same numbers, on any machine.
    """

    def __init__(self, seed: bytes, label: str):
        self._key = hmac.new(seed, label.encode("utf-8"), hashlib.sha256).digest()
        self._counter = 0
        self._buf = b""

    def _fill(self, need: int) -> None:
        while len(self._buf) < need:
            block = hashlib.sha256(self._key + self._counter.to_bytes(8, "big")).digest()
            self._buf += block
            self._counter += 1

    def _next64(self) -> int:
        self._fill(8)
        value = int.from_bytes(self._buf[:8], "big")
        self._buf = self._buf[8:]
        return value

    def randbelow(self, n: int) -> int:
        """Uniform integer in 0..n-1, without modulo bias (rejection sampling)."""
        if n <= 0:
            raise ValueError("n must be positive")
        limit = (2 ** 64 // n) * n
        while True:
            x = self._next64()
            if x < limit:
                return x % n

    def uniform(self) -> float:
        """Uniform float in [0, 1)."""
        return self._next64() / 2 ** 64

    def shuffle(self, items):
        """Fisher–Yates shuffle. Returns a new list."""
        items = list(items)
        for i in range(len(items) - 1, 0, -1):
            j = self.randbelow(i + 1)
            items[i], items[j] = items[j], items[i]
        return items


def new_seed() -> bytes:
    """Fresh 256-bit seed from the operating system's secure source."""
    return secrets.token_bytes(32)


def commitment(seed: bytes) -> str:
    """v1: publish this before enrolment. It reveals nothing about the seed."""
    return hashlib.sha256(b"appuscholar-commit-v1:" + seed).hexdigest()


def plan_hash(plan) -> str:
    """SHA-256 of the canonical JSON of the registered plan."""
    return hashlib.sha256(_canonical(plan)).hexdigest()


def commitment_v2(seed: bytes, plan_sha256: str) -> str:
    """v2: binds the seed and the registered plan together."""
    return hashlib.sha256(b"appuscholar-commit-v2:" + seed + bytes.fromhex(plan_sha256)).hexdigest()


def _canonical(obj) -> bytes:
    # ensure_ascii=False: a plan field in Hindi (maker/holder names, params notes) must hash the
    # same way here as in the browser and alloc.js, which both keep non-ASCII text as literal
    # UTF-8 bytes. json.dumps's default ensure_ascii=True instead escapes it to \uXXXX, which
    # hashes to a different value for the exact same plan - a commitment made from a bilingual
    # plan could never be reproduced from this engine.
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


# ---------------------------------------------------------------------------
# Allocation methods
# ---------------------------------------------------------------------------

def simple(seed: bytes, n: int, arms, probs=None):
    """Unrestricted (simple) randomisation. Use for large trials."""
    stream = HashStream(seed, "simple")
    arms = list(arms)
    if probs is None:
        probs = [1 / len(arms)] * len(arms)
    if abs(sum(probs) - 1) > 1e-9:
        raise ValueError("probabilities must sum to 1")
    cum = []
    total = 0.0
    for p in probs:
        total += p
        cum.append(total)
    out = []
    for _ in range(n):
        u = stream.uniform()
        for arm, c in zip(arms, cum):
            if u < c:
                out.append(arm)
                break
        else:
            out.append(arms[-1])
    return out


def default_blocks(k: int):
    """Default block sizes for k arms: 2k, 3k, 4k. [4, 6, 8] for two arms, [6, 9, 12] for three.

    A fixed (4, 6, 8) default only fits two arms (second review, finding 5)."""
    return [2 * k, 3 * k, 4 * k]


def stratum_label(s):
    """One string per stratum, the same in both engines.

    Third review: str(x) and JS String(x) differ for floats, None, lists and large numbers
    (1.0 -> "1.0" vs "1"; None -> "None" vs "null"), and a different label keys a different
    HMAC stream, so the engines would allocate differently. Only strings, ints and bools are
    accepted; anything else is a protocol error, raised here and in alloc.js alike."""
    if isinstance(s, bool):
        return "true" if s else "false"
    if isinstance(s, int) and abs(s) < 2 ** 53:
        return str(s)  # JS refuses integers past 2**53 (Number.isSafeInteger), so this does too
    if isinstance(s, float) and s.is_integer() and abs(s) < 2 ** 53:
        return str(int(s))  # JSON "1.0" reaches JS as the number 1, so it is "1" here too
    if isinstance(s, str):
        return s
    raise ValueError(f"stratum label must be a string or whole number, got {type(s).__name__}: {s!r}")


def _block_generator(stream: HashStream, arms, block_sizes):
    """Endless stream of arm labels, in randomly ordered blocks of random size."""
    arms = list(arms)
    k = len(arms)
    sizes = list(block_sizes) if block_sizes is not None else default_blocks(k)
    if not sizes:
        raise ValueError("block sizes must be a non-empty list")
    sizes = [int(b) if isinstance(b, float) and b.is_integer() else b for b in sizes]
    for b in sizes:
        # review finding 12: 0 % k == 0, so a block size of 0 used to pass this check. With only
        # size-0 blocks, the while loop below would then spin forever choosing size 0 and never
        # reaching `yield` - a silent hang with no error, rather than failing fast at validation.
        # Second review: NaN and floats must fail here too, as they now do in alloc.js.
        # A float that is a whole number (6.0, as JSON may carry it) is accepted as that whole
        # number, the same as JS, where 6.0 and 6 are one value. A cap of 10000 stops a typo from
        # shuffling a block the size of a city.
        if isinstance(b, float) and b.is_integer():
            b = int(b)
        if isinstance(b, bool) or not isinstance(b, int) or b <= 0 or b % k or b > 10000:
            raise ValueError(f"block size {b} is not a positive whole multiple of {k} arms (max 10000)")
    while True:
        size = sizes[stream.randbelow(len(sizes))]
        block = [arms[i % k] for i in range(size)]
        for arm in stream.shuffle(block):
            yield arm


def permuted_blocks(seed: bytes, n: int, arms, block_sizes=None):
    """Permuted-block randomisation with varying block sizes.

    Each block has equal numbers per arm. The block size changes at random,
    so the next assignment is hard to predict near the end of a block.
    """
    gen = _block_generator(HashStream(seed, "blocks"), arms, block_sizes)
    return [next(gen) for _ in range(n)]


def stratified_blocks(seed: bytes, strata, arms, block_sizes=None):
    """Stratified permuted blocks. Each stratum has its own stream and its own blocks.

    `strata` is the stratum label for each participant, in enrolment order.
    The stratum labels must be fixed in the protocol before enrolment.
    """
    gens = {}
    out = []
    for raw in strata:
        s = stratum_label(raw)
        if s not in gens:
            gens[s] = _block_generator(
                HashStream(seed, f"stratum:{s}"), arms, block_sizes
            )
        out.append(next(gens[s]))
    return out


def minimisation(seed: bytes, people, arms, factors, p_best=0.8):
    """Pocock–Simon minimisation with a biased coin (Pocock and Simon, 1975).

    `people` is a list of dicts, one per participant in enrolment order, each
    with a level for every factor. Each arrival is allocated after the previous
    ones, so the protocol must fix the factors and levels in advance.

    For each arm, the score is the sum over factors of the spread (max minus min)
    of arm counts for that person's level, after assigning the person to that arm.
    The arm with the lowest score is chosen with probability p_best (ties broken
    at random). Otherwise another arm is chosen at random.
    """
    if not 0.5 < p_best <= 1:
        raise ValueError("p_best should be between 0.5 and 1")
    stream = HashStream(seed, "minimisation")
    arms = list(arms)
    counts = {f: defaultdict(lambda: {a: 0 for a in arms}) for f in factors}
    out = []
    for person in people:
        scores = {}
        for arm in arms:
            total = 0
            for f in factors:
                c = counts[f][person[f]]
                after = [c[a] + (1 if a == arm else 0) for a in arms]
                total += max(after) - min(after)
            scores[arm] = total
        best = min(scores.values())
        best_arms = [a for a in arms if scores[a] == best]
        if stream.uniform() < p_best:
            arm = best_arms[stream.randbelow(len(best_arms))]
        else:
            others = [a for a in arms if a not in best_arms] or arms
            arm = others[stream.randbelow(len(others))]
        for f in factors:
            counts[f][person[f]][arm] += 1
        out.append(arm)
    return out


def matched_pairs(seed: bytes, pairs, arm_names=("A", "B")):
    """Matched-pairs allocation for two arms. Returns {unit: arm}.

    `pairs` is a list of (unit, unit) tuples. Within each pair, a coin flip
    decides which unit gets arm_names[0].
    """
    stream = HashStream(seed, "pairs")
    alloc = {}
    for u1, u2 in pairs:
        if stream.randbelow(2) == 0:
            alloc[u1], alloc[u2] = arm_names[0], arm_names[1]
        else:
            alloc[u2], alloc[u1] = arm_names[0], arm_names[1]
    return alloc


def constrained_two_arm(seed: bytes, units, balance_ok, arm_names=("A", "B"),
                        enumerate_limit=200_000, max_draws=200_000):
    """Constrained randomisation for two arms with equal sizes (Box 11.1 method).

    `balance_ok(group_a, group_b)` returns True if the split is acceptable.
    It must be written and fixed before randomisation.

    If the number of possible splits is at most `enumerate_limit`, every split
    is checked and one acceptable split is drawn uniformly. Otherwise the
    program draws random splits, keeps the acceptable ones, and reports that
    the draw is not uniform over all acceptable splits.

    Returns a dict with the allocation and an audit summary.
    """
    units = list(units)
    n = len(units)
    if n % 2:
        raise ValueError("two equal arms need an even number of units")
    half = n // 2
    total = math.comb(n, half)
    stream = HashStream(seed, "constrained")
    if total <= enumerate_limit:
        accepted = []
        for combo in itertools.combinations(range(n), half):
            chosen = set(combo)
            a = [units[i] for i in combo]
            b = [units[i] for i in range(n) if i not in chosen]
            if balance_ok(a, b):
                accepted.append(combo)
        if not accepted:
            raise ValueError("no split satisfies the balance rule; relax the rule")
        pick = accepted[stream.randbelow(len(accepted))]
        method = "enumerated: uniform over all acceptable splits"
        n_accepted = len(accepted)
    else:
        seen = set()
        for _ in range(max_draws):
            idx = stream.shuffle(range(n))
            combo = tuple(sorted(idx[:half]))
            if combo in seen:
                continue
            a = [units[i] for i in combo]
            b = [units[i] for i in range(n) if i not in set(combo)]
            if balance_ok(a, b):
                seen.add(combo)
        if not seen:
            raise ValueError("no acceptable split found in the draws; relax the rule")
        accepted = sorted(seen)
        pick = accepted[stream.randbelow(len(accepted))]
        method = "sampled: uniform over the acceptable splits found, not all of them"
        n_accepted = len(accepted)
    chosen = set(pick)
    alloc = {units[i]: (arm_names[0] if i in chosen else arm_names[1]) for i in range(n)}
    return {
        "allocation": alloc,
        "possible_splits": total,
        "acceptable_splits_found": n_accepted,
        "selection": method,
    }


# ---------------------------------------------------------------------------
# Cluster trials: the units are schools, clinics, wards or communities
# ---------------------------------------------------------------------------
#
# Individuals arrive one by one. Clusters do not: the whole list is known
# before anything is allocated, so these methods allocate all clusters in one
# pass instead of one arrival at a time.
#
# Rules shared by all three methods, fixed here so the two engines (Python and
# alloc.js) cannot drift apart:
#
# - A cluster is a dict with a unique string "id", a value for every factor,
#   and (if `weight` names one) a positive number, usually its size.
# - Allocation depends on the seed and on the SET of clusters, never on the
#   order they were typed in. Clusters are put in the order of the UTF-8 bytes
#   of their ids before anything else happens.
# - A numeric factor (cluster size, baseline prevalence) is cut into bins by
#   `bins[factor]`, a strictly increasing list of cut points. A value goes in
#   bin i where i is the number of cut points at or below it: cuts [20, 50]
#   give <20, 20 to under 50, and 50 or more. A factor with no bins keeps its
#   own values as levels: a string, a whole number up to 2^53, or true/false (written "true"/"false",
#   so 1 and "1" are the same level). Text must be valid Unicode (no lone surrogates).
# - Results hold lists of pairs, never objects keyed by data, so the output
#   has one order and one JSON form in every language.

MAX_WEIGHT = 1e9
MIN_WEIGHT = 1e-3


def bin_level(value, cuts) -> int:
    """Index of the bin a numeric value falls in. See the rules above."""
    if not _finite(value):
        raise ValueError(f"a binned factor needs a finite number, got {value!r}")
    i = 0
    while i < len(cuts) and value >= cuts[i]:
        i += 1
    return i


def _fsum(values):
    """Plain left-to-right sum. The built-in sum() uses compensated summation for floats from
    Python 3.12, which JavaScript does not, so fractional weights would disagree in the last digit."""
    t = 0
    for v in values:
        t += v
    return t


def _clean(text, what):
    """Reject text that is not valid Unicode (a lone surrogate): JavaScript would accept it."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError(f"{what} contains an invalid character (lone surrogate)")
    return text


def _finite(x):
    """A finite real number whose value is the same in JavaScript: integers beyond 2^53 are refused."""
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x or x in (float("inf"), float("-inf")):
        return False
    return not (isinstance(x, int) and abs(x) > 2 ** 53)


def _num(x):
    """A whole-number float becomes an int, so 120.0 and 120 print the same in every language."""
    if isinstance(x, float) and x.is_integer() and abs(x) < 2 ** 53:
        return int(x)
    return x


def _utf8_key(text: str) -> bytes:
    return text.encode("utf-8")


def _levels_key(levels) -> str:
    """One unambiguous string for a stratum: the JSON of its [factor, level] pairs."""
    return json.dumps(levels, separators=(",", ":"), ensure_ascii=False)


def _cluster_table(clusters, arms, factors, bins, weight):
    """Validate the inputs and return (rows, arms, factors) with rows in id order.

    Each row is {"id", "levels": [[factor, level], ...], "weight": number or None}.
    """
    if not isinstance(arms, (list, tuple)):
        raise ValueError("arms must be a list")
    if factors is not None and not isinstance(factors, (list, tuple)):
        raise ValueError("factors must be a list")
    if bins is not None and not isinstance(bins, dict):
        raise ValueError("bins must be an object")
    if weight is not None and (not isinstance(weight, str) or not weight):
        raise ValueError("weight must be the name of a field")
    arms = list(arms)
    factors = list(factors or [])
    bins = dict(bins or {})
    for t in arms + factors:
        if isinstance(t, str):
            _clean(t, "an arm or factor name")
    if len(arms) < 2 or len(set(arms)) != len(arms) or not all(isinstance(a, str) and a for a in arms):
        raise ValueError("arms must be two or more different non-empty strings")
    if len(set(factors)) != len(factors) or not all(isinstance(f, str) and f for f in factors):
        raise ValueError("factors must be different non-empty strings")
    for f, cuts in bins.items():
        if f not in factors:
            raise ValueError(f"bins given for '{f}', which is not a factor")
        if (not isinstance(cuts, (list, tuple)) or not cuts
                or any(not _finite(c) for c in cuts)
                or any(cuts[i] >= cuts[i + 1] for i in range(len(cuts) - 1))):
            raise ValueError(f"bins for '{f}' must be a non-empty, strictly increasing list of numbers")
    if not isinstance(clusters, (list, tuple)) or len(clusters) < 2:
        raise ValueError("a cluster trial needs a list of at least two clusters")
    seen = set()
    rows = []
    for c in clusters:
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"]:
            raise ValueError("every cluster needs a non-empty string id")
        cid = _clean(c["id"], "a cluster id")
        if cid in seen:
            raise ValueError(f"cluster id '{cid}' appears twice")
        seen.add(cid)
        levels = []
        for f in factors:
            if f not in c:
                raise ValueError(f"cluster '{cid}' has no value for factor '{f}'")
            if f in bins:
                levels.append([f, "b%d" % bin_level(c[f], bins[f])])
            else:
                lab = stratum_label(c[f])
                if isinstance(c[f], int) and not isinstance(c[f], bool) and abs(c[f]) > 2 ** 53:
                    raise ValueError(f"cluster '{cid}': '{f}' is a whole number beyond 2^53")
                levels.append([f, _clean(lab, "a factor level")])
        w = None
        if weight is not None:
            w = c.get(weight)
            if not _finite(w) or not (MIN_WEIGHT <= w <= MAX_WEIGHT):
                raise ValueError(f"cluster '{cid}': '{weight}' must be a number from {MIN_WEIGHT:g} to {MAX_WEIGHT:g}")
        rows.append({"id": cid, "levels": levels, "weight": w})
    rows.sort(key=lambda r: _utf8_key(r["id"]))
    return rows, arms, factors


def _arm_totals(rows, alloc, arms, weight):
    out = []
    for a in arms:
        mine = [r for r in rows if alloc[r["id"]] == a]
        out.append({"arm": a, "clusters": len(mine),
                    "weight": _num(_fsum(r["weight"] for r in mine)) if weight is not None else None})
    return out


def stratified_clusters(seed: bytes, clusters, arms, factors, bins=None, weight=None):
    """Stratified allocation of a known list of clusters, for one or several factors.

    Strata are the combinations of factor levels. Inside each stratum the arms
    are dealt out as evenly as the stratum size allows, then shuffled over its
    clusters, so a stratum of 6 clusters and 2 arms gives exactly 3 and 3.

    When a stratum does not divide evenly, the spare clusters go to the arms
    with the fewest clusters so far, counted over the strata already done
    (strata are taken in the order of their keys), ties broken at random. So
    the overall counts stay as close as possible instead of drifting by one
    per stratum.

    `weight` names a number on each cluster (size). It is only summed per arm
    in the result, to show how the participant numbers came out; it does not
    steer the allocation. Use cluster_minimisation to balance on it.

    Warnings, not errors, when the design is too thin to balance:
    - stratum_missing_arm: a stratum has fewer clusters than arms.
    - strata_too_fine: there are more strata than clusters can fill, at one
      cluster per arm per stratum.
    """
    rows, arms, factors = _cluster_table(clusters, arms, factors, bins, weight)
    k = len(arms)
    strata = {}
    for r in rows:
        strata.setdefault(_levels_key(r["levels"]), []).append(r)
    global_counts = {a: 0 for a in arms}
    alloc = {}
    detail = []
    warnings = []
    for key in sorted(strata, key=_utf8_key):
        members = strata[key]
        m = len(members)
        stream = HashStream(seed, "cluster-stratum:" + key)
        base, spare = divmod(m, k)
        shuffled = stream.shuffle(range(k))  # random order among arms, so ties break at random
        ranked = sorted(shuffled, key=lambda i: (global_counts[arms[i]], shuffled.index(i)))
        extra = set(ranked[:spare])
        labels = []
        for i, a in enumerate(arms):
            labels += [a] * (base + (1 if i in extra else 0))
        labels = stream.shuffle(labels)
        counts = {a: 0 for a in arms}
        for r, lab in zip(members, labels):
            alloc[r["id"]] = lab
            global_counts[lab] += 1
            counts[lab] += 1
        detail.append({"levels": members[0]["levels"], "clusters": m,
                       "counts": [[a, counts[a]] for a in arms]})
        if m < k:
            warnings.append({"kind": "stratum_missing_arm", "levels": members[0]["levels"], "clusters": m})
    if len(strata) * k > len(rows):
        warnings.append({"kind": "strata_too_fine", "strata": len(strata), "clusters": len(rows), "arms": k})
    return {
        "method": "stratified_clusters",
        "allocation": [[r["id"], alloc[r["id"]]] for r in rows],
        "strata": detail,
        "arm_totals": _arm_totals(rows, alloc, arms, weight),
        "warnings": warnings,
    }


def cluster_minimisation(seed: bytes, clusters, arms, factors, bins=None, weight=None, p_best=0.8):
    """Minimisation for a known list of clusters (Pocock and Simon, 1975, adapted).

    The clusters are taken in a random order drawn from the seed, so the order
    cannot be chosen by the researcher. For each cluster in turn, every arm gets
    a score: the sum, over the whole set of clusters and over each factor level
    this cluster belongs to, of the spread (largest minus smallest) of the arm
    totals if the cluster joined that arm. Two totals are kept for each group:
    the number of clusters, and, if `weight` is given, the weight (cluster size)
    divided by the average weight, so one typical cluster counts 1 in both. The
    arm with the lowest score is chosen with probability p_best (ties at
    random), otherwise one of the other arms at random.

    This balances the number of clusters and, with `weight`, the number of
    participants, across arms overall and within every factor level. It does
    not guarantee balance; with few clusters or many factors, check the
    `balance` list in the result and the warnings.

    Minimisation is not stratification: a factor level with one cluster in it
    still gets no pair to balance against. The warning `level_single_cluster`
    names such levels.
    """
    if isinstance(p_best, bool) or not isinstance(p_best, (int, float)) or not 0.5 < p_best <= 1:
        raise ValueError("p_best should be a number above 0.5 and at most 1")
    rows, arms, factors = _cluster_table(clusters, arms, factors, bins, weight)
    n = len(rows)
    mean_w = (_fsum(r["weight"] for r in rows) / n) if weight is not None else None
    order_stream = HashStream(seed, "cluster-minimisation:order")
    stream = HashStream(seed, "cluster-minimisation")
    order = order_stream.shuffle(range(n))

    def fresh():
        return {"n": {a: 0 for a in arms}, "w": {a: 0.0 for a in arms}}

    overall = fresh()
    groups = {}
    for r in rows:
        for f, lvl in r["levels"]:
            groups.setdefault(_levels_key([f, lvl]), fresh())

    def spread(tot, arm, add):
        after = [tot[a] + (add if a == arm else 0) for a in arms]
        return max(after) - min(after)

    alloc = {}
    for idx in order:
        r = rows[idx]
        wn = (r["weight"] / mean_w) if weight is not None else 0.0
        members = [overall] + [groups[_levels_key([f, lvl])] for f, lvl in r["levels"]]
        scores = {}
        for a in arms:
            total = 0
            for g in members:
                total += spread(g["n"], a, 1)
                if weight is not None:
                    total += spread(g["w"], a, wn)
            scores[a] = total
        best = min(scores.values())
        best_arms = [a for a in arms if scores[a] == best]
        if stream.uniform() < p_best:
            arm = best_arms[stream.randbelow(len(best_arms))]
        else:
            others = [a for a in arms if a not in best_arms] or arms
            arm = others[stream.randbelow(len(others))]
        for g in members:
            g["n"][arm] += 1
            g["w"][arm] += wn
        alloc[r["id"]] = arm

    balance = []
    warnings = []
    for key in sorted(groups, key=_utf8_key):
        f, lvl = json.loads(key)
        members_n = sum(groups[key]["n"].values())
        entry = {"factor": f, "level": lvl, "clusters": members_n,
                 "counts": [[a, groups[key]["n"][a]] for a in arms]}
        if weight is not None:
            sums = {a: _fsum(rr["weight"] for rr in rows
                             if alloc[rr["id"]] == a and [f, lvl] in rr["levels"]) for a in arms}
            entry["weights"] = [[a, _num(sums[a])] for a in arms]
        balance.append(entry)
        if members_n < 2:
            warnings.append({"kind": "level_single_cluster", "factor": f, "level": lvl})
    return {
        "method": "cluster_minimisation",
        "processing_order": [rows[i]["id"] for i in order],
        "allocation": [[r["id"], alloc[r["id"]]] for r in rows],
        "arm_totals": _arm_totals(rows, alloc, arms, weight),
        "balance": balance,
        "warnings": warnings,
    }


MAX_TRIES = 200000
NARROW_CHOICE = 100  # fewer distinct acceptable allocations than this in `tries` draws is a warning


def constrained_clusters(seed: bytes, clusters, arms, constraints, tries=10000):
    """Constrained randomisation for a small cluster trial, two arms, with rules written as data.

    Candidate allocations are drawn at random, each putting half the clusters
    (rounded so the arms differ by at most one) in each arm. The first
    candidate that meets every constraint is the allocation. All `tries`
    candidates are drawn, to count how many different allocations qualified
    (`acceptable_seen`). If fewer than NARROW_CHOICE did, the warning
    `narrow_choice` says the rules leave too small a set to randomise from.
    If none qualifies the call raises: loosen the rules or widen the design.

    Each constraint is a dict, so it can sit in a plan and be hashed:
      {"type": "mean_diff", "factor": F, "max": X}   arm means of numeric F differ by at most X
      {"type": "count_diff", "factor": F, "max": X}  for every level of F, arm counts differ by at most X

    Constrained randomisation is the usual choice with fewer than about 20
    clusters, where stratifying on several factors leaves strata of one.
    """
    rows, arms, _ = _cluster_table(clusters, arms, [], None, None)
    if len(arms) != 2:
        raise ValueError("constrained_clusters handles two arms")
    if isinstance(tries, float) and tries.is_integer():
        tries = int(tries)
    if not isinstance(tries, int) or isinstance(tries, bool) or not 1 <= tries <= MAX_TRIES:
        raise ValueError(f"tries must be a whole number from 1 to {MAX_TRIES}")
    if not isinstance(constraints, (list, tuple)) or not constraints:
        raise ValueError("give at least one constraint")
    byid = {c["id"]: c for c in clusters}
    prepared = []
    for c in constraints:
        if not isinstance(c, dict) or c.get("type") not in ("mean_diff", "count_diff"):
            raise ValueError("a constraint needs type mean_diff or count_diff")
        f, mx = c.get("factor"), c.get("max")
        if not isinstance(f, str) or not f:
            raise ValueError("a constraint needs a factor name")
        if not _finite(mx) or mx < 0:
            raise ValueError("a constraint max must be a finite number, zero or more")
        vals = []
        for r in rows:
            if f not in byid[r["id"]]:
                raise ValueError(f"cluster '{r['id']}' has no value for factor '{f}'")
            x = byid[r["id"]][f]
            if c["type"] == "mean_diff":
                if not _finite(x):
                    raise ValueError(f"mean_diff needs a finite number for '{f}' on cluster '{r['id']}'")
                vals.append(x)
            else:
                if isinstance(x, int) and not isinstance(x, bool) and abs(x) > 2 ** 53:
                    raise ValueError(f"count_diff: '{f}' on cluster '{r['id']}' is a whole number beyond 2^53")
                vals.append(_clean(stratum_label(x), "a factor level"))
        prepared.append((c["type"], vals, mx))
    n = len(rows)
    stream = HashStream(seed, "constrained-clusters")
    sizes = [n // 2, n - n // 2]
    first_is_big = n % 2 == 1 and stream.randbelow(2) == 0
    n0 = sizes[1] if first_is_big else sizes[0]
    chosen = None
    attempt_at = 0
    distinct = set()
    for attempt in range(1, tries + 1):
        picks = stream.shuffle(range(n))
        in0 = set(picks[:n0])
        ok = True
        for kind, vals, mx in prepared:
            if kind == "mean_diff":
                s0 = s1 = 0
                for i in range(n):
                    if i in in0:
                        s0 += vals[i]
                    else:
                        s1 += vals[i]
                if abs(s0 / n0 - s1 / (n - n0)) > mx:
                    ok = False
                    break
            else:
                lv = {}
                for i in range(n):
                    e = lv.setdefault(vals[i], [0, 0])
                    e[0 if i in in0 else 1] += 1
                if any(abs(e[0] - e[1]) > mx for e in lv.values()):
                    ok = False
                    break
        if ok:
            if chosen is None:
                chosen, attempt_at = in0, attempt
            distinct.add(",".join(str(i) for i in sorted(in0)))
    if chosen is not None:
        warnings = []
        if len(distinct) < NARROW_CHOICE:
            warnings.append({"kind": "narrow_choice", "distinct_acceptable": len(distinct), "tries": tries})
        return {
            "method": "constrained_clusters",
            "allocation": [[rows[i]["id"], arms[0] if i in chosen else arms[1]] for i in range(n)],
            "attempts": attempt_at,
            "acceptable_seen": len(distinct),
            "arm_totals": [{"arm": arms[0], "clusters": n0}, {"arm": arms[1], "clusters": n - n0}],
            "warnings": warnings,
        }
    raise ValueError(f"none of {tries} random allocations met the constraints; loosen them")


def williams_rows(k: int):
    """Balanced Latin square rows (Williams design) for k treatments.

    Each treatment appears once in each position. Each treatment follows each
    other treatment equally often. For odd k the reversed rows are added, so
    the design has 2k sequences.
    """
    if k < 2:
        raise ValueError("need at least two treatments")
    seq = [0]
    lo, hi = 1, k - 1
    take_lo = True
    while len(seq) < k:
        if take_lo:
            seq.append(lo)
            lo += 1
        else:
            seq.append(hi)
            hi -= 1
        take_lo = not take_lo
    rows = [[(f + i) % k for f in seq] for i in range(k)]
    if k % 2:
        rows += [list(reversed(r)) for r in rows]
    return rows


def crossover(seed: bytes, n: int, treatments):
    """Cross-over sequences for n participants, balanced across Williams rows.

    Returns one list of treatments per participant, in period order.
    """
    treatments = list(treatments)
    rows = williams_rows(len(treatments))
    order = [rows[i % len(rows)] for i in range(n)]
    order = HashStream(seed, "crossover").shuffle(order)
    return [[treatments[t] for t in row] for row in order]


# ---------------------------------------------------------------------------
# Audit record and verification
# ---------------------------------------------------------------------------

def audit_record(study_id: str, method: str, params: dict, seed: bytes, result, plan_sha256: str = None) -> dict:
    """Record for the study file. Publish the commitment early. Reveal the seed later.

    With plan_sha256 the record uses commitment v2, which binds the registered plan.
    Without it the v1 commitment is written, as before.
    """
    return {
        "study_id": study_id,
        "software_version": VERSION,
        "method": method,
        "params": params,
        "commitment_version": 2 if plan_sha256 else 1,
        "plan_sha256": plan_sha256,
        "commitment_sha256": commitment_v2(seed, plan_sha256) if plan_sha256 else commitment(seed),
        "result_sha256": hashlib.sha256(_canonical(result)).hexdigest(),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed_revealed_hex": None,
    }


def verify(record: dict, seed_hex: str, rerun) -> bool:
    """Check a revealed seed against the commitment and the result hash.

    `rerun(seed)` must re-run the same method with the same params and return
    the result. Returns True only if all checks pass.
    """
    seed = bytes.fromhex(seed_hex)
    if record.get("commitment_version", 1) == 2:
        expected = commitment_v2(seed, record["plan_sha256"])
    else:
        expected = commitment(seed)
    if expected != record["commitment_sha256"]:
        return False
    result = rerun(seed)
    return hashlib.sha256(_canonical(result)).hexdigest() == record["result_sha256"]


# ---------------------------------------------------------------------------
# Envelope material
# ---------------------------------------------------------------------------

FACE_EN = (
    "Envelope {no} of {total}. Study {study}. "
    "Open only when eligibility is confirmed and written consent is signed. "
    "Do not open out of order. Write the participant ID on the stub and on the log."
)
FACE_HI = (
    "लिफ़ाफ़ा {no} / {total}। अध्ययन {study}। "
    "तभी खोलें जब पात्रता पक्की हो और लिखित सहमति मिल जाए। क्रम से बाहर न खोलें।"
)


def envelope_files(out_dir: str, study_id: str, allocation_list) -> dict:
    """Write three files for an envelope trial.

    master_list.csv   Keep with the study coordinator, not at the site. Shows the arm.
    envelope_faces.csv  Text to print on each envelope face. Does not show the arm.
    opening_log.csv   Blank log. One row per envelope, filled when opened.
    Print the faces, then seal each arm into an opaque, numbered envelope
    with a tamper-evident seal and a blank inner stub.
    """
    os.makedirs(out_dir, exist_ok=True)
    total = len(allocation_list)
    master = os.path.join(out_dir, "master_list.csv")
    faces = os.path.join(out_dir, "envelope_faces.csv")
    log = os.path.join(out_dir, "opening_log.csv")
    with open(master, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["envelope_no", "arm", "study_id"])
        for i, arm in enumerate(allocation_list, start=1):
            w.writerow([i, arm, study_id])
    with open(faces, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["envelope_no", "face_text_en", "face_text_hi"])
        for i in range(1, total + 1):
            w.writerow([
                i,
                FACE_EN.format(no=i, total=total, study=study_id),
                FACE_HI.format(no=i, total=total, study=study_id),
            ])
    with open(log, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["envelope_no", "participant_id", "date_opened", "opened_by",
                    "eligibility_confirmed", "consent_signed", "notes"])
        for i in range(1, total + 1):
            w.writerow([i, "", "", "", "", "", ""])
    return {"master": master, "faces": faces, "log": log}


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def run_config(config: dict, seed: bytes):
    """Run one allocation from a config dict. Returns (result, params)."""
    m = config["method"]
    if m == "simple":
        params = {"n": config["n"], "arms": config["arms"], "probs": config.get("probs")}
        res = simple(seed, config["n"], config["arms"], config.get("probs"))
    elif m == "permuted_blocks":
        # third review: the audit params record the sizes actually used, never null
        bs = config.get("block_sizes") or default_blocks(len(config["arms"]))
        params = {"n": config["n"], "arms": config["arms"], "block_sizes": bs}
        res = permuted_blocks(seed, config["n"], config["arms"], bs)
    elif m == "stratified":
        bs = config.get("block_sizes") or default_blocks(len(config["arms"]))
        params = {"strata": config["strata"], "arms": config["arms"], "block_sizes": bs}
        res = stratified_blocks(seed, config["strata"], config["arms"], bs)
    elif m == "minimisation":
        params = {"people": config["people"], "arms": config["arms"],
                  "factors": config["factors"], "p_best": config.get("p_best", 0.8)}
        res = minimisation(seed, config["people"], config["arms"],
                           config["factors"], config.get("p_best", 0.8))
    elif m in ("stratified_clusters", "cluster_minimisation"):
        params = {"clusters": config["clusters"], "arms": config["arms"],
                  "factors": config.get("factors", []), "bins": config.get("bins"),
                  "weight": config.get("weight")}
        if m == "stratified_clusters":
            res = stratified_clusters(seed, config["clusters"], config["arms"],
                                      config.get("factors", []), config.get("bins"), config.get("weight"))
        else:
            params["p_best"] = config.get("p_best", 0.8)
            res = cluster_minimisation(seed, config["clusters"], config["arms"],
                                       config.get("factors", []), config.get("bins"),
                                       config.get("weight"), config.get("p_best", 0.8))
    elif m == "constrained_clusters":
        params = {"clusters": config["clusters"], "arms": config["arms"],
                  "constraints": config["constraints"], "tries": config.get("tries", 10000)}
        res = constrained_clusters(seed, config["clusters"], config["arms"],
                                   config["constraints"], config.get("tries", 10000))
    elif m == "crossover":
        params = {"n": config["n"], "treatments": config["treatments"]}
        res = crossover(seed, config["n"], config["treatments"])
    else:
        raise ValueError(f"method '{m}' is not in the command line; use the Python API")
    return res, params


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Appuscholar randomisation")
    p.add_argument("config", help="JSON config file")
    p.add_argument("--out", required=True, help="output folder")
    p.add_argument("--seed-hex", help="reuse a seed (for verification). Omit for a new seed.")
    p.add_argument("--envelopes", action="store_true", help="also write envelope files")
    a = p.parse_args(argv)
    with open(a.config, encoding="utf-8") as f:
        config = json.load(f)
    os.makedirs(a.out, exist_ok=True)
    seed = bytes.fromhex(a.seed_hex) if a.seed_hex else new_seed()
    result, params = run_config(config, seed)
    record = audit_record(config["study_id"], config["method"], params, seed, result)
    with open(os.path.join(a.out, "allocation.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, "audit_record.json"), "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=1)
    if a.seed_hex is None:
        # Written to a separate file. Keep it away from the site until enrolment is closed.
        with open(os.path.join(a.out, "SEED_KEEP_SECRET.txt"), "w", encoding="utf-8") as f:
            f.write(seed.hex() + "\n")
    if a.envelopes:
        if config["method"] == "minimisation" or not isinstance(result, list):
            raise SystemExit("envelope output needs a list of arms in enrolment order")
        envelope_files(os.path.join(a.out, "envelopes"), config["study_id"], result)
    print(f"Wrote allocation for {config['study_id']} to {a.out}")
    print(f"Commitment (publish before enrolment): {record['commitment_sha256']}")


if __name__ == "__main__":
    main()
