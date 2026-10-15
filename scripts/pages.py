"""Manual page composition; geometry and labels always come from the shared model."""
from art import *
from model import *
import json

def desc(s,k):
 p=s['parts'][k];d=derived(s)
 if k=='1':return f"{n(d['body_w'])} wide; {n(d['base'])} base / {n(d['max_h'])} max high"
 if k in ['2a','2b']:q=s['parts']['2a'];return f"{n(q['width'])} x {n(q['height'])} max"
 if k=='3':return f"{n(d['band_w'])} x {n(d['band_h'])} finished; cut {n(d['band_cut_w'])} x {n(d['band_cut_h'])}"
 if k=='4':return f"{n(d['back_w'])} x {n(d['back_h'])} finished; cut {n(d['back_cut_w'])} x {n(d['back_cut_h'])}"
 return 'Length as needed; width / height not applicable'

def seam_sections(a,x=42,y=397):
 a.text(x,y,'LAYER DETAIL / SCHEMATIC',8,True,BLUE)
 a.rect(x,y+15,150,8,'#303c43');a.rect(x,y+24,150,8,'#778a94');a.line(x+15,y+34,x+135,y+34,BLUE,2,[3,2]);a.text(x+160,y+23,'Joined layers',9);a.text(x+160,y+37,'Blue = seam; test bulk and stretch',8,c=MUTED)

def assembly(a,s,x,y,w=140,stage=0,mode='body',active='top'):
 d=derived(s);sc=min((w-12)/d['body_w'],5);bh=d['max_h']*sc
 # A small but proportionate body with simple band / insert relationship.
 by=y+25
 part(a,s,'1',x+6,by,sc)
 bandTop=by+d['extra']*sc-d['band_h']*sc
 bandBottom=by+(d['extra']+d['base'])*sc
 if mode in ['top','both','back','finish']:
  a.rect(x+6,bandTop,d['body_w']*sc,d['band_h']*sc,'#778a94',INK,.6)
  if stage==1 and active=='top':a.line(x+6,by+d['extra']*sc,x+6+d['body_w']*sc,by+d['extra']*sc,ORANGE,1.5,[3,2])
 if mode in ['both','back','finish']:
  a.rect(x+6,bandBottom,d['body_w']*sc,d['band_h']*sc,'#778a94',INK,.6)
  if stage==1 and active=='bottom':a.line(x+6,bandBottom,x+6+d['body_w']*sc,bandBottom,ORANGE,1.5,[3,2])
 if mode in ['back','finish']:
  a.rect(x+6+d['body_w']*sc,bandTop,d['back_w']*sc,d['back_h']*sc,'#b6c6cc',INK,.6)
 if stage==1:a.arrow(x+10,by+bh+20,x+w-12,by+bh+20)
 a.text(x+7,by+bh+40,'Exterior schematic',7,c=MUTED)

