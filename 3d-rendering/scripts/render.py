"""Render the saved editable scene. Run with Blender -b SCENE --python THIS -- ..."""
import bpy,sys,json,argparse,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from provenance import source_hash
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
import fcntl
lockpath=ROOT/'3d-rendering/cache/render.lock';lockpath.parent.mkdir(parents=True,exist_ok=True);render_lock=lockpath.open('w');fcntl.flock(render_lock,fcntl.LOCK_EX)
p=argparse.ArgumentParser();p.add_argument('--film',action='store_true');p.add_argument('--resolution',choices=['review','4k'],default='4k');p.add_argument('--samples',type=int,default=12);p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=960);p.add_argument('--stills',action='store_true');p.add_argument('--denoise-quality',choices=['HIGH','BALANCED','FAST']);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
s=bpy.context.scene
assert s.get('source_hash')==source_hash(ROOT),'Stale scene: rebuild after dependent source changes'
s.render.engine='CYCLES';s.cycles.samples=a.samples;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.render.use_persistent_data=True
s.cycles.denoising_quality=a.denoise_quality or ('HIGH' if a.stills else 'FAST');s.cycles.adaptive_min_samples=2
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU'
except Exception:s.cycles.device='CPU'
s.render.resolution_x,s.render.resolution_y=(3840,2160) if a.resolution=='4k' else (1920,1080);s.render.resolution_percentage=100
folder=ROOT/'3d-rendering';(folder/'renders').mkdir(exist_ok=True)
def channels(owner):
 ad=owner.animation_data
 if not ad or not ad.action or not ad.action_slot:return []
 return [fc for layer in ad.action.layers for strip in layer.strips for bag in strip.channelbags if bag.slot_handle==ad.action_slot.handle for fc in bag.fcurves]
lens_curve=next((fc for fc in channels(s.camera.data) if fc.data_path=='lens'),None)
if lens_curve:lens_curve.mute=True
def set_frame(frame):
 s.frame_set(frame)
 if lens_curve:s.camera.data.lens=lens_curve.evaluate(frame)
 bpy.context.view_layer.update()
def render_checked():
 lens=s.camera.data.lens;matrix=s.camera.matrix_world.copy();bpy.ops.render.render(write_still=True)
 assert abs(s.camera.data.lens-lens)<1e-5,'Lens animation overrode validated framing'
 assert max(abs(s.camera.matrix_world[i][j]-matrix[i][j]) for i in range(4) for j in range(4))<1e-5,'Camera animation overrode validated view'
def fit_frame():
 # Keep every product piece and catalog label inside an 8% border. The avatar
 # deliberately remains contextual: its full height need not enter a torso shot.
 deps=bpy.context.evaluated_depsgraph_get();points=[]
 for ob in bpy.data.objects:
  if not ob.hide_render and ('instance_id' in ob or ob.name.startswith('Label ')):
   ev=ob.evaluated_get(deps);points.extend(ev.matrix_world@Vector(p) for p in ev.bound_box)
 assert points,'No product geometry to frame'
 for _ in range(2):
  projected=[world_to_camera_view(s,s.camera,p) for p in points];assert all(p.z>0 for p in projected),'Product behind camera'
  extent=max(max(abs(p.x-.5),abs(p.y-.5)) for p in projected)
  if extent<=.42:break
  s.camera.data.lens*=.42/extent
 projected=[world_to_camera_view(s,s.camera,p) for p in points]
 assert all(.075<=p.x<=.925 and .075<=p.y<=.925 for p in projected),'Product camera clipping'
if a.film:
 dest=folder/'frames'/a.resolution;dest.mkdir(parents=True,exist_ok=True)
 receipt={'source_hash':source_hash(ROOT),'scene_hash':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'samples':a.samples,'resolution':[s.render.resolution_x,s.render.resolution_y],'denoising':'GPU OpenImageDenoise','denoise_quality':s.cycles.denoising_quality,'adaptive_min_samples':2};receiptfile=dest/'source.json'
 if receiptfile.exists():assert json.loads(receiptfile.read_text())==receipt,'Stale frame cache: archive before rerendering'
 else:assert not list(dest.glob('*.png')),'Unidentified frame cache: archive before rendering'
 receiptfile.write_text(json.dumps(receipt,indent=2)+'\n')
 for frame in range(a.start,a.end+1):
  file=dest/f'{frame:04}.png'
  if file.exists():
   with file.open('rb') as f:f.seek(-12,2);complete=f.read(12)==b'\x00\x00\x00\x00IEND\xaeB`\x82'
   if complete:continue
   file.unlink()
  set_frame(frame);fit_frame();s.render.filepath=str(file);render_checked()
  if frame%24==0:print('EFBD_PROGRESS',frame,'of',a.end,flush=True)
if a.stills:
 for name,frame in [('catalog',72),('supports',320),('assembly',610),('torso-fit',740),('hero-front',850),('hero-angle',950)]:
  set_frame(frame);fit_frame();s.render.filepath=str(folder/'renders'/f'{name}.png');render_checked()
 # Back/side/interior camera views use fitted geometry and retain the same surface.
 set_frame(850);cam=s.camera;target=bpy.data.objects['Camera framing target'];shift=(json.loads((ROOT/'pattern-drafting/source/wearer.json').read_text())['band_center_height']['value']-40)*.0254
 for ob in [cam,target]:
  for fc in channels(ob):
   if fc.data_path=='location':fc.mute=True
 target.location=(0,0,1.016+shift)
 for name,position in [('hero-back',(0,1.05,1.32)),('hero-side',(.95,-.1,1.32)),('interior',(0,-.7,1.64))]:
  cam.location=(position[0],position[1],position[2]+shift);cam.data.lens=60
  if name=='interior':s.camera.data.lens=48
  body=next(o for o in bpy.data.objects if o.get('instance_id')=='1')
  if name=='interior':body.hide_render=True
  bpy.context.view_layer.update();fit_frame();s.render.filepath=str(folder/'renders'/f'{name}.png');render_checked();body.hide_render=False
 set_frame(850);cam.location=(.12,-.7,1.18+shift);target.location=(0,-.12,1.016+shift);cam.data.lens=70;bpy.context.view_layer.update();s.render.filepath=str(folder/'renders/material-detail.png');render_checked()
 manifest={'revision':s['source_revision'],'source_hash':source_hash(ROOT),'scene_hash':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'resolution':[s.render.resolution_x,s.render.resolution_y],'samples':a.samples,'engine':'Cycles','physical_verified':False,'mode':'stills','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((folder/'renders').glob('*.png'))}}
 (folder/'reports/render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
