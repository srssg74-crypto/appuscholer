# Reported statistics from a paper's page text

`statsfind.js` pulls out what a paper prints: M and SD (also 21.4 ± 2.3), t(df) = x, F(df1, df2) = x, chi-square(df) = x, r = x,
p with its sign, 95% CI bounds, OR/HR/RR, beta, d, eta-squared, R-squared, alpha, and n or N. Each hit carries its page and the exact
text, so it can be shown beside the page and checked. A hit means "the paper prints this", not "this is right".

`find(pages)` takes one text string per page. `node test_statsfind.js` runs the fixtures.
`PDF_DIR=... node run.mjs -v` counts hits on real PDFs and prints samples (needs pdfjs-dist; set PDFJS to its legacy/build/pdf.mjs).

Run on 25 PDFs on 15 Nov 2026: 481 p-values, 375 mean and SD pairs, 266 sample sizes, 109 effect sizes, 85 CIs, 51 correlations,
48 t, 23 F, 20 ratios, 10 chi-square. A sample of 46 hits (a few of each kind) was read by hand; all were real except one ratio, which is fixed. That is a spot check, not a precision figure.
Not yet in the app. Tables that put M and SD in separate columns need the table reader, not this.
