#!/usr/bin/env python3
"""
preview_selecao.py — Previa da home com BARRA DE SELECAO, em duas larguras.

PROPOSITO
    A selecao da home hoje muda so a cor do texto. Trocando o alvo da
    chamada de `set_style_text_color` (0xD4D10A) para
    `set_style_bg_color` (0xD4D092), a linha selecionada ganha uma barra.

    Os chevrons ficam na FOLHA de imagem, ou seja ATRAS dos rotulos.
    Entao a largura da barra decide se ela cobre ou nao o chevron da
    linha selecionada. Esta ferramenta desenha as duas opcoes lado a lado
    para a decisao ser tomada olhando, nao imaginando.

USO
    python3 tools/preview_selecao.py firmware/WORKING/GN438_openpod_v026.bin \
        --out analysis/preview/selecao.png [--larguras 128,110] [--scale 4]

DEPENDENCIAS
    Python 3 + PIL

LIMITACOES
    - Nao simula a LVGL: desenha o que os dados dizem.
    - A cor da barra usa LV_PALETTE_CYAN (#00BCD4), que e a paleta 7 ja
      usada hoje pela selecao (`0xd57b48(7)`).
"""
import argparse, os, struct, sys

FONT_TABLE, FONT_CMAP, FONT_BASE, FONT_N = 0x00086C44, 0x000A27E6, 0x0005E7E0, 7098
TBL_LABEL, TBL_TEXT = 0x000486A0, 0x000486C4
PIX_OFF, PAL_OFF = 0x000CE15C, 0x000CDD5C
W, H = 128, 160
POOL_PT = 0x00121104
COR_BARRA = (0x00, 0xBC, 0xD4)      # LV_PALETTE_CYAN, a paleta 7 atual


def dsc(d, i):
    o = FONT_TABLE + i * 16
    bmp, adv = struct.unpack_from("<2I", d, o)
    bw, bh = struct.unpack_from("<HH", d, o + 8)
    ox, oy = struct.unpack_from("<hh", d, o + 12)
    return dict(bmp=bmp, adv=adv, w=bw, h=bh, ox=ox, oy=oy)


def rows(d, g):
    st = (g["w"] + 7) // 8
    return [[(d[FONT_BASE + g["bmp"] + y * st + x // 8] >> (7 - (x % 8))) & 1
             for x in range(g["w"])] for y in range(g["h"])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--larguras", default="128,110")
    ap.add_argument("--scale", type=int, default=4)
    ap.add_argument("--sel", default="0", help="linhas selecionadas, ex: 0,2")
    a = ap.parse_args()
    d = open(a.path, "rb").read()
    from PIL import Image, ImageDraw

    cmap = struct.unpack_from("<%dH" % FONT_N, d, FONT_CMAP)
    gid = {c: i for i, c in enumerate(cmap)}
    # A ascendente TEM de considerar os acentos: 'a' 'a' 'i' 'u' sobem 1 px
    # acima do maior glifo ASCII. Calcular so com ASCII faz o acento ser
    # desenhado ACIMA da caixa do rotulo -- defeito de renderizacao que
    # chegou a parecer defeito de desenho.
    _faixa = list(range(0x21, 0x7F)) + [0xC0 + k for k in range(64)] + \
             [0xE0 + k for k in range(32)]
    asc = max(dsc(d, gid[c])["oy"] + dsc(d, gid[c])["h"]
              for c in _faixa if c in gid)
    pal = [(d[PAL_OFF + i * 4 + 2], d[PAL_OFF + i * 4 + 1], d[PAL_OFF + i * 4])
           for i in range(256)]
    base = struct.unpack_from("<I", d, POOL_PT)[0] - 0x00C00000
    n = d[0x0012ED88] // 4
    ys = [struct.unpack_from("<hh", d, TBL_LABEL + i * 4)[1] for i in range(n)]
    ids = [struct.unpack_from("<I", d, TBL_TEXT + i * 4)[0] for i in range(n)]

    def txt(i):
        p = struct.unpack_from("<I", d, base + ids[i] * 4)[0] - 0x00C00000
        return d[p:d.index(b"\0", p)].decode("utf-8", "replace")

    def painel(larg_barra, sel=0):
        img = Image.new("RGB", (W, H))
        px = img.load()
        for y in range(H):
            for x in range(W):
                px[x, y] = pal[d[PIX_OFF + y * W + x]]
        # barra de selecao, por cima da folha (e do chevron, se alcancar)
        dr = ImageDraw.Draw(img)
        x0 = struct.unpack_from("<hh", d, TBL_LABEL + sel * 4)[0]
        dr.rectangle([x0, ys[sel], x0 + larg_barra - 1, ys[sel] + 14],
                     fill=COR_BARRA)
        for i in range(n):
            x = 6
            for c in txt(i):
                g = gid.get(ord(c))
                if g is None:
                    continue
                gl = dsc(d, g)
                for ry, row in enumerate(rows(d, gl)):
                    for rx, on in enumerate(row):
                        if on:
                            X, Y = x + gl["ox"] + rx, ys[i] + asc - (gl["oy"] + gl["h"]) + ry
                            if 0 <= X < W and 0 <= Y < H:
                                px[X, Y] = (255, 255, 255)
                x += gl["adv"]
        # faixa superior simulada
        for s, xx in (("23:38", 3), ("OpenPod", 42)):
            x = xx
            for c in s:
                g = gid.get(ord(c))
                gl = dsc(d, g)
                for ry, row in enumerate(rows(d, gl)):
                    for rx, on in enumerate(row):
                        if on:
                            X, Y = x + gl["ox"] + rx, 1 + asc - (gl["oy"] + gl["h"]) + ry
                            if 0 <= X < W and 0 <= Y < H:
                                px[X, Y] = (255, 255, 255)
                x += gl["adv"]
        return img

    largs = [int(v) for v in a.larguras.split(",")]
    sels = [int(v) for v in a.sel.split(",")]
    if len(sels) > 1 and len(largs) == 1:
        largs = largs * len(sels)
    elif len(sels) == 1:
        sels = sels * len(largs)
    s = a.scale
    gap, topo = 16, 22
    out = Image.new("RGB", (len(largs) * W * s + gap * (len(largs) + 1),
                            H * s + topo + gap), (24, 24, 28))
    dr = ImageDraw.Draw(out)
    for k, lg in enumerate(largs):
        p = painel(lg, sels[k]).resize((W * s, H * s), Image.NEAREST)
        x0 = gap + k * (W * s + gap)
        out.paste(p, (x0, topo))
        dr.text((x0 + 4, 6), f"barra ate x={lg} · selecao na linha {sels[k]}",
                fill=(235, 235, 240))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    out.save(a.out)
    print(f"  itens: {n}   linhas y={ys}")
    print(f"  larguras renderizadas: {largs}")
    print(f"  previa gravada: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
