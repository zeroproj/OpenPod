#!/usr/bin/env python3
"""
patch_icones_home.py — troca os 9 icones da tela principal.

O SLOT (docs/IMAGENS.md §3)

    A home desenha uma `lv_img_dsc` INDEXED_8 de 128x160: a folha com os
    nove icones de fabrica, grade 3x3, circulos de 30 px. Cabecalho em
    0x000CDD50:

        0x1402000A   cf=10 (INDEXED_8BIT), w=128, h=160
        0x00005400   data_size = 21504 = 1024 (paleta) + 20480 (pixels)
        0x00CCDD5C   ponteiro XIP -> flash 0x000CDD5C

    **O cabecalho nao e tocado.** A folha nova tem 128x160, os icones nas
    MESMAS posicoes (centros medidos na de fabrica). So paleta e pixels.
    Paleta BGRA sem pre-inversao, como na logo (patch_logo.py).

    A navegacao da home e por indice, nunca pelo desenho
    (docs/PLANO_HOME.md §1.2): trocar a folha nao toca na navegacao.

USO
    python3 tools/patch_icones_home.py --in <entrada.bin> --out <saida.bin>
                                       [--png assets/IconesHome.png] [--dry-run]
    python3 tools/patch_icones_home.py --autoteste

    O PNG sai de tools/desenha_icones_home.py.

DEPENDENCIAS
    Python 3 + Pillow
"""

import argparse
import hashlib
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CAB      = 0x000CDD50          # lv_img_dsc
PALETA   = 0x000CDD5C          # 256 * BGRA
PIXELS   = 0x000CE15C          # 128 * 160
FIM      = 0x000D315C
LARG, ALT = 128, 160
CF_INDEXED_8 = 10
XIP = 0x00C00000

PROIBIDO = 0x0000D000          # regra R1: nada abaixo/dentro deste setor

PNG_PADRAO = "assets/IconesHome.png"
ORIGINAL   = "firmware/ORIGINAL/GN438_original.bin"


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
    """Aplica sobre o ORIGINAL e le de volta pelo cabecalho: a imagem
    decodificada tem de bater com a quantizacao, e nada fora do slot muda."""
    print()
    print("  AUTOTESTE — aplicar no ORIGINAL e decodificar de volta")
    print()
    o = os.path.join(RAIZ, ORIGINAL)
    d = bytearray(open(o, "rb").read())
    orig = bytes(d)
    (_, _, _, _, _), erros = confere_slot(d)
    if erros:
        print("  slot inesperado: " + "; ".join(erros))
        return 1
    pal, px, n, src, q = converte(os.path.join(RAIZ, PNG_PADRAO))
    aplica(d, pal, px)
    cab, tam, ptr = struct.unpack_from("<3I", d, CAB)
    base = ptr - XIP
    p2, x2 = d[base:base + 1024], d[base + 1024:base + tam]
    lido = bytes(c for i in x2 for c in (p2[i*4+2], p2[i*4+1], p2[i*4]))
    ok_img = lido == q.convert("RGB").tobytes()
    fora = [i for i in range(len(orig)) if orig[i] != d[i]
            and not (PALETA <= i < FIM)]
    difs = erro_por_canal(src, q)
    print(f"    cores usadas        : {n}")
    print(f"    relido pelo cabecalho == quantizada: {'SIM' if ok_img else 'NAO'}")
    print(f"    bytes fora do slot  : {len(fora)}")
    print(f"    erro por canal      : medio {sum(difs)/len(difs):.3f}  "
          f"maximo {max(difs)}")
    print()
    if not ok_img or fora:
        print("  AUTOTESTE FALHOU")
        return 1
    print("  AUTOTESTE OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description="icones da tela principal")
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
    print("  ICONES DA TELA PRINCIPAL")
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
        print("  os icones ja estao aplicados — nada a fazer")
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
