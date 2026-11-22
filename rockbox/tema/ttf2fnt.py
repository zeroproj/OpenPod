#!/usr/bin/env python3
"""ttf2fnt.py - converte uma fonte TrueType/OpenType em fonte do Rockbox (.fnt, "RB12"), suavizada.

Formato (lido em firmware/font.c e tools/convttf.c do Rockbox; este arquivo e codigo nosso):
  cabecalho "RB12" + maxwidth, height, ascent, depth (u16) + firstchar, defaultchar, size,
  nbits, noffset, nwidth (u32); depois os bitmaps, pad para 2, offsets (u16), larguras (u8).
  depth=1: 4 bits por pixel, linha a linha, nibble baixo primeiro, 15 = vazio, 0 = tinta cheia.
  Cada glifo tem a largura de avanco e a altura da fonte; comeca num byte novo.

Uso:
  python3 ttf2fnt.py --ttf Inter.ttf --px 12 --peso 400 --saida 12-Inter.fnt
"""
import argparse
import struct
from PIL import Image, ImageDraw, ImageFont

PRIMEIRO, ULTIMO = 0x20, 0xFF            # Latin-1: cobre o portugues (acentos, c cedilha)


def carrega(ttf, px, peso, opsz):
    f = ImageFont.truetype(ttf, px)
    eixos = [a["name"] for a in f.get_variation_axes()] if hasattr(f, "get_variation_axes") else []
    if eixos:
        val = []
        for a in eixos:
            n = a.decode() if isinstance(a, bytes) else a
            val.append(peso if n.lower().startswith("weight") else opsz)
        f.set_variation_by_axes(val)
    return f


def glifo(f, ch, asc, h):
    avanco = max(1, round(f.getlength(ch)))
    im = Image.new("L", (avanco + 4, h), 0)
    ImageDraw.Draw(im).text((0, asc), ch, font=f, fill=255, anchor="ls")
    # recorta a margem extra so se estiver vazia (italicos/kerning podem passar do avanco)
    larg = avanco
    for x in range(im.width - 1, avanco - 1, -1):
        if any(im.getpixel((x, y)) for y in range(h)):
            larg = x + 1
            break
    return im.crop((0, 0, larg, h))


def empacota(im):
    w, h = im.size
    nib = [((255 - im.getpixel((x, y))) + 8) // 17 for y in range(h) for x in range(w)]
    out = bytearray()
    for i in range(0, len(nib), 2):
        lo = nib[i]
        hi = nib[i + 1] if i + 1 < len(nib) else 0
        out.append(lo | (hi << 4))
    return bytes(out)


def converte(ttf, px, peso, opsz, saida):
    f = carrega(ttf, px, peso, opsz)
    # altura pela tinta real (inclui acentos), nao pelo espacamento de linha da fonte
    topo = base = 0
    for c in list(range(0x21, 0x7F)) + list(range(0xA0, ULTIMO + 1)):
        x0, y0, x1, y1 = f.getbbox(chr(c), anchor="ls")
        topo, base = max(topo, -y0), max(base, y1)
    asc, h = topo, topo + base
    dados, offs, larg = bytearray(), [], []
    for c in range(PRIMEIRO, ULTIMO + 1):
        ch = chr(c)
        if c < 0x7F or c >= 0xA0:
            im = glifo(f, ch, asc, h)
        else:                                   # 0x7F..0x9F: controle, vira espaco
            im = glifo(f, " ", asc, h)
        offs.append(len(dados))
        larg.append(im.width)
        dados += empacota(im)
    assert len(dados) < 0xFFDB, "fonte grande demais para offsets de 16 bits"
    n = ULTIMO - PRIMEIRO + 1
    cab = b"RB12" + struct.pack("<HHHHIIIIII", max(larg), h, asc, 1, PRIMEIRO, PRIMEIRO,
                                n, len(dados), n, n)
    corpo = bytes(dados) + (b"\0" if len(dados) & 1 else b"")
    corpo += struct.pack(f"<{n}H", *offs) + bytes(larg)
    open(saida, "wb").write(cab + corpo)
    return h, asc, max(larg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttf", required=True)
    ap.add_argument("--px", type=int, required=True)
    ap.add_argument("--peso", type=int, default=400)
    ap.add_argument("--opsz", type=int, default=14)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    h, asc, mw = converte(a.ttf, a.px, a.peso, a.opsz, a.saida)
    print(f"{a.saida}: altura {h}, ascendente {asc}, largura max {mw}")


if __name__ == "__main__":
    main()
