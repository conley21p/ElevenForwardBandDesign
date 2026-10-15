"""Nine explicit posture/depth fixtures, local-normal depth and clearance observations.

Postures are geometric bends, not a calibrated human movement or cloth model.
"""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from provenance import source_hash
from model import load
from drafting import inputs
from scene import cross_section
assert bpy.context.scene['source_hash']==source_hash(ROOT),'Stale scene'
report=json.loads((ROOT/'3d-rendering/reports/ease-05-hero-0.005.json').read_text());center=inputs(ROOT)[0]['band_center_height']['value']*.0254
avatar=next(o for o in bpy.data.objects if o.name.startswith('Avatar -'))
av=[v.co.copy() for v in avatar.data.vertices];faces=[list(p.vertices) for p in avatar.data.polygons];items={o['instance_id']:o for o in bpy.data.objects if 'instance_id' in o}
geometry=json.loads((ROOT/'pattern-drafting/exports/ease-05/geometry.json').read_text());d=geometry['dimensions'];cy=cross_section(av,faces,center)['cy'];target_depth=geometry['depth_target_in']
def bend(v,pose):
 x,y,z=v;theta=math.radians(0 if pose=='standing' else 20 if pose=='seated' else 35)*max(0,min(1,(z-(center-.16))/.30));pivot=center-.16
 return Vector((x,cy+(y-cy)*math.cos(theta)-(z-pivot)*math.sin(theta),pivot+(y-cy)*math.sin(theta)+(z-pivot)*math.cos(theta)))
results=[];collection=bpy.data.collections.new('Diagnostic fixtures - geometric postures, uncalibrated');bpy.context.scene.collection.children.link(collection)
for pose in ['standing','seated','forward-bend']:
 posed=[bend(v,pose) for v in av];tree=BVHTree.FromPolygons(posed,faces)
 for depth in [0,target_depth/2,target_depth]:
  state={};base=[];full=[];local_depths=[]
  for inst,ob in items.items():
   points=[p.co.copy() for p in ob.data.shape_keys.key_blocks['Fitted visualization'].data]
   if inst=='1':
    # Remove only authored pouch displacement; keep wearing ease and seam geometry.
    uv={}
    for poly in ob.data.polygons:
     for li,vi in zip(poly.loop_indices,poly.vertices):uv[vi]=ob.data.uv_layers.active.data[li].uv.copy()
    for i,v in enumerate(points):
     xx=uv[i].x/.0254;yy=uv[i].y/.0254;left=(d['body_w']-d['zone'])/2;r=d['zone']/3;t=(xx-left)/r;a=d['extra']
     if left<xx<left+d['zone']:
      if t<1:a=d['extra']*(1-(3*t*t-2*t*t*t))
      elif xx<=left+d['zone']-r:a=0
      else:t=(left+d['zone']-xx)/r;a=d['extra']*(1-(3*t*t-2*t*t*t))
     yf=(yy-a)/(d['max_h']-2*a);zone=max(0,math.cos((xx-d['body_w']/2)/d['zone']*math.pi)) if abs(xx-d['body_w']/2)<d['zone']/2 else 0
     amount=target_depth*.0254*zone**2*max(0,math.sin(math.pi*yf))**1.4;theta=xx/d['circ']*2*math.pi-math.pi+d['back_w']/d['circ']*math.pi;rad=Vector((math.sin(theta),-math.cos(theta),0));zero=v-rad*amount;new=zero+rad*amount*depth/target_depth;v=new
     bp=bend(zero,pose);fp=bend(new,pose);_,normal,_,_=tree.find_nearest(bp);local_depths.append(max(0,(fp-bp).dot(normal))/.0254);points[i]=v
   ps=[bend(v,pose) for v in points];distances=[]
   for v in ps:
    near,no,_,_=tree.find_nearest(v);distances.append((v-near).dot(no))
   state[inst]={'penetrations_over_0_5mm':sum(v<-.0005 for v in distances),'min_signed_clearance_mm':min(distances)*1000}
   me=bpy.data.meshes.new(f'{pose}-{depth}-{inst}');me.from_pydata(ps,[],[list(p.vertices) for p in ob.data.polygons]);me.update();fixture=bpy.data.objects.new(me.name,me);collection.objects.link(fixture);fixture.hide_render=True;fixture.hide_viewport=True;fixture['pose']=pose;fixture['depth_in']=depth;fixture['physical_verified']=False
  results.append({'pose_fixture':pose,'requested_authored_radial_projection_in':depth,'max_local_normal_projection_in':max(local_depths),'clearance':state,'retention_flange_outlet_recovery':'requires physical test','status':'geometric fixture observations only; not calibrated motion/cloth validation'})
out={'revision':load(ROOT)['revision'],'source_hash':source_hash(ROOT),'physical_verified':False,'posture_method':'smooth geometric torso bend; no musculoskeletal or load model','reference_center_y_m':cy,'results':results,'depth_note':'Local-normal observation may differ from authored radial target. Physical target acceptance remains open.'}
file=ROOT/'3d-rendering/scenes/diagnostic-fixtures.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True);out['scene_file']=str(file.relative_to(ROOT));out['scene_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();(ROOT/'3d-rendering/reports/posture-depth-fixtures.json').write_text(json.dumps(out,indent=2)+'\n');print('EFBD_DIAGNOSTICS_COMPLETE')
