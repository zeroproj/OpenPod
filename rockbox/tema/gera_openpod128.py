#!/usr/bin/env python3
"""gera_openpod128.py - o tema OpenPod128 para o Rockbox YP3 (128x160), linha Rockbox (D33).

Gera, em rockbox/tema/saida/.rockbox/:
  themes/OpenPod128.cfg          o tema (escolher em Configuracoes > Tema)
  wps/OpenPod128.sbs             barra base: barra do OpenPod, lista com os nossos icones,
                                 cartao do player embaixo enquanto toca (em TODAS as telas)
  wps/OpenPod128.wps             tela Tocando agora: capa grande, nome, artista, barra, tempos
  wps/OpenPod128/*.bmp           bateria, play/pausa, cartao, moldura, nota
  icons/OpenPod128.bmp           os icones da lista (32 x 14x14, ordem do enum themable_icons)

Tudo desenhado por nos (icones do assets/IconesHome_escuro_colorido_apps.png). Fontes: as que o
pacote do Rockbox YP3 ja traz no cartao (Cantarell, SIL OFL 1.1); nenhuma fonte vai no tema.
O formato dos .sbs/.wps segue a documentacao de temas do Rockbox. Nenhum codigo de terceiros.

Uso:  python3 rockbox/tema/gera_openpod128.py      (sai em rockbox/tema/saida e OpenPod128.zip)
"""
import os
import shutil
import zipfile
from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
SAIDA = os.path.join(AQUI, "saida", ".rockbox")
NOME = "OpenPod128"
MAG = (255, 0, 255)                      # transparente nos bitmaps de cor do Rockbox

BAR = "16181E"                           # a barra de cima do OpenPod
CARD = (30, 30, 34)
CARD_HEX = "1E1E22"
CINZA_HEX = "AAAAB0"
TRILHO_HEX = "46464C"

# ------------------------------------------------------------------ icones
FOLHA = Image.open(os.path.join(RAIZ, "assets", "IconesHome_escuro_colorido_apps.png")).convert("RGB")
COLS, ROWS = (7, 48, 89), (16, 64, 112)  # cantos dos quadrados na folha (31x30), medidos
GRADE = {"musica": (0, 0), "video": (0, 1), "grav": (0, 2), "fm": (1, 0), "livro": (1, 1),
         "apps": (1, 2), "bt": (2, 0), "config": (2, 1), "pasta": (2, 2)}


def nosso(nome, tam=14):
    r, c = GRADE[nome]
    x, y = COLS[c], ROWS[r]
    return FOLHA.crop((x, y, x + 31, y + 31)).resize((tam, tam), Image.LANCZOS)


def glifo(desenho, cor=(200, 200, 210)):
    """Icone simples 14x14 no mesmo estilo: quadrado escuro arredondado + simbolo."""
    im = Image.new("RGB", (14, 14), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 13, 13), 3, fill=(44, 44, 48))
    desenho(d, cor)
    return im


def seta(d, c):   d.polygon([(5, 3), (10, 7), (5, 11)], fill=c)
def lista(d, c):  [d.line((3, y, 10, y), fill=c) for y in (4, 7, 10)]
def letra(t):
    return lambda d, c: d.text((4, 1), t, fill=c)
def eq(d, c):     [d.line((x, 11, x, h), fill=c, width=2) for x, h in ((3, 6), (7, 3), (11, 8))]
def tela(d, c):   d.rectangle((3, 3, 10, 9), outline=c); d.line((5, 11, 8, 11), fill=c)
def ponto(d, c):  d.ellipse((5, 5, 8, 8), fill=c)
def teclas(d, c): [d.rectangle((x, y, x + 1, y + 1), fill=c) for x in (3, 6, 9) for y in (4, 8)]
def setas(d, c):  d.line((3, 5, 10, 5), fill=c); d.line((3, 9, 10, 9), fill=c)

# ordem do enum themable_icons (apps/gui/icon.h): 32 icones
ICONES = [
    nosso("musica"),            # Audio            (Banco de dados / Musica)
    nosso("pasta"),             # Folder
    glifo(lista),               # Playlist
    glifo(seta, (255, 255, 255)),  # Cursor
    nosso("video"),             # Wps
    glifo(tela),                # Firmware
    glifo(letra("A")),          # Font
    glifo(letra("Aa")),         # Language
    nosso("config"),            # Config
    nosso("apps"),              # Plugin
    nosso("livro"),             # Bookmark (Atalhos, Favoritos)
    nosso("fm"),                # Preset
    glifo(seta, (90, 200, 90)),  # Queued
    glifo(setas),               # Moving
    glifo(teclas),              # Keyboard
    glifo(seta, (255, 255, 255)),  # Reverse_Cursor
    glifo(letra("?")),          # Questionmark
    glifo(ponto),               # Menu_setting
    glifo(ponto),               # Menu_functioncall
    glifo(seta),                # Submenu
    nosso("config"),            # Submenu_Entered  (Configuracoes no menu inicial)
    nosso("grav"),              # Recording
    nosso("grav"),              # Voice
    nosso("config"),            # General_settings_menu
    glifo(letra("i")),          # System_menu
    nosso("video"),             # Playback_menu    (Tocando agora)
    glifo(tela),                # Display_menu
    glifo(tela),                # Remote_Display_menu
    nosso("fm"),                # Radio_screen
    nosso("pasta"),             # file_view_menu   (Arquivos)
    glifo(eq),                  # EQ
    nosso("musica"),            # Rockbox
]
assert len(ICONES) == 32


