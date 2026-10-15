"""Lightweight pipeline checks: no Blender/GPU required in CI."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader
from model import load,derived,cut,bounds
from provenance import source_hash
from drafting import inputs,variant_spec,INSTANCES
def verify_pipeline(root,require_artifacts=True):
 s=load(root);w,vs=inputs(root);ops=set(s['operations']);parts=set(s['parts'])
 assert not w['production_approved'] and w['pants_size']['status']=='reported clothing label'
 assert w['band_center_circumference']['status']=='provisional'
 assert all(m['color']=='black' for m in s['materials'].values()),'Palette change requires synchronized shader and layout support'
 for vid,v in vs.items():
  q=variant_spec(s,w,v);d=derived(q);folder=root/f'pattern-drafting/exports/{vid}'
  m=json.loads((folder/'seams.json').read_text());assert m['revision']==s['revision'] and m['variant']==vid
  assert len(m['part_instances'])==6 and m['part_instances']==INSTANCES
  for seam in m['seams']:
   assert seam['operation'] in ops and all(p in INSTANCES for p in seam['parts'])
   assert not any(e in ['insertion','flange'] for e in seam['edges'])
  assert len(m['seams'])==6
  for k in ['1','2a','2b','3','4']:
   e=ET.parse(folder/f'part-{k}.svg').getroot();assert e.get('width').endswith('in') and e.get('height').endswith('in');assert e.get('data-design-revision')==s['revision']
  native=ET.parse(root/f'pattern-drafting/native/{vid}.sm2d');assert len(native.findall('.//piece'))==6
  for typ,wh in [('letter',(612,792)),('a4',(595.27559055,841.88976378))]:
   pdf=PdfReader(folder/f'cutting-{typ}.pdf');assert len(pdf.pages)>1
   assert all(abs(float(p.mediabox.width)-wh[0])<.01 and abs(float(p.mediabox.height)-wh[1])<.01 for p in pdf.pages)
   assert all('Calibration' in (p.extract_text() or '') for p in pdf.pages)
  assert len(PdfReader(folder/'cutting-plotter.pdf').pages)==1
 shots=json.loads((root/'3d-rendering/source/shots.json').read_text());assert shots['fps']==24 and shots['duration_seconds']==40
 assert all(op in ops for sh in shots['shots'] for op in sh['operations'])
 assert [(sh['start'],sh['end']) for sh in shots['shots']]==[(0,6),(6,14),(14,22),(22,28),(28,34),(34,40)]
 if require_artifacts:
  current=source_hash(root)
  for name in ['ease-05-hero-0.005.json','ease-00-simulation-0.005.json','ease-05-simulation-0.005.json','ease-10-simulation-0.005.json','ease-05-simulation-0.0025.json','virtual-coupons.json','render-manifest.json','posture-depth-fixtures.json','fit-study.json','delivery-docs-manifest.json']:
   r=json.loads((root/'3d-rendering/reports'/name).read_text());assert r['source_hash']==current,f'Stale 3D result: {name}';assert r['physical_verified'] is False
   if name=='delivery-docs-manifest.json':
    for file,sha in r['files'].items():assert hashlib.sha256((root/file).read_bytes()).hexdigest()==sha,f'Edited delivery documentation: {file}'
   if 'render_cut_envelopes_in' in r:
    q=variant_spec(s,w,vs[r['variant']]);assert set(r['render_cut_envelopes_in'])==set(INSTANCES)
    for inst,bb in r['render_cut_envelopes_in'].items():
     expected=bounds(cut(q,INSTANCES[inst]));assert max(abs(a-b) for a,b in zip(bb,expected))*25.4<=.5,'Render/pattern cut dimension mismatch'
     assert r['allowance_vertex_counts'][inst]>0,'Render missing cutting allowance'
   if 'native_cloth_run' in r:
    run=r['native_cloth_run'];assert run['fixture_pin_vertices']>0 and run['sewing_edges']>0
    assert run['rest_shape']=='flat seam-line patterns in meters'
    assert all(p['finite'] for p in run['snapshots']),'Non-finite cloth study'
   if name=='posture-depth-fixtures.json':
    for result in r['results']:
     target=result['requested_authored_radial_projection_in'];actual=result['max_local_normal_projection_in']
     if result['pose_fixture']=='standing' and target>0:assert target*.5<actual<target*1.2,'Depth diagnostic direction or units are inconsistent'
   if 'scene_file' in r:
    file=root/r['scene_file']
    if file.exists():assert hashlib.sha256(file.read_bytes()).hexdigest()==r['scene_sha256'],f'Directly edited scene: {file.name}'
    else:
     released=json.loads((root/'3d-rendering/release-assets.json').read_text())['files'];assert file.name in released and released[file.name]['sha256']==r['scene_sha256'],'Missing scene/release checksum'
  r=json.loads((root/'3d-rendering/reports/render-manifest.json').read_text())
  assert hashlib.sha256((root/'3d-rendering/scenes/ease-05-hero.blend').read_bytes()).hexdigest()==r['scene_hash'],'Render references an edited scene'
  for file,sha in r['files'].items():assert hashlib.sha256((root/'3d-rendering/renders'/file).read_bytes()).hexdigest()==sha,f'Edited render: {file}'
  video=json.loads((root/'3d-rendering/video/video-manifest.json').read_text());assert video['source_hash']==current,'Stale video';assert video['frames']==960 and video['fps']==24 and video['duration_seconds']==40
  for file,sha in video['outputs'].items():
   p=root/'3d-rendering/video'/file
   # Large binaries may reside in release assets; publish manifest pins their hashes.
   if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,f'Edited video: {file}'
   else:
    published=json.loads((root/'3d-rendering/release-assets.json').read_text());assert file in published['files'] and published['files'][file]['sha256']==sha and published['files'][file]['url'].startswith('https://github.com/conley21p/ElevenForwardBandDesign/releases/download/'),'Missing released video'
 print('PASS: CAD bridge, four patterns, seam references, full-scale PDFs and artifact provenance')
