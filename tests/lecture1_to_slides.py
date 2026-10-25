"""Turn lecture-01-v2.md into the app's slide list for the lecture 'reading-a-p-value'."""
import re, json, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'lecture-01-v2.md'
md = open(SRC, encoding='utf8').read()
md = md.split('# Lecture 1: Reading a p-value', 1)[1].split('# Numbers checked', 1)[0]

# Board lines, kept short so they fit the board. (EN line 1, EN line 2, HI line 1, HI line 2)
B = {
 1: ("Tara's study", "p = .034", "Tara की study", "p = .034"),
 4: ("Good morning!", "Reading a p-value", "सुप्रभात!", "p-value को पढ़ना"),
 6: ("Goal 1: say what p means", "Goal 2: catch the mistakes about p", "लक्ष्य 1: p का मतलब एक वाक्य में", "लक्ष्य 2: p की आम ग़लतियाँ पकड़ना"),
 9: ("Does a 10-minute breathing routine", "lower exam anxiety?", "क्या 10 मिनट का breathing routine", "exam की घबराहट कम करता है?"),
 10: ("60 second-year students", "Lottery: 30 and 30", "60 second-year students", "Lottery से 30 और 30"),
 11: ("Group A: breathing routine, 14 days", "Group B: as usual", "Group A: breathing routine, 14 दिन", "Group B: पहले जैसा"),
 13: ("20 questions, anxiety score 20–80", "Higher score = more anxiety", "20 सवाल, anxiety score 20–80", "ज़्यादा score = ज़्यादा घबराहट"),
 14: ("Group A average: 41.2", "Group B average: 46.8", "Group A का औसत: 41.2", "Group B का औसत: 46.8"),
 15: ("Gap = 46.8 − 41.2 = 5.6 points", "Breathing routine, or chance?", "फ़र्क़ = 46.8 − 41.2 = 5.6 अंक", "Breathing routine या संयोग?"),
 16: ("One class, split by lottery", "Same test, averages still differ", "एक class, lottery से दो हिस्से", "एक ही test, फिर भी औसत अलग"),
 18: ("Slept well, headache, calm by nature", "Lottery mixes them unevenly", "नींद, सिरदर्द, शांत स्वभाव", "Lottery इन्हें बराबर नहीं बाँटती"),
 19: ("Chance variation =", "a gap made by luck alone", "Chance variation =", "सिर्फ़ संयोग से बना फ़र्क़"),
 21: ("10 tosses", "9 heads and 1 tail", "10 उछाल", "9 head और 1 tail"),
 23: ("10 tosses: 1,024 possible orders", "9 or 10 heads: only 11 orders", "10 उछाल: 1,024 संभव क्रम", "9 या 10 head: सिर्फ़ 11 क्रम"),
 24: ("11 ÷ 1,024 = 0.011", "about 1 time in 100", "11 ÷ 1,024 = 0.011", "लगभग सौ में एक बार"),
 26: ("Null hypothesis =", "the 'nothing is happening' story", "शून्य परिकल्पना (null hypothesis) =", "'कुछ नहीं हो रहा' वाली कहानी"),
 28: ("p-value = chance of a result this big,", "IF the null hypothesis is true", "p-value = इतने बड़े result का chance,", "अगर null hypothesis सच हो"),
 29: ("In simple words:", "how often chance alone gives this gap", "सरल शब्दों में:", "सिर्फ़ संयोग से इतना फ़र्क़ कितनी बार"),
 31: ("The computer finds .034 by a t-test", "(Lecture 4)", "Computer .034, t-test से निकालता है", "(Lecture 4)"),
 32: ("100 colleges, useless routine", "gap of 5.6+ in only 3 or 4", "100 colleges, बेकार routine", "5.6+ का फ़र्क़ सिर्फ़ 3–4 में"),
 34: ("Quick check:", "does p say how likely the null is?", "छोटी जाँच:", "क्या p, null की संभावना बताता है?"),
 36: ("Dev: '3.4% chance Tara is wrong'", "✗", "Dev: 'Tara के ग़लत होने का 3.4% chance'", "✗"),
 38: ("p = chance of the data, if null is true", "NOT the chance that null is true", "p = null सच हो तो data का chance", "null के सच होने का chance नहीं"),
 39: ("Tara: 'proven'", "✗", "Tara: 'साबित'", "✗"),
 41: ("p-value depends on two things:", "size of the gap, number of students", "p-value दो चीज़ों पर टिकी है:", "फ़र्क़ का आकार, students की गिनती"),
 42: ("30 per group: chance gaps ≈ 2.6", "10,000 per group: chance gaps ≈ 0.14", "हर group में 30: संयोग का फ़र्क़ ≈ 2.6", "हर group में 10,000: ≈ 0.14"),
 43: ("0.5 ÷ 0.14 ≈ 3.5 times, so p < .001", "yet nobody notices 0.5 point", "0.5 ÷ 0.14 ≈ 3.5 गुना, इसलिए p < .001", "पर आधा अंक किसी को नहीं दिखता"),
 45: ("Scores: 40, 45, 50, 55, 60", "Average 50; distances 10, 5, 0, 5, 10", "Scores: 40, 45, 50, 55, 60", "औसत 50; दूरियाँ 10, 5, 0, 5, 10"),
 46: ("Standard deviation = usual distance", "from the average (here about 8)", "मानक विचलन (standard deviation) =", "औसत से आम दूरी (यहाँ लगभग 8)"),
 48: ("Cohen's d = gap ÷ standard deviation", "Tara: 5.6 ÷ 10 = 0.56", "Cohen's d = फ़र्क़ ÷ standard deviation", "Tara: 5.6 ÷ 10 = 0.56"),
 49: ("0.2 small, 0.5 medium, 0.8 large", "Tara's d = 0.56: medium", "0.2 छोटा, 0.5 मध्यम, 0.8 बड़ा", "Tara का d = 0.56: मध्यम"),
 52: (".05 = 1 in 20, a habit since the 1920s", ".049 and .051: almost the same", ".05 = बीस में एक, 1920 से आदत", ".049 और .051: लगभग बराबर"),
 53: ("Two-tailed: both directions (use this)", "One-tailed: one way, chosen first", "Two-tailed: दोनों तरफ़ (यही लें)", "One-tailed: एक तरफ़, पहले से तय"),
 54: ("1 test: 95% no false alarm", "15 tests: 0.95 × ... (15 times) = 46%", "1 test: 95% कोई झूठा अलार्म नहीं", "15 tests: 0.95 × ... (15 बार) = 46%"),
 55: ("At least one false alarm:", "100% − 46% = 54%", "कम से कम एक झूठा अलार्म:", "100% − 46% = 54%"),
 57: ("Plan the tests before the data", "Report every test you ran", "Data से पहले tests तय करें", "हर test की report दें"),
 58: ("t(58) = 2.17, p = .034, d = 0.56", "58 = 60 students − 2 groups", "t(58) = 2.17, p = .034, d = 0.56", "58 = 60 students − 2 groups"),
 59: ("p: how often, if nothing were happening", "Not the chance you are right. Not the size.", "p: कुछ न हो, तो कितनी बार", "सही होने का chance नहीं, असर का आकार नहीं"),
 60: ("Exit question:", "Tara's p = .034. What does it mean?", "जाने से पहले सवाल:", "Tara का p = .034, मतलब क्या?"),
 62: ("Next class: effect size, with Dr Meera", "Thank you!", "अगली class: effect size, Dr Meera के साथ", "धन्यवाद!"),
}
PART_HI = {
 "Before class": "शुरुआत", "Tara's study": "Tara की study", "Why chance matters": "संयोग क्यों मायने रखता है",
 "The null hypothesis and the p-value": "Null hypothesis और p-value", "The two mistakes": "दो ग़लतियाँ",
 "Spread, and how big the effect is": "फैलाव, और असर कितना बड़ा है", "The .05 line and two-tailed tests": ".05 की रेखा और two-tailed test",
 "How the p-value is misused": "p-value का ग़लत इस्तेमाल", "Writing the result": "Result लिखना", "Closing": "समापन",
}
# English delivery notes for the natural voice (the Hindi 'आवाज़' notes in the script)
VO = {1: "excited, quick", 2: "relaxed, a little teasing", 3: "hesitant, then curious; pause after the question",
      4: "warm, smiling, unhurried", 14: "proud", 15: "slow down on the question, pause after it",
      18: "pause three seconds before the last word", 19: "stress 'chance variation', a new term",
      26: "slow and clear, a definition", 28: "the slowest slide; pause before 'if'", 30: "pause three seconds after 'think'",
      34: "three seconds of silence before 'think about'", 38: "genuine praise, bright", 46: "stress 'standard deviation', a new term",
      60: "three seconds of silence before turning to Tara", 61: "slow and confident", 62: "warm, smiling"}
