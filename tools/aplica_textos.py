#!/usr/bin/env python3
"""
aplica_textos.py — Aplica as propostas de `tools/propoe_textos.py`.

Reusa o MESMO dicionario da ferramenta de proposta, entao o que voce leu
em `docs/TEXTOS_REVISAO.md` e exatamente o que e gravado.

MECANISMO

    Nunca edita string no lugar. Cada texto novo vai para a area livre e
    o ponteiro da tabela de idioma e repontado. A regra existe porque
    varios ponteiros apontam para o MEIO de strings maiores:

        0x00C5537C  "video" (pt 3) e a cauda de "Reproducao de video"

    Sobrescrever mudaria as duas.

    A tabela do portugues foi realocada para a area livre no V021, entao
    a base e lida do pool de `get_string` (0x00121104), nunca fixa.

USO
    python3 tools/aplica_textos.py \\
        --in  firmware/WORKING/GN438_openpod_v051.bin \\
        --out firmware/WORKING/GN438_openpod_v052.bin [--dry-run]

ENDERECO EXPLICITO (--em)

    Por padrao esta ferramenta ALOCAVA sozinha na area livre, o que fazia
    o endereco depender de tudo que rodou antes. Com `--em 0x1A3600` quem
    chama declara onde. Ver `tools/build.py` para o motivo.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from propoe_textos import P

XIP = 0x00C00000
POOL_PT = 0x00121104
TBL, CMAP, N_GLIFOS = 0x00086C44, 0x000A27E6, 7098
LIVRE_INI, LIVRE_FIM = 0x001A3038, 0x001FC000
LIM = 113
PROIBIDO = 0x0000D000


def main():
    ap = argparse.ArgumentParser(description="Aplica a revisao dos textos")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", type=lambda x: int(x, 0), default=None,
                    help="endereco EXPLICITO das strings novas")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2
    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — revisao dos textos em portugues")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    base = struct.unpack_from("<I", d, POOL_PT)[0] - XIP
    cmap = struct.unpack_from("<%dH" % N_GLIFOS, d, CMAP)
    idx = {c: i for i, c in enumerate(cmap)}

    def w(t):
        return sum(struct.unpack_from("<I", d, TBL + idx[ord(c)] * 16 + 4)[0]
                   for c in t.split("\n")[0])

    faltando = []
    for i, t in P.items():
        for c in t:
            if c != "\n" and ord(c) not in idx and c not in faltando:
                faltando.append(c)
    if faltando:
        print(f"  ABORTADO: caracteres fora da fonte: {faltando}", file=sys.stderr)
        return 1
    print(f"  tabela pt viva: 0x{base + XIP:08X}")
    print(f"  {len(P)} textos a trocar, todos com glifo na fonte  OK\n")

    if a.em is not None:
        cur = a.em
    else:
        cur = LIVRE_INI
        for i in range(LIVRE_INI, LIVRE_INI + 0x8000):
            if d[i] != 0xFF:
                cur = i + 1
        cur = (cur + 3) & ~3
    print(f"  area livre a partir de 0x{cur:06X}\n")

    antes_cabe = depois_cabe = 0
    for i in range(216):
        p = struct.unpack_from("<I", d, base + i * 4)[0] - XIP
        e = d.find(b"\0", p)
        if e < 0 or e - p > 200:
            continue
        s = d[p:e].decode("utf-8", "replace")
        if w(s) <= LIM:
            antes_cabe += 1

    trocados = []
    for i, t in sorted(P.items()):
        p = struct.unpack_from("<I", d, base + i * 4)[0] - XIP
        e = d.find(b"\0", p)
        antigo = d[p:e].decode("utf-8", "replace")
        blob = t.encode("utf-8") + b"\0"
        if cur + len(blob) > LIVRE_FIM:
            print("  ABORTADO: nao cabe na area livre.", file=sys.stderr)
            return 1
        if any(b != 0xFF for b in d[cur:cur + len(blob)]):
            print(f"  ABORTADO: 0x{cur:06X} nao esta virgem.", file=sys.stderr)
            return 1
        d[cur:cur + len(blob)] = blob
        struct.pack_into("<I", d, base + i * 4, cur + XIP)
        trocados.append((i, antigo, t, cur))
        cur = (cur + len(blob) + 3) & ~3

    ruim = 0
    for i, antigo, t, end in trocados:
        p = struct.unpack_from("<I", d, base + i * 4)[0] - XIP
        e = d.find(b"\0", p)
        if d[p:e].decode("utf-8") != t:
            ruim += 1
    if ruim:
        print(f"  ABORTADO: {ruim} textos divergem na releitura.", file=sys.stderr)
        return 1
    print(f"  conferencia: {len(trocados)} textos relidos pelo ponteiro, "
          "todos iguais  OK\n")

    for i in range(216):
        p = struct.unpack_from("<I", d, base + i * 4)[0] - XIP
        e = d.find(b"\0", p)
        if e < 0 or e - p > 200:
            continue
        if w(d[p:e].decode("utf-8", "replace")) <= LIM:
            depois_cabe += 1
    print(f"  cabem em {LIM} px: {antes_cabe} -> {depois_cabe}\n")

    print("  AMOSTRA (os que voce ve todo dia)")
    for i in (8, 37, 40, 87, 97, 103, 104, 144, 195):
        for j, antigo, t, end in trocados:
            if j == i:
                print(f"    id {i:>3}  {antigo!r:<28} -> {t!r}")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}")
    print("    " + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido.", file=sys.stderr)
        return 1
    print("  tabela de particoes NAO tocada   OK\n")
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
