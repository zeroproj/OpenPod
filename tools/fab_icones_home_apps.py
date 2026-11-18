#!/usr/bin/env python3
"""
fab_icones_home_apps.py — ficha 021 (Reload 3.0): o glifo do indice 5
(Imagem) vira Apps na folha `escuro_colorido`.

A FOLHA

    A folha da home e INDEXED_8, 128x160, paleta em 0x0CDD5C e pixels em
    0x0CE15C (128*160 indices). A 2.2 ja gravou a folha escura colorida e o
    `fab_home_moldura.py` ja moveu a grade. Esta ferramenta NAO refaz a
    paleta: ela mantem os 1024 bytes da 2.2 e troca apenas os indices dos
    pixels do icone 5. Assim o resto da tela fica byte a byte igual, e a
    diferenca contra a 2.2.1 e so o icone 5.

    O PNG novo e o antigo estao na grade ANTES da moldura. Como a moldura
    move a faixa do meio de y 62..97 para 70..105, o glifo do PNG cai 8
    linhas abaixo no binario final (`DESLOC_Y`). Escrever so a diferenca
    dos PNGs, ja deslocada, apaga o icone antigo e nao deixa resto.

    O PNG novo (`assets/IconesHome_escuro_colorido_apps.png`) e gerado por
    `desenha_icones_home.py` com `ESTILO=escuro_colorido GLIFO5=apps`. A
    ferramenta confere o sha256 dos dois PNGs e que eles so diferem dentro
    da caixa do icone 5 (x 93..115, y 68..90 na folha). O PNG antigo e o
    da 2.2 (`assets/IconesHome_escuro_colorido.png`), sha fixado.

    Os pixels do icone 5 sao remapeados para a PALETA EXISTENTE da 2.2
    (a mesma funcao de distancia de Chebyshev do `fab_icones_home.py`).
    Nenhuma entrada de paleta e criada ou trocada; o verde do glifo cai na
    entrada mais proxima (119,219,119) da paleta, com erro medio 1,54 e
    maximo 13.

PREMISSAS, conferidas ANTES de escrever

    - a imagem tem 2 MiB;
    - o cabecalho da folha (0x0CDD50) e o de fabrica, palavra por palavra;
    - a regiao paleta+pixels (0x0CDD5C..0x0D315C) tem o sha256 da folha
      2.2 (`escuro_colorido`), e nao outra;
    - o PNG antigo e o novo tem os shas fixados e 128x160;
    - a diferenca entre os PNGs esta dentro da caixa do icone 5 e nao e
      vazia.

USO

    python3 tools/fab_icones_home_apps.py --in <3.0.bin> --out <3.0.bin>
    python3 tools/fab_icones_home_apps.py --in ... --out ... --dry-run
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fab_icones_home as F  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG_NOVO = "assets/IconesHome_escuro_colorido_apps.png"
SHA_NOVO = "eccc855b6a944cd226411400bcc24eaa528f2f8d9f4aaa93f3577ebf5cb462cc"
PNG_ANTIGO = "assets/IconesHome_escuro_colorido.png"
SHA_ANTIGO = "5eff7463214bd8004bce30352b660d75087bb3fa139731d52ab777bf57dffaa2"
SHEET_SHA_2_2 = ("751ca714aeeb4c4810a52334b287fe6db359aa866e398f746f5e7734"
                 "d6b4d742")
CAIXA_ICONE5 = (88, 70, 121, 101)         # caixa final, x0, y0, x1, y1
DESLOC_Y = 8                              # fab_home_moldura: faixa 2 +8


def le_png(caminho, sha_esperado):
    if not os.path.exists(caminho):
        raise ValueError(f"{caminho} nao existe")
    bruto = open(caminho, "rb").read()
    got = hashlib.sha256(bruto).hexdigest()
    if got != sha_esperado:
        raise ValueError(f"{caminho} tem sha256 {got}, esperado "
                         f"{sha_esperado}")
    try:
        from PIL import Image
    except ImportError:
        sys.exit("ERRO: Pillow nao esta instalado (pip3 install Pillow)")
    img = Image.open(caminho)
    if img.size != (F.HOME_LARG, F.HOME_ALT):
        raise ValueError(f"{caminho} tem {img.size[0]}x{img.size[1]}, "
                         f"esperado {F.HOME_LARG}x{F.HOME_ALT}")
    return img.convert("RGB").tobytes()


def caixa_diferenca(a, b):
    xs, ys = [], []
    for y in range(F.HOME_ALT):
        for x in range(F.HOME_LARG):
            if F.pixel(a, x, y) != F.pixel(b, x, y):
                xs.append(x)
                ys.append(y)
    if not xs:
        raise ValueError("os dois PNGs sao iguais; nao ha glifo para trocar")
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def confere_premissas(d):
    erros = []
    if len(d) != F.TAMANHO:
        erros.append(f"a imagem tem {len(d)} bytes, esperado {F.TAMANHO}")
        return erros
    erros += F.confere_cabecalho(d)
    erros += F.confere_sha(d, F.HOME_PAL, F.HOME_FIM - F.HOME_PAL,
                           SHEET_SHA_2_2, "a folha 2.2 (paleta+pixels)")
    return erros


def paleta(d):
    blob = bytes(d[F.HOME_PAL:F.HOME_PX])
    return [(blob[i * 4 + 2], blob[i * 4 + 1], blob[i * 4])
            for i in range(256)]


def confere_resultado(d, orig, novo, caixa):
    erros = []
    x0, y0, x1, y1 = caixa
    if bytes(d[F.HOME_PAL:F.HOME_PX]) != bytes(orig[F.HOME_PAL:F.HOME_PX]):
        erros.append("a paleta da 2.2 foi tocada")
    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    if not dif:
        erros.append("nada mudou na folha")
    for i in dif:
        if not (F.HOME_PX <= i < F.HOME_FIM):
            erros.append(f"alterou fora dos pixels em 0x{i:06X}")
            break
        p = i - F.HOME_PX
        x, y = p % F.HOME_LARG, p // F.HOME_LARG
        if not (x0 <= x < x1 and y0 <= y < y1):
            erros.append(f"alterou fora da caixa do icone 5 em ({x},{y})")
            break
    pal = paleta(d)
    soma = n = 0
    pior = 0
    pior_em = None
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = d[F.HOME_PX + y * F.HOME_LARG + x]
            c = pal[i]
            ref = F.pixel(novo, x, y - DESLOC_Y)
            e = [abs(c[k] - ref[k]) for k in range(3)]
            if max(e) > pior:
                pior, pior_em = max(e), (x, y, c, ref)
            soma += sum(e)
            n += 3
    medio = soma / n if n else 0.0
    if medio > F.ERRO_MEDIO_MAX:
        erros.append(f"erro medio {medio:.2f} > {F.ERRO_MEDIO_MAX}")
    if pior > F.ERRO_MAX:
        x, y, c, ref = pior_em
        erros.append(f"erro maximo {pior} em ({x},{y}): RGB{c} contra "
                     f"RGB{ref} (max {F.ERRO_MAX})")
    return erros, medio, pior


def mesma_entrada(src, dst):
    if os.path.abspath(src) == os.path.abspath(dst):
        return True
    if not os.path.lexists(dst):
        return False
    try:
        return os.path.samefile(src, dst)
    except OSError:
        return False


def main():
    ap = argparse.ArgumentParser(
        description="ficha 021: glifo Apps no indice 5 da folha da home")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--png", default=os.path.join(RAIZ, PNG_NOVO))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.src):
        print(f"RECUSADO: {a.src} nao existe.", file=sys.stderr)
        return 2
    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)
    print("=" * 72)
    print("OpenPod — Reload 3.0: o glifo Apps no indice 5 da home")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n  png    : {a.png}\n")

    erros = confere_premissas(d)
    if erros:
        print("  RECUSADO — a folha de entrada nao e a 2.2:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    try:
        novo = le_png(a.png, SHA_NOVO)
        antigo = le_png(os.path.join(RAIZ, PNG_ANTIGO), SHA_ANTIGO)
        caixa = caixa_diferenca(antigo, novo)
    except ValueError as e:
        print(f"  RECUSADO — {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    x0, y0, x1, y1 = caixa
    caixa_final = (x0, y0 + DESLOC_Y, x1, y1 + DESLOC_Y)
    if (caixa_final[0] < CAIXA_ICONE5[0] or caixa_final[1] < CAIXA_ICONE5[1]
            or caixa_final[2] > CAIXA_ICONE5[2]
            or caixa_final[3] > CAIXA_ICONE5[3]):
        print(f"  RECUSADO — o PNG muda fora da caixa do icone 5: "
              f"{caixa_final} contra {CAIXA_ICONE5}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    pal = paleta(d)
    cache = {}
    for y in range(y0, y1):
        for x in range(x0, x1):
            d[F.HOME_PX + (y + DESLOC_Y) * F.HOME_LARG + x] = \
                F.indice_mais_proximo(pal, F.pixel(novo, x, y), cache)

    print("  premissas conferidas:")
    print(f"    - 2 MiB; cabecalho 0x{F.HOME_CAB:06X} de fabrica")
    print(f"    - folha 2.2 (paleta+pixels) sha256 {SHEET_SHA_2_2[:16]}...")
    print(f"    - PNG antigo {SHA_ANTIGO[:16]}... e novo "
          f"{SHA_NOVO[:16]}...")
    print(f"    - os PNGs so diferem em x {x0}..{x1 - 1}, "
          f"y {y0}..{y1 - 1}; no binario, +{DESLOC_Y} em y\n")
    print(f"  FOLHA  paleta 0x{F.HOME_PAL:06X}..0x{F.HOME_PX:06X} "
          f"INTOCADA")
    print(f"         pixels 0x{F.HOME_PX:06X}..0x{F.HOME_FIM:06X}: so a "
          f"caixa do icone 5 remapeada")

    erros, medio, pior = confere_resultado(d, orig, novo, caixa_final)
    if erros:
        print("  RECUSADO — a folha montada nao passa na conferencia:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print(f"    erro contra o PNG dentro da caixa: medio {medio:.2f} "
          f"(max {F.ERRO_MEDIO_MAX}), maximo {pior} (max {F.ERRO_MAX}) OK\n")

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(i < 0xE000 for i in dif) or any(0xD000 <= i < 0xE000 for i in dif):
        print("  RECUSADO: alterou abaixo de 0xE000 ou o setor 0xD000",
              file=sys.stderr)
        return 1
    if any(i >= 0x1FC000 for i in dif):
        print("  RECUSADO: alterou a PSMP", file=sys.stderr)
        return 1

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
