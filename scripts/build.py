#!/usr/bin/env python3
"""Build deterministic SVG pages, layout, documents and a bookmarked vector PDF."""
from pathlib import Path
import json,hashlib,io,sys,xml.etree.ElementTree as ET
from reportlab.graphics import renderSVG,renderPDF
from reportlab.pdfgen.canvas import Canvas
from model import *
from art import *
from pages import *

SOURCE_PATHS=['design/design-spec.json','manual/source/steps.json','manual/source/references.json']
def source_hash(root):
 from provenance import source_hash as compute
 return compute(root)
def read_all(root):
 s=load(root);steps=json.loads((root/SOURCE_PATHS[1]).read_text());refs=json.loads((root/SOURCE_PATHS[2]).read_text());validate(s,steps);return s,steps,refs

def svg_bytes(a,rev,prev=None,next=None):
 raw=renderSVG.drawToString(a.d)
 if isinstance(raw,bytes):raw=raw.decode()
 root=ET.fromstring(raw);root.set('data-design-revision',rev)
 if a.w==792:root.set('width','11in');root.set('height','8.5in')
 # Navigation is an SVG overlay; PDF has separate page bookmarks.
 for x,label,url in [(560,'Previous',prev),(665,'Next',next)]:
  if not url:continue
  g=ET.SubElement(root,'{http://www.w3.org/2000/svg}a',{'href':url})
  t=ET.SubElement(g,'{http://www.w3.org/2000/svg}text',{'x':str(x),'y':str(a.h-8),'font-size':'8','font-family':'Helvetica','fill':BLUE});t.text=label
 return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def layout(s):
 d=derived(s);a=Art(1500,2520);a.rect(0,0,1500,9,BLUE)
 a.text(60,55,'ELEVEN FORWARD / MATERIAL AND CUTTING LAYOUT',30,True)
 a.text(60,88,s['revision']+' | Common scale: 30 SVG units = 1 inch | Prototype, not a full-size print pattern',16)
 a.text(60,116,'Pale = cutting allowance. Black = finished seam boundary. Blue dashed = seam line. Orange = fold.',16)
 a.text(60,146,'Cut sizes include prototype allowances; material behavior and outward pouch depth remain unverified.',16)
 a.text(60,191,'#1 MAIN OUTER BODY / QTY 1',23,True)
 a.text(60,218,s['materials']['compression']['name'],17)
 x,y=85,280;part(a,s,'1',x,y,30,True)
 a.dim(x,y+330,x+d['body_w']*30,y+330,f"{n(d['body_w'])} in finished width",15)
 a.dim(1200,y+d['extra']*30,1200,y+(d['extra']+d['base'])*30,f"{n(d['base'])} in base",14)
 a.dim(1340,y,1340,y+d['max_h']*30,f"{n(d['max_h'])} in max",14)
 a.dim(x+(d['body_w']-d['zone'])*15,y-25,x+(d['body_w']+d['zone'])*15,y-25,f"{n(d['zone'])} in pouch zone",14)
 a.text(60,671,f"Extra {n(d['extra'])} in above + below. Cut outline offsets every joining edge by {n(d['sa'])} in.",17)
 a.text(60,697,f"Body attachment edge: {d['edge_length']:.3f} in; matching band: {n(d['band_w'])} in; local excess: {d['excess']:.3f} in.",17)
 a.text(60,723,f"Outward depth target: {n(d['depth'])} in from body plane. Flat extra fabric does not establish this capacity.",17)
 for k,x,title in [('2a',85,'LOWER'),('2b',580,'UPPER')]:
  a.text(x-25,782,f'#{k} {title} SUPPORT / QTY 1',21,True);a.text(x-25,810,s['materials']['support']['name'],15)
  part(a,s,k,x,850,30,True)
  a.dim(x,970,x+s['parts']['2a']['width']*30,970,f"{n(s['parts']['2a']['width'])} in finished width",14);a.dim(x+335,850,x+335,850+s['parts']['2a']['height']*30,f"{n(s['parts']['2a']['height'])} in max",13)
  a.wrap(x-25,1020,f"Cut: {n(d['sa'])} in at attached outer perimeter only. No allowance at free notched edge.",430,16,21)
 a.text(1100,782,'REFERENCE BAG',19,True);bag(a,s,1100,850,30)
 a.dim(1100,1060,1100+s['bag']['width']*30,1060,f"{n(s['bag']['width'])} in horizontal",13)
 a.dim(1430,850,1430,850+s['bag']['height']*30,f"{n(s['bag']['height'])} in",12)
 a.text(1100,1100,'Sizing only; not product',13)
 a.text(60,1125,'#3 IDENTICAL TOP AND BOTTOM BANDS / QTY 2',23,True)
 a.text(60,1153,s['materials']['band']['name'],17)
 part(a,s,'3',85,1200,30,True)
 a.dim(77.5,1360,85+(d['band_w']+d['sa'])*30,1360,f"{n(d['band_cut_w'])} in CUT length",15)
 a.dim(1230,1192.5,1230,1200+(2*d['band_h']+d['sa'])*30,f"{n(d['band_cut_h'])} in CUT",14)
 a.text(60,1420,f"Unfolded fabric shown. Fold at orange line: {n(d['band_w'])} x {n(d['band_h'])} in finished per band.",17)
 a.text(60,1446,'Short ends stay open and join #4. Same material, shape and cut for top and bottom.',17)
 a.text(60,1510,'#4 FULL-HEIGHT ELASTIC BACK INSERT / QTY 1',23,True)
 a.text(60,1538,s['materials']['elastic']['name'],17)
 part(a,s,'4',85,1580,30,True)
 a.dim(77.5,1940,85+(d['back_w']+d['sa'])*30,1940,f"{n(d['back_cut_w'])} in CUT",14)
 a.dim(230,1572.5,230,1580+(d['back_h']+d['hem'])*30,f"{n(d['back_cut_h'])} in CUT",14)
 for hh in [d['band_h'],d['band_h']+d['base']]:a.line(80,1580+hh*30,150,1580+hh*30,BLUE,1.7)
 a.text(420,1605,f"Finished: {n(d['back_w'])} x {n(d['back_h'])} in. Side seams: {n(d['sa'])} in. End hems: {n(d['hem'])} in.",17)
 a.text(420,1640,f"Top {n(d['band_h'])} / body {n(d['base'])} / bottom {n(d['band_h'])} in sections align at both joins.",17)
 a.text(420,1675,'Sew the bands to #1 while flat, then sew two full-height insert seams.',17)
 a.text(420,1710,f"Each horizontal level: {n(d['body_w'])} in main section + {n(d['back_w'])} in insert = {n(d['circ'])} in nominal.",17)
 a.wrap(420,1750,'The insert stretches across its narrow width. Test the full assembly: the body, doubled bands, hems and seams can limit overall extension.',920,17,24)
 a.text(60,2020,'#6 THREAD / AS REQUIRED',23,True)
 a.text(60,2053,s['materials']['thread']['name'],17)
 a.text(60,2083,'Black structural stitching. Optional lime decoration must not restrict stretch. Thread is not a cut panel.',17)
 a.text(60,2145,'SIX CUT TEXTILE PIECES + THREAD. SLIP-ON: NO HOOK-AND-EYE CLOSURE.',20,True)
 a.wrap(60,2186,'Finished dimensions are separate from cutting dimensions. Quarter-inch allowances are prototype choices. Interior free edges are overedge-finished; attachment edges are turned under and zigzagged. Pouch volume, flange clearance and slip-on extension require a recorded physical sample.',1375,17,25)
 a.text(60,2310,'ASSEMBLY AND CHANGE CONTROL',21,True,BLUE)
 a.wrap(60,2347,'Update design/design-spec.json and the affected operation text first. Regenerate this layout and the manual together. Every request needs a downstream-impact review; previously passed physical checks require retest after relevant changes.',1360,17,25)
 a.text(60,2475,'See manual/index.md for step pages, printable PDF, sources and inspection worksheets.',16,c=MUTED)
 return a

