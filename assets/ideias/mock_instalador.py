"""Modelo do Instalador OpenPod (ficha 029): 4 telas, visual claro e premium. Ilustracao."""
import sys
from PIL import Image, ImageDraw, ImageFont

LOGO, OUT = sys.argv[1], sys.argv[2]
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
def f(px, peso=0): return ImageFont.truetype(HN, px, index={0: 0, 1: 1, 2: 4}[peso])

W, H = 760, 500
FUNDO, CARTAO, TXT, SUB, AZUL, BORDA = (245, 245, 247), (255, 255, 255), (29, 29, 31), (110, 110, 115), (0, 113, 227), (220, 220, 224)
logo = Image.open(LOGO).convert("RGB")


def janela(titulo):
    im = Image.new("RGB", (W, H), FUNDO); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 38), fill=(236, 236, 238))
    for i, c in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
        d.ellipse((14 + i * 20, 13, 26 + i * 20, 25), fill=c)
    d.text((W // 2, 12), "Instalador OpenPod", font=f(13, 1), fill=SUB, anchor="ma")
    # marca: o fone do logo em um quadrado escuro arredondado + nome
    m = Image.new("RGB", (34, 34), (0, 0, 0)); m.paste(logo.crop((2, 4, 30, 31)).resize((26, 26)), (4, 4))
    mask = Image.new("L", (34, 34), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 33, 33), 8, fill=255)
    im.paste(m, (32, 58), mask)
    d.text((76, 64), "OpenPod", font=f(17, 2), fill=TXT)
    d.text((32, 110), titulo, font=f(28, 2), fill=TXT)
    d.text((32, H - 30), "zeroproj.github.io/OpenPod", font=f(12), fill=AZUL)
    return im, d


def botao(d, x, y, w, txt, primario=True):
    d.rounded_rectangle((x, y, x + w, y + 38), 19, fill=AZUL if primario else (232, 232, 237))
    d.text((x + w // 2, y + 10), txt, font=f(15, 1), fill="white" if primario else AZUL, anchor="ma")


def tela1():
    im, d = janela("Escolha o sistema")
    d.text((32, 146), "Os dois funcionam no seu player. Você pode trocar quando quiser.", font=f(14), fill=SUB)
    for i, (t, s1, s2, sel) in enumerate((
            ("OpenPod System", "O sistema de fábrica, melhorado.", "Rádio, gravador, vídeo, Bluetooth.", True),
            ("OpenPod RockBox", "Rockbox com o tema OpenPod.", "Mais formatos, plugins e jogos.", False))):
        x = 32 + i * 352
        d.rounded_rectangle((x, 180, x + 336, 300), 16, fill=CARTAO, outline=AZUL if sel else BORDA, width=3 if sel else 1)
        d.ellipse((x + 300, 196, x + 320, 216), outline=AZUL if sel else BORDA, width=2)
        if sel: d.ellipse((x + 305, 201, x + 315, 211), fill=AZUL)
        d.text((x + 20, 196), t, font=f(19, 2), fill=TXT)
        d.text((x + 20, 228), s1, font=f(14), fill=TXT)
        d.text((x + 20, 250), s2, font=f(14), fill=SUB)
        d.text((x + 20, 274), "Reload 3.5 · 10/12/2026" if i == 0 else "Rockbox YP3 · 22/11/2026", font=f(12), fill=SUB)
    d.rounded_rectangle((32, 318, 728, 360), 12, fill=CARTAO, outline=BORDA)
    d.ellipse((48, 331, 62, 345), fill=AZUL); d.text((72, 330), "Versão mais nova do site", font=f(14, 1), fill=TXT)
    d.text((300, 330), "ou", font=f(14), fill=SUB); d.text((326, 330), "Escolher arquivo…", font=f(14, 1), fill=AZUL)
    botao(d, 568, 420, 160, "Continuar")
    d.text((32, 432), "Restaurar o original", font=f(13, 1), fill=AZUL)
    return im


def tela2():
    im, d = janela("Conecte o player")
    d.rounded_rectangle((32, 160, 300, 400), 18, fill=CARTAO, outline=BORDA)
    d.rounded_rectangle((126, 190, 206, 370), 14, fill=(40, 40, 44))      # player
    d.rounded_rectangle((134, 200, 198, 262), 4, fill=(10, 10, 12))
    d.ellipse((140, 282, 192, 334), fill=(60, 60, 64)); d.ellipse((156, 298, 176, 318), fill=(40, 40, 44))
    d.polygon([(160, 336), (172, 336), (166, 346)], fill=AZUL)           # baixo
    d.line((166, 370, 166, 392), fill=(120, 120, 125), width=4)           # cabo
    passos = ["Desligue o player.", "Segure o botão de baixo (⏯).", "Ligue o cabo USB e solte o botão."]
    for i, p in enumerate(passos):
        y = 176 + i * 52
        d.ellipse((330, y, 358, y + 28), fill=AZUL); d.text((344, y + 5), str(i + 1), font=f(15, 2), fill="white", anchor="ma")
        d.text((372, y + 4), p, font=f(16), fill=TXT)
    d.rounded_rectangle((330, 340, 728, 384), 22, fill=(232, 245, 236))
    d.ellipse((346, 356, 358, 368), fill=(40, 180, 80))
    d.text((368, 352), "Player encontrado · bateria 82%", font=f(15, 1), fill=(20, 110, 50))
    botao(d, 568, 420, 160, "Instalar")
    return im


def tela3():
    im, d = janela("Instalando o OpenPod RockBox")
    d.text((32, 146), "Não desconecte o cabo. Leva cerca de 2 minutos.", font=f(14), fill=SUB)
    d.rounded_rectangle((32, 180, 728, 390), 18, fill=CARTAO, outline=BORDA)
    etapas = [("Cópia de segurança da flash", 1), ("Conferência do aparelho", 1), ("Gravação", 0.62), ("Arquivos do cartão", 0)]
    for i, (t, v) in enumerate(etapas):
        y = 200 + i * 46
        if v == 1:
            d.ellipse((52, y, 74, y + 22), fill=(40, 180, 80)); d.text((63, y + 3), "✓", font=f(14, 2), fill="white", anchor="ma")
        elif v > 0:
            d.ellipse((52, y, 74, y + 22), outline=AZUL, width=3)
        else:
            d.ellipse((52, y, 74, y + 22), outline=BORDA, width=2)
        d.text((88, y + 2), t, font=f(16, 1 if 0 < v < 1 else 0), fill=TXT if v else SUB)
        if 0 < v < 1:
            d.rounded_rectangle((420, y + 7, 690, y + 15), 4, fill=(232, 232, 237))
            d.rounded_rectangle((420, y + 7, 420 + int(270 * v), y + 15), 4, fill=AZUL)
            d.text((700, y + 2), "62%", font=f(13), fill=SUB)
    return im


def tela4():
    im, d = janela("Pronto")
    d.ellipse((330, 170, 430, 270), fill=(40, 180, 80))
    d.line((355, 222, 374, 241), fill="white", width=9); d.line((374, 241, 408, 200), fill="white", width=9)
    d.text((380, 292), "O OpenPod RockBox está instalado.", font=f(20, 2), fill=TXT, anchor="ma")
    d.text((380, 324), "Desconecte o cabo. O tema OpenPod já vem escolhido.", font=f(14), fill=SUB, anchor="ma")
    d.text((380, 346), "A cópia de segurança ficou em Documentos/OpenPod.", font=f(14), fill=SUB, anchor="ma")
    botao(d, 300, 400, 160, "Concluir")
    return im


telas = [tela1(), tela2(), tela3(), tela4()]
out = Image.new("RGB", (W * 2 + 60, H * 2 + 60), (210, 210, 215))
for i, t in enumerate(telas):
    out.paste(t, (20 + (i % 2) * (W + 20), 20 + (i // 2) * (H + 20)))
out.save(OUT)
print("ok", OUT)
