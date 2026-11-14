/*
 * Appuscholar randomisation engine, JavaScript port of randomise.py (version 1.0.0).
 * Pure JavaScript, no dependencies, works offline in a single HTML file.
 * Must reproduce the Python output exactly. See test_alloc.js and vectors.json.
 */
(function (root) {
  "use strict";

  // ---------- SHA-256 and HMAC-SHA256 (pure JS) ----------
  var K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  function sha256(bytes) {
    var h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var l = bytes.length;
    var bitLenHi = Math.floor((l * 8) / 0x100000000);
    var bitLenLo = (l * 8) >>> 0;
    var padLen = ((l + 9 + 63) >> 6) << 6;
    var m = new Uint8Array(padLen);
    m.set(bytes);
    m[l] = 0x80;
    m[padLen - 8] = (bitLenHi >>> 24) & 0xff; m[padLen - 7] = (bitLenHi >>> 16) & 0xff;
    m[padLen - 6] = (bitLenHi >>> 8) & 0xff; m[padLen - 5] = bitLenHi & 0xff;
    m[padLen - 4] = (bitLenLo >>> 24) & 0xff; m[padLen - 3] = (bitLenLo >>> 16) & 0xff;
    m[padLen - 2] = (bitLenLo >>> 8) & 0xff; m[padLen - 1] = bitLenLo & 0xff;
    var w = new Array(64);
    for (var off = 0; off < padLen; off += 64) {
      for (var i = 0; i < 16; i++) {
        var j = off + i * 4;
        w[i] = ((m[j] << 24) | (m[j + 1] << 16) | (m[j + 2] << 8) | m[j + 3]) >>> 0;
      }
      for (i = 16; i < 64; i++) {
        var s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
        var s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
      }
      var a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
      for (i = 0; i < 64; i++) {
        var S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        var ch = (e & f) ^ (~e & g);
        var t1 = (hh + S1 + ch + K[i] + w[i]) >>> 0;
        var S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        var maj = (a & b) ^ (a & c) ^ (b & c);
        var t2 = (S0 + maj) >>> 0;
        hh = g; g = f; f = e; e = (d + t1) >>> 0;
        d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      h[0] = (h[0] + a) >>> 0; h[1] = (h[1] + b) >>> 0; h[2] = (h[2] + c) >>> 0; h[3] = (h[3] + d) >>> 0;
      h[4] = (h[4] + e) >>> 0; h[5] = (h[5] + f) >>> 0; h[6] = (h[6] + g) >>> 0; h[7] = (h[7] + hh) >>> 0;
    }
    var out = new Uint8Array(32);
    for (i = 0; i < 8; i++) {
      out[i * 4] = h[i] >>> 24; out[i * 4 + 1] = (h[i] >>> 16) & 0xff;
      out[i * 4 + 2] = (h[i] >>> 8) & 0xff; out[i * 4 + 3] = h[i] & 0xff;
    }
    return out;
  }
  function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }

  function concat(a, b) {
    var out = new Uint8Array(a.length + b.length);
    out.set(a, 0); out.set(b, a.length);
    return out;
  }
  function utf8(s) { return new TextEncoder().encode(s); }

  function hmac(key, msg) {
    if (key.length > 64) key = sha256(key);
    var k = new Uint8Array(64);
    k.set(key);
    var ipad = new Uint8Array(64), opad = new Uint8Array(64);
    for (var i = 0; i < 64; i++) { ipad[i] = k[i] ^ 0x36; opad[i] = k[i] ^ 0x5c; }
    return sha256(concat(opad, sha256(concat(ipad, msg))));
  }

  function hex(bytes) {
    var s = "";
    for (var i = 0; i < bytes.length; i++) s += (bytes[i] < 16 ? "0" : "") + bytes[i].toString(16);
    return s;
  }
  function fromHex(s) {
    var out = new Uint8Array(s.length / 2);
    for (var i = 0; i < out.length; i++) out[i] = parseInt(s.substr(i * 2, 2), 16);
    return out;
  }

  // ---------- Deterministic stream (same as HashStream in Python) ----------
  var TWO64 = 18446744073709551616n;

  function HashStream(seed, label) {
    this._key = hmac(seed, utf8(label));
    this._counter = 0;
    this._buf = new Uint8Array(0);
    this._pos = 0;
  }
  HashStream.prototype._fill = function (need) {
    while (this._buf.length - this._pos < need) {
      var cb = new Uint8Array(8);
      var c = BigInt(this._counter);
      for (var i = 7; i >= 0; i--) { cb[i] = Number(c & 0xffn); c >>= 8n; }
      var block = sha256(concat(this._key, cb));
      var rest = this._buf.slice(this._pos);
      this._buf = concat(rest, block);
      this._pos = 0;
      this._counter++;
    }
  };
  HashStream.prototype._next64 = function () {
    this._fill(8);
    var v = 0n;
    for (var i = 0; i < 8; i++) v = (v << 8n) | BigInt(this._buf[this._pos + i]);
    this._pos += 8;
    return v;
  };
  HashStream.prototype.randbelow = function (n) {
    if (n <= 0) throw new Error("n must be positive");
    var N = BigInt(n);
    var limit = (TWO64 / N) * N;
    for (;;) {
      var x = this._next64();
      if (x < limit) return Number(x % N);
    }
  };
  HashStream.prototype.uniform = function () {
    return Number(this._next64()) / 18446744073709551616;
  };
  HashStream.prototype.shuffle = function (items) {
    var a = items.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = this.randbelow(i + 1);
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  };

  // ---------- Commitment ----------
  function commitment(seed) {
    return hex(sha256(concat(utf8("appuscholar-commit-v1:"), seed)));
  }
  function planHash(plan) {
    return hex(sha256(utf8(canonicalJSON(plan))));
  }
  function commitmentV2(seed, planSha256Hex) {
    var planBytes = new Uint8Array(planSha256Hex.length / 2);
    for (var i = 0; i < planBytes.length; i++) planBytes[i] = parseInt(planSha256Hex.substr(i * 2, 2), 16);
    return hex(sha256(concat(concat(utf8("appuscholar-commit-v2:"), seed), planBytes)));
  }

  // ---------- Methods ----------
  function simple(seed, n, arms, probs) {
    var st = new HashStream(seed, "simple");
    if (!probs) probs = arms.map(function () { return 1 / arms.length; });
    var cum = [], total = 0;
    for (var i = 0; i < probs.length; i++) { total += probs[i]; cum.push(total); }
    var out = [];
    for (var k = 0; k < n; k++) {
      var u = st.uniform(), picked = arms[arms.length - 1];
      for (var j = 0; j < arms.length; j++) { if (u < cum[j]) { picked = arms[j]; break; } }
      out.push(picked);
    }
    return out;
  }

  // Default block sizes follow the arm count: 2k, 3k, 4k. A fixed [4,6,8] only fits two arms
  // (second review, finding 5). For two arms this is still [4,6,8], so the vectors are unchanged.
  function defaultBlocks(k) { return [2 * k, 3 * k, 4 * k]; }

  function BlockGen(stream, arms, blockSizes) {
    this.st = stream; this.arms = arms; this.sizes = blockSizes; this.queue = [];
    var k = arms.length;
    if (!Array.isArray(blockSizes) || blockSizes.length === 0) throw new Error("block sizes must be a non-empty list");
    for (var i = 0; i < blockSizes.length; i++) {
      var b = blockSizes[i];
      // review finding 12: 0 % k === 0, so a block size of 0 used to pass this check. With an
      // empty queue, next() below would then do queue.shift() on an empty array and silently
      // return undefined as the "arm" for that position, corrupting the list with no error at all.
      // Second review: NaN <= 0 and NaN % k are both false, so NaN slipped through the same way,
      // as did 4.5 (4.5 % 2 is 0.5, caught) but not e.g. 6.0000000001 % 3. Require a finite
      // positive integer, same as the Python engine's isinstance(b, int) check.
      if (typeof b !== "number" || !isFinite(b) || Math.floor(b) !== b || b <= 0 || b % k || b > 10000) throw new Error("block size " + b + " is not a positive whole multiple of " + k + " arms (max 10000)");
    }
  }
  BlockGen.prototype.next = function () {
    if (this.queue.length === 0) {
      var size = this.sizes[this.st.randbelow(this.sizes.length)];
      var block = [];
      for (var i = 0; i < size; i++) block.push(this.arms[i % this.arms.length]);
      this.queue = this.st.shuffle(block);
    }
    return this.queue.shift();
  };

  function permutedBlocks(seed, n, arms, blockSizes) {
    blockSizes = blockSizes || defaultBlocks(arms.length);
    var g = new BlockGen(new HashStream(seed, "blocks"), arms, blockSizes);
    var out = [];
    for (var i = 0; i < n; i++) out.push(g.next());
    return out;
  }

  // One string per stratum, the same rule as randomise.py's stratum_label: String(label), so
  // true -> "true" and 1 -> "1" in both engines. Second review, finding 12: 1 and "1" used to be
  // two gens sharing one stream key ("stratum:1"), i.e. two strata with identical sequences,
  // and true/1 diverged from Python (str(True) is "True"). Labels should be strings anyway.
  // Third review: String(x) and Python's str(x) differ for floats, null, arrays and large numbers,
  // and a different label keys a different stream. Only strings, whole numbers and booleans are
  // accepted; anything else is a protocol error, thrown here and raised in randomise.py alike.
  function stratumLabel(s) {
    if (typeof s === "string") return s;
    if (typeof s === "boolean") return s ? "true" : "false";
    if (typeof s === "number" && Number.isSafeInteger(s)) return String(s);
    throw new Error("stratum label must be a string or whole number, got " + (s === null ? "null" : typeof s) + ": " + JSON.stringify(s));
  }

  function stratifiedBlocks(seed, strata, arms, blockSizes) {
    blockSizes = blockSizes || defaultBlocks(arms.length);
    // review finding 12: a plain {} used as a map coerces every key to a string and already has
    // inherited properties (constructor, __proto__, toString, ...). A stratum label equal to one
    // of those names would find it already "in gens" via the prototype chain and crash calling
    // .next() on it; and numeric label 1 and string label "1" would collide into the same key,
    // merging two distinct strata that Python's dict (real type-sensitive keys) keeps separate.
    // Map has neither problem: no inherited keys, and keys keep their original type.
    var gens = new Map(), out = [];
    for (var i = 0; i < strata.length; i++) {
      var s = stratumLabel(strata[i]);
      if (!gens.has(s)) gens.set(s, new BlockGen(new HashStream(seed, "stratum:" + s), arms, blockSizes));
      out.push(gens.get(s).next());
    }
    return out;
  }

  function minimisation(seed, people, arms, factors, pBest) {
    if (pBest === undefined) pBest = 0.8;
    var st = new HashStream(seed, "minimisation");
    // review finding 12: plain {} objects used as maps coerce keys to strings and inherit
    // Object.prototype properties (constructor, __proto__, ...), so a factor level equal to one
    // of those names would find a bogus "existing" entry via the prototype chain instead of
    // initializing fresh counts, and a numeric level 1 would collide with a string level "1" -
    // two levels Python's dict (real, type-sensitive keys) keeps separate. Map avoids both.
    var counts = new Map();
    factors.forEach(function (f) { counts.set(f, new Map()); });
    var out = [];
    people.forEach(function (person) {
      // second review, finding 12: this was a plain {}, so an arm named "__proto__" threw.
      var scores = new Map();
      arms.forEach(function (arm) {
        var total = 0;
        factors.forEach(function (f) {
          var lvl = person[f], byLevel = counts.get(f);
          if (!byLevel.has(lvl)) { var fresh = new Map(); arms.forEach(function (a) { fresh.set(a, 0); }); byLevel.set(lvl, fresh); }
          var c = byLevel.get(lvl);
          var after = arms.map(function (a) { return c.get(a) + (a === arm ? 1 : 0); });
          total += Math.max.apply(null, after) - Math.min.apply(null, after);
        });
        scores.set(arm, total);
      });
      var best = Math.min.apply(null, arms.map(function (a) { return scores.get(a); }));
      var bestArms = arms.filter(function (a) { return scores.get(a) === best; });
      var arm;
      if (st.uniform() < pBest) {
        arm = bestArms[st.randbelow(bestArms.length)];
      } else {
        var others = arms.filter(function (a) { return bestArms.indexOf(a) < 0; });
        if (others.length === 0) others = arms.slice();
        arm = others[st.randbelow(others.length)];
      }
      factors.forEach(function (f) { var c = counts.get(f).get(person[f]); c.set(arm, c.get(arm) + 1); });
      out.push(arm);
    });
    return out;
  }

  function matchedPairs(seed, pairs, armNames) {
    armNames = armNames || ["A", "B"];
    var st = new HashStream(seed, "pairs");
    // same reasoning as above: a unit id of "constructor" or similar should not collide with
    // Object.prototype when used as a plain-object key.
    var allocMap = new Map();
    pairs.forEach(function (p) {
      if (st.randbelow(2) === 0) { allocMap.set(p[0], armNames[0]); allocMap.set(p[1], armNames[1]); }
      else { allocMap.set(p[1], armNames[0]); allocMap.set(p[0], armNames[1]); }
    });
    // Second review, finding 12: copying into a plain {} lost a unit called "__proto__" (the
    // assignment set the prototype instead of a key) and merged 1 with "1". A null-prototype
    // object has no __proto__ setter, so every unit id lands as an own key; ids are coerced to
    // strings here, as they are in the CSV the Python engine reads them from, and as
    // Object.defineProperty keeps "__proto__" as an ordinary own property.
    var alloc = Object.create(null);
    allocMap.forEach(function (v, k) {
      Object.defineProperty(alloc, String(k), { value: v, enumerable: true, writable: true, configurable: true });
    });
    return alloc;
  }

  // ---- Cluster trials (mirrors randomise.py; see the rules in its comments) ----
  var MAX_WEIGHT = 1e9, MIN_WEIGHT = 1e-3;

  function isNum(x) { return typeof x === "number" && isFinite(x); }
  function binLevel(value, cuts) {
    if (!isNum(value)) throw new Error("a binned factor needs a finite number, got " + JSON.stringify(value));
    var i = 0;
    while (i < cuts.length && value >= cuts[i]) i++;
    return i;
  }
  function cmpBytes(a, b) {
    var x = utf8(a), y = utf8(b), n = Math.min(x.length, y.length);
    for (var i = 0; i < n; i++) if (x[i] !== y[i]) return x[i] - y[i];
    return x.length - y.length;
  }
  function sortedByBytes(keys) { return keys.slice().sort(cmpBytes); }
  function levelsKey(levels) { return JSON.stringify(levels); }

  function clusterTable(clusters, arms, factors, bins, weight) {
    arms = Array.prototype.slice.call(arms || []);
    factors = Array.prototype.slice.call(factors || []);
    bins = bins || {};
    var ok = function (a) { return typeof a === "string" && a.length > 0; };
    if (arms.length < 2 || new Set(arms).size !== arms.length || !arms.every(ok))
      throw new Error("arms must be two or more different non-empty strings");
    if (new Set(factors).size !== factors.length || !factors.every(ok))
      throw new Error("factors must be different non-empty strings");
    Object.keys(bins).forEach(function (f) {
      var cuts = bins[f];
      if (factors.indexOf(f) < 0) throw new Error("bins given for '" + f + "', which is not a factor");
      if (!Array.isArray(cuts) || !cuts.length || !cuts.every(isNum) || cuts.some(function (c, i) { return i < cuts.length - 1 && c >= cuts[i + 1]; }))
        throw new Error("bins for '" + f + "' must be a non-empty, strictly increasing list of numbers");
    });
    if (!Array.isArray(clusters) || clusters.length < 2) throw new Error("a cluster trial needs a list of at least two clusters");
    var seen = new Set(), rows = [];
    clusters.forEach(function (c) {
      if (!c || typeof c !== "object" || Array.isArray(c) || !ok(c.id)) throw new Error("every cluster needs a non-empty string id");
      var cid = c.id;
      if (seen.has(cid)) throw new Error("cluster id '" + cid + "' appears twice");
      seen.add(cid);
      var levels = [];
      factors.forEach(function (f) {
        if (!Object.prototype.hasOwnProperty.call(c, f)) throw new Error("cluster '" + cid + "' has no value for factor '" + f + "'");
        if (Object.prototype.hasOwnProperty.call(bins, f)) levels.push([f, "b" + binLevel(c[f], bins[f])]);
        else levels.push([f, stratumLabel(c[f])]);
      });
      var w = null;
      if (weight !== null && weight !== undefined) {
        w = Object.prototype.hasOwnProperty.call(c, weight) ? c[weight] : undefined;
        if (!isNum(w) || w < MIN_WEIGHT || w > MAX_WEIGHT)
          throw new Error("cluster '" + cid + "': '" + weight + "' must be a number from " + MIN_WEIGHT + " to " + MAX_WEIGHT);
      }
      rows.push({ id: cid, levels: levels, weight: w });
    });
    rows.sort(function (a, b) { return cmpBytes(a.id, b.id); });
    return { rows: rows, arms: arms, factors: factors };
  }

  function armTotals(rows, alloc, arms, weight) {
    var hasW = weight !== null && weight !== undefined;
    return arms.map(function (a) {
      var mine = rows.filter(function (r) { return alloc.get(r.id) === a; });
      var w = null;
      if (hasW) { w = 0; mine.forEach(function (r) { w += r.weight; }); }
      return { arm: a, clusters: mine.length, weight: w };
    });
  }

  function stratifiedClusters(seed, clusters, arms, factors, bins, weight) {
    var t = clusterTable(clusters, arms, factors, bins, weight), rows = t.rows;
    arms = t.arms;
    var k = arms.length, strata = new Map();
    rows.forEach(function (r) {
      var key = levelsKey(r.levels);
      if (!strata.has(key)) strata.set(key, []);
      strata.get(key).push(r);
    });
    var globalCounts = new Map(), alloc = new Map(), detail = [], warnings = [];
    arms.forEach(function (a) { globalCounts.set(a, 0); });
    sortedByBytes(Array.from(strata.keys())).forEach(function (key) {
      var members = strata.get(key), m = members.length;
      var stream = new HashStream(seed, "cluster-stratum:" + key);
      var base = Math.floor(m / k), spare = m % k;
      var order = []; for (var i = 0; i < k; i++) order.push(i);
      var shuffled = stream.shuffle(order);
      var ranked = shuffled.slice().sort(function (x, y) {
        var d = globalCounts.get(arms[x]) - globalCounts.get(arms[y]);
        return d !== 0 ? d : shuffled.indexOf(x) - shuffled.indexOf(y);
      });
      var extra = new Set(ranked.slice(0, spare)), labels = [];
      arms.forEach(function (a, i) {
        var q = base + (extra.has(i) ? 1 : 0);
        for (var j = 0; j < q; j++) labels.push(a);
      });
      labels = stream.shuffle(labels);
      var counts = new Map(); arms.forEach(function (a) { counts.set(a, 0); });
      members.forEach(function (r, idx) {
        var lab = labels[idx];
        alloc.set(r.id, lab);
        globalCounts.set(lab, globalCounts.get(lab) + 1);
        counts.set(lab, counts.get(lab) + 1);
      });
      detail.push({ levels: members[0].levels, clusters: m, counts: arms.map(function (a) { return [a, counts.get(a)]; }) });
      if (m < k) warnings.push({ kind: "stratum_missing_arm", levels: members[0].levels, clusters: m });
    });
    if (strata.size * k > rows.length) warnings.push({ kind: "strata_too_fine", strata: strata.size, clusters: rows.length, arms: k });
    return {
      method: "stratified_clusters",
      allocation: rows.map(function (r) { return [r.id, alloc.get(r.id)]; }),
      strata: detail,
      arm_totals: armTotals(rows, alloc, arms, weight),
      warnings: warnings
    };
  }

  function clusterMinimisation(seed, clusters, arms, factors, bins, weight, pBest) {
    if (pBest === undefined || pBest === null) pBest = 0.8;
    if (!(pBest > 0.5 && pBest <= 1)) throw new Error("p_best should be between 0.5 and 1");
    var t = clusterTable(clusters, arms, factors, bins, weight), rows = t.rows;
    arms = t.arms;
    var hasW = weight !== null && weight !== undefined, n = rows.length, meanW = null;
    if (hasW) { var tot = 0; rows.forEach(function (r) { tot += r.weight; }); meanW = tot / n; }
    var orderStream = new HashStream(seed, "cluster-minimisation:order");
    var stream = new HashStream(seed, "cluster-minimisation");
    var idxs = []; for (var i = 0; i < n; i++) idxs.push(i);
    var order = orderStream.shuffle(idxs);
    function fresh() {
      var g = { n: new Map(), w: new Map() };
      arms.forEach(function (a) { g.n.set(a, 0); g.w.set(a, 0); });
      return g;
    }
    var overall = fresh(), groups = new Map();
    rows.forEach(function (r) {
      r.levels.forEach(function (fl) { var key = levelsKey(fl); if (!groups.has(key)) groups.set(key, fresh()); });
    });
    function spread(tot, arm, add) {
      var lo = Infinity, hi = -Infinity;
      arms.forEach(function (a) {
        var v = tot.get(a) + (a === arm ? add : 0);
        if (v < lo) lo = v; if (v > hi) hi = v;
      });
      return hi - lo;
    }
    var alloc = new Map();
    order.forEach(function (idx) {
      var r = rows[idx], wn = hasW ? r.weight / meanW : 0;
      var members = [overall].concat(r.levels.map(function (fl) { return groups.get(levelsKey(fl)); }));
      var scores = new Map(), best = Infinity;
      arms.forEach(function (a) {
        var total = 0;
        members.forEach(function (g) {
          total += spread(g.n, a, 1);
          if (hasW) total += spread(g.w, a, wn);
        });
        scores.set(a, total);
        if (total < best) best = total;
      });
      var bestArms = arms.filter(function (a) { return scores.get(a) === best; }), arm;
      if (stream.uniform() < pBest) {
        arm = bestArms[stream.randbelow(bestArms.length)];
      } else {
        var others = arms.filter(function (a) { return bestArms.indexOf(a) < 0; });
        if (!others.length) others = arms;
        arm = others[stream.randbelow(others.length)];
      }
      members.forEach(function (g) { g.n.set(arm, g.n.get(arm) + 1); g.w.set(arm, g.w.get(arm) + wn); });
      alloc.set(r.id, arm);
    });
    var balance = [], warnings = [];
    sortedByBytes(Array.from(groups.keys())).forEach(function (key) {
      var fl = JSON.parse(key), g = groups.get(key), m = 0;
      arms.forEach(function (a) { m += g.n.get(a); });
      var entry = { factor: fl[0], level: fl[1], clusters: m, counts: arms.map(function (a) { return [a, g.n.get(a)]; }) };
      if (hasW) {
        entry.weights = arms.map(function (a) {
          var sum = 0;
          rows.forEach(function (rr) {
            if (alloc.get(rr.id) === a && rr.levels.some(function (x) { return x[0] === fl[0] && x[1] === fl[1]; })) sum += rr.weight;
          });
          return [a, sum];
        });
      }
      balance.push(entry);
      if (m < 2) warnings.push({ kind: "level_single_cluster", factor: fl[0], level: fl[1] });
    });
    return {
      method: "cluster_minimisation",
      processing_order: order.map(function (i) { return rows[i].id; }),
      allocation: rows.map(function (r) { return [r.id, alloc.get(r.id)]; }),
      arm_totals: armTotals(rows, alloc, arms, weight),
      balance: balance,
      warnings: warnings
    };
  }

  var MAX_TRIES = 200000;
  function constrainedClusters(seed, clusters, arms, constraints, tries) {
    if (tries === undefined || tries === null) tries = 10000;
    var t = clusterTable(clusters, arms, [], null, null), rows = t.rows;
    arms = t.arms;
    if (arms.length !== 2) throw new Error("constrained_clusters handles two arms");
    if (!Number.isInteger(tries) || tries < 1 || tries > MAX_TRIES) throw new Error("tries must be a whole number from 1 to " + MAX_TRIES);
    if (!Array.isArray(constraints) || !constraints.length) throw new Error("give at least one constraint");
    var byid = new Map(); clusters.forEach(function (c) { byid.set(c.id, c); });
    var prepared = constraints.map(function (c) {
      if (!c || typeof c !== "object" || (c.type !== "mean_diff" && c.type !== "count_diff")) throw new Error("a constraint needs type mean_diff or count_diff");
      var f = c.factor, mx = c.max;
      if (typeof f !== "string" || !f) throw new Error("a constraint needs a factor name");
      if (!isNum(mx) || mx < 0) throw new Error("a constraint max must be a finite number, zero or more");
      var vals = rows.map(function (r) {
        var rec = byid.get(r.id);
        if (!Object.prototype.hasOwnProperty.call(rec, f)) throw new Error("cluster '" + r.id + "' has no value for factor '" + f + "'");
        var x = rec[f];
        if (c.type === "mean_diff") {
          if (!isNum(x)) throw new Error("mean_diff needs a finite number for '" + f + "' on cluster '" + r.id + "'");
          return x;
        }
        return stratumLabel(x);
      });
      return { kind: c.type, vals: vals, mx: mx };
    });
    var n = rows.length, stream = new HashStream(seed, "constrained-clusters");
    var lo = Math.floor(n / 2), hi = n - lo;
    var firstIsBig = n % 2 === 1 && stream.randbelow(2) === 0;
    var n0 = firstIsBig ? hi : lo;
    var idx = []; for (var q = 0; q < n; q++) idx.push(q);
    for (var attempt = 1; attempt <= tries; attempt++) {
      var picks = stream.shuffle(idx), in0 = new Set(picks.slice(0, n0)), ok = true;
      for (var pi = 0; pi < prepared.length && ok; pi++) {
        var pc = prepared[pi];
        if (pc.kind === "mean_diff") {
          var s0 = 0, s1 = 0;
          for (var i = 0; i < n; i++) { if (in0.has(i)) s0 += pc.vals[i]; else s1 += pc.vals[i]; }
          if (Math.abs(s0 / n0 - s1 / (n - n0)) > pc.mx) ok = false;
        } else {
          var lv = new Map();
          for (var j = 0; j < n; j++) {
            if (!lv.has(pc.vals[j])) lv.set(pc.vals[j], [0, 0]);
            lv.get(pc.vals[j])[in0.has(j) ? 0 : 1]++;
          }
          lv.forEach(function (e) { if (Math.abs(e[0] - e[1]) > pc.mx) ok = false; });
        }
      }
      if (ok) {
        return {
          method: "constrained_clusters",
          allocation: rows.map(function (r, i) { return [r.id, in0.has(i) ? arms[0] : arms[1]]; }),
          attempts: attempt,
          arm_totals: [{ arm: arms[0], clusters: n0 }, { arm: arms[1], clusters: n - n0 }]
        };
      }
    }
    throw new Error("none of " + tries + " random allocations met the constraints; loosen them");
  }

  function williamsRows(k) {
    if (k < 2) throw new Error("need at least two treatments");
    var seq = [0], lo = 1, hi = k - 1, takeLo = true;
    while (seq.length < k) {
      if (takeLo) { seq.push(lo); lo++; } else { seq.push(hi); hi--; }
      takeLo = !takeLo;
    }
    var rows = [];
    for (var i = 0; i < k; i++) rows.push(seq.map(function (f) { return (f + i) % k; }));
    if (k % 2) rows = rows.concat(rows.map(function (r) { return r.slice().reverse(); }));
    return rows;
  }

  function crossover(seed, n, treatments) {
    var rows = williamsRows(treatments.length);
    var order = [];
    for (var i = 0; i < n; i++) order.push(rows[i % rows.length]);
    order = new HashStream(seed, "crossover").shuffle(order);
    return order.map(function (row) { return row.map(function (t) { return treatments[t]; }); });
  }

  // ---------- Verification helpers ----------
  function canonicalJSON(obj) {
    // Matches Python json.dumps(obj, sort_keys=True, separators=(",", ":")) for arrays of
    // strings and numbers and plain objects of those. Used for result hashes.
    if (obj === null) return "null";
    if (Array.isArray(obj)) return "[" + obj.map(canonicalJSON).join(",") + "]";
    if (typeof obj === "object") {
      return "{" + Object.keys(obj).sort().map(function (k) {
        return JSON.stringify(k) + ":" + canonicalJSON(obj[k]);
      }).join(",") + "}";
    }
    return JSON.stringify(obj);
  }
  function resultHash(result) { return hex(sha256(utf8(canonicalJSON(result)))); }

  var Alloc = {
    VERSION: "1.0.0",
    sha256: sha256, hmac: hmac, hex: hex, fromHex: fromHex, utf8: utf8,
    HashStream: HashStream,
    commitment: commitment,
    planHash: planHash,
    commitmentV2: commitmentV2,
    simple: simple,
    defaultBlocks: defaultBlocks,
    stratumLabel: stratumLabel,
    permutedBlocks: permutedBlocks,
    stratifiedBlocks: stratifiedBlocks,
    minimisation: minimisation,
    matchedPairs: matchedPairs,
    binLevel: binLevel,
    stratifiedClusters: stratifiedClusters,
    clusterMinimisation: clusterMinimisation,
    constrainedClusters: constrainedClusters,
    williamsRows: williamsRows,
    crossover: crossover,
    resultHash: resultHash,
    canonicalJSON: canonicalJSON
  };
  if (typeof module !== "undefined" && module.exports) module.exports = Alloc;
  else root.Alloc = Alloc;
})(typeof globalThis !== "undefined" ? globalThis : this);