def faixa(imgs):
    w = imgs[0].width
    out = Image.new("RGB", (w, sum(i.height for i in imgs)), MAG)
    y = 0
    for i in imgs:
        out.paste(i, (0, y))
        y += i.height
    return out


# ------------------------------------------------------------------ bitmaps do skin
def bateria():
    quadros = []
    for nivel in range(7):               # 0..5 vazia -> cheia; 6 carregando (igual ao padrao)
        im = Image.new("RGB", (16, 8), MAG)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 13, 7), outline=(255, 255, 255))
        d.rectangle((14, 2, 15, 5), fill=(255, 255, 255))
        if nivel < 6:
            w = round(10 * nivel / 5)
            if w:
                d.rectangle((2, 2, 1 + w, 5), fill=(255, 255, 255) if nivel > 1 else (230, 80, 70))
        else:
            d.polygon([(8, 1), (4, 4), (7, 4), (5, 7), (10, 3), (7, 3)], fill=(90, 200, 90))
        quadros.append(im)
    return faixa(quadros)


def play():
    quadros = []
    verde = (90, 200, 90)
    for k in range(5):                   # play, pausa, play, avanca, volta
        im = Image.new("RGB", (9, 9), MAG)
        d = ImageDraw.Draw(im)
        if k in (0, 2):
            d.polygon([(1, 0), (1, 8), (8, 4)], fill=verde)
        elif k == 1:
            d.rectangle((1, 0, 3, 8), fill=(255, 255, 255)); d.rectangle((5, 0, 7, 8), fill=(255, 255, 255))
        elif k == 3:
            d.polygon([(0, 0), (0, 8), (4, 4)], fill=verde); d.polygon([(4, 0), (4, 8), (8, 4)], fill=verde)
        else:
            d.polygon([(8, 0), (8, 8), (4, 4)], fill=verde); d.polygon([(4, 0), (4, 8), (0, 4)], fill=verde)
        quadros.append(im)
    return faixa(quadros)


def retangulo(w, h, r, fill=None, outline=None, larg=1):
    im = Image.new("RGB", (w, h), MAG)
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill, outline=outline, width=larg)
    return im


def nota(tam):
    im = Image.new("RGB", (tam, tam), (44, 44, 48))
    d = ImageDraw.Draw(im)
    s = tam / 28
    c = (120, 120, 128)
    d.ellipse((7 * s, 16 * s, 14 * s, 22 * s), fill=c)
    d.rectangle((12 * s, 6 * s, 14 * s, 19 * s), fill=c)
    d.polygon([(12 * s, 6 * s), (21 * s, 9 * s), (21 * s, 12 * s), (14 * s, 9.5 * s)], fill=c)
    return im


# ------------------------------------------------------------------ skins
CABEC = """# OpenPod128 - tema do OpenPod para o Rockbox YP3 (128x160). Linha Rockbox (D33).
# Desenhos do OpenPod; fontes Cantarell (SIL OFL 1.1) que ja vem no cartao do Rockbox YP3.
"""

BARRA = f"""%V(0,0,128,16,-)%Vb({BAR})
%V(3,1,36,14,2)%Vf(FFFFFF)%Vb({BAR})
%cH:%cM
%V(38,1,52,14,2)%Vf(FFFFFF)%Vb({BAR})
%acOpenPod
%V(108,4,16,8,-)%Vb({BAR})
%?bc<%xd(B,7)|%xd(B,%bl,-1)>
"""

