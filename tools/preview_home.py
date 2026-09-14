#!/usr/bin/env python3
"""
preview_home.py — Renderiza, fora do aparelho, como a tela do menu principal
                  vai ficar depois de um patch de layout.

PROPOSITO
    O menu principal e montado a partir de dados: as coordenadas dos rotulos
    (0x000486A0), as coordenadas das areas de icone (0x0004867C), os ids de
    texto (0x000486C4) e a folha de imagem de 128x160 (pixels em 0x000CE15C).
    Todos esses dados estao DENTRO do firmware.

    Esta ferramenta le esses dados do proprio .bin e compoe a tela usando a
    FONTE DO PROPRIO FIRMWARE (tabela de glifos em 0x00086C44, cmap em
    0x000A27E6, bitmaps 1 bpp a partir de 0x0005E7E0).

    Serve para responder, antes de gravar, perguntas que so a tela responde:
      - o texto cabe na largura do rotulo, ou vai quebrar linha?
      - as linhas se sobrepoem?
      - o chevron colide com o texto?

    NAO substitui o teste no aparelho: nao simula a LVGL, so desenha o que
    os dados dizem. Ver docs/MENU_LISTA.md secao 18.

USO
    python3 tools/preview_home.py firmware/WORKING/GN438_openpod_v014.bin \
        --out analysis/preview/home_v014.png [--lang pt] [--scale 3]

    Sem --out, imprime a tela em ASCII no terminal.

DEPENDENCIAS
    Python 3. PIL (Pillow) apenas para --out; sem PIL, use a saida ASCII.

LIMITACOES
    - Assume text_align lido de 0x0012ED54 e largura lida de 0x0012ED5E.
    - Desenha o texto alinhado a esquerda ou centrado conforme esse byte;
      nao implementa os demais modos da LVGL.
    - Nao desenha a faixa de status (objeto separado, nao esta na folha).
    - A cor da selecao nao e simulada: todos os rotulos saem em branco.
"""

import argparse
import os
import struct
import sys

FONT_TABLE = 0x00086C44
FONT_CMAP = 0x000A27E6
FONT_BASE = 0x0005E7E0
FONT_N = 7098

TBL_ICON = 0x0004867C
TBL_LABEL = 0x000486A0
TBL_TEXT = 0x000486C4
OFF_ALIGN = 0x0012ED54
OFF_WIDTH = 0x0012ED5E

PIX_OFF = 0x000CE15C
PAL_OFF = 0x000CDD5C
IMG_W, IMG_H = 128, 160

LANGS = {"de": 0x52744, "zh": 0x523E4, "en": 0x52AA4, "fr": 0x52E04,
         "it": 0x534C4, "nl": 0x53824, "pt": 0x53B84, "es": 0x53EE4}


def read_dsc(d, i):
    o = FONT_TABLE + i * 16
    bmp, adv = struct.unpack_from("<2I", d, o)
    box_w, box_h = struct.unpack_from("<HH", d, o + 8)
    ofs_x, ofs_y = struct.unpack_from("<hh", d, o + 12)
    return dict(bmp=bmp, adv=adv, w=box_w, h=box_h, ox=ofs_x, oy=ofs_y)


