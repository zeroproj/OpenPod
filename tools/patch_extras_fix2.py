#!/usr/bin/env python3
"""
patch_extras_fix2.py — o campo 0x0A tem de valer 2. Eu tinha decidido o
                       contrario, com o argumento invertido.

O QUE O APARELHO MOSTROU (2.2)

    Mantenedor: *"a primeira vez ele ate entra em pasta mas depois nao
    entra, e isso acontece com video tb e radio; os outros nao funciona."*

    Ou seja: dos seis, tres abrem uma vez e param, tres nunca abrem. Nao
    e "nao chega la" — e "chega errado".

A CAUSA

    A cauda que abre a pagina destino monta os argumentos assim:

        0x00101036   ldrh r2, [r4, #0x0c]     ctrl
        0x00101038   ldrh r1, [r4, #0x0a]     <-- daqui
        0x0010103A   ldrh r0, [r4, #0x08]     origem
        0x0010103C   b    0x001011F2          abre

    E as caudas que abrem SEM mensagem fixam o mesmo argumento:

        0x0010123A   movs r3, #0x28
        0x0010123C   movs r2, #7
        0x0010123E   movs r1, #2              <-- FIXO em 2
        0x00101240   b    0x001011F2

    Logo `r1` **tem de valer 2**. Na home `msg[0x0a]` ja vale 2, entao
    bate. No Extras vale 4 — e eu preservei o 4 DE PROPOSITO.

O MEU ERRO, POR ESCRITO

    No cabecalho do `patch_extras_fix.py` eu escrevi que trocar esse
    campo por 2 "seria um bug silencioso, porque a cauda le e repassa".

    A observacao estava certa e a conclusao invertida: ele e repassado
    **justamente porque precisa valer 2**.

    O que faz o "voltar" retornar ao Extras e o `msg[0x08]` (origem =
    0x53), lido separadamente em `0x0010103A`. Eu juntei os dois campos
    num raciocinio so e escolhi preservar o errado.

O QUE FAZ

    Acrescenta duas instrucoes a rotina em 0x001A5900:

        movs r1, #2
        strh r1, [r4, #0x0a]

    `msg[0x08]` (origem) continua intocado — o voltar segue apontando
    para o Extras.

USO
    python3 tools/patch_extras_fix2.py \\
        --in  firmware/WORKING/GN438_openpod_v073_carimbado.bin \\
        --out firmware/WORKING/GN438_openpod_v074.bin [--dry-run]

SEGURANCA
    - exige a rotina do `patch_extras_fix` byte a byte; se nao for
      exatamente ela, RECUSA;
    - confere a cauda 0x00101038 e a cauda fixa 0x0010123E, que sao a
      evidencia do diagnostico;
    - desmonta a rotina nova e confere COM OPERANDOS;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.
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
DESPACHO = 0x00D00FB2
CAUDA_MSG = 0x00101038      # ldrh r1,[r4,#0x0a]
CAUDA_FIXA = 0x0010123E     # movs r1,#2
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


def monta_antiga(base, glob):
    c = bytearray()

    def h(*hw):
        for x in hw:
            c.extend(struct.pack("<H", x))
    h(0x2A05)
    o = len(c)
    h(0x0000)
    p1 = len(c)
    h(0x0000)
    h(0x5C9B, 0x81A3)
    p2 = len(c)
    h(0x0000)
    c.extend(bw(base + len(c), DESPACHO))
    sai = len(c)
    h(0xE8BD, 0x81F0)
    struct.pack_into("<H", c, o, 0xD800 | (((sai - (o + 4)) >> 1) & 0xFF))
    while len(c) % 4:
        h(0xBF00)
    mapa = len(c)
    c.extend(bytes(MAPA) + b"\0\0")
    g = len(c)
    c.extend(struct.pack("<I", glob))
    struct.pack_into("<H", c, p1,
                     0xA300 | (((base + mapa) - ((base + p1 + 4) & ~3)) >> 2))
    struct.pack_into("<H", c, p2,
                     0x4E00 | (((base + g) - ((base + p2 + 4) & ~3)) >> 2))
    return bytes(c)


def monta(base, glob):
    c = bytearray()

    def h(*hw):
        for x in hw:
            c.extend(struct.pack("<H", x))
    h(0x2A05)                      # cmp  r2, #5
    o = len(c)
    h(0x0000)                      # bhi  sai
    p1 = len(c)
    h(0x0000)                      # adr  r3, MAPA
    h(0x5C9B)                      # ldrb r3, [r3, r2]
    h(0x81A3)                      # strh r3, [r4, #0x0c]   ctrl_id
    h(0x2102)                      # movs r1, #2
    h(0x8161)                      # strh r1, [r4, #0x0a]   <-- a correcao
    p2 = len(c)
    h(0x0000)                      # ldr  r6, =GLOBAL
    c.extend(bw(base + len(c), DESPACHO))
    sai = len(c)
    h(0xE8BD, 0x81F0)              # sai: pop.w {r4-r8, pc}
    struct.pack_into("<H", c, o, 0xD800 | (((sai - (o + 4)) >> 1) & 0xFF))
    while len(c) % 4:
        h(0xBF00)
    mapa = len(c)
    c.extend(bytes(MAPA) + b"\0\0")
    g = len(c)
    c.extend(struct.pack("<I", glob))
    struct.pack_into("<H", c, p1,
                     0xA300 | (((base + mapa) - ((base + p1 + 4) & ~3)) >> 2))
    struct.pack_into("<H", c, p2,
                     0x4E00 | (((base + g) - ((base + p2 + 4) & ~3)) >> 2))
    return bytes(c)


ESPERADO = ["cmp r2, #5", "bhi #0xda5914", "adr r3, #0x10",
            "ldrb r3, [r3, r2]", "strh r3, [r4, #0xc]", "movs r1, #2",
            "strh r1, [r4, #0xa]", "ldr r6, [pc, #0x10]", "b.w #0xd00fb2",
            "pop.w {r4, r5, r6, r7, r8, pc}"]


def main():
    ap = argparse.ArgumentParser(description="Extras: msg[0x0a] = 2")
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
    glob = struct.unpack_from("<I", data, 0x001A591C)[0]
    antiga = monta_antiga(BLOB + XIP, glob)
    atual = bytes(data[BLOB:BLOB + len(antiga)])
    if atual != antiga:
        erros.append("0x001A5900 nao contem a rotina do patch_extras_fix\n"
                     f"      esperado {antiga.hex()}\n"
                     f"      achei    {atual.hex()}")
    # evidencia do diagnostico
    if bytes(data[CAUDA_MSG:CAUDA_MSG + 2]) != bytes.fromhex("6189"):
        erros.append(f"0x{CAUDA_MSG:06X} nao e `ldrh r1,[r4,#0xa]`")
    if bytes(data[CAUDA_FIXA:CAUDA_FIXA + 2]) != bytes.fromhex("0221"):
        erros.append(f"0x{CAUDA_FIXA:06X} nao e `movs r1,#2` — "
                     "a evidencia do diagnostico nao confere")

    nova = monta(BLOB + XIP, glob)
    got = [f"{i.mnemonic} {i.op_str}".strip()
           for i in md.disasm(nova, BLOB + XIP)][:len(ESPERADO)]
    if got != ESPERADO:
        erros.append(f"rotina nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")
    if any(v != 0xFF for v in data[BLOB + len(nova):BLOB + 0x80]):
        erros.append("area apos a rotina nova nao esta livre")
    if erros:
        print("RECUSADO:")
        for e in erros:
            print("   -", e)
        return 1

    print()
    print("  EXTRAS — o campo 0x0A tem de valer 2")
    print()
    print("  evidencia conferida na imagem:")
    print(f"    0x{CAUDA_MSG:06X}  ldrh r1,[r4,#0x0a]   (cauda por mensagem)")
    print(f"    0x{CAUDA_FIXA:06X}  movs r1,#2           (cauda fixa)")
    print()
    print("  antes: msg[0x0a] preservado em 4  -> a cauda passa 4")
    print("  agora: msg[0x0a] = 2              -> igual a home")
    print("  msg[0x08] (origem = 0x53) INTOCADO — o voltar segue no Extras")
    print()
    for i, (c, n) in enumerate(zip(MAPA, NOMES)):
        print(f"    {i}  {n:14s} -> ctrl {c}")
    print()
    data[BLOB:BLOB + len(nova)] = nova
    print(f"  0x{BLOB:06X}  rotina reescrita: {len(antiga)} -> {len(nova)} B")

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