def catalog_md(s):
 d=derived(s);lines=['# Current design specification','',f"Revision: **{s['revision']}**. Generated from shared design data; edit the source, not this table.",'','## Parts','', '| ID | Item | Qty | Finished / cut dimensions (inches) | Material |','|---|---|---:|---|---|']
 for k,p in s['parts'].items():lines.append(f"| {k} | {p['name']} | {p['qty']} | {desc(s,k)} | {s['materials'][p['material']]['name']} |")
 lines+=['','## Construction and cutting',f"- #1: {n(d['extra'])} inches extra above and below across a centered {n(d['zone'])}-inch zone. Offset all joining boundaries by {n(d['sa'])} inch for cutting.",'- #2a/#2b: left-side flange reliefs; upper is a vertical reflection. Quarter-inch allowance at turned attached perimeter only, none at the free insertion edge. Free edges are softly overedged; pocket attachment uses a coupon-qualified stretch zigzag.',f"- #3: two open folded strips, each cut {n(d['band_cut_w'])} x {n(d['band_cut_h'])}. Folded finished projection: {n(d['band_cut_h'])}/2 - {n(d['sa'])} = {n(d['band_h'])} inches. Short ends join #4, not each other.",f"- #4: cut {n(d['back_cut_w'])} x {n(d['back_cut_h'])}; finish at {n(d['back_w'])} x {n(d['back_h'])}. Side joining allowances {n(d['sa'])}; top/bottom turned hems {n(d['hem'])}.",f"- The insert bridges top {n(d['band_h'])} / body {n(d['base'])} / bottom {n(d['band_h'])} inch sections. Finished nominal circumference is {n(d['circ'])} inches; no negative-ease claim is implied.",'- Attach pockets, finish insert ends, fold and attach open bands, then sew both full-height back seams. Six textile pieces plus thread. No closure or separate elastic binding.','', '## Expansion and ease',f"Body seam line: {d['edge_length']:.4f} inches each. Band attachment seam: {n(d['band_w'])} inches. Excess {d['excess']:.4f} inches is local to the shaped zone ({d['ease_percent']:.2f}% relative to its straight length). Numerical polyline integration uses a sampled smooth profile.",f"The target is {n(d['depth'])} inches of outward pouch depth from the local body plane, not additional flat height. A curved-fixture test must confirm clearance, insertion/removal, retention, recovery and band behavior. All physical checks currently require retest.",f"Side assembly height target: {n(d['back_h'])} inches. The {n(d['max_h'])}-inch body maximum plus bands is a flat-pattern relationship, not a guaranteed assembled front height.",'','## Material and setup status','Fiber ratios, fabric weight, supplier, branded wicking technology, thread sizes and machine settings are not established. Material names are proposals; no Dri-FIT certification or reference-brand composition is claimed. Follow material care limits and qualify all seams on representative coupons.','', '## Scale','Master layout uses 30 SVG units/inch. Catalog manual pages are labeled schematics, not 1:1 cutting patterns. The unfolded #3 outline is twice the finished height before allowances.','']
 return '\n'.join(lines)

