#!/usr/bin/env python3
"""
patch_sem_separador.py — tira o traco entre os itens da lista. 1 byte.

A REFERENCIA MANDA

    `marte/mockups/marte_completo.png`, a especificacao visual do
    produto: a lista do nano e **branca e limpa**. Nao ha traco entre os
    itens. Regra em `docs/MARTE_ALVO.md` §0 — aparencia se decide pela
    referencia.

    Cuidado com a confusao que eu ja fiz: o `faixa_separador` do
    `nanoclone.json` NAO e o traco entre as linhas. E a linha **y=17**,
    de 1 px, **embaixo da faixa** — e essa FICA.

    Sao dois objetos diferentes, e a medicao confirma:

        0x0012174C   CRIA_FAIXA   border_width = 1   <- FICA
        0x001217A0   CRIA_LINHA   border_width = 1   <- vai a ZERO

DE ONDE VINHA O TRACO

        00D2178A   movs r0, #0x12
        00D2178C   bl   palette_main        <- a cor vem da PALETA da LVGL
        00D21796   bl   set_style_border_color
        00D2179E   movs r1, #1
        00D217A0   bl   set_style_border_width

    A cor da borda da linha nunca teve campo na tabela — e a oitava vez
    que um valor de aparencia mora fora dela. Zerando a largura, a cor
    deixa de importar.

O SETTER, CONFERIDO

        0x00D4D0F4   movw r1, #0x1032   ; b.w 0xD4CAC4
                     0x32 = 50 = LV_STYLE_BORDER_WIDTH (LVGL v8)

    Nao supus pelo nome: desmontei o wrapper e li o numero da
    propriedade.

USO
    python3 tools/patch_sem_separador.py --in <e.bin> --out <s.bin> [--dry-run]

LIMITACOES
    - so a borda da LINHA. Faixa, conteiner e as outras seis chamadas de
      border_width do firmware ficam como estao;
    - recusa se a linha nao estiver com largura 1, ou se a faixa nao
      estiver com largura 1 — nos dois casos o firmware nao e o esperado.
"""

import argparse, hashlib, struct, sys

XIP       = 0x00C00000
BW        = 0x00D4D0F4        # set_style_border_width, prop 0x1032
LINHA_IMM = 0x0012179E        # movs r1,#1  dentro de CRIA_LINHA
LINHA_BL  = 0x001217A0
FAIXA_IMM = 0x0012174A        # o movs da faixa — so para CONFERIR
PROIBIDO  = 0x0000D000


def dec_bl(origem, b):
    w1, w2 = struct.unpack("<HH", b)
    if (w1 & 0xF800) != 0xF000 or (w2 & 0xD000) != 0xD000:
        return None
    S = (w1 >> 10) & 1
    j1, j2 = (w2 >> 13) & 1, (w2 >> 11) & 1
    off = (S << 24) | (((~(j1 ^ S)) & 1) << 23) | (((~(j2 ^ S)) & 1) << 22) \
        | ((w1 & 0x3FF) << 12) | ((w2 & 0x7FF) << 1)
    return origem + 4 + (off - (1 << 25) if S else off)


def main():
    ap = argparse.ArgumentParser(description="sem traco entre os itens")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != 0x200000:
        print(f"ERRO: {a.src} tem {len(d)} B", file=sys.stderr)
        return 1
    orig = bytes(d)

    print("\n  SEM TRACO ENTRE OS ITENS — como o nano\n")

    # 1. o ponto da LINHA e mesmo movs r1,#N seguido de border_width?
    w = struct.unpack_from("<H", d, LINHA_IMM)[0]
    alvo = dec_bl(LINHA_BL + XIP, bytes(d[LINHA_BL:LINHA_BL + 4]))
    if (w & 0xFF00) != 0x2100 or alvo != BW:
        print(f"  ABORTADO: 0x{LINHA_IMM:06X} nao e 'movs r1,#N' seguido de "
              f"border_width (achei 0x{w:04X} -> 0x{alvo or 0:08X})",
              file=sys.stderr)
        return 1
    larg = w & 0xFF
    print(f"    CRIA_LINHA  0x{LINHA_IMM:06X}  border_width = {larg}")
    if larg == 0:
        print("    ja esta em 0 — nada a fazer")
        return 0
    if larg != 1:
        print(f"  ABORTADO: esperava largura 1, achei {larg}.", file=sys.stderr)
        return 1

    # 2. a faixa TEM de continuar com o traco
    wf = struct.unpack_from("<H", d, FAIXA_IMM)[0]
    if (wf & 0xFF00) != 0x2100 or (wf & 0xFF) != 1:
        print(f"  ABORTADO: a faixa em 0x{FAIXA_IMM:06X} nao esta com "
              f"largura 1 (0x{wf:04X}). O traco dela deve FICAR.",
              file=sys.stderr)
        return 1
    print(f"    CRIA_FAIXA  0x{FAIXA_IMM:06X}  border_width = 1   INTOCADA")
    print()

    d[LINHA_IMM] = 0x00
    volta = struct.unpack_from("<H", d, LINHA_IMM)[0] & 0xFF
    print("  ALTERACOES")
    print(f"    0x{LINHA_IMM:06X}   1 B   movs r1,#1 -> movs r1,#0")
    print(f"  conferencia: relido -> largura {volta}  "
          f"{'OK' if volta == 0 else 'DIVERGE'}")
    if volta != 0:
        return 1
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido (R1).", file=sys.stderr)
        return 1
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}\n")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
