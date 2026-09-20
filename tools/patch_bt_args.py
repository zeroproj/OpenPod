#!/usr/bin/env python3
"""
patch_bt_args.py — o Extras passa a abrir o Bluetooth como a fabrica.

O DEFEITO
    Entrar no Bluetooth pelo Extras REINICIA o aparelho. De fabrica o
    Bluetooth funciona inteiro.

A CAUSA — argumentos, nao preparacao

    De fabrica (0x00D012D6, item 6 da home):

        movs r3, #0x23     pagina 35
        movs r2, #6        indice do item na home
        movs r1, #2
        b.w  0xd0dae0

    No nosso despacho do Extras (0x00DA622C):

        ldrb r3, [tabela_C, r5]   r3 = 35            certo
        movs r2, #0                                  errado, fabrica usa 6
        ldrh r1, [r4, #0xa]                          errado, fabrica usa 2
        ldrh r0, [r4, #8]

    A pagina esta certa. Os argumentos nao.

    Levantado nos doze itens da home de fabrica: r1 e sempre 2 e r2 e o
    INDICE do item na home. Bluetooth e o 7o icone, entao 6.

    O mesmo r2 ja quebrou o Configurar nas Core 4.8/4.9 -- a DIAG 7
    provou. La o efeito foi a pagina nao abrir; aqui e reiniciar.

POR QUE SO O BLUETOOTH

    Dois tipos de item na home de fabrica:

        A  verifica, prepara, b 0xd01036
           Gravacao, Radio, Livro digital, Imagem, Pastas
        B  movs r3,#pag; movs r2,#indice; movs r1,#2
           Bluetooth

    Os cinco do tipo A ja tem rotina de preparacao no nosso despacho. O
    Bluetooth e o unico do tipo B: o que falta a ele nao e preparacao,
    sao argumentos.

O CONSERTO

    Os quatro bytes de `movs r2,#0` + `ldrh r1,[r4,#0xa]` viram um
    `b.w` para uma rotina de 22 bytes na area livre:

        movs r2, #0
        ldrh r1, [r4, #0xa]
        cmp  r5, #4            indice do Bluetooth no Extras
        bne  sai
        movs r1, #2
        movs r2, #6
    sai:
        ldrh r0, [r4, #8]
        pop.w {r4,r5,r6,r7,r8,lr}
        b.w  0xd0dae0

    Os outros cinco itens passam pelo `bne` e saem iguais a antes.

USO
    python3 tools/patch_bt_args.py --in <fw.bin> --out <novo.bin>

DEPENDENCIAS
    capstone

SEGURANCA
    - confere os quatro bytes de origem antes de trocar;
    - desmonta a rotina inteira de volta e compara instrucao a
      instrucao com o esperado;
    - so escreve em area 0xFF virgem;
    - conferir depois com check_pilha.py: a rotina NAO tem quadro
      proprio de proposito -- ela e um salto de cauda que herda o
      quadro do despacho e executa o mesmo pop que ele executava.
"""
import argparse
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

XIP = 0x00C00000
TAM = 2 * 1024 * 1024
CAUDA = 0x00DA6230                       # movs r2,#0 ; ldrh r1,[r4,#0xa]
ORIGEM = bytes.fromhex("00226189")
ABRE = 0x00D0DAE0
IDX_BT = 4

ESPERADO = [
    "movs r2, #0", "ldrh r1, [r4, #0xa]", "cmp r5, #4", "bne #0x%x",
    "movs r1, #2", "movs r2, #6", "ldrh r0, [r4, #8]",
    "pop.w {r4, r5, r6, r7, r8, lr}", "b.w #0x%x",
]


def bw(de, para):
    off = (para - (de + 4)) >> 1
    s = (off >> 23) & 1
    i1 = (off >> 22) & 1
    i2 = (off >> 21) & 1
    j1 = (~i1 & 1) ^ s
    j2 = (~i2 & 1) ^ s
    return struct.pack("<HH",
                       0xF000 | (s << 10) | ((off >> 11) & 0x7FF),
                       0x9000 | (j1 << 13) | (j2 << 11) | (off & 0x7FF))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAM:
        sys.exit("ABORTADO: %s tem %d bytes, esperado %d" % (a.src, len(d), TAM))
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

    print("=" * 70)
    print("OpenPod — o Extras abre o Bluetooth como a fabrica")
    print("=" * 70)

    o = CAUDA - XIP
    if bytes(d[o:o + 4]) != ORIGEM:
        sys.exit("ABORTADO: 0x%08X nao tem 'movs r2,#0 ; ldrh r1,[r4,#0xa]'."
                 % CAUDA)
    print("  cauda em 0x%08X confere" % CAUDA)

    livre = None
    for k in range(0x1A6100, 0x1A6200):
        if d[k:k + 40] == b"\xff" * 40:
            livre = k + (k & 1)
            break
    if livre is None:
        sys.exit("ABORTADO: nao achei 40 bytes virgens na area livre.")
    h = livre + XIP

    rot = bytearray()
    rot += bytes.fromhex("0022")          # movs r2, #0
    rot += bytes.fromhex("6189")          # ldrh r1, [r4, #0xa]
    rot += bytes.fromhex("042d")          # cmp  r5, #4
    rot += bytes.fromhex("01d1")          # bne  +4
    rot += bytes.fromhex("0221")          # movs r1, #2
    rot += bytes.fromhex("0622")          # movs r2, #6
    rot += bytes.fromhex("2089")          # ldrh r0, [r4, #8]
    rot += bytes.fromhex("bde8f041")      # pop.w {r4,r5,r6,r7,r8,lr}
    rot += bw(h + len(rot), ABRE)         # b.w  0xd0dae0
    d[livre:livre + len(rot)] = rot
    d[o:o + 4] = bw(CAUDA, h)

    print("\n  rotina em 0x%08X (%d bytes):" % (h, len(rot)))
    got = []
    for x in md.disasm(bytes(d[livre:livre + len(rot)]), h):
        got.append("%s %s" % (x.mnemonic, x.op_str))
        print("     0x%08X  %-8s %s" % (x.address, x.mnemonic, x.op_str))
    esp = list(ESPERADO)
    esp[3] = esp[3] % (h + 12)
    esp[8] = esp[8] % ABRE
    if got != esp:
        sys.exit("ABORTADO: a rotina nao desmontou como esperado.\n  %s\n  %s"
                 % (got, esp))

    i = list(md.disasm(bytes(d[o:o + 4]), CAUDA))[0]
    if i.mnemonic != "b.w" or int(i.op_str.replace("#", ""), 16) != h:
        sys.exit("ABORTADO: a cauda nao aponta para a rotina.")
    print("\n  cauda 0x%08X  ->  %s %s" % (CAUDA, i.mnemonic, i.op_str))

    orig = open(a.src, "rb").read()
    mudou = sum(1 for k in range(TAM) if d[k] != orig[k])
    print("  bytes alterados: %d   setor: 0x1A6000" % mudou)
    open(a.dst, "wb").write(bytes(d))
    print("  gravado: %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
