#!/usr/bin/env python3
"""
scan_fonts.py — Descobre automaticamente tabelas de glifos LVGL no firmware.

PROPOSITO
    O firmware YP3 armazena fontes e conjuntos de icones no formato
    lv_font_fmt_txt do LVGL v8, compilado com LV_FONT_FMT_TXT_LARGE = 1.
    Cada descritor de glifo ocupa 16 bytes:

        +0x00  uint32  bitmap_index
        +0x04  uint32  adv_w
        +0x08  uint16  box_w
        +0x0A  uint16  box_h
        +0x0C  int16   ofs_x
        +0x0E  int16   ofs_y

    Este script localiza essas tabelas sem conhecer offsets previamente,
    usando auto-consistencia: em uma tabela valida,

        bitmap_index[i+1] == bitmap_index[i] + ceil(box_w * bpp / 8) * box_h

    O bpp e inferido testando 1, 2, 4 e 8 e escolhendo o que produz a
    cadeia consistente mais longa.

USO
    python3 tools/scan_fonts.py <arquivo.bin> [--min-glyphs 16] [--start 0] [--end 0x200000]

DEPENDENCIAS
    Apenas biblioteca padrao do Python 3.

EXEMPLO
    python3 tools/scan_fonts.py firmware/WORKING/GN438_analysis.bin --min-glyphs 20

LIMITACOES
    - Reporta a tabela de descritores e o bpp; a BASE do blob de bitmaps e
      apenas estimada (assumindo que o blob termina onde a tabela comeca).
      Essa estimativa deve ser confirmada renderizando glifos.
    - Tabelas com menos de --min-glyphs entradas sao ignoradas para reduzir
      falsos positivos.
"""

import argparse
import struct
import sys

DSC = 16


def dsc(d, o):
    bmp, adv = struct.unpack_from("<2I", d, o)
    bw, bh = struct.unpack_from("<2H", d, o + 8)
    ox, oy = struct.unpack_from("<2h", d, o + 12)
    return bmp, adv, bw, bh, ox, oy


def sane(r):
    bmp, adv, bw, bh, ox, oy = r
    return (bmp < 0x400000 and adv <= 256 and bw <= 256 and bh <= 256
            and -64 <= ox <= 64 and -64 <= oy <= 64)


def chain(d, o, bpp):
    """Comprimento da cadeia auto-consistente comecando em o, para um bpp."""
    n = 0
    while o + (n + 2) * DSC <= len(d):
        a = dsc(d, o + n * DSC)
        b = dsc(d, o + (n + 1) * DSC)
        if not sane(a) or not sane(b):
            break
        step = ((a[2] * bpp + 7) // 8) * a[3]
        if b[0] != a[0] + step:
            break
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="Descobre tabelas de glifos LVGL")
    ap.add_argument("path")
    ap.add_argument("--min-glyphs", type=int, default=16)
    ap.add_argument("--start", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--end", type=lambda s: int(s, 0), default=None)
    args = ap.parse_args()

    d = open(args.path, "rb").read()
    end = args.end if args.end is not None else len(d)

    found = []
    o = args.start
    while o < end - DSC * 4:
        best = (0, 0)
        for bpp in (1, 2, 4, 8):
            n = chain(d, o, bpp)
            if n > best[0]:
                best = (n, bpp)
        n, bpp = best
        if n >= args.min_glyphs:
            found.append((o, n + 1, bpp))
            o += (n + 1) * DSC
        else:
            o += 4

    print("=" * 78)
    print(f"TABELAS DE GLIFOS ENCONTRADAS: {len(found)}")
    print("=" * 78)
    print(f"  {'TABELA':<12}{'GLIFOS':>8}{'BPP':>5}{'FIM':>12}"
          f"{'BLOB(bytes)':>13}  {'BASE EST.':>11}  DIMENSOES")
    for off, n, bpp in found:
        last = dsc(d, off + (n - 1) * DSC)
        blob = last[0] + ((last[2] * bpp + 7) // 8) * last[3]
        dims = {}
        for i in range(n):
            r = dsc(d, off + i * DSC)
            dims[f"{r[2]}x{r[3]}"] = dims.get(f"{r[2]}x{r[3]}", 0) + 1
        top = ", ".join(f"{k}({v})" for k, v in
                        sorted(dims.items(), key=lambda kv: -kv[1])[:3])
        print(f"  0x{off:08X}{n:>8}{bpp:>5}  0x{off + n*DSC:08X}{blob:>13}"
              f"   0x{off-blob:08X}  {top}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
