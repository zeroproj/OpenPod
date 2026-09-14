#!/usr/bin/env python3
"""
patch_sonda.py — faz o aparelho MOSTRAR um valor na tela.

POR QUE

    Quatro hipoteses minhas sobre a faixa clara e tres sobre o Extras
    foram derrubadas pelo aparelho. O padrao e claro: eu venho adivinhando
    valores que o aparelho conhece. Falta observacao, nao analise.

    Nos controlamos a interface. Entao da para pedir para ela contar.

O QUE FAZ

    1. Ao entrar no despacho do Extras, grava em hexadecimal os tres
       campos da mensagem que importam:

           msg[0x08]  pagina de origem
           msg[0x0a]  o campo que eu troquei por 2
           msg[0x0c]  o INDICE DO ITEM — o valor que eu suponho ser 0..5

       Resultado: seis digitos hex num buffer da area livre.

    2. O titulo da pagina Extras passa a mostrar esse buffer em vez da
       palavra "Extras".

    Fluxo de uso: entra no Extras, escolhe um item, volta ao Extras — o
    titulo mostra o que foi enviado.

O QUE ISSO RESOLVE

    Se `msg[0x0c]` nao for 0..5, o meu `cmp r2,#5` esta rejeitando itens
    validos, e a causa do "tres funcionam, tres nao" aparece na hora.
    Se for 0..5, o problema esta depois, nos handlers — e eu paro de
    procurar no lugar errado.

    A sonda fica no aparelho e serve para a proxima investigacao tambem.

MONTAGEM

    Usa `tools/asm.py` (clang). As rotinas NAO sao codificadas a mao —
    foi assim que entraram os dois bugs de encoding do projeto.

USO
    python3 tools/patch_sonda.py \\
        --in  firmware/WORKING/GN438_openpod_v075_carimbado.bin \\
        --out firmware/WORKING/GN438_openpod_v076.bin [--dry-run]

SEGURANCA
    - exige as duas areas livres (0xFF) antes de escrever;
    - exige o `bl get_string` da rotina de titulos em 0x001A5032;
    - exige a rotina do Extras como o patch_extras_fix2 deixou;
    - desmonta tudo o que montou e imprime, para conferencia humana;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import monta                                    # noqa: E402

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
FLASH_SIZE = 0x200000

SONDA_STR = 0x001A5A60      # devolve o buffer quando a pagina e 0x53
SONDA_GRV = 0x001A5A80      # grava os tres campos em hex
BUF = 0x001A5B00
EXTRAS = 0x001A5900
GANCHO_TITULO = 0x001A5032  # o `bl get_string` da rotina de titulos
GET_STRING = 0x00D2108C
DESPACHO = 0x00D00FB2
PAGINA_EXTRAS = 0x53
MAPA = [5, 7, 11, 4, 6, 8]

FONTE_STR = f"""
.syntax unified
.thumb
    ldrb r1, [r4]
    cmp  r1, #{PAGINA_EXTRAS}
    beq  Lsonda
    ldr  r1, =0x{GET_STRING | 1:X}
    bx   r1
Lsonda:
    ldr  r0, =0x{BUF + XIP:X}
    bx   lr
.ltorg
"""

FONTE_GRV = f"""
.syntax unified
.thumb
    push {{r0,r1,r2,r3,lr}}
    ldr  r1, =0x{BUF + XIP:X}
    movs r2, #0
Lloop:
    lsls r0, r2, #1
    adds r0, #8
    ldrb r3, [r4, r0]
    lsrs r0, r3, #4
    bl   Lnib
    strb r0, [r1]
    adds r1, #1
    and  r0, r3, #15
    bl   Lnib
    strb r0, [r1]
    adds r1, #1
    adds r2, #1
    cmp  r2, #3
    blt  Lloop
    movs r0, #0
    strb r0, [r1]
    pop  {{r0,r1,r2,r3,pc}}
Lnib:
    cmp  r0, #10
    blt  Ldig
    adds r0, #55
    bx   lr
Ldig:
    adds r0, #48
    bx   lr
.ltorg
"""


def fonte_extras(glob):
    return f"""