def build(root=ROOT,out=None):
 out=Path(out or root);s,steps,refs=read_all(root);rev=s['revision'];generated={};boundslog={}
 def save(path,data):
  b=data.encode() if isinstance(data,str) else data;generated[path]=b
 a=layout(s)
 # master reference bag must share 30-unit scale: part below fixed by local script source.
 save('design/ostomy-band-scaled-layout.svg',svg_bytes(a,rev))
 pages=reference_pages(s,refs);titles=['Parts catalog','Cutting and allowances','Equipment and threads','Serger threading','Coverstitch and zigzag','Operation chart','Pouch expansion']
 for st in steps:pages.append(step_page(s,st,len(pages)+1));titles.append(f"Step {st['number']:02} - {st['title']}")
 pages+=appendix_pages(s,refs,len(pages)+1);titles+=['Research - manufacturers','Research - standards','Worksheet - setup','Worksheet - fit and change']
 filenames=[f"{i+1:02}-"+''.join(c.lower() if c.isalnum() else '-' for c in t).strip('-')+'.svg' for i,t in enumerate(titles)]
 pdfbuf=io.BytesIO();pdf=Canvas(pdfbuf,pagesize=(792,612),invariant=1,pageCompression=1);pdf.setTitle('Eleven Forward - Prototype Assembly Manual');pdf.setAuthor('Eleven Forward')
 for i,(page,title,fn) in enumerate(zip(pages,titles,filenames)):
  save('manual/pages/'+fn,svg_bytes(page,rev,filenames[i-1] if i else None,filenames[i+1] if i+1<len(pages) else None))
  pdf.bookmarkPage(f'p{i+1}');pdf.addOutlineEntry(title,f'p{i+1}',0,False);renderPDF.draw(page.d,pdf,0,0);pdf.showPage();boundslog[fn]=page.text_bounds
 pdf.save();save('manual/assembly-manual.pdf',pdfbuf.getvalue())
 save('docs/DESIGN_SPEC.md',catalog_md(s))
 idx=['# Assembly manual','',f'Revision **{rev}**. Prototype instructions; physical performance unverified.','', '[Printable PDF](assembly-manual.pdf) | [Master material layout](../design/ostomy-band-scaled-layout.svg)','']
 idx += [f"{i+1}. [{t}](pages/{fn})" for i,(t,fn) in enumerate(zip(titles,filenames))]
 idx += ['','## Research links','']+[f"- [{r['id']}: {r['title']}]({r['url']}) - {r['use']} Accessed {r['accessed']}." for r in refs]
 save('manual/index.md','\n'.join(idx)+'\n')
 save('docs/RESEARCH.md','# Sewing research\n\nManufacturer guidance and standards catalog references; not a certification claim.\n\n'+'\n\n'.join(f"### {r['id']} - {r['title']}\n\n[{r['url']}]({r['url']})\n\n{r['use']} Accessed {r['accessed']}." for r in refs)+'\n\nProject choices: quarter-inch prototype allowances, open folded edge bands, full-height back insert, turned and zigzagged pocket attachments. These are not requirements imposed by a cited standard.\n')
 save('manual/page-manifest.json',json.dumps({'revision':rev,'source_hash':source_hash(root),'pages':[{'number':i+1,'title':t,'file':'pages/'+fn} for i,(t,fn) in enumerate(zip(titles,filenames))]},indent=2)+'\n')
 from drafting import generate
 for path,data in generate(root).items():save(path,data)
 manifest={'revision':rev,'source_hash':source_hash(root),'outputs':{k:hashlib.sha256(v).hexdigest() for k,v in sorted(generated.items())}}
 save('design/generated-manifest.json',json.dumps(manifest,indent=2)+'\n')
 for path,data in generated.items():
  p=out/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return generated

if __name__=='__main__':
 build();print('Built master layout, 31 SVG pages, bookmarked PDF, specifications and manifests.')
