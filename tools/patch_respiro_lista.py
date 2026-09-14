#!/usr/bin/env python3
"""
patch_respiro_lista.py — Respiro entre a faixa superior e a lista.

O QUE O MANTENEDOR VIU (2026-09-14, foto da 1.8)

    "a linha da barra superior quando comeca o menu. no menu principal
     esta perfeito, ja no submenu ela ja esta juntando com os itens"

    Na home:                 Nas telas de lista do sistema:

      10:43 OpenPod [bat]      Configurar          [bat]
      ---------------------    ####################
      (2 px de respiro)        # Despertador     #   <- a selecao ENCOSTA
      # Musica           #       Idioma

A CAUSA — geometria, nao desenho

    A faixa superior e um objeto de altura `ver_res / divisor`, e ela ja
    desenha um traco: `0x00D216F0` define `border_width = 1` e
    `border_side = 1` (BOTTOM), na cor da paleta 0x12.

    O conteiner da lista e alinhado em `TOP_MID` com `y_ofs` igual a
    MESMA altura da faixa, e as linhas dentro dele em `y = passo*i - 1`:

        Configurar   faixa  y 0..21   (160/7  = 22)
                     lista  y 22      linha 0 em 22 + (0 - 1) = 21

    **A linha 0 comeca em y=21, que e exatamente onde a faixa desenha o
    traco.** A barra de selecao cobre o traco e encosta no titulo. Nao e
    falta de separador -- e sobreposicao de 1 px.

O PONTO UNICO

    O conteiner da lista nao e criado por cada tela: sai de um helper
    compartilhado, `0x00D21690`, usado por **58 paginas**.

    Dar `pad_top` a ele empurra o conteudo para baixo em todas de uma vez,
    porque `lv_obj_align` posiciona pelo *content area* do pai, que e a
    area ja descontada do padding.

        0x001216CC   bl set_style_radius  ->  bl <rotina na area livre>

    A rotina faz o `radius` que ja fazia e acrescenta `pad_top`.

QUANTO DE RESPIRO

    `PAD = 3`, escolhido pela geometria, nao por gosto:

        Configurar   faixa 0..21 (traco em 21), linha 0 vai para
                     22 + 3 - 1 = 24    ->  respiro em y 22..23  (2 px)
        Extras       faixa 0..15 (traco em 15), lista comeca em
                     16 + 3 = 19        ->  respiro em y 16..18  (3 px)

    2 px e exatamente o respiro da home (`STATUS_BAR.md` 11).

USO
    python3 tools/patch_respiro_lista.py \\
        --in  firmware/WORKING/GN438_openpod_v058.bin \\
        --out firmware/WORKING/GN438_openpod_v059.bin [--dry-run]

DEPENDENCIAS
    Python 3 + capstone

SEGURANCA
    - PROVA AS PREMISSAS na imagem: desmonta `0x00D4D064` e `0x00D4D01C`
      e exige que fixem as propriedades 96 (RADIUS) e 16 (PAD_TOP);
    - exige que o ponto de gancho seja exatamente o `bl` do radius;
    - exige area livre virgem no destino;
    - desmonta a rotina montada e confere instrucao por instrucao;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.

LIMITACOES
    - O helper serve **58 paginas**, e eu NAO conferi as 58 uma a uma.
      Telas que nao sejam lista tambem ganham 3 px de padding no
      conteiner. E reversivel em 4 bytes, mas e a ressalva honesta: o
      alcance e maior que o defeito relatado.
    - Nao acrescenta separador nenhum: o traco ja existe, so estava
      coberto.
"""

import argparse
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
FLASH_SIZE = 0x200000

SET_RADIUS = 0x00D4D064
SET_PAD_TOP = 0x00D4D01C
PROP_RADIUS, PROP_PAD_TOP = 96, 16
PAD = 3

GANCHO = 0x001216CC           # o `bl set_style_radius` em 0x00D21690
BLOB_OFF = 0x001A5220
BLOB_MAX = 0x100


