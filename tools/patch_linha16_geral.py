#!/usr/bin/env python3
"""
patch_linha16_geral.py — toda linha de lista passa a ter 16 px.

O QUE CONSERTA
    Telas que calculam a altura da linha como tela_altura/7 = 22 px, o
    valor de fabrica, em vez de /10 = 16, o padrao OpenPod.

POR QUE ESTA FERRAMENTA EXISTE, E NAO OUTRA
    Ja tentei duas vezes:

        patch_faixa_16px.py   varreu por VALOR FIXO      achou 23, faltou 1
        patch_bt_linha.py     varreu por ASSINATURA de   achou 1, faltou 5
                              bytes, com o registrador
                              e a instrucao seguinte

    As duas falharam pelo mesmo motivo: casaram FORMA, nao SIGNIFICADO.
    O mantenedor gravou, olhou a tela e o Bluetooth continuava grande.

    Aqui a varredura e semantica. Desmonta o firmware e procura o
    PADRAO:

        movs rX, #7        um divisor 7 qualquer, em qualquer registrador
        ...
        sdiv rY, rZ, rX    a divisao
        ...
        bl  set_size | set_height

    Sem depender de quais registradores, nem do que vem antes ou depois.
    E por isso acha os seis, e nao um.

USO
    python3 tools/patch_linha16_geral.py --in <fw.bin> --out <novo.bin>
    python3 tools/patch_linha16_geral.py --in <fw.bin> --listar

DEPENDENCIAS
    capstone

SEGURANCA
    - so aceita `movs rX, #7` no endereco achado;
    - desmonta cada um de volta e confere que virou `movs rX, #0xa`;
    - um byte por sitio, nada mais.
"""
import argparse
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

XIP = 0x00C00000
TAM = 2 * 1024 * 1024
GEOM = (0xd4a1ea, 0xd4a21a)          # set_height, set_size


def acha(d):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    fora = []
    for base in range(0x100000, 0x1B0000, 0x8000):
        ins = list(md.disasm(d[base:base + 0x8200], base + XIP))
        for k, x in enumerate(ins):
            if x.mnemonic != "sdiv":
                continue
            reg = x.op_str.split(", ")[-1]
            pos = None
            for j in range(k - 1, max(0, k - 6), -1):
                y = ins[j]
                if y.mnemonic == "movs" and y.op_str.startswith(reg + ","):
                    try:
                        if int(y.op_str.split("#")[1], 0) == 7:
                            pos = y.address
                    except ValueError:
                        pass
                    break
            if pos is None:
                continue
            for j in range(k + 1, min(k + 8, len(ins))):
                if ins[j].mnemonic == "bl":
                    try:
                        if int(ins[j].op_str.replace("#", ""), 16) in GEOM:
                            fora.append(pos)
                    except ValueError:
                        pass
                    break
    return sorted(set(fora))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--listar", action="store_true")
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAM:
        sys.exit("ABORTADO: %s tem %d bytes, esperado %d" % (a.src, len(d), TAM))

    sitios = acha(d)
    print("=" * 66)
    print("OpenPod — altura de linha: tela/7 (22 px) -> tela/10 (16 px)")
    print("=" * 66)
    print("  sitios fora do padrao: %d" % len(sitios))
    for s in sitios:
        print("    0x%08X" % s)
    if a.listar or not sitios:
        return 0
    if not a.dst:
        sys.exit("\nuse --out para gravar, ou --listar so para ver")

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print()
    for s in sitios:
        o = s - XIP
        if d[o] != 7:
            sys.exit("ABORTADO: 0x%08X nao tem imediato 7. Nao gravei." % s)
        d[o] = 0x0A
        i = list(md.disasm(bytes(d[o:o + 2]), s))[0]
        ok = i.mnemonic == "movs" and i.op_str.endswith("#0xa")
        print("  0x%08X  %s %-12s %s" % (s, i.mnemonic, i.op_str,
                                         "OK" if ok else "NAO CONFERE"))
        if not ok:
            sys.exit("ABORTADO: nao desmontou como esperado.")

    restantes = acha(d)
    print()
    print("  varredura de novo apos gravar: %d sitio(s) fora do padrao"
          % len(restantes))
    if restantes:
        sys.exit("ABORTADO: sobrou sitio. Nao gravei.")

    orig = open(a.src, "rb").read()
    mudou = sum(1 for k in range(TAM) if d[k] != orig[k])
    setores = sorted({((s - XIP) // 0x1000) * 0x1000 for s in sitios})
    print("  bytes alterados: %d   setores: %s"
          % (mudou, ", ".join("0x%06X" % x for x in setores)))
    open(a.dst, "wb").write(bytes(d))
    print("  gravado: %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
