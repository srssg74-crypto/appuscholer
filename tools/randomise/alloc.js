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

  function BlockGen(stream, arms, blockSizes) {
    this.st = stream; this.arms = arms; this.sizes = blockSizes; this.queue = [];
    var k = arms.length;
    for (var i = 0; i < blockSizes.length; i++) {
      // review finding 12: 0 % k === 0, so a block size of 0 used to pass this check. With an
      // empty queue, next() below would then do queue.shift() on an empty array and silently
      // return undefined as the "arm" for that position, corrupting the list with no error at all.
      if (blockSizes[i] <= 0 || blockSizes[i] % k) throw new Error("block size " + blockSizes[i] + " is not a positive multiple of " + k + " arms");
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
    blockSizes = blockSizes || [4, 6, 8];
    var g = new BlockGen(new HashStream(seed, "blocks"), arms, blockSizes);
    var out = [];
    for (var i = 0; i < n; i++) out.push(g.next());
    return out;
  }

  function stratifiedBlocks(seed, strata, arms, blockSizes) {
    blockSizes = blockSizes || [4, 6, 8];
    // review finding 12: a plain {} used as a map coerces every key to a string and already has
    // inherited properties (constructor, __proto__, toString, ...). A stratum label equal to one
    // of those names would find it already "in gens" via the prototype chain and crash calling
    // .next() on it; and numeric label 1 and string label "1" would collide into the same key,
    // merging two distinct strata that Python's dict (real type-sensitive keys) keeps separate.
    // Map has neither problem: no inherited keys, and keys keep their original type.
    var gens = new Map(), out = [];
    for (var i = 0; i < strata.length; i++) {
      var s = strata[i];
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
      var scores = {};
      arms.forEach(function (arm) {
        var total = 0;
        factors.forEach(function (f) {
          var lvl = person[f], byLevel = counts.get(f);
          if (!byLevel.has(lvl)) { var fresh = new Map(); arms.forEach(function (a) { fresh.set(a, 0); }); byLevel.set(lvl, fresh); }
          var c = byLevel.get(lvl);
          var after = arms.map(function (a) { return c.get(a) + (a === arm ? 1 : 0); });
          total += Math.max.apply(null, after) - Math.min.apply(null, after);
        });
        scores[arm] = total;
      });
      var best = Math.min.apply(null, arms.map(function (a) { return scores[a]; }));
      var bestArms = arms.filter(function (a) { return scores[a] === best; });
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
    var alloc = {};
    allocMap.forEach(function (v, k) { alloc[k] = v; });
    return alloc;
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
    permutedBlocks: permutedBlocks,
    stratifiedBlocks: stratifiedBlocks,
    minimisation: minimisation,
    matchedPairs: matchedPairs,
    williamsRows: williamsRows,
    crossover: crossover,
    resultHash: resultHash,
    canonicalJSON: canonicalJSON
  };
  if (typeof module !== "undefined" && module.exports) module.exports = Alloc;
  else root.Alloc = Alloc;
})(typeof globalThis !== "undefined" ? globalThis : this);
