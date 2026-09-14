#!/usr/bin/env python3
"""
firmware_info.py — Visao geral estrutural de um dump de firmware bruto.

PROPOSITO
    Produz, sem assumir arquitetura ou formato:
      - metadados do arquivo (tamanho, SHA-256)
      - histograma de bytes e bytes dominantes
      - mapa de entropia por bloco
      - classificacao grosseira de cada bloco (vazio / baixa / media / alta entropia)
      - regioes de preenchimento (0x00 e 0xFF) contiguas
      - varredura de magic numbers conhecidos e de magics ASCII repetidos

USO
    python3 tools/firmware_info.py <arquivo.bin> [--block 4096]

DEPENDENCIAS
    Apenas biblioteca padrao do Python 3.

EXEMPLO
    python3 tools/firmware_info.py firmware/WORKING/GN438_analysis.bin --block 4096

LIMITACOES
    - Entropia por bloco e um indicador, nao prova de compressao ou de cifragem.
    - A varredura de magics reporta candidatos; cada ocorrencia precisa ser
      confirmada manualmente antes de virar conclusao.
"""

import argparse
import hashlib
import math
import re
import sys
from collections import Counter

# Magics de formatos comuns. Presenca e apenas um CANDIDATO, nunca prova.
MAGICS = {
    b"\x89PNG\r\n\x1a\n": "PNG",
    b"BM": "BMP (fraco: 2 bytes)",
    b"\xff\xd8\xff": "JPEG SOI",
    b"GIF87a": "GIF87a",
    b"GIF89a": "GIF89a",
    b"\x1f\x8b\x08": "gzip",
    b"PK\x03\x04": "ZIP local header",
    b"\xfd7zXZ\x00": "XZ",
    b"]\x00\x00": "LZMA (fraco)",
    b"\x04\x22\x4d\x18": "LZ4 frame",
    b"hsqs": "SquashFS LE",
    b"sqsh": "SquashFS BE",
    b"UBI#": "UBI",
    b"\x85\x19": "JFFS2 (fraco)",
    b"\x7fELF": "ELF",
    b"ID3": "ID3 tag (MP3)",
    b"RIFF": "RIFF (WAV/AVI)",
    b"\x00\x00\x01\xba": "MPEG-PS",
    b"\x00\x00\x01\xb3": "MPEG video seq",
    b"OggS": "Ogg",
    b"fLaC": "FLAC",
    b"\xef\xbb\xbf": "UTF-8 BOM",
    b"\x55\xaa": "boot signature (fraco)",
}


def entropy(data: bytes) -> float:
    """Entropia de Shannon em bits/byte (0.0 a 8.0)."""
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def classify(block: bytes, ent: float) -> str:
    uniq = len(set(block))
    if uniq == 1:
        return f"FILL 0x{block[0]:02X}"
    if ent < 1.0:
        return "quase-vazio"
    if ent < 4.0:
        return "baixa"
    if ent < 6.5:
        return "media"
    if ent < 7.5:
        return "alta"
    return "muito alta"


def fill_runs(data: bytes, byte_val: int, min_len: int):
    """Sequencias contiguas de um mesmo byte com tamanho >= min_len."""
    pattern = re.compile(bytes([byte_val]) + b"{" + str(min_len).encode() + b",}")
    return [(m.start(), m.end() - m.start()) for m in pattern.finditer(data)]


def scan_magics(data: bytes):
    hits = {}
    for magic, name in MAGICS.items():
        offs = []
        start = 0
        while True:
            i = data.find(magic, start)
            if i < 0:
                break
            offs.append(i)
            start = i + 1
            if len(offs) > 5000:
                break
        if offs:
            hits[name] = offs
    return hits


def scan_ascii_tags(data: bytes, min_count: int = 2):
    """Tags ASCII de 4 bytes em offsets alinhados a 4, que se repetem no dump.

    Util para achar cabecalhos de particao/registro proprietarios sem
    assumir nenhum formato conhecido.
    """
    counter = Counter()
    for off in range(0, len(data) - 4, 4):
        tag = data[off:off + 4]
        if all(0x41 <= b <= 0x5A or 0x61 <= b <= 0x7A for b in tag):
            counter[tag] += 1
    return [(t, c) for t, c in counter.most_common(40) if c >= min_count]


def main():
    ap = argparse.ArgumentParser(description="Visao geral estrutural de firmware bruto")
    ap.add_argument("path")
    ap.add_argument("--block", type=int, default=4096, help="tamanho do bloco de entropia")
    ap.add_argument("--no-map", action="store_true", help="omite o mapa bloco a bloco")
    args = ap.parse_args()

    with open(args.path, "rb") as fh:
        data = fh.read()

    print("=" * 78)
    print("ARQUIVO")
    print("=" * 78)
    print(f"  path      : {args.path}")
    print(f"  size      : {len(data)} bytes (0x{len(data):X})")
    print(f"  sha256    : {hashlib.sha256(data).hexdigest()}")
    print(f"  entropia  : {entropy(data):.4f} bits/byte (global)")

    print()
    print("=" * 78)
    print("HISTOGRAMA — 12 bytes mais frequentes")
    print("=" * 78)
    total = len(data)
    for val, cnt in Counter(data).most_common(12):
        print(f"  0x{val:02X}  {cnt:>9}  {100.0 * cnt / total:6.2f}%")

    print()
    print("=" * 78)
    print(f"REGIOES DE PREENCHIMENTO (runs >= 1024 bytes)")
    print("=" * 78)
    for bv in (0x00, 0xFF):
        runs = fill_runs(data, bv, 1024)
        tot = sum(l for _, l in runs)
        print(f"  byte 0x{bv:02X}: {len(runs)} run(s), {tot} bytes ({100.0*tot/total:.2f}%)")
        for off, ln in sorted(runs, key=lambda r: -r[1])[:10]:
            print(f"      0x{off:08X} .. 0x{off+ln-1:08X}  ({ln} bytes)")

    print()
    print("=" * 78)
    print("MAGIC NUMBERS CANDIDATOS")
    print("=" * 78)
    hits = scan_magics(data)
    if not hits:
        print("  nenhum")
    for name, offs in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        head = ", ".join(f"0x{o:08X}" for o in offs[:8])
        more = f" ... (+{len(offs)-8})" if len(offs) > 8 else ""
        print(f"  {name:<28} {len(offs):>5}x  {head}{more}")

    print()
    print("=" * 78)
    print("TAGS ASCII DE 4 BYTES ALINHADAS (candidatas a header proprietario)")
    print("=" * 78)
    tags = scan_ascii_tags(data)
    if not tags:
        print("  nenhuma")
    for tag, cnt in tags:
        print(f"  {tag.decode('ascii'):<8} {cnt:>6}x")

    if not args.no_map:
        print()
        print("=" * 78)
        print(f"MAPA DE ENTROPIA (blocos de {args.block} bytes, agrupado por classe)")
        print("=" * 78)
        bs = args.block
        cur_cls, cur_start, ents = None, 0, []
        def flush(end):
            if cur_cls is None:
                return
            avg = sum(ents) / len(ents)
            print(f"  0x{cur_start:08X} .. 0x{end-1:08X}  {end-cur_start:>8} bytes  "
                  f"ent~{avg:4.2f}  {cur_cls}")
        for off in range(0, len(data), bs):
            blk = data[off:off + bs]
            e = entropy(blk)
            c = classify(blk, e)
            if c != cur_cls:
                flush(off)
                cur_cls, cur_start, ents = c, off, [e]
            else:
                ents.append(e)
        flush(len(data))

    print()


if __name__ == "__main__":
    sys.exit(main())
