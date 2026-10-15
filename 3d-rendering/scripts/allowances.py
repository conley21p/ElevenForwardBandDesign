"""Render cut borders and their returned seam/hem positions; units are inches."""
import math
from model import offsets,offset_polygon,finishing_note

def expand(s,k,verts,faces,uv,boundary):
 finishing_note(s) # Unsupported finishing changes must not silently render.
 pts=[verts[i][:2] for i in boundary]
 ds=([s['back_hem_allowance'] if abs(a[1]-b[1])<1e-9 else s['seam_allowance'] for a,b in zip(pts,pts[1:]+pts[:1])] if k=='4' else offsets(s,k,pts))
 outer=offset_polygon(pts,ds)
 result={'verts':list(verts),'faces':list(faces),'uv':list(uv),'turned':list(verts),'ring':[],'base_count':len(verts)}
 oi=[]
 for bi,p,o in zip(boundary,pts,outer):
  if math.dist(p,o)<1e-8:oi.append(bi);continue
  idx=len(result['verts']);oi.append(idx);result['ring'].append(idx)
  result['verts'].append((o[0],o[1],0));result['uv'].append((o[0]*.0254,o[1]*.0254))
  if k in ['1','2a','2b']:turned=(2*p[0]-o[0],2*p[1]-o[1],0)
  elif k=='3':turned=(2*p[0]-o[0],o[1],0)
  else:turned=(o[0],2*p[1]-o[1],0)
  result['turned'].append(turned)
 for j,bi in enumerate(boundary):
  jj=(j+1)%len(boundary);face=list(dict.fromkeys([bi,oi[j],oi[jj],boundary[jj]]))
  area2=abs(sum(result['verts'][a][0]*result['verts'][b][1]-result['verts'][a][1]*result['verts'][b][0] for a,b in zip(face,face[1:]+face[:1])))
  if len(face)>=3 and area2>1e-12 and (oi[j]!=bi or oi[jj]!=boundary[jj]):result['faces'].append(tuple(face))
 return result
