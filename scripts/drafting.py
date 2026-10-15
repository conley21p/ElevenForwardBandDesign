"""Allowance-aware physical patterns and CAD bridge; all coordinates are inches."""
import copy, io, json, math, xml.etree.ElementTree as ET
from pathlib import Path
from model import load, dims, derived, shape, cut, bounds, length, digest, canonical, quantize

INSTANCES={'1':'1','2a':'2a','2b':'2b','3-top':'3','3-bottom':'3','4':'4'}
def inputs(root):
 return (json.loads((root/'pattern-drafting/source/wearer.json').read_text()),
         json.loads((root/'pattern-drafting/source/variants.json').read_text()))
def variant_spec(s,wearer,v):
 s=copy.deepcopy(s)
 if v['ease_fraction'] is not None:
  s['parts']['1']['width']=wearer['band_center_circumference']['value']*(1-v['ease_fraction'])-s['parts']['4']['width']
 assert s['parts']['1']['width']>s['parts']['1']['zone_width']
 return s
def path(pts):return 'M '+' L '.join(f'{x:.8f},{y:.8f}' for x,y in quantize(pts,8))+' Z'
def svg(s,k,vid):
 pts=cut(s,k);x0,y0,x1,y1=bounds(pts);pad=.7;w=x1-x0+2*pad;h=y1-y0+2*pad
 e=ET.Element('svg',{'xmlns':'http://www.w3.org/2000/svg','width':f'{w:.8f}in','height':f'{h:.8f}in','viewBox':f'{x0-pad} {y0-pad} {w} {h}','data-design-revision':s['revision'],'data-variant':vid,'data-part':k})
 ET.SubElement(e,'path',{'id':'cut-line','d':path(pts),'fill':'none','stroke':'#172128','stroke-width':'.015'})
 ET.SubElement(e,'path',{'id':'seam-line','d':path(shape(s,k)),'fill':'none','stroke':'#317292','stroke-width':'.012','stroke-dasharray':'.08 .06'})
 d=dims(s);hh=(bounds(shape(s,k))[3])/2
 if k=='3':ET.SubElement(e,'path',{'id':'fold-line','d':f'M 0 {hh} H {d["band_w"]}','fill':'none','stroke':'#b96026','stroke-width':'.012','stroke-dasharray':'.12 .04 .03 .04'})
 if k in ['1','3']:
  from model import body_top
  top=body_top(s);left=(d['body_w']-d['zone'])/2
  for i,xx in enumerate([left,d['body_w']/2,left+d['zone']]):
   yy=min(top,key=lambda p:abs(p[0]-xx))[1] if k=='1' else 0
   for y0 in [yy,d['max_h']-yy] if k=='1' else [0,2*d['band_h']]:
    ET.SubElement(e,'path',{'id':f'registration-{i}-{y0:g}','d':f'M {xx} {y0-.1} V {y0+.1}','stroke':'#317292','stroke-width':'.015','fill':'none'})
 if k in ['2a','2b']:
  q=s['parts']['2a'];y=0 if k=='2a' else q['height']
  free=[p for p in shape(s,k) if (p[1]<=q['notch_depth']+1e-7 if k=='2a' else p[1]>=q['height']-q['notch_depth']-1e-7) and p[0] not in [0,q['width']]]
  ET.SubElement(e,'path',{'id':'free-edge-no-sew','d':f'M 0 {y} '+' '.join(f'L {x} {yy}' for x,yy in free)+f' L {q["width"]} {y}','fill':'none','stroke':'#a74637','stroke-width':'.022'})
 # Printed calibration lives outside the pattern outline.
 ET.SubElement(e,'rect',{'id':'calibration','x':str(x0),'y':str(y1+.16),'width':'1','height':'.25','fill':'none','stroke':'black','stroke-width':'.01'})
 for y,txt in [(y0-.32,f'#{k} | {s["parts"][k]["name"]} | {vid}'),(y1+.57,'Print 100% / actual size. Calibration bar = 1 inch. Blue = seam; black = cut.')]:
  ET.SubElement(e,'text',{'x':str(x0),'y':str(y),'font-family':'sans-serif','font-size':'.12'}).text=txt
 width=bounds(shape(s,k))[2]
 ET.SubElement(e,'path',{'id':'stretch-direction','d':f'M {width*.35} {hh} h {width*.3} m -.15 -.06 l .15 .06 -.15 .06','stroke':'#617177','stroke-width':'.012','fill':'none'})
 return ET.tostring(e,encoding='utf-8',xml_declaration=True)

