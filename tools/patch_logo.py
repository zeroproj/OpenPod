#!/usr/bin/env python3
"""
patch_logo.py — poe a logo do OpenPod na tela de abertura.

O SLOT

    A tela de abertura desenha uma `lv_img_dsc` INDEXED_8 de 128x35 que,
    de fabrica, e o logotipo **GENAI**. Cabecalho em 0x000CC7C4:

        0x0462000A   cf=10 (INDEXED_8BIT), w=128, h=35
        0x00001580   data_size = 5504 = 1024 (paleta) + 4480 (pixels)
        0x00CCC7D0   ponteiro XIP -> flash 0x000CC7D0

    Confere com o mapa: base XIP 0x00C00000 + 0x0CC7D0.

        0x000CC7D0  1024 B  paleta, 256 entradas BGRA
        0x000CCBD0  4480 B  pixels, 128*35, um byte de indice por pixel
        0x000CDD50          fim

    **O cabecalho nao e tocado** — a logo nova tem exatamente 128x35, o
    tamanho do slot. Nada de redimensionar, nada de mexer em ponteiro.

POR QUE ESTA FERRAMENTA EXISTE

    A logo ja esteve no aparelho: foi a V007, em 12/09. Mas a ferramenta
    que fez aquilo **nao ficou no repositorio** — so a imagem resultante.
    Quando a construcao passou a sair de uma receita declarada
    (`tools/build.py`), a logo ficou de fora sem ninguem perceber: a 3.0
    e a 3.1 bootam com o logotipo GENAI de fabrica.

    Medido, nao suposto: entre o ORIGINAL e a imagem construida ha
    **0 bytes de diferenca** em 0x0CC7C4..0x0CDD50.

A PALETA E BGRA, E NAO LEVA PRE-INVERSAO

    Constante de cor crua precisa ser pre-invertida (o display e RGB565
    com os bytes trocados, `docs/COLOR_SOURCE.md` §9). **Paleta de
    imagem nao**: o formato e BGRA proprio, validado no V002/V003. Cada
    entrada e B, G, R, A — e A e sempre 255 aqui.

CRITERIO DE ACEITE

    Aplicada sobre o ORIGINAL com `assets/OpenLogo.png`, esta ferramenta
    produz em 0x0CC7C4..0x0CDD50 **exatamente os mesmos bytes** da
    imagem V007, que rodou no aparelho. Verificavel:

        python3 tools/patch_logo.py --autoteste

    Isso nao e coincidencia: a conversao da V007 era mediana-corte do
    Pillow, e e a mesma daqui. 247 cores, erro medio 0,07 por canal
    contra o PNG de origem, maximo 6.

USO
    python3 tools/patch_logo.py --in <entrada.bin> --out <saida.bin>
                                [--png assets/OpenLogo.png] [--dry-run]
    python3 tools/patch_logo.py --autoteste

DEPENDENCIAS
    Python 3 + Pillow

LIMITACOES
    - o PNG tem de ser exatamente 128x35; a ferramenta **recusa** outro
      tamanho em vez de redimensionar (redimensionar e decisao de design,
      nao de ferramenta);
    - no maximo 256 cores depois da quantizacao, que e o limite do slot;
    - so troca paleta e pixels. Se um dia a logo precisar de outro
      tamanho, e outro trabalho: mexe no cabecalho e na tela.
"""

import argparse
import hashlib
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CAB      = 0x000CC7C4          # lv_img_dsc
PALETA   = 0x000CC7D0          # 256 * BGRA
PIXELS   = 0x000CCBD0          # 128 * 35
FIM      = 0x000CDD50
LARG, ALT = 128, 35
CF_INDEXED_8 = 10
XIP = 0x00C00000

PROIBIDO = 0x0000D000          # regra R1: nada abaixo/dentro deste setor

PNG_PADRAO = "assets/OpenLogo.png"
ORIGINAL   = "firmware/ORIGINAL/GN438_original.bin"
REFERENCIA = "firmware/WORKING/GN438_openpod_v007.bin"   # a que rodou


def converte(caminho_png):
    """PNG 128x35 -> (1024 B de paleta BGRA, 4480 B de indices)."""
    try:
        from PIL import Image
    except ImportError:
        sys.exit("ERRO: Pillow nao esta instalado (pip3 install Pillow)")

    img = Image.open(caminho_png)
    if img.size != (LARG, ALT):
        sys.exit(f"ERRO: {caminho_png} tem {img.size[0]}x{img.size[1]}, "
                 f"e o slot e {LARG}x{ALT}. A ferramenta nao redimensiona.")
    img = img.convert("RGB")
    q = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)

    pal = q.getpalette()[:768]
    blob = bytearray()
    for i in range(256):
        r, g, b = (pal[i * 3:i * 3 + 3] + [0, 0, 0])[:3]
        blob += bytes((b, g, r, 255))          # BGRA, sem pre-inversao
    px = q.tobytes()
    assert len(blob) == 1024 and len(px) == LARG * ALT
    return bytes(blob), px, len(set(px)), img, q


