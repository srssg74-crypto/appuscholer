# Reported statistics from a paper's page text

`statsfind.js` pulls out what a paper prints: M and SD (also 21.4 ± 2.3), t(df) = x, F(df1, df2) = x, chi-square(df) = x, r = x,
p with its sign, 95% CI bounds, OR/HR/RR, beta, d, eta-squared, R-squared, alpha, and n or N. Each hit carries its page and the exact
text, so it can be shown beside the page and checked. A hit means "the paper prints this", not "this is right".

`find(pages)` takes one text string per page. `node test_statsfind.js` runs the fixtures.
`PDF_DIR=... node run.mjs -v` counts hits on real PDFs and prints samples (needs pdfjs-dist; set PDFJS to its legacy/build/pdf.mjs).

Run on 25 PDFs on 15 Nov 2026: 481 p-values, 375 mean and SD pairs, 266 sample sizes, 109 effect sizes, 85 CIs, 51 correlations,
48 t, 23 F, 20 ratios, 10 chi-square. A sample of 46 hits (a few of each kind) was read by hand; all were real except one ratio, which is fixed. That is a spot check, not a precision figure.
Not yet in the app. Tables that put M and SD in separate columns need the table reader, not this.

## Do the numbers agree? (consistency.js)

`consistency.js` turns each reported t, F or chi-square with its degrees of freedom back into a p-value and compares it with the p printed next to it (within 60 characters after the test).
Allowed for: rounding of the test statistic and of p, a p cut off instead of rounded (.0289 printed as .02), "p = .001" printed for anything smaller, one-tailed tests when the page says so.
A p described as adjusted (Bonferroni, Holm, corrected) is reported as "adjusted", not as a mismatch. "R 2 Adjusted" is not read as an adjusted p.
Status: ok, inconsistent, decision (the mismatch changes whether p is below .05), adjusted.

The p-value functions match scipy 1.18 on 150 cases (`dist_vectors.json`; relative 1e-9 or absolute 1e-12). `node test_consistency.js` runs them and the fixtures.
Run on the 53 sample PDFs (`node run_consistency.mjs`, 15 Nov 2026): 106 pairs checked, 95 ok, 11 flagged. All 11 were read against the page text.
Eight look like real mismatches in the papers (for example F(1, 130) = 6.14 printed with p = .001 when the test statistic gives .0145; the same F(1,38) = 33.76 printed with two different p-values; r(41) = 0.29 printed with p = .07 when it gives .059; r(79) = 0.31 printed with p = .002 when it gives .005, which would fit a one-tailed test the page does not name).
The other three are chi-square comparisons of adherence rates whose printed p may come from an exact test the paper does not name.
One-tailed tests are allowed for (t and r) when the page says one-tailed; without that word on the page a half-size p is flagged.
That is a spot check on 106 pairs from 53 files; it is not a precision or recall figure. A mismatch is a reason to look at the page, not proof of an error.
Not checked: correlations printed without df, t tests given as "t = x" without df, results in tables.

### Confidence intervals beside estimates

`checkCI` takes an OR, HR, RR or PR (null 1), or a beta or d (null 0), followed within 40 characters by its confidence interval and, within 70 more, a p-value.
The estimate must lie inside its interval (rounding allowed for). An interval that excludes the null goes with p below 1 minus the level (.05 for 95%), one that includes it with p above. An interval that ends at the null (1.00) is borderline and is not flagged.
On the 53 sample PDFs: 46 intervals checked (12 of them with a p beside), none flagged. Zero flags on 46 can mean clean papers or a check that is too lenient; the fixtures show it flags a wrong p and an estimate outside its interval.
