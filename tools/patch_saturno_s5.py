#!/usr/bin/env python3
"""
patch_saturno_s5.py — SATURNO S5: a folha de imagem deixa de desenhar a faixa.

POR QUE

    Depois do S4 a faixa da home e um objeto LVGL criado pelo helper
    compartilhado, com altura e cores da TABELA. Mas os pixels da faixa
    continuam na folha de imagem 0x000CDD50, pintados pelo V017/V018.

    Resultado: a faixa e desenhada DUAS vezes. Hoje o resultado e
    identico, porque as duas ocupam y 0..16 e as cores batem. Mas sao
    DUAS fontes de verdade para a mesma coisa — exatamente o que o
    Saturno existe para acabar. Mude `altura_faixa` na tabela e os pixels
    da folha ficam para tras.

O QUE FAZ

    Repinta as linhas 0..16 da folha com o indice do FUNDO. A partir
    daqui, quem desenha a faixa da home e so o objeto.

SEGURANCA

    - confere o descritor da folha (cf, largura, altura);
    - confere que as linhas 0..16 contem SOMENTE os indices da faixa
      (2,3,4,5) e do fundo (1). Se houver qualquer outro indice ali, e
      porque a folha guarda outra coisa naquela faixa, e a ferramenta
      RECUSA em vez de apagar;
    - nao mexe na paleta, so em pixels;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.

LIMITACOES

    Se o objeto da faixa nao aparecer no aparelho, a home fica SEM faixa
    (fundo preto onde havia o degrade). E reversivel repintando, mas e o
    risco real deste passo — e por isso ele foi separado do S4.

USO
    python3 tools/patch_saturno_s5.py \\
        --in  firmware/WORKING/GN438_openpod_v063.bin \\
        --out firmware/WORKING/GN438_openpod_v064.bin [--dry-run]
"""

import argparse
import struct
import sys

FLASH_SIZE = 0x200000
IMG_DESC = 0x000CDD50
PAL_OFF = 0x000CDD5C
PIX_OFF = 0x000CE15C
IMG_W, IMG_H = 128, 160

BG_INDEX = 1
IDX_FAIXA = {2, 3, 4, 5}
ALTURA = 17                      # y 0..16 — a faixa + o separador


def main():
    ap = argparse.ArgumentParser(description="Saturno S5: limpar a folha")
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

    erros = []
    hdr = struct.unpack_from("<I", data, IMG_DESC)[0]
    cf, w, h = hdr & 0x1F, (hdr >> 10) & 0x7FF, (hdr >> 21) & 0x7FF
    if (cf, w, h) != (10, IMG_W, IMG_H):
        erros.append(f"descritor da folha inesperado: cf={cf} {w}x{h}")

    usados = {}
    for y in range(ALTURA):
        for x in range(IMG_W):
            i = data[PIX_OFF + y * IMG_W + x]
            usados.setdefault(i, 0)
            usados[i] += 1
    estranhos = set(usados) - IDX_FAIXA - {BG_INDEX}
    if estranhos:
        erros.append(f"as linhas 0..{ALTURA-1} contem indices fora da faixa: "
                     f"{sorted(estranhos)} — a folha guarda outra coisa ali, "
                     "RECUSADO")
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    def rgb(i):
        return (data[PAL_OFF + i * 4 + 2], data[PAL_OFF + i * 4 + 1],
                data[PAL_OFF + i * 4])

    print()
    print("  SATURNO S5 — a folha deixa de desenhar a faixa")
    print()
    print(f"  linhas 0..{ALTURA-1} da folha, antes:")
    ant = None
    for y in range(ALTURA):
        i = data[PIX_OFF + y * IMG_W]
        if i != ant:
            print(f"    y{y:2d}..  indice {i:3d}  RGB{rgb(i)}")
            ant = i
    print(f"  indices presentes: {dict(sorted(usados.items()))}")
    print()
    print("  ALTERACOES")
    n = 0
    for y in range(ALTURA):
        for x in range(IMG_W):
            p = PIX_OFF + y * IMG_W + x
            if data[p] != BG_INDEX:
                data[p] = BG_INDEX
                n += 1
    print(f"    0x{PIX_OFF:06X}  {n} pixels -> indice {BG_INDEX} "
          f"RGB{rgb(BG_INDEX)}")
    print("    a paleta NAO foi tocada")
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
