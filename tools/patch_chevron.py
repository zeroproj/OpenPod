#!/usr/bin/env python3
"""
patch_chevron.py — Redesenha os chevrons da home menores, no estilo nano.

O chevron atual tem 6x9 px com traco de 2 px -- 75% da altura do texto
(12 px). No iPod nano ele e bem mais discreto. Este patch redesenha a
folha de fundo com um chevron de 4x7 e traco de 1 px (58%).

Os chevrons ficam em x = 116..121 (a coluna liberada pela V032). Um
chevron de 4 px fica centralizado nessa faixa, em x = 117..120.

O QUE E ALTERADO

    0x000CE15C   px   folha de fundo: so os pixels dos chevrons

    Nenhum codigo. Nenhuma tabela. So imagem.

USO
    python3 tools/patch_chevron.py \
        --in  firmware/WORKING/GN438_openpod_v032.bin \
        --out firmware/WORKING/GN438_openpod_v033.bin [--dry-run]

SEGURANCA
    - le as coordenadas das tabelas, nao assume;
    - apaga so a area do chevron antigo, nao a folha inteira;
    - recusa se o chevron novo nao couber na faixa livre;
    - recusa se algum setor alterado for <= 0x00D000.
"""

import argparse
import os
import struct
import sys

PIX = 0x000CE15C
W, H = 128, 160
BG, FG = 1, 0
TBL_ICON = 0x0004867C
TBL_LABEL = 0x000486A0
N = 9
LARGURA_OFF = 0x0012ED5E
ANTIGO_W, ANTIGO_H, ANTIGO_DY = 6, 9, 3
PROIBIDO = 0x0000D000

NOVO = [".#..", "..#.", "...#", "..#.", ".#..", "#..."]
NOVO = ["#...", ".#..", "..#.", "...#", "..#.", ".#..", "#..."]


def main():
    ap = argparse.ArgumentParser(description="Chevron menor, estilo nano")
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
    print("OpenPod — chevron menor, estilo nano")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    coords = [struct.unpack_from("<hh", d, TBL_ICON + i * 4) for i in range(N)]
    x_rot = struct.unpack_from("<h", d, TBL_LABEL)[0]
    larg = d[LARGURA_OFF]
    novo_w, novo_h = len(NOVO[0]), len(NOVO)
    faixa_ini, faixa_fim = x_rot + larg, 127

    print("  GEOMETRIA LIDA DO FIRMWARE")
    print(f"    barra ocupa   x = {x_rot}..{x_rot + larg - 1}")
    print(f"    faixa livre   x = {faixa_ini}..{faixa_fim}  "
          f"({faixa_fim - faixa_ini + 1} px)")
    print(f"    chevron atual {ANTIGO_W}x{ANTIGO_H}, traco 2 px")
    print(f"    chevron novo  {novo_w}x{novo_h}, traco 1 px")
    print()

    if novo_w > faixa_fim - faixa_ini + 1:
        print(f"  ABORTADO: o chevron de {novo_w} px nao cabe na faixa livre.",
              file=sys.stderr)
        return 1

    # centraliza o chevron novo na faixa livre
    x_novo = faixa_ini + (faixa_fim - faixa_ini + 1 - novo_w) // 2
    dy_novo = ANTIGO_DY + (ANTIGO_H - novo_h) // 2
    print(f"    chevron novo em x = {x_novo}..{x_novo + novo_w - 1}, "
          f"dy = {dy_novo}")
    print()

    apagados = desenhados = 0
    for (cx, cy) in coords:
        if cy >= H:
            continue                      # itens escondidos fora da tela
        # apaga a area do chevron antigo
        for dy in range(ANTIGO_H):
            for dx in range(ANTIGO_W):
                x, y = cx + dx, cy + ANTIGO_DY + dy
                if 0 <= x < W and 0 <= y < H:
                    if d[PIX + y * W + x] != BG:
                        apagados += 1
                    d[PIX + y * W + x] = BG
        # desenha o novo
        for dy, linha in enumerate(NOVO):
            for dx, c in enumerate(linha):
                if c != "#":
                    continue
                x, y = x_novo + dx, cy + dy_novo + dy
                if 0 <= x < W and 0 <= y < H:
                    d[PIX + y * W + x] = FG
                    desenhados += 1

    visiveis = len([c for c in coords if c[1] < H])
    print(f"  {visiveis} chevrons redesenhados  "
          f"({apagados} px apagados, {desenhados} desenhados)")
    print()
    print("  PREVIA (uma linha)")
    cy = coords[0][1]
    print("      " + "".join(str(x % 10) for x in range(114, 128)))
    for y in range(cy, cy + 16):
        print(f"   {y:>3} " + "".join(
            "#" if d[PIX + y * W + x] != BG else "." for x in range(114, 128)))
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
