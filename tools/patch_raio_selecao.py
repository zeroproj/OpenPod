#!/usr/bin/env python3
"""
patch_raio_selecao.py — Tira o arredondamento da linha das listas.

O QUE O MANTENEDOR VIU

    "a selecao da home e mais quadrada e a outra no inicio e redonda --
    acho que nao esta usando o mesmo esqueleto"

    Esta certo. Na home a selecao e o fundo de um **rotulo**, que nasce
    com raio 0. Nas listas e o fundo de um **widget de linha**, que herda
    o arredondamento do tema da LVGL.

    Nao e a mesma peca, entao nao basta igualar a cor: e preciso igualar
    a forma.

O OBSTACULO, E A SAIDA

    `lv_obj_set_style_radius` **nao existe no binario** -- o linker
    descartou os setters que o firmware nao usava.

    Mas todos os setters sao casca fina sobre um despachante comum:

        00D4D100  mov  r3, r2      ; seletor
        00D4D102  mov  r2, r1      ; valor
        00D4D104  movs r1, #0x33   ; propriedade
        00D4D106  b.w  0xD4CAC4    ; despachante

    Assinatura: `0xD4CAC4(obj, propriedade, valor, seletor)`.

    E o formato da propriedade sai dos wrappers que existem:

        WIDTH     0x1001    prop 0x01 | 0x1000 (LAYOUT_REFR)
        PAD_LEFT  0x1012    prop 0x12 | 0x1000
        BG_OPA    0x0021    prop 0x21, sem flag
        BORDER_SIDE 0x0033  prop 0x33, sem flag

    `LV_STYLE_RADIUS` e 11 sem flags -> **0x000B**.

A ROTINA

    Substitui a da 1.1 (que so punha a cor) por uma que poe cor E raio.
    O gancho continua na ultima chamada de 0x00D21764, o criador de linha
    compartilhado por **39 telas**.

        push  {r0, lr}
        bl    border_side       ; chamada original
        movs  r0, #7 ; bl palette_main
        mov   r1, r0 ; ldr r0,[sp] ; movs r2,#4
        bl    bg_color          ; cor do selecionado (FOCUS_KEY)
        ldr   r0, [sp]
        movs  r1, #0x0B         ; LV_STYLE_RADIUS
        movs  r2, #0            ; raio 0 = quadrado
        movs  r3, #0            ; seletor 0 = todos os estados
        bl    0xD4CAC4          ; o despachante, direto
        pop   {r0, pc}

USO
    python3 tools/patch_raio_selecao.py \\
        --in  firmware/WORKING/GN438_openpod_v048.bin \\
        --out firmware/WORKING/GN438_openpod_v049.bin [--raio 0]
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
HOOK = 0x001217AA
BORDER_SIDE = 0x00D4D100
PALETTE = 0x00D57B48
BG_COLOR = 0x00D4D092
DESPACHANTE = 0x00D4CAC4
RADIUS = 0x000B
FOCUS_KEY = 4
LIVRE_INI = 0x001A3038
PROIBIDO = 0x0000D000


def enc(o, dst):
    off = dst - (o + 4)
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack("<HH", 0xF000 | (s << 10) | ((off >> 12) & 0x3FF),
                       0xD000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF))


def dec(o, b):
    h1, h2 = struct.unpack("<HH", b)
    s = (h1 >> 10) & 1
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if s:
        off -= 1 << 25
    return o + 4 + off


def livre(d):
    f = LIVRE_INI
    for i in range(LIVRE_INI, LIVRE_INI + 0x4000):
        if d[i] != 0xFF:
            f = i + 1
    return (f + 3) & ~3


def main():
    ap = argparse.ArgumentParser(description="Selecao quadrada nas listas")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--raio", type=int, default=0)
    ap.add_argument("--paleta", type=int, default=7)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2
    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — selecao quadrada, igual a da home")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    antiga = dec(HOOK + XIP, bytes(d[HOOK:HOOK + 4]))
    if not (LIVRE_INI + XIP <= antiga < 0x00E00000):
        print(f"  ABORTADO: 0x{HOOK:06X} aponta para 0x{antiga:08X}, "
              f"esperava a rotina da 1.1 na area livre.", file=sys.stderr)
        return 1
    rot = livre(d)
    if any(b != 0xFF for b in d[rot:rot + 0x40]):
        print(f"  ABORTADO: 0x{rot:06X} nao esta virgem.", file=sys.stderr)
        return 1
    print(f"  gancho 0x{HOOK:06X} -> 0x{antiga:08X} (rotina da 1.1)  OK")
    print(f"  rotina nova em 0x{rot:06X}, virgem  OK")
    print(f"  a rotina da 1.1 fica orfa na area livre (inofensiva)\n")

    c = bytearray()
    c += struct.pack("<H", 0xB501)                     # push {r0, lr}
    c += enc(rot + XIP + len(c), BORDER_SIDE)
    c += struct.pack("<H", 0x2000 | a.paleta)          # movs r0, #paleta
    c += enc(rot + XIP + len(c), PALETTE)
    c += struct.pack("<H", 0x4601)                     # mov r1, r0
    c += struct.pack("<H", 0x9800)                     # ldr r0, [sp]
    c += struct.pack("<H", 0x2200 | FOCUS_KEY)         # movs r2, #4
    c += enc(rot + XIP + len(c), BG_COLOR)
    c += struct.pack("<H", 0x9800)                     # ldr r0, [sp]
    c += struct.pack("<H", 0x2100 | RADIUS)            # movs r1, #0x0B
    c += struct.pack("<H", 0x2200 | a.raio)            # movs r2, #raio
    c += struct.pack("<H", 0x2300)                     # movs r3, #0
    c += enc(rot + XIP + len(c), DESPACHANTE)
    c += struct.pack("<H", 0xBD01)                     # pop {r0, pc}
    d[rot:rot + len(c)] = c
    d[HOOK:HOOK + 4] = enc(HOOK + XIP, rot + XIP)

    print("  ROTINA  (0x%08X)" % (rot + XIP))
    desc = [(0x00, 2, "push  {r0, lr}", ""),
            (0x02, 4, "bl    border_side", "chamada original"),
            (0x06, 2, f"movs  r0, #{a.paleta}", ""),
            (0x08, 4, "bl    palette_main", "-> r0 = a cor"),
            (0x0C, 2, "mov   r1, r0", ""), (0x0E, 2, "ldr   r0, [sp]", ""),
            (0x10, 2, "movs  r2, #4", "FOCUS_KEY"),
            (0x12, 4, "bl    bg_color", "a cor do selecionado"),
            (0x16, 2, "ldr   r0, [sp]", ""),
            (0x18, 2, "movs  r1, #0x0B", "LV_STYLE_RADIUS"),
            (0x1A, 2, f"movs  r2, #{a.raio}", "o raio"),
            (0x1C, 2, "movs  r3, #0", "todos os estados"),
            (0x1E, 4, "bl    0x00D4CAC4", "o despachante, direto"),
            (0x22, 2, "pop   {r0, pc}", "")]
    for off, n, asm, com in desc:
        print(f"    +0x{off:02X}  {bytes(c[off:off+n]).hex():<8}  {asm:<20}"
              + (f"; {com}" if com else ""))
    print()
    ok = True
    for off, alvo, nome in ((0x02, BORDER_SIDE, "border_side"),
                            (0x08, PALETTE, "palette_main"),
                            (0x12, BG_COLOR, "bg_color"),
                            (0x1E, DESPACHANTE, "despachante")):
        g = dec(rot + XIP + off, bytes(c[off:off + 4]))
        print(f"    bl {nome:<13} -> 0x{g:08X}  {'OK' if g == alvo else 'ERRADO'}")
        ok &= g == alvo
    g = dec(HOOK + XIP, bytes(d[HOOK:HOOK + 4]))
    ok &= g == rot + XIP
    print(f"    gancho         -> 0x{g:08X}  "
          f"{'OK' if g == rot + XIP else 'ERRADO'}")
    if not ok:
        return 1
    print()
    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
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
