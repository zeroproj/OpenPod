#!/usr/bin/env python3
"""
patch_extras_fix.py — conserta o `patch_extras`: ele matava a mensagem.

O SINTOMA

    Mantenedor, na 2.1: *"ao entrar no Extras, qualquer coisa que eu clico
    nao leva a nada."* Nao e "leva ao lugar errado" como antes da 2.1 —
    e NADA. O patch anterior trocou seis destinos errados por seis
    destinos nenhum, o que e pior.

A CAUSA — uma guarda, achada lendo o codigo, nao adivinhando

    O caminho que chega ao nosso gancho dentro de `pstr_page84_process`
    so e alcancado quando o campo 0x0A da mensagem vale **4**:

        0x0010CC30  ldrh r2, [r4, #0xa]
        0x0010CC36  cmp  r2, #4
        0x0010CC38  beq  0xd0cc70      ; <- ramo onde fica o gancho

    Mas nos mandavamos a mensagem para a ENTRADA de `page1_process`, e a
    primeira coisa que ela faz e exigir que esse mesmo campo valha **2**:

        0x00100F62  ldrh   r2, [r4, #0xa]
        0x00100F64  cmp    r2, #2
        0x00100F66  bne.w  0xd012f6     ; <- sai sem fazer nada

    A mensagem morria ali, antes do `tbh`. A tabela de desvio, o mapa de
    indices e a rotina estavam todos CERTOS — e por isso a auditoria
    estatica anterior nao viu nada: ela conferia a tabela, nao o trajeto.

A CORRECAO QUE **NAO** FOI FEITA, E POR QUE

    O obvio seria escrever 2 nesse campo. **Seria um bug silencioso.**
    A cauda que abre a pagina destino le esse campo e o repassa:

        0x00101036  ldrh r2, [r4, #0xc]   ; ctrl_id
        0x00101038  ldrh r1, [r4, #0xa]   ; <== LE
        0x0010103A  ldrh r0, [r4, #8]     ; pagina de origem

    E o 0x0A junto com o 0x08 e o que faz o "voltar" retornar ao **Extras**
    em vez da home. Forcar 2 abriria a tela certa e quebraria o voltar —
    o tipo de estrago que so aparece tres versoes depois.

O QUE FAZ

    Entra DEPOIS das guardas, direto no despacho, preservando o campo:

        0x00100FB2  ldrh r3, [r4, #0xc]
        0x00100FB4  cmp  r3, #0xb
        0x00100FB6  bhi.w ...
        0x00100FBA  tbh  [pc, r3, lsl #1]

    As guardas puladas ja foram feitas, de forma identica, pela propria
    `pstr_page84_process` antes do gancho ([0x0e]==1 em 0x0010CC70 e
    [0x14]==4 em 0x0010CC76). Nao se esta relaxando verificacao nenhuma.

    Tambem monta `r6` com o ponteiro global, que `page1_process` montaria
    em 0x00100F52 e que a cauda 0x0010101C **le antes de escrever**:

        0x00101244  0x00823D05   (literal de page1_process)
        0x0010CD74  0x00823D05   (literal de pstr_page84_process)

    Os dois lados carregam o mesmo valor e o usam igual (`ldrb [r3,#0xa]`
    para ler a pagina corrente), o que confirma que e o mesmo objeto.

USO
    python3 tools/patch_extras_fix.py \\
        --in  firmware/WORKING/GN438_openpod_v072.bin \\
        --out firmware/WORKING/GN438_openpod_v073.bin [--dry-run]

SEGURANCA
    - exige a rotina QUEBRADA byte a byte em 0x001A5900; se nao for
      exatamente ela, RECUSA (nao adivinha o estado);
    - exige o gancho `b.w 0x00DA5900` em 0x0010CC7E;
    - exige que 0x00100FB2 seja mesmo o `ldrh r3,[r4,#0xc]` do despacho;
    - exige que os dois literais do ponteiro global sejam iguais;
    - desmonta a rotina montada e confere COM OPERANDOS, sem filtrar as
      linhas de literal;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.

LIMITACOES
    Muda DESPACHO de pagina. Grave e teste SOZINHA (MENU_LISTA.md 14).
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

BLOB = 0x001A5900
DESPACHO = 0x00D00FB2          # ldrh r3,[r4,#0xc] ; cmp #0xb ; bhi ; tbh
DESPACHO_OFF = 0x00100FB2
DESPACHO_ESPERADO = bytes.fromhex("a389" "0b2b")   # ldrh r3,[r4,#0xc];cmp
GANCHO_OFF = 0x0010CC7E
LIT_A, LIT_B = 0x00101244, 0x0010CD74               # ponteiro global
MAPA = [5, 7, 11, 4, 6, 8]
NOMES = ["Video", "Gravacao", "Radio", "Livro digital", "Bluetooth",
         "Ver pastas"]


def bw(origem, destino, link=False):
    off = destino - (origem + 4)
    if off & 1 or not (-(1 << 24) <= off < (1 << 24)):
        raise ValueError("fora de alcance")
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = ((0xD000 if link else 0x9000)
           | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def monta_quebrada(base, page1_entry=0x00D00F3C):
    """Reproduz exatamente o que o patch_extras gravou, para poder exigir
       esse estado antes de sobrescrever."""
    c = bytearray()

    def h(*hw):
        for x in hw:
            c.extend(struct.pack("<H", x))
    h(0x2A05)
    o = len(c)
    h(0x0000)
    p = len(c)
    h(0x0000)
    h(0x5C9B, 0x81A3, 0x4620, 0xE8BD, 0x41F0)
    c.extend(bw(base + len(c), page1_entry))
    sai = len(c)
    h(0xE8BD, 0x81F0)
    struct.pack_into("<H", c, o, 0xD800 | (((sai - (o + 4)) >> 1) & 0xFF))
    while len(c) % 4:
        h(0xBF00)
    lit = len(c)
    c.extend(bytes(MAPA) + b"\0\0")
    struct.pack_into("<H", c, p,
                     0xA300 | (((base + lit) - ((base + p + 4) & ~3)) >> 2))
    return bytes(c)


def monta(base, global_ptr):
    c = bytearray()

    def h(*hw):
        for x in hw:
            c.extend(struct.pack("<H", x))
    h(0x2A05)                      # cmp  r2, #5
    o_bhi = len(c)
    h(0x0000)                      # bhi  sai
    p_adr = len(c)
    h(0x0000)                      # adr  r3, MAPA
    h(0x5C9B)                      # ldrb r3, [r3, r2]
    h(0x81A3)                      # strh r3, [r4, #0xc]   ctrl_id
    p_ldr = len(c)
    h(0x0000)                      # ldr  r6, =global
    c.extend(bw(base + len(c), DESPACHO))    # b.w  despacho (SEM pop)
    sai = len(c)
    h(0xE8BD, 0x81F0)              # sai: pop.w {r4-r8, pc}
    struct.pack_into("<H", c, o_bhi,
                     0xD800 | (((sai - (o_bhi + 4)) >> 1) & 0xFF))
    while len(c) % 4:
        h(0xBF00)
    mapa = len(c)
    c.extend(bytes(MAPA) + b"\0\0")
    glob = len(c)
    c.extend(struct.pack("<I", global_ptr))
    struct.pack_into("<H", c, p_adr,
                     0xA300 | (((base + mapa) - ((base + p_adr + 4) & ~3)) >> 2))
    struct.pack_into("<H", c, p_ldr,
                     0x4E00 | (((base + glob) - ((base + p_ldr + 4) & ~3)) >> 2))
    return bytes(c)


ESPERADO = ["cmp r2, #5", "bhi #0xda5910", "adr r3, #0xc",
            "ldrb r3, [r3, r2]", "strh r3, [r4, #0xc]", "ldr r6, [pc, #0x10]",
            "b.w #0xd00fb2", "pop.w {r4, r5, r6, r7, r8, pc}"]


def main():
    ap = argparse.ArgumentParser(description="conserta a rota do Extras")
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
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    erros = []
    quebrada = monta_quebrada(BLOB + XIP)
    atual = bytes(data[BLOB:BLOB + len(quebrada)])
    if atual != quebrada:
        erros.append("0x001A5900 nao contem a rotina do patch_extras\n"
                     f"      esperado {quebrada.hex()}\n"
                     f"      achei    {atual.hex()}")
    if bytes(data[GANCHO_OFF:GANCHO_OFF + 4]) != bw(GANCHO_OFF + XIP,
                                                    BLOB + XIP):
        erros.append(f"gancho em 0x{GANCHO_OFF:06X} nao aponta para a rotina")
    if bytes(data[DESPACHO_OFF:DESPACHO_OFF + 4]) != DESPACHO_ESPERADO:
        erros.append(f"0x{DESPACHO_OFF:06X} nao e o despacho esperado")
    g1 = struct.unpack_from("<I", data, LIT_A)[0]
    g2 = struct.unpack_from("<I", data, LIT_B)[0]
    if g1 != g2:
        erros.append(f"os dois literais do global divergem: "
                     f"0x{g1:08X} != 0x{g2:08X}")

    rot = monta(BLOB + XIP, g1)
    got = [f"{i.mnemonic} {i.op_str}".strip()
           for i in md.disasm(rot, BLOB + XIP)][:len(ESPERADO)]
    if got != ESPERADO:
        erros.append(f"rotina nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for e in erros:
            print("   -", e)
        return 1

    print()
    print("  EXTRAS — a mensagem parava numa guarda")
    print()
    print(f"  antes:  b.w page1_process (0x00100F3C)  -> exige [0xa]==2,")
    print( "          mas o Extras chega com [0xa]==4  -> saia sem fazer nada")
    print(f"  agora:  b.w despacho       (0x{DESPACHO_OFF:06X})  -> tbh direto")
    print(f"  campo [0xa] PRESERVADO (a cauda 0x00101036 o repassa: "
          "e o que faz o voltar retornar ao Extras)")
    print(f"  r6 montado com o global 0x{g1:08X} (a cauda 0x0010101C o le)")
    print()
    print("  MAPA  indice do Extras -> ctrl_id da home")
    for i, (c, n) in enumerate(zip(MAPA, NOMES)):
        print(f"    {i}  {n:14s} -> {c}")
    print()
    print("  ALTERACOES")
    if len(rot) > len(quebrada):
        sys.exit("rotina nova maior que a antiga — revisar area livre")
    data[BLOB:BLOB + len(quebrada)] = rot + b"\xff" * (len(quebrada) - len(rot))
    print(f"    0x{BLOB:06X}  rotina reescrita {len(rot)} B")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X} (R1)")
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
