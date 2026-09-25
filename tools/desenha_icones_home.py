#!/usr/bin/env python3
"""
desenha_icones_home.py - desenha assets/IconesHome.png, a folha 128x160 dos
9 icones da tela principal (estilo moderno, aprovado 2026-09-24).

Squircle 30 px com degrade por funcao e simbolo branco, nas mesmas
posicoes da folha de fabrica. Desenho proprio, em codigo: nenhum pixel
da Apple nem da fabrica.

USO
    GLIFO=255,255,255 python3 tools/desenha_icones_home.py assets/IconesHome.png /tmp/ampliada.png
"""
# Proposta de folha de icones OpenPod: 128x160, 9 circulos de 30px nas posicoes de fabrica.
# Estilo: aro prata (casca da bateria 197,206,213), miolo grafite, simbolo verde (180,246,131).
import sys, math
from PIL import Image, ImageDraw, ImageFont
K=8  # supersampling
W,H=128,160
CEN=[(22.5,31.5),(63.5,31.5),(104.5,31.5),(22.5,79.5),(63.5,79.5),(104.5,79.5),(22.5,127.5),(63.5,127.5),(104.5,127.5)]
R=15.0
import os
RAD=float(os.environ.get('RAD','6'))
PRATA=(197,206,213); VERDE=(180,246,131)
img=Image.new('RGB',(W*K,H*K),(0,0,0)); d=ImageDraw.Draw(img)
def s(v): return v*K
def disc(cx,cy,r,fill): d.ellipse([s(cx-r),s(cy-r),s(cx+r),s(cy+r)],fill=fill)
def grad_shape(cx,cy,half,rad,top,bot):
    from PIL import Image as I, ImageDraw as D
    sz=int(s(2*half)); m=I.new('L',(sz,sz),0)
    D.Draw(m).rounded_rectangle([0,0,sz-1,sz-1],radius=int(s(rad)),fill=255)
    g=I.new('RGB',(sz,sz))
    gd=D.Draw(g)
    for i in range(sz):
        t=i/sz; gd.line([0,i,sz,i],fill=tuple(int(a+(b-a)*t) for a,b in zip(top,bot)))
    img.paste(g,(int(s(cx-half)),int(s(cy-half))),m)
CORES=[((255,94,98),(214,30,70)),((255,176,64),(240,110,20)),((255,82,82),(200,20,40)),
       ((90,200,250),(0,122,220)),((255,190,70),(245,130,20)),((120,220,120),(30,160,70)),
       ((70,150,255),(20,80,220)),((160,166,176),(90,96,106)),((90,190,255),(20,110,230))]
_k=[0]
GLOSS=_o_env=__import__('os').environ.get('GLOSS')=='1'
def squircle_mask(sz,rad):
    from PIL import Image as I
    m=I.new('L',(sz,sz),0); px=m.load(); r=sz/2; n=4.6
    for y in range(sz):
        for x in range(sz):
            u=abs((x+0.5-r)/r); v=abs((y+0.5-r)/r)
            if u**n+v**n<=1: px[x,y]=255
    return m
def base(cx,cy):
    from PIL import Image as I, ImageDraw as D
    top,bot=CORES[_k[0]]; _k[0]+=1
    sz=int(s(2*R)); m=squircle_mask(sz,0)
    g=I.new('RGB',(sz,sz)); gd=D.Draw(g)
    for i in range(sz):
        t=i/sz; gd.line([0,i,sz,i],fill=tuple(int(a+(b-a)*t) for a,b in zip(top,bot)))
    if GLOSS:
        hl=I.new('L',(sz,sz),0); D.Draw(hl).ellipse([-sz*0.3,-sz*0.62,sz*1.3,sz*0.46],fill=70)
        from PIL import ImageChops
        hl=ImageChops.multiply(hl,m); g.paste((255,255,255),(0,0),hl)
    img.paste(g,(int(s(cx-R)),int(s(cy-R))),m)
