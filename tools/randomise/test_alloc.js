const fs = require("fs");
const A = require("./alloc.js");
const v = JSON.parse(fs.readFileSync("vectors.json", "utf8"));
const seed = A.fromHex(v.seed_hex);
let fails = 0;
function check(name, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) { fails++; console.log("FAIL", name, "\n got", JSON.stringify(got), "\n want", JSON.stringify(want)); }
  else console.log("ok  ", name);
}
check("commitment", A.commitment(seed), v.commitment);
check("plan hash", A.planHash(v.plan_example), v.plan_sha256);
check("commitment v2", A.commitmentV2(seed, v.plan_sha256), v.commitment_v2);
check("simple 2 arms", A.simple(seed, 30, ["A","B"]), v.simple_A_B_30);
check("simple 3 arms probs", A.simple(seed, 30, ["A","B","C"], [0.5,0.3,0.2]), v.simple_3arms_probs_30);
check("permuted blocks 2 arms", A.permutedBlocks(seed, 40, ["A","B"], [4,6,8]), v.blocks_A_B_40);
check("permuted blocks 3 arms", A.permutedBlocks(seed, 60, ["A","B","C"], [6,12]), v.blocks_3arms_60);
check("stratified", A.stratifiedBlocks(seed, v.strata_list, ["A","B"], [4,6,8]), v.strat_30);
check("minimisation", A.minimisation(seed, v.people, ["A","B"], ["sex","age","sev"], 0.8), v.mini_24);
check("crossover 2 trt", A.crossover(seed, 8, ["X","Y"]), v.cross_8);
check("crossover 3 trt", A.crossover(seed, 6, ["P","Q","S"]), v.cross_6_3trt);
check("williams 4", A.williamsRows(4), v.williams_4);
check("williams 3", A.williamsRows(3), v.williams_3);
check("matched pairs", A.matchedPairs(seed, [["c1","c2"],["c3","c4"],["c5","c6"]]), v.pairs);
check("result hash", A.resultHash(A.permutedBlocks(seed, 40, ["A","B"], [4,6,8])), v.result_hash_blocks40);
// SHA-256 known answer (empty string)
check("sha256 empty", A.hex(A.sha256(new Uint8Array(0))), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
console.log(fails === 0 ? "ALL JS TESTS PASSED" : fails + " FAILED");
process.exit(fails ? 1 : 0);
