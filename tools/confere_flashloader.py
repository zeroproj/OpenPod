#!/usr/bin/env python3
"""
confere_flashloader.py — confere uma gravacao feita pelo Flashloader
                         SL-DEV da Shenju (Windows).

PARA QUE
    O Flashloader grava a imagem inteira a partir de um `.up`. Esta
    ferramenta le o que saiu do aparelho ANTES e DEPOIS e responde:

      - o aparelho ficou exatamente igual ao `.up`?
      - quais setores mudaram, e sao os esperados?
      - a PSMP (configuracoes do usuario) foi preservada?
      - o bootloader continua o de fabrica?

USO
    python3 tools/confere_flashloader.py --depois depois.bin
    python3 tools/confere_flashloader.py --antes antes.bin --depois depois.bin

    --up     qual .up era esperado
             (padrao: release/OpenPod-Core-5.7-Public-Beta-1/OpenPod_Beta1.up)
    --antes  opcional; sem ele, nao da para listar o que mudou

EXEMPLO
    $ python3 tools/confere_flashloader.py --antes antes.bin --depois depois.bin
    payload do .up   0x1a7000 B   CRC 0xcedb CONFERE
    cobertura        IGUAL ao .up em todos os 0x1a7 setores
    PSMP 0x1FC000    PRESERVADA
    bootloader       identico ao de fabrica
    mudou            44 setores, de 0x48000 a 0x1a6000
    VEREDITO: GRAVACAO CORRETA

DEPENDENCIAS
    nenhuma (so a biblioteca padrao)

LIMITACOES
    Confere bytes, nao comportamento. Imagem certa e aparelho que nao
    liga sao coisas diferentes -- se acontecer, o problema nao esta na
    gravacao.
"""
import argparse
import hashlib
import struct
import sys

SETOR = 0x1000
PSMP = 0x1FC000
BOOT_FIM = 0xD000
TAM = 2 * 1024 * 1024
ORIG_SHA = "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f"


def crc16(b):
    c = 0xFFFF
    for x in b:
        c ^= x << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def le(p, esperado=None):
    d = open(p, "rb").read()
    if esperado and len(d) != esperado:
        sys.exit("ABORTADO: %s tem %d bytes, esperado %d" % (p, len(d), esperado))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--up", default="release/OpenPod-Core-5.7-Public-Beta-1/"
                                    "OpenPod_Beta1.up")
    ap.add_argument("--antes")
    ap.add_argument("--depois", required=True)
    ap.add_argument("--original", default="firmware/ORIGINAL/GN438_original.bin")
    a = ap.parse_args()

    up = le(a.up)
    if up[0:6] != b"CONFIG" or up[0x16:0x1C] != b"SL6801":
        sys.exit("ABORTADO: %s nao parece um .up da Shenju" % a.up)
    off = struct.unpack_from("<I", up, 6)[0]
    tam = struct.unpack_from("<I", up, 0x10)[0]
    crc = struct.unpack_from("<H", up, 0x14)[0]
    pay = up[off:off + tam]
    bate = crc16(pay) == crc
    print("payload do .up   0x%x B   CRC 0x%04x %s"
          % (tam, crc, "CONFERE" if bate else "NAO CONFERE"))
    if not bate:
        sys.exit("ABORTADO: o proprio .up esta corrompido. Nao conclua nada.")

    dep = le(a.depois, TAM)

    falhas = []

    # 1) o aparelho ficou igual ao .up, dentro da cobertura?
    ruins = [s for s in range(0, tam, SETOR)
             if dep[s:s + SETOR] != pay[s:s + SETOR]]
    if ruins:
        falhas.append("cobertura")
        print("cobertura        %d setor(es) DIFEREM do .up" % len(ruins))
        for s in ruins[:10]:
            print("                   0x%06X" % s)
        if len(ruins) > 10:
            print("                   ... e mais %d" % (len(ruins) - 10))
    else:
        print("cobertura        IGUAL ao .up em todos os 0x%x setores"
              % (tam // SETOR))

    # 2) a PSMP sobreviveu?
    if a.antes:
        ant = le(a.antes, TAM)
        if ant[PSMP:] == dep[PSMP:]:
            print("PSMP 0x%06X    PRESERVADA" % PSMP)
        else:
            falhas.append("PSMP")
            print("PSMP 0x%06X    MUDOU -- as configuracoes foram perdidas" % PSMP)
    else:
        print("PSMP 0x%06X    nao da para dizer (falta --antes)" % PSMP)

    # 3) bootloader
    try:
        orig = le(a.original, TAM)
        if hashlib.sha256(orig).hexdigest() != ORIG_SHA:
            sys.exit("PARE: o firmware ORIGINAL nao confere com o SHA-256 "
                     "conhecido. Nao siga.")
        if dep[:BOOT_FIM] == orig[:BOOT_FIM]:
            print("bootloader       identico ao de fabrica")
        else:
            falhas.append("bootloader")
            print("bootloader       DIFERE do de fabrica -- atencao")
    except FileNotFoundError:
        print("bootloader       nao conferido (%s nao encontrado)" % a.original)

    # 4) o que mudou
    if a.antes:
        dif = [s for s in range(0, TAM, SETOR)
               if ant[s:s + SETOR] != dep[s:s + SETOR]]
        if dif:
            print("mudou            %d setores, de 0x%X a 0x%X"
                  % (len(dif), dif[0], dif[-1]))
        else:
            print("mudou            nenhum setor -- o aparelho JA estava assim")

    print()
    if falhas:
        print("VEREDITO: ALGO NAO CONFERE (%s)" % ", ".join(falhas))
        print("NAO desligue o aparelho. Ver docs/MODO_DOWNLOAD.md.")
        return 1
    print("VEREDITO: GRAVACAO CORRETA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
