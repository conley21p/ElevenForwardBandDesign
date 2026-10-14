"""Derived geometry in inches. Only this module resolves dimensional formulas."""
import json, math, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(root=ROOT): return json.loads((root/'design/design-spec.json').read_text())
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def digest(v): return hashlib.sha256(canonical(v)).hexdigest()
def n(v): return f'{v:g}'
def dims(s):
 p=s['parts'];a=s['seam_allowance'];b=p['1'];h=p['3']['height'];w=b['width'];backh=b['base_height']+2*h
 return dict(sa=a,hem=s['back_hem_allowance'],body_w=w,base=b['base_height'],max_h=b['max_height'],zone=b['zone_width'],extra=(b['max_height']-b['base_height'])/2,band_w=w,band_h=h,band_cut_w=w+2*a,band_cut_h=2*h+2*a,back_w=p['4']['width'],back_h=backh,back_cut_w=p['4']['width']+2*a,back_cut_h=backh+2*s['back_hem_allowance'],circ=w+p['4']['width'],depth=s['depth_target'])
def body_top(s,N=360):
 d=dims(s);w=d['body_w'];e=d['extra'];z=d['zone'];left=(w-z)/2;r=z/3
 def height(x):
  t=(x-left)/r
  if x<left or x>left+z:return e
  if t<=1:return e*(1-(3*t*t-2*t*t*t))
  if x<=left+z-r:return 0
  t=(left+z-x)/r;return e*(1-(3*t*t-2*t*t*t))
 xs=sorted(set([w*i/N for i in range(N+1)]+[left,left+r,left+z-r,left+z]))
 return [(x,height(x)) for x in xs]
def shape(s,k):
 d=dims(s);p=s['parts'];a=s['seam_allowance']
 if k=='1':
  t=body_top(s);return t+[(x,d['max_h']-y) for x,y in reversed(t)]
 if k in ['2a','2b']:
  q=p['2a'];w=q['width'];h=q['height'];l=q['notch_center']-q['notch_width']/2
  pts=[(0,0),(l,0)]+[(l+q['notch_width']*i/80,q['notch_depth']*math.sin(math.pi*i/80)) for i in range(1,81)]+[(w,0),(w,h-.6)]
  pts += [(w-.6+.6*math.cos(t),h-.6+.6*math.sin(t)) for t in [math.pi/2*i/20 for i in range(1,21)]]
  pts += [(.6,h)]+[(.6+.6*math.cos(t),h-.6+.6*math.sin(t)) for t in [math.pi/2+math.pi/2*i/20 for i in range(1,21)]]
  if k=='2b':pts=[(x,h-y) for x,y in reversed(pts)]
  return pts
 if k=='3': return [(0,0),(d['band_w'],0),(d['band_w'],2*d['band_h']),(0,2*d['band_h'])]
 if k=='4':return [(0,0),(d['back_w'],0),(d['back_w'],d['back_h']),(0,d['back_h'])]
 raise ValueError(k)
def offsets(s,k,pts):
 a=s['seam_allowance']
 if k in ['1','3']:return [a]*len(pts)
 if k=='4':return [s['back_hem_allowance'],a,s['back_hem_allowance'],a]
 # Free notched edge spans endpoints with both y <= notch_depth; sides also include a point below this.
 h=s['parts']['2a']['height'];dep=s['parts']['2a']['notch_depth'];w=s['parts']['2a']['width']
 vals=[]
 for i,(x,y) in enumerate(pts):
  xx,yy=pts[(i+1)%len(pts)]
  free=(y<=dep+1e-7 and yy<=dep+1e-7) if k=='2a' else (y>=h-dep-1e-7 and yy>=h-dep-1e-7)
  # explicitly exclude vertical side segments
  free=free and abs(xx-x)>1e-9
  vals.append(0 if free else a)
 return vals

def offset_polygon(pts,ds):
 """Intersection of adjacent outward offset segments (sampled curved paths)."""
 lines=[]
 for i,(x,y) in enumerate(pts):
  xx,yy=pts[(i+1)%len(pts)];dx,dy=xx-x,yy-y;L=math.hypot(dx,dy)
  if L<1e-10:raise ValueError('duplicate vertex')
  nx,ny=dy/L,-dx/L;lines.append(((x+nx*ds[i],y+ny*ds[i]),(dx,dy)))
 result=[]
 for i in range(len(pts)):
  (p,u),(q,v)=lines[i-1],lines[i];cross=u[0]*v[1]-u[1]*v[0]
  if abs(cross)<1e-10:result.append(q);continue
  t=((q[0]-p[0])*v[1]-(q[1]-p[1])*v[0])/cross
  result.append((p[0]+t*u[0],p[1]+t*u[1]))
 return result

def cut(s,k):
 p=shape(s,k);return offset_polygon(p,offsets(s,k,p))
def bounds(pts):
 xs,ys=zip(*pts);return (min(xs),min(ys),max(xs),max(ys))
def length(p):return sum(math.dist(a,b) for a,b in zip(p,p[1:]))
def derived(s):
 d=dims(s);d['edge_length']=length(body_top(s));d['excess']=d['edge_length']-d['band_w'];d['zone_edge']=d['zone']+d['excess'];d['ease_percent']=100*d['excess']/d['zone'];return d

def validate(s,steps):
 p=s['parts'];d=dims(s)
 assert s['units']=='in' and s['scale']==30,'Unit/scale change requires renderer and instruction review'
 assert s['formulas']=={'extra_per_side':'(parts.1.max_height - parts.1.base_height) / 2','nominal_circumference':'parts.1.width + parts.4.width','band_cut_width':'parts.3.width + 2 * seam_allowance','band_cut_height':'2 * parts.3.height + 2 * seam_allowance'},'Dimensional formula changed: update the resolver and tests'
 assert set(p)=={'1','2a','2b','3','4','6'},'Active part IDs mismatch'
 assert p['3']['width_formula']=='parts.1.width','Band length dependency changed: review connections'
 assert p['4']['height_formula']=='parts.1.base_height + 2 * parts.3.height','Back height dependency changed'
 assert p['2b']['mirror_of']=='2a','Upper support must mirror lower support vertically'
 assert sum(v['qty'] for k,v in p.items() if k!='6')==6,'Textile count must be reviewed'
 assert p['3']['qty']==2,'Both bands are required'
 assert d['max_h']>d['base']>0 and d['body_w']>d['zone']>0
 for q in p.values():
  assert q['material'] in s['materials']
  assert all(op in s['operations'] for op in q['operations'])
 for c in s['connections']:assert c['from'] in p and c['to'] in p
 assert [x['number'] for x in steps]==list(range(1,21))
 for step in steps:
  assert all(k in p for k in step['parts']),f"Unknown part in {step['id']}"
  assert step['operation'] in s['operations']
 for k in ['1','2a','2b','3','4']:
  a,b,c,e=bounds(cut(s,k));assert c>a and e>b
 for name,check in s['physical_checks'].items():
  assert check['status'] in ['requires retest','not evaluated','physically verified']
  if check['status']=='physically verified':
   evidence=check.get('evidence');assert isinstance(evidence,dict) and all(evidence.get(k) for k in ['date','record','design_hash','result']),f'Missing evidence for {name}'
   facts={k:v for k,v in s.items() if k!='physical_checks'}
   assert evidence['design_hash']==digest(facts),f'Stale physical verification for {name}'
 return d
