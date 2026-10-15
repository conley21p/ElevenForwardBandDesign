"""Encode actual 24fps Cycles frames to 4K and 1080p MP4, with restrained captions."""
import argparse,json,subprocess,hashlib
from pathlib import Path
from model import ROOT,load
from provenance import source_hash
def run(root=ROOT):
 source=root/'3d-rendering/frames/4k';frames=sorted(source.glob('*.png'));assert len(frames)==960,'Need all 960 native 4K frames'
 receipt=json.loads((source/'source.json').read_text());assert receipt['source_hash']==source_hash(root),'Stale frame cache'
 assert [p.name for p in frames]==[f'{i:04}.png' for i in range(1,961)],'Missing/extra frame'
 folder=root/'3d-rendering/video';folder.mkdir(exist_ok=True)
 # Drawtext is optional on some FFmpeg packages; use captions in a separate SRT too.
 labels=[(0,6,'Six textile pieces'),(6,14,'Interior supports / flange clearance'),(14,22,'Identical folded top and bottom bands'),(22,28,'Higher-stretch back insert'),(28,34,'Provisional male torso fit'),(34,40,'Eleven Forward / fitted product')]
 srt=[]
 def stamp(t):return f'00:00:{t:02},000'
 for i,(a,b,label) in enumerate(labels,1):srt.extend([str(i),f'{stamp(a)} --> {stamp(b)}',label,''])
 (folder/'assembly-captions.srt').write_text('\n'.join(srt))
 filters=subprocess.run(['ffmpeg','-hide_banner','-filters'],capture_output=True,text=True).stdout
 vf=[]
 if 'drawtext' in filters:
  for a,b,label in labels:
   vf.append(f"drawtext=text='{label}':fontcolor=white:fontsize=44:x=90:y=h-140:box=1:boxcolor=black@0.5:boxborderw=18:enable='gte(t,{a})*lt(t,{b})'")
 for name,size in [('assembly-4k.mp4',None),('assembly-1080p.mp4',(1920,1080))]:
  chain=list(vf)
  if size:chain.append('scale=1920:1080:flags=lanczos')
  cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate','24','-start_number','1','-i',str(source/'%04d.png')]
  if chain:cmd+=['-vf',','.join(chain)]
  cmd+=['-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(folder/name)]
  subprocess.run(cmd,check=True)
  data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(folder/name)],text=True));v=data['streams'][0]
  assert v['r_frame_rate']=='24/1' and int(v['nb_frames'])==960 and abs(float(data['format']['duration'])-40)<.05
  assert (v['width'],v['height'])==((3840,2160) if size is None else size)
 manifest={'revision':load(root)['revision'],'source_hash':source_hash(root),'scene_hash':receipt['scene_hash'],'render_settings':receipt,'frames':960,'fps':24,'duration_seconds':40,'physical_verified':False,'render_method':'Native Cycles 4K frames; no frame interpolation or resolution upscaling','outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*') if p.suffix in ['.mp4','.srt']}}
 (folder/'video-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS: 40-second / 24fps / native 4K and 1080p videos')
if __name__=='__main__':run()
