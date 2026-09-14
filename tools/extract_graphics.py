#!/usr/bin/env python3
"""
extract_graphics.py — Extrai recursos graficos do firmware GN-438 / YP3 para PNG.

PROPOSITO
    Exporta para arquivos PNG:
      - conjuntos de icones / fontes LVGL (lv_font_fmt_txt, 1bpp ou 4bpp)
      - imagens lv_img_dsc_t (TRUE_COLOR_CHROMA em RGB565, INDEXED_8 com paleta)

    A flash e mapeada em memoria na base 0x00C00000 (confirmado: os ponteiros
    dos descritores de imagem satisfazem ptr - 0x00C00000 == offset no arquivo).

USO
    python3 tools/extract_graphics.py <arquivo.bin> --out DIR [--icons] [--images]

DEPENDENCIAS
    Apenas biblioteca padrao do Python 3 (PNG escrito sem bibliotecas externas).

EXEMPLO
    python3 tools/extract_graphics.py firmware/WORKING/GN438_analysis.bin \
        --out extracted --icons --images

LIMITACOES
    - Os offsets das tabelas sao constantes verificadas manualmente para
      ESTE firmware (yp3_2.0.43). Outra versao exigira nova varredura
      com tools/scan_fonts.py.
    - Glifos CJK da fonte de texto nao sao exportados individualmente
      (6763 arquivos); use --font-ascii para exportar apenas ASCII.
"""

import argparse
import os
import struct
import sys
import zlib

FLASH_BASE = 0x00C00000

# Tabelas verificadas para o firmware yp3_2.0.43 (SHA-256 b7cd5eb9...)
ICON_SETS = [
    # (nome, offset_tabela, base_blob, bpp, offset_cmap)
    ("icons_main", 0x000BE720, 0x000B0DC4, 4, 0x000C1150),
    ("icons_small", 0x000A6568, 0x000A5F71, 4, None),
]
TEXT_FONT = ("font_text_12px", 0x00086C44, 0x0005E7E0, 1, 0x000A27E6)

IMAGES = [
    # (offset_descritor)
    0x000C235C, 0x000C36F0, 0x000C4A84, 0x000C5E18,
    0x000C71AC, 0x000C73B8, 0x000CC7C4, 0x000CDD50,
]


def png(path, w, h, rgba):
    """Escreve um PNG RGBA de 8 bits sem dependencias externas."""
    raw = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


def read_dsc(d, table, i):
    o = table + i * 16
    bmp, adv = struct.unpack_from("<2I", d, o)
    bw, bh = struct.unpack_from("<2H", d, o + 8)
    ox, oy = struct.unpack_from("<2h", d, o + 12)
    return bmp, adv, bw, bh, ox, oy


