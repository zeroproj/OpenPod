#!/usr/bin/env python3
"""
patch_bateria_miolo.py — o miolo da bateria fica verde de verdade

O QUE JA FOI MEDIDO
    A varredura por FAIXA DE ENDERECO (nao por assinatura) de
    0x00D23600..0x00D23960 achou SETE escritores de cor no icone:

        0x00D2366C  BG_COLOR    vermelho    bateria fraca    — fica
        0x00D2367A  TEXT_COLOR  vermelho    bateria fraca    — fica
        0x00D2368C  TEXT_COLOR  prateado    Core 5.6
        0x00D2369A  BG_COLOR    BRANCO      <- o miolo branco
        0x00D236B6  TEXT_COLOR  BRANCO      <- instrucoes sobrepostas
        0x00D236CE  TEXT_COLOR  prateado    Core 5.6
        0x00D236DC  BG_COLOR    verde de fabrica RGB(90,186,123)

    As Cores 5.2 e 5.3 pintaram na CRIACAO do objeto (0x00D22682 e
    0x00D22622) -- e o atualizador sobrescreve. Por isso nao apareciam.

A COR CERTA
    O verde do Marte e o do MIOLO, medido por amostragem da area interna
    dos 10 quadros (descontando 3 px de casca):

        RGB(180,246,131) / (197,255,139) / (164,250,98)

    A Core 5.2 usou RGB(115,218,57), que e a cor da BORDA do
    preenchimento -- amostrei a imagem inteira em vez do miolo. O
    mantenedor corrigiu: "no projeto marte e verde por dentro".

A PRE-INVERSAO — confirmada na tela em 2026-09-18
    A DIAG 8 pintou a casca com 0x07E0. Se nao houvesse inversao, sairia
    VERDE; com inversao, VERMELHO. **Saiu vermelha.**

    Primeira verificacao em tela da regra do COLOR_SOURCE.md §9, que
    estava no projeto desde setembro deduzida de um unico caso.

USO
    python3 tools/patch_bateria_miolo.py entrada.bin saida.bin
"""
import sys

BASE_XIP = 0x00C00000
MARTE_MIOLO = (180, 246, 131)
BRANCO = bytes.fromhex("4ff0ff31")          # mov.w r1, #-1
VERDE_FABRICA = bytes.fromhex("4cf65d71")   # movw r1, #0xcf5d
SITIOS = [(0x00D2369A - 0x14, BRANCO, "miolo: branco"),
          (0x00D236DC - 0x14, VERDE_FABRICA, "miolo: verde de fabrica")]


def to565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def pre_inverte(v):
    return ((v & 0xFF) << 8) | (v >> 8)


def movw(rd, valor):
    imm4, i = (valor >> 12) & 0xF, (valor >> 11) & 1
    imm3, imm8 = (valor >> 8) & 7, valor & 0xFF
    return ((0xF240 | (i << 10) | imm4).to_bytes(2, "little")
            + ((imm3 << 12) | (rd << 8) | imm8).to_bytes(2, "little"))


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: patch_bateria_miolo.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")
    cor = pre_inverte(to565(*MARTE_MIOLO))
    novo = movw(1, cor)

    for base, esperado, texto in SITIOS:
        # o `movw`/`mov.w` fica alguns bytes antes do `bl`; procura na janela
        achou = None
        for k in range(0, 0x18, 2):
            off = base + k - BASE_XIP
            if bytes(img[off:off + 4]) == esperado:
                achou = off
                break
        if achou is None:
            sys.exit(f"erro: nao achei {esperado.hex()} perto de {base:#x}")
        img[achou:achou + 4] = novo
        print(f"  {achou + BASE_XIP:#010x}  {texto} -> movw r1, #{cor:#06x}")

    open(sys.argv[2], "wb").write(img)
    print(f"     RGB{MARTE_MIOLO} — o verde-limao do miolo do Marte")
    print(f"\n  escrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
