# Blender scenes, fit study and product film

Blender 4.5.14 LTS and FFmpeg are the tested tools. Cycles runs on the available Apple M4 Pro GPU. No paid add-on is required. The avatar comes from MakeHuman CC0 core assets, with explicit male and athletic targets; asset licenses and provenance are retained.

The initial profile is a 74-inch adult male with a size-34 clothing label. Its 34-inch center circumference and 44-inch provisional wearing height are visualization assumptions. Other circumferences are measured computationally from the avatar and recorded in reports. A wide band crosses different circumferences; 5% ease at its center does not imply 5% ease everywhere. In particular, the lower edge extends farther over the provisional hips and requires its own fabric and seam extension checks.

## Reproduce

From the repository root, install the pinned Python requirements. Install Seamly2D, Blender 4.5 LTS, and FFmpeg separately.

```sh
python scripts/pipeline.py build --seamly /path/to/Seamly2D --blender /path/to/Blender --film
python scripts/verify.py
python -m unittest discover -s tests -v
```

The build produces synchronized manuals/patterns, real CAD exports, a hero scene, three 5 mm sewing-spring studies, a 2.5 mm study of the visualization candidate, virtual coupons, geometric posture/depth fixtures, ten 4K still views, and all 960 native 4K film frames. The film encoder produces 40-second 24fps 4K and 1080p MP4s. Frame sequences and caches remain local; compact sources and deliverables are tracked, while larger scenes and video packages are release assets.

For targeted rebuilding, use `scene.py` in Blender with `--mode hero` or `--mode simulation --run-study`; `--spacing .0025` selects the finer study. Use `--python-exit-code 1` so script errors fail the process. Run `render.py --stills` or `--film --resolution 4k` on the saved hero scene. A stale scene source hash fails before rendering. Then run `python scripts/encode_video.py`.

## What the two geometry representations mean

The editable hero scene contains six separate meshes with flat and fitted shape keys, physical-meter UVs, folded double-layer edge bands, fabric thickness, structural seam details, lights, cameras and assembly keyframes. It is **authored fitted visualization**, not the result of calibrated cloth simulation. Its shape illustrates the pouch envelope and a stretched wearing form. The invisible-wearer and torso views use the exact same garment geometry.

The separate construction scenes combine six seam-line panels with loose sewing edges and a native Cloth modifier. Matching registration intervals preserve intentional easing; free flange/insertion edges remain open. Fold lines are pinned to the provisional torso fixture; bounded sewing forces and collision controls allow the remaining mesh to relax. Simulation settings and fiber mass per vertex are recorded. Flat pattern shape keys provide the rest spring lengths; both raw edges of each folded band are connected. Structural, shear and bending groups use the four proposed material profiles. This is a provisional isotropic approximation; native cloth and the selected settings are not a validated nonlinear orthotropic compression model.

Synthetic cantilever coupons run at 5 mm and 2.5 mm spacing. They record gravity and gravity-removal behavior, extension and deflection; they have not been matched to real swatches. Compare these observations before using a different mesh. Physical fiber ratio, stretch, recovery, thickness, GSM, laundering and machine-qualified seams remain unknown.

Nine posture/depth fixtures provide geometric clearance observations for standing, seated-style torso bend and forward bend at 0, 0.75 and 1.5-inch authored radial envelopes. The postures are smooth geometric bends, not a calibrated human rig or load model. Depth is additionally measured against the local avatar normal and may differ from radial displacement. Retention, flange access, outlet access and recovery require real sample tests. This distinction is recorded in the fixture report.

## Film and visual inspection

Six parts are laid out first. Supports are positioned on the flat body, then the body wraps while matching bands fold and attach. The camera switches to the back for the insert connections, then shows the male torso and the fitted invisible-wearer hero. The operation IDs come from the manual. The reference pouch is not shown as a supplied product component. Matching black thread, matte black knit, restrained sheen and studio lighting provide the material treatment. There is no music or voice-over.

Inspect catalog, supports, assembly, torso, front, angle, back, side, interior cutaway and material-detail stills. Check skin intersections, open insert transitions, free edges, folded thickness, grayscale readability and camera framing. The diagnostic scene and numerical reports remain separate from the beauty film. Video quality checks require 960 frames, 24fps, exactly 40 seconds and native 3840x2160 source frames. The 1080p version is downsampled from those frames.

Large release files have SHA-256 checksums. Source/measurement/material changes invalidate scene, study, still and film receipts. GitHub Actions checks hashes and geometry without running GPU rendering; local rebuilding supplies expensive artifacts. No branch-protection guarantee is claimed.

Product views automatically fit all garment pieces inside an 8% image border. The material-detail view is intentionally enlarged. GPU jobs take an exclusive local lock; avoid other manual Metal render jobs while building.

Flat render pieces include the shared edge-specific cutting allowances. Their borders return under the joined panels during assembly: body/band and back joins lie toward the main body/bands, support edges turn under, and insert end hems turn inward. Simulation uses seam-line geometry with total mass derived from full cut areas.

Native cloth studies collide against both the avatar and a horizontal rigid ellipsoidal pouch sizing envelope. Its width/height come from the reference bag and its depth from the expansion target. The envelope has no modeled flange/outlet or fluid behavior; access and retention remain physical sample checks.

See the [illustrated storyboard](STORYBOARD.md) and [readable fit-study comparison](reports/fit-study.md) for shot references, measured observations and unresolved limitations.
