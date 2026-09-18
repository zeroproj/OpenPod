#!/usr/bin/env python3
"""
fonte_para_svg.py — desenha um texto com a FONTE REAL do firmware e
                    devolve SVG.

POR QUE EXISTE
    A pagina do projeto reconstroi a tela do aparelho em CSS. As cores
    sao medidas, mas o texto usava uma fonte web -- e a fonte do GN-438
    e bitmap, 1 bpp, 12 px de altura. Lado a lado, sao duas categorias
    de tipografia diferentes, e a reconstrucao denunciava isso.

    Aqui os pixels sao os do firmware. Nao e parecido: e igual.

O FORMATO (CONFIRMADO, ver docs/GUI_ANALYSIS.md secao 3)
    lv_font_fmt_txt do LVGL v8, LV_FONT_FMT_TXT_LARGE=1.

        blob de bitmaps   0x0005E7E0   1 bpp, empacotado por linha
        tabela de glifos  0x00086C44   7098 x 16 B
        cmap (u16)        0x000A27E6   ordenada, U+0020..U+FFE5

    Descritor de 16 B: bitmap_index u32, adv_w u32, box_w u16,
    box_h u16, ofs_x i16, ofs_y i16.

    Posicao vertical: y_topo = ALTURA - ofs_y - box_h. Deduzido e
    conferido -- 'A' (ofs_y=3, box_h=9) fica no topo e 'g' (ofs_y=1)
    desce 2 px, que e a descendente.

USO
    python3 tools/fonte_para_svg.py --imagem <fw.bin> --texto "Musica"
    python3 tools/fonte_para_svg.py --imagem <fw.bin> --pagina docs/index.html

    --pagina  troca os textos da tela reconstruida na propria pagina

DEPENDENCIAS
    nenhuma (so a biblioteca padrao)

LIMITACOES
    So 1 bpp. Se um dia aparecer fonte de 2 ou 4 bpp no firmware, esta
    ferramenta recusa em vez de desenhar errado.
"""
import argparse
import re
import struct
import sys

BLOB = 0x0005E7E0
TBL = 0x00086C44
CMAP = 0x000A27E6
N = 7098
ALTURA = 12


class Fonte:
    def __init__(self, caminho):
        self.d = open(caminho, "rb").read()
        cm = struct.unpack_from("<%dH" % N, self.d, CMAP)
        self.idx = {c: i for i, c in enumerate(cm)}

    def glifo(self, ch):
        g = self.idx.get(ord(ch))
        if g is None:
            return None
        bi, adv, bw, bh, ox, oy = struct.unpack_from("<IIHHhh", self.d, TBL + g * 16)
        linha = (bw + 7) // 8
        bm = self.d[BLOB + bi: BLOB + bi + linha * bh]
        px = [[(bm[y * linha + (x >> 3)] >> (7 - (x & 7))) & 1 if y * linha + (x >> 3) < len(bm) else 0
               for x in range(bw)] for y in range(bh)]
        return dict(adv=adv, bw=bw, bh=bh, ox=ox, oy=oy, px=px)

    def matriz(self, txt):
        """Devolve (largura, matriz de 0/1 com ALTURA linhas)."""
        larg = 0
        for ch in txt:
            g = self.glifo(ch)
            if g is None:
                sys.exit("ABORTADO: caractere ausente na fonte: %r (U+%04X)" % (ch, ord(ch)))
            larg += g["adv"]
        m = [[0] * larg for _ in range(ALTURA)]
        x = 0
        for ch in txt:
            g = self.glifo(ch)
            topo = ALTURA - g["oy"] - g["bh"]
            for yy in range(g["bh"]):
                y = topo + yy
                if 0 <= y < ALTURA:
                    for xx in range(g["bw"]):
                        if g["px"][yy][xx]:
                            px = x + g["ox"] + xx
                            if 0 <= px < larg:
                                m[y][px] = 1
            x += g["adv"]
        return larg, m


def svg(larg, m, classe="g"):
    """SVG compacto: corridas horizontais viram um retangulo cada."""
    partes = []
    for y, linha in enumerate(m):
        x = 0
        while x < larg:
            if linha[x]:
                ini = x
                while x < larg and linha[x]:
                    x += 1
                partes.append("M%d %dh%dv1h-%dz" % (ini, y, x - ini, x - ini))
            else:
                x += 1
    return ('<svg class="%s" viewBox="0 0 %d %d" width="%d" height="%d" '
            'shape-rendering="crispEdges" aria-hidden="true">'
            '<path fill="currentColor" d="%s"/></svg>'
            % (classe, larg, ALTURA, larg, ALTURA, "".join(partes)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imagem", required=True)
    ap.add_argument("--texto")
    ap.add_argument("--pagina")
    a = ap.parse_args()
    f = Fonte(a.imagem)

    if a.texto:
        larg, m = f.matriz(a.texto)
        for linha in m:
            print("".join("#" if v else "." for v in linha))
        print("\n%d x %d px" % (larg, ALTURA))
        print(svg(larg, m))
        return 0

    if not a.pagina:
        sys.exit("use --texto ou --pagina")

    s = open(a.pagina, encoding="utf-8").read()

    def troca(alvo, texto):
        nonlocal s
        larg, m = f.matriz(texto)
        novo = '<span class="t" aria-label="%s">%s</span>' % (texto, svg(larg, m))
        n = s.count(alvo)
        if n != 1:
            sys.exit("ABORTADO: esperava 1 ocorrencia de %r, achei %d" % (alvo[:50], n))
        s = s.replace(alvo, alvo.replace(">" + texto + "<", ">" + novo + "<"), 1)

    troca('<span>14:32</span>', "14:32")
    troca('<span class="mid">OpenPod</span>', "OpenPod")
    for rot in ("Música", "Vídeo", "Extras", "Configurar"):
        troca('<div class="row%s">%s</div>' % (" sel" if rot == "Música" else "", rot), rot)

    # o alternador Fabrica troca o titulo da faixa por JS: gera os dois
    for rot in ("OpenPod", "Menu"):
        larg, m = f.matriz(rot)
        s = s.replace("/*{SVG_%s}*/" % rot.upper(),
                      "'" + svg(larg, m).replace("'", "\\'") + "'")

    open(a.pagina, "w", encoding="utf-8").write(s)
    print("pagina redesenhada com a fonte do firmware")
    return 0


if __name__ == "__main__":
    sys.exit(main())
