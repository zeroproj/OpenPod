#!/usr/bin/env python3
"""
varre_divisores.py — Padroniza a altura da linha em TODAS as listas do
                     sistema, ajustando o que ja existe.

A IDEIA

    Nao reescrever a GUI: ajustar a constante que o proprio firmware ja
    usa. Toda tela de lista chama o criador de linha 0x00D21764 e logo em
    seguida calcula

        altura = lv_disp_get_ver_res() / divisor

    Com divisor 7 a linha tem 22 px. Com 10 tem 16 px -- o passo da home.
    E um byte por tela.

COMO ENCONTRA

    1. acha todas as chamadas a 0x00D21764 (padrao de bits do BL);
    2. em cada uma, procura o `sdiv` seguinte;
    3. volta ate a ultima escrita do registrador divisor, aceitando
       `movs rX, #imm` (2 B) e `mov.w rX, #imm` (4 B);
    4. so troca se o valor for exatamente o esperado.

    Telas com outro divisor sao DEIXADAS EM PAZ e reportadas. Uma delas
    usa 13 (linha de 12 px): subir para 16 poderia estourar a lista.

USO
    python3 tools/varre_divisores.py \
        --in  firmware/WORKING/GN438_openpod_v040.bin \
        --out firmware/WORKING/GN438_openpod_v041.bin \
        [--de 7] [--para 10] [--dry-run]

SEGURANCA
    - so troca onde o valor atual e exatamente `--de`;
    - confere relendo cada byte alterado;
    - lista o que NAO foi tocado e por que;
    - recusa se algum setor alterado for <= 0x00D000.
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
ROW = 0x00D21764
FIRM_INI, FIRM_FIM = 0x0000E000, 0x001A0570
PROIBIDO = 0x0000D000


def dec_bl(ad, h1, h2):
    s = (h1 >> 10) & 1
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if s:
        off -= 1 << 25
    return ad + 4 + off


def acha_divisor(d, ini, fim):
    """Procura `sdiv rD, rN, rM` e a ultima escrita imediata de rM."""
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    escritas = {}
    for i in md.disasm(d[ini:fim], ini + XIP):
        if i.mnemonic == "movs" and "#" in i.op_str:
            r = i.op_str.split(",")[0].strip()
            try:
                escritas[r] = (i.address - XIP, int(i.op_str.split("#")[1], 0), 2)
            except ValueError:
                pass
        elif i.mnemonic in ("mov.w", "movw") and "#" in i.op_str:
            r = i.op_str.split(",")[0].strip()
            try:
                escritas[r] = (i.address - XIP, int(i.op_str.split("#")[1], 0), 4)
            except ValueError:
                pass
        elif i.mnemonic == "sdiv":
            partes = [p.strip() for p in i.op_str.split(",")]
            if len(partes) == 3 and partes[2] in escritas:
                return escritas[partes[2]]
            return None
    return None


def main():
    ap = argparse.ArgumentParser(
        description="Padroniza a altura da linha em todas as listas")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--de", type=int, default=7)
    ap.add_argument("--para", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — altura da linha padronizada em todas as listas")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}")
    print(f"  divisor {a.de} -> {a.para}   "
          f"(linha {160 // a.de} px -> {160 // a.para} px)\n")

    chamadas = []
    for ad in range(FIRM_INI, FIRM_FIM - 4, 2):
        h1, h2 = struct.unpack_from("<HH", d, ad)
        if (h1 & 0xF800) == 0xF000 and (h2 & 0xD000) == 0xD000:
            if dec_bl(ad + XIP, h1, h2) == ROW:
                chamadas.append(ad)
    print(f"  telas que usam o criador de linha 0x{ROW:08X}: {len(chamadas)}\n")

    trocados, pulados = [], []
    for c in chamadas:
        r = acha_divisor(d, c, min(c + 0x80, len(d)))
        if r is None:
            pulados.append((c, None, "sem sdiv/divisor identificavel"))
            continue
        off, val, tam = r
        if val != a.de:
            pulados.append((c, val, f"divisor {val}, nao e {a.de}"))
            continue
        if tam == 2:
            d[off] = a.para                      # movs: imediato no byte baixo
        else:
            if val > 0xFF or a.para > 0xFF:
                pulados.append((c, val, "mov.w com imediato codificado"))
                continue
            d[off + 2] = a.para                  # mov.w: imediato em +2
        trocados.append((c, off, tam))

    print(f"  {'chamada':<11}{'divisor':<12}{'forma':<9}")
    print("  " + "-" * 34)
    for c, off, tam in trocados:
        print(f"  0x{c:06X}   0x{off:06X}    "
              f"{'movs' if tam == 2 else 'mov.w'}")
    print("  " + "-" * 34)
    print(f"  TROCADOS: {len(trocados)}\n")

    if pulados:
        print("  NAO TOCADOS (de proposito):")
        for c, val, por in pulados:
            print(f"    0x{c:06X}   {por}")
        print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    if len(dif) != len(trocados):
        print(f"  ABORTADO: {len(dif)} bytes mudaram mas "
              f"{len(trocados)} trocas foram pedidas.", file=sys.stderr)
        return 1
    for i in dif:
        if d[i] != a.para:
            print(f"  ABORTADO: 0x{i:06X} ficou {d[i]}, esperado {a.para}.",
                  file=sys.stderr)
            return 1
    print(f"  conferencia: {len(dif)} bytes, todos com valor {a.para}  OK")

    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  setores: {len(secs)}")
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
