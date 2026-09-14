#!/usr/bin/env python3
"""
extract_fonts.py — Decodifica fontes bitmap LVGL embutidas no firmware YP3.

PROPOSITO
    O firmware usa fontes no formato lv_font_fmt_txt (LVGL v8) com bitmaps
    de 1 bit por pixel. Cada fonte e composta por tres blocos contiguos:

        [ glyph_bitmap ]  blob de bitmaps 1bpp, empacotado por linha
        [ glyph_dsc    ]  tabela de descritores de 16 bytes por glifo
        [ cmap         ]  lista de codepoints Unicode (uint16), ordenada

    Descritor de glifo (16 bytes, little-endian) — layout deduzido e
    validado por auto-consistencia e por renderizacao:

        +0x00  uint32  bitmap_index offset dentro do blob de bitmaps
        +0x04  uint32  adv_w        avanco horizontal em pixels
        +0x08  uint16  box_w        largura da caixa em pixels
        +0x0A  uint16  box_h        altura da caixa em pixels
        +0x0C  int16   ofs_x        deslocamento horizontal
        +0x0E  int16   ofs_y        deslocamento vertical

    Corresponde a lv_font_fmt_txt_glyph_dsc_t do LVGL v8 compilado com
    LV_FONT_FMT_TXT_LARGE = 1 (campos alargados para 32/16 bits).

    O glifo de indice 0 e o espaco (box_h = 0, apenas adv_w).
    O tamanho do bitmap de um glifo e ceil(box_w/8) * box_h.

USO
    python3 tools/extract_fonts.py <arquivo.bin> --table 0x86C40 --base 0x5E7E0 \
        [--cmap 0x0A27E6] [--render 0x41,0x42] [--dump-dir DIR]

DEPENDENCIAS
    Apenas biblioteca padrao do Python 3.

EXEMPLO
    python3 tools/extract_fonts.py firmware/WORKING/GN438_analysis.bin \
        --table 0x86C40 --base 0x5E7E0 --cmap 0x0A27E6 --render 0x41,0x61,0x30

LIMITACOES
    - Os offsets de tabela/blob/cmap NAO sao auto-descobertos: precisam ser
      informados. O modo --scan localiza tabelas candidatas por
      auto-consistencia, mas a base do blob deve ser confirmada visualmente.
    - Nao decodifica o cabecalho lv_font_t em si (ponteiros em RAM), apenas
      os tres blocos de dados.
"""

import argparse
import struct
import sys

DSC_SIZE = 16


def read_dsc(data, table, i):
    o = table + i * DSC_SIZE
    bmp, adv = struct.unpack_from("<2I", data, o)
    box_w, box_h = struct.unpack_from("<HH", data, o + 8)
    ofs_x, ofs_y = struct.unpack_from("<hh", data, o + 12)
    return {"ofs_y": ofs_y, "ofs_x": ofs_x, "bitmap_index": bmp,
            "adv_w": adv, "box_w": box_w, "box_h": box_h}


def glyph_size(g):
    return ((g["box_w"] + 7) // 8) * g["box_h"]


def count_glyphs(data, table, limit=40000):
    """Conta glifos enquanto bitmap_index[i+1] == bitmap_index[i] + tamanho[i]."""
    n = 1
    while n < limit:
        g = read_dsc(data, table, n - 1)
        nxt = read_dsc(data, table, n)
        if nxt["bitmap_index"] != g["bitmap_index"] + glyph_size(g):
            break
        if nxt["box_w"] > 64 or nxt["box_h"] > 64:
            break
        n += 1
    return n


def render(data, base, g):
    stride = (g["box_w"] + 7) // 8
    rows = []
    for y in range(g["box_h"]):
        line = ""
        for x in range(g["box_w"]):
            byte = data[base + g["bitmap_index"] + y * stride + x // 8]
            line += "#" if (byte >> (7 - (x % 8))) & 1 else "."
        rows.append(line)
    return rows


def read_cmap(data, cmap_off, n):
    return list(struct.unpack_from("<%dH" % n, data, cmap_off))


def main():
    ap = argparse.ArgumentParser(description="Decodifica fontes bitmap LVGL do firmware")
    ap.add_argument("path")
    ap.add_argument("--table", type=lambda s: int(s, 0), required=True,
                    help="offset da tabela glyph_dsc")
    ap.add_argument("--base", type=lambda s: int(s, 0), required=True,
                    help="offset do blob glyph_bitmap")
    ap.add_argument("--cmap", type=lambda s: int(s, 0), default=None,
                    help="offset da lista de codepoints (uint16)")
    ap.add_argument("--render", default=None,
                    help="lista de codepoints a renderizar, ex: 0x41,0x42")
    ap.add_argument("--max-render", type=int, default=12)
    args = ap.parse_args()

    data = open(args.path, "rb").read()
    n = count_glyphs(data, args.table)

    from collections import Counter
    cw, chh = Counter(), Counter()
    for i in range(n):
        g = read_dsc(data, args.table, i)
        cw[g["box_w"]] += 1
        chh[g["box_h"]] += 1

    print("=" * 70)
    print("FONTE")
    print("=" * 70)
    print(f"  glyph_bitmap : 0x{args.base:06X}")
    print(f"  glyph_dsc    : 0x{args.table:06X} .. 0x{args.table + n*DSC_SIZE:06X}")
    print(f"  glifos       : {n}")
    last = read_dsc(data, args.table, n - 1)
    blob_end = args.base + last["bitmap_index"] + glyph_size(last)
    print(f"  blob bitmaps : 0x{args.base:06X} .. 0x{blob_end:06X} "
          f"({blob_end - args.base} bytes)")
    print(f"  larguras     : {dict(cw.most_common(6))}")
    print(f"  alturas      : {dict(chh.most_common(6))}")

    cmap = None
    if args.cmap is not None:
        cmap = read_cmap(data, args.cmap, n)
        print(f"  cmap         : 0x{args.cmap:06X} ({n} codepoints)")
        print(f"  faixa        : U+{min(cmap):04X} .. U+{max(cmap):04X}")
        ascii_n = sum(1 for c in cmap if 0x20 <= c <= 0x7E)
        cjk_n = sum(1 for c in cmap if 0x4E00 <= c <= 0x9FFF)
        sym_n = sum(1 for c in cmap if 0xF000 <= c <= 0xF8FF)
        print(f"  ASCII: {ascii_n}   CJK(U+4E00-9FFF): {cjk_n}   "
              f"simbolos(U+F000-F8FF): {sym_n}")

    if args.render:
        wanted = [int(x, 0) for x in args.render.split(",")]
        print()
        print("=" * 70)
        print("RENDER")
        print("=" * 70)
        for cp in wanted[:args.max_render]:
            if cmap is not None:
                if cp not in cmap:
                    print(f"  U+{cp:04X}: ausente no cmap")
                    continue
                gid = cmap.index(cp)
            else:
                gid = cp
            g = read_dsc(data, args.table, gid)
            ch = chr(cp) if 0x20 <= cp < 0x7F else "?"
            print(f"  U+{cp:04X} '{ch}'  gid={gid}  {g['box_w']}x{g['box_h']}  "
                  f"adv={g['adv_w']} ofs=({g['ofs_x']},{g['ofs_y']})  "
                  f"bmp=0x{g['bitmap_index']:X}")
            for row in render(data, args.base, g):
                print("      " + row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
