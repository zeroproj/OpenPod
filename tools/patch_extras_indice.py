#!/usr/bin/env python3
"""
patch_extras_indice.py — o Extras passa o indice CERTO para cada item.

O DEFEITO (um bug, quatro sintomas — docs/EXTRAS_INDICE.md)
    O despacho do Extras passa sub=0 para os seis itens. A fabrica passa
    o indice que o item tem NA HOME dela:

        nosso indice   item            pagina   sub de fabrica
        0              Gravacao        24       2
        1              Radio           26       3
        2              Livro digital   12       4
        3              Imagem          21       5
        4              Bluetooth       35       6
        5              Pastas          34       0

    Sintomas: Livro/Imagem nao atualizam a biblioteca (a varredura
    "Lendo arquivos..." nao dispara direito), Bluetooth reinicia ao
    entrar nas opcoes, Pastas acerta por acidente (sub 0 = 0).

POR QUE A BETA 10 QUEBROU, E POR QUE ESTE NAO QUEBRA
    A Beta 10 testava `cmp r5,#4` NA CAUDA, DEPOIS do `blx r3` da
    preparacao — r5 podia estar corrompido ali. A Beta 13 provou no
    aparelho (2026-09-21) que o salto e a area livre funcionam; o erro
    era a logica. Este patch:

        - nao usa r5 depois do blx (a reescrita acontece ANTES de
          qualquer preparacao, logo apos `mov r5,r2`);
        - nao tem cmp nenhum — a tabela cobre os seis uniformemente;
        - nao toca em r1 (a primitiva 0x00D0DAE0 nem propaga r1; so
          r0=origem, r2=sub, r3=pagina chegam a pagina).

O CONSERTO — dois pontos, um campo

    1. INSERCAO em 0x00DA6206 (4 bytes: `mov r5,r2 ; movs r0,#0x53`
       viram um b.w para a area livre):

           mov  r5, r2              ; os dois bytes substituidos,
           movs r0, #0x53           ; reproduzidos aqui
           ldr  r3, [pc, #8]        ; -> tabela_sub
           ldrb r3, [r3, r5]
           strh r3, [r4, #0xc]      ; o campo que o trampolim 0x00D01036 le
           b.w  0x00DA620A          ; volta para o bl 0xd0d9e8

       Vale para Livro e Imagem, cujas preparacoes saltam para o
       trampolim 0x00D01036 (que le r2 de [r4,#0xc]).

    2. CAUDA em 0x00DA6230: `movs r2,#0` (0022) vira
       `ldrh r2,[r4,#0xc]` (A289). Dois bytes, in-place, sem salto.

       Vale para Gravacao, Radio (a preparacao retorna), Bluetooth e
       Pastas, que chegam a cauda.

    Nada entre 0x00DA6206 e as preparacoes le [r4,#0xc] esperando o
    indice nosso: as tabelas A/B usam r5, que fica intacto.

USO
    python3 tools/patch_extras_indice.py --in <beta12.bin> --out <novo.bin>

DEPENDENCIAS
    capstone

SEGURANCA
    - confere os bytes de origem nos dois pontos antes de trocar;
    - so escreve em area 0xFF virgem;
    - desmonta a rotina de volta e compara instrucao a instrucao;
    - recusa imagem cuja cauda ja esteja remendada (Beta 10/11/13 tem
      um b.w no lugar dos 4 bytes originais — usar a Beta 12 de base);
    - depois: check_branch_targets.py e check_pilha.py.
"""
import argparse
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

XIP = 0x00C00000
TAM = 2 * 1024 * 1024

INSERCAO = 0x00DA6206          # mov r5,r2 ; movs r0,#0x53
ORIGEM_INS = bytes.fromhex("15465320")
VOLTA = 0x00DA620A             # bl 0xd0d9e8 (logo depois)

CAUDA = 0x00DA6230             # movs r2,#0
ORIGEM_CAUDA = bytes.fromhex("0022")
LDRH_R2 = bytes.fromhex("a289")        # ldrh r2, [r4, #0xc]

TABELA_SUB = bytes([2, 3, 4, 5, 6, 0])

