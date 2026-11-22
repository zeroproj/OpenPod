#!/usr/bin/env python3
"""gera_nanoclone128.py - adapta o tema NanoClone (176x132, deitado) para o Rockbox YP3 (128x160, em pe).

NanoClone: Billy Blair, CC-BY-SA 3.0 (originais em nanoclone_original/). Esta adaptacao tambem e
CC-BY-SA 3.0. Uso pessoal, nao publicar (D31/D33: nada de marca de terceiros em texto publico).
Mudancas: layout em pe; barra de titulo refeita com o mesmo degrade, sem texto embutido (o titulo
e texto do tema); trilho, progresso e volume redimensionados para 116 px; fonte Myriad Pro (Adobe,
proprietaria) trocada por "NanoSans", convertida da Source Sans 3 (Adobe, SIL OFL 1.1; o nome
"Source" e reservado pela licenca, por isso o nome novo).

Uso:  python3 rockbox/tema/gera_nanoclone128.py      (sai em rockbox/tema/saida_nano e NanoClone128.zip)
"""
import os
import shutil
import zipfile
from PIL import Image

import ttf2fnt

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(AQUI, "nanoclone_original")
SAIDA = os.path.join(AQUI, "saida_nano", ".rockbox")
NOME = "NanoClone128"
MAG = (255, 0, 255)
W, H, BARRA_H = 128, 160, 18

FONTES = {"14-NanoSans-Semibold.fnt": ("SourceSans3.ttf", 14, 600),   # lista e titulos (18)
          "13-NanoSans-Regular.fnt": ("SourceSans3.ttf", 13, 400)}    # info e tempos (17)

CREDITO = """# NanoClone128: adaptacao para 128x160 do NanoClone de Billy Blair (CC-BY-SA 3.0).
# Adaptado pelo OpenPod (CC-BY-SA 3.0). Fonte NanoSans: da Source Sans 3 (Adobe, SIL OFL 1.1).
"""


def abre(n):
    return Image.open(os.path.join(ORIG, n)).convert("RGB")


def tres_partes(im, largura, borda=4):
    """Estica na horizontal mantendo as pontas (trilho, progresso, volume)."""
    h = im.height
    meio = im.crop((borda, 0, im.width - borda, h)).resize((largura - 2 * borda, h), Image.LANCZOS)
    out = Image.new("RGB", (largura, h))
    out.paste(im.crop((0, 0, borda, h)), (0, 0))
    out.paste(meio, (borda, 0))
    out.paste(im.crop((im.width - borda, 0, im.width, h)), (largura - borda, 0))
    return out


def fundo(com_trilho):
    """Barra com o degrade original (coluna x=2, sem o texto) + corpo branco; trilho opcional."""
    src = abre("NanoClone.bmp")
    out = Image.new("RGB", (W, H), (255, 255, 255))
    for y in range(BARRA_H):
        cor = src.getpixel((2, y))
        for x in range(W):
            out.putpixel((x, y), cor)
    if com_trilho:
        bg = abre("bg-176x132x16.bmp")
        trilho = tres_partes(bg.crop((6, 100, 170, 111)), 116)
        out.paste(trilho, (6, 124))
    return out


SBS = CREDITO + """%wd
%X(fundo.bmp)
%Fl(2,14-NanoSans-Semibold.fnt,48)
%xl(D,battery.bmp,0,0,10)
%xl(G,playbtns.bmp,0,0,5)
%xl(F,hold.bmp,0,0)
%V(4,2,15,13,-)
%?mh<%xd(F)|%?mp<%xd(Ga)|%xd(Gb)|%xd(Gc)|%xd(Gd)|%xd(Ge)>>
%V(22,0,82,18,2)%Vf(000000)
%acOpenPod
%V(105,2,21,13,-)
%?bp<%?bc<%xd(Da)|%xd(Db)>|%?bl<|%xd(Dc)|%xd(Dd)|%xd(De)|%xd(Df)|%xd(Dg)|%xd(Dh)|%xd(Di)|%xd(Dj)>>
%Vi(-,0,19,128,141,1)
"""

