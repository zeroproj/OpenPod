"""Comparacao: OpenPod 3.5 (fabrica) x Rockbox padrao x Rockbox + tema OpenPod.
Ilustracao (nao e captura). Icones reais tirados da folha INDEXED_8 da imagem 3.5."""
import sys
from PIL import Image, ImageDraw, ImageFont

IMG35, MOCK35, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
X = 0xC00000
S = 3                                   # escala: 128x160 -> 384x480
F = "/System/Library/Fonts/HelveticaNeue.ttc"
def font(px, bold=False):
    return ImageFont.truetype(F, px, index=1 if bold else 0)

# ---- icones reais da folha (paleta BGRA em 0x0CDD5C, pixels em 0x0CE15C)
b = open(IMG35, "rb").read()
pal = b[0x0CDD5C:0x0CDD5C + 1024]
px = b[0x0CE15C:0x0CE15C + 128 * 160]
sheet = Image.new("RGBA", (128, 160))
sheet.putdata([(pal[i*4+2], pal[i*4+1], pal[i*4], pal[i*4+3]) for i in px])
COLS, ROWS = (5, 46, 87), (17, 58, 97)
def icone(r, c, tam):
    x, y = COLS[c] + 2, ROWS[r] + 2
    return sheet.crop((x, y, x + 32, y + 32)).resize((tam, tam), Image.LANCZOS)
# ordem da grade: musica video gravador / fm livro apps / bt config arquivos
ICO = {"musica": (0, 0), "video": (0, 1), "grav": (0, 2), "fm": (1, 0), "livro": (1, 1),
       "apps": (1, 2), "bt": (2, 0), "config": (2, 1), "arq": (2, 2)}

W, H = 384, 480
def moldura(tela):
    fr = Image.new("RGB", (420, 520), (245, 246, 248))
    d = ImageDraw.Draw(fr)
    d.rounded_rectangle((0, 0, 419, 519), 28, fill=(40, 40, 44))
    fr.paste(tela, (18, 20))
    return fr

def barra_openpod(d):
    d.rectangle((0, 0, W, 45), fill=(22, 24, 30))
    d.text((10, 6), "07:45", font=font(28), fill="white")
    d.text((W // 2, 6), "OpenPod", font=font(28), fill="white", anchor="ma")
    d.rounded_rectangle((328, 13, 368, 33), 3, outline="white", width=3)
    d.rectangle((333, 18, 363, 28), fill="white"); d.rectangle((369, 19, 373, 27), fill="white")

def cartao(img, d, y):
    d.rounded_rectangle((8, y, W - 8, y + 104), 14, fill=(30, 30, 34))
    capa = Image.new("RGB", (76, 76)); cd = ImageDraw.Draw(capa)
    for i in range(76):
        cd.line((0, i, 76, i), fill=(110 + i, 40, 160 - i))
    cd.ellipse((12, 12, 64, 64), fill=(240, 170, 50)); cd.ellipse((32, 32, 44, 44), fill=(40, 20, 60))
    img.paste(capa, (20, y + 14))
    d.text((108, y + 14), "Nome da Música", font=font(24, True), fill="white")
    d.polygon([(W - 36, y + 18), (W - 36, y + 40), (W - 18, y + 29)], fill=(90, 200, 90))
    d.text((108, y + 46), "Artista", font=font(20), fill=(170, 170, 175))
    d.text((W - 18, y + 46), "-2:28", font=font(20), fill=(200, 200, 205), anchor="ra")
    d.rounded_rectangle((108, y + 80, W - 18, y + 86), 3, fill=(70, 70, 76))
    d.rounded_rectangle((108, y + 80, 200, y + 86), 3, fill="white")

def rockbox_padrao():
    img = Image.new("RGB", (W, H), (236, 238, 242)); d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 30), fill=(60, 64, 72))
    d.text((8, 3), "07:45", font=font(22), fill="white")
    d.rounded_rectangle((330, 7, 366, 23), 2, outline="white", width=2)
    d.rectangle((334, 11, 356, 19), fill="white")
    itens = ["Arquivos", "Banco de dados", "Tocando agora", "Configurações", "Gravação",
             "Rádio FM", "Listas de reprodução", "Plugins", "Sistema", "Atalhos"]
    y = 38
    for i, t in enumerate(itens):
        if i == 0:
            d.rectangle((0, y - 2, W, y + 38), fill=(60, 110, 200))
        d.rectangle((12, y + 8, 32, y + 28), outline=(90, 90, 100) if i else "white", width=2)
        d.text((44, y + 4), t, font=font(26), fill="white" if i == 0 else (20, 20, 24))
        y += 44
    return img

def rockbox_openpod():
    img = Image.new("RGB", (W, H), "black"); d = ImageDraw.Draw(img)
    barra_openpod(d)
    itens = [("musica", "Música"), ("video", "Tocando agora"), ("arq", "Arquivos"),
             ("fm", "Rádio FM"), ("grav", "Gravação"), ("apps", "Plugins e jogos"),
             ("bt", "Bluetooth"), ("config", "Configurações")]
    y = 52
    for i, (k, t) in enumerate(itens):
        if i == 0:
            d.rounded_rectangle((6, y - 2, W - 6, y + 36), 8, outline="white", width=3)
        img.paste(icone(*ICO[k], 30), (14, y + 2), icone(*ICO[k], 30))
        d.text((56, y + 4), t, font=font(25, i == 0), fill="white")
        y += 37
    cartao(img, d, H - 116)
    return img

# painel 1: o modelo da 3.5 ja aprovado (o celular do meio do PNG)
p1 = Image.open(MOCK35).convert("RGB").crop((515, 30, 935, 550))
p2, p3 = moldura(rockbox_padrao()), moldura(rockbox_openpod())

out = Image.new("RGB", (1460, 650), (245, 246, 248)); d = ImageDraw.Draw(out)
legs = [("OpenPod 3.5", "Fábrica + player na tela inicial"),
        ("Rockbox · tema padrão", "Menu em lista, sem player na tela inicial"),
        ("Rockbox · tema OpenPod", "Nosso visual + player em todas as telas")]
for i, p in enumerate((p1, p2, p3)):
    x = 25 + i * 490
    out.paste(p, (x, 30))
    d.text((x + 210, 572), legs[i][0], font=font(26, True), fill=(20, 20, 24), anchor="ma")
    d.text((x + 210, 606), legs[i][1], font=font(19), fill=(110, 110, 118), anchor="ma")
out.save(OUT)
print("ok", OUT)
