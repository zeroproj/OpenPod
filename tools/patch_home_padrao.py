#!/usr/bin/env python3
"""
patch_home_padrao.py — A home herda o padrao das listas do sistema.

A DECISAO

    Com Extras e Configurar padronizados, o mantenedor comparou as telas
    no aparelho e decidiu: a barra de selecao **de borda a borda** e mais
    agradavel que a de 110 px com margem. A home passa a seguir as outras,
    nao o contrario.

    Consequencia aceita: **o chevron sai**. Ele e desenhado na folha de
    fundo, entao a barra opaca de largura total o cobriria de qualquer
    forma (regra R-L2 do Design System). Melhor tirar de proposito do que
    deixar sumir na linha selecionada.

O QUE MUDA

    1. Rotulo de x=6 para x=0, largura 110 -> 128: a barra sangra ate as
       bordas.
    2. `pad_left = 6` no rotulo: o TEXTO continua recuado 6 px dentro da
       barra. Sem isso ele encostaria na borda esquerda.
       (`set_style_pad_left` = 0x00D4D034, prop 0x12.)
    3. Altura 15 -> 16 e passo de 16 px, igual as outras telas.
    4. Chevrons apagados da folha de fundo.

    O item 2 exige estender a rotina da area livre que ja e chamada no
    laco (a da V028b, que liga fundo preto opaco). Uma rotina nova e o
    gancho repontado.

USO
    python3 tools/patch_home_padrao.py \
        --in  firmware/WORKING/GN438_openpod_v042.bin \
        --out firmware/WORKING/GN438_openpod_v043.bin [--dry-run]
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
TBL_LABEL = 0x000486A0
TBL_ICON = 0x0004867C
N = 9
VISIVEIS = 4
Y0, PASSO = 19, 16
LARG_OFF, ALT_OFF = 0x0012ED5E, 0x0012ED5C
HOOK = 0x0012ED58
TEXT_ALIGN = 0x00D4D13A
BG_COLOR = 0x00D4D092
BG_OPA = 0x00D4D0B4
PAD_LEFT = 0x00D4D034
RECUO = 6
PIX = 0x000CE15C
W, H = 128, 160
BG = 1
LIVRE_INI = 0x001A3038
PROIBIDO = 0x0000D000


def enc_bl(o, dst):
    off = dst - (o + 4)
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack("<HH", 0xF000 | (s << 10) | ((off >> 12) & 0x3FF),
                       0xD000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF))


def dec_bl(o, b):
    h1, h2 = struct.unpack("<HH", b)
    s = (h1 >> 10) & 1
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if s:
        off -= 1 << 25
    return o + 4 + off


def proximo_livre(d):
    fim = LIVRE_INI
    for i in range(LIVRE_INI, LIVRE_INI + 0x4000):
        if d[i] != 0xFF:
            fim = i + 1
    return (fim + 3) & ~3


def main():
    ap = argparse.ArgumentParser(description="Home no padrao das outras listas")
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
    print("OpenPod — a home herda o padrao das listas")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    erros = []
    if dec_bl(HOOK + XIP, bytes(d[HOOK:HOOK + 4])) not in range(0x00DA3000, 0x00DA4000):
        erros.append(f"0x{HOOK:06X} nao aponta para a area livre")
    rot = proximo_livre(d)
    if any(b != 0xFF for b in d[rot:rot + 0x30]):
        erros.append(f"0x{rot:06X} nao esta virgem")
    if erros:
        print("  ABORTADO:")
        for m in erros:
            print(f"    - {m}")
        return 1
    antiga = dec_bl(HOOK + XIP, bytes(d[HOOK:HOOK + 4]))
    print(f"  gancho 0x{HOOK:06X} -> 0x{antiga:08X} (rotina da V028b)  OK")
    print(f"  rotina nova em 0x{rot:06X} (XIP 0x{rot + XIP:08X}), virgem  OK\n")

    # 1 — coordenadas: x=0, passo de 16
    print("  COORDENADAS DOS ROTULOS")
    for i in range(N):
        x, y = struct.unpack_from("<hh", d, TBL_LABEL + i * 4)
        if i < VISIVEIS:
            ny = Y0 + PASSO * i
            struct.pack_into("<hh", d, TBL_LABEL + i * 4, 0, ny)
            print(f"    item {i}: ({x:>3},{y:>3}) -> (  0,{ny:>3})")
        else:
            struct.pack_into("<hh", d, TBL_LABEL + i * 4, 0, y)
    print()

    # 2 — largura e altura
    la, al = d[LARG_OFF], d[ALT_OFF]
    d[LARG_OFF], d[ALT_OFF] = W, PASSO
    print("  GEOMETRIA DA LINHA")
    print(f"    largura {la} -> {W}   (barra de borda a borda)")
    print(f"    altura  {al} -> {PASSO}\n")

    # 3 — rotina nova com pad_left
    c = bytearray()
    c += struct.pack("<H", 0xB501)                       # push {r0, lr}
    c += enc_bl(rot + XIP + len(c), TEXT_ALIGN)
    for alvo, val in ((BG_COLOR, 0), (BG_OPA, 0xFF), (PAD_LEFT, RECUO)):
        c += struct.pack("<H", 0x9800)                   # ldr r0, [sp]
        c += struct.pack("<H", 0x2100 | val)             # movs r1, #val
        c += struct.pack("<H", 0x2200)                   # movs r2, #0
        c += enc_bl(rot + XIP + len(c), alvo)
    c += struct.pack("<H", 0xBD01)                       # pop {r0, pc}
    d[rot:rot + len(c)] = c
    d[HOOK:HOOK + 4] = enc_bl(HOOK + XIP, rot + XIP)

    print("  ROTINA NOVA")
    nomes = [(0x00, 2, "push  {r0, lr}", ""),
             (0x02, 4, "bl    text_align", "chamada original"),
             (0x06, 2, "ldr   r0, [sp]", ""), (0x08, 2, "movs  r1, #0", "preto"),
             (0x0A, 2, "movs  r2, #0", ""), (0x0C, 4, "bl    bg_color", ""),
             (0x10, 2, "ldr   r0, [sp]", ""), (0x12, 2, "movs  r1, #0xff", "opaco"),
             (0x14, 2, "movs  r2, #0", ""), (0x16, 4, "bl    bg_opa", ""),
             (0x1A, 2, "ldr   r0, [sp]", ""),
             (0x1C, 2, f"movs  r1, #{RECUO}", "recuo do texto"),
             (0x1E, 2, "movs  r2, #0", ""), (0x20, 4, "bl    pad_left", "<- NOVO"),
             (0x24, 2, "pop   {r0, pc}", "")]
    for off, n, asm, com in nomes:
        print(f"    +0x{off:02X}  {bytes(c[off:off+n]).hex():<8}  {asm:<18}"
              + (f"; {com}" if com else ""))
    ok = True
    for off, alvo in ((0x02, TEXT_ALIGN), (0x0C, BG_COLOR), (0x16, BG_OPA),
                      (0x20, PAD_LEFT)):
        g = dec_bl(rot + XIP + off, bytes(c[off:off + 4]))
        ok &= g == alvo
    g = dec_bl(HOOK + XIP, bytes(d[HOOK:HOOK + 4]))
    ok &= g == rot + XIP
    print(f"\n    conferencia dos 5 saltos: {'todos OK' if ok else 'ERRO'}")
    if not ok:
        return 1
    print()

    # 4 — apaga os chevrons da folha
    n = 0
    for i in range(N):
        cx, cy = struct.unpack_from("<hh", d, TBL_ICON + i * 4)
        if cy >= H:
            continue
        for dy in range(12):
            for dx in range(8):
                x, y = cx + dx, cy + dy
                if 0 <= x < W and 0 <= y < H and d[PIX + y * W + x] != BG:
                    d[PIX + y * W + x] = BG
                    n += 1
    print(f"  CHEVRONS apagados da folha: {n} pixels\n")

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
