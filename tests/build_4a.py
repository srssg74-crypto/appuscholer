"""Build 4a: slide fixes, classmate scenes, quiz merge. Run from the repo root: python3 build_4a.py index.html"""
import re, json, sys

SRC = sys.argv[1]
FIX = 'build-data/appuscholar-slide-fixes.json'
CM = ['build-data/classmates-01-10.json', 'build-data/classmates-11-20.json']
QZ = 'build-data/quiz128.json'
J = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))

lines = open(SRC, encoding='utf8').read().split('\n')
pat = re.compile(r'^apLibAdd\((\{.*\})\);?\s*$')
idx = [i for i, l in enumerate(lines) if pat.match(l)]
assert len(idx) == 20
L = [json.loads(pat.match(lines[i]).group(1)) for i in idx]
for l in L:
    assert len(l['slides']) == 34 and len(l['quiz']) == 4

# 1. slide fixes (1-based slide numbers on the full 34-slide list)
fixes = json.load(open(FIX))
for x in fixes:
    s = L[x['lecture'] - 1]['slides'][x['slide'] - 1]
    for k in ('board', 'boardH', 'say', 'sayH'):
        if x.get(k) is not None:
            s[k] = x[k]

# visuals that no longer matched the corrected words
s = L[18]['slides'][4]  # L19 S5: one plot each proves nothing
assert s['v']['k'] == 'compare'
s['v'] = {"k": "compare", "neutral": 1,
          "left": {"t": ["One plot each", "एक-एक टुकड़ा"], "items": [["Plot A: fertiliser", "टुकड़ा A: खाद"], ["Plot B: none", "टुकड़ा B: कोई खाद नहीं"]]},
          "right": {"t": ["Many plots", "कई टुकड़े"], "items": [["Fertiliser given by chance", "खाद संयोग से बाँटी"], ["Compare the averages", "औसत की तुलना"]]}}
s = L[16]['slides'][29]  # L17 S30: named qualified contact, else Tele-MANAS
assert s['v']['k'] == 'check'
s['v']['items'] = [{"l": ["Name a qualified contact (MHCA 2017)", "योग्य संपर्क व्यक्ति तय कीजिए (MHCA 2017)"]},
                   {"l": ["None named? Tele-MANAS 14416", "कोई तय नहीं? Tele-MANAS 14416"]},
                   {"l": ["Tell your ethics committee", "अपनी ethics committee को बताइए"]}]

# 2. classmates: each becomes a question slide and the professor's answer slide, same board
asks = {'dev': ('Dev asks', 'Dev का सवाल'), 'tara': ('Tara asks', 'Tara का सवाल')}
cms = json.load(open(CM[0])) + json.load(open(CM[1]))
assert len(cms) == 79
by_lec = {}
for c in cms:
    by_lec.setdefault(c['lecture'], []).append(c)
for n, group in by_lec.items():
    sl = L[n - 1]['slides']
    T = L[n - 1]['teacher']
    # place after the original slide; if that slide sits in a field-only block, move to the block's end
    placed = []
    for c in group:
        assert c['answer_who'] == T, (n, c['insert_after'])
        p = c['insert_after']
        while p < len(sl) and sl[p - 1].get('f') and sl[p].get('f'):
            p += 1
        placed.append((p, c))
    for p, c in sorted(placed, key=lambda t: -t[0]):  # from the end so earlier positions stay valid
        who = c['who']
        cast = [who, T]
        base = {"board": c['board'], "boardH": c['boardH'], "cast": cast, "cm": 1, "tone": "light"}
        q = dict(base, t=asks[who][0], tH=asks[who][1], who=who, say=c['say'], sayH=c['sayH'], e={who: "think", T: "smile"})
        a = dict(base, t="The answer", tH="जवाब", who=T, say=c['answer_say'], sayH=c['answer_sayH'], e={who: "smile", T: "smile"})
        sl[p:p] = [q, a]

# 3. quiz: lecture questions go into their lectures, step questions into AP_QUIZ (12 steps x 4 + 20 lectures x 4 = 128)
qz = json.load(open(QZ))
assert len(qz) == 128
keep = ('q', 'qH', 'o', 'oH', 'a', 'r', 'rH', 's', 'sH')
clean = lambda x: {k: x[k] for k in keep if x.get(k) not in (None, '')}
for x in qz:
    assert len(x['o']) == len(x['oH']) == len(x['r']) == len(x['rH']) and 0 <= x['a'] < len(x['o'])
lecq, stepq = {}, {}
for x in qz:
    g = x['id'].rsplit('-', 1)[0]
    (lecq if g.startswith('lecture-') else stepq).setdefault(g, []).append(clean(x))
for l in L:
    l['quiz'] = lecq.pop('lecture-' + l['id'])
assert not lecq
for i, l in zip(idx, L):
    lines[i] = 'apLibAdd(' + J(l) + ');'
qi = [i for i, l in enumerate(lines) if l.startswith('const AP_QUIZ={')]
assert len(qi) == 1
Q = json.loads(lines[qi[0]][len('const AP_QUIZ='):].rstrip().rstrip(';'))
for k in Q:
    Q[k] = stepq.pop('learn-' + k)
assert not stepq
lines[qi[0]] = 'const AP_QUIZ=' + J(Q) + ';'

open(SRC, 'w', encoding='utf8').write('\n'.join(lines))
print('slides per lecture:', [len(l['slides']) for l in L])
