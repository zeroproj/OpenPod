#!/usr/bin/env python3
"""
patch_fundo_preto.py — o papel de parede da tela Tocando Agora vira preto.

POR QUE
    A tela Tocando Agora desenha um papel de parede: um swoosh azul em
    128x160, lv_img_dsc_t em 0x000C73B8 (ver docs/IMAGENS.md).

    Ele e o oposto do alvo. O iPod nano nao tem papel de parede atras do
    texto -- e no GN-438 ha um motivo a mais: o painel mostra faixas
    horizontais sobre fundo claro, e esse swoosh e claro em boa parte da
    tela.

COMO, E POR QUE ASSIM
    A imagem e INDEXED_8: paleta BGRA de 256 entradas (1024 B) seguida
    de 1 byte de indice por pixel (20.480 B).

    Para deixa-la preta basta zerar a PALETA. Os 20.480 bytes de indice
    ficam intactos, e a imagem inteira passa a apontar para preto.

        1.024 bytes mudam   em vez de   21.504
        1 setor tocado      em vez de   6

    E e reversivel byte a byte: a paleta original fica registrada no
    relatorio e em docs/IMAGENS.md.

    Nao mexemos no descritor. Largura, altura, formato e data_size
    continuam os mesmos -- entao nada que leia essa imagem precisa
    saber que algo mudou.

USO
    python3 tools/patch_fundo_preto.py \\
        --in  firmware/WORKING/GN438_beta2_carimbado.bin \\
        --out firmware/WORKING/GN438_beta3_carimbado.bin

DEPENDENCIAS
    nenhuma (so a biblioteca padrao)

SEGURANCA
    - confere o descritor antes de escrever: formato, largura, altura e
      data_size tem que bater com o esperado;
    - recusa se a imagem nao tiver 2 MiB;
    - confere depois que a paleta ficou toda preta e que os indices nao
      foram tocados.

LIMITACOES
    Deixa a imagem preta, nao a remove. O objeto continua sendo
    desenhado -- so nao aparece. Remover a chamada seria mais barato em
    CPU, mas exige mexer em codigo; isto aqui mexe so em dados.
"""
import argparse
import struct
import sys

XIP = 0x00C00000
DESC = 0x000C73B8          # lv_img_dsc_t do papel de parede
ESPERADO = dict(cf=10, w=128, h=160, size=1024 + 128 * 160)
TAM = 2 * 1024 * 1024


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAM:
        sys.exit("ABORTADO: %s tem %d bytes, esperado %d" % (a.src, len(d), TAM))

    h, size, ptr = struct.unpack_from("<III", d, DESC)
    cf = h & 0x1F
    az = (h >> 5) & 7
    w = (h >> 10) & 0x7FF
    hh = (h >> 21) & 0x7FF
    print("=" * 70)
    print("OpenPod — papel de parede da tela Tocando Agora")
    print("=" * 70)
    print("  descritor 0x%06X   cf=%d w=%d h=%d data_size=%d" % (DESC, cf, w, hh, size))

    if az != 0 or cf != ESPERADO["cf"] or w != ESPERADO["w"] \
            or hh != ESPERADO["h"] or size != ESPERADO["size"]:
        sys.exit("ABORTADO: o descritor nao e o esperado. Nao escrevi nada.")

    base = ptr - XIP
    if not (0 <= base < TAM):
        sys.exit("ABORTADO: ponteiro de dados fora do arquivo")
    print("  dados     0x%06X   paleta 1024 B + %d B de indices" % (base, w * hh))

    pal = bytes(d[base:base + 1024])
    cores = len({pal[i:i + 4] for i in range(0, 1024, 4)})
    print("  paleta atual: %d cores distintas" % cores)
    if pal == bytes(1024):
        sys.exit("ABORTADO: a paleta ja esta zerada. Nada a fazer.")

    indices_antes = bytes(d[base + 1024:base + 1024 + w * hh])

    # BGRA, opaco: B=0 G=0 R=0 A=0xFF
    nova = bytes([0x00, 0x00, 0x00, 0xFF]) * 256
    d[base:base + 1024] = nova

    # conferencia
    if bytes(d[base:base + 1024]) != nova:
        sys.exit("ABORTADO: a paleta nao ficou como pedido")
    if bytes(d[base + 1024:base + 1024 + w * hh]) != indices_antes:
        sys.exit("ABORTADO: os indices foram tocados. Nao gravei.")
    if struct.unpack_from("<III", d, DESC) != (h, size, ptr):
        sys.exit("ABORTADO: o descritor mudou. Nao gravei.")

    setores = sorted({(base + i) // 0x1000 for i in range(1024)})

    open(a.dst, "wb").write(bytes(d))
    print()
    print("  ALTERACOES")
    print("    0x%06X  1024 B  paleta -> preto opaco (00 00 00 FF)" % base)
    print("    indices: intactos (%d B)" % (w * hh))
    print("    descritor: intacto")
    print("    setores tocados: %s" % ", ".join("0x%06X" % (s * 0x1000) for s in setores))
    print()
    print("  gravado: %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