def seam_manifest(s,vid):
 d=derived(s);left=(d['body_w']-d['zone'])/2
 seams=[{'id':'support-lower','parts':['1','2a'],'operation':'POCKET','edges':['inside-lower-cradle','attached-perimeter'],'free_edges':['insertion','flange'],'direction':'left to right around outer perimeter'},
 {'id':'support-upper','parts':['1','2b'],'operation':'POCKET','edges':['inside-upper-cradle','attached-perimeter'],'free_edges':['insertion','flange'],'direction':'left to right around outer perimeter'}]
 for side,inst in [('top','3-top'),('bottom','3-bottom')]:
  seams.append({'id':'body-'+side,'parts':['1',inst],'operation':'JOIN','preparation':'FOLD','edges':[side,'paired-raw-folded-edge'],'lengths_in':[d['edge_length'],d['band_w']],'ease_in':d['excess'],'ease_zone_in':[left,left+d['zone']],'registration_x_in':[0,left,left+d['zone']/2,left+d['zone'],d['body_w']],'direction':'left to right; excess confined to pouch zone'})
 for side in ['left','right']:
  seams.append({'id':'back-'+side,'parts':['3-top','1','3-bottom','4'],'operation':'JOIN','edges':['short-end',side,'short-end',side],'length_in':d['back_h'],'sections_in':[d['band_h'],d['base'],d['band_h']],'direction':'top to bottom'})
 return {'revision':s['revision'],'variant':vid,'units':'in','part_instances':INSTANCES,'seams':seams,'folds':{'3-top':d['band_h'],'3-bottom':d['band_h']},'bag':s['bag'],'depth_target_in':s['depth_target'],'physical_verified':False}

def native(s,vid):
 """Seamly2D 0.6.8 format. Sampled, formula-driven drafting points."""
 d=dims(s);e=ET.Element('pattern')
 for tag,text in [('version','0.6.8'),('unit','inch'),('description',f'{s["revision"]} / {vid}. Provisional fit. Reconcile CAD edits into shared JSON before approval.'),('notes','Free support edges have no cut allowance. Native seam allowance uses node-specific values.'),('measurements','wearer.smis')]:ET.SubElement(e,tag).text=text
 inc=ET.SubElement(e,'increments')
 vals={'BodyWidth':d['body_w'],'BaseHeight':d['base'],'MaxHeight':d['max_h'],'ZoneWidth':d['zone'],'BandHeight':d['band_h'],'BackWidth':d['back_w'],'SupportWidth':s['parts']['2a']['width'],'SupportHeight':s['parts']['2a']['height'],'SA':d['sa'],'Hem':d['hem']}
 for name,val in vals.items():ET.SubElement(inc,'increment',{'name':'#'+name,'formula':str(val),'description':'Shared source; regenerate after approved change'})
 ET.SubElement(inc,'increment',{'name':'#Extra','formula':'(#MaxHeight-#BaseHeight)/2','description':'Integral expansion above and below'})
 nid=1
 for j,(instance,k) in enumerate(INSTANCES.items()):
  block=ET.SubElement(e,'draftBlock',{'name':instance});calc=ET.SubElement(block,'calculation');model=ET.SubElement(block,'modeling');pieces=ET.SubElement(block,'pieces')
  origin=nid;nid+=1
  ET.SubElement(calc,'point',{'id':str(origin),'type':'single','name':f'O{j}','x':'1','y':str(2+j*15),'mx':'0','my':'0'})
  pts=shape(s,k)
  # Body sampling remains <0.5 mm geometric error while keeping CAD responsive.
  if k=='1':
   from model import body_top
   t=body_top(s,120);pts=t+[(x,d['max_h']-y) for x,y in reversed(t)]
  nodes=[]
  for i,(x,y) in enumerate(pts):
   if k=='1':
    l=(d['body_w']-d['zone'])/2
    if x<l:xf=f'(#BodyWidth-#ZoneWidth)/2*{x/l:.12g}'
    elif x>l+d['zone']:xf=f'(#BodyWidth+#ZoneWidth)/2+(#BodyWidth-#ZoneWidth)/2*{(x-l-d["zone"])/l:.12g}'
    else:xf=f'(#BodyWidth-#ZoneWidth)/2+#ZoneWidth*{(x-l)/d["zone"]:.12g}'
    yf=f'#Extra*{y/d["extra"]:.12g}' if y<=d['extra'] else f'#MaxHeight-#Extra*{(d["max_h"]-y)/d["extra"]:.12g}'
   else:
    wx='#BodyWidth' if k=='3' else '#BackWidth' if k=='4' else '#SupportWidth'
    hy='2*#BandHeight' if k=='3' else '#BaseHeight+2*#BandHeight' if k=='4' else '#SupportHeight'
    bb=bounds(pts);xf=f'({wx})*{x/bb[2]:.12g}';yf=f'({hy})*{y/bb[3]:.12g}'
   xid=nid;yid=nid+1;mid=nid+2;nid+=3
   ET.SubElement(calc,'point',{'id':str(xid),'type':'endLine','name':f'X{j}_{i}','basePoint':str(origin),'length':xf,'angle':'0','lineType':'none','lineColor':'black','mx':'0','my':'0'})
   ET.SubElement(calc,'point',{'id':str(yid),'type':'endLine','name':f'P{j}_{i}','basePoint':str(xid),'length':yf,'angle':'270','lineType':'none','lineColor':'black','mx':'0','my':'0'})
   ET.SubElement(model,'point',{'id':str(mid),'idObject':str(yid),'type':'modeling','inUse':'true','mx':'0','my':'0'})
   nodes.append(mid)
  piece=ET.SubElement(pieces,'piece',{'id':str(nid),'name':instance,'version':'2','closed':'1','seamAllowance':'0' if k in ['2a','2b'] else '1','width':'#SA','mx':'0','my':'0'});nid+=1
  ns=ET.SubElement(piece,'nodes')
  from model import offsets
  allowances=offsets(s,k,pts)
  for i,mid in enumerate(nodes):
   attrs={'idObject':str(mid),'type':'NodePoint','before':str(allowances[i-1]),'after':str(allowances[i])}
   ET.SubElement(ns,'node',attrs)
 return ET.tostring(e,encoding='utf-8',xml_declaration=True)+b'\n'
