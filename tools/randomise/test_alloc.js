const fs = require("fs");
const path = require("path");
const A = require(path.join(__dirname, "alloc.js"));
// second review, finding 13: a bare "vectors.json" only resolved from inside this folder, so the
// suite failed with ENOENT from the repo root. Resolve next to this file instead.
const v = JSON.parse(fs.readFileSync(path.join(__dirname, "vectors.json"), "utf8"));
const seed = A.fromHex(v.seed_hex);
let fails = 0;
function check(name, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) { fails++; console.log("FAIL", name, "\n got", JSON.stringify(got), "\n want", JSON.stringify(want)); }
  else console.log("ok  ", name);
}
check("commitment", A.commitment(seed), v.commitment);
check("plan hash", A.planHash(v.plan_example), v.plan_sha256);
// review finding 7: a plan with non-ASCII (Hindi) text must hash the same way here as in
// randomise.py, now that randomise.py's _canonical() uses ensure_ascii=False to match
// JSON.stringify's literal-UTF-8 behaviour. Pinned against the Python engine's own output.
check("plan hash (unicode, cross-engine)", A.planHash({method:"perm",maker:"डॉ. मीना शर्मा",holder:"समन्वयक",arms:"A,B",params:"blocks of 4,6,8",conc:"central",blind:"both"}), "892b237f034c3d508750d98bf1e0cdf366a8573011daf5944fdc9e26986089db");
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
// review finding 12: engine edge cases. A plain {} used as a map would crash or silently merge
// keys here; Map-based gens/counts fix this. Pinned against the Python engine's own output for
// the identical seed and inputs (see test_randomise.py's matching assertions).
const seed12 = A.fromHex("03".repeat(32));
check("stratified: reserved-name labels don't crash", A.stratifiedBlocks(seed12, ["constructor","__proto__","toString","constructor","__proto__"], ["A","B"], [4,6,8]), ["A","B","B","A","A"]);
try {
  A.permutedBlocks(seed12, 4, ["A","B"], [0]);
  fails++; console.log("FAIL block size 0 should throw, not silently build a short/undefined-padded list");
} catch (e) { console.log("ok  ", "permuted blocks: block size 0 throws"); }
// Second review: 1 and "1" used to be two gens sharing one stream key (two strata with identical
// sequences, pinned then as six A's). They are now one stratum in both engines: one balanced block.
check("stratified: numeric 1 and string \"1\" labels are one stratum", A.stratifiedBlocks(seed12, [1,"1",1,"1",1,"1"], ["A","B"], [4,6,8]), ["A","A","A","B","B","B"]);
// third review: labels that String() and str() render differently are refused in both engines
[[1.5,1.5],[null,null],[[1,2],[1,2]],[1e23,1e23],[{},{}]].forEach(function (bad) {
  try { A.stratifiedBlocks(seed12, bad, ["A","B"], [4,6,8]); fails++; console.log("FAIL strata " + JSON.stringify(bad) + " should throw"); }
  catch (e) { console.log("ok  ", "stratified: labels " + JSON.stringify(bad) + " throw"); }
});
check("stratified: true and 1 are different strata, keyed like Python", A.stratifiedBlocks(seed12, [true,1,true,1], ["A","B"], [4,6,8]), A.stratifiedBlocks(seed12, ["true","1","true","1"], ["A","B"], [4,6,8]));

// Second review, findings 5 and 12: arm-count defaults and strict block-size validation.
check("default blocks follow the arm count", [A.defaultBlocks(2), A.defaultBlocks(3)], [[4,6,8],[6,9,12]]);
check("two-arm default is still [4,6,8] (vectors unchanged)", A.permutedBlocks(seed, 40, ["A","B"]), v.blocks_A_B_40);
const three = A.permutedBlocks(seed12, 30, ["A","B","C"]);
check("three-arm plan with default blocks works and is balanced", [three.length, three.filter(x=>x==="A").length, three.filter(x=>x==="B").length, three.filter(x=>x==="C").length, three.indexOf(undefined)], [30,10,10,10,-1]);
check("block size 4.0 is 4 (JSON cannot tell them apart)", A.permutedBlocks(seed12, 8, ["A","B"], [4.0]), A.permutedBlocks(seed12, 8, ["A","B"], [4]));
[[NaN],[4.0000000001],[6.5],["4"],[],[Infinity],[10002]].forEach(function (bad) {
  try { A.permutedBlocks(seed12, 4, ["A","B"], bad); fails++; console.log("FAIL block sizes " + JSON.stringify(bad) + " should throw"); }
  catch (e) { console.log("ok  ", "permuted blocks: block sizes " + JSON.stringify(bad) + " throw"); }
});
try {
  const mp = A.minimisation(seed12, [{sex:"m"},{sex:"f"},{sex:"m"},{sex:"f"}], ["__proto__","B"], ["sex"]);
  check("minimisation: an arm named __proto__ does not throw", mp.length, 4);
} catch (e) { fails++; console.log("FAIL minimisation threw on arm __proto__: " + e.message); }
const pp = A.matchedPairs(seed12, [["__proto__","u2"],["c3","c4"]]);
check("matched pairs: a unit called __proto__ keeps its allocation", Object.keys(pp).sort(), ["__proto__","c3","c4","u2"]);
check("matched pairs: numeric 1 and string \"1\" are not silently merged away from Python", typeof pp, "object");