SBS = CABEC + f"""# Barra base: aparece nos menus. Lista com os nossos icones e, enquanto toca, o cartao do
# player embaixo (capa, nome, play/pausa, artista e barra), como a 3.5 da linha de fabrica.
%wd
%Fl(2,13-Cantarell-Bold-1bit.fnt,48)
%Fl(3,11-Cantarell-Regular-1bit.fnt,72)
%xl(B,bateria.bmp,0,0,7)
%xl(I,__list_icons__,0,0)
%xl(H,moldura.bmp,0,0)
%xl(K,cartao.bmp,0,0)
%xl(N,nota28.bmp,0,0)
%xl(P,play.bmp,0,0,5)
%Cl(0,0,28,28,c,c)
%Lb(item,128,17)
%?mp<%VI(cheia)|%VI(curta)>
%?mp<|%Vd(m)>
{BARRA}%Vi(cheia,0,17,128,143,1)
%Vi(curta,0,17,128,105,1)
%Vl(item,2,0,124,17,-)%Vb(000000)
%xd(H,%Lc)
%Vl(item,6,1,14,14,-)%Vb(000000)
%?if(%LI,=,-1)<|%xd(I,%LI,2)>
%Vl(item,24,1,100,14,1)%Vf(FFFFFF)%Vb(000000)
%s%LT
%Vl(m,3,123,122,35,-)%Vb(000000)
%xd(K)
%Vl(m,7,126,28,28,-)%Vb({CARD_HEX})
%?C<%Cd|%xd(N)>
%Vl(m,39,125,72,13,2)%Vf(FFFFFF)%Vb({CARD_HEX})
%s%?it<%it|%fn>
%Vl(m,113,127,9,9,-)%Vb({CARD_HEX})
%xd(P,%mp)
%Vl(m,39,138,82,11,3)%Vf({CINZA_HEX})%Vb({CARD_HEX})
%s%?ia<%ia|%?iA<%iA|>>
%Vl(m,39,151,80,3,-)%Vf(FFFFFF)%Vb({TRILHO_HEX})
%pb(0,0,80,3,noborder)
"""

WPS = CABEC + f"""# Tocando agora: a capa grande (ou a nota), nome, artista, barra e tempos, como na 2.0+.
%wd
%Fl(2,13-Cantarell-Bold-1bit.fnt,48)
%Fl(3,11-Cantarell-Regular-1bit.fnt,72)
%xl(B,bateria.bmp,0,0,7)
%xl(N,nota80.bmp,0,0)
%xl(P,play.bmp,0,0,5)
%Cl(0,0,80,80,c,c)
%V(0,0,128,160,-)%Vb(000000)
{BARRA}%V(24,21,80,80,-)%Vb(000000)
%?C<%Cd|%xd(N)>
%V(2,104,124,15,2)%Vf(FFFFFF)%Vb(000000)
%ac%s%?it<%it|%fn>
%V(2,119,124,13,3)%Vf({CINZA_HEX})%Vb(000000)
%ac%s%?ia<%ia|%?iA<%iA|>>
%V(8,136,112,4,-)%Vf(FFFFFF)%Vb({TRILHO_HEX})
%pb(0,0,112,4,noborder)
%V(8,143,40,13,3)%Vf({CINZA_HEX})%Vb(000000)
%pc
%V(60,145,9,9,-)%Vb(000000)
%xd(P,%mp)
%V(80,143,40,13,3)%Vf({CINZA_HEX})%Vb(000000)
%ar-%pr
"""

CFG = f"""# OpenPod128 - tema do OpenPod (linha Rockbox, D33). Configuracoes > Tema > OpenPod128.
wps: /.rockbox/wps/{NOME}.wps
sbs: /.rockbox/wps/{NOME}.sbs
font: /.rockbox/fonts/12-Cantarell-Regular-1bit.fnt
iconset: /.rockbox/icons/{NOME}.bmp
viewers iconset: -
statusbar: off
scrollbar: off
show icons: on
foreground color: FFFFFF
background color: 000000
selector type: bar (color)
line selector start color: 000000
line selector text color: FFFFFF
filetype colours: -
backdrop: -
ui viewport: -
"""


def main():
    if os.path.isdir(os.path.dirname(SAIDA)):
        shutil.rmtree(os.path.dirname(SAIDA))
    bmpdir = os.path.join(SAIDA, "wps", NOME)
    for p in ("themes", "icons", bmpdir):
        os.makedirs(os.path.join(SAIDA, p), exist_ok=True)
    open(os.path.join(SAIDA, "themes", NOME + ".cfg"), "w").write(CFG)
    open(os.path.join(SAIDA, "wps", NOME + ".sbs"), "w").write(SBS)
    open(os.path.join(SAIDA, "wps", NOME + ".wps"), "w").write(WPS)
    faixa(ICONES).save(os.path.join(SAIDA, "icons", NOME + ".bmp"))
    bateria().save(os.path.join(bmpdir, "bateria.bmp"))
    play().save(os.path.join(bmpdir, "play.bmp"))
    retangulo(122, 35, 6, fill=CARD).save(os.path.join(bmpdir, "cartao.bmp"))
    retangulo(124, 17, 4, outline=(255, 255, 255), larg=1).save(os.path.join(bmpdir, "moldura.bmp"))
    nota(28).save(os.path.join(bmpdir, "nota28.bmp"))
    nota(80).save(os.path.join(bmpdir, "nota80.bmp"))
    zp = os.path.join(AQUI, NOME + ".zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for raiz, _, arqs in os.walk(SAIDA):
            for a in sorted(arqs):
                p = os.path.join(raiz, a)
                z.write(p, os.path.relpath(p, os.path.dirname(SAIDA)))
    print("ok:", zp)


if __name__ == "__main__":
    main()