import os as _o
G=tuple(int(x) for x in _o.environ.get('GLIFO','180,246,131').split(',')); LW=s(1.8)
def musica(cx,cy):
    disc(cx,cy,8.5,G); disc(cx,cy,3,(214,30,70)); disc(cx,cy,1.2,G)
def play(cx,cy):
    d.arc([s(cx-8),s(cy-8),s(cx+8),s(cy+8)],40,330,fill=G,width=int(LW))
    d.polygon([(s(cx-2.5),s(cy-4.5)),(s(cx-2.5),s(cy+4.5)),(s(cx+4.5),s(cy))],fill=G)
def mic(cx,cy):
    d.rounded_rectangle([s(cx-3),s(cy-8),s(cx+3),s(cy+2)],radius=s(3),fill=G)
    d.arc([s(cx-6),s(cy-5),s(cx+6),s(cy+5)],0,180,fill=G,width=int(LW))
    d.line([s(cx),s(cy+5),s(cx),s(cy+8)],fill=G,width=int(LW)); d.line([s(cx-3.5),s(cy+8),s(cx+3.5),s(cy+8)],fill=G,width=int(LW))
def fm(cx,cy):
    f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',int(s(11)))
    d.text((s(cx),s(cy)),'FM',font=f,fill=G,anchor='mm')
def livro(cx,cy):
    d.polygon([(s(cx-9),s(cy-6)),(s(cx-0.6),s(cy-4)),(s(cx-0.6),s(cy+7)),(s(cx-9),s(cy+5))],fill=G)
    d.polygon([(s(cx+9),s(cy-6)),(s(cx+0.6),s(cy-4)),(s(cx+0.6),s(cy+7)),(s(cx+9),s(cy+5))],fill=G)
def imagem(cx,cy):
    d.rounded_rectangle([s(cx-9),s(cy-7),s(cx+9),s(cy+7)],radius=s(1.5),outline=G,width=int(LW))
    d.polygon([(s(cx-7),s(cy+5)),(s(cx-2),s(cy-1)),(s(cx+2),s(cy+3)),(s(cx+4),s(cy+1)),(s(cx+7),s(cy+5))],fill=G)
    disc(cx+4,cy-3,1.8,G)
def bt(cx,cy):
    pts=[(cx-5,cy-4),(cx+5,cy+4),(cx,cy+8.5),(cx,cy-8.5),(cx+5,cy-4),(cx-5,cy+4)]
    d.line([(s(x),s(y)) for x,y in pts],fill=G,width=int(LW),joint='curve')
def gear(cx,cy):
    for k in range(8):
        a=k*math.pi/4
        x,y=cx+7.5*math.cos(a),cy+7.5*math.sin(a)
        d.polygon([(s(x+2.2*math.cos(a+b)),s(y+2.2*math.sin(a+b))) for b in (math.pi/2,-math.pi/2,-math.pi*0.8,math.pi*0.8)],fill=G)
    disc(cx,cy,6.5,G); disc(cx,cy,2.8,(110,116,126))
def pasta(cx,cy):
    d.polygon([(s(cx-9),s(cy-6)),(s(cx-3),s(cy-6)),(s(cx-1),s(cy-4)),(s(cx+9),s(cy-4)),(s(cx+9),s(cy+7)),(s(cx-9),s(cy+7))],fill=G)
    d.line([s(cx-9),s(cy-1.5),s(cx+9),s(cy-1.5)],fill=(110,116,126),width=int(s(1)))
GLIFOS=[musica,play,mic,fm,livro,imagem,bt,gear,pasta]
for (cx,cy),g in zip(CEN,GLIFOS):
    base(cx,cy); g(cx,cy)
out=img.resize((W,H),Image.LANCZOS)
out.save(sys.argv[1]); out.resize((W*4,H*4),Image.NEAREST).save(sys.argv[2])
