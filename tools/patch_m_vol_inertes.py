#!/usr/bin/env python3
"""
patch_m_vol_inertes.py — M e VOL param de pular 3 linhas na tela inicial

O PROBLEMA
    Na roda fisica:

                M          <- em cima
        |<<    >||    >>|
               VOL         <- embaixo

    `M` e `VOL` pulam TRES linhas na tela inicial. Nao e defeito: e a
    semantica da GRADE 3x3 de fabrica, onde cima/baixo pulava uma linha
    inteira de tres celulas. Com a home virada LISTA, pular 3 numa lista
    de 9 com rotacao ficou imprevisivel.

    Mantenedor: "quando navego pelo menu pelas setas ele anda certinho,
    quando uso as teclas M e vol eles pulam 3 em 3".

A DECISAO
    Do mantenedor: **M e VOL nao fazem nada** na tela inicial.

    Foi preferida a converter para +-1 porque nao introduz redundancia,
    e a mexer em volume porque isso e outra medicao. E a de menor risco
    das quatro consideradas.

COMO
    Nao reescreve os ramos. Manda as duas teclas para a saida de "tecla
    nao reconhecida" que o proprio firmware ja tem:

        0x00D2E992  ldr r1,[pc,#0x1f4] / ldr r0,[pc,#0x1f8]
                    pop.w {r4,r5,r6,lr}
                    b.w #0x2b0            (registra e retorna)

    Dois bytes em cada despacho:

        0x00D2E9F2  beq #0x00D2EAEE  ->  beq #0x00D2E992   (key_id 0x81)
        0x00D2EA00  bne #0x00D2E992  ->  b   #0x00D2E992   (key_id 0xA0)

    O frame e desfeito pelo `pop.w` da propria saida -- nao ha pilha
    desbalanceada aqui (ver tools/check_pilha.py e a Core 4.5).

USO
    python3 tools/patch_m_vol_inertes.py entrada.bin saida.bin

LIMITACOES
    - So afeta `page_home_event_cb`. Dentro das outras telas M e VOL
      seguem como estavam.
    - Qual das duas teclas e 0xA0 e qual e 0x81 continua NAO
      DETERMINADO (`docs/BUTTON_ANALYSIS.md`). Como as duas ficam
      inertes, nao precisa saber.
"""
import sys

BASE_XIP = 0x00C00000
SAIDA    = 0x00D2E992        # "tecla nao reconhecida": registra e retorna
PATCHES  = [
    (0x00D2E9F2, bytes.fromhex("7cd0"), bytes.fromhex("ced0"),
     "key_id 0x81: beq 0x00D2EAEE -> beq 0x00D2E992"),
    (0x00D2EA00, bytes.fromhex("c7d1"), bytes.fromhex("c7e7"),
     "key_id 0xA0: bne 0x00D2E992 -> b   0x00D2E992"),
]


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: patch_m_vol_inertes.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")

    for addr, antes, depois, texto in PATCHES:
        off = addr - BASE_XIP
        if bytes(img[off:off + 2]) != antes:
            sys.exit(f"erro: {addr:#x} tem {img[off:off+2].hex()}, "
                     f"esperava {antes.hex()} — imagem errada?")
        img[off:off + 2] = depois
        print(f"  {addr:#010x}  {texto}")

    open(sys.argv[2], "wb").write(img)
    print(f"\n  M e VOL ficam inertes na tela inicial")
    print(f"  escrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
