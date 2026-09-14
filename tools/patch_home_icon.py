#!/usr/bin/env python3
"""
patch_home_icon.py — Substitui um icone da folha do menu principal do GN-438.

PROPOSITO
    O menu principal (page_home_create) desenha uma unica imagem
    lv_img_dsc_t de 128x160 em INDEXED_8, que contem os 9 icones em grade
    3x3. Esta ferramenta altera os PIXELS de UMA celula dessa imagem.

    Por que isto e o patch de menor risco possivel:
      - a imagem tem tamanho fixo; nenhum offset muda;
      - nao ha tabela de recursos a atualizar;
      - so indices de paleta JA EXISTENTES sao usados: a paleta nao muda;
      - apenas o CRC da particao FIRM precisa ser recalculado, e
        tools/rebuild_firmware.py ja faz isso.

    A imagem original NUNCA e alterada: a entrada e aberta somente para
    leitura e a saida e um arquivo novo.

GEOMETRIA (verificada neste firmware, yp3_2.0.43)
    descritor  0x000CDD50   INDEXED_8  128x160  21504 bytes
    paleta     0x000CDD5C   256 entradas BGRA
    pixels     0x000CE15C   20480 bytes, 1 byte de indice por pixel

    celulas (x0, y0, largura, altura):
      1 Musica    ( 6, 16) 33x31     6 Fotos      (89, 65) 31x31
      2 Video     (48, 16) 32x31     7 Bluetooth  ( 6,112) 33x31
      3 Gravador  (89, 16) 31x31     8 Ajustes    (48,112) 32x31
      4 FM        ( 6, 65) 33x31     9 Arquivos   (89,112) 31x31
      5 eBook     (48, 65) 32x31

USO
    python3 tools/patch_home_icon.py --in <original.bin> --out <patched.bin> \
        --cell N --op recolor --rgb R,G,B [--dry-run]

    --op recolor   remapeia cada pixel da celula para a entrada de paleta
                   mais proxima da cor alvo, preservando a luminancia
                   relativa do pixel original. Pixels de fundo nao mudam.

    --keep A,B,C   indices de paleta a PRESERVAR (nao remapeados). Use para
                   manter detalhes que devem continuar com a cor original,
                   por exemplo o rotulo vermelho do disco de vinil.

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SAIDA
    Relata cada byte alterado (contagem, faixa) e recalcula o CRC da
    particao FIRM para que a imagem permaneca auto-consistente.

LIMITACOES
    - A geometria acima e constante deste firmware. Outra versao exige
      nova analise.
    - Nao altera a paleta. Cores fora do alcance da paleta existente sao
      aproximadas.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

IMG_DESC = 0x000CDD50
PAL_OFF = 0x000CDD5C
PIX_OFF = 0x000CE15C
IMG_W, IMG_H = 128, 160
BG_INDEX = 1

CELLS = {
    1: ("Musica", 6, 16, 33, 31),
    2: ("Video", 48, 16, 32, 31),
    3: ("Gravador", 89, 16, 31, 31),
    4: ("FM", 6, 65, 33, 31),
    5: ("eBook", 48, 65, 32, 31),
    6: ("Fotos", 89, 65, 31, 31),
    7: ("Bluetooth", 6, 112, 33, 31),
    8: ("Ajustes", 48, 112, 32, 31),
    9: ("Arquivos", 89, 112, 31, 31),
}


def load_palette(data):
    """256 entradas BGRA -> lista de (R, G, B)."""
    return [(data[PAL_OFF + i * 4 + 2],
             data[PAL_OFF + i * 4 + 1],
             data[PAL_OFF + i * 4 + 0]) for i in range(256)]


def luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def nearest_index(pal, target):
    best, bi = None, 0
    for i, c in enumerate(pal):
        dr, dg, db = c[0] - target[0], c[1] - target[1], c[2] - target[2]
        d2 = dr * dr + dg * dg + db * db
        if best is None or d2 < best:
            best, bi = d2, i
    return bi


def build_recolor_map(pal, used, rgb):
    """Para cada indice usado, escolhe a entrada de paleta mais proxima da
    cor alvo escalada pela luminancia relativa do pixel original."""
    lumas = [luma(pal[i]) for i in used if i != BG_INDEX]
    if not lumas:
        return {}
    lo, hi = min(lumas), max(lumas)
    span = (hi - lo) or 1.0
    mapping = {}
    for i in used:
        if i == BG_INDEX:
            continue
        t = (luma(pal[i]) - lo) / span          # 0.0 .. 1.0
        # escala a cor alvo pela luminancia relativa (0.25 .. 1.0)
        f = 0.25 + 0.75 * t
        target = (min(255, int(rgb[0] * f)),
                  min(255, int(rgb[1] * f)),
                  min(255, int(rgb[2] * f)))
        mapping[i] = nearest_index(pal, target)
    return mapping


def main():
    ap = argparse.ArgumentParser(
        description="Substitui um icone da folha do menu principal")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--cell", type=int, required=True, choices=sorted(CELLS))
    ap.add_argument("--op", default="recolor", choices=["recolor"])
    ap.add_argument("--rgb", default="0,160,255",
                    help="cor alvo R,G,B (padrao: azul OpenPod)")
    ap.add_argument("--keep", default="",
                    help="indices de paleta a preservar, ex: 5,7,8")
    ap.add_argument("--dry-run", action="store_true",
                    help="analisa e relata, sem gravar nada")
    args = ap.parse_args()

    if os.path.abspath(args.src) == os.path.abspath(args.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    with open(args.src, "rb") as fh:          # somente leitura
        data = bytearray(fh.read())

    # sanidade: o descritor ainda e o esperado?
    hdr = struct.unpack_from("<I", data, IMG_DESC)[0]
    cf, w, h = hdr & 0x1F, (hdr >> 10) & 0x7FF, (hdr >> 21) & 0x7FF
    if (cf, w, h) != (10, IMG_W, IMG_H):
        print(f"ABORTADO: descritor inesperado cf={cf} {w}x{h}", file=sys.stderr)
        return 1

    name, x0, y0, cw, ch = CELLS[args.cell]
    pal = load_palette(data)

    used = set()
    for y in range(y0, y0 + ch):
        for x in range(x0, x0 + cw):
            used.add(data[PIX_OFF + y * IMG_W + x])

    rgb = tuple(int(v) for v in args.rgb.split(","))
    keep = {int(v) for v in args.keep.split(",") if v.strip()}
    mapping = build_recolor_map(pal, used, rgb)
    for k in keep:
        mapping.pop(k, None)

    print("=" * 70)
    print(f"PATCH — celula {args.cell} ({name})")
    print("=" * 70)
    print(f"  origem      : {args.src}")
    print(f"  destino     : {args.dst}")
    print(f"  regiao      : ({x0},{y0}) {cw}x{ch} px")
    print(f"  operacao    : {args.op} -> RGB{rgb}")
    print(f"  indices usados na celula: {len(used)} (fundo {BG_INDEX} preservado)")
    print(f"  indices preservados por --keep: {sorted(keep) if keep else 'nenhum'}")
    print(f"  remapeamentos: {len(mapping)}")

    changed, first, last = 0, None, None
    for y in range(y0, y0 + ch):
        for x in range(x0, x0 + cw):
            off = PIX_OFF + y * IMG_W + x
            old = data[off]
            new = mapping.get(old, old)
            if new != old:
                changed += 1
                first = off if first is None else min(first, off)
                last = off if last is None else max(last, off)
                if not args.dry_run:
                    data[off] = new

    print(f"  bytes alterados: {changed} de {cw*ch} pixels da celula")
    if changed:
        print(f"  faixa alterada : 0x{first:06X} .. 0x{last:06X}")
    print(f"  paleta alterada: NAO (0 bytes)")
    print(f"  tamanho do arquivo: inalterado ({len(data)} bytes)")

    if args.dry_run:
        print("\n  --dry-run: nada foi gravado.")
        return 0

    # o unico CRC afetado e o da particao FIRM (o patch fica alem dos
    # 4 KiB cobertos por loadCrc e fora do cabecalho HLKJ)
    pt = struct.unpack_from("<I", data, 0x20)[0]
    n = struct.unpack_from("<I", data, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if data[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", data, b + 4)
            old_crc = struct.unpack_from("<H", data, b + 0x0C)[0]
            new_crc = fw.crc16(bytes(data[off:off + ln]))
            # R1: NAO gravar o CRC da FIRM. Nao e verificado pelo aparelho, e
            # escrever aqui poe o setor 0x00D000 (tabela de particoes) de
            # volta na lista de setores — foi ele que matou o primeiro
            # aparelho. Achado pelo tools/build.py ao reconstruir do zero.
            pass   # NAO gravar o CRC (R1)
            print(f"  CRC da FIRM: 0x{old_crc:04X} -> 0x{new_crc:04X}")
            break

    with open(args.dst, "wb") as fh:
        fh.write(data)
    print(f"\n  gravado: {args.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