WPS = CREDITO + """%wd
%X(fundo_wps.bmp)
%Fl(2,14-NanoSans-Semibold.fnt,48)
%Fl(3,13-NanoSans-Regular.fnt,72)
%xl(D,battery.bmp,0,0,10)
%xl(G,playbtns.bmp,0,0,5)
%xl(I,shuffle.bmp,0,0)
%xl(H,repeat.bmp,0,0,4)
%xl(F,hold.bmp,0,0)
%?C<%Vd(a)|%Vd(b)>
%?mv(2.0)<%Vd(f)|%Vd(d)>
%V(4,2,15,13,-)
%?mh<%xd(F)|%?mp<%xd(Ga)|%xd(Gb)|%xd(Gc)|%xd(Gd)|%xd(Ge)>>
%V(22,0,82,18,2)%Vf(000000)
%acTocando
%V(105,2,21,13,-)
%?bp<%?bc<%xd(Da)|%xd(Db)>|%?bl<|%xd(Dc)|%xd(Dd)|%xd(De)|%xd(Df)|%xd(Dg)|%xd(Dh)|%xd(Di)|%xd(Dj)>>
%V(5,20,80,17,3)%Vf(000000)%Vb(FFFFFF)
%al%pp de %pe
%V(90,22,16,12,-)%Vb(FFFFFF)
%?mm<|%xd(Ha)|%xd(Hb)|%t(1.0)%xd(Hc);%t(1.0)%xd(Ha)|%xd(Hd)>
%V(108,22,16,12,-)%Vb(FFFFFF)
%?ps<%xd(I)>
%Vl(a,40,36,48,48,-)%Vb(FFFFFF)
%Cl(0,0,48,48,c,c)
%Cd
%Vl(a,4,86,120,36,2)%Vf(000000)%Vb(FFFFFF)
%ac%s%?it<%it|%fn>
%ac%s%?ia<%ia|%?iA<%iA|>>
%Vl(b,4,44,120,72,2)%Vf(000000)%Vb(FFFFFF)
%ac%s%?it<%it|%fn>
%Vf(000000)%ac%s%?ia<%ia|%?iA<%iA|>>
%ac%s%?id<%id|>
%ac%s%?iy<%iy|>
%Vl(d,6,124,116,11,-)%Vb(FFFFFF)
%pb(0,0,116,11,progresso.bmp)
%Vl(f,6,124,116,11,-)%Vb(FFFFFF)
%pv(0,0,116,11,volume.bmp)
%V(6,138,116,17,3)%Vf(000000)%Vb(FFFFFF)
%?mv(2.0)<%ac%pv dB|%al%pc%ar-%pr>
"""

CFG = f"""# NanoClone128 - adaptado do NanoClone de Billy Blair (CC-BY-SA 3.0) para 128x160.
wps: /.rockbox/wps/{NOME}.wps
sbs: /.rockbox/wps/{NOME}.sbs
font: /.rockbox/fonts/14-NanoSans-Semibold.fnt
filetype colours: -
ui viewport: -
statusbar: off
show icons: off
scrollbar: off
line selector text color: FFFFFF
line selector start color: 639CE3
line selector end color: 2866DD
selector type: bar (gradient)
foreground color: 000000
background color: FFFFFF
"""


def main():
    if os.path.isdir(os.path.dirname(SAIDA)):
        shutil.rmtree(os.path.dirname(SAIDA))
    bmp = os.path.join(SAIDA, "wps", NOME)
    for p in ("themes", "fonts", bmp):
        os.makedirs(os.path.join(SAIDA, p), exist_ok=True)
    open(os.path.join(SAIDA, "themes", NOME + ".cfg"), "w").write(CFG)
    open(os.path.join(SAIDA, "wps", NOME + ".sbs"), "w").write(SBS)
    open(os.path.join(SAIDA, "wps", NOME + ".wps"), "w").write(WPS)
    fundo(False).save(os.path.join(bmp, "fundo.bmp"))
    fundo(True).save(os.path.join(bmp, "fundo_wps.bmp"))
    tres_partes(abre("progress.bmp"), 116).save(os.path.join(bmp, "progresso.bmp"))
    tres_partes(abre("volume.bmp"), 116).save(os.path.join(bmp, "volume.bmp"))
    for n in ("battery.bmp", "playbtns.bmp", "shuffle.bmp", "repeat.bmp", "hold.bmp"):
        shutil.copy(os.path.join(ORIG, n), os.path.join(bmp, n))
    for nome, (ttf, px, peso) in FONTES.items():
        ttf2fnt.converte(os.path.join(AQUI, "fontes", ttf), px, peso, 14, os.path.join(SAIDA, "fonts", nome))
    shutil.copy(os.path.join(AQUI, "fontes", "SourceSans3-OFL.txt"),
                os.path.join(SAIDA, "fonts", "NanoSans-OFL.txt"))
    zp = os.path.join(AQUI, NOME + ".zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for raiz, _, arqs in os.walk(SAIDA):
            for a in sorted(arqs):
                p = os.path.join(raiz, a)
                z.write(p, os.path.relpath(p, os.path.dirname(SAIDA)))
    print("ok:", zp)


if __name__ == "__main__":
    main()