def measurements(w):
 e=ET.Element('smis')
 for tag,txt in [('version','0.3.4'),('read-only','false'),('notes','Provisional waist = 34 inches; pants size is not a measured waist.'),('unit','inch'),('pm_system','998')]:ET.SubElement(e,tag).text=txt
 person=ET.SubElement(e,'personal')
 for tag,txt in [('family-name','Provisional'),('given-name','Athletic male'),('birth-date','1990-01-01'),('gender','male'),('email','')]:ET.SubElement(person,tag).text=txt
 body=ET.SubElement(e,'body-measurements')
 for name,val in [('height',w['height']['value']),('waist_circ',w['band_center_circumference']['value'])]:ET.SubElement(body,'m',{'name':name,'value':str(val)})
 return ET.tostring(e,encoding='utf-8',xml_declaration=True)+b'\n'

def pdf_patterns(s,vid,page=None):
 """1:1 plotter or tiled PDF, using points=72/in with 0.25in overlaps."""
 from reportlab.pdfgen.canvas import Canvas
 placements=[];y=0
 for inst,k in INSTANCES.items():
  bb=bounds(cut(s,k));placements.append((inst,k,1-bb[0],y+1-bb[1]));y+=bb[3]-bb[1]+1.4
 W=max(bounds(cut(s,k))[2]-bounds(cut(s,k))[0] for k in INSTANCES.values())+2;H=y+1
 buf=io.BytesIO();pagesize=page or (W*72,H*72);c=Canvas(buf,pagesize=pagesize,invariant=1,pageCompression=1)
 c.setTitle(f'Eleven Forward / {vid} / full-scale cutting pattern')
 pw,ph=pagesize;usablew=pw/72-1;usableh=ph/72-1;overlap=.25
 nx=math.ceil((W-overlap)/(usablew-overlap)) if page else 1;ny=math.ceil((H-overlap)/(usableh-overlap)) if page else 1
 for row in range(ny):
  for col in range(nx):
   ox=col*(usablew-overlap) if page else 0;oy=row*(usableh-overlap) if page else 0
   c.saveState();clip=c.beginPath();clip.rect(36,36,pw-72,ph-72) if page else clip.rect(0,0,pw,ph);c.clipPath(clip,stroke=0)
   c.translate(36 if page else 0,ph-36 if page else ph);c.scale(72,-72);c.translate(-ox,-oy)
   for inst,k,x,y0 in placements:
    for pts,color,dash in [(cut(s,k),(0.08,.12,.15),[]),(shape(s,k),(.15,.4,.55),[.08,.06])]:
     c.setStrokeColorRGB(*color);c.setLineWidth(.012);c.setDash(dash);p=c.beginPath();p.moveTo(x+pts[0][0],y0+pts[0][1])
     for xx,yy in pts[1:]:p.lineTo(x+xx,y0+yy)
     p.close();c.drawPath(p)
    c.setDash([]);c.setStrokeColorRGB(.65,.28,.12)
    if k=='3':c.line(x,y0+dims(s)['band_h'],x+dims(s)['band_w'],y0+dims(s)['band_h'])
    if k in ['1','3']:
     from model import body_top
     c.setStrokeColorRGB(.15,.4,.55)
     dd=dims(s);top=body_top(s);left=(dd['body_w']-dd['zone'])/2
     for xx in [left,dd['body_w']/2,left+dd['zone']]:
      yy=min(top,key=lambda p:abs(p[0]-xx))[1] if k=='1' else 0
      for ymark in [yy,dd['max_h']-yy] if k=='1' else [0,2*dd['band_h']]:c.line(x+xx,y0+ymark-.1,x+xx,y0+ymark+.1)
    # Text flip locally for upright labels in top-down drawing coordinates.
    c.saveState();c.translate(x,y0-.28);c.scale(1,-1);c.setFillColorRGB(.05,.1,.12);c.setFont('Helvetica',.14);c.drawString(0,0,f'#{inst} | {vid} | {s["parts"][k]["name"]}');c.restoreState()
   c.restoreState();c.setFillColorRGB(.08,.12,.15);c.setFont('Helvetica',8)
   c.drawString(36,ph-20,f'{s["revision"]} / {vid} / 100% ACTUAL SIZE / row {row+1}, column {col+1}')
   c.rect(36,10,72,18);c.drawString(116,16,'Calibration: 1 inch horizontal / 0.25 inch vertical')
   if page:
    c.drawString(36,ph-30,f'Grid origin {ox:.2f}, {oy:.2f} in; overlap 0.25 in. Trim to corner marks; match row/column.')
    for xx,yy in [(36,36),(pw-36,36),(36,ph-36),(pw-36,ph-36)]:c.line(xx-4,yy,xx+4,yy);c.line(xx,yy-4,xx,yy+4)
   c.showPage()
 c.save();return buf.getvalue()

