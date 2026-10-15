# Parametric drafting and full-scale patterns

The approved baseline is 34 inches of body plus a 2-inch insert: 36 inches nominal circumference. It is preserved alongside three exploratory patterns based on a provisional 34-inch body reference. Size-34 pants are a clothing label. None of these patterns is production-fit approved.

| Variant | Nominal relaxed circumference | #1 and each #3 width | Role |
|---|---:|---:|---|
| baseline | 36 in | 34 in | approved geometry; physical fit unverified |
| ease-00 | 34 in | 32 in | exploratory |
| ease-05 | 32.3 in | 30.3 in | initial visualization candidate only |
| ease-10 | 30.6 in | 28.6 in | exploratory |

Widths above are finished seam dimensions, not cutting widths. Do not mix variants. Each folder includes its own seam manifest and assembly supplement. Both identical folded bands stay open and join the full-height insert. The six textile pieces are body, lower support, upper support, top band, bottom band, and insert.

## Edit and export

1. Fill the [measurement worksheet](measurement-worksheet.pdf). Record standing/seated values, intended wearing height, actual pouch/flange/outlet, and fabric lot/test data. Replace provisional entries only with dated measurements.
2. Edit approved facts in the shared design specification; edit wearer and trial settings in `source/`. Answer the repository impact question before every change.
3. Run `python scripts/build.py` from the repository root. Open a generated `.sm2d` file in Seamly2D; its adjacent `wearer.smis` loads automatically. Drafting points use formulas and named increments. CAD edits must be reconciled into JSON and regenerated before approval.
4. Export and validate through the actual application: `python scripts/cad_bridge.py --seamly /path/to/Seamly2D`. Tested version: 2026.10.12.200, revision 05969e153860.
5. Use the generated cutting SVGs/PDFs for the allowance-aware cutting outline. **Native pocket automatic allowances are disabled** because the tested application produced malformed geometry at the zero-allowance concave free edge. The bridge offsets their exported seam outlines with the shared edge rules and verifies the results.

Every piece SVG has physical inch dimensions. Black is cut, blue dashed is seam, orange is fold, red is the free/no-sew boundary. Blue registration ticks match the pouch-zone endpoints and center on the body and bands. Mark these in the allowance; do not slash the seam. Greatest usable stretch runs along width. Pocket free edges have zero added allowance; the attached perimeter has a quarter-inch turned allowance.

## Print

Print PDFs at **100% / actual size**, with page scaling disabled. Measure each 1-inch calibration bar in both directions before cutting. Letter and A4 sets have a quarter-inch overlap; trim to the corner marks and align the row/column grid. A single full-size plotter PDF and individual full-size SVGs are also included. The separate master material diagram remains 30 SVG units per inch and is not the production print pattern.

DXF interchange files use plain ASCII AutoCAD R12 polylines, with coordinates in inches and named CUT/SEAM layers. They are not represented as AAMA-certified files. Seamly2D supports additional AAMA formats; use them only after recipient-specific checks. The CAD bridge uses physical SVG scale plus an independent seam manifest rather than relying on proprietary metadata survival.

The sample mesh imports the validated application-exported seam paths. Cutting allowances are represented by the print patterns; simulation uses seam lines. All physical checks remain open, including 1.5-inch outward capacity, flange access, retention, slip-on extension, comfort and laundering.
