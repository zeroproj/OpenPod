#!/usr/bin/env python3
"""
patch_selecao_criacao.py — A seleção restaurada na CRIAÇÃO da home também
                           vira barra, como já acontece na navegação.

O DEFEITO

    `patch_barra_selecao.py` (V027) tratou dois caminhos:

        seleção     0x0012EB4C   bl text_color -> bl bg_color
        desseleção  4 ramos de tecla

    E deixou passar o terceiro: a **criação** da tela. Quando a home é
    recriada (você entra num item e volta, ou liga o aparelho), o índice
    salvo em 0x00823D83 é repintado com o estilo ANTIGO:

        00D2EDAE   movs r0, #7
        00D2EDB2   bl   0xD57B48    ; palette_main(7)
        00D2EDBC   bl   0xD4D10A    ; set_style_text_color   <- aqui

    Resultado na tela: o item em que você entrou por último fica com o
    TEXTO ciano e sem barra, enquanto o cursor atual tem barra. Dois
    indicadores diferentes disputando a mesma lista.

A CORREÇÃO

    O trecho da criação é byte a byte igual ao da seleção; só o alvo da
    última chamada difere:

        seleção   00D2EB4C   bl 0x00D4D092   (set_bg_color)
        criação   00D2EDBC   bl 0x00D4D10A   (set_text_color)

    Trocar o alvo da criação para `set_bg_color` faz os dois caminhos
    produzirem exatamente o mesmo resultado. Mesma paleta, mesma cor,
    mesma barra.

    O `bg_opa` já está ligado para todo rótulo pela rotina da V028b, e o
    fundo preto padrão também — então a barra aparece sem mais nada.

O QUE É ALTERADO

    0x0012EDBC   4 B   bl 0x00D4D10A -> bl 0x00D4D092

    Um setor: 0x0012E000. A tabela de partições NÃO é tocada — o CRC da
    FIRM não é verificado (CONFIRMADO no hardware, ver INCIDENTE §9).

USO
    python3 tools/patch_selecao_criacao.py \
        --in  firmware/WORKING/GN438_openpod_v028_ptorig.bin \
        --out firmware/WORKING/GN438_openpod_v031.bin [--dry-run]

SEGURANÇA
    - recusa se origem == destino;
    - recusa se o `bl` não apontar hoje para set_text_color;
    - confere que o trecho da criação é mesmo idêntico ao da seleção;
    - decodifica de volta o `bl` que gera e compara o alvo;
    - recusa se algum setor alterado for <= 0x00D000.
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
ALVO = 0x0012EDBC
TEXT_COLOR = 0x00D4D10A
BG_COLOR = 0x00D4D092
REF_SEL = 0x0012EB4C          # a mesma chamada, no caminho de selecao
PROIBIDO = 0x0000D000


def enc_bl(origem, destino):
    off = destino - (origem + 4)
    if not -(1 << 24) <= off < (1 << 24) or off & 1:
        raise ValueError("fora de alcance")
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack("<HH", 0xF000 | (s << 10) | ((off >> 12) & 0x3FF),
                       0xD000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF))


def dec_bl(origem, blob):
    h1, h2 = struct.unpack("<HH", blob)
    s = (h1 >> 10) & 1
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if s:
        off -= 1 << 25
    return origem + 4 + off


def main():
    ap = argparse.ArgumentParser(
        description="Barra de selecao tambem na criacao da home")
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
    print("OpenPod V031 — a selecao restaurada tambem vira barra")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    erros = []
    atual = dec_bl(ALVO + XIP, bytes(d[ALVO:ALVO + 4]))
    if atual != TEXT_COLOR:
        erros.append(f"0x{ALVO:06X} aponta para 0x{atual:08X}, "
                     f"esperado set_text_color 0x{TEXT_COLOR:08X}")
    ref = dec_bl(REF_SEL + XIP, bytes(d[REF_SEL:REF_SEL + 4]))
    if ref != BG_COLOR:
        erros.append(f"0x{REF_SEL:06X} (selecao) aponta para 0x{ref:08X}, "
                     f"esperado set_bg_color — a entrada nao tem a barra da V027")
    # Os dois trechos tem que ser identicos fora as duas chamadas.
    # O `bl palette_main` no meio e relativo ao PC, entao difere por
    # construcao: comparar so as partes que nao sao branch.
    def moldura(off):
        return bytes(d[off - 14:off - 10]) + bytes(d[off - 6:off])
    if moldura(ALVO) != moldura(REF_SEL):
        erros.append("o trecho da criacao nao e identico ao da selecao; "
                     "revise antes de patchar")
    for off, nome in ((ALVO, "criacao"), (REF_SEL, "selecao")):
        if dec_bl(off - 10 + XIP, bytes(d[off - 10:off - 6])) != 0x00D57B48:
            erros.append(f"0x{off-10:06X} ({nome}) nao e bl palette_main")
    if erros:
        print("  ABORTADO — a entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print("  entrada conferida:")
    print(f"    0x{REF_SEL:06X} (selecao) -> set_bg_color      OK")
    print(f"    0x{ALVO:06X} (criacao) -> set_text_color    <- a corrigir")
    print("    os 14 bytes anteriores sao identicos nos dois     OK")
    print()

    novo = enc_bl(ALVO + XIP, BG_COLOR)
    if dec_bl(ALVO + XIP, novo) != BG_COLOR:
        print("  ABORTADO: codificacao nao confere na volta.", file=sys.stderr)
        return 1
    d[ALVO:ALVO + 4] = novo

    print("  ALTERACAO")
    print(f"    0x{ALVO:06X}  {bytes(orig[ALVO:ALVO+4]).hex()} -> {novo.hex()}")
    print(f"                bl 0x{TEXT_COLOR:08X} -> bl 0x{BG_COLOR:08X}")
    print(f"                set_text_color -> set_bg_color")
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
