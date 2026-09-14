#!/usr/bin/env python3
"""
patch_lista_sistema.py — Aproxima a lista do sistema (Extras e Configurar)
                         do padrao da home.

AS DUAS TELAS SAO A MESMA

    Extras e Configurar usam `page_set_menu_create` (0x00D3A638) com
    tabelas de itens diferentes. Confirmado visualmente no aparelho:
    mesma engrenagem, mesmo separador, mesma altura de linha, mesma faixa
    superior so com bateria. Um patch pega as duas.

A ESTRUTURA, DESMONTADA

    Por item (laco de 10), tres objetos:

        r4 = 0xD21764(...)               ; a linha
             set_h(r4, ver_res / sb)     ; sb = 7  -> 160/7 = 22 px
             set_align(r4, 2, 0, (ver_res/sb)*i - 1)
        fp = novo_rotulo(r4)
             0xD4D12E(fp, 0x00CA671C)    ; fonte de icones
             set_text(fp, 0x00C5D622)    ; U+F013, a engrenagem
        sb = novo_rotulo(r4)
             set_w(sb, hor_res - 15)
             set_text(sb, get_string(id))

    Guardados na struct: linhas em 0, rotulos em 0x28, icones em 0x50 --
    o esquema N*4 / 2*N*4 ja documentado.

O QUE ESTE PATCH FAZ

    1. **Altura da linha 22 -> 16 px.** O divisor `sb` vale 7 e divide a
       resolucao VERTICAL (0x00D568CC e `lv_disp_get_ver_res`). Trocar
       para 10 da 160/10 = 16, o mesmo passo da home, e 10 itens passam a
       ocupar a tela exata. **1 byte.**

    2. **Tira a engrenagem.** O rotulo de icone passa a receber uma
       string vazia em vez de U+F013. O objeto continua existindo (a
       struct nao muda), so nao desenha nada. **4 bytes** no pool de
       literais.

    NAO mexe na barra superior nem no separador -- sao trabalhos
    separados, cada um com sua investigacao.

USO
    python3 tools/patch_lista_sistema.py \
        --in  firmware/WORKING/GN438_openpod_v038.bin \
        --out firmware/WORKING/GN438_openpod_v039.bin \
        [--divisor 10] [--manter-icone] [--dry-run]

SEGURANCA
    - recusa se o `mov.w` do divisor nao estiver no valor esperado;
    - recusa se o literal nao apontar para o glifo da engrenagem;
    - recusa se o alvo da string vazia nao for um byte NUL;
    - recusa divisor que nao caiba 10 itens na tela;
    - recusa se algum setor alterado for <= 0x00D000.
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
GLIFO_ENGRENAGEM = 0x00C5D622
VAZIA = 0x00C4F982            # NUL logo depois da string " "
VER_RES = 160
PROIBIDO = 0x0000D000

# O separador nasce no criador da linha (0x00D21764), compartilhado por
# TODAS as listas do sistema:
#     0x0012179E  movs r1,#1 ; bl 0x00D4D0F4  -> border_width = 1
#     0x001217A8  movs r1,#1 ; bl 0x00D4D100  -> border_side  = BOTTOM
# Largura 0 apaga o separador em todas as telas de uma vez, e torna o
# border_side irrelevante -- inclusive os overrides que o Extras faz por
# item (2 = TOP, 3 = TOP|BOTTOM).
BORDER_W = 0x0012179E

# Duas telas, dois codigos. Elas PARECEM iguais e nao sao: a V039 mexeu so
# no Configurar e o Extras ficou intacto -- provado por foto no aparelho.
#
#   nome: (divisores, literal do icone, n de itens)
#   divisores: lista de (offset do byte, valor esperado, para que serve)
TELAS = {
    "configurar": {
        "func": 0x00D3A638,
        "divisores": [(0x0013A7BA, 7, "altura da linha e espacamento")],
        "lit_icone": 0x0013A8BC,
        "n": 10,
    },
    "extras": {
        "func": 0x00D2F0A0,
        "divisores": [(0x0012F0EC, 7, "conteiner: altura e y"),
                      (0x0012F22E, 7, "altura da linha")],
        "lit_icone": 0x0012F330,
        "n": 6,
    },
}


def main():
    ap = argparse.ArgumentParser(
        description="Lista do sistema no padrao da home")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--tela", choices=sorted(TELAS), required=True)
    ap.add_argument("--divisor", type=int, default=10)
    ap.add_argument("--manter-icone", action="store_true")
    ap.add_argument("--sem-separador", action="store_true",
                    help="border_width=0 no criador de linha (afeta TODAS "
                         "as listas do sistema)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — lista do sistema (Extras e Configurar)")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    T = TELAS[a.tela]
    DIVISORES, LIT_ICONE, N_ITENS = T["divisores"], T["lit_icone"], T["n"]
    print(f"  tela   : {a.tela}  (funcao 0x{T['func']:08X}, {N_ITENS} itens)\n")

    erros = []
    for off, esperado, _ in DIVISORES:
        if d[off] != esperado:
            erros.append(f"0x{off:06X} = {d[off]}, esperado {esperado}")
    lit = struct.unpack_from("<I", d, LIT_ICONE)[0]
    if lit != GLIFO_ENGRENAGEM:
        erros.append(f"literal 0x{LIT_ICONE:06X} = 0x{lit:08X}, "
                     f"esperado 0x{GLIFO_ENGRENAGEM:08X}")
    if a.sem_separador and d[BORDER_W] != 1:
        erros.append(f"0x{BORDER_W:06X} = {d[BORDER_W]}, esperado 1")
    if d[VAZIA - XIP] != 0:
        erros.append(f"0x{VAZIA:08X} nao e NUL")
    if not 1 <= a.divisor <= 40:
        erros.append(f"divisor {a.divisor} fora de faixa")
    elif (VER_RES // a.divisor) * N_ITENS > VER_RES + a.divisor:
        erros.append(f"divisor {a.divisor} nao cabe {N_ITENS} itens em "
                     f"{VER_RES} px")
    if erros:
        print("  ABORTADO — a entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print("  entrada conferida: divisores, literal da engrenagem, NUL  OK\n")

    alt_ant = VER_RES // DIVISORES[0][1]
    alt_nova = VER_RES // a.divisor
    print("  GEOMETRIA")
    for off, esperado, para in DIVISORES:
        print(f"    divisor 0x{off:06X}  {esperado} -> {a.divisor}   ({para})")
    print(f"    altura linha {alt_ant} -> {alt_nova} px"
          f"   (home usa 15/16)")
    print(f"    10 itens     {alt_ant * N_ITENS} -> {alt_nova * N_ITENS} px"
          f"   (tela tem {VER_RES})")
    print()

    for off, _, _ in DIVISORES:
        d[off] = a.divisor
    if not a.manter_icone:
        struct.pack_into("<I", d, LIT_ICONE, VAZIA)
    if a.sem_separador:
        d[BORDER_W] = 0

    print("  ALTERACOES")
    for off, esperado, para in DIVISORES:
        print(f"    0x{off:06X}   1 B  divisor {esperado} -> {a.divisor}  ({para})")
    if not a.manter_icone:
        print(f"    0x{LIT_ICONE:06X}   4 B  icone 0x{GLIFO_ENGRENAGEM:08X} "
              f"(U+F013) -> 0x{VAZIA:08X} (string vazia)")
    else:
        print("    (--manter-icone: a engrenagem fica)")
    if a.sem_separador:
        print(f"    0x{BORDER_W:06X}   1 B  border_width 1 -> 0  "
              "(separador, TODAS as listas)")
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