.syntax unified
.thumb
    ldr  r1, =0x{SONDA_GRV + XIP | 1:X}
    blx  r1
    cmp  r2, #5
    bhi  Lsai
    adr  r3, Lmapa
    ldrb r3, [r3, r2]
    strh r3, [r4, #0xc]
    movs r1, #2
    strh r1, [r4, #0xa]
    ldr  r6, =0x{glob:X}
    ldr  r3, =0x{DESPACHO | 1:X}
    bx   r3
Lsai:
    pop.w {{r4,r5,r6,r7,r8,pc}}
.p2align 2
Lmapa:
    .byte {','.join(str(x) for x in MAPA)},0,0
.ltorg
"""


def bl(origem, destino):
    off = destino - (origem + 4)
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = (0xD000 | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11)
           | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def main():
    ap = argparse.ArgumentParser(description="sonda na tela")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.src == a.dst:
        sys.exit("origem e destino iguais")
    orig = open(a.src, "rb").read()
    if len(orig) != FLASH_SIZE:
        sys.exit(f"tamanho inesperado: {len(orig)}")
    data = bytearray(orig)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    erros = []
    # o gancho do titulo tem de ser mesmo o bl get_string
    k = next(md.disasm(bytes(data[GANCHO_TITULO:GANCHO_TITULO + 4]),
                       GANCHO_TITULO + XIP), None)
    if not (k and k.mnemonic == "bl"
            and int(k.op_str.strip("#"), 0) == GET_STRING):
        erros.append(f"0x{GANCHO_TITULO:06X} nao e `bl get_string`")
    for base, tam, nome in ((SONDA_STR, 0x20, "sonda_string"),
                            (SONDA_GRV, 0x60, "sonda_grava"),
                            (BUF, 0x20, "buffer")):
        if any(v != 0xFF for v in data[base:base + tam]):
            erros.append(f"area de {nome} (0x{base:06X}) nao esta livre")
    if True:
        pass
    glob = struct.unpack_from("<I", data, 0x001A5920)[0]
    if not (XIP <= glob < XIP + FLASH_SIZE or 0x800000 <= glob < 0x900000):
        erros.append(f"ponteiro global improvavel: 0x{glob:08X}")
    if erros:
        print("RECUSADO:")
        for e in erros:
            print("   -", e)
        return 1

    b_str = monta(FONTE_STR)
    b_grv = monta(FONTE_GRV)
    b_ext = monta(fonte_extras(glob))

    print()
    print("  SONDA — o aparelho passa a mostrar o que recebe")
    print()
    print(f"  buffer ............ 0x{BUF:06X}")
    print(f"  sonda_string ...... 0x{SONDA_STR:06X}  ({len(b_str)} B)")
    print(f"  sonda_grava ....... 0x{SONDA_GRV:06X}  ({len(b_grv)} B)")
    print(f"  rotina do Extras .. 0x{EXTRAS:06X}  ({len(b_ext)} B)")
    print()
    for nome, base, b in (("sonda_string", SONDA_STR, b_str),
                          ("sonda_grava", SONDA_GRV, b_grv),
                          ("extras", EXTRAS, b_ext)):
        print(f"  --- {nome} (montado pelo clang, desmontado para conferir)")
        for i in md.disasm(b, base + XIP):
            print(f"      {i.address - XIP:06X}  {i.mnemonic:9s} {i.op_str}")
    print()

    # O BUFFER PRECISA NASCER VALIDO.
    #
    # Na primeira versao eu deixei o buffer em 0xFF e o entreguei assim.
    # `lv_label_set_text` saiu lendo memoria atras de um terminador que
    # nao existia e a tela do Extras deixou de abrir. Erro basico, e
    # custou uma gravacao do mantenedor.
    data[BUF:BUF + 8] = b"------\x00\x00"
    data[SONDA_STR:SONDA_STR + len(b_str)] = b_str
    data[SONDA_GRV:SONDA_GRV + len(b_grv)] = b_grv
    data[EXTRAS:EXTRAS + len(b_ext)] = b_ext
    if len(b_ext) < 0x24:
        data[EXTRAS + len(b_ext):EXTRAS + 0x24] = \
            b"\xff" * (0x24 - len(b_ext))
    data[GANCHO_TITULO:GANCHO_TITULO + 4] = bl(GANCHO_TITULO + XIP,
                                               SONDA_STR + XIP)
    print(f"  0x{GANCHO_TITULO:06X}  bl get_string -> bl sonda_string")
    print()
    print("  COMO LER NA TELA (titulo da pagina Extras):")
    print("      PP AA CC   ->   PP = msg[0x08] origem   (esperado 53)")
    print("                      AA = msg[0x0a]          (esperado 02)")
    print("                      CC = msg[0x0c] INDICE   (esperado 00..05)")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X} (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print("  CRC da FIRM: campo intocado (R1)")
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(data))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
