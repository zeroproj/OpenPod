#!/usr/bin/env python3
"""
patch_fila_de.py — o contador da fila vira "7 de 152".

O QUE MUDA
    7/152  ->  7 de 152

    E o que o Projeto Marte pede: "3 de 52" em vez de barra. Le melhor,
    e a barra confunde com fracao.

COMO
    O contador e um sprintf com "%d/%d", literal em 0x00C4CE1F. Esse
    literal e compartilhado por NOVE ponteiros -- varias telas usam o
    mesmo formato. Trocar a string no lugar mudaria todas.

    Por isso: escrevemos "%d de %d" na AREA LIVRE e repontamos apenas
    o ponteiro de 0x00D08444, que e o da Tocando Agora. Os outros oito
    continuam com a barra.

    Mesma tecnica do patch_versao.py: nunca editar string no lugar.

USO
    python3 tools/patch_fila_de.py --in <fw.bin> --out <novo.bin>
    --texto "%d de %d"     para experimentar outro formato

DEPENDENCIAS
    nenhuma (so a biblioteca padrao)

SEGURANCA
    - confere que o ponteiro aponta para o formato de fabrica;
    - confere que o texto novo tem exatamente dois %d;
    - escreve so em area 0xFF virgem, e rele pelo ponteiro depois.

LIMITACAO, E ELA IMPORTA
    "de" e portugues. O firmware tem oito idiomas, e esta tela passa a
    mostrar "7 de 152" em todos eles. O OpenPod ja assume portugues em
    outros pontos (a string de versao, os textos revisados), mas isso
    aqui e uma regressao para quem usa o aparelho em ingles.

    A alternativa seria puxar a palavra da tabela de idiomas -- mais
    caro, e nao ha id existente para "de"/"of".
"""
import argparse
import struct
import sys

XIP = 0x00C00000
TAM = 2 * 1024 * 1024
POOL = 0x00D08444         # o ponteiro da fila na Tocando Agora
FABRICA = 0x00C4CE1F      # "%d/%d"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--texto", default="%d de %d")
    a = ap.parse_args()

    if a.texto.count("%d") != 2:
        sys.exit("ABORTADO: o formato precisa de exatamente dois %d")

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAM:
        sys.exit("ABORTADO: %s tem %d bytes, esperado %d" % (a.src, len(d), TAM))

    print("=" * 66)
    print("OpenPod — contador da fila: 7/152 -> %s" % (a.texto % (7, 152)))
    print("=" * 66)

    atual = struct.unpack_from("<I", d, POOL - XIP)[0]
    if atual != FABRICA:
        sys.exit("ABORTADO: o ponteiro em 0x%08X aponta para 0x%08X, "
                 "esperado 0x%08X." % (POOL, atual, FABRICA))
    print("  ponteiro 0x%08X -> 0x%08X  \"%s\""
          % (POOL, atual, d[atual - XIP:atual - XIP + 5].decode()))

    # area livre: primeiro bloco de 0xFF grande o bastante
    novo = a.texto.encode() + b"\x00"
    livre = None
    for o in range(0x1A6000, 0x1A7000):
        if d[o:o + len(novo) + 16] == b"\xff" * (len(novo) + 16):
            livre = o
            break
    if livre is None:
        sys.exit("ABORTADO: nao achei area livre virgem para o texto.")

    d[livre:livre + len(novo)] = novo
    struct.pack_into("<I", d, POOL - XIP, livre + XIP)

    # conferencia: rele pelo ponteiro
    p = struct.unpack_from("<I", d, POOL - XIP)[0]
    lido = bytes(d[p - XIP:d.index(b"\x00", p - XIP)]).decode()
    print("  texto novo em 0x%06X (XIP 0x%08X)" % (livre, livre + XIP))
    print("  relido pelo ponteiro -> %r  %s"
          % (lido, "OK" if lido == a.texto else "NAO CONFERE"))
    if lido != a.texto:
        sys.exit("ABORTADO: nao gravei.")

    orig = open(a.src, "rb").read()
    mudou = sum(1 for k in range(TAM) if d[k] != orig[k])
    print("  os outros 8 ponteiros de \"%%d/%%d\" nao foram tocados")
    print("  bytes alterados: %d   setores: 0x%06X, 0x%06X"
          % (mudou, ((POOL - XIP) // 0x1000) * 0x1000, (livre // 0x1000) * 0x1000))
    open(a.dst, "wb").write(bytes(d))
    print("  gravado: %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