def count_glyphs(d, table, bpp, limit=40000):
    n = 1
    while n < limit:
        a = read_dsc(d, table, n - 1)
        b = read_dsc(d, table, n)
        if b[0] != a[0] + ((a[2] * bpp + 7) // 8) * a[3]:
            break
        if not (0 <= b[2] <= 256 and 0 <= b[3] <= 256):
            break
        n += 1
    return n


def glyph_rgba(d, base, g, bpp):
    """Glifo -> RGBA preto com alfa (icones/fontes sao mascaras de alfa)."""
    bmp, adv, bw, bh, ox, oy = g
    stride = (bw * bpp + 7) // 8
    out = bytearray(bw * bh * 4)
    for y in range(bh):
        for x in range(bw):
            byte = d[base + bmp + y * stride + (x * bpp) // 8]
            if bpp == 1:
                v = 255 if (byte >> (7 - (x % 8))) & 1 else 0
            elif bpp == 4:
                v = ((byte >> 4) if x % 2 == 0 else (byte & 0xF)) * 17
            else:
                v = byte
            i = (y * bw + x) * 4
            out[i:i + 4] = bytes((0, 0, 0, v))
    return out


def rgb565_rgba(d, off, w, h):
    out = bytearray(w * h * 4)
    for i in range(w * h):
        v = int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little")
        r = ((v >> 11) & 0x1F) * 255 // 31
        gg = ((v >> 5) & 0x3F) * 255 // 63
        b = (v & 0x1F) * 255 // 31
        out[i * 4:i * 4 + 4] = bytes((r, gg, b, 255))
    return out


def indexed8_rgba(d, off, w, h):
    """Paleta de 256 entradas BGRA de 4 bytes, seguida dos indices."""
    pal = [d[off + i * 4:off + i * 4 + 4] for i in range(256)]
    px = off + 1024
    out = bytearray(w * h * 4)
    for i in range(w * h):
        b, g, r, a = pal[d[px + i]]
        out[i * 4:i * 4 + 4] = bytes((r, g, b, a))
    return out


def main():
    ap = argparse.ArgumentParser(description="Extrai graficos do firmware para PNG")
    ap.add_argument("path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--icons", action="store_true")
    ap.add_argument("--images", action="store_true")
    ap.add_argument("--font-ascii", action="store_true",
                    help="exporta tambem os glifos ASCII da fonte de texto")
    args = ap.parse_args()

    d = open(args.path, "rb").read()
    n_total = 0

    if args.icons:
        for name, table, base, bpp, cmap_off in ICON_SETS:
            n = count_glyphs(d, table, bpp)
            outdir = os.path.join(args.out, name)
            os.makedirs(outdir, exist_ok=True)
            cmap = (struct.unpack_from("<%dH" % n, d, cmap_off)
                    if cmap_off is not None else None)
            written = 0
            for i in range(n):
                g = read_dsc(d, table, i)
                if g[2] == 0 or g[3] == 0:
                    continue
                cp = cmap[i] if cmap and i < len(cmap) else None
                fn = (f"{i:04d}_U+{cp:04X}.png" if cp else f"{i:04d}.png")
                png(os.path.join(outdir, fn), g[2], g[3],
                    glyph_rgba(d, base, g, bpp))
                written += 1
            print(f"  {name:<14} {written} icones -> {outdir}")
            n_total += written

    if args.font_ascii:
        name, table, base, bpp, cmap_off = TEXT_FONT
        n = count_glyphs(d, table, bpp)
        cmap = struct.unpack_from("<%dH" % n, d, cmap_off)
        outdir = os.path.join(args.out, name)
        os.makedirs(outdir, exist_ok=True)
        written = 0
        for i, cp in enumerate(cmap):
            if not (0x20 <= cp <= 0x7E):
                continue
            g = read_dsc(d, table, i)
            if g[2] == 0 or g[3] == 0:
                continue
            png(os.path.join(outdir, f"U+{cp:04X}.png"), g[2], g[3],
                glyph_rgba(d, base, g, bpp))
            written += 1
        print(f"  {name:<14} {written} glifos ASCII -> {outdir}")
        n_total += written

    if args.images:
        outdir = os.path.join(args.out, "images")
        os.makedirs(outdir, exist_ok=True)
        CF = {6: "TRUE_COLOR_CHROMA", 10: "INDEXED_8"}
        for o in IMAGES:
            hdr = int.from_bytes(d[o:o + 4], "little")
            cf = hdr & 0x1F
            w = (hdr >> 10) & 0x7FF
            h = (hdr >> 21) & 0x7FF
            ptr = int.from_bytes(d[o + 8:o + 12], "little")
            data_off = ptr - FLASH_BASE
            if cf == 6:
                rgba = rgb565_rgba(d, data_off, w, h)
            elif cf == 10:
                rgba = indexed8_rgba(d, data_off, w, h)
            else:
                print(f"  0x{o:06X}: formato {cf} nao suportado")
                continue
            fn = f"img_{o:06X}_{w}x{h}_{CF.get(cf, cf)}.png"
            png(os.path.join(outdir, fn), w, h, rgba)
            print(f"  imagem {w}x{h} {CF.get(cf)} -> {fn}")
            n_total += 1

    print(f"\ntotal: {n_total} arquivos PNG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