def mini(a,s,mode,stage,x,y,w,h):
 d=derived(s)
 if mode in ['lower_edge','upper_edge','lower_attach','upper_attach']:
  k='2b' if 'upper' in mode else '2a';sc=10;px=x+18;py=y+50
  if 'attach' in mode:a.rect(px-6,py-18,112,78,'#dbe5e9')
  part(a,s,k,px,py,sc)
  points=shape(s,k);ds=offsets(s,k,points)
  if stage>=1:
   for i,pt in enumerate(points):
    isfree=ds[i]==0
    if (isfree and 'edge' in mode) or (not isfree and 'attach' in mode):
     q=points[(i+1)%len(points)];a.line(px+pt[0]*sc,py+pt[1]*sc,px+q[0]*sc,py+q[1]*sc,BLUE,1.7)
   a.arrow(px+20,py+55,px+80,py+55)
   if 'attach' in mode:
    for i,pt in enumerate(points):
     if ds[i]==0:
      q=points[(i+1)%len(points)];a.line(px+pt[0]*sc,py+pt[1]*sc,px+q[0]*sc,py+q[1]*sc,RED,1,[2,2])
    edgey=py if k=='2a' else py+s['parts']['2a']['height']*sc
    a.circle(px,edgey,2,BLUE,BLUE);a.circle(px+s['parts']['2a']['width']*sc,edgey,2,BLUE,BLUE)
  a.text(x+10,y+132,('Finish only free edge' if 'edge' in mode else 'Dots = start / stop'),7,c=MUTED)
  if 'attach' in mode:a.text(x+10,y+146,'Red dash = leave open',7,c=RED)
 elif mode=='position':
  a.rect(x+13,y+28,115,96,'#dbe5e9');bag(a,s,x+21,y+45,9)
  if stage>=1:
   for k,yy in [('2a',y+72),('2b',y+45)]:part(a,s,k,x+21,yy,9)
  a.text(x+10,y+144,'Inside view / left flange',7,c=MUTED)
 elif mode=='depth':
  a.line(x+20,y+30,x+20,y+128,INK,2)
  amount=25+stage*20;a.poly([(x+20,y+38),(x+amount,y+65),(x+amount+10,y+80),(x+amount,y+99),(x+20,y+122)],'#e4e0d6',MUTED)
  a.arrow(x+20,y+80,x+amount+10,y+80,ORANGE)
  a.text(x+8,y+147,['Reference plane','Progressive gauge',f"Target {n(d['depth'])} in"][stage],8,True)
 elif mode=='fold':
  if stage==0:
   a.rect(x+12,y+50,115,48,FAB);a.line(x+12,y+74,x+127,y+74,ORANGE,1.5,[4,2]);a.text(x+12,y+115,'Two open cut strips',8)
  else:
   a.rect(x+12,y+62,115,24,FAB);a.line(x+12,y+62,x+127,y+62,BLUE,1.5);a.arrow(x+65,y+43,x+65,y+59);a.text(x+12,y+115,'Fold; keep ends open',8)
 elif mode=='insert':
  sc=9;xx=x+45;yy=y+18;part(a,s,'4',xx,yy,sc)
  for hh in [d['band_h'],d['band_h']+d['base']]:a.line(xx-5,yy+hh*sc,xx+d['back_w']*sc+5,yy+hh*sc,BLUE,1.5)
  if stage>=1:
   a.line(xx,yy,xx+d['back_w']*sc,yy,ORANGE,2);a.line(xx,yy+d['back_h']*sc,xx+d['back_w']*sc,yy+d['back_h']*sc,ORANGE,2)
  a.text(x+9,y+139,'Top / body / bottom',8);a.text(x+9,y+152,f"{n(d['band_h'])} / {n(d['base'])} / {n(d['band_h'])} in",8)
 elif mode in ['back_first','back_close']:
  xx=x+30;yy=y+25;sc=8;a.rect(xx,yy,32,d['back_h']*sc,FAB);a.rect(xx+32+(8 if stage==0 else 0),yy,d['back_w']*sc,d['back_h']*sc,'#b6c6cc',INK)
  for hh in [d['band_h'],d['band_h']+d['base']]:a.line(xx,yy+hh*sc,xx+50,yy+hh*sc,'#ffffff',1)
  if stage>=1:a.line(xx+32,yy,xx+32,yy+d['back_h']*sc,BLUE,2);a.arrow(xx+25,yy+10,xx+25,yy+70)
  a.text(x+8,y+141,'Full-height join',8);a.text(x+8,y+154,'Match both junctions',7,c=MUTED)
 elif mode=='coupon':
  a.rect(x+14,y+38,110,35,FAB);a.rect(x+14,y+73,110,35,'#778a94');a.line(x+14,y+73,x+124,y+73,BLUE,2,[3,2])
  if stage>=1:a.arrow(x+55,y+73,x+20,y+73,ORANGE);a.arrow(x+80,y+73,x+118,y+73,ORANGE)
  a.text(x+10,y+139,['Match layers','Extend / release','Inspect and record'][stage],8)
 elif mode in ['materials','cut']:
  for i,k in enumerate(['1','2a','3']):part(a,s,k,x+12,y+25+i*40,2.5,cutline=(mode=='cut'),labels=True)
  if stage==1:a.arrow(x+15,y+150,x+120,y+150,ORANGE)
 elif mode=='record':
  for i in range(5):a.rect(x+15,y+24+i*22,8,8,None,MUTED);a.line(x+35,y+30+i*22,x+125,y+30+i*22,'#9aabb3',.6)
  a.text(x+15,y+153,['Measure','Document','Review / retest'][stage],8)
 else:
  target='both' if 'bottom' in mode else 'top' if 'top' in mode else 'finish'
  assembly(a,s,x,y,w,stage,target,active='bottom' if 'bottom' in mode else 'top')
  if stage==2:a.text(x+8,y+145,'Check before continuing',7,True,GREEN)

