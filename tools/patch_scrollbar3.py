#!/usr/bin/env python3
"""
patch_scrollbar3.py — Esconde a barra de rolagem no objeto CERTO.

O ERRO DAS DUAS TENTATIVAS ANTERIORES

    V034 e V036 aplicaram `clear_flag` e `bg_opa=0` em **r4**. Nas duas
    vezes a linha continuou no aparelho.

    Motivo: r4 nao e quem rola. As linhas sao criadas com pai **r7**:

        00D2EC80   mov r0, r4
        00D2EC82   bl  0xD5615C     ; r7 = conteiner das linhas
        ...
        00D2ECEE   mov r0, r7
        00D2ECF0   bl  0xD5D850     ; cada linha, com pai r7

    O mecanismo estava certo desde a V036 (LV_PART_SCROLLBAR = 0x10000,
    confirmado contra 0x00D29CC8 no proprio firmware). O alvo e que
    estava errado.

O QUE MUDA

    1. Desfaz o gancho da V034/V036 em 0x0012EC0E: volta a `bl set_size`.
       A rotina antiga em 0x00DA3400 fica orfa e inofensiva.
    2. Novo gancho em 0x0012EC82 (`bl 0xD5615C`), para uma rotina que
       chama a original, estiliza o conteiner retornado e **devolve o
       valor de retorno intacto** -- ele e usado logo em seguida.

        push  {r4, lr}
        bl    0xD5615C          ; r0 = conteiner das linhas
        mov   r4, r0            ; guarda o retorno
        movs  r1, #0x10
        bl    clear_flag        ; LV_OBJ_FLAG_SCROLLABLE
        mov   r0, r4
        movs  r1, #0
        mov.w r2, #0x10000      ; LV_PART_SCROLLBAR
        bl    set_style_bg_opa
        mov   r0, r4            ; devolve o retorno
        pop   {r4, pc}

    Setores: 0x0012E000 (os dois ganchos) e 0x001A3000 (a rotina).

USO
    python3 tools/patch_scrollbar3.py \
        --in  firmware/WORKING/GN438_openpod_v036.bin \
        --out firmware/WORKING/GN438_openpod_v037.bin [--dry-run]

ENDERECO EXPLICITO (--em)

    Sem ele a ferramenta aloca sozinha e o endereco passa a depender da
    ordem. Ver `tools/build.py`.
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
HOOK_VELHO = 0x0012EC0E
SET_SIZE = 0x00D4A21A
HOOK_NOVO = 0x0012EC82
CRIA_CONT = 0x00D5615C
CLEAR_FLAG = 0x00D4924A
BG_OPA = 0x00D4D0B4
MOVW_FONTE = 0x00129CC0
LIVRE_INI = 0x001A3038
PROIBIDO = 0x0000D000


def enc_bl(o, dst):
    off = dst - (o + 4)
    if not -(1 << 24) <= off < (1 << 24) or off & 1:
        raise ValueError("fora de alcance")
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


def proximo_livre(d, em=None):
    if em is not None:
        return em
    fim = LIVRE_INI
    for i in range(LIVRE_INI, LIVRE_INI + 0x4000):
        if d[i] != 0xFF:
            fim = i + 1
    return (fim + 3) & ~3


def main():
    ap = argparse.ArgumentParser(description="Barra de rolagem, objeto certo")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", type=lambda x: int(x, 0), default=None,
                    help="endereco EXPLICITO da rotina")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — barra de rolagem: agora no conteiner certo (r7)")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    erros = []
    if dec_bl(HOOK_NOVO + XIP, bytes(d[HOOK_NOVO:HOOK_NOVO + 4])) != CRIA_CONT:
        erros.append(f"0x{HOOK_NOVO:06X} nao chama 0x{CRIA_CONT:08X}")
    movw = bytes(d[MOVW_FONTE:MOVW_FONTE + 4])
    if movw != bytes.fromhex("4ff48032"):
        erros.append("mov.w de referencia mudou")
    rot = proximo_livre(d, a.em)
    if any(b != 0xFF for b in d[rot:rot + 0x30]):
        erros.append(f"0x{rot:06X} nao esta virgem")
    if erros:
        print("  ABORTADO:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print(f"  gancho novo 0x{HOOK_NOVO:06X} -> bl 0x{CRIA_CONT:08X}  OK")
    print(f"  rotina nova em 0x{rot:06X} (XIP 0x{rot + XIP:08X}), virgem  OK\n")

    c = bytearray()
    c += struct.pack("<H", 0xB510)                    # push {r4, lr}
    c += enc_bl(rot + XIP + len(c), CRIA_CONT)
    c += struct.pack("<H", 0x4604)                    # mov r4, r0
    c += struct.pack("<H", 0x2110)                    # movs r1, #0x10
    c += enc_bl(rot + XIP + len(c), CLEAR_FLAG)
    c += struct.pack("<H", 0x4620)                    # mov r0, r4
    c += struct.pack("<H", 0x2100)                    # movs r1, #0
    c += movw                                         # mov.w r2, #0x10000
    c += enc_bl(rot + XIP + len(c), BG_OPA)
    c += struct.pack("<H", 0x4620)                    # mov r0, r4
    c += struct.pack("<H", 0xBD10)                    # pop {r4, pc}
    d[rot:rot + len(c)] = c
    d[HOOK_NOVO:HOOK_NOVO + 4] = enc_bl(HOOK_NOVO + XIP, rot + XIP)
    d[HOOK_VELHO:HOOK_VELHO + 4] = enc_bl(HOOK_VELHO + XIP, SET_SIZE)

    desc = [(0x00, 2, "push  {r4, lr}"), (0x02, 4, "bl    0x%08X" % CRIA_CONT),
            (0x06, 2, "mov   r4, r0"), (0x08, 2, "movs  r1, #0x10"),
            (0x0A, 4, "bl    0x%08X" % CLEAR_FLAG), (0x0E, 2, "mov   r0, r4"),
            (0x10, 2, "movs  r1, #0"), (0x12, 4, "mov.w r2, #0x10000"),
            (0x16, 4, "bl    0x%08X" % BG_OPA), (0x1A, 2, "mov   r0, r4"),
            (0x1C, 2, "pop   {r4, pc}")]
    print("  ROTINA")
    for off, n, asm in desc:
        print(f"    +0x{off:02X}  {bytes(c[off:off+n]).hex():<8}  {asm}")
    print()
    ok = True
    for off, alvo, nome in ((0x02, CRIA_CONT, "original"),
                            (0x0A, CLEAR_FLAG, "clear_flag"),
                            (0x16, BG_OPA, "bg_opa")):
        g = dec_bl(rot + XIP + off, bytes(c[off:off + 4]))
        print(f"    bl {nome:<11} -> 0x{g:08X}  {'OK' if g == alvo else 'ERRADO'}")
        ok &= g == alvo
    g = dec_bl(HOOK_NOVO + XIP, bytes(d[HOOK_NOVO:HOOK_NOVO + 4]))
    print(f"    gancho novo  -> 0x{g:08X}  {'OK' if g == rot + XIP else 'ERRADO'}")
    ok &= g == rot + XIP
    g = dec_bl(HOOK_VELHO + XIP, bytes(d[HOOK_VELHO:HOOK_VELHO + 4]))
    print(f"    gancho velho -> 0x{g:08X}  (revertido para set_size)"
          f"  {'OK' if g == SET_SIZE else 'ERRADO'}")
    ok &= g == SET_SIZE
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
    print(f"  tabela de particoes NAO tocada   OK\n")
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