ESPERADO = [
    "mov r5, r2", "movs r0, #0x53", "ldr r3, [pc, #8]",
    "ldrb r3, [r3, r5]", "strh r3, [r4, #0xc]", "b.w #0x%x",
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
    print("OpenPod — o Extras passa o indice certo para cada item")
    print("=" * 70)

    o = INSERCAO - XIP
    if bytes(d[o:o + 4]) != ORIGEM_INS:
        sys.exit("ABORTADO: 0x%08X nao tem 'mov r5,r2 ; movs r0,#0x53'."
                 % INSERCAO)
    print("  ponto de insercao 0x%08X confere" % INSERCAO)

    c = CAUDA - XIP
    if bytes(d[c:c + 2]) != ORIGEM_CAUDA:
        sys.exit("ABORTADO: cauda 0x%08X nao tem 'movs r2,#0' — esta "
                 "imagem ja esta remendada? Use a Beta 12 de base." % CAUDA)
    print("  cauda 0x%08X confere (movs r2,#0)" % CAUDA)

    livre = None
    for k in range(0x1A6100, 0x1A6200, 4):
        if d[k:k + 32] == b"\xff" * 32:
            livre = k
            break
    if livre is None:
        sys.exit("ABORTADO: nao achei 32 bytes virgens na area livre.")
    h = livre + XIP

    rot = bytearray()
    rot += bytes.fromhex("1546")          # mov  r5, r2
    rot += bytes.fromhex("5320")          # movs r0, #0x53
    rot += bytes.fromhex("024b")          # ldr  r3, [pc, #8] -> tabela
    rot += bytes.fromhex("5b5d")          # ldrb r3, [r3, r5]
    rot += bytes.fromhex("a381")          # strh r3, [r4, #0xc]
    rot += bw(h + len(rot), VOLTA)        # b.w  volta
    rot += b"\xbf\x00"                    # alinhamento
    tab_off = livre + len(rot)
    rot += TABELA_SUB                     # 6 bytes
    rot += b"\xff" * ((4 - len(rot) % 4) % 4)
    assert (h + 16) - ((h + 8) & ~3) == 8, "tabela fora do alcance do ldr"
    d[livre:livre + len(rot)] = rot
    d[o:o + 4] = bw(INSERCAO, h)
    d[c:c + 2] = LDRH_R2

    print("\n  rotina em 0x%08X (%d bytes), tabela em 0x%08X:"
          % (h, 14, tab_off + XIP))
    got = []
    for x in md.disasm(bytes(d[livre:livre + 14]), h):
        got.append("%s %s" % (x.mnemonic, x.op_str))
        print("     0x%08X  %-8s %s" % (x.address, x.mnemonic, x.op_str))
    esp = list(ESPERADO)
    esp[5] = esp[5] % VOLTA
    if got != esp:
        sys.exit("ABORTADO: a rotina nao desmontou como esperado.\n  %s\n  %s"
                 % (got, esp))
    if bytes(d[tab_off:tab_off + 6]) != TABELA_SUB:
        sys.exit("ABORTADO: a tabela nao gravou como esperado.")
    print("  tabela_sub:", list(TABELA_SUB))

    i = list(md.disasm(bytes(d[o:o + 4]), INSERCAO))[0]
    if i.mnemonic != "b.w" or int(i.op_str.replace("#", ""), 16) != h:
        sys.exit("ABORTADO: a insercao nao aponta para a rotina.")
    print("\n  insercao 0x%08X  ->  %s %s" % (INSERCAO, i.mnemonic, i.op_str))

    i = list(md.disasm(bytes(d[c:c + 2]), CAUDA))[0]
    if i.mnemonic != "ldrh" or i.op_str != "r2, [r4, #0xc]":
        sys.exit("ABORTADO: a cauda nao virou 'ldrh r2,[r4,#0xc]'.")
    print("  cauda    0x%08X  ->  %s %s" % (CAUDA, i.mnemonic, i.op_str))

    orig = open(a.src, "rb").read()
    mudou = sum(1 for k in range(TAM) if d[k] != orig[k])
    print("  bytes alterados: %d   setor: 0x1A6000" % mudou)
    open(a.dst, "wb").write(bytes(d))
    print("  gravado: %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
