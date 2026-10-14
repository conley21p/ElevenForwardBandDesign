# Mandatory change-impact review

Before every design or manual change, ask and answer:

> Does this change affect another part, material, dimension, seam, assembly step, instruction, or inspection requirement—and what else must be updated?

Summarize the answer to the user. Proceed with authorized dependent edits; ask about new design decisions. Record the request, direct parts, dependent parts/operations, generated documents, invalidated physical checks, decisions, and completion status in docs/changes. A no-impact conclusion needs a reason.

Shared facts live in design/design-spec.json. Manual prose lives in manual/source. Generated layout, pages, PDF, and specifications are not independent authorities. Reconcile a change from either surface into source, update affected prose, regenerate, and verify. Never hand-edit generated output to bypass a failed check.

Review material changes for needles, thread, feed, stretch, bulk and laundering; dimensions for connected seam lengths, notches, fit and allowances; pocket changes for flange/outlet access; quantities for catalogs and sequence; stitch changes for machine capability and seam extension; operation ordering for sewing access; bag/depth changes for retention and volume.

Invalidate affected physical results after relevant source changes. Never label unperformed tests as verified. Do not invent machine-specific threading routes. Distinguish flat pattern geometry from assembled outward depth. Preserve historical revisions, excluding them from current-output checks.

Run `python scripts/build.py` and `python scripts/verify.py` before committing. Commit source, impact record, generated outputs and documentation together. CI checks consistency; branch protection is not presumed.