def step_page(s,st,idx):
 d=derived(s);vals={k:n(round(v,3)) for k,v in d.items()};vals['allowance_lay']=finishing_note(s);a=Art();rev=s['revision'];op=s['operations'][st['operation']]
 a.header(f"Assembly / Step {st['number']:02}",st['title'],f"Parts {', '.join('#'+k for k in st['parts'])}  |  {st['operation']}: {op['machine']}",rev,idx)
 for j,l in enumerate(['BEFORE','ACTION','CHECKED RESULT']):
  x=32+j*148;a.rect(x,119,140,192,'#f1f5f6');a.text(x+8,135,l,8,True,BLUE);mini(a,s,st['diagram'],j,x,145,140,160)
 a.text(32,333,'WHAT TO DO',10,True,BLUE);y=353
 for i,action in enumerate(st['actions'],1):
  t=action.format(**vals);a.text(32,y,str(i)+'.',10,True);y=a.wrap(49,y,t,416,10,13)+7
 assert y<565,f"Step text too long {st['id']}: {y}"
 a.text(500,133,'SEWING OPERATION',9,True,BLUE)
 yy=a.wrap(500,154,op['name']+' - '+op['stitch'],250,10,14)
 yy=a.wrap(500,yy+8,'Joining allowance: '+n(d['sa'])+' in where specified. Use the approved coupon settings.',250,9,13)
 yy+=15;a.text(500,yy,'CHECK BEFORE CONTINUING',9,True,GREEN);yy+=19
 for check in st['checks']:yy=a.wrap(500,yy,'- '+check.format(**vals),250,10,14)+9
 yy+=5;a.text(500,yy,'AVOID THIS',9,True,RED);yy=a.wrap(500,yy+19,st['mistake'].format(**vals),250,10,14)
 yy+=15;a.text(500,yy,'RECORD',9,True,BLUE);a.wrap(500,yy+18,'Operator / date / coupon ID / pass or issue. Stop and review dependent parts if the check fails.',250,9,13)
 # A compact layer section for each sewing page, below the guidance when room allows.
 if yy<450 and st['operation'] in ['JOIN','POCKET','HEM']:
  a.rect(500,yy+70,100,7,FAB);a.rect(500,yy+78,100,7,'#8b9fa8')
  if st['diagram'] in ['top_sew','bottom_sew','lower_attach','upper_attach']:a.rect(500,yy+86,100,7,'#8b9fa8')
  a.line(505,yy+96,595,yy+96,BLUE,1,[3,2]);a.text(610,yy+81,'Layer schematic',8)
 return a

