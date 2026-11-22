"""Previa da Reload 3.5 como vai sair: icones reais da imagem 3.5, cartao so com o nome da musica."""
import sys
from PIL import Image, ImageDraw, ImageFont
IMG, OUT = sys.argv[1], sys.argv[2]
b = open(IMG, "rb").read()
pal = b[0x0CDD5C:0x0CDD5C + 1024]; px = b[0x0CE15C:0x0CE15C + 128 * 160]
folha = Image.new("RGB", (128, 160)); folha.putdata([(pal[i*4+2], pal[i*4+1], pal[i*4]) for i in px])
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
def f(p, w=0): return ImageFont.truetype(HN, p, index=1 if w else 0)
MOLD = [(5, 17), (46, 17), (87, 17), (5, 58), (46, 58), (87, 58), (5, 97), (46, 97), (87, 97)]

def tela(nome, sel=1):
    im = folha.copy(); d = ImageDraw.Draw(im)
    for y in range(16):                                   # barra de cima (degrade escuro)
        c = 34 - y; d.line((0, y, 127, y), fill=(c, c + 2, c + 8))
    d.text((3, 2), "07:45", font=f(11), fill="white")
    d.text((64, 2), "OpenPod", font=f(11), fill="white", anchor="ma")
    d.rectangle((106, 4, 121, 11), outline="white"); d.rectangle((108, 6, 119, 9), fill="white"); d.rectangle((122, 6, 123, 9), fill="white")
    x, y = MOLD[sel]; d.rounded_rectangle((x, y, x + 36, y + 36), 6, outline="white", width=2)   # moldura
    d.rounded_rectangle((8, 136, 119, 157), 4, fill=(26, 26, 28))                                  # cartao 112x22
    verde = (80, 200, 90) if nome else (120, 120, 128)
    d.ellipse((12, 147, 18, 152), fill=verde); d.rectangle((16, 140, 17, 150), fill=verde); d.rectangle((16, 140, 21, 141), fill=verde)
    txt = nome or "Nada tocando"
    fonte = f(10, 1)
    while d.textlength(txt, font=fonte) > 92 and len(txt) > 2:
        txt = txt[:-2] + "…" if not txt.endswith("…") else txt[:-2] + "…"
    d.text((26, 141), txt, font=fonte, fill="white" if nome else (150, 150, 158))
    return im

telas = [("Tocando · nome curto", tela("Beatriz")), ("Tocando · nome longo", tela("Pra Não Esquecer De Mim (Ao Vivo)")),
         ("Sem música", tela(None, 0))]
out = Image.new("RGB", (3 * (384 + 40) + 20, 480 + 90), (245, 246, 248)); d = ImageDraw.Draw(out)
for i, (leg, t) in enumerate(telas):
    x = 20 + i * 424
    d.rounded_rectangle((x - 10, 10, x + 394, 500), 24, fill=(40, 40, 44))
    out.paste(t.resize((384, 480), Image.NEAREST), (x, 15))
    d.text((x + 192, 515), leg, font=f(22, 1), fill=(20, 20, 24), anchor="ma")
d.text((20, 548), "OpenPod Reload 3.5 · prévia (ícones reais da imagem; barra e textos aproximados)", font=f(15), fill=(110, 110, 118))
out.save(OUT); print("ok", OUT)
