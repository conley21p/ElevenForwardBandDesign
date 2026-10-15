"""One reproducible build command for CAD, Blender studies, stills and film."""
import argparse,subprocess,sys,json,fcntl
from pathlib import Path
from model import ROOT
from build import build
from cad_bridge import export
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['build','verify']);p.add_argument('--seamly',default='/Volumes/Seamly2D/Seamly2D.app/Contents/MacOS/Seamly2D');p.add_argument('--blender',default='/Applications/Blender.app/Contents/MacOS/Blender');p.add_argument('--film',action='store_true');a=p.parse_args()
 if a.command=='verify':
  from verify import verify
  verify();return
 cache=ROOT/'3d-rendering/cache';cache.mkdir(exist_ok=True)
 build_lock=(cache/'pipeline.lock').open('w')
 try:fcntl.flock(build_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('Another pipeline build is already running; resume that build before starting another.')
 build();export(a.seamly)
 def blender(script,args,scene=None):
  cmd=[a.blender,'-b']+([str(scene)] if scene else ['--factory-startup'])+['--python-exit-code','1','--python',str(ROOT/'3d-rendering/scripts'/script),'--']+args
  with (cache/(script+'.log')).open('w') as log:subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 blender('scene.py',['--mode','hero'])
 scene=ROOT/'3d-rendering/scenes/ease-05-hero.blend';blender('render.py',['--stills','--resolution','4k','--samples','48'],scene)
 blender('diagnostics.py',[],scene)
 for vid in ['ease-00','ease-05','ease-10']:blender('scene.py',['--mode','simulation','--variant',vid,'--run-study'])
 blender('scene.py',['--mode','simulation','--spacing','.0025','--run-study'])
 blender('coupons.py',[])
 from delivery_docs import build_delivery_docs
 build_delivery_docs()
 if a.film:
  blender('render.py',['--film','--resolution','4k','--samples','12'],scene)
  from encode_video import run
  run()
 print('Built patterns, CAD bridge, native scenes, studies and renders. Run verify after impact review.')
if __name__=='__main__':main()
