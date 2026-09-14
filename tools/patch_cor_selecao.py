#!/usr/bin/env python3
"""
patch_cor_selecao.py — Todas as listas do sistema passam a usar a cor de
                       selecao da home.

O DIAGNOSTICO

    A home pinta a selecao EXPLICITAMENTE:

        00D2EB42  movs r0, #7 ; bl palette_main   (navegacao)
        00D2EDB2  movs r0, #7 ; bl palette_main   (criacao)

    O criador de linha compartilhado (0x00D21764), usado por **39 telas**,
    define fundo preto e cor de borda (paleta 0x12) -- e **nunca define a
    cor do estado selecionado**. Sem ela, a LVGL cai no azul do tema. Por
    isso Extras e Configurar ficam com uma cor diferente da home.

    O seletor de estado existe e o firmware ja o usa em 5 lugares:

        0x00000004 = LV_STATE_FOCUS_KEY
        ex. 0x00D21D44: set_style_bg_color(obj, palette_main(5), 4)

O GANCHO

    A ultima chamada de 0x00D21764:

        001217A8  movs r1, #1
        001217AA  bl 0x00D4D100      ; border_side  <- o gancho
        001217AE  mov r0, r4
        001217B0  pop {r4, pc}

    Escolhida porque recebe o objeto em r0, retorna void, e e a ultima --
    entao a cor e aplicada depois de todo o resto.

    Uma rotina, um gancho, **39 telas**.

O QUE E ALTERADO

    0x001217AA   4 B  bl border_side -> bl <rotina>
    area livre  24 B  a rotina

USO
    python3 tools/patch_cor_selecao.py \\
        --in  firmware/WORKING/GN438_openpod_v046.bin \\
        --out firmware/WORKING/GN438_openpod_v047.bin \\
        [--paleta 7] [--dry-run]

ENDERECO EXPLICITO (--em)

    Por padrao esta ferramenta ALOCAVA sozinha: varria a area livre e se
    encaixava depois do ultimo byte ocupado. Isso fazia o endereco da
    rotina depender de TUDO que rodou antes — e os patches seguintes
    fixavam esse endereco no codigo. Resultado: a corrente so compunha
    na ordem historica exata (ver `tools/build.py`).

    Com `--em 0x1A3200` o endereco passa a ser declarado por quem chama.
    O comportamento antigo continua sendo o padrao, para nao quebrar uso
    manual; a receita do `build.py` sempre passa `--em`.
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
FOCUS_KEY = 4
ROW = 0x00D21764
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


def livre(d, em=None):
    if em is not None:
        return em
    f = LIVRE_INI
    for i in range(LIVRE_INI, LIVRE_INI + 0x4000):
        if d[i] != 0xFF:
            f = i + 1
    return (f + 3) & ~3


def conta_telas(d):
    n = 0
    for ad in range(0xE000, 0x1A0570 - 4, 2):
        h1, h2 = struct.unpack_from("<HH", d, ad)
        if (h1 & 0xF800) == 0xF000 and (h2 & 0xD000) == 0xD000:
            if dec(ad + XIP, bytes(d[ad:ad + 4])) == ROW:
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="Cor da selecao unificada")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--paleta", type=int, default=7)
    ap.add_argument("--em", type=lambda x: int(x, 0), default=None,
                    help="endereco EXPLICITO da rotina na area livre. "
                         "Sem ele, a ferramenta aloca sozinha — e o "
                         "endereco passa a depender da ordem.")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2
    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — a cor da selecao da home, em todas as listas")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    erros = []
    if dec(HOOK + XIP, bytes(d[HOOK:HOOK + 4])) != BORDER_SIDE:
        erros.append(f"0x{HOOK:06X} nao chama border_side")
    if not 0 <= a.paleta <= 20:
        erros.append(f"paleta {a.paleta} fora de faixa")
    rot = livre(d, a.em)
    if any(b != 0xFF for b in d[rot:rot + 0x30]):
        erros.append(f"0x{rot:06X} nao esta virgem")
    if erros:
        print("  ABORTADO:")
        for m in erros:
            print(f"    - {m}")
        return 1
    n = conta_telas(d)
    print(f"  gancho 0x{HOOK:06X} -> bl border_side  OK")
    print(f"  telas que usam o criador de linha: {n}")
    print(f"  rotina nova em 0x{rot:06X}, virgem  OK\n")

    c = bytearray()
    c += struct.pack("<H", 0xB501)                     # push {r0, lr}
    c += enc(rot + XIP + len(c), BORDER_SIDE)          # bl border_side
    c += struct.pack("<H", 0x2000 | a.paleta)          # movs r0, #paleta
    c += enc(rot + XIP + len(c), PALETTE)              # bl palette_main
    c += struct.pack("<H", 0x4601)                     # mov r1, r0
    c += struct.pack("<H", 0x9800)                     # ldr r0, [sp]
    c += struct.pack("<H", 0x2200 | FOCUS_KEY)         # movs r2, #4
    c += enc(rot + XIP + len(c), BG_COLOR)             # bl bg_color
    c += struct.pack("<H", 0xBD01)                     # pop {r0, pc}
    d[rot:rot + len(c)] = c
    d[HOOK:HOOK + 4] = enc(HOOK + XIP, rot + XIP)

    print("  ROTINA  (0x%08X)" % (rot + XIP))
    desc = [(0x00, 2, "push  {r0, lr}", "preserva o objeto"),
            (0x02, 4, "bl    border_side", "chamada original"),
            (0x06, 2, f"movs  r0, #{a.paleta}", "a paleta da home"),
            (0x08, 4, "bl    palette_main", "-> r0 = a cor"),
            (0x0C, 2, "mov   r1, r0", ""),
            (0x0E, 2, "ldr   r0, [sp]", "recupera o objeto"),
            (0x10, 2, "movs  r2, #4", "LV_STATE_FOCUS_KEY"),
            (0x12, 4, "bl    bg_color", "a cor do selecionado"),
            (0x16, 2, "pop   {r0, pc}", "")]
    for off, nn, asm, com in desc:
        print(f"    +0x{off:02X}  {bytes(c[off:off+nn]).hex():<8}  {asm:<20}"
              + (f"; {com}" if com else ""))
    print()
    ok = True
    for off, alvo, nome in ((0x02, BORDER_SIDE, "border_side"),
                            (0x08, PALETTE, "palette_main"),
                            (0x12, BG_COLOR, "bg_color")):
        g = dec(rot + XIP + off, bytes(c[off:off + 4]))
        print(f"    bl {nome:<13} -> 0x{g:08X}  {'OK' if g == alvo else 'ERRADO'}")
        ok &= g == alvo
    g = dec(HOOK + XIP, bytes(d[HOOK:HOOK + 4]))
    print(f"    gancho         -> 0x{g:08X}  "
          f"{'OK' if g == rot + XIP else 'ERRADO'}")
    ok &= g == rot + XIP
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
    print("  tabela de particoes NAO tocada   OK\n")
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
