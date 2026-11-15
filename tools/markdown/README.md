# Markdown import for the Reading shelf

`mdpages.js` turns Markdown from an OCR or conversion tool into pages and sections. `node test_mdpages.js` runs the fixtures.

Page markers it reads: `<!-- page 3 -->`, `--- Page 3 ---`, `[Page 3]`, `# Page 3`, `{2}------` (zero-based, as some converters print) and form feed.
Markers out of order are not trusted. A file with no markers is cut into parts of about 3,000 characters, and the reader says so: a part number is not a printed page.

Not tested on real OCR output. Which converters print page markers at all is still unknown; one real test with a scanned paper is pending.
