#!/usr/bin/env python3
"""
patch_bateria_verde.py — a barra da bateria ganha o verde do Marte

O QUE E, E O QUE NAO E
    O icone da bateria NAO e uma imagem: e um glifo da fonte de icones
    (U+E626) mais um `lv_bar` filho que desenha o nivel. O glifo e
    MONOCROMATICO, entao o icone colorido do Marte (21x13, casca
    metalica, degrade) nao tem como ser reproduzido sem trocar o rotulo
    por um objeto de imagem -- o que e codigo, nao dado.

    Este patch faz a parte que E dado: a COR da barra de nivel.

MEDIDO
    0x00D22682  movw r1, #0xcf5d   -> bl 0x00D4D092 (BG_COLOR)
                com r2 = 0x20000 = LV_PART_INDICATOR

    0xCF5D e pre-invertido (LV_COLOR_16_SWAP, ver COLOR_SOURCE.md §9).
    Invertido = 0x5DCF = RGB(90,186,123) -- ja um verde, mas azulado.

    O verde do Marte, medido em marte/adaptado/icones/battery_09.png,
    e o tom mais usado no preenchimento: RGB(115,218,57).

USO
    python3 tools/patch_bateria_verde.py entrada.bin saida.bin

LIMITACOES
    - So a barra de nivel. A casca continua sendo o glifo da fonte.
    - A cor de bateria fraca (0x00F8 = vermelho, em view_set_icon_bat
      0x00D23666) NAO e tocada: o vermelho do Marte tambem e vermelho.
"""
import sys

BASE_XIP = 0x00C00000
SITIO    = 0x00D22682
ANTES    = bytes.fromhex("4cf65d71")        # movw r1, #0xcf5d
MARTE    = (115, 218, 57)                   # battery_09.png, o verde do nivel


def to565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def pre_inverte(v):
    return ((v & 0xFF) << 8) | (v >> 8)


def movw(rd, valor):
    """MOVW T3: imm4:i:imm3:imm8"""
    imm4 = (valor >> 12) & 0xF
    i = (valor >> 11) & 1
    imm3 = (valor >> 8) & 7
    imm8 = valor & 0xFF
    w1 = 0xF240 | (i << 10) | imm4
    w2 = (imm3 << 12) | (rd << 8) | imm8
    return w1.to_bytes(2, "little") + w2.to_bytes(2, "little")


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: patch_bateria_verde.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")
    off = SITIO - BASE_XIP
    if bytes(img[off:off + 4]) != ANTES:
        sys.exit(f"erro: {SITIO:#x} tem {img[off:off+4].hex()}, "
                 f"esperava {ANTES.hex()} — imagem errada?")

    cor = to565(*MARTE)
    novo = movw(1, pre_inverte(cor))
    img[off:off + 4] = novo
    open(sys.argv[2], "wb").write(img)

    def mostra(v):
        r = ((v >> 11) & 0x1F) * 255 // 31
        g = ((v >> 5) & 0x3F) * 255 // 63
        b = (v & 0x1F) * 255 // 31
        return f"RGB({r},{g},{b})"

    antiga = 0x5DCF
    print(f"  {SITIO:#010x}  movw r1, #{antiga ^ 0:#06x} -> #{pre_inverte(cor):#06x}")
    print(f"     antes  {mostra(antiga)}   (verde azulado de fabrica)")
    print(f"     agora  {mostra(cor)}   (o verde do Marte)")
    print(f"\n  escrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
