#!/usr/bin/env python3
"""
patch_bar_height.py — Da altura decente a faixa superior e re-espaca a lista.

O PROBLEMA, MEDIDO

    A fonte de texto tem ascendente 12 e descendente 0. Com y_ofs = 2, o
    relogio e o titulo ocupam y = 2 .. 14.

    A barra do V017 vai de y0 a y12, com o separador em y13.

        texto   y  2 .. 14
        barra   y  0 .. 12
        linha   y 13

    Ou seja: o texto ESTOURA a barra em 1 px e cruza o separador. E por
    isso que a faixa parece apertada -- nao e impressao, e geometria.

A CORRECAO

    barra      y  0 .. 15     texto sobe para y_ofs = 1, ocupando 1..13
    separador  y 16
    respiro    y 17 .. 18     2 px, senao a linha encosta em "Musica"
    lista      y 19 .. 159    (141 px para 9 linhas)

    As 9 linhas nao cabem em espacamento inteiro (141 / 9 = 15,7), entao
    ficam alternando 16 e 15 px:

        19  35  50  66  82  97  113  129  144

    A ultima termina exatamente em 159. A diferenca de 1 px entre linhas
    e invisivel com fonte de 12 px, e e melhor que sobrar espaco morto no
    rodape ou cortar a ultima linha.

    A bateria desce de y=0 para y=2, para centralizar na barra nova.

O QUE E ALTERADO

    0x0004867C   36 B  coordenadas dos chevrons   -> (116, linha + 3)
    0x000486A0   36 B  coordenadas dos rotulos    -> (6, linha)
    0x0012260E    1 B  y da bateria  0x00 -> 0x02
    0x001217D6    1 B  y_ofs do relogio  0x02 -> 0x01
    0x001226B6    1 B  y_ofs do titulo   0x02 -> 0x01
    0x000CE15C   px    folha inteira redesenhada: barra, separador,
                       9 chevrons nas posicoes novas

    Mais o CRC-16 da particao FIRM.

    O y_ofs do relogio e do titulo cai de 2 para 1: e isso que libera os
    2 px de respiro sem apertar a barra nem cortar a ultima linha.

USO
    python3 tools/patch_bar_height.py \
        --in  firmware/WORKING/GN438_openpod_v017.bin \
        --out firmware/WORKING/GN438_openpod_v018.bin [--dry-run]

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se as tabelas de entrada nao forem as do V014/V017;
    - recusa se a paleta nao tiver as entradas do V017;
    - recusa se alguma linha passar de 160 px;
    - a entrada e aberta somente para leitura; a saida e arquivo novo.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

TBL_ICON = 0x0004867C
TBL_LABEL = 0x000486A0
BATERIA_Y = 0x0012260E

IMG_DESC = 0x000CDD50
PAL_OFF = 0x000CDD5C
PIX_OFF = 0x000CE15C
IMG_W, IMG_H = 128, 160
BG_INDEX = 1
FG_INDEX = 0

# geometria nova
# O texto da barra sobe para y_ofs = 1 (ocupa y 1..13), o que libera
# espaco para 2 px de respiro entre o separador e a primeira linha da
# lista. Sem isso a linha encosta no topo de "Musica" -- medido: 0 px.
BANDA_FIM = 15          # barra ocupa y 0..15
SEPARADOR_Y = 16
LISTA_Y0 = 19           # y 17 e 18 ficam no fundo: o respiro
YOFS_RELOGIO = 0x001217D6
YOFS_TITULO = 0x001226B6
N = 9
LABEL_X = 6
LABEL_H = 15
CHEVRON_X = 116
CHEVRON_DY = 3

BANDAS = [(0, 4, 2), (5, 9, 3), (10, BANDA_FIM, 4)]
SEPARADOR_IDX = 5

CHEVRON = [
    "##....", ".##...", "..##..", "...##.", "....##",
    "...##.", "..##..", ".##...", "##....",
]

# estado de entrada esperado (V014 -> V017)
COORD_ICON_V17 = [(116, 16 + 16 * i) for i in range(N)]
COORD_LABEL_V17 = [(6, 16 + 16 * i) for i in range(N)]
PALETA_V17 = {2: (20, 22, 26), 3: (14, 16, 19), 4: (9, 10, 12),
              5: (52, 56, 62)}


def linhas():
    return [LISTA_Y0 + round(i * (IMG_H - LISTA_Y0) / N) for i in range(N)]


def read_pairs(d, off):
    return [struct.unpack_from("<hh", d, off + i * 4) for i in range(N)]


def firm_entry(data):
    pt = struct.unpack_from("<I", data, 0x20)[0]
    n = struct.unpack_from("<I", data, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if data[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", data, b + 4)
            return b, off, ln
    raise RuntimeError("particao FIRM nao encontrada")


def check(data):
    e = []
    hdr = struct.unpack_from("<I", data, IMG_DESC)[0]
    cf, w, h = hdr & 0x1F, (hdr >> 10) & 0x7FF, (hdr >> 21) & 0x7FF
    if (cf, w, h) != (10, IMG_W, IMG_H):
        e.append(f"descritor da folha inesperado: cf={cf} {w}x{h}")

    if read_pairs(data, TBL_ICON) != COORD_ICON_V17:
        e.append("tabela de chevrons nao e a do V014/V017")
    if read_pairs(data, TBL_LABEL) != COORD_LABEL_V17:
        e.append("tabela de rotulos nao e a do V014/V017")
    if data[BATERIA_Y] != 0x00:
        e.append(f"y da bateria em 0x{BATERIA_Y:06X} e "
                 f"0x{data[BATERIA_Y]:02X}, esperado 0x00")
    for off, nome in ((YOFS_RELOGIO, "relogio"), (YOFS_TITULO, "titulo")):
        if data[off] != 0x02:
            e.append(f"y_ofs do {nome} em 0x{off:06X} e "
                     f"0x{data[off]:02X}, esperado 0x02")

    for i, (r, g, b) in PALETA_V17.items():
        got = (data[PAL_OFF + i * 4 + 2], data[PAL_OFF + i * 4 + 1],
               data[PAL_OFF + i * 4])
        if got != (r, g, b):
            e.append(f"paleta idx {i} e {got}, esperado {(r, g, b)} "
                     "— a entrada nao parece ser o V017")

    ys = linhas()
    if ys[-1] + LABEL_H > IMG_H:
        e.append(f"a ultima linha terminaria em {ys[-1] + LABEL_H}, "
                 f"alem de {IMG_H}")
    if ys[0] <= SEPARADOR_Y:
        e.append("a primeira linha comecaria em cima do separador")
    return e


def desenha_folha(data, ys):
    for i in range(IMG_W * IMG_H):
        data[PIX_OFF + i] = BG_INDEX
    for y0, y1, pi in BANDAS:
        for y in range(y0, y1 + 1):
            for x in range(IMG_W):
                data[PIX_OFF + y * IMG_W + x] = pi
    for x in range(IMG_W):
        data[PIX_OFF + SEPARADOR_Y * IMG_W + x] = SEPARADOR_IDX
    for y0 in ys:
        for dy, linha in enumerate(CHEVRON):
            for dx, c in enumerate(linha):
                if c != "#":
                    continue
                x, y = CHEVRON_X + dx, y0 + CHEVRON_DY + dy
                if 0 <= x < IMG_W and 0 <= y < IMG_H:
                    data[PIX_OFF + y * IMG_W + x] = FG_INDEX


def main():
    ap = argparse.ArgumentParser(
        description="Faixa superior mais alta e lista re-espacada")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if os.path.abspath(args.src) == os.path.abspath(args.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    with open(args.src, "rb") as fh:
        orig = fh.read()
    data = bytearray(orig)

    print("=" * 72)
    print("OpenPod — faixa superior com altura decente (V017 -> V018)")
    print("=" * 72)
    print(f"  origem : {args.src}")
    print(f"  destino: {args.dst}")
    print()

    erros = check(data)
    if erros:
        print("  ABORTADO — o firmware de entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print("  estado de entrada conferido: tabelas do V014/V017, paleta do "
          "V017, bateria em y=0  OK")
    print()

    ys = linhas()
    print("  GEOMETRIA")
    print(f"    barra       y  0 ..{BANDA_FIM:>3}   (texto em 1..13: "
          f"1 px em cima, {BANDA_FIM - 13} embaixo)")
    print(f"    separador   y {SEPARADOR_Y:>3}")
    print(f"    respiro     y {SEPARADOR_Y+1:>3} ..{LISTA_Y0-1:>3}   "
          f"({LISTA_Y0 - SEPARADOR_Y - 1} px antes da lista)")
    print(f"    lista       y {LISTA_Y0:>3} ..{ys[-1] + LABEL_H:>3}")
    print(f"    linhas      {ys}")
    print(f"    espacamento {[b - a for a, b in zip(ys, ys[1:])]}")
    print()

    novo_rotulo = [(LABEL_X, y) for y in ys]
    novo_chevron = [(CHEVRON_X, y) for y in ys]
    for off, pares in ((TBL_LABEL, novo_rotulo), (TBL_ICON, novo_chevron)):
        for i, (x, y) in enumerate(pares):
            struct.pack_into("<hh", data, off + i * 4, x, y)
    data[BATERIA_Y] = 0x02
    data[YOFS_RELOGIO] = 0x01
    data[YOFS_TITULO] = 0x01
    desenha_folha(data, ys)

    print("  ALTERACOES")
    print(f"    0x{TBL_LABEL:06X}  36 B  coordenadas dos rotulos")
    print(f"    0x{TBL_ICON:06X}  36 B  coordenadas dos chevrons")
    print(f"    0x{BATERIA_Y:06X}   1 B  y da bateria 0x00 -> 0x02")
    print(f"    0x{YOFS_RELOGIO:06X}   1 B  y_ofs do relogio 0x02 -> 0x01")
    print(f"    0x{YOFS_TITULO:06X}   1 B  y_ofs do titulo  0x02 -> 0x01")
    print(f"    0x{PIX_OFF:06X}  px    folha redesenhada")
    print()

    base, foff, flen = firm_entry(data)
    old_crc = struct.unpack_from("<H", data, base + 0x0C)[0]
    new_crc = fw.crc16(bytes(data[foff:foff + flen]))
    if args.dry_run:
        print(f"  CRC da FIRM: 0x{old_crc:04X} -> 0x{new_crc:04X} (nao gravado)")
    else:
        # R1: o CRC da FIRM nao e verificado pelo aparelho, e gravar aqui
        # poria o setor 0x00D000 (tabela de particoes) de volta na lista
        # de setores a escrever. Foi esse setor que matou o primeiro
        # aparelho. Achado pelo tools/build.py ao reconstruir do zero.
        pass   # NAO gravar o CRC (R1)
        print(f"  CRC da FIRM: 0x{old_crc:04X} -> 0x{new_crc:04X}")

    d2 = [i for i in range(len(orig)) if orig[i] != data[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in d2})
    print(f"  bytes alterados: {len(d2)}   tamanho: inalterado ({len(data)})")
    print(f"  setores de 4 KiB a regravar: {len(secs)}")
    print("    " + "  ".join(f"0x{s:06X}" for s in secs))
    print()

    if args.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0

    with open(args.dst, "wb") as fh:
        fh.write(data)
    print(f"  gravado: {args.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
