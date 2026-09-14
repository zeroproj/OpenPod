#!/usr/bin/env python3
"""
patch_saturno_s12.py — SATURNO S12: fundo pintado com o campo de fundo.

O DEFEITO

    A pagina 0x18 (Gravacao) tem 2 objetos cujo fundo do estado normal e
    BRANCO, gritando no tema escuro.

    Eu havia anotado isso como "bug que a V013 causou". **Estava errado.**
    Fui ao firmware de fabrica conferir, como o mantenedor pediu que se
    fizesse sempre, e la o getter ja era:

        ORIGINAL 0x00121384:  mov.w r0, #-1   ; branco

    Ou seja: o branco e de fabrica. A V013 nao mexeu nisso.

    O problema real e outro, e e estrutural: `0x00122F5A` pinta
    **BG_COLOR** (prop 32) usando o getter de **cor de TEXTO**. E o mesmo
    getter que o S10 ligou em `cor_texto`. Resultado: mexer na cor do
    texto do aparelho mexeria no fundo desse objeto. Duas coisas
    diferentes presas no mesmo campo — exatamente o que o Saturno existe
    para desfazer.

O QUE FAZ

    Esse ponto passa a ler `cor_tela` (+0x00) da tabela, que e o campo do
    fundo. Os outros dois estados do mesmo objeto NAO sao tocados:

        LV_PART_SELECTED (0x40000)  palette(7)   <- selecao, ja padronizada
        foco (seletor 4)            palette(0xE) <- estado, nao padronizacao

USO
    python3 tools/patch_saturno_s12.py \\
        --in  firmware/WORKING/GN438_openpod_v071.bin \\
        --out firmware/WORKING/GN438_openpod_v072.bin [--dry-run]

SEGURANCA
    - exige encontrar no ponto exatamente `bl 0x00D21384` seguido do
      `bl` de BG_COLOR com seletor 0; se o padrao nao bater, RECUSA;
    - confere a rotina montada COM OPERANDOS, sem filtrar literais;
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

GETTER_TEXTO = 0xD21384
SET_BG_COLOR = 0xD4D092
PONTO = 0x00122F50          # bl GETTER_TEXTO, cujo valor vira BG_COLOR
PONTO_BG = 0x00122F5A       # bl SET_BG_COLOR logo abaixo

TAB = 0x00DA5400
OFS_COR_TELA = 0x00

BLOB = 0x001A5A20
BLOB_MAX = 0x20


def bl(origem, destino):
    off = destino - (origem + 4)
    if off & 1 or not (-(1 << 24) <= off < (1 << 24)):
        raise ValueError("fora de alcance")
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = (0xD000 | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11)
           | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def monta(base):
    c = bytearray()
    p = len(c)
    c += b"\0\0"                                        # ldr  r0, =TAB
    c += struct.pack("<H", 0x8800 | (OFS_COR_TELA << 5))  # ldrh r0, [r0, #0]
    c += struct.pack("<H", 0x4770)                      # bx   lr
    while len(c) % 4:
        c += struct.pack("<H", 0xBF00)
    lit = len(c)
    c += struct.pack("<I", TAB)
    struct.pack_into("<H", c, p,
                     0x4800 | (((base + lit) - ((base + p + 4) & ~3)) >> 2))
    return bytes(c)


ESPERADO = ["ldr r0, [pc, #4]", "ldrh r0, [r0]", "bx lr"]


def main():
    ap = argparse.ArgumentParser(description="Saturno S12: fundo da 0x18")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
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

    def alvo(off):
        k = next(md.disasm(bytes(data[off:off + 4]), off + XIP), None)
        if k and k.mnemonic in ("bl", "b.w") and k.op_str.startswith("#"):
            return int(k.op_str.strip("#"), 0)
        return None

    erros = []
    if alvo(PONTO) != GETTER_TEXTO:
        erros.append(f"0x{PONTO:06X} nao chama o getter de texto "
                     f"(achei 0x{(alvo(PONTO) or 0):06X})")
    if alvo(PONTO_BG) != SET_BG_COLOR:
        erros.append(f"0x{PONTO_BG:06X} nao e BG_COLOR — o padrao mudou")
    if any(v != 0xFF for v in data[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB:06X} nao esta virgem")

    rot = monta(BLOB + XIP)
    got = [f"{i.mnemonic} {i.op_str}".strip()
           for i in md.disasm(rot, BLOB + XIP)][:len(ESPERADO)]
    if got != ESPERADO:
        erros.append(f"rotina nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for e in erros:
            print("   -", e)
        return 1

    cor = struct.unpack_from("<H", data, 0x001A5400 + OFS_COR_TELA)[0]
    print()
    print("  SATURNO S12 — o fundo passa a vir do campo de fundo")
    print()
    print(f"  antes:  BG_COLOR <- getter de TEXTO (0x{GETTER_TEXTO - XIP:06X})")
    print(f"  agora:  BG_COLOR <- cor_tela da tabela = 0x{cor:04X}")
    print()
    print("  ALTERACOES")
    data[BLOB:BLOB + len(rot)] = rot
    print(f"    0x{BLOB:06X}  cor_tela {len(rot)} B")
    data[PONTO:PONTO + 4] = bl(PONTO + XIP, BLOB + XIP)
    print(f"    0x{PONTO:06X}  pagina 0x18 -> cor_tela")
    print()
    print("  NAO tocados (estados, nao padronizacao):")
    print("    0x00122F4C  LV_PART_SELECTED -> palette(7)")
    print("    0x00122F6A  foco             -> palette(0xE)")
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