SLOW = {26, 28, 29, 46, 47}
EXPR = {1: "happy", 2: "smile", 3: "think", 14: "happy", 17: "think", 22: "think", 36: "smile", 37: "think", 40: "think", 51: "think", 56: "think", 61: "happy"}

slides, part, partH, board, boardH, seenpart = [], None, None, None, None, None
for blk in re.split(r'(?m)^(?=## Part |### Slide )', md):
    m = re.match(r'## Part \d+: (.+)', blk)
    if m:
        part = m.group(1).strip(); partH = PART_HI[part]; part = {'Before class': 'Opening'}.get(part, part); continue
    m = re.match(r'### Slide (\d+) · (\w+)', blk)
    if not m: continue
    n, who = int(m.group(1)), m.group(2).lower()
    who = {'professor': 'raj'}.get(who, who)
    en = re.search(r'(?m)^EN: (.+)$', blk).group(1).strip()
    hi = re.search(r'(?m)^HI: (.+)$', blk).group(1).strip()
    special = []
    for a, b2 in (("P-VALUE", "p-value"), ("COHEN'S D", "Cohen's d"), ("TWO-TAILED", "two-tailed")):
        if a in en: en = en.replace(a, b2); special.append(b2)
    caps = special + [w for w in re.findall(r"\b[A-Z][A-Z'’]{2,}(?: [A-Z][A-Z'’]+)*\b", en)]
    for w in caps:  # capitals mark the stressed words in the script; speech engines may spell them out
        if w not in special: en = en.replace(w, w.lower())
    stress = "; ".join("stress '%s'" % w.lower() for w in caps if w.lower() not in (VO.get(n) or ''))
    if n in B:
        b = B[n]; board, boardH = [b[0], b[1]], [b[2], b[3]]
    assert board, n
    s = {"t": part, "tH": partH, "who": who, "board": board, "boardH": boardH, "say": en, "sayH": hi}
    if part != seenpart:
        s["part"], s["partH"], seenpart = part, partH, part
    vo = "; ".join(x for x in (VO.get(n), stress) if x)
    if vo: s["vo"] = vo
    if n in SLOW: s["slow"] = 1
    before = n <= 3  # Professor Raj is not in the room yet
    if who in ('tara', 'dev') or before:
        cast = [who] if before else [who, 'raj']
        s.update(cast=cast, cm=1, e={c: (EXPR.get(n, 'smile') if c == who else 'smile') for c in cast})
    else:
        s.update(a=EXPR.get(n, 'smile') if who == 'appu' else 'think', r='smile' if who == 'appu' else 'point')
    if n in (34, 60): s["tone"] = "q"
    slides.append(s)