def erro_por_canal(src, q):
    """diferenca absoluta, canal a canal, entre o PNG e a quantizacao."""
    a = src.convert("RGB").tobytes()
    b = q.convert("RGB").tobytes()
    return [abs(x - y) for x, y in zip(a, b)]


def confere_slot(d):
    """O slot e mesmo o que esperamos? Se nao for, para."""
    cab, tam, ptr = struct.unpack_from("<3I", d, CAB)
    cf = cab & 0x1F
    w = (cab >> 10) & 0x7FF
    h = (cab >> 21) & 0x7FF
    erros = []
    if cf != CF_INDEXED_8: erros.append(f"cf={cf}, esperado {CF_INDEXED_8}")
    if (w, h) != (LARG, ALT): erros.append(f"{w}x{h}, esperado {LARG}x{ALT}")
    if tam != 1024 + LARG * ALT: erros.append(f"data_size=0x{tam:X}")
    if ptr != PALETA + XIP: erros.append(f"ponteiro=0x{ptr:08X}")
    return (w, h, cf, tam, ptr), erros


def aplica(d, pal, px):
    d[PALETA:PALETA + 1024] = pal
    d[PIXELS:PIXELS + LARG * ALT] = px
    return d


def autoteste():
    print()
    print("  AUTOTESTE — reproduzir o slot da V007, que rodou no aparelho")
    print()
    o = os.path.join(RAIZ, ORIGINAL)
    r = os.path.join(RAIZ, REFERENCIA)
    for p in (o, r, os.path.join(RAIZ, PNG_PADRAO)):
        if not os.path.exists(p):
            print(f"  FALTA: {p}")
            return 1
    d = bytearray(open(o, "rb").read())
    ref = open(r, "rb").read()
    pal, px, n, src, q = converte(os.path.join(RAIZ, PNG_PADRAO))
    aplica(d, pal, px)

    igual = bytes(d[CAB:FIM]) == ref[CAB:FIM]
    print(f"    cores usadas        : {n}")
    print(f"    slot 0x{CAB:06X}..0x{FIM:06X} identico a V007: "
          f"{'SIM' if igual else 'NAO'}")

    # erro da quantizacao contra o PNG de origem
    difs = erro_por_canal(src, q)
    print(f"    erro por canal      : medio {sum(difs)/len(difs):.3f}  "
          f"maximo {max(difs)}")
    print()
    if not igual:
        print("  AUTOTESTE FALHOU")
        return 1
    print("  AUTOTESTE OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description="logo do OpenPod na abertura")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--png", default=PNG_PADRAO)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    a = ap.parse_args()

    if a.autoteste:
        return autoteste()
    if not a.src or not a.dst:
        ap.error("--in e --out sao obrigatorios (ou use --autoteste)")

    d = bytearray(open(a.src, "rb").read())
    if len(d) != 0x200000:
        print(f"ERRO: {a.src} tem {len(d)} B, esperado 2097152",
              file=sys.stderr)
        return 1
    orig = bytes(d)

    print()
    print("  LOGO DO OPENPOD NA ABERTURA")
    print()
    (w, h, cf, tam, ptr), erros = confere_slot(d)
    print(f"    slot 0x{CAB:06X}  {w}x{h}  cf={cf}  data_size=0x{tam:X}  "
          f"ptr=0x{ptr:08X}")
    if erros:
        print("    ABORTADO: o slot nao e o esperado -> " + "; ".join(erros),
              file=sys.stderr)
        return 1

    png = a.png if os.path.isabs(a.png) else os.path.join(RAIZ, a.png)
    pal, px, n, src, q = converte(png)
    print(f"    {os.path.relpath(png, RAIZ)}  {LARG}x{ALT}  "
          f"-> INDEXED_8, {n} cores")

    difs = erro_por_canal(src, q)
    print(f"    erro da quantizacao: medio {sum(difs)/len(difs):.3f} "
          f"por canal, maximo {max(difs)}")
    print()

    aplica(d, pal, px)

    print("  ALTERACOES")
    print(f"    0x{PALETA:06X}  1024 B  paleta BGRA, 256 entradas")
    print(f"    0x{PIXELS:06X}  {LARG*ALT} B  pixels, 1 indice por pixel")
    print(f"    cabecalho em 0x{CAB:06X}: INTOCADO")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    if not dif:
        print("  a logo ja esta aplicada — nada a fazer")
    fora = [i for i in dif if not (PALETA <= i < FIM)]
    if fora:
        print(f"  ABORTADO: escreveu fora do slot, em 0x{min(fora):06X}",
              file=sys.stderr)
        return 1
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido (R1).", file=sys.stderr)
        return 1
    print("  tabela de particoes NAO tocada   OK")
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}")
    print()

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
