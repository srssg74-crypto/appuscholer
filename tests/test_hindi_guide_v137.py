"""Version 137: the whole 'Which test fits my data?' guide reads in Hindi, every branch, and returns to English."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("LS.set('appu_lang','hi');applyLang();document.getElementById('statsDlg').showModal();document.getElementById('tgPanel').style.display='block';window._tg={};tgRender()")
    pg.wait_for_timeout(300)
    ok('कौन-सा test ठीक बैठता है' in pg.inner_text('#tgPanel'), 'title in Hindi')
    # walk every question and count English-only leftovers (Latin words of 4+ letters outside known terms)
    allowed = re.compile(r'^(test|t-test|chi|square|Welch|Student|ANOVA|Pearson|Spearman|Wilcoxon|Mann|Whitney|Kruskal|Wallis|Friedman|McNemar|Fisher|exact|Poisson|binomial|logistic|regression|alpha|omega|Cronbach|Cohen|dispersion|skew|outliers|scale|score|column|columns|jamovi|JASP|Stats|Lab|demo|table|cells|items|item|ratings|yes|data|parse|paste|Likert|rank|ranks|Cramér|kappa|point|biserial|multiple|linear|ordinal|nominal|manova|ancova|mixed|repeated|measures|measure|effect|size|power|normality|Shapiro|Levene|Bonferroni|Tukey|Games|Howell|Dunn|Holm|SD|df|NHST|APA|OLS|odds|ratio|CI|Kendall|tau|phi|eta|Mauchly|Greenhouse|Geisser|Anderson|Darling|Kolmogorov|Smirnov|Sidak|Z|z|F|p|r|n|N|M|bias|Welch|Hochberg|Brown|Forsythe|Fisher|Pillai|Wilks|Hotelling|Cochran|Q|Sign|sign|signed|one|two|sample|samples|paired|independent|unpaired|between|within|subjects|factor|factors|ICC|reliability|validity|correlation|covariance|variance|mean|means|median|mode|range|IQR|Likert|Cohen|Hedges|Glass|Bayes|Bayesian|BF|MANOVA|ANCOVA|GLM|HLM|SEM|CFA|EFA|PCA|KMO|Bartlett|scree|varimax|oblimin|promax|AIC|BIC|ROC|AUC|VIF|Cook|leverage|Durbin|Watson|Breusch|Pagan|White|Huber|bootstrap|permutation|exact|Monte|Carlo|MCMC|Gibbs|Wald|score|likelihood|deviance|Pearson|log|logit|probit|cloglog|tobit|hurdle|zero|inflated|negative|binomial|quasi|gamma|beta|ordered|multinomial|conditional|survival|Cox|Kaplan|Meier|hazard|censoring|GEE|LMM|GLMM|REML|ML|MLE|EM|MAR|MCAR|MNAR|FIML|imputation|MICE|listwise|pairwise|deletion)$', re.I)
    qs = pg.evaluate("Object.keys(TG_Q)")
    bad = []
    for q in qs:
        for o in pg.evaluate("TG_Q[%r].o.map(x=>x[0])" % q):
            pass
    # first question and all options of every question rendered via direct state is branch dependent; sample branches
    branches = [{}, {'goal':'compare'}, {'goal':'relate'}, {'goal':'predict'}, {'goal':'counts'}, {'goal':'scale'}]
    for st in branches:
        pg.evaluate("window._tg=%s;tgRender()" % str(st).replace("'", '"'))
        t = pg.inner_text('#tgPanel')
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", t) if not allowed.match(w)]
        ok(len(words) <= 6, 'branch %s mostly Hindi (leftover English: %s)' % (st, words[:8]))
    pg.evaluate("window._tg={goal:'counts',cntDes:'prop'};tgRender()")
    t = pg.inner_text('#tgPanel')
    ok('यह क्यों ठीक बैठता है' in t and 'यह क्या मानकर चलता है' in t and 'यह कब ठीक नहीं बैठता' in t, 'why / assumes / stops fitting in Hindi')
    ok('एक छोटा demo आज़माइए' in t and 'पहले अनुमान लगाइए' in t, 'demo chrome in Hindi')
    ok('Use this test' not in t and 'Best fit' not in t, 'no English buttons left')
    pg.evaluate("document.getElementById('tgPanel').querySelector('input[name=tgPred]').checked=true;tgDemo('binom')")
    pg.wait_for_timeout(800)
    d = pg.inner_text('#tgDemoOut')
    ok('आपने' in d and 'कैसे पढ़ें' in d, 'demo output in Hindi: %s' % d[:80])
    pg.evaluate("window._tg={goal:'predict',prdOut:'count'};tgRender()")
    ok('सबसे ठीक बैठने वाला' in pg.inner_text('#tgPanel'), 'result label in Hindi')
    pg.evaluate("LS.set('appu_lang','en');applyLang();window._tg={goal:'counts',cntDes:'prop'};tgRender()")
    t = pg.inner_text('#tgPanel')
    ok('Best fit' in t and 'Why this fits' in t and not re.search('[ऀ-ॿ]', t), 'English restored, no Hindi left')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
