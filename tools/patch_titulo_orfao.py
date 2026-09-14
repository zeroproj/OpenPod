#!/usr/bin/env python3
"""
patch_titulo_orfao.py — o titulo deixa de se acumular na tela.

O QUE AS FOTOS MOSTRARAM

    "Musi(ta5)2" na lista de musicas. "Desligar aparelho" por baixo de
    "Sobre o aparelho". O descanso de tela exibindo "Despertador". E a
    "faixa clara" que eu persegui com quatro hipoteses erradas.

    Nada disso era faixa, nem contador, nem fundo de display. Era **o
    mesmo defeito**: rotulos de titulo se ACUMULANDO na tela.

O MECANISMO

    1. `CRIA_TITULO` (0x00D226AC) cria o rotulo com o pai devolvido por
       `0x00D2139A`, que e uma **camada que sobrevive a troca de pagina**
       — nao e a tela.

    2. `view_clean_all_objs` zera o slot `[0x14]` em `0x00123A6E`:

           0x00123A6C   str r5, [r3, #0x0c]
           0x00123A6E   str r5, [r3, #0x14]    <- so ANULA o ponteiro
           0x00123A70   str r5, [r3, #0x20]

       **Sem apagar o objeto.** Nao ha `lv_obj_del` nesse trecho.

    3. A nossa rotina de titulos so cria quando `[0x14] == 0`. Como o
       slot foi zerado e o rotulo continua vivo na camada, ela cria
       **outro por cima**. A cada troca de pagina, mais um.

E EU PIOREI ISSO SEM PERCEBER

    O `patch_titulos` cortou a guarda em `0x00123E8A`, e aquele ramo era
    justamente quem APAGAVA esse objeto:

        0x00123EA8   bl 0x00D4D350        <- lv_obj_del
        0x00123EAC   ldr r3, [r5]
        0x00123EAE   str r4, [r3, #0x14]

    Eu analisei esse trecho duas vezes, descrevi o caminho de apagar em
    `ARQUITETURA.md` §4.1, e nao liguei que tinha cortado exatamente ele.

A CORRECAO

    A rotina passa a guardar o ponteiro num slot NOSSO, na area livre —
    nao no `[0x14]`, que e zerado pelas nossas costas. E antes de criar
    um titulo novo, **apaga o anterior**.

    A rotina nao cabia mais no espaco original (0x001A5000..0x001A5058,
    88 B, com a tabela logo depois), entao foi realocada para
    0x001A5C00 e o chamador em 0x00123880 passa a apontar para la. A
    tabela pagina->id fica onde esta.

USO
    python3 tools/patch_titulo_orfao.py \\
        --in  firmware/WORKING/GN438_openpod_v076_sonda.bin \\
        --out firmware/WORKING/GN438_openpod_v077.bin [--dry-run]

SEGURANCA
    - exige o chamador `bl 0x00DA5000` em 0x00123880;
    - exige que `view_clean_all_objs` ainda zere o slot sem apagar
      (e a premissa do diagnostico; se mudou, RECUSA);
    - montada pelo clang, desmontada e impressa para conferencia;
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

CHAMADOR = 0x00123880
ROTINA_VELHA = 0x001A5000
ROTINA_NOVA = 0x001A5C00
SLOT = 0x001A5BF0           # o nosso ponteiro, fora do alcance do limpador
TABELA = 0x00DA5058
VIEW_P_PTR = 0x0081CE2C
CRIA_TITULO = 0x00D226AC
GET_STRING = 0x00DA5A60     # a sonda (que faz tail-call ao get_string real)
SET_TEXT = 0x00D5ED94
OBJ_ALIGN = 0x00D4A3A2
OBJ_DEL = 0x00D4D350
LIMPADOR = 0x00123A6E       # str r5,[r3,#0x14] — a premissa do diagnostico


def fonte():
    return f"""
.syntax unified
.thumb
    push {{r4,r5,r6,lr}}
    ldr  r4, =0x{VIEW_P_PTR:X}
    ldr  r4, [r4]
    cmp  r4, #0
    beq  Lfim
    ldrb r0, [r4]
    ldr  r5, =0x{TABELA:X}