def dxf(s):
 # Open, plain ASCII R12 polylines; physical units documented as inches.
 pairs=[(0,'SECTION'),(2,'HEADER'),(9,'$ACADVER'),(1,'AC1009'),(9,'$MEASUREMENT'),(70,0),(0,'ENDSEC'),(0,'SECTION'),(2,'ENTITIES')]
 y=0
 for inst,k in INSTANCES.items():
  for layer,pts in [('CUT',cut(s,k)),('SEAM',shape(s,k))]:
   pairs += [(0,'POLYLINE'),(8,inst+'_'+layer),(66,1),(70,1),(10,0),(20,0),(30,0)]
   for x,yy in pts:pairs += [(0,'VERTEX'),(8,inst+'_'+layer),(10,f'{x:.10f}'),(20,f'{-yy-y:.10f}'),(30,0)]
   pairs += [(0,'SEQEND')]
  y+=bounds(cut(s,k))[3]+2
 pairs += [(0,'ENDSEC'),(0,'EOF')]
 return '\n'.join(str(v) for pair in pairs for v in pair)+'\n'

def generate(root):
 from reportlab.pdfgen.canvas import Canvas
 s=load(root);w,vs=inputs(root);out={}
 out['pattern-drafting/native/wearer.smis']=measurements(w)
 summaries={};assembly={}
 for vid,v in vs.items():
  q=variant_spec(s,w,v);d=derived(q);manifest=seam_manifest(q,vid)
  summaries[vid]={'role':v['role'],'ease_fraction':v['ease_fraction'],'dimensions':d,'physical_verified':False}
  out[f'pattern-drafting/native/{vid}.sm2d']=native(q,vid)
  out[f'pattern-drafting/exports/{vid}/seams.json']=canonical(quantize(manifest))+b'\n'
  geometry={'revision':s['revision'],'variant':vid,'dimensions':d,'parts':{k:{'finished':shape(q,k),'cut':cut(q,k),'material':q['parts'][k]['material']} for k in ['1','2a','2b','3','4']},'seams':manifest,'bag':q['bag'],'depth_target_in':q['depth_target']}
  out[f'pattern-drafting/exports/{vid}/geometry.json']=canonical(quantize(geometry))+b'\n'
  for k in ['1','2a','2b','3','4']:out[f'pattern-drafting/exports/{vid}/part-{k}.svg']=svg(q,k,vid)
  for typ,size in [('plotter',None),('letter',(612,792)),('a4',(595.27559055,841.88976378))]:out[f'pattern-drafting/exports/{vid}/cutting-{typ}.pdf']=pdf_patterns(q,vid,size)
  out[f'pattern-drafting/exports/{vid}/cutting-r12-inches.dxf']=dxf(q)
  assembly[vid]=f'# {vid} assembly supplement\n\n{s["revision"]}. {v["role"]}. Physical fit unverified.\n\nUse the baseline manual operation order. Substitute only this variant\'s generated geometry and dimensions. Both open bands are {d["band_w"]:g} inches long and join the {d["back_w"]:g} x {d["back_h"]:g} inch insert; body/band junction registration marks must align. Body attachment edges measure {d["edge_length"]:.4f} inches; ease {d["excess"]:.4f} inches into each band within the centered {d["zone"]:g}-inch zone. Cut both bands {d["band_cut_w"]:g} x {d["band_cut_h"]:g} inches. Nominal circumference {d["circ"]:g} inches. Support and depth checks still apply. Do not mix variant pieces.\n'
  out[f'pattern-drafting/exports/{vid}/assembly-supplement.md']=assembly[vid].encode()
 out['pattern-drafting/variant-report.json']=canonical(quantize({'revision':s['revision'],'wearer':w,'variants':summaries}))+b'\n'
 selected=json.loads((root/'3d-rendering/source/shots.json').read_text())['variant']
 slots={'BODY_WIDTH':f'{s["parts"]["1"]["width"]:g}','INSERT_WIDTH':f'{s["parts"]["4"]["width"]:g}','CIRC':f'{derived(s)["circ"]:g}','WEARER_CIRC':f'{w["band_center_circumference"]["value"]:g}','HEIGHT':f'{w["height"]["value"]:g}','PANTS':str(w['pants_size']['value']),'WEARER_HEIGHT':f'{w["band_center_height"]["value"]:g}','TRIAL_EASE':f'{vs[selected]["ease_fraction"]*100:g}'}
 rows=['| Variant | Nominal relaxed circumference | #1 and each #3 width | Role |','|---|---:|---:|---|']
 rows += [f'| {vid} | {v["dimensions"]["circ"]:g} in | {v["dimensions"]["body_w"]:g} in | {v["role"]} |' for vid,v in summaries.items()]
 slots['VARIANT_TABLE']='\n'.join(rows)
 for template,target in [('pattern-drafting/source/README.md.in','pattern-drafting/README.md'),('3d-rendering/source/README.md.in','3d-rendering/README.md'),('docs/source/README.md.in','README.md')]:
  text=(root/template).read_text()
  for key,value in slots.items():text=text.replace('@@'+key+'@@',value)
  assert '@@' not in text,'Unresolved documentation field'
  out[target]=text.encode()
 # Compact measurement worksheet PDF.
 b=io.BytesIO();c=Canvas(b,pagesize=(612,792),invariant=1);c.setTitle('Eleven Forward / wearer and fabric measurements');c.setFont('Helvetica-Bold',18);c.drawString(36,745,'WEARER AND MATERIAL MEASUREMENTS');c.setFont('Helvetica',10)
 lines=['Athletic adult male / reported height 74 in / clothing label size 34.', 'Actual body measurements and fabric tests required before production approval.', 'Record in inches. State date, person, posture and intended wearing location.', '']
 lines += [name.replace('_',' ')+' : _____________________' for name in ['band_center_circumference','upper_edge_circumference','lower_edge_circumference','hip_seat_circumference','front_length','side_length','back_length','band_center_height','pouch_position_from_navel','pouch_width_height_depth','flange_diameter','outlet_access','seated_center_upper_lower','standing_center_upper_lower']]
 lines += ['','Fabric lot / composition / GSM / thickness: __________________________','Direction / load / extension / recovery: ______________________________','Seam coupon / laundering / notes: __________________________________','Measured values must replace provisional entries in wearer.json.']
 for i,line in enumerate(lines):c.drawString(36,708-i*24,line)
 c.save();out['pattern-drafting/measurement-worksheet.pdf']=b.getvalue()
 return out
