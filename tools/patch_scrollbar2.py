#!/usr/bin/env python3
"""
patch_scrollbar2.py — Esconde a barra de rolagem da home DE VERDADE.

POR QUE A V034 NAO BASTOU

    A V034 limpou `LV_OBJ_FLAG_SCROLLABLE` (0x10) do conteiner. Gravada
    no aparelho, a linha vertical **continuou**. Ou seja: nesta LVGL o
    desenho da barra nao depende dessa flag.

    A correcao certa e deixar a **parte scrollbar** transparente. O
    proprio firmware ja usa seletores de parte, o que confirma o mapa de
    constantes da LVGL v8 sem precisar supor:

        0x00010000  LV_PART_SCROLLBAR   (1 chamada, em 0x00D29CC8)
        0x00020000  LV_PART_INDICATOR   (7)
        0x00040000  LV_PART_SELECTED    (9)
        0x00050000  LV_PART_ITEMS       (1)

    E a codificacao de `mov.w r2, #0x10000` e copiada literalmente de
    0x00D29CC0 -- do proprio firmware, nao gerada por mim.

O QUE MUDA

    So o corpo da rotina que ja existe na area livre (0x00DA3400). O
    gancho em 0x0012EC0E continua apontando para ela; nada mais muda.

        push  {r0, lr}
        bl    set_size            ; chamada original
        ldr   r0, [sp]
        movs  r1, #0x10
        bl    clear_flag          ; impede a rolagem em si
        ldr   r0, [sp]
        movs  r1, #0
        mov.w r2, #0x10000        ; LV_PART_SCROLLBAR
        bl    set_style_bg_opa    ; barra invisivel
        pop   {r0, pc}

    Um setor: 0x001A3000.

USO
    python3 tools/patch_scrollbar2.py \
        --in  firmware/WORKING/GN438_openpod_v035.bin \
        --out firmware/WORKING/GN438_openpod_v036.bin [--dry-run]

SEGURANCA
    - recusa se a rotina da V034 nao estiver exatamente onde se espera;
    - recusa se o espaco extra nao estiver virgem;
    - copia a codificacao de mov.w do proprio firmware e confere;
    - decodifica de volta os tres `bl` e compara os alvos;
    - recusa se algum setor alterado for <= 0x00D000.
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
ROT = 0x001A3400
SET_SIZE = 0x00D4A21A
CLEAR_FLAG = 0x00D4924A
BG_OPA = 0x00D4D0B4
SCROLLABLE = 0x10
MOVW_FONTE = 0x00129CC0          # `mov.w r2, #0x10000` no proprio firmware
PART_SCROLLBAR = 0x00010000
PROIBIDO = 0x0000D000

ATUAL = bytes.fromhex("01b5") + b"\x00" * 0          # so o inicio e conferido


def enc_bl(origem, destino):
    off = destino - (origem + 4)
    if not -(1 << 24) <= off < (1 << 24) or off & 1:
        raise ValueError("fora de alcance")
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack("<HH", 0xF000 | (s << 10) | ((off >> 12) & 0x3FF),
                       0xD000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF))


def dec_bl(origem, blob):
    h1, h2 = struct.unpack("<HH", blob)
    s = (h1 >> 10) & 1
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if s:
        off -= 1 << 25
    return origem + 4 + off


def main():
    ap = argparse.ArgumentParser(description="Barra de rolagem invisivel")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — barra de rolagem invisivel (LV_PART_SCROLLBAR)")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    erros = []
    if bytes(d[ROT:ROT + 2]) != bytes.fromhex("01b5"):
        erros.append(f"0x{ROT:06X} nao comeca com push {{r0, lr}}")
    if dec_bl(ROT + XIP + 2, bytes(d[ROT + 2:ROT + 6])) != SET_SIZE:
        erros.append("a rotina nao chama set_size no inicio")
    if any(b != 0xFF for b in d[ROT + 0x10:ROT + 0x30]):
        erros.append("nao ha espaco virgem para estender a rotina")
    movw = bytes(d[MOVW_FONTE:MOVW_FONTE + 4])
    if movw != bytes.fromhex("4ff48032"):
        erros.append(f"0x{MOVW_FONTE:06X} nao e o mov.w esperado "
                     f"(tem {movw.hex()})")
    if erros:
        print("  ABORTADO — a entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print(f"  rotina da V034 encontrada em 0x{ROT:06X}  OK")
    print(f"  mov.w r2,#0x10000 copiado de 0x{MOVW_FONTE:06X}: {movw.hex()}  OK")
    print()

    c = bytearray()
    c += struct.pack("<H", 0xB501)                     # push {r0, lr}
    c += enc_bl(ROT + XIP + len(c), SET_SIZE)          # bl set_size
    c += struct.pack("<H", 0x9800)                     # ldr r0, [sp]
    c += struct.pack("<H", 0x2100 | SCROLLABLE)        # movs r1, #0x10
    c += enc_bl(ROT + XIP + len(c), CLEAR_FLAG)        # bl clear_flag
    c += struct.pack("<H", 0x9800)                     # ldr r0, [sp]
    c += struct.pack("<H", 0x2100)                     # movs r1, #0
    c += movw                                          # mov.w r2, #0x10000
    c += enc_bl(ROT + XIP + len(c), BG_OPA)            # bl set_style_bg_opa
    c += struct.pack("<H", 0xBD01)                     # pop {r0, pc}
    d[ROT:ROT + len(c)] = c

    print("  ROTINA NOVA")
    desc = [(0x00, 2, "push  {r0, lr}", ""),
            (0x02, 4, "bl    0x%08X" % SET_SIZE, "set_size original"),
            (0x06, 2, "ldr   r0, [sp]", ""),
            (0x08, 2, "movs  r1, #0x10", "LV_OBJ_FLAG_SCROLLABLE"),
            (0x0A, 4, "bl    0x%08X" % CLEAR_FLAG, "impede a rolagem"),
            (0x0E, 2, "ldr   r0, [sp]", ""),
            (0x10, 2, "movs  r1, #0", "opacidade 0"),
            (0x12, 4, "mov.w r2, #0x10000", "LV_PART_SCROLLBAR"),
            (0x16, 4, "bl    0x%08X" % BG_OPA, "barra invisivel"),
            (0x1A, 2, "pop   {r0, pc}", "")]
    for off, n, asm, com in desc:
        print(f"    +0x{off:02X}  {bytes(c[off:off+n]).hex():<8}  {asm:<22}"
              + (f"; {com}" if com else ""))
    print()

    ok = True
    for off, alvo, nome in ((0x02, SET_SIZE, "set_size"),
                            (0x0A, CLEAR_FLAG, "clear_flag"),
                            (0x16, BG_OPA, "set_style_bg_opa")):
        got = dec_bl(ROT + XIP + off, bytes(c[off:off + 4]))
        print(f"    bl {nome:<18} -> 0x{got:08X}  "
              f"{'OK' if got == alvo else 'ERRADO'}")
        ok &= got == alvo
    if not ok:
        print("  ABORTADO: codificacao nao confere.", file=sys.stderr)
        return 1
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido.", file=sys.stderr)
        return 1
    print(f"  tabela de particoes (0x{PROIBIDO:06X}) NAO tocada   OK")
    print("  o gancho em 0x0012EC0E nao muda: continua apontando para a rotina")
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
