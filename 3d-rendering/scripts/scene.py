"""Blender 4.5 LTS: measurable construction mesh and authored product visualization.

The hero is an explicit provisional fitted shape, never passed off as calibrated
cloth output. Construction scene uses native sewing springs and is separately tested.
"""
import bpy, sys, json, math, hashlib, argparse
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from model import load, derived, shape, bounds, cut
from drafting import variant_spec, inputs, INSTANCES
from provenance import source_hash
IN=.0254

def mesh(name,verts,faces,material=None,edges=()):
 data=bpy.data.meshes.new(name);data.from_pydata(verts,edges,faces);data.update();ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
 if material:ob.data.materials.append(material)
 for p in data.polygons:p.use_smooth=True
 return ob
def aim(ob,p):ob.rotation_euler=(Vector(p)-ob.location).to_track_quat('-Z','Y').to_euler()
def material(name,color,rough=.55,skin=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 p.inputs['Sheen Weight'].default_value=.035 if not skin else .02
 if not skin:
  p.inputs['Sheen Tint'].default_value=(.05,.06,.07,1)
  p.inputs['Specular IOR Level'].default_value=.22
 if skin:p.inputs['Subsurface Weight'].default_value=.08
 tex=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1800 if skin else 2700;noise.inputs['Detail'].default_value=2;l.new(tex.outputs['Generated'] if skin else tex.outputs['UV'],noise.inputs['Vector'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12 if skin else .24;bump.inputs['Distance'].default_value=.00018 if skin else .00032;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 if not skin:
  wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='X';wave.inputs['Scale'].default_value=1200;wave.inputs['Distortion'].default_value=3;l.new(tex.outputs['UV'],wave.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.45;l.new(noise.outputs['Fac'],mix.inputs[1]);l.new(wave.outputs['Color'],mix.inputs[2]);l.new(mix.outputs['Color'],bump.inputs['Height'])
 return m
def curve(name,pts,mat,r=.00035):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,v in zip(sp.points,pts):p.co=(*v,1)
 ob=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(ob);c.materials.append(mat);return ob
def obj_asset(height_in):
 verts=[];faces=[];group='';base=ROOT/'3d-rendering/assets/makehuman'
 for line in (base/'base.obj').read_text().splitlines():
  a=line.split()
  if not a:continue
  if a[0]=='v':verts.append([float(v) for v in a[1:4]])
  elif a[0]=='g':group=a[1]
  elif a[0]=='f' and group=='body':faces.append([int(v.split('/')[0])-1 for v in a[1:]])
 for filename,factor in [('male.target',1),('athletic.target',.65)]:
  for line in (base/filename).read_text().splitlines():
   if not line or line.startswith('#'):continue
   a=line.split()
   if len(a)==4:
    i=int(a[0]);delta=list(map(float,a[1:]));verts[i]=[v+factor*d for v,d in zip(verts[i],delta)]
 used=set(i for f in faces for i in f);lo=min(verts[i][1] for i in used);hi=max(verts[i][1] for i in used);scale=height_in*IN/(hi-lo)
 verts=[(x*scale,-z*scale,(y-lo)*scale) for x,y,z in verts]
 return verts,faces
def cross_section(verts,faces,z):
 points=[];adj={}
 for f in faces:
  # Avoid arm sections outside central torso.
  if any(abs(verts[i][0])>.29 for i in f):continue
  hits=[]
  for i,j in zip(f,f[1:]+f[:1]):
   a,b=verts[i],verts[j]
   if (a[2]<=z<b[2]) or (b[2]<=z<a[2]):
    t=(z-a[2])/(b[2]-a[2]);hits.append((round(a[0]+t*(b[0]-a[0]),6),round(a[1]+t*(b[1]-a[1]),6)))
  if len(hits)==2:
   a,b=hits;adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
 # Separate torso loop from arm/hand cross sections before measuring circumference.
 components=[];remaining=set(adj)
 while remaining:
  stack=[remaining.pop()];component=[]
  while stack:
   p=stack.pop();component.append(p)
   for n in adj[p]:
    if n in remaining:remaining.remove(n);stack.append(n)
  components.append(component)
 central=[c for c in components if min(p[0] for p in c)<0<max(p[0] for p in c)]
 points=max(central or components,key=len)
 if not points:raise ValueError('No torso cross-section')
 cx=sum(p[0] for p in points)/len(points);cy=sum(p[1] for p in points)/len(points)
 points=sorted(set((round(x,7),round(y,7)) for x,y in points),key=lambda p:math.atan2(p[0]-cx,-(p[1]-cy)))
 perimeter=sum(math.dist(p,q) for p,q in zip(points,points[1:]+points[:1]))
 return {'z':z,'perimeter_m':perimeter,'cx':cx,'cy':cy,'rx':(max(p[0] for p in points)-min(p[0] for p in points))/2,'ry':(max(p[1] for p in points)-min(p[1] for p in points))/2,'points':points}

def grid(s,k,spacing=.005,cad_outline=None):
 """Structured interior quad grid, with analytic free-edge and contour bounds."""
 d=derived(s);p=s['parts']['2a'];w=d['body_w'] if k in ['1','3'] else d['back_w'] if k=='4' else p['width']
 h=d['max_h'] if k=='1' else d['band_h']*2 if k=='3' else d['back_h'] if k=='4' else p['height']
 nx=max(8,math.ceil(w*IN/spacing));ny=max(8,math.ceil(h*IN/spacing));verts=[];uv=[]
 if k=='3' and ny%2:ny+=1 # Fold line must be an actual row for pinning and thickness.
 def limits(x):
  if cad_outline:
   hits=[]
   xx=max(1e-7,min(w-1e-7,x))
   for a,b in zip(cad_outline,cad_outline[1:]+cad_outline[:1]):
    if min(a[0],b[0])<=xx<=max(a[0],b[0]) and abs(a[0]-b[0])>1e-9:
     t=(xx-a[0])/(b[0]-a[0]);hits.append(a[1]+t*(b[1]-a[1]))
   if hits:return min(hits),max(hits)
  if k=='1':
   z=d['zone'];left=(w-z)/2;r=z/3;t=(x-left)/r
   yy=d['extra']
   if left<x<left+z:
    if t<1:yy=d['extra']*(1-(3*t*t-2*t*t*t))
    elif x<=left+z-r:yy=0
    else:t=(left+z-x)/r;yy=d['extra']*(1-(3*t*t-2*t*t*t))
   return yy,h-yy
  if k in ['2a','2b']:
   t=(x-(p['notch_center']-p['notch_width']/2))/p['notch_width'];free=p['notch_depth']*math.sin(math.pi*t) if 0<t<1 else 0
   r=.6;bottom=h
   if x<r:bottom=h-r+math.sqrt(max(0,r*r-(x-r)**2))
   if x>w-r:bottom=h-r+math.sqrt(max(0,r*r-(x-w+r)**2))
   return (free,bottom) if k=='2a' else (h-bottom,h-free)
  return 0,h
 for i in range(nx+1):
  x=w*i/nx;a,b=limits(x)
  for j in range(ny+1):y=a+(b-a)*j/ny;verts.append((x,y,0));uv.append((x*IN,y*IN))
 faces=[(i*(ny+1)+j,(i+1)*(ny+1)+j,(i+1)*(ny+1)+j+1,i*(ny+1)+j+1) for i in range(nx) for j in range(ny)]
 edges={'left':[j for j in range(ny+1)],'right':[nx*(ny+1)+j for j in range(ny+1)],'top':[i*(ny+1) for i in range(nx+1)],'bottom':[i*(ny+1)+ny for i in range(nx+1)]}
 return verts,faces,uv,edges

def setup(args):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 s=load(ROOT);w,vs=inputs(ROOT);q=variant_spec(s,w,vs[args.variant]);d=derived(q);profiles=json.loads((ROOT/'3d-rendering/source/materials.json').read_text())['profiles']
 from cad_bridge import validate as validate_cad
 bridge=validate_cad(ROOT)['variants'][args.variant]['normalized_geometry']
 mats={k:material(k,(.003,.004,.005),v['roughness']) for k,v in profiles.items()};thread=material('Black structural thread',(.01,.012,.014),.43);skin=material('Natural skin',(.43,.235,.145),.47,True)
 avverts,avfaces=obj_asset(w['height']['value']);center=w['band_center_height']['value']*IN;section=cross_section(avverts,avfaces,center);factor=w['band_center_circumference']['value']*IN/section['perimeter_m'];cy=section['cy']
 # Radial torso scaling smooths away above/below waist; all values remain provisional.
 avverts=[(x*(1+(factor-1)*math.exp(-((z-center)/.24)**2)),cy+(y-cy)*(1+(factor-1)*math.exp(-((z-center)/.24)**2)),z) for x,y,z in avverts]
 avatar=mesh('Avatar - CC0 MakeHuman - provisional male',avverts,avfaces,skin);sub=avatar.modifiers.new('Skin smooth','SUBSURF');sub.levels=1;sub.render_levels=2
 avatar.modifiers.new('Collision surface','COLLISION');avatar.collision.thickness_outer=.002
 section_count=math.ceil(d['back_h']/.25);sections=[cross_section(avverts,avfaces,center+(-d['back_h']/2+d['back_h']*i/section_count)*IN) for i in range(section_count+1)]
 def torso(x,z):
  theta=x/(d['body_w']+d['back_w'])*2*math.pi-math.pi+d['back_w']/(d['circ'])*math.pi
  lo=min(sections,key=lambda sec:abs(sec['z']-z));ordered=sorted(sections,key=lambda sec:sec['z']);a,b=ordered[0],ordered[-1]
  for aa,bb in zip(ordered,ordered[1:]):
   if aa['z']<=z<=bb['z']:a,b=aa,bb;break
  t=max(0,min(1,(z-a['z'])/(b['z']-a['z'])))
  # Use polar cross-section points rather than an assumed perfect cylinder.
  def radial(sec):
   pts=sec['points'];rays=sorted((math.atan2(px-sec['cx'],-(py-sec['cy'])),math.hypot(px-sec['cx'],py-sec['cy'])) for px,py in pts)
   rays=[(rays[-1][0]-2*math.pi,rays[-1][1])]+rays+[(rays[0][0]+2*math.pi,rays[0][1])]
   th=(theta+math.pi)%(2*math.pi)-math.pi
   for (ta,ra),(tb,rb) in zip(rays,rays[1:]):
    if ta<=th<=tb:return ra+(rb-ra)*(th-ta)/max(tb-ta,1e-9)
   return sec['rx']
  rr=radial(a)*(1-t)+radial(b)*t;yc=a['cy']*(1-t)+b['cy']*t
  return theta,rr,yc
 def fitted(k,xy,inst):
  x,y,_=xy
  if k=='1':
   left=(d['body_w']-d['zone'])/2;r=d['zone']/3;yy=d['extra'];tt=(x-left)/r
   if left<x<left+d['zone']:
    if tt<1:yy=d['extra']*(1-(3*tt*tt-2*tt*tt*tt))
    elif x<left+d['zone']-r:yy=0
    else:tt=(left+d['zone']-x)/r;yy=d['extra']*(1-(3*tt*tt-2*tt*tt*tt))
   yf=(y-yy)/(d['max_h']-2*yy);z=center+(d['base']/2-d['base']*yf)*IN
   # Authored puff: required outward envelope plus small natural knit folds.
   zone=max(0,math.cos((x-d['body_w']/2)/d['zone']*math.pi)) if abs(x-d['body_w']/2)<d['zone']/2 else 0
   puff=d['depth']*IN*zone**2*max(0,math.sin(math.pi*yf))**1.4
   wrinkle=.0012*zone*math.sin(x*22+yf*32)*math.sin(math.pi*yf)
   offset=.004+puff+wrinkle
  elif k=='3':
   top=inst=='3-top';fold=d['band_h'];yy=fold-abs(y-fold);z=center+(d['base']/2+yy if top else -d['base']/2-yy)*IN;offset=.004+(0.00065 if y<fold else 0)
  elif k=='4':x=d['body_w']+x;z=center+(d['back_h']/2-y)*IN;offset=.004
  else:
   x+=(d['body_w']-q['parts']['2a']['width'])/2;z=center+(q['parts']['2a']['height']-y if k=='2b' else -y)*IN;offset=.002
  theta,rr,yc=torso(x,z);rr+=offset
  return (math.sin(theta)*rr,yc-math.cos(theta)*rr,z)
 objects={};raw={};layout={'1':(-.55,.2),'2a':(-.46,-.11),'2b':(-.13,-.11),'3-top':(-.55,.51),'3-bottom':(-.55,-.38),'4':(.44,-.1)}
 labels=[];labelmat=material('Catalog label',(.008,.01,.012),.8)
 for inst,k in INSTANCES.items():
  verts,faces,uv,edge=grid(q,k,args.spacing,bridge[inst]['finished']);fit=[fitted(k,p,inst) for p in verts];raw[inst]=(verts,faces,uv,edge,fit)
  from allowances import expand
  boundary=edge['top']+edge['right'][1:]+list(reversed(edge['bottom']))[1:]+list(reversed(edge['left']))[1:-1]
  expanded=expand(q,k,verts,faces,uv,boundary);verts=expanded['verts'];faces=expanded['faces'];uv=expanded['uv'];fit=list(fit)
  for xy in expanded['turned'][expanded['base_count']:]:
   pos=Vector(fitted(k,xy,inst));radial=Vector((pos.x,pos.y-cy,0)).normalized();pos+=radial*(.0009 if k in ['2a','2b'] else -.0015 if k=='3' else -.0008);fit.append(tuple(pos))
  ox,oy=layout[inst];flat=[(ox+x*IN,oy+(-y if k in ['2a','2b'] else y)*IN,.62) for x,y,_ in verts]
  ob=mesh('#'+inst+' '+q['parts'][k]['name'],flat,faces,mats[q['parts'][k]['material']]);ob['part_id']=k;ob['instance_id']=inst;ob['source_revision']=s['revision'];ob['variant']=args.variant;ob['physical_verified']=False
  uvlay=ob.data.uv_layers.new(name='Physical meters')
  for poly in ob.data.polygons:
   for li,vi in zip(poly.loop_indices,poly.vertices):uvlay.data[li].uv=uv[vi]
  ob.shape_key_add(name='Flat cutting piece');key=ob.shape_key_add(name='Fitted visualization')
  for v,p in zip(key.data,fit):v.co=p
  if k in ['2a','2b']:
   positioned=ob.shape_key_add(name='Positioned on flat body')
   bodyox,bodyoy=layout['1'];sx=(d['body_w']-q['parts']['2a']['width'])/2
   sy=d['max_h']/2+(q['parts']['2a']['height'] if k=='2b' else 0)
   for i,(v,(x,y,_)) in enumerate(zip(positioned.data,expanded['turned'])):v.co=(bodyox+(sx+x)*IN,bodyoy+(sy-y)*IN,.622 if i>=expanded['base_count'] else .623)
  objects[inst]=ob;ob['allowance_vertices']=len(expanded['ring']);ob['flat_cut_bounds_in']=bounds([(x,y) for x,y,_ in verts]);ob['seam_vertex_count']=expanded['base_count']
  expected=bounds(cut(q,k));assert max(abs(a-b) for a,b in zip(ob['flat_cut_bounds_in'],expected))*25.4<=.5,'Render cutting envelope mismatch'
  smooth=ob.modifiers.new('Render surface refinement','SUBSURF');smooth.levels=1;smooth.render_levels=1
  solid=ob.modifiers.new('Physical fabric thickness','SOLIDIFY');solid.thickness=profiles[q['parts'][k]['material']]['thickness_mm']/1000;solid.offset=0
  # More realistic folded bands are represented by two raw halves in one folded sheet.
  ob['stretch_direction']='UV U / circumference'
  text=bpy.data.curves.new('Label '+inst,'FONT');text.body={'1':'#1  OUTER BODY','2a':'#2a  LOWER SUPPORT','2b':'#2b  UPPER SUPPORT','3-top':'#3  TOP BAND','3-bottom':'#3  BOTTOM BAND','4':'#4  BACK INSERT'}[inst];text.size=.017;text.extrude=.0001;label=bpy.data.objects.new(text.name,text);bpy.context.collection.objects.link(label);label.location=(ox,oy-.026-(q['parts']['2a']['height']*IN if k in ['2a','2b'] else 0),.625);text.materials.append(labelmat);labels.append(label)
 for label in labels:
  label.hide_render=False;label.keyframe_insert('hide_render',frame=1);label.keyframe_insert('hide_render',frame=144);label.hide_render=True;label.keyframe_insert('hide_render',frame=145)
 # Seam details are sampled from final boundaries; matching black thread.
 seams=[]
 for inst in ['1','3-top','3-bottom','4']:
  _,_,_,ed,fit=raw[inst]
  for side in (['top','bottom'] if inst=='1' else ['left','right'] if inst=='4' else []):
   pts=[fit[i] for i in ed[side]];pts=[(x*1.001,y*1.001,z) for x,y,z in pts];seams.append(curve('Seam '+inst+' '+side,pts,thread,.00025))
 # Reference bag, shown only in diagnostics/interior views.
 _,front_radius,front_cy=torso(d['body_w']/2,center);half_depth=q['depth_target']*IN/2
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(0,front_cy-front_radius-.006-half_depth,center));bag=bpy.context.object;bag.name='REFERENCE ONLY - horizontal pouch envelope';bag.scale=(q['bag']['width']/2*IN,half_depth,q['bag']['height']/2*IN);bag.data.materials.append(material('Reference pouch',(.43,.42,.37),.7));bag.hide_render=True;bag.hide_viewport=True;bag['role']='Reference envelope only; not supplied; flange and outlet unmodeled'
 # Studio
 scene.render.engine='CYCLES';scene.cycles.samples=args.samples;scene.cycles.use_denoising=True;scene.cycles.denoising_use_gpu=True;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.08;scene.cycles.max_bounces=5
 prefs=bpy.context.preferences.addons['cycles'].preferences
 try:
  prefs.compute_device_type='METAL';prefs.get_devices()
  for dev in prefs.devices:dev.use=dev.type=='METAL'
  scene.cycles.device='GPU'
 except Exception:scene.cycles.device='CPU'
 scene.world.color=(.12,.12,.12);scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.18,.2,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
 for name,pos,power,size in [('Key',(-1,-1.4,2.3),220,1.4),('Fill',(1,-.8,1.7),130,1.2),('Rim',(0,1,1.9),260,1.1)]:
  data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.location=pos;aim(ob,(0,0,center))
 floor=mesh('Studio ground',[(-200,-200,.08),(200,-200,.08),(200,200,.08),(-200,200,.08)],[(0,1,2,3)],material('Warm studio',(.47,.46,.43),.85))
 data=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',data);bpy.context.collection.objects.link(cam);scene.camera=cam;data.lens=60;data.clip_start=.01
 scene.render.resolution_x=args.width;scene.render.resolution_y=args.height;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.fps=24;scene.frame_start=1;scene.frame_end=960
 scene.view_settings.view_transform='AgX'
 return s,q,d,w,objects,raw,seams,avatar,cam,bag,fitted

def animate(ctx):
 s,q,d,w,objects,raw,seams,avatar,cam,bag,fitted=ctx;scene=bpy.context.scene
 timings={'1':(1,500),'2a':(145,238),'2b':(238,336),'3-top':(337,433),'3-bottom':(433,528),'4':(529,672)}
 # Body stays flat during support positioning, then wraps while bands attach.
 timings['1']=(337,528)
 for inst,ob in objects.items():
  key=ob.data.shape_keys.key_blocks['Fitted visualization'];start,end=timings[inst]
  key.value=0;key.keyframe_insert('value',frame=1);key.keyframe_insert('value',frame=start)
  key.value=1;key.keyframe_insert('value',frame=end);key.keyframe_insert('value',frame=960)
  if inst in ['2a','2b']:
   position=ob.data.shape_keys.key_blocks['Positioned on flat body'];position.value=0;position.keyframe_insert('value',frame=1);position.keyframe_insert('value',frame=start);position.value=1;position.keyframe_insert('value',frame=end);position.keyframe_insert('value',frame=336);position.value=0;position.keyframe_insert('value',frame=528)
   key.value=0;key.keyframe_insert('value',frame=start);key.keyframe_insert('value',frame=end);key.keyframe_insert('value',frame=336);key.value=1;key.keyframe_insert('value',frame=528)
 # Camera catalog -> construction overview -> torso -> floating fitted hero.
 keys=[(1,(0,-.78,2.65),(0,.14,.62),40),(144,(0,-.8,2.55),(0,.14,.62),40),(336,(.55,-1.45,1.8),(0,0,.88),52),(528,(.3,-1.12,1.35),(0,0,1.016),60),(529,(.4,1.1,1.35),(0,0,1.016),60),(672,(-.25,1.1,1.35),(0,0,1.016),60),(673,(.35,-1.4,1.4),(0,0,1.10),60),(816,(.25,-1.4,1.4),(0,0,1.10),60),(817,(.25,-1.05,1.32),(0,0,1.016),66),(960,(-.45,-1.05,1.32),(0,0,1.016),66)]
 target_ob=bpy.data.objects.new('Camera framing target',None);bpy.context.collection.objects.link(target_ob);track=cam.constraints.new('TRACK_TO');track.target=target_ob;track.track_axis='TRACK_NEGATIVE_Z';track.up_axis='UP_Y'
 shift=(w['band_center_height']['value']-40)*IN
 for frame,pos,target,lens in keys:
  if frame>144:pos=(pos[0],pos[1],pos[2]+shift);target=(target[0],target[1],target[2]+shift)
  cam.location=pos;target_ob.location=target;cam.data.lens=lens;cam.keyframe_insert('location',frame=frame);target_ob.keyframe_insert('location',frame=frame);cam.data.keyframe_insert('lens',frame=frame)
 avatar.hide_render=True;avatar.keyframe_insert('hide_render',frame=1);avatar.keyframe_insert('hide_render',frame=672);avatar.hide_render=False;avatar.keyframe_insert('hide_render',frame=673);avatar.keyframe_insert('hide_render',frame=816);avatar.hide_render=True;avatar.keyframe_insert('hide_render',frame=817)
 for ob in seams:
  ob.hide_render=True;ob.keyframe_insert('hide_render',frame=1);ob.keyframe_insert('hide_render',frame=527);ob.hide_render=False;ob.keyframe_insert('hide_render',frame=528)
 scene['source_hash']=source_hash(ROOT);scene['source_revision']=s['revision'];scene['visualization_status']='Authored provisional fitted shape; physically unverified. Native cloth study is separate.'

def simulation(ctx,args):
 s,q,d,w,objects,raw,seams,avatar,cam,bag,fitted=ctx
 bag.hide_viewport=False;bag.modifiers.new('Reference pouch collision envelope','COLLISION');bag.collision.thickness_outer=.001
 for ob in objects.values():ob.hide_render=True;ob.hide_viewport=True
 for ob in seams:ob.hide_render=True;ob.hide_viewport=True
 verts=[];restverts=[];faces=[];loose=[];edges={};groups={};areas={};profiles=json.loads((ROOT/'3d-rendering/source/materials.json').read_text())['profiles']
 for inst,(vv,ff,uv,ed,fit) in raw.items():
  off=len(verts);verts.extend(fit);faces.extend(tuple(i+off for i in f) for f in ff);edges[inst]={k:[i+off for i in v] for k,v in ed.items()};groups[inst]=list(range(off,len(verts)))
  restverts.extend((x*IN,y*IN,0) for x,y,_ in vv)
  outline=cut(q,INSTANCES[inst]);areas[inst]=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(outline,outline[1:]+outline[:1])))/2*IN*IN
 def sew(a,b):
  for j,i in enumerate(a):loose.append((i,b[round(j*(len(b)-1)/max(1,len(a)-1))]))
 sew(edges['1']['top'],edges['3-top']['top']);sew(edges['1']['bottom'],edges['3-bottom']['top'])
 sew(edges['1']['top'],edges['3-top']['bottom']);sew(edges['1']['bottom'],edges['3-bottom']['bottom'])
 for inst in ['2a','2b']:
  # Attach side and curved perimeter to nearest body vertices; leave notched edge free.
  boundary=edges[inst]['left']+edges[inst]['right']+edges[inst]['bottom' if inst=='2a' else 'top']
  body=groups['1'];from mathutils.kdtree import KDTree
  kd=KDTree(len(body))
  for i in body:kd.insert(verts[i],i)
  kd.balance()
  for i in sorted(set(boundary)):_,nearest,_=kd.find(verts[i]);loose.append((i,nearest))
 for side,backside in [('left','right'),('right','left')]:
  a=edges['3-top'][side]+edges['1'][side]+list(reversed(edges['3-bottom'][side]));a=sorted(set(a),key=lambda i:verts[i][2],reverse=True);b=sorted(edges['4'][backside],key=lambda i:verts[i][2],reverse=True);sew(a,b)
 ob=mesh('Six-panel native sewing-spring study',verts,faces,bpy.data.materials['compression'],loose)
 ob.shape_key_add(name='Positioned around avatar');rest=ob.shape_key_add(name='Flat-pattern rest lengths')
 for v,co in zip(rest.data,restverts):v.co=co
 rest.value=0
 pins=ob.vertex_groups.new(name='Boundary fixture - provisional')
 for inst in ['3-top','3-bottom']:
  # Keep fold lines on the torso fixture; free body/pockets can relax.
  ids=groups[inst];pinids=[i for i in ids if abs(verts[i][2]-(w['band_center_height']['value']*IN+(d['base']/2+d['band_h'])*(1 if inst=='3-top' else -1)*IN))<.001]
  pins.add(pinids,1,'REPLACE')
 cloth=ob.modifiers.new('Native cloth / bounded sewing springs','CLOTH');cs=cloth.settings;cs.quality=8;cs.use_sewing_springs=True;cs.sewing_force_max=5;cs.vertex_group_mass=pins.name;cs.rest_shape_key=rest
 totalmass=sum(areas[inst]*profiles[q['parts'][INSTANCES[inst]]['material']]['gsm']/1000 for inst in groups);cs.mass=totalmass/len(verts);cs.tension_stiffness=8;cs.compression_stiffness=8;cs.shear_stiffness=6;cs.bending_stiffness=.3;cs.air_damping=3
 for param,groupfield,maximum in [('tension','vertex_group_structural_stiffness','tension_stiffness_max'),('shear','vertex_group_shear_stiffness','shear_stiffness_max'),('bending','vertex_group_bending','bending_stiffness_max')]:
  values=[p[param] for p in profiles.values()];lo,hi=min(values),max(values);vg=ob.vertex_groups.new(name='Material '+param)
  for inst,indices in groups.items():vg.add(indices,(profiles[q['parts'][INSTANCES[inst]]['material']][param]-lo)/(hi-lo),'REPLACE')
  setattr(cs,groupfield,vg.name);setattr(cs,param+'_stiffness',lo);setattr(cs,maximum,hi)
 cs.compression_stiffness=3;cs.compression_stiffness_max=12
 cloth.collision_settings.use_self_collision=True;cloth.collision_settings.self_distance_min=.001;cloth.collision_settings.distance_min=.002;cloth.point_cache.frame_start=1;cloth.point_cache.frame_end=48
 ob['mass_per_vertex_kg']=cs.mass;ob['total_provisional_mass_kg']=totalmass;ob['sewing_edge_count']=len(loose);ob['seam_manifest']='pattern-drafting/exports/'+args.variant+'/seams.json';ob['physical_verified']=False;ob['rest_shape']='flat seam-line patterns in meters';ob['fixture_pin_vertices']=sum(1 for v in ob.data.vertices if any(g.group==pins.index and g.weight>0 for g in v.groups))
 bpy.context.scene.frame_end=48;bpy.context.scene.gravity=(0,0,-9.81);avatar.hide_render=True;cam.animation_data_clear();cam.data.animation_data_clear();cam.location=(.45,-1.4,w['band_center_height']['value']*IN+.2);target=bpy.data.objects['Camera framing target'];target.animation_data_clear();target.location=(0,0,w['band_center_height']['value']*IN)
 return ob,cloth

def main():
 argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--variant',default='ease-05');p.add_argument('--mode',choices=['hero','simulation'],default='hero');p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080);p.add_argument('--samples',type=int,default=32);p.add_argument('--spacing',type=float,default=.005);p.add_argument('--render-frame',type=int);p.add_argument('--output');p.add_argument('--run-study',action='store_true');args=p.parse_args(argv)
 ctx=setup(args);animate(ctx);scene=bpy.context.scene;folder=ROOT/'3d-rendering';(folder/'scenes').mkdir(exist_ok=True);(folder/'reports').mkdir(exist_ok=True);(folder/'renders').mkdir(exist_ok=True)
 study=None
 if args.mode=='simulation':study,cloth=simulation(ctx,args)
 scene.frame_set(740 if args.mode=='hero' else 1)
 filename=folder/'scenes'/f'{args.variant}-{args.mode}{"-"+str(args.spacing*1000)+"mm" if args.mode=="simulation" else ""}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(filename),compress=True)
 s,q,d,w,objects,raw,seams,avatar,cam,bag,fitted=ctx
 report={'revision':s['revision'],'source_hash':source_hash(ROOT),'blender_version':bpy.app.version_string,'variant':args.variant,'mode':args.mode,'mesh_spacing_m':args.spacing,'units':'meters','physical_verified':False,'hero_geometry':'authored fitted visualization; not calibrated cloth output','piece_count':len(objects),'vertex_counts':{k:len(v[0]) for k,v in raw.items()},'provisional_center_target_in':w['band_center_circumference']['value'],'avatar_sections':[]}
 report['render_cut_envelopes_in']={inst:list(ob['flat_cut_bounds_in']) for inst,ob in objects.items()};report['allowance_vertex_counts']={inst:ob['allowance_vertices'] for inst,ob in objects.items()}
 for t in [-d['back_h']/2,-d['base']/2,0,d['base']/2,d['back_h']/2]:
  sec=cross_section([tuple(v.co) for v in avatar.data.vertices],[list(p.vertices) for p in avatar.data.polygons],w['band_center_height']['value']*IN+t*IN);report['avatar_sections'].append({'height_offset_in':t,'circumference_in':sec['perimeter_m']/IN,'status':'derived from provisional avatar'})
 if args.mode=='hero':
  from mathutils.bvhtree import BVHTree
  tree=BVHTree.FromPolygons([v.co for v in avatar.data.vertices],[list(p.vertices) for p in avatar.data.polygons]);penetrations={}
  for inst,(_,_,_,_,positions) in raw.items():
   distances=[]
   for p0 in positions:
    pt,no,_,dist=tree.find_nearest(Vector(p0));distances.append((Vector(p0)-pt).dot(no))
   penetrations[inst]={'inside_vertices_over_0_5mm':sum(v<-.0005 for v in distances),'minimum_signed_distance_m':min(distances)}
  report['avatar_intersection_check']=penetrations
  report['scenarios']=[{'pose':pose,'pouch_projection_in':depth,'status':'requires physical test; authored geometry only; no retention/pressure inference'} for pose in ['standing','seated','forward bend'] for depth in [0,.75,q['depth_target']]]
  report['production_approval']=False
 if args.run_study and study:
  snapshots=[]
  for frame in range(1,49):
   scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();ev=study.evaluated_get(deps);positions=[tuple(v.co) for v in ev.data.vertices]
  if frame in [1,12,24,48]:snapshots.append({'frame':frame,'finite':all(math.isfinite(c) for v in positions for c in v),'bounds_m':[[min(v[i] for v in positions),max(v[i] for v in positions)] for i in range(3)]})
  rest=study.data.shape_keys.key_blocks['Flat-pattern rest lengths'];face_edges=set(tuple(sorted((a,b))) for f in study.data.polygons for a,b in zip(list(f.vertices),list(f.vertices)[1:]+list(f.vertices)[:1]));strains=[math.dist(positions[a],positions[b])/max(math.dist(tuple(rest.data[a].co),tuple(rest.data[b].co)),1e-9)-1 for a,b in face_edges]
  snapshots[-1]['maximum_edge_strain']=max(strains);snapshots[-1]['minimum_edge_strain']=min(strains)
  report['native_cloth_run']={'frames':48,'sewing_edges':study['sewing_edge_count'],'fixture_pin_vertices':study['fixture_pin_vertices'],'rest_shape':study['rest_shape'],'mass_per_vertex_kg':study['mass_per_vertex_kg'],'material_groups':['tension/compression','shear','bending'],'mass_note':'Full cut-area GSM-derived total mass averaged across seam-line vertices; not per-material vertex mass','reference_pouch_collision':{'width_in':q['bag']['width'],'height_in':q['bag']['height'],'depth_in':q['depth_target'],'shape':'rigid ellipsoidal sizing envelope; flange/outlet and fluid unmodeled'},'snapshots':snapshots,'status':'exploratory fixture-pinned simulation; physical calibration absent'}
  bpy.ops.wm.save_as_mainfile(filepath=str(filename),compress=True)
 report['scene_file']=str(filename.relative_to(ROOT));report['scene_sha256']=hashlib.sha256(filename.read_bytes()).hexdigest()
 (folder/'reports'/f'{args.variant}-{args.mode}-{args.spacing:g}.json').write_text(json.dumps(report,indent=2)+'\n')
 if args.render_frame:
  scene.frame_set(args.render_frame);scene.render.filepath=args.output or str(folder/'renders'/f'{args.mode}-{args.render_frame}.png');bpy.ops.render.render(write_still=True)
 print('EFBD_BUILD_COMPLETE',filename,flush=True)
if __name__=='__main__':main()
