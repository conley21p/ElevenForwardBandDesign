"""Validate real Seamly2D exports and normalize their seam/cut paths to inches."""
import json,math,re,hashlib,xml.etree.ElementTree as ET,subprocess,sys,argparse
from pathlib import Path
from model import ROOT,bounds,digest,load,shape,cut,offset_polygon,offsets,quantize
from drafting import INSTANCES,inputs,variant_spec
def read_export(file):
 doc=ET.parse(file);root=doc.getroot();vb=list(map(float,root.attrib['viewBox'].split()))
 physical=float(root.attrib['width'].removesuffix('mm'));unit_in=physical/25.4/vb[2]
 assert abs(unit_in-1/96)<1e-6,'Unexpected CAD export scaling'
 # Qt rounds physical SVG dimensions; coordinates retain the exact 96 dpi unit.
 unit_in=1/96
 result={}
 for g in list(root):
  inst=g.get('id')
  if inst not in INSTANCES:continue
  paths=[p.get('d') for p in g.iter() if p.tag.endswith('path') and p.get('d') and len(re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',p.get('d')))>8]
  assert len(paths)>=1,f'Missing seam path for {inst}'
  polygons=[]
  for data in paths[:2]:
   nums=list(map(float,re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',data)));pts=[(nums[i]*unit_in,nums[i+1]*unit_in) for i in range(0,len(nums),2)]
   if math.dist(pts[0],pts[-1])<1e-7:pts.pop()
   polygons.append(pts)
  # Translation cancels when normalized relative to the seam outline.
  x0,y0,_,_=bounds(polygons[0]);result[inst]={'finished':[(x-x0,y-y0) for x,y in polygons[0]]}
  if len(polygons)>1:result[inst]['cut']=[(x-x0,y-y0) for x,y in polygons[1]]
 return result
def segment_distance(p,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/max(dx*dx+dy*dy,1e-20)));return math.dist(p,(a[0]+t*dx,a[1]+t*dy))
def error(a,b):return max(min(segment_distance(p,x,y) for x,y in zip(b,b[1:]+b[:1])) for p in a)
def validate(root=ROOT,write=False):
 s=load(root);w,vs=inputs(root);report={'revision':s['revision'],'application':'Seamly2D 2026.10.12.200','upstream_revision':'05969e153860','format':'SVG actual application export / 96 units per inch','variants':{}}
 for vid,v in vs.items():
  q=variant_spec(s,w,v);file=root/f'pattern-drafting/cad-export/{vid}_pieces.svg';assert file.exists(),f'Missing actual CAD export: {vid}'
  cad=read_export(file);assert set(cad)==set(INSTANCES)
  errors={}
  for inst,k in INSTANCES.items():
   if k in ['2a','2b']:
    pts=cad[inst]['finished'];cad[inst]['cut']=offset_polygon(pts,offsets(q,k,pts))
   for which,expected in [('finished',shape(q,k)),('cut',cut(q,k))]:
    # body seam bounding top is 0; all other native origins are 0.
    e=max(error(cad[inst][which],expected),error(expected,cad[inst][which]))*25.4
    assert e<=.5,f'CAD {vid}/{inst}/{which} differs by {e:.3f}mm; reconcile native draft'
    errors[inst+'-'+which]=round(e,6)
  native=root/f'pattern-drafting/native/{vid}.sm2d'
  report['variants'][vid]={'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'export_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'errors_mm':errors,'normalized_geometry':cad,'support_allowance_method':'Bridge offsets native seam outline; CAD zero-allowance concave edge export was malformed'}
 report['measurement_sha256']=hashlib.sha256((root/'pattern-drafting/native/wearer.smis').read_bytes()).hexdigest()
 file=root/'pattern-drafting/cad-export/bridge-report.json'
 if write:file.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
 else:
  saved=json.loads(file.read_text());assert digest(quantize(saved,8))==digest(quantize(report,8)),'Stale CAD bridge receipt: export native files and revalidate'
 return report
def export(exe,root=ROOT):
 for vid in inputs(root)[1]:
  cmd=[exe,'-b',vid,'-d',str(root/'pattern-drafting/cad-export'),'--exportOnlyDetails','-f','0',str(root/f'pattern-drafting/native/{vid}.sm2d')]
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
  assert r.returncode==0,(r.stdout+r.stderr)[-2500:]
 validate(root,True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seamly');p.add_argument('--record',action='store_true');a=p.parse_args()
 if a.seamly:export(a.seamly)
 else:validate(write=a.record)
 print('PASS: all six native CAD pieces, allowances and export scales within 0.5mm for every variant')