def reference_pages(s,refs):
 d=derived(s);out=[]
 def page(k,title,sub):
  a=Art();a.header(k,title,sub,s['revision'],len(out)+1);out.append(a);return a
 a=page('Reference / 01','Parts catalog','Finished dimensions in inches. Six cut textile pieces; thread additional. Bag is reference-only.')
 rows=[('1',118),('2a',176),('2b',234),('3',292),('4',350),('6',408)]
 for k,y in rows:
  p=s['parts'][k];a.rect(32,y,728,53,'#f1f5f6');a.text(43,y+17,f"#{k}  {p['name']}  /  Qty {p['qty']}",11,True)
  a.text(43,y+34,desc(s,k),10)
  if k!='6':part(a,s,k,325,y+12,2,cutline=False)
  a.wrap(420,y+17,s['materials'][p['material']]['name'],327,9,12)
 a.box(32,478,354,79,'REFERENCE BAG',f"Horizontal {n(s['bag']['width'])} x {n(s['bag']['height'])} in envelope. Not part of product. Left flange is diagram orientation, not a confirmed anatomical side.")
 a.box(402,478,358,79,'CONSTRUCTION',f"Slip-on. Open body and bands join a {n(d['back_h'])}-inch full-height back insert. No separate closure or bottom binding.")
 a=page('Reference / 02','Cut lines, folds and allowances','Finished sizes are targets. The master layout shows both cut and finished boundaries; not a 1:1 print pattern.')
 a.text(32,130,'PART / FINISHED TARGET',10,True,BLUE);a.text(350,130,'CUTTING RULE',10,True,BLUE)
 rules=[('1',f"Offset all joining edges by {n(d['sa'])} in; preserve the shaped zone."),('2a',f"Add {n(d['sa'])} in only at turned attachment perimeter; none at free overedge."),('2b','Same allowances as #2a, reflected vertically; both cutouts stay left.'),('3',f"Cut two {n(d['band_cut_w'])} x {n(d['band_cut_h'])} in strips; keep short ends open."),('4',f"Cut {n(d['back_cut_w'])} x {n(d['back_cut_h'])} in; side seams plus short-edge hems.")]
 y=153
 for k,t in rules:
  a.wrap(32,y,'#'+k+'  '+desc(s,k),292,10,13);a.wrap(350,y,t,405,10,13);a.line(32,y+42,760,y+42,'#d4dfe3',.5);y+=62
 a.box(32,474,354,83,'FOLDED BAND CALCULATION',f"{n(d['band_cut_h'])} / 2 - {n(d['sa'])} = {n(d['band_h'])} in finished projection. The short-end allowances join #4, not each other.")
 a.box(402,474,358,83,'LINE LEGEND','Pale outline = cut. Blue dashed = finished seam / fold-under line. Orange dashed = fold or basting. Red = leave open.')
 a=page('Reference / 03','Equipment, needles and thread','Manufacturer guidance informs choices; the actual machines and fabric stack determine final setup.')
 columns=[(32,'MACHINES',['Serger: structural four-thread join; soft three-thread free-edge finish.','Coverstitch: back-insert hems and selected allowance finishing.','Standard machine: stretch-capable zigzag for pocket perimeter.','Rotary cutter, clips, removable markers, blunt needle, gauge and curved fixture.']), (280,'THREAD ROLES',['Polyester needle thread, sized to the fabric and machine.','Soft textured polyester in loopers where compatible; check next-to-skin feel.','Use matching black for structural seams; decoration must not restrict stretch.','Needle and looper threads are not interchangeable without testing.']), (528,'NEEDLE / FABRIC',['Use the machine-specified needle system and a knit-compatible point.','Domestic stretch needles are not a universal serger substitute.','Keep stretch around the wearer; test doubled #3 separately.','Follow supplier care and heat limits; no branded fabric performance assumed.'])]
 for x,title,items in columns:
  a.text(x,137,title,11,True,BLUE);y=164
  for t in items:y=a.wrap(x,y,t,225,10,15)+18
 a.box(32,467,728,87,'COUPON FIRST','Record machine model, needle system/size, thread positions, stitch length/width, differential feed and foot pressure. Begin with manufacturer knit settings. Change one variable at a time; retain an approved sample for each layer stack. Sources: AE, COATS, SCHMETZ.')
 a=page('Reference / 04','Serger threading and seam anatomy','Thread-role schematic, not a machine-specific threading route. Follow the actual manual for threading order.')
 colors=[BLUE,GREEN,ORANGE,RED];names=['Needle 1','Needle 2','Upper looper','Lower looper']
 for i,(c,name) in enumerate(zip(colors,names)):
  x=60+i*105;a.rect(x,137,45,38,c);a.text(x+22,160,str(i+1),13,True,'#ffffff',anchor='middle');a.line(x+22,177,x+22,230,c,2);a.arrow(x+22,230,150+i*27,310,c);a.text(x,198,name,9,True,c)
 a.rect(70,315,355,16,'#778a94');a.rect(70,332,355,16,FAB)
 for i in range(12):
  x=85+i*26;a.poly([(x,308),(x+5,354),(x+20,354),(x+24,309)],None,BLUE,1,False)
 a.text(70,375,'Two plies / schematic enlargement - not to scale',9,c=MUTED)
 a.wrap(490,139,'Four-thread construction: two needle positions plus two looper positions. Confirm the machine formation before using an ISO stitch code.',260,11,16)
 a.wrap(490,240,'Three-thread edge finish: use the machine-approved needle configuration for a soft free edge. This finish does not replace the structural join.',260,11,16)
 a.box(32,426,728,126,'FEED, BALANCE AND END SECURITY','Guide without pulling. Differential feed is adjusted on the coupon to remove waves without gathering the garment. Avoid needle cuts, exposed loops and excessive tension that limits extension. Secure chain tails through the seam with a blunt needle where the machine method permits; inspect for unraveling. Production threads are black; colors here identify roles. Sources: AE, COATS, PEGASUS.')
 a=page('Reference / 05','Coverstitch and pocket zigzag','Role diagrams and seam choices. Thread according to the actual machine manual; retain settings with the sample.')
 a.text(32,135,'COVERSTITCH / TWO NEEDLES + LOOPER',11,True,BLUE)
 for i,c in enumerate([BLUE,GREEN]):
  x=95+i*65;a.rect(x,155,30,26,c);a.arrow(x+15,181,x+15,235,c)
 a.rect(55,245,290,12,FAB)
 for x in [110,175]:a.line(x,237,x,275,BLUE,2)
 a.poly([(60,270),(105,279),(175,270),(220,279),(275,270),(335,279)],None,ORANGE,2,False)
 a.wrap(32,310,'Needle threads form face rows; looper thread covers the underside. Check tunneling and extension. Secure ends by the machine-approved method; simply clipping tails may allow unraveling.',325,10,14)
 a.text(420,135,'STANDARD MACHINE / NEEDLE + BOBBIN',11,True,BLUE)
 a.rect(445,176,265,65,'#d9e4e8');a.rect(445,207,265,34,FAB)
 a.poly([(452+i*10,215+(i%2)*12) for i in range(26)],None,BLUE,1.5,False)
 a.text(445,267,'Turned pocket edge; zigzag stays in allowance',9,c=MUTED)
 a.wrap(420,310,'Use the qualified stretch zigzag along the turned attachment perimeter. Free insertion edges remain open. Set width and length on coupons; do not substitute a rigid straight stitch.',325,10,14)
 a.box(32,430,728,122,'COMMON ERRORS','Tunneling: review thread tension, needle spacing and fabric support. Skipped stitches: confirm needle system, point, condition and threading. Cracking under stretch: review seam formation and thread consumption. Do not assume a domestic serger flatlock is an industrial flatseam. Sources: COATS, SCHMETZ, PEGASUS.')
 a=page('Reference / 06','Operation chart and troubleshooting','Prototype choices; record successful settings instead of copying universal tension numbers.')
 y=130
 for key,op in s['operations'].items():
  a.text(32,y,key,10,True,BLUE);a.text(92,y,op['name'],10,True);a.wrap(365,y,op['machine']+' / '+op['stitch'],390,9,12);y+=44
 a.box(32,463,354,90,'WAVES / BULK','Guide without stretching. Review differential feed, pressure, seam allowance and thread balance on coupons. Do not fix a mismatch by pulling every layer.')
 a.box(402,463,358,90,'STOP / REVIEW','Stop for needle cuts, broken thread, blocked access or hard folds. Record the cause and review connected materials, geometry and instructions. Sources: AE, COATS.')
 a=page('Reference / 07','Pouch expansion and easing','The flat maximum height is a design dimension. Outward depth is a separate, unverified physical requirement.')
 depth(a,s,32,125,440,190)
 a.text(500,139,'REVISED BODY EDGE',11,True,BLUE)
 y=a.wrap(500,162,f"Base {n(d['base'])} in; max {n(d['max_h'])} in. Extra {n(d['extra'])} in above and below across the {n(d['zone'])}-inch zone.",250,10,14)
 y=a.wrap(500,y+12,f"Each body seam line measures {d['edge_length']:.3f} in against a {n(d['band_w'])}-inch band seam line. Local excess: {d['excess']:.3f} in ({d['ease_percent']:.1f}% of the straight zone).",250,10,14)
 a.wrap(500,y+12,'Compute and baste the excess locally. Do not assume stretching, trimming or a flat measurement guarantees capacity.',250,10,14)
 a.box(32,383,728,168,'DEPTH CHECK / BEFORE PERMANENT SEWING',f"Use a curved body-representative fixture and smooth mock-up or gauge. Measure perpendicular to the local body plane at intermediate depth and at {n(d['depth'])} in outward projection. Check flange clearance, outlet access, insertion, removal, retention, recovery and band flatness. Do not sew with the reference bag in place. A failure stops the affected operation and triggers review of #1, #2a, #2b, #3 and material stretch together. No clinical pressure or bag capacity is established by this check.")
 return out

