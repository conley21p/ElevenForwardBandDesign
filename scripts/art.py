"""Shared vector drawing primitives: same reportlab drawing exports SVG and PDF."""
from reportlab.graphics.shapes import Drawing,Rect,Line,PolyLine,Polygon,Circle,String
from reportlab.lib.colors import HexColor,Color
from reportlab.pdfbase.pdfmetrics import stringWidth
import html,math
INK='#20343d'; MUTED='#536772'; BLUE='#146e9b'; ORANGE='#a45314'; RED='#ad3939'; PALE='#edf3f5'; FAB='#303c43'; GREEN='#2e6a51'
class Art:
 def __init__(self,w=792,h=612):self.w=w;self.h=h;self.d=Drawing(w,h);self.rect(0,0,w,h,'#ffffff',None);self.text_bounds=[]
 def rect(self,x,y,w,h,fill=PALE,stroke=None,sw=1):
  self.d.add(Rect(x,self.h-y-h,w,h,fillColor=HexColor(fill) if fill else None,strokeColor=HexColor(stroke) if stroke else None,strokeWidth=sw))
 def line(self,x,y,xx,yy,c=MUTED,sw=1,dash=None):
  o=Line(x,self.h-y,xx,self.h-yy,strokeColor=HexColor(c),strokeWidth=sw)
  if dash:o.strokeDashArray=dash
  self.d.add(o)
 def poly(self,pts,fill=FAB,stroke=INK,sw=1,closed=True,dash=None):
  cls=Polygon if closed else PolyLine;o=cls([z for x,y in pts for z in (x,self.h-y)],fillColor=HexColor(fill) if fill and closed else None,strokeColor=HexColor(stroke) if stroke else None,strokeWidth=sw)
  if dash:o.strokeDashArray=dash
  self.d.add(o)
 def circle(self,x,y,r,fill=None,stroke=MUTED,sw=1):self.d.add(Circle(x,self.h-y,r,fillColor=HexColor(fill) if fill else None,strokeColor=HexColor(stroke) if stroke else None,strokeWidth=sw))
 def text(self,x,y,t,size=10,bold=False,c=INK,anchor='start'):
  font='Helvetica-Bold' if bold else 'Helvetica';width=stringWidth(str(t),font,size)
  actualx=x-(width/2 if anchor=='middle' else width if anchor=='end' else 0)
  assert actualx>=-1 and actualx+width<=self.w+1,f'Text outside canvas: {t}'
  assert 0<=y<=self.h,f'Text vertical bounds: {t}'
  self.text_bounds.append((actualx,y-size,width,size,str(t)))
  self.d.add(String(x,self.h-y,str(t),fontName=font,fontSize=size,fillColor=HexColor(c),textAnchor=anchor))
 def wrap(self,x,y,t,width,size=10,leading=14,bold=False,c=INK):
  font='Helvetica-Bold' if bold else 'Helvetica';lines=[]
  for par in str(t).split('\n'):
   cur=''
   for word in par.split():
    nxt=(cur+' '+word).strip()
    if cur and stringWidth(nxt,font,size)>width:lines.append(cur);cur=word
    else:cur=nxt
   lines.append(cur)
  for line in lines:self.text(x,y,line,size,bold,c);y+=leading
  return y
 def arrow(self,x,y,xx,yy,c=BLUE,sw=1.5):
  self.line(x,y,xx,yy,c,sw);ang=math.atan2(yy-y,xx-x)
  p=[(xx,yy),(xx-6*math.cos(ang-.45),yy-6*math.sin(ang-.45)),(xx-6*math.cos(ang+.45),yy-6*math.sin(ang+.45))];self.poly(p,c,c)
 def dim(self,x,y,xx,yy,label,size=9):
  self.line(x,y,xx,yy,MUTED,.7)
  if abs(yy-y)<.01:
   self.line(x,y-4,x,y+4);self.line(xx,y-4,xx,y+4);self.text((x+xx)/2,y+13,label,size,anchor='middle')
  else:
   self.line(x-4,y,x+4,y);self.line(x-4,yy,x+4,yy);self.text(x+7,(y+yy)/2+3,label,size)
 def header(self,kicker,title,subtitle,rev,index):
  self.rect(0,0,self.w,7,BLUE);self.text(32,32,kicker.upper(),9,True,BLUE)
  end=self.wrap(32,59,title,725,22,25,True)
  self.wrap(32,end+1,subtitle,725,10,13,c=MUTED)
  self.line(32,104,760,104,'#c7d4d9')
  self.text(32,590,f'ELEVEN FORWARD  /  {rev}  /  PROTOTYPE - PHYSICAL FIT NOT VERIFIED',8,c=MUTED)
  self.text(760,590,f'{index:02}',9,True,anchor='end')
 def box(self,x,y,w,h,title,body,c=BLUE):
  self.rect(x,y,w,h,PALE);self.rect(x,y,3,h,c);self.text(x+12,y+20,title,10,True,c);return self.wrap(x+12,y+38,body,w-24,9,12)

def part(a,s,k,x,y,scale=10,cutline=False,labels=False):
 from model import shape,cut,dims
 pts=shape(s,k)
 if cutline:a.poly([(x+px*scale,y+py*scale) for px,py in cut(s,k)],'#dce7eb',MUTED,.6)
 a.poly([(x+px*scale,y+py*scale) for px,py in pts],FAB,INK,.7)
 if cutline:a.poly([(x+px*scale,y+py*scale) for px,py in pts],None,BLUE,.7,dash=[3,2])
 if k=='3':
  d=dims(s);a.line(x,y+d['band_h']*scale,x+d['band_w']*scale,y+d['band_h']*scale,ORANGE,1,[5,3])
 if labels:a.text(x,y-6,'#'+k,9,True)

def bag(a,s,x,y,scale=12):
 w=s['bag']['width']*scale;h=s['bag']['height']*scale
 a.rect(x,y,w,h,'#e4e0d6','#a19f94');a.circle(x+2*scale,y+h/2,1.45*scale,'#f6f4ed','#9c9e92');a.circle(x+2*scale,y+h/2,scale,'#c8c7bf','#9c9e92');return w,h

def depth(a,s,x,y,w=360,h=160):
 from model import dims
 d=dims(s);base=x+45;mid=y+h/2
 a.line(base,y+15,base,y+h-12,INK,3)
 a.text(base-10,y+10,'BODY',8,True,anchor='middle')
 pts=[(base,y+18),(base+20,y+22),(base+70,y+42),(base+110,mid),(base+70,y+h-42),(base+20,y+h-22),(base,y+h-18)]
 a.poly(pts,'#e4e0d6',MUTED)
 a.poly([(px+7,py) for px,py in pts],None,BLUE,2,False)
 a.arrow(base,mid,base+110,mid,ORANGE)
 a.text(base+55,mid-12,f"{d['depth']:g} in target",10,True,ORANGE,anchor='middle')
 a.wrap(base+150,y+30,'Measure perpendicular to the local body plane. Flat extra fabric is not a depth guarantee.',w-210,10,14)
 a.text(x+5,y+h+8,'Side section / schematic - not to scale',8,c=MUTED)