V = {
 21: {"k": "coins", "n": 10, "heads": 9, "l": ["9 heads and 1 tail in 10 tosses", "10 उछाल में 9 head और 1 tail"]},
 26: {"k": "tree", "root": ["Null hypothesis: nothing is happening", "Null hypothesis: कुछ नहीं हो रहा"], "kids": [{"l": ["Coin", "सिक्का"], "kids": [["The coin is fair", "सिक्का सही है"]]}, {"l": ["Tara's study", "Tara की study"], "kids": [["The breathing routine does nothing", "Breathing routine से कुछ नहीं बदलता"]]}]},
 32: {"k": "bell", "title": ["100 colleges, useless routine", "100 colleges, बेकार routine"], "tails": "both", "z": 2.17, "labels": {"mid": ["Small gaps: most colleges", "छोटे फ़र्क़: ज़्यादातर colleges"], "tail": ["5.6 or more: only 3–4", "5.6 या ज़्यादा: सिर्फ़ 3–4"]}},
 38: {"k": "compare", "left": {"t": ["Not what p is", "p यह नहीं है"], "items": [["Chance the null hypothesis is true", "null hypothesis के सच होने का chance"]]}, "right": {"t": ["What p is", "p यह है"], "items": [["Chance of the data, if the null hypothesis is true", "null hypothesis सच हो, तो data का chance"]]}},
 58: {"k": "formula", "lines": ["t(58) = 2.17, p = .034, d = 0.56", "df = 60 − 2 = 58", ["Write p exactly; p < .001, never p = .000", "p पूरा लिखें; p < .001, कभी p = .000 नहीं"]], "hl": 0},
}
for n, v in V.items(): slides[n - 1]["v"] = v
assert len(slides) == 62, len(slides)
json.dump(slides, open('lecture-01-slides.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print(len(slides), 'slides')