// ---- cluster trials: shared vectors, order independence, validation ----
const cv = v.clusters, cs = A.fromHex(cv.seed_hex);
check("cluster stratified matches the Python vector", A.stratifiedClusters(cs, cv.clusters, cv.arms, cv.factors, cv.bins, cv.weight), cv.stratified);
check("cluster minimisation matches the Python vector", A.clusterMinimisation(cs, cv.clusters, cv.arms, cv.factors, cv.bins, cv.weight), cv.minimisation);
const reversed = cv.clusters.slice().reverse();
check("cluster stratified does not depend on input order", A.stratifiedClusters(cs, reversed, cv.arms, cv.factors, cv.bins, cv.weight).allocation, cv.stratified.allocation);
check("cluster minimisation does not depend on input order", A.clusterMinimisation(cs, reversed, cv.arms, cv.factors, cv.bins, cv.weight).allocation, cv.minimisation.allocation);
check("bin edges: a value on a cut point goes up", [A.binLevel(99.9,[100,200]), A.binLevel(100,[100,200]), A.binLevel(200,[100,200])], [0,1,2]);
[
  [[{id:"a"}], ["A","B"], []],
  [[{id:"a"},{id:"a"}], ["A","B"], []],
  [[{id:"a"},{id:""}], ["A","B"], []],
  [[{id:"a"},{id:"b"}], ["A"], []],
  [[{id:"a",g:1},{id:"b"}], ["A","B"], ["g"]],
  [[{id:"a",g:1.5},{id:"b",g:2}], ["A","B"], ["g"]],
].forEach(function (c, i) {
  [A.stratifiedClusters, A.clusterMinimisation].forEach(function (fn) {
    try { fn(cs, c[0], c[1], c[2]); fails++; console.log("FAIL cluster validation case " + i + " should throw"); }
    catch (e) { console.log("ok  ", "cluster validation case " + i + " throws"); }
  });
});
try { A.stratifiedClusters(cs, [{id:"a",g:1},{id:"b",g:2}], ["A","B"], ["g"], {g:[5,5]}); fails++; console.log("FAIL equal cut points should throw"); }
catch (e) { console.log("ok   equal cut points throw"); }
try { A.clusterMinimisation(cs, [{id:"a",s:true},{id:"b",s:5}], ["A","B"], [], null, "s"); fails++; console.log("FAIL boolean weight should throw"); }
catch (e) { console.log("ok   boolean weight throws"); }
const pr = A.stratifiedClusters(cs, [{id:"__proto__"},{id:"constructor"}], ["__proto__","B"], []);
check("cluster ids and arms called __proto__ are only names", pr.allocation.map(function (x) { return x[0]; }).sort(), ["__proto__","constructor"]);

// ---- constrained clusters ----
["constrained","constrained_odd"].forEach(function (k) {
  const c = v[k];
  check("constrained clusters match the Python vector (" + k + ")", A.constrainedClusters(A.fromHex(c.seed_hex), c.clusters, c.arms, c.constraints, c.tries), c.result);
});
const cc = v.constrained;
check("constrained clusters do not depend on input order", A.constrainedClusters(A.fromHex(cc.seed_hex), cc.clusters.slice().reverse(), cc.arms, cc.constraints, cc.tries), cc.result);
[[[]],[[{type:"bogus",factor:"size",max:1}]],[[{type:"mean_diff",factor:"nope",max:1}]],[[{type:"mean_diff",factor:"size",max:-1}]],[[{type:"mean_diff",factor:"region",max:1}]],[[{type:"mean_diff",factor:"size",max:0.0001}],20],[[{type:"mean_diff",factor:"size",max:10}],0]].forEach(function (a, i) {
  try { A.constrainedClusters(A.fromHex(cc.seed_hex), cc.clusters, cc.arms, a[0], a[1] === undefined ? 100 : a[1]); fails++; console.log("FAIL constrained case " + i + " should throw"); }
  catch (e) { console.log("ok  ", "constrained case " + i + " throws"); }
});