def appendix_pages(s,refs,start):
 out=[]
 for chunk in [refs[:4],refs[4:]]:
  a=Art();idx=start+len(out);a.header('Research appendix','Sources and limits','Source descriptions are paraphrased. Links are live in the SVG index; no standards text is reproduced.',s['revision'],idx)
  y=130
  for ref in chunk:
   a.text(32,y,ref['id']+' / '+ref['title'],12,True,BLUE);y=a.wrap(32,y+21,ref['use'],710,10,14)
   y=a.wrap(32,y+4,ref['url'],710,8,11);a.text(32,y+8,'Accessed '+ref['accessed']+' / '+ref['type'],8,c=MUTED);y+=33
  a.box(32,481,728,76,'NO CERTIFICATION CLAIM','Terminology standards do not certify the product. Coupon and laundering checks here are informal prototype checks; full laboratory procedures require the applicable standard and equipment.')
  out.append(a)
 for typ in ['SETUP AND MEASUREMENTS','FIT, EXPANSION AND CHANGE RECORD']:
  a=Art();idx=start+len(out);a.header('Prototype worksheet',typ.title(),'Complete by hand or in the source-controlled physical test record. Blank fields are not passed tests.',s['revision'],idx)
  fields=(['Operator / date / sample ID / revision','Material supplier, lot and stretch direction for each part','Machine model / needle system / needle size','Needle threads / looper threads / bobbin thread','Stitch formation / length / width / tension / differential feed','Approved coupon IDs and required extension','Relaxed circumference / side height / folded-band heights','Actual wash / dry procedure and before-after measurements'] if typ.startswith('SETUP') else ['Fixture and bag/mock-up description; flange and outlet dimensions','Depth measured from local body plane; intermediate / target result','Insertion / removal / flange and outlet clearance','Retention / band flatness / recovery / seam defects','Slip-on extension tested and limiting seam or material','Photograph / measurement record locations','Change requested; other affected parts and operations','Pass / fail / not evaluated; next revision / retest required'])
  y=135
  for f in fields:
   a.text(32,y,f,10,True);a.line(32,y+24,760,y+24,'#acbdc5',.7);y+=51
  out.append(a)
 return out
