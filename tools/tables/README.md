# Tables of a research paper

`tables.js` finds tables from where each piece of text sits on the page (pdf.js text items): the caption ("Table 3"), the rows, the columns.
A table that runs over two pages is joined into one, with the header printed again on the second page dropped.
Mean and SD are read from the table's own columns: "Mean | SD" pairs, an "M (SD)" column, "a ± b" cells in a table whose caption says descriptive, mean or SD.
Decimal commas ("3,7241") are values; the text of a hit keeps what is printed.

`read(pages)` takes one pdf.js `items` array per page and returns `{ tables, hits, notes }`. Each hit has its table number and the page of its row.
A hit says what the table prints, not that it is right. A table drawn as a picture has no text and is not found.

Run: `node test_tables.js` (synthetic fixtures). Real PDFs: `PDF_DIR=... node run.mjs -v` (needs pdfjs-dist; set `PDFJS` to its `legacy/build/pdf.mjs`).

Run on 53 PDFs on 15 Nov 2026: 79 tables in 34 of them, 2 joined across pages, 175 mean and SD pairs.
Checks made: every number of every hit appears on the cited page (175 of 175). That caught one real bug, decimal commas read as thousands.
Read by eye: Tables 1 and 2 of one trial paper (including the joined one), Table 3 of another, the Average and Deviation table of a third. Those pairs matched what is printed.
This is a spot check, not a precision figure; pairing of a mean with its SD was read by hand only for those tables.

Known limits:
- Two-column pages: a table in one column can pick up text from the next column, so rows and headers can be wrong. Qualitative tables with long cells come out badly. The reader says to check the table against the page.
- Tables with several header lines or spanning headers can lose a group name in the label.
- A second-page table with no caption and no repeated header is joined only if it starts within three lines of the page top, has three or more columns on a table that already had three, and follows a table that ran to the end of the previous page.
