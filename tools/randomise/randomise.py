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
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


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


def _block_generator(stream: HashStream, arms, block_sizes):
    """Endless stream of arm labels, in randomly ordered blocks of random size."""
    arms = list(arms)
    k = len(arms)
    sizes = list(block_sizes)
    for b in sizes:
        if b % k:
            raise ValueError(f"block size {b} is not a multiple of {k} arms")
    while True:
        size = sizes[stream.randbelow(len(sizes))]
        block = [arms[i % k] for i in range(size)]
        for arm in stream.shuffle(block):
            yield arm


def permuted_blocks(seed: bytes, n: int, arms, block_sizes=(4, 6, 8)):
    """Permuted-block randomisation with varying block sizes.

    Each block has equal numbers per arm. The block size changes at random,
    so the next assignment is hard to predict near the end of a block.
    """
    gen = _block_generator(HashStream(seed, "blocks"), arms, block_sizes)
    return [next(gen) for _ in range(n)]


def stratified_blocks(seed: bytes, strata, arms, block_sizes=(4, 6, 8)):
    """Stratified permuted blocks. Each stratum has its own stream and its own blocks.

    `strata` is the stratum label for each participant, in enrolment order.
    The stratum labels must be fixed in the protocol before enrolment.
    """
    gens = {}
    out = []
    for s in strata:
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
        bs = config.get("block_sizes", [4, 6, 8])
        params = {"n": config["n"], "arms": config["arms"], "block_sizes": bs}
        res = permuted_blocks(seed, config["n"], config["arms"], bs)
    elif m == "stratified":
        bs = config.get("block_sizes", [4, 6, 8])
        params = {"strata": config["strata"], "arms": config["arms"], "block_sizes": bs}
        res = stratified_blocks(seed, config["strata"], config["arms"], bs)
    elif m == "minimisation":
        params = {"people": config["people"], "arms": config["arms"],
                  "factors": config["factors"], "p_best": config.get("p_best", 0.8)}
        res = minimisation(seed, config["people"], config["arms"],
                           config["factors"], config.get("p_best", 0.8))
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
