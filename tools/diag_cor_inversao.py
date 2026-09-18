#!/usr/bin/env python3
"""
diag_cor_inversao.py — a regra da pre-inversao de cor vale ou nao?

A DUVIDA
    O COLOR_SOURCE.md §9 diz que as cores no firmware estao
    PRE-INVERTIDAS (LV_COLOR_16_SWAP): o valor gravado e o RGB565 com os
    dois bytes trocados.

    Evidencia a favor: a bateria fraca usa 0x00F8, que pre-invertido da
    0xF800 = vermelho puro. Direto daria azul.

    Evidencia contra: a Core 5.6 escreveu 0x7AC6 (o pre-invertido de
    RGB(197,206,213), prateado) e o mantenedor viu DOURADO -- que e
    exatamente RGB(123,89,49), o 0x7AC6 lido DIRETO.

    As duas nao podem estar certas.

O TESTE
    Pinta a casca da bateria com 0x07E0, que e inequivoco dos dois lados:

        lido direto      RGB(  0,255,  0)   VERDE puro
        pre-invertido    RGB(230,  0, 57)   VERMELHO

    casca VERDE     -> nao ha inversao. As cores se escrevem DIRETAS,
                       e a Core 5.6 tem que usar 0xC67A.
    casca VERMELHA  -> a inversao existe, o 0x7AC6 esta certo, e o
                       "dourado" tem outra explicacao.

    Uma gravacao, resposta definitiva, e fecha uma regra que o projeto
    carrega desde setembro sem nunca ter sido verificada na tela.

USO
    python3 tools/diag_cor_inversao.py entrada.bin saida.bin

ATENCAO
    Imagem de DIAGNOSTICO. A casca da bateria fica verde ou vermelha o
    tempo todo. Reversivel: volte para a Core 5.6.
"""
import sys

BASE_XIP = 0x00C00000
TESTE = 0x07E0
# os dois `movw r1, #0x7ac6` que a Core 5.6 instalou na casca
SITIOS = [0x00D23686, 0x00D236CA]
ATUAL = bytes.fromhex("47f6c621")     # movw r1, #0x7ac6


def movw(rd, valor):
    imm4, i = (valor >> 12) & 0xF, (valor >> 11) & 1
    imm3, imm8 = (valor >> 8) & 7, valor & 0xFF
    return ((0xF240 | (i << 10) | imm4).to_bytes(2, "little")
            + ((imm3 << 12) | (rd << 8) | imm8).to_bytes(2, "little"))


def mostra(v):
    r = ((v >> 11) & 0x1F) * 255 // 31
    g = ((v >> 5) & 0x3F) * 255 // 63
    b = (v & 0x1F) * 255 // 31
    return f"RGB({r:>3},{g:>3},{b:>3})"


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: diag_cor_inversao.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")

    novo = movw(1, TESTE)
    for addr in SITIOS:
        off = addr - BASE_XIP
        if bytes(img[off:off + 4]) != ATUAL:
            sys.exit(f"erro: {addr:#x} tem {img[off:off+4].hex()}, "
                     f"esperava {ATUAL.hex()} — nao e a Core 5.6?")
        img[off:off + 4] = novo
        print(f"  {addr:#010x}  movw r1, #{TESTE:#06x}")

    open(sys.argv[2], "wb").write(img)
    inv = ((TESTE & 0xFF) << 8) | (TESTE >> 8)
    print(f"\n  se a casca ficar VERDE    {mostra(TESTE)}  -> NAO ha inversao")
    print(f"  se ficar VERMELHA         {mostra(inv)}  -> a inversao existe")
    print(f"\n  escrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