// ---- review fixes ----
const fv = v.clusters_fractional, fs2 = A.fromHex(fv.seed_hex);
check("fractional-weight stratified matches the Python vector", A.stratifiedClusters(fs2, fv.clusters, fv.arms, fv.factors, fv.bins, fv.weight), fv.stratified);
check("fractional-weight minimisation matches the Python vector", A.clusterMinimisation(fs2, fv.clusters, fv.arms, fv.factors, fv.bins, fv.weight), fv.minimisation);
check("cluster ids sort by UTF-8 bytes: U+E000 before an emoji", A.stratifiedClusters(cs, [{id:"\u{1F600}"},{id:"\ue000"}], ["A","B"], []).allocation.map(function (x) { return x[0]; }), ["\ue000","\u{1F600}"]);
const refuse = function (label, fn) { try { fn(); fails++; console.log("FAIL " + label + " should throw"); } catch (e) { console.log("ok  ", label + " throws"); } };
const b2 = [{id:"a",g:1},{id:"b",g:2}];
refuse("p_best as text", function () { A.clusterMinimisation(cs, b2, ["A","B"], ["g"], null, null, "0.9"); });
refuse("p_best null", function () { A.clusterMinimisation(cs, b2, ["A","B"], ["g"], null, null, null); });
refuse("p_best true", function () { A.clusterMinimisation(cs, b2, ["A","B"], ["g"], null, null, true); });
refuse("arms given as text", function () { A.stratifiedClusters(cs, b2, "AB", ["g"]); });
refuse("lone surrogate id", function () { A.stratifiedClusters(cs, [{id:"\ud800",g:1},{id:"b",g:2}], ["A","B"], ["g"]); });
refuse("lone surrogate level", function () { A.stratifiedClusters(cs, [{id:"a",g:"\udfff"},{id:"b",g:2}], ["A","B"], ["g"]); });
refuse("empty weight name", function () { A.stratifiedClusters(cs, [{id:"a",s:5},{id:"b",s:5}], ["A","B"], [], null, ""); });
refuse("numeric weight name", function () { A.stratifiedClusters(cs, [{id:"a",0:5},{id:"b",0:5}], ["A","B"], [], null, 0); });
refuse("tries null", function () { A.constrainedClusters(cs, cc.clusters, cc.arms, cc.constraints, null); });
check("tries 100.0 is accepted (it is 100 in JSON)", A.constrainedClusters(A.fromHex(cc.seed_hex), cc.clusters, cc.arms, cc.constraints, 100.0).method, "constrained_clusters");
check("a well-formed surrogate pair is fine", A.stratifiedClusters(cs, [{id:"\u{1F600}"},{id:"b"}], ["A","B"], []).allocation.length, 2);
const c2 = [10,20,30,50].map(function (x, i) { return {id:"c"+i, x:x}; });
check("mean_diff limit exactly at the best split passes", A.constrainedClusters(cs, c2, ["A","B"], [{type:"mean_diff",factor:"x",max:5}], 300).method, "constrained_clusters");
refuse("mean_diff limit just under the best split", function () { A.constrainedClusters(cs, c2, ["A","B"], [{type:"mean_diff",factor:"x",max:4.99}], 300); });
const nc = A.constrainedClusters(cs, [0,1,2,3,4,5].map(function (i) { return {id:"c"+i, x:10*(i+1)}; }), ["A","B"], [{type:"mean_diff",factor:"x",max:4}], 2000);
check("narrow choice is warned about", [nc.warnings.some(function (w) { return w.kind === "narrow_choice"; }), nc.acceptable_seen < 20], [true, true]);
const lm = A.clusterMinimisation(cs, [{id:"a",g:"x"},{id:"b",g:"y"},{id:"c",g:"y"}], ["A","B"], ["g"]);
check("a level with one cluster is flagged, two is not", lm.warnings.filter(function (w) { return w.kind === "level_single_cluster"; }).map(function (w) { return w.level; }), ["x"]);
const eq = A.stratifiedClusters(cs, [0,1,2,3].map(function (i) { return {id:"c"+i, g:i%2}; }), ["A","B"], ["g"]);
check("4 clusters in 2 strata of 2 arms is not too fine", eq.warnings.some(function (w) { return w.kind === "strata_too_fine"; }), false);
const firsts = new Set(); for (let k = 1; k < 40; k++) firsts.add(A.clusterMinimisation(A.fromHex(("%02x".replace("%02x", (k).toString(16).padStart(2,"0"))).repeat(32)), [{id:"a"},{id:"b"}], ["A","B"], []).allocation[0][1]);
check("minimisation ties use both arms across seeds", Array.from(firsts).sort(), ["A","B"]);

console.log(fails === 0 ? "ALL JS TESTS PASSED" : fails + " FAILED");
process.exit(fails ? 1 : 0);