def glyph_rows(d, g):
    stride = (g["w"] + 7) // 8
    out = []
    for y in range(g["h"]):
        line = []
        for x in range(g["w"]):
            b = d[FONT_BASE + g["bmp"] + y * stride + x // 8]
            line.append((b >> (7 - (x % 8))) & 1)
        out.append(line)
    return out


def string_at(d, ptr):
    o = ptr - 0x00C00000
    return d[o:d.index(b"\0", o)].decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser(description="Previa do menu principal")
    ap.add_argument("path")
    ap.add_argument("--lang", default="pt", choices=sorted(LANGS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--status", action="store_true",
                    help="desenha tambem o relogio e o titulo da faixa superior")
    args = ap.parse_args()

    with open(args.path, "rb") as fh:
        d = fh.read()

    cmap = struct.unpack_from("<%dH" % FONT_N, d, FONT_CMAP)
    gid = {c: i for i, c in enumerate(cmap)}

    # Na LVGL, ofs_y e medido a partir da LINHA DE BASE, nao do topo da
    # caixa. A ascendente e derivada do proprio firmware: o maior
    # (ofs_y + box_h) entre os glifos ASCII imprimiveis.
    # A faixa TEM de incluir os acentuados: á ã í ú sobem 1 px acima do
    # maior glifo ASCII. Calcular so com ASCII desenha o acento ACIMA da
    # caixa do rotulo -- ver docs/STATUS_BAR.md secao 13.
    _faixa = list(range(0x21, 0x7F)) + list(range(0xC0, 0x100))
    ascent = max(read_dsc(d, gid[c])["oy"] + read_dsc(d, gid[c])["h"]
                 for c in _faixa if c in gid)

    # quantos itens a home monta: o limite do laco de page_home_create
    n_itens = d[0x0012ED88] // 4
    icon_xy = [struct.unpack_from("<hh", d, TBL_ICON + i * 4)
               for i in range(n_itens)]
    lab_xy = [struct.unpack_from("<hh", d, TBL_LABEL + i * 4)
              for i in range(n_itens)]
    ids = [struct.unpack_from("<I", d, TBL_TEXT + i * 4)[0]
           for i in range(n_itens)]
    lab_w = d[OFF_WIDTH]
    align = d[OFF_ALIGN]

    # A base da tabela do idioma vem do POOL do get_string, nao de um
    # endereco fixo: desde o V021 a tabela do portugues foi realocada
    # para a area livre (docs/MENU_HIERARQUIA.md secao 11).
    base = LANGS[args.lang]
    if args.lang == "pt":
        base = struct.unpack_from("<I", d, 0x00121104)[0] - 0x00C00000
    textos = [string_at(d, struct.unpack_from("<I", d, base + i * 4)[0])
              for i in ids]

    # tela: 0 = fundo, 1 = pixel da folha, 2 = pixel de texto
    scr = [[0] * IMG_W for _ in range(IMG_H)]
    bg = d[PIX_OFF]
    for y in range(IMG_H):
        for x in range(IMG_W):
            if d[PIX_OFF + y * IMG_W + x] != bg:
                scr[y][x] = 1

    print(f"  fonte     : 0x{FONT_TABLE:06X} / cmap 0x{FONT_CMAP:06X}")
    print(f"  idioma    : {args.lang} (tabela 0x{base:06X})")
    print(f"  itens     : {n_itens} (do limite do laco em 0x0012ED88)")
    print(f"  rotulo    : largura {lab_w} px, "
          f"align {align} ({'esquerda' if align == 0 else 'centro' if align == 2 else '?'})")
    print()
    print(f"  {'#':>2}  {'texto':<16}{'px':>4}  {'rotulo':<12}{'icone':<12}estouro")
    estouros = 0
    for i, t in enumerate(textos):
        w = sum(read_dsc(d, gid[ord(c)])["adv"] for c in t if ord(c) in gid)
        over = "SIM" if w > lab_w else "-"
        if w > lab_w:
            estouros += 1
        print(f"  {i:>2}  {t:<16}{w:>4}  {str(lab_xy[i]):<12}"
              f"{str(icon_xy[i]):<12}{over}")

        x0, y0 = lab_xy[i]
        px = x0 if align == 0 else x0 + max(0, (lab_w - w) // 2)
        for c in t:
            g = gid.get(ord(c))
            if g is None:
                continue
            gl = read_dsc(d, g)
            for ry, row in enumerate(glyph_rows(d, gl)):
                for rx, on in enumerate(row):
                    if not on:
                        continue
                    # topo do bitmap = linha de base - (ofs_y + altura)
                    X = px + gl["ox"] + rx
                    Y = y0 + ascent - (gl["oy"] + gl["h"]) + ry
                    if 0 <= X < IMG_W and 0 <= Y < IMG_H:
                        scr[Y][X] = 2
            px += gl["adv"]
    print()
    print(f"  rotulos que estouram a largura: {estouros}")

    # colisao vertical entre linhas consecutivas (rotulos de 15 px)
    ys = sorted(y for _, y in lab_xy)
    colisoes = sum(1 for a, b in zip(ys, ys[1:]) if b - a < 15)
    print(f"  linhas com menos de 15 px de espacamento: {colisoes}")

    # --- faixa superior: relogio + titulo, lidos do proprio firmware ---
    if args.status:
        def desenha(txt, px, py):
            x = px
            for c in txt:
                g = gid.get(ord(c))
                if g is None:
                    continue
                gl = read_dsc(d, g)
                for ry, row in enumerate(glyph_rows(d, gl)):
                    for rx, on in enumerate(row):
                        if on:
                            X = x + gl["ox"] + rx
                            Y = py + ascent - (gl["oy"] + gl["h"]) + ry
                            if 0 <= X < IMG_W and 0 <= Y < IMG_H:
                                scr[Y][X] = 2
                x += gl["adv"]
            return x

        def larg(txt):
            return sum(read_dsc(d, gid[ord(c)])["adv"] for c in txt if ord(c) in gid)

        # O titulo mora no label view_p[0x14] (criado em 0x00D226AC), que e
        # o que realmente aparece na faixa. O V016 patcheou o view_p[0x18]
        # (0x00D226F8), que nunca e criado -- ver docs/STATUS_BAR.md §9.
        titulo_ptr = struct.unpack_from("<I", d, 0x001226F4)[0]
        titulo = string_at(d, titulo_ptr) if titulo_ptr >= 0x00C00000 else ""
        t_align, t_x, t_y = d[0x001226BE], d[0x001226BA], d[0x001226B6]
        if titulo and ord(titulo[0]) >= 0xE000:
            titulo = ""          # ainda e um glifo de icone, nao um titulo
        desenha("23:38", 3, 2)                       # relogio: TOP_LEFT + (3,2)
        if titulo:
            tw = larg(titulo)
            tx = ((IMG_W - tw) // 2 + t_x) if t_align == 2 else t_x
            desenha(titulo, tx, t_y)
            print(f"  faixa: relogio x 3..{3+larg('23:38')} · "
                  f"titulo {titulo!r} {tw} px x {tx}..{tx+tw} (align {t_align})")

    if args.out:
        try:
            from PIL import Image
        except ImportError:
            print("\n  PIL ausente: instale com 'pip3 install Pillow' "
                  "ou omita --out para ver em ASCII.", file=sys.stderr)
            return 1
        pal = [(d[PAL_OFF + i * 4 + 2], d[PAL_OFF + i * 4 + 1],
                d[PAL_OFF + i * 4 + 0]) for i in range(256)]
        img = Image.new("RGB", (IMG_W, IMG_H))
        pix = img.load()
        for y in range(IMG_H):
            for x in range(IMG_W):
                v = scr[y][x]
                if v == 0:
                    pix[x, y] = pal[bg]
                elif v == 1:
                    pix[x, y] = pal[d[PIX_OFF + y * IMG_W + x]]
                else:
                    pix[x, y] = (255, 255, 255)
        if args.scale > 1:
            img = img.resize((IMG_W * args.scale, IMG_H * args.scale),
                             Image.NEAREST)
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        img.save(args.out)
        print(f"\n  previa gravada: {args.out}")
    else:
        print()
        for y in range(IMG_H):
            print("  " + "".join(".#@"[scr[y][x]] for x in range(IMG_W)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