Lbusca:
    ldrb r1, [r5]
    cmp  r1, #0
    beq  Lfim
    cmp  r1, r0
    beq  Lachou
    adds r5, #2
    b    Lbusca
Lachou:
    ldr  r3, [r4, #0x14]
    cmp  r3, #0
    bne  Lfim                  @ esta pagina ja tem titulo
    @ --- apaga o orfao da pagina anterior, se houver
    ldr  r6, =0x{SLOT + XIP:X}
    ldr  r0, [r6]
    cmp  r0, #0
    beq  Lcria
    ldr  r1, =0x{OBJ_DEL | 1:X}
    blx  r1
    ldr  r6, =0x{SLOT + XIP:X}
    movs r0, #0
    str  r0, [r6]
Lcria:
    ldr  r4, =0x{VIEW_P_PTR:X}
    ldr  r4, [r4]
    ldrb r6, [r5, #1]
    ldr  r1, =0x{CRIA_TITULO | 1:X}
    blx  r1
    str  r0, [r4, #0x14]
    ldr  r1, =0x{SLOT + XIP:X}
    str  r0, [r1]
    mov  r5, r0
    cmp  r6, #0xff
    beq  Lfim
    mov  r0, r6
    ldr  r1, =0x{GET_STRING | 1:X}
    blx  r1
    mov  r1, r0
    mov  r0, r5
    ldr  r2, =0x{SET_TEXT | 1:X}
    blx  r2
    mov  r0, r5
    movs r1, #2
    mvn  r2, #11
    movs r3, #1
    ldr  r4, =0x{OBJ_ALIGN | 1:X}
    blx  r4
Lfim:
    pop  {{r4,r5,r6,pc}}
.ltorg
"""


def bl(origem, destino):
    off = (destino - (origem + 4)) >> 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    return struct.pack("<HH",
                       0xF000 | (s << 10) | ((off >> 11) & 0x3FF),
                       0xD000 | (((~i1 & 1) ^ s) << 13)
                       | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF))


def main():
    ap = argparse.ArgumentParser(description="titulo orfao")
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
    k = next(md.disasm(bytes(data[CHAMADOR:CHAMADOR + 4]), CHAMADOR + XIP),
             None)
    if not (k and k.mnemonic == "bl"
            and int(k.op_str.strip("#"), 0) == ROTINA_VELHA + XIP):
        erros.append(f"0x{CHAMADOR:06X} nao chama a rotina de titulos")
    # a premissa: o limpador zera o slot SEM apagar
    if bytes(data[LIMPADOR:LIMPADOR + 2]) != bytes.fromhex("5d61"):
        erros.append(f"0x{LIMPADOR:06X} nao e `str r5,[r3,#0x14]` — "
                     "a premissa do diagnostico nao confere")
    for base, tam, nome in ((ROTINA_NOVA, 0xC0, "rotina nova"),
                            (SLOT, 4, "slot")):
        if any(v != 0xFF for v in data[base:base + tam]):
            erros.append(f"area de {nome} (0x{base:06X}) nao esta livre")
    if erros:
        print("RECUSADO:")
        for e in erros:
            print("   -", e)
        return 1

    b = monta(fonte())
    print()
    print("  TITULO ORFAO — o rotulo deixa de se acumular")
    print()
    print(f"  rotina nova ... 0x{ROTINA_NOVA:06X}  ({len(b)} B)")
    print(f"  slot nosso .... 0x{SLOT:06X}  (fora do alcance do limpador)")
    print(f"  chamador ...... 0x{CHAMADOR:06X}")
    print()
    for i in md.disasm(b, ROTINA_NOVA + XIP):
        print(f"      {i.address - XIP:06X}  {i.mnemonic:9s} {i.op_str}")
    print()
    data[ROTINA_NOVA:ROTINA_NOVA + len(b)] = b
    data[SLOT:SLOT + 4] = b"\x00\x00\x00\x00"
    data[CHAMADOR:CHAMADOR + 4] = bl(CHAMADOR + XIP, ROTINA_NOVA + XIP)
    print(f"  0x{CHAMADOR:06X}  bl 0x{ROTINA_VELHA:06X} -> "
          f"bl 0x{ROTINA_NOVA:06X}")

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
