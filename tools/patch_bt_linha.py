#!/usr/bin/env python3
"""
patch_bt_linha.py — a lista do Bluetooth adota a altura de linha padrao.

O DEFEITO
    Reportado pelo mantenedor ao testar a Beta 4: "Bluetooth nao segue o
    padrao, ta tudo grande."

    Medido:
        faixa            tela_alt/10 = 16    ja certo
        altura da lista  tela_alt - /10 = 144 ja certo
        ALTURA DA LINHA  tela_alt/7  = 22    fora do padrao

        0x00D28804   movs r2, #7
                     sdiv r2, r0, r2
                     bl   set_size

POR QUE ESCAPOU
    O patch_faixa_16px.py procurou altura em VALORES FIXOS. O Bluetooth
    calcula por divisao. A varredura passou por cima -- 24 sitios, achou
    23.

    Mesma licao da bateria verde: varredura por assinatura sempre perde
    alguem e nao avisa.

O CONSERTO
    Um byte: 07 -> 0A, dando tela_alt/10 = 16.

USO
    python3 tools/patch_bt_linha.py --in <fw.bin> --out <novo.bin>

DEPENDENCIAS
    capstone (para conferir antes e depois)

SEGURANCA
    - so aceita se a sequencia aparecer EXATAMENTE uma vez;
    - desmonta de volta e confere que virou movs r2, #0xa.
"""
import argparse
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

XIP = 0x00C00000
TAM = 2 * 1024 * 1024
ANTES = bytes.fromhex("072290fbf2f24846")   # movs r2,#7 ; sdiv r2,r0,r2 ; mov r0,sb
DEPOIS = bytes.fromhex("0a2290fbf2f24846")  # movs r2,#0xa ; ...


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAM:
        sys.exit("ABORTADO: %s tem %d bytes, esperado %d" % (a.src, len(d), TAM))

    n = d.count(ANTES)
    print("=" * 66)
    print("OpenPod — altura de linha do Bluetooth: 22 px -> 16 px")
    print("=" * 66)
    print("  sequencia de fabrica encontrada: %d vez(es)" % n)
    if n != 1:
        sys.exit("ABORTADO: esperava exatamente 1. Nao escrevi nada.")

    o = d.find(ANTES)
    d[o:o + len(DEPOIS)] = DEPOIS

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    ins = list(md.disasm(bytes(d[o:o + 8]), o + XIP))
    txt = "%s %s" % (ins[0].mnemonic, ins[0].op_str)
    print("  0x%08X  %-20s %s" % (o + XIP, txt, "OK" if "#0xa" in txt else "NAO CONFERE"))
    if "#0xa" not in txt:
        sys.exit("ABORTADO: nao desmontou como esperado. Nao gravei.")

    orig = open(a.src, "rb").read()
    mudou = sum(1 for k in range(TAM) if d[k] != orig[k])
    print("  bytes alterados: %d   setor: 0x%06X" % (mudou, (o // 0x1000) * 0x1000))
    open(a.dst, "wb").write(bytes(d))
    print("  gravado: %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