def ins_em(d, a):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    return next(md.disasm(d[a - XIP:a - XIP + 4], a), None)


def bl(origem, destino):
    off = destino - (origem + 4)
    if off & 1 or not (-(1 << 24) <= off < (1 << 24)):
        raise ValueError("bl fora de alcance")
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = (0xD000 | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11)
           | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def prop_do_wrapper(d, addr):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    prop = None
    for i in md.disasm(d[addr - XIP:addr - XIP + 32], addr):
        if i.mnemonic in ("movs", "movw") and i.op_str.startswith("r1, #"):
            prop = int(i.op_str.split("#")[1], 0)
        if i.mnemonic == "b.w" and "0xd4cac4" in i.op_str:
            return None if prop is None else prop & 0x3FF
    return None


def monta(base):
    c = [struct.pack("<H", 0xB501)]            # push {r0, lr}
    c.append(bl(base + 2, SET_RADIUS))         # bl   set_style_radius
    c.append(struct.pack("<H", 0x9800))        # ldr  r0, [sp]
    c.append(struct.pack("<H", 0x2100 | PAD))  # movs r1, #PAD
    c.append(struct.pack("<H", 0x2200))        # movs r2, #0
    c.append(bl(base + 12, SET_PAD_TOP))       # bl   set_style_pad_top
    c.append(struct.pack("<H", 0xBD01))        # pop  {r0, pc}
    return b"".join(c)


ESPERADO = ["push", "bl", "ldr", "movs", "movs", "bl", "pop"]


def main():
    ap = argparse.ArgumentParser(description="Respiro entre a faixa e a lista")
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
    for addr, esperada, nome in ((SET_RADIUS, PROP_RADIUS, "RADIUS"),
                                 (SET_PAD_TOP, PROP_PAD_TOP, "PAD_TOP")):
        p = prop_do_wrapper(data, addr)
        if p != esperada:
            erros.append(f"0x{addr:08X} fixa a propriedade {p}, "
                         f"esperado {esperada} ({nome})")

    g = ins_em(data, GANCHO + XIP)
    if not (g and g.mnemonic == "bl"
            and int(g.op_str.strip("#"), 0) == SET_RADIUS):
        erros.append(f"0x{GANCHO:06X} nao e o `bl set_style_radius` esperado "
                     f"({g.mnemonic + ' ' + g.op_str if g else '?'})")
    if any(b != 0xFF for b in data[BLOB_OFF:BLOB_OFF + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB_OFF:06X} nao esta virgem")

    base = BLOB_OFF + XIP
    blob = monta(base)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    got = [x.mnemonic for x in md.disasm(blob, base)]
    if got != ESPERADO:
        erros.append(f"rotina montada nao confere: {got}")

    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print("  OPENPOD — RESPIRO ENTRE A FAIXA E A LISTA")
    print()
    print(f"  premissas conferidas: 0x{SET_RADIUS:08X}=RADIUS(96)  "
          f"0x{SET_PAD_TOP:08X}=PAD_TOP(16)")
    print(f"  gancho conferido:     0x{GANCHO:06X} = bl set_style_radius")
    print()
    print(f"  pad_top = {PAD} px no conteiner compartilhado 0x00D21690")
    print("    Configurar  faixa 0..21, traco em 21 -> linha 0 vai para 24"
          "   (respiro 2 px)")
    print("    Extras      faixa 0..15, traco em 15 -> lista comeca em 19"
          "   (respiro 3 px)")
    print()
    print("  ALTERACOES")
    data[BLOB_OFF:BLOB_OFF + len(blob)] = blob
    print(f"    0x{BLOB_OFF:06X}  rotina {len(blob)} B — radius + pad_top")
    data[GANCHO:GANCHO + 4] = bl(GANCHO + XIP, base)
    print(f"    0x{GANCHO:06X}  bl 0x{SET_RADIUS:08X} -> bl 0x{base:08X}")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X}, abaixo de 0x00E000 (R1)")
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
