#!/usr/bin/env python3
"""
patch_tempo_restante.py — o segundo tempo passa a ser o RESTANTE.

O QUE MUDA
    04:02  ->  -3:55

    Hoje a Tocando Agora mostra decorrido e DURACAO TOTAL. O Projeto
    Marte mostra decorrido e RESTANTE, com sinal negativo -- e saber
    quanto falta e mais util que saber quanto dura.

COMO O FIRMWARE BUSCA OS DOIS NUMEROS

    0x00CFF15C   tempo decorrido
    0x00CFF184   duracao total

    Confirmado pelo calculo da barra de progresso, que faz
    decorrido * 100 / total usando exatamente essas duas.

    O sitio do segundo tempo (0x00D08748) chama a segunda.

O CONSERTO
    Uma rotina de 16 bytes na area livre:

        push {r4, lr}
        bl   0x00CFF184     ; total
        mov  r4, r0
        bl   0x00CFF15C     ; decorrido
        subs r0, r4, r0     ; restante
        pop  {r4, pc}

    E o `bl` do sitio e reapontado para ela. Mais o formato, que passa
    de "%02d:%02d" para "-%02d:%02d", string nova na area livre.

POR QUE ESSA ROTINA E SEGURA
    Ela e alcancada por `bl` e tem push/pop PROPRIOS -- ela e dona do
    seu quadro. As duas vezes que uma rotina em area livre travou o
    aparelho (Core 3.2 e Core 4.5) foi por quadro alheio: uma foi
    alcancada por `b.w` e saiu com `bx lr` sem desfazer o push do
    hospedeiro; a outra usou um quadro de 6 registradores onde o
    hospedeiro tinha 4.

    Aqui nao ha hospedeiro. Conferir com tools/check_pilha.py.

USO
    python3 tools/patch_tempo_restante.py --in <fw.bin> --out <novo.bin>

DEPENDENCIAS
    capstone

SEGURANCA
    - confere que o sitio chama 0x00CFF184 antes de reapontar;
    - desmonta a rotina inteira de volta e compara instrucao a
      instrucao com o esperado;
    - confere que o `bl` do sitio passou a apontar para a rotina;
    - so escreve em area 0xFF virgem.
"""
import argparse
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

XIP = 0x00C00000
TAM = 2 * 1024 * 1024
DECORRIDO = 0x00CFF15C
TOTAL = 0x00CFF184
SITIO = 0x00D08748        # o `bl` que busca o segundo tempo
POOL = 0x00D087D4         # o ponteiro do formato desse tempo
FMT_CURTO = 0x00C4CD5D    # "%02d:%02d"

ESPERADO = ["push {r4, lr}", "bl #0xcff184", "mov r4, r0",
            "bl #0xcff15c", "subs r0, r4, r0", "pop {r4, pc}"]


def bl(de, para):
    off = (para - (de + 4)) >> 1
    s = (off >> 23) & 1
    i1 = (off >> 22) & 1
    i2 = (off >> 21) & 1
    j1 = (~i1 & 1) ^ s
    j2 = (~i2 & 1) ^ s
    return struct.pack("<HH",
                       0xF000 | (s << 10) | ((off >> 11) & 0x7FF),
                       0xD000 | (j1 << 13) | (j2 << 11) | (off & 0x7FF))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAM:
        sys.exit("ABORTADO: %s tem %d bytes, esperado %d" % (a.src, len(d), TAM))
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

    print("=" * 68)
    print("OpenPod — o segundo tempo vira o RESTANTE")
    print("=" * 68)

    # o sitio chama mesmo a duracao total?
    i = list(md.disasm(bytes(d[SITIO - XIP:SITIO - XIP + 4]), SITIO))[0]
    if i.mnemonic != "bl" or int(i.op_str.replace("#", ""), 16) != TOTAL:
        sys.exit("ABORTADO: 0x%08X nao chama 0x%08X (achei %s %s)."
                 % (SITIO, TOTAL, i.mnemonic, i.op_str))
    print("  sitio 0x%08X  bl 0x%08X  (duracao total)" % (SITIO, TOTAL))

    # area livre
    livre = None
    for o in range(0x1A6000, 0x1A7000):
        if d[o:o + 80] == b"\xff" * 80:
            livre = o
            break
    if livre is None:
        sys.exit("ABORTADO: nao achei 80 bytes virgens na area livre.")
    base = livre + XIP

    rot = bytearray()
    rot += bytes.fromhex("10b5")
    rot += bl(base + len(rot), TOTAL)
    rot += bytes.fromhex("0446")
    rot += bl(base + len(rot), DECORRIDO)
    rot += bytes.fromhex("201a")
    rot += bytes.fromhex("10bd")
    d[livre:livre + len(rot)] = rot

    fmt = b"-%02d:%02d\x00"
    pos_fmt = livre + len(rot)
    d[pos_fmt:pos_fmt + len(fmt)] = fmt

    d[SITIO - XIP:SITIO - XIP + 4] = bl(SITIO, base)
    struct.pack_into("<I", d, POOL - XIP, pos_fmt + XIP)

    # --- conferencia ---------------------------------------------------
    print("\n  rotina em 0x%08X:" % base)
    got = []
    for x in md.disasm(bytes(d[livre:livre + len(rot)]), base):
        got.append("%s %s" % (x.mnemonic, x.op_str))
        print("     0x%08X  %-8s %s" % (x.address, x.mnemonic, x.op_str))
    if got != ESPERADO:
        sys.exit("ABORTADO: a rotina nao desmontou como esperado.\n  %s" % got)

    i = list(md.disasm(bytes(d[SITIO - XIP:SITIO - XIP + 4]), SITIO))[0]
    if int(i.op_str.replace("#", ""), 16) != base:
        sys.exit("ABORTADO: o `bl` do sitio nao aponta para a rotina.")
    print("\n  sitio reapontado -> %s %s" % (i.mnemonic, i.op_str))

    p = struct.unpack_from("<I", d, POOL - XIP)[0]
    lido = bytes(d[p - XIP:d.index(b"\x00", p - XIP)]).decode()
    print("  formato em 0x%08X -> %r  %s"
          % (p, lido, "OK" if lido == "-%02d:%02d" else "NAO CONFERE"))
    if lido != "-%02d:%02d":
        sys.exit("ABORTADO: o formato nao confere.")

    orig = open(a.src, "rb").read()
    mudou = sum(1 for k in range(TAM) if d[k] != orig[k])
    print("\n  bytes alterados: %d   setores: 0x108000, 0x1A6000" % mudou)
    open(a.dst, "wb").write(bytes(d))
    print("  gravado: %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
