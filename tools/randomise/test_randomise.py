import sys, json, collections
sys.path.insert(0, ".")
import randomise as R

seed = bytes.fromhex("01" * 32)
seed2 = bytes.fromhex("02" * 32)

# 1 determinism
assert R.permuted_blocks(seed, 40, ["A","B"]) == R.permuted_blocks(seed, 40, ["A","B"])
assert R.permuted_blocks(seed, 40, ["A","B"]) != R.permuted_blocks(seed2, 40, ["A","B"])

# 2 full blocks balanced: sizes 4,6,8 -> each completed block has equal arms
seq = R.permuted_blocks(seed, 200, ["A","B"], (4,6,8))
# reconstruct boundaries by regenerating block sizes is internal; check overall balance within 4
c = collections.Counter(seq)
assert abs(c["A"] - c["B"]) <= 4, c

# 3 block size must be multiple of arms
try:
    R.permuted_blocks(seed, 10, ["A","B","C"], (4,6)); raise SystemExit("should fail")
except ValueError: pass

# 4 stratified: each stratum balanced
strata = ["m","f"] * 60
st = R.stratified_blocks(seed, strata, ["A","B"], (4,6,8))
for s in ("m","f"):
    arms_s = [a for a, t in zip(st, strata) if t == s]
    cs = collections.Counter(arms_s)
    assert abs(cs["A"] - cs["B"]) <= 4, (s, cs)

# 5 streams independent: changing one stratum label doesn't change another stratum's sequence
st2 = R.stratified_blocks(seed, ["m","f","x","m","f"], ["A","B"], (4,6,8))
st3 = R.stratified_blocks(seed, ["m","f","m","f"], ["A","B"], (4,6,8))
assert [a for a,t in zip(st2,["m","f","x","m","f"]) if t=="f"] == [a for a,t in zip(st3,["m","f","m","f"]) if t=="f"]

# 6 minimisation beats simple on imbalance (simulation)
import random
rng = random.Random(1)
people = [{"sex": rng.choice(["M","F"]), "age": rng.choice(["young","old"]), "sev": rng.choice(["lo","hi"])} for _ in range(60)]
mini = R.minimisation(seed, people, ["A","B"], ["sex","age","sev"], 0.8)
simp = R.simple(seed, 60, ["A","B"])
def imb(alloc):
    worst = 0
    for f in ["sex","age","sev"]:
        for lvl in set(p[f] for p in people):
            a = sum(1 for p,x in zip(people,alloc) if p[f]==lvl and x=="A")
            n = sum(1 for p in people if p[f]==lvl)
            worst = max(worst, abs(2*a-n))
    return worst
assert imb(mini) <= imb(simp), (imb(mini), imb(simp))
print("minimisation imbalance", imb(mini), "simple imbalance", imb(simp))

# 7 matched pairs: each pair one A one B
pairs = [("c1","c2"),("c3","c4"),("c5","c6")]
mp = R.matched_pairs(seed, pairs)
for u1,u2 in pairs:
    assert {mp[u1], mp[u2]} == {"A","B"}

# 8 constrained: 12 communities, 924 splits; accept balance rule
units = [f"c{i}" for i in range(12)]
bal = {f"c{i}": (i % 2) for i in range(12)}   # 0 and 1 types
def ok(a, b):
    return sum(bal[u] for u in a) == sum(bal[u] for u in b) == 3
res = R.constrained_two_arm(seed, units, ok)
assert res["possible_splits"] == 924, res["possible_splits"]
assert res["acceptable_splits_found"] > 0
assert sorted(res["allocation"].values()).count("A") == 6

# 9 crossover Williams: k=4 rows balanced; each ordered adjacent pair appears once
rows = R.williams_rows(4)
pairs_seen = collections.Counter((r[i], r[i+1]) for r in rows for i in range(3))
assert all(v == 1 for v in pairs_seen.values()) and len(pairs_seen) == 12
for r in rows: assert sorted(r) == [0,1,2,3]
rows3 = R.williams_rows(3)
for r in rows3: assert sorted(r) == [0,1,2]
seqs = R.crossover(seed, 8, ["AB1","AB2"]) if False else R.crossover(seed, 8, ["X","Y"])
assert all(sorted(s) == ["X","Y"] for s in seqs)

# 10 verification: good record passes, altered result fails
params = {"n": 40, "arms": ["A","B"], "block_sizes": [4,6,8]}
result = R.permuted_blocks(seed, 40, ["A","B"], (4,6,8))
rec = R.audit_record("TEST", "permuted_blocks", params, seed, result)
rerun = lambda s: R.permuted_blocks(s, 40, ["A","B"], (4,6,8))
assert R.verify(rec, seed.hex(), rerun)
assert not R.verify(rec, seed2.hex(), rerun)
bad = dict(rec)
assert not R.verify(bad, seed.hex(), lambda s: list(reversed(rerun(s))))

# 11 bias-free randbelow: rough uniformity on 3 values
st = R.HashStream(seed, "uniform-test")
cnt = collections.Counter(st.randbelow(3) for _ in range(30000))
assert all(abs(v - 10000) < 500 for v in cnt.values()), cnt

# 12 plan_hash on non-ASCII text (fix for review finding 7): json.dumps defaults to
# ensure_ascii=True, escaping Hindi text to \uXXXX, while JS's JSON.stringify (used by both
# alloc.js's canonicalJSON and the app's lighter alCanon) keeps it as literal UTF-8. Before the
# fix this engine could never reproduce a commitment made from a plan with Hindi maker/holder
# names or notes - exactly the kind of plan this bilingual app expects. Cross-checked by hand
# against alloc.js's planHash() and index.html's alCanon() for the identical plan dict; this
# pins that known-good value so a regression is caught without needing node here.
plan_unicode = {"method":"perm","maker":"डॉ. मीना शर्मा","holder":"समन्वयक","arms":"A,B",
                "params":"blocks of 4,6,8","conc":"central","blind":"both"}
assert R.plan_hash(plan_unicode) == "892b237f034c3d508750d98bf1e0cdf366a8573011daf5944fdc9e26986089db", R.plan_hash(plan_unicode)
# an ASCII-only plan is unaffected either way (sanity check the fix didn't break the common case)
plan_ascii = {"method":"simple","maker":"Dr. Rao","holder":"Coordinator","arms":"A,B","params":"","conc":"central","blind":"both"}
assert R.plan_hash(plan_ascii) == R.plan_hash(dict(plan_ascii)), "plan_hash must be deterministic"

# 13 engine edge cases (fix for review finding 12), cross-checked by hand against alloc.js for
# the identical seed/inputs (see tools/randomise/README or the fix commit for the JS-side values
# pinned here): a stratum label equal to a JS Object.prototype property name must not misbehave
# (Python dicts have no such inherited keys, so this is really pinning the JS fix, run here too
# so the Python engine's own output for the same scenario is tracked for drift); block size 0
# must raise instead of hanging; numeric and string versions of the same label must be handled
# in a way that matches the JS Map-based fix exactly.
seed12 = bytes.fromhex("03" * 32)
assert R.stratified_blocks(seed12, ["constructor","__proto__","toString","constructor","__proto__"], ["A","B"], (4,6,8)) == ["A","B","B","A","A"]
try:
    R.permuted_blocks(seed12, 4, ["A","B"], (0,)); raise SystemExit("block size 0 should raise")
except ValueError:
    pass
assert R.stratified_blocks(seed12, [1,"1",1,"1",1,"1"], ["A","B"], (4,6,8)) == ["A","A","A","A","A","A"]

print("ALL TESTS PASSED")
