"""Small reproducible native-cloth coupons. Provisional settings, not lab results."""
import bpy,json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from provenance import source_hash
profiles=json.loads((ROOT/'3d-rendering/source/materials.json').read_text())['profiles'];results={}
for name,p in profiles.items():
 for spacing in [.005,.0025]:
  bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
  nx=round(.1/spacing);ny=round(.05/spacing);verts=[(i*.1/nx,j*.05/ny,.5) for i in range(nx+1) for j in range(ny+1)];faces=[(i*(ny+1)+j,(i+1)*(ny+1)+j,(i+1)*(ny+1)+j+1,i*(ny+1)+j+1) for i in range(nx) for j in range(ny)]
  me=bpy.data.meshes.new('coupon');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);pins=ob.vertex_groups.new(name='Clamped edge');pins.add(list(range(ny+1)),1,'REPLACE');cl=ob.modifiers.new('Native cloth','CLOTH');cs=cl.settings;cs.vertex_group_mass=pins.name;cs.mass=p['gsm']/1000*.1*.05/len(verts);cs.quality=8;cs.tension_stiffness=p['tension'];cs.compression_stiffness=p['compression'];cs.shear_stiffness=p['shear'];cs.bending_stiffness=p['bending'];cl.point_cache.frame_end=48
  scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=48;observations=[]
  for frame in range(1,49):
   scene.gravity=(0,0,-9.81 if frame<=24 else 0);scene.frame_set(frame);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());ps=[tuple(v.co) for v in ev.data.vertices]
   if frame in [1,12,24,48]:
    arc=sum(sum(math.dist(ps[i*(ny+1)+j],ps[(i+1)*(ny+1)+j]) for i in range(nx)) for j in range(ny+1))/(ny+1)
    observations.append({'frame':frame,'finite':all(math.isfinite(c) for v in ps for c in v),'free_edge_drop_m':.5-sum(ps[nx*(ny+1)+j][2] for j in range(ny+1))/(ny+1),'end_to_end_m':sum(math.dist(ps[j],ps[nx*(ny+1)+j]) for j in range(ny+1))/(ny+1),'mean_arc_length_m':arc,'mean_arc_strain':arc/.1-1})
  results[f'{name}-{spacing}']={'spacing_m':spacing,'mass_per_vertex_kg':cs.mass,'area_m2':.005,'observations':observations,'boundary':'one-edge-clamped horizontal cantilever; gravity removed after frame 24'}
folder=ROOT/'3d-rendering/reports';folder.mkdir(exist_ok=True);(folder/'virtual-coupons.json').write_text(json.dumps({'source_hash':source_hash(ROOT),'blender_version':bpy.app.version_string,'physical_verified':False,'status':'synthetic uncalibrated gravity coupon observations; no material modulus or load-test certification','measurement_note':'Arc strain separates length change from bending; end-to-end distance is a chord. Gravity removal provides geometric recovery observations only.','results':results},indent=2)+'\n');print('EFBD_COUPONS_COMPLETE',flush=True)
