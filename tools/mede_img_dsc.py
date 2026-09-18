#!/usr/bin/env python3
"""
mede_img_dsc.py — acha e decodifica os descritores lv_img_dsc_t do firmware.

POR QUE
    Tres itens do Projeto Marte estavam bloqueados pela mesma frase --
    "o layout do descritor de imagem nao esta medido":

        M-g   bateria em bitmap
        M-h   degrade da faixa
        capa  a arte do album na tela Tocando Agora

    Mas o aparelho JA desenha imagem: o papel de parede azul da tela
    Tocando Agora e uma lv_img_dsc_t posta com lv_img_set_src. Se ele
    desenha, o descritor esta la para ser lido.

O QUE PROCURA
    lv_img_dsc_t do LVGL v8 tem 12 bytes:

        +0x00  uint32  header    campo de bits
        +0x04  uint32  data_size
        +0x08  ptr     data      aponta para XIP, 0x00C00000 + offset

    header (32 bits, do bit 0 para o 31):
        cf           5 bits   formato de cor
        always_zero  3 bits   TEM que ser 0 -- e a ancora da busca
        reserved     2 bits
        w           11 bits
        h           11 bits

    Um candidato so e aceito quando TODAS batem:
      - always_zero == 0
      - cf e um formato conhecido
      - o ponteiro cai dentro do arquivo depois de tirar 0x00C00000
      - data_size == o tamanho que w, h e cf preveem

    A ultima condicao e a que separa descritor de coincidencia: tres
    campos independentes precisam concordar.

USO
    python3 tools/mede_img_dsc.py firmware/ORIGINAL/GN438_original.bin
    python3 tools/mede_img_dsc.py <fw> --em 0x000CC7C4   decodifica um so

DEPENDENCIAS
    nenhuma (so a biblioteca padrao)

LIMITACOES
    Acha descritores ESTATICOS, no binario. Imagem montada em runtime
    (uma capa decodificada, por exemplo) nao aparece aqui.
"""
import argparse
import struct
import sys

XIP = 0x00C00000

CF = {
    0: ("UNKNOWN", None),
    1: ("RAW", None),
    2: ("RAW_ALPHA", None),
    3: ("RAW_CHROMA", None),
    4: ("TRUE_COLOR", 2),
    5: ("TRUE_COLOR_ALPHA", 3),
    6: ("TRUE_COLOR_CHROMA", 2),
    7: ("INDEXED_1BIT", None),
    8: ("INDEXED_2BIT", None),
    9: ("INDEXED_4BIT", None),
    10: ("INDEXED_8BIT", 1),
    11: ("ALPHA_1BIT", None),
    12: ("ALPHA_2BIT", None),
    13: ("ALPHA_4BIT", None),
    14: ("ALPHA_8BIT", 1),
}
PALETA = {7: 2 * 4, 8: 4 * 4, 9: 16 * 4, 10: 256 * 4}


def decodifica(h):
    cf = h & 0x1F
    az = (h >> 5) & 0x07
    res = (h >> 8) & 0x03
    w = (h >> 10) & 0x7FF
    hh = (h >> 21) & 0x7FF
    return cf, az, res, w, hh


def tamanho_previsto(cf, w, h):
    nome, bpp = CF.get(cf, ("?", None))
    if bpp is None:
        if cf == 7:
            return PALETA[7] + ((w + 7) // 8) * h
        if cf == 8:
            return PALETA[8] + ((w + 3) // 4) * h
        if cf == 9:
            return PALETA[9] + ((w + 1) // 2) * h
        return None
    if cf == 10:
        return PALETA[10] + w * h
    return w * h * bpp


def olha(d, off, verboso=False):
    if off + 12 > len(d):
        return None
    h, size, ptr = struct.unpack_from("<III", d, off)
    cf, az, res, w, hh = decodifica(h)
    if az != 0 or cf not in CF or w == 0 or hh == 0:
        return None
    if not (XIP <= ptr < XIP + len(d)):
        return None
    prev = tamanho_previsto(cf, w, hh)
    if prev is None or size != prev:
        return None
    return dict(off=off, cf=cf, nome=CF[cf][0], w=w, h=hh, size=size,
                ptr=ptr, dados=ptr - XIP)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--em", help="decodificar um endereco especifico (hex)")
    a = ap.parse_args()
    d = open(a.path, "rb").read()

    if a.em:
        off = int(a.em, 16)
        if off >= XIP:
            off -= XIP
        h, size, ptr = struct.unpack_from("<III", d, off)
        cf, az, res, w, hh = decodifica(h)
        print("em 0x%06X (XIP 0x%08X)" % (off, off + XIP))
        print("  header    0x%08X" % h)
        print("    cf           %-2d  %s" % (cf, CF.get(cf, ("?",))[0]))
        print("    always_zero  %d   %s" % (az, "ok" if az == 0 else "NAO BATE"))
        print("    reserved     %d" % res)
        print("    w            %d" % w)
        print("    h            %d" % hh)
        print("  data_size 0x%X (%d)" % (size, size))
        prev = tamanho_previsto(cf, w, hh)
        print("    previsto  %s  ->  %s" % (prev, "CONFERE" if prev == size else "NAO CONFERE"))
        print("  data      0x%08X  -> offset 0x%06X" % (ptr, ptr - XIP))
        return 0

    achados = []
    for off in range(0, len(d) - 12, 4):
        r = olha(d, off)
        if r:
            achados.append(r)

    print("=" * 74)
    print("DESCRITORES lv_img_dsc_t — %d encontrados" % len(achados))
    print("=" * 74)
    print("%-10s %-20s %-10s %-10s %s" % ("descritor", "formato", "tamanho",
                                          "data_size", "dados"))
    for r in achados:
        print("0x%06X %-20s %4dx%-4d  %9d  0x%06X"
              % (r["off"], r["nome"], r["w"], r["h"], r["size"], r["dados"]))
    print()
    print("Todos passaram nas quatro condicoes: always_zero=0, formato")
    print("conhecido, ponteiro dentro do arquivo, e data_size igual ao")
    print("previsto por largura, altura e formato.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
