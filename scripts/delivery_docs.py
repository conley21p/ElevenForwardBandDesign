"""Readable storyboard and uncalibrated fit-study comparison."""
import json, hashlib
from model import ROOT, load
from provenance import source_hash

def build_delivery_docs():
 root=ROOT; reports=root/'3d-rendering/reports'; s=load(root)
 read=lambda name:json.loads((reports/name).read_text())
 shots=json.loads((root/'3d-rendering/source/shots.json').read_text())
 pictures=['renders/catalog.png','renders/supports.png','../manual/pages/19-step-12---baste-the-top-band-flat.svg','renders/assembly.png','renders/torso-fit.png','renders/hero-front.png']
 lines=['# Illustrated assembly-film storyboard','','40 seconds, 24 fps. Black materials; no audio. Reference views below explain the construction stages. The band diagram is a manual reference, not a film frame. This is a provisional design visualization; physical fit remains unverified.','']
 for sh,picture in zip(shots['shots'],pictures):
  lines += [f"## {sh['start']}–{sh['end']} seconds: {sh['name']}",'',f"Manual operation IDs: {', '.join(sh['operations']) or 'completed-product inspection' }.",'',f"![{sh['name']}]({picture})",'']
 (root/'3d-rendering/STORYBOARD.md').write_text('\n'.join(lines))
 studies={v:read(f'{v}-simulation-0.005.json') for v in ['ease-00','ease-05','ease-10']}
 coarse=studies['ease-05']['native_cloth_run']['snapshots'][-1]; fine=read('ease-05-simulation-0.0025.json')['native_cloth_run']['snapshots'][-1]
 comparison={'maximum_bounds_coordinate_change_mm':max(abs(a-b) for x,y in zip(coarse['bounds_m'],fine['bounds_m']) for a,b in zip(x,y))*1000,'maximum_edge_strain_difference':fine['maximum_edge_strain']-coarse['maximum_edge_strain'],'interpretation':'Different mesh extrema are not a convergence proof. Large local strains and absent physical calibration prevent production-fit qualification.'}
 result={'revision':s['revision'],'source_hash':source_hash(root),'physical_verified':False,'avatar_sections':studies['ease-05']['avatar_sections'],'coarse_studies':{v:r['native_cloth_run']['snapshots'][-1] for v,r in studies.items()},'mesh_comparison':comparison,'depth_observations':[{k:r[k] for k in ['pose_fixture','requested_authored_radial_projection_in','max_local_normal_projection_in']} for r in read('posture-depth-fixtures.json')['results']],'limitations':['Beauty geometry is authored fitted visualization, not calibrated simulation output.','Native cloth has large local strains; material settings are uncalibrated isotropic approximations.','Postures use geometric bends, not a musculoskeletal rig.','Pouch collision uses a rigid ellipsoid without flange, outlet or fluid.','Slip-on extension, comfort, retention, flange/outlet clearance, recovery and laundering require physical samples.']}
 (reports/'fit-study.json').write_text(json.dumps(result,indent=2)+'\n')
 lines=['# Provisional fit study','','**Physical fit unverified.** These are digital observations, not a production pattern approval or compression prescription.','','## Native cloth, final frame 48','','| Variant | Maximum local edge strain | Minimum local edge strain |','|---|---:|---:|']
 for v,r in result['coarse_studies'].items():lines.append(f"| {v} | {r['maximum_edge_strain']:.1%} | {r['minimum_edge_strain']:.1%} |")
 lines += ['',f"The 5 mm versus 2.5 mm candidate changes the largest bounding-coordinate value by {comparison['maximum_bounds_coordinate_change_mm']:.2f} mm; maximum edge strain differs by {comparison['maximum_edge_strain_difference']:.3f}. {comparison['interpretation']}",'','## Authored depth fixtures','','| Pose | Requested radial depth (in) | Observed local-normal depth (in) |','|---|---:|---:|']
 for r in result['depth_observations']:lines.append(f"| {r['pose_fixture']} | {r['requested_authored_radial_projection_in']:.2f} | {r['max_local_normal_projection_in']:.3f} |")
 lines += ['','Depth is measured relative to the zero-expansion fitted surface along the local torso normal. This does not replace the physical 1.5-inch acceptance check.','','## Limitations','']+['- '+v for v in result['limitations']]
 (reports/'fit-study.md').write_text('\n'.join(lines)+'\n')
 files=['3d-rendering/STORYBOARD.md','3d-rendering/reports/fit-study.json','3d-rendering/reports/fit-study.md']
 manifest={'revision':s['revision'],'source_hash':source_hash(root),'physical_verified':False,'files':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files}}
 (reports/'delivery-docs-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':build_delivery_docs()
