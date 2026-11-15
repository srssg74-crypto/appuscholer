# Section detection for research PDFs

`sections.js` finds the title, headings, section kinds (abstract, introduction, methods, results,
discussion, limitations, conclusion, references, back matter) and subsections of a paper from the
text items pdf.js already gives us. No model, no network, no new library.

Input: one `items` array per page (pdf.js `getTextContent().items`). Output: `{ title, body, headings, sections, lines, notes }`.
A scan or a page printed as images has almost no text; `notes` says so, and that is the case for OCR.

How it decides, in short: body text size and font are fixed once for the whole paper. A heading is a short line that
stands apart: larger, or in a font used for little else, or a numbered or well-known section name. Lines repeated on
three or more pages are running heads. Reference entries, table headers, captions and lower-case starts are never headings.
Letter-spaced capitals ("RE SU LT S") are put back together. Structured-abstract labels stay with the abstract.

Run: `node test_sections.js` (synthetic fixtures, no PDFs needed).
Measure on real papers: `PDF_DIR=/path/to/pdfs node summary.mjs` (needs pdfjs-dist; set `PDFJS` to its `legacy/build/pdf.mjs`).
`node run.mjs file.pdf` prints the headings of one paper.

Measured 15 Nov 2026 on 25 PDFs (research papers plus a few guides and one image-only print):
Introduction 20, Methods 23, Results 21, Discussion 22, References 24. The misses are mostly papers with no such heading
(APA style opens straight into text; Nature style has no Introduction heading), and one PDF that is all images.
About 200 other headings were read through by hand: a handful of false ones remain (table fragments, a few wrapped lines).
Not yet wired into index.html.
