# R3 reproducibility record

The source revision is EFBD-2026-10-14-R3. This record describes the initial digital prototype, not a production-fit approval.

## Tested tools

- Seamly2D 2026.10.12.200, source revision 05969e153860; native files loaded and exported through the actual application.
- Blender 4.5.14 LTS, Apple M4 Pro Metal rendering.
- Python 3.12.14 with reportlab 4.4.9, pypdf 6.10.0 and Pillow 12.3.0.
- FFmpeg 8.1.2 for image-sequence encoding and ffprobe for stream validation.
- Independent DXF audit: ezdxf 1.4.3 in a temporary validation environment. All four R12/AC1009 files contain twelve closed polylines and report no errors or repairs. Choose inches explicitly when importing R12 coordinates. See DXF_VALIDATION.json.

## Inputs and outputs

Approved geometry is in the shared design specification. The wearer profile, ease variants, material proposals and shot configuration are separate source files. Generated readme tables carry the same values. Native CAD exports and their geometry comparison receipt are retained in pattern-drafting/cad-export.

The initial wearer uses a reported height and clothing label, with provisional body circumference and wearing location. The avatar is a synthetic MakeHuman-derived profile, not a body scan. Its derived sections, garment cut envelopes, mass assumptions and mesh spacing are recorded in the Blender reports. Actual fabric tests and wearer measurements remain outstanding.

The hero is authored fitted geometry with full cutting allowances and returned seam borders. The separate native cloth studies use flat-pattern rest lengths, per-material stiffness groups, seam-line meshes, and avatar/reference-pouch collisions. Neither is a calibrated compression or medical-pressure model.

## Commands

```sh
python scripts/pipeline.py build --seamly /path/to/Seamly2D --blender /path/to/Blender --film
python scripts/verify.py
python -m unittest discover -s tests -v
```

For an interrupted film, resume render.py against the same saved hero scene and settings. Do not rebuild the scene and mix its new checksum into an existing frame cache. Both pipeline and renderer locks prevent duplicate jobs; stale cache receipts fail.

## Validation evidence

The final report and artifact manifests record exact source/scene/output hashes. The video manifest records its frame count, duration, frame rate, native resolution and render-job settings. Larger binaries are published as versioned repository release assets with checksums. The source, compact scenes, print exports and reports are tracked in the public repository. Physical expansion, retention, access, slip-on extension, laundering and comfort remain sample-test requirements.

The installed FFmpeg build has no drawtext filter. Catalog part labels are native Blender objects; the six stage captions are delivered as a synchronized SRT sidecar rather than burned overlays. The film has no audio.

Native XML includes a final newline matching Seamly2D normalization. The actual-application round-trip audit is recorded in NATIVE_XML_VALIDATION.json; the source pattern and measurement files remain byte-for-byte unchanged after export.
