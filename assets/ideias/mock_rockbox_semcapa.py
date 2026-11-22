"""Previa do OpenPod RockBox (tema OpenPod128 v6) SEM capa: bitmaps reais do tema + fonte Inter.
Uso: python3 mock_rockbox_semcapa.py <saida_tema/.rockbox> <Inter.ttf> <out.png> [<tela_menu.png>]"""
import sys
from PIL import Image, ImageDraw, ImageFont

RB, TTF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W = RB + "/wps/OpenPod128/"


def inter(px, peso):
    f = ImageFont.truetype(TTF, px)
    f.set_variation_by_axes([14, peso])
    return f


F12, F13B, F10 = inter(12, 500), inter(13, 700), inter(10, 500)
BAR, CARD, CINZA, TRILHO = (0x16, 0x18, 0x1E), (0x1E, 0x1E, 0x22), (0xAA, 0xAA, 0xB0), (0x6A, 0x6A, 0x72)
MAG = (255, 0, 255)


def bmp(nome):
    return Image.open(W + nome).convert("RGB")


def cola(im, src, x, y):
    m = Image.new("L", src.size, 0)
    m.putdata([0 if p == MAG else 255 for p in src.getdata()])
    im.paste(src, (x, y), m)


def quadro(nome, k, h):
    s = bmp(nome)
    return s.crop((0, k * h, s.width, (k + 1) * h))


ICONES = Image.open(RB + "/icons/OpenPod128.bmp").convert("RGB")


def icone(n):
    return ICONES.crop((0, n * 14, 14, n * 14 + 14))


def barra(im, d):
    d.rectangle((0, 0, 127, 17), fill=BAR)
    d.text((2, 2), "07:45", font=F10, fill="white")
    d.text((69, 0), "OpenPod", font=F13B, fill="white", anchor="ma")
    cola(im, quadro("bateria.bmp", 5, 8), 108, 5)


def cartao(im, d, titulo, artista):
    im.paste(bmp("cartao_esq.bmp"), (3, 121))
    d.rectangle((39, 121, 112, 158), fill=CARD)
    im.paste(bmp("cartao_dir.bmp"), (113, 121))
    im.paste(bmp("nota28.bmp"), (7, 126))
    d.text((39, 122), titulo, font=F13B, fill="white")
    cola(im, quadro("play.bmp", 0, 9), 114, 127)
    d.text((39, 139), artista, font=F10, fill=CINZA)
    d.rectangle((39, 154, 112, 156), fill=TRILHO)
    d.rectangle((39, 154, 62, 156), fill="white")


MENU = [(29, "Arquivos"), (0, "Banco de dados"), (25, "Tocando agora"), (20, "Configurações"),
        (21, "Gravação"), (28, "Rádio FM"), (2, "Listas"), (9, "Plugins")]


def menu(tocando, sel=2):
    im = Image.new("RGB", (128, 160), (0, 0, 0)); d = ImageDraw.Draw(im)
    barra(im, d)
    linhas = 5 if tocando else 7
    for i, (ic, txt) in enumerate(MENU[:linhas]):
        y = 19 + i * 19
        if i == sel:
            cola(im, bmp("moldura.bmp"), 1, y)
        im.paste(icone(ic), (6, y + 3))
        d.text((24, y + 1), txt, font=F12, fill="white")
    if tocando:
        cartao(im, d, "Beatriz", "2ZDinizz")
    return im


def tocando():
    im = Image.new("RGB", (128, 160), (0, 0, 0)); d = ImageDraw.Draw(im)
    barra(im, d)
    im.paste(bmp("nota80.bmp"), (24, 22))
    d.text((64, 104), "Pra Não Esquecer…", font=F13B, fill="white", anchor="ma")
    d.text((64, 121), "DJ Glenner", font=F10, fill=CINZA, anchor="ma")
    d.rectangle((8, 139, 119, 143), fill=TRILHO); d.rectangle((8, 139, 36, 143), fill="white")
    d.text((8, 145), "0:38", font=F10, fill=CINZA)
    cola(im, quadro("play.bmp", 1, 9), 60, 148)
    d.text((119, 145), "-2:21", font=F10, fill=CINZA, anchor="ra")
    return im


telas = [("Menu · tocando", menu(True)), ("Tocando agora", tocando()), ("Menu · sem música", menu(False, 0))]
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
out = Image.new("RGB", (3 * 424 + 20, 570), (245, 246, 248)); d = ImageDraw.Draw(out)
for i, (leg, t) in enumerate(telas):
    x = 20 + i * 424
    d.rounded_rectangle((x - 10, 10, x + 394, 500), 24, fill=(40, 40, 44))
    out.paste(t.resize((384, 480), Image.NEAREST), (x, 15))
    d.text((x + 192, 515), leg, font=ImageFont.truetype(HN, 22, index=1), fill=(20, 20, 24), anchor="ma")
d.text((20, 548), "OpenPod RockBox · tema OpenPod128 · sem capa (a nota no lugar) · prévia com os desenhos reais do tema",
       font=ImageFont.truetype(HN, 15), fill=(110, 110, 118))
out.save(OUT)
if len(sys.argv) > 4:
    menu(True).resize((384, 480), Image.NEAREST).save(sys.argv[4])
print("ok", OUT)
