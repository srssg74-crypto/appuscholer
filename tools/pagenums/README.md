# Printed page numbers

`pagenums.js` finds the page numbers printed on the pages of a PDF (footer or running head) and gives every PDF page its printed label,
so a quote can be cited by the page a reader looks up, not by the PDF page.

Input: one text string per page. Output: `{ confident, offset, same, votes, labels, how, notes }`.
Each page's first and last three lines vote for `printed = PDF page + offset`. The offset with most pages behind it wins and every page
is labelled from it. A misread number ("200S", "lOlO") is put right; a page with no number is filled in from its neighbours, but only
one page before the first and after the last page where a number was seen (an unnumbered cover stays unlabelled).
Not used when too few pages agree, or two numberings are about equally common (for example a gazette that prints "3 (2)" in the head and "2" in the foot).
Roman numerals are not read.

Run: `node test_pagenums.js`.

Checked 16 Nov 2026 on text from three real scans (spot check, not a precision figure):
a 16-page phone scan of a dermatology textbook chapter with Adobe's OCR layer (printed pages 1998 to 2013; four misreads corrected,
all 16 right); an 8-page English phone scan read with Tesseract (printed 148 to 154, the number on page 2 misread as "M48" was filled
in from the sequence, the cover left unlabelled). A Hindi image-only gazette scan could not be tested: no Hindi OCR data here.
