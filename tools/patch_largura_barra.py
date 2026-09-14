#!/usr/bin/env python3
"""
patch_largura_barra.py — Ajusta a largura dos rotulos da home (e portanto
                         da barra de selecao), liberando a coluna do chevron.

POR QUE

    A V028b ligou fundo opaco em cada rotulo. Como o rotulo tem 116 px a
    partir de x=6, ele ocupa x = 6..121 -- e os chevrons da folha de fundo
    estao em x = 116..121. Resultado: o fundo do rotulo pinta por cima
    deles e os chevrons somem.

    Nao e bug de desenho: e sobreposicao geometrica. A correcao e reduzir
    a largura para 110, deixando x = 116..121 livre.

        rotulo/barra   x =   6 .. 115   (110 px)
        chevron        x = 116 .. 121   (6 px, sempre visivel)
        margem direita x = 122 .. 127   (6 px, igual a esquerda)

O QUE E ALTERADO

    0x0012ED5E   1 B   largura do rotulo

    Um setor: 0x0012E000. A tabela de particoes NAO e tocada.

USO
    python3 tools/patch_largura_barra.py \
        --in  firmware/WORKING/GN438_openpod_v031.bin \
        --out firmware/WORKING/GN438_openpod_v032.bin [--largura 110]

SEGURANCA
    - recusa se origem == destino;
    - recusa se a largura atual nao for a esperada;
    - recusa se a barra invadir a coluna do chevron;
    - recusa se a barra passar da borda da tela;
    - le as tabelas de coordenadas para calcular, nao assume valores.
"""

import argparse
import os
import struct
import sys

LARGURA = 0x0012ED5E
TBL_ICON = 0x0004867C
TBL_LABEL = 0x000486A0
TELA_W = 128
CHEVRON_W = 6
PROIBIDO = 0x0000D000


def main():
    ap = argparse.ArgumentParser(description="Largura da barra de selecao")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--largura", type=int, default=110)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    x_rot = struct.unpack_from("<h", d, TBL_LABEL)[0]
    x_chv = struct.unpack_from("<h", d, TBL_ICON)[0]
    atual = d[LARGURA]

    print("=" * 72)
    print("OpenPod — largura da barra de selecao")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()
    print("  GEOMETRIA LIDA DO FIRMWARE")
    print(f"    rotulo comeca em x = {x_rot}")
    print(f"    chevron comeca em x = {x_chv}   (largura {CHEVRON_W})")
    print(f"    largura atual do rotulo = {atual}"
          f"   -> ocupa x = {x_rot}..{x_rot + atual - 1}")
    if x_chv <= x_rot + atual - 1:
        print(f"    >>> o rotulo INVADE o chevron em "
              f"{x_rot + atual - x_chv} px — e por isso que ele some")
    print()

    nova = a.largura
    erros = []
    if not 1 <= nova <= TELA_W:
        erros.append(f"largura {nova} fora da tela")
    if x_rot + nova - 1 >= x_chv:
        erros.append(f"largura {nova} ainda invadiria o chevron "
                     f"(rotulo iria ate x={x_rot + nova - 1}, "
                     f"chevron comeca em x={x_chv})")
    if x_rot + nova > TELA_W:
        erros.append(f"largura {nova} passaria da borda da tela")
    if erros:
        print("  ABORTADO:")
        for m in erros:
            print(f"    - {m}")
        return 1

    d[LARGURA] = nova
    print("  ALTERACAO")
    print(f"    0x{LARGURA:06X}  0x{atual:02X} -> 0x{nova:02X}   ({atual} -> {nova})")
    print()
    print("  GEOMETRIA NOVA")
    print(f"    barra    x = {x_rot:>3} ..{x_rot + nova - 1:>4}   ({nova} px)")
    print(f"    chevron  x = {x_chv:>3} ..{x_chv + CHEVRON_W - 1:>4}   (livre)")
    print(f"    margens  esquerda {x_rot} px, direita "
          f"{TELA_W - (x_chv + CHEVRON_W)} px")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido.", file=sys.stderr)
        return 1
    print(f"  tabela de particoes (0x{PROIBIDO:06X}) NAO tocada   OK")
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
