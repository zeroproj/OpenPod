#!/usr/bin/env python3
"""
patch_saturno_s8.py — SATURNO S8: o recuo do texto da linha vira tabela.

O QUE SOBRAVA

    Medi a borda esquerda do texto de cada linha, em vez de supor:

        41 rotulos   sem align  -> ficam na origem da linha, x = 0
         4 rotulos   align=7 (LEFT_MID) com x_ofs = 13  <- espaco do icone
        19 objetos   align=8 (RIGHT_MID)   -> VALOR a direita, legitimo

    A home, que e a regua, poe seus rotulos em **x = 0** (tabela
    `0x00C486A0`). Ou seja: 41 telas e a home concordam, e 4 divergem — e
    divergem justamente pelo espaco de um icone que o S7 acabou de
    esconder. Ficaria um recuo de 13 px com nada dentro.

    **Os 19 `align=8` NAO sao ruido** e nao sao tocados: telas com valor
    ou interruptor a direita precisam mesmo disso.

O QUE FAZ

    Os 4 pontos passam por uma rotina que decide o `x_ofs` pela tabela:

        icones != 0  ->  mantem o x_ofs original (o espaco volta sozinho)
        icones == 0  ->  usa o campo `margem`

    `margem` passa a valer **0**, que e o valor da home. Ligar os icones
    de novo (`--icones 1` no S7) devolve o recuo sem tocar em codigo.

USO
    python3 tools/patch_saturno_s8.py \\
        --in  firmware/WORKING/GN438_openpod_v066.bin \\
        --out firmware/WORKING/GN438_openpod_v067.bin [--dry-run]

SEGURANCA
    - localiza os pontos pelos ARGUMENTOS (align=7, x_ofs=13) dentro de
      telas que criam linha, nao por endereco fixo;
    - recusa se nenhum ponto for achado, ou se algum ja estiver desviado;
    - confere a rotina montada com operandos;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.
"""

import argparse
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
FLASH_SIZE = 0x200000

ALIGN = 0xD4A3A2
CRIA_LINHA = 0xD21764
TAB = 0x00DA5400
TAB_OFF = 0x001A5400
OFS_MARGEM, OFS_ICONES = 0x0F, 0x12

ALIGN_ESQ, X_ICONE = 7, 13

BLOB = 0x001A5880
BLOB_MAX = 0x60


def bl(origem, destino, link=True):
    off = destino - (origem + 4)
    if off & 1 or not (-(1 << 24) <= off < (1 << 24)):
        raise ValueError("fora de alcance")
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = ((0xD000 if link else 0x9000)
           | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def monta(base):
    c = bytearray()

    def h(*hw):
        for x in hw:
            c.extend(struct.pack("<H", x))

    h(0xB538)                    # push {r3, r4, r5, lr}
    pos_lit = len(c)
    h(0x0000)                    # ldr r4, =TAB
    h(0x7CA5)                    # ldrb r5, [r4, #0x12]   icones
    h(0x2D00)                    # cmp  r5, #0
    o_bne = len(c)
    h(0x0000)                    # bne  fim
    h(0x7BE2)                    # ldrb r2, [r4, #0x0F]   margem
    fim = len(c)
    c.extend(bl(base + len(c), ALIGN))
    h(0xBD38)                    # pop {r3, r4, r5, pc}
    struct.pack_into("<H", c, o_bne, 0xD100 | (((fim - (o_bne + 4)) >> 1) & 0xFF))
    while len(c) % 4:
        h(0xBF00)
    lit = len(c)
    c.extend(struct.pack("<I", TAB))
    pc = (base + pos_lit + 4) & ~3
    struct.pack_into("<H", c, pos_lit, 0x4C00 | (((base + lit) - pc) >> 2))
    return bytes(c)


ESPERADO = ["push {r3, r4, r5, lr}", "ldrb r5, [r4, #0x12]", "cmp r5, #0",
            "bne #", "ldrb r2, [r4, #0xf]", "bl #0xd4a3a2",
            "pop {r3, r4, r5, pc}"]


def main():
    ap = argparse.ArgumentParser(description="Saturno S8: recuo do texto")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--margem", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.src == a.dst:
        sys.exit("origem e destino iguais")
    with open(a.src, "rb") as fh:
        orig = fh.read()
    if len(orig) != FLASH_SIZE:
        sys.exit(f"tamanho inesperado: {len(orig)}")
    data = bytearray(orig)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    def ins(x):
        try:
            return next(md.disasm(data[x - XIP:x - XIP + 4], x), None)
        except Exception:
            return None

    telas_lista = set()
    for x in range(0xD20000, 0xD40000, 2):
        k = ins(x)
        if (k and k.mnemonic == "bl" and k.op_str.startswith("#")
                and int(k.op_str.strip("#"), 0) == CRIA_LINHA):
            telas_lista.add(x // 0x2000)

    sites = []
    for x in range(0xD20000, 0xD40000, 2):
        k = ins(x)
        if not (k and k.mnemonic == "bl" and k.op_str.startswith("#")):
            continue
        if int(k.op_str.strip("#"), 0) != ALIGN:
            continue
        v = {}
        for b in range(x - 16, x, 2):
            j = ins(b)
            if j and j.mnemonic == "movs" and ", #" in j.op_str:
                r, val = j.op_str.split(", #")
                if r in ("r1", "r2"):
                    v[r] = int(val, 0)
        if v.get("r1") == ALIGN_ESQ and v.get("r2") == X_ICONE:
            sites.append(x)

    erros = []
    if not sites:
        erros.append(f"nenhum align={ALIGN_ESQ} com x_ofs={X_ICONE} encontrado")
    if any(vv != 0xFF for vv in data[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB:06X} nao esta virgem")
    if data[TAB_OFF + OFS_ICONES] == 0xFF:
        erros.append("o campo `icones` da tabela nao existe — rode o S7 antes")

    rot = monta(BLOB + XIP)
    got = [f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(rot, BLOB + XIP)]
    got = [g for g in got if "[pc" not in g][:len(ESPERADO)]
    ok = len(got) == len(ESPERADO) and all(
        g.startswith(e) if e.endswith("#") else g == e
        for g, e in zip(got, ESPERADO))
    if not ok:
        erros.append(f"rotina nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print("  SATURNO S8 — o recuo do texto vem da tabela")
    print()
    print(f"  pontos com align={ALIGN_ESQ} (LEFT_MID) e x_ofs={X_ICONE}: "
          f"{len(sites)}")
    for x in sites:
        print(f"     0x{x - XIP:06X}")
    print()
    print(f"  margem = {a.margem}   (a home poe seus rotulos em x=0)")
    print("  icones != 0 -> o x_ofs original volta sozinho, sem tocar codigo")
    print("  os 19 align=8 (valor a direita) NAO sao tocados")
    print()
    print("  ALTERACOES")
    data[TAB_OFF + OFS_MARGEM] = a.margem
    print(f"    0x{TAB_OFF + OFS_MARGEM:06X}  margem = {a.margem}")
    data[BLOB:BLOB + len(rot)] = rot
    print(f"    0x{BLOB:06X}  rotina {len(rot)} B")
    for x in sites:
        data[x - XIP:x - XIP + 4] = bl(x, BLOB + XIP)
    print(f"    {len(sites)} ganchos -> a rotina")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X} (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}  "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print("  CRC da FIRM: campo intocado (R1)")
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as fh:
        fh.write(data)
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
