#!/usr/bin/env python3
"""
patch_marte_paleta.py — Marte M1: o tema claro do iPod nano, em 12 bytes.

O QUE FAZ

    Troca seis campos de cor da tabela de tema do Saturno, em 0x001A5400.
    Nenhum byte de codigo. Nenhuma rotina nova.

    E o passo de maior efeito visivel e menor risco do projeto: o
    aparelho inteiro muda de cara, e desfazer sao os mesmos 12 bytes.

DE ONDE VEM CADA COR

    Extraidas bitmap a bitmap do tema NanoClone 5.2 (Billy Blair,
    CC BY-SA 3.0), em `marte/paleta/nanoclone.json`. Nao sao escolha
    nossa: sao as cores do tema.

    O iPod nano e tema CLARO — `foreground 000000`, `background FFFFFF`
    no .cfg. O OpenPod foi para o escuro. Marte nao e ajuste de cor: e
    inverter o tema inteiro.

        campo            hoje      Marte (RGB565)   gravado
        cor_tela         0x0000    0xFFFF branco    0xFFFF
        cor_faixa        0x8208    0xBE39 cinza     0x39BE
        cor_separador    0xC731    0x5B0D           0x0D5B
        cor_texto        0xFFFF    0x0000 preto     0x0000
        cor_texto_sel    0xFFFF    0xFFFF branco    0xFFFF
        cor_selecao      0xFA05    0x2B3B azul      0x3B2B

O SWAP, QUE E FACIL ERRAR

    O display e RGB565 com os bytes trocados, e a tabela guarda os
    valores PRE-INVERTIDOS (docs/COLOR_SOURCE.md 9). A ferramenta recebe
    RGB565 puro e faz o swap — nao passe valor ja invertido.

    Prova de que a tabela e mesmo pre-invertida: a selecao de hoje esta
    gravada como 0xFA05, cujo swap e 0x05FA — R=0, G=47, B=26, o ciano
    que se ve na tela. Se nao houvesse swap, 0xFA05 seria um vermelho.

POR QUE ISTO PODE CONSERTAR DEFEITO, E NAO SO RECOLORIR

    Fotografado no aparelho em 2026-09-14, com a Core 2.0: onde o
    conteiner nao e coberto por itens, aparece BRANCO — o fundo do
    display, que ninguem pinta. No Despertador sao 3 itens e sobra um
    bloco branco; na home os 9 itens cobrem tudo.

    No tema do nano o conteudo E BRANCO. O buraco que hoje parece
    defeito passa a ser o fundo certo — e o texto, que hoje e branco
    sobre branco quando cai ali, passa a ser preto.

    Classe: PROVAVEL. So o aparelho decide.

USO
    python3 tools/patch_marte_paleta.py --in <entrada.bin> --out <saida.bin>
                                        [--dry-run]

DEPENDENCIAS
    Python 3

LIMITACOES
    - exige a tabela do Saturno presente: RECUSA se 0x001A5400 estiver
      virgem. Marte M1 nao funciona sobre a Core 1.0.x;
    - so cor. Degrade da faixa e da selecao sao M2/M3, e precisam de
      rotina nova;
    - nao mexe em geometria: altura de faixa, de linha e inicio da lista
      ficam como estao.
"""

import argparse, hashlib, struct, sys

TAB      = 0x001A5400
PROIBIDO = 0x0000D000

# (offset na tabela, nome, RGB565 puro do NanoClone)
CAMPOS = [
    (0x00, "cor_tela",      0xFFFF),
    (0x02, "cor_faixa",     0xBE39),
    (0x04, "cor_separador", 0x5B0D),
    (0x06, "cor_texto",     0x0000),
    (0x08, "cor_texto_sel", 0xFFFF),
    (0x0A, "cor_selecao",   0x2B3B),
]


def swap(v):
    """RGB565 puro -> como a tabela guarda (bytes trocados)."""
    return ((v & 0xFF) << 8) | (v >> 8)


def main():
    ap = argparse.ArgumentParser(description="Marte M1: o tema claro do nano")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != 0x200000:
        print(f"ERRO: {a.src} tem {len(d)} B, esperado 2097152", file=sys.stderr)
        return 1
    orig = bytes(d)

    print("\n  MARTE M1 — O TEMA CLARO DO IPOD NANO\n")

    if all(x == 0xFF for x in d[TAB:TAB + 0x14]):
        print(f"  ABORTADO: a tabela de tema em 0x{TAB:06X} esta VIRGEM.",
              file=sys.stderr)
        print("  Marte M1 escreve nela. E preciso a carcaca antes "
              "(receita core2.0).", file=sys.stderr)
        return 1

    print(f"  tabela em 0x{TAB:06X}")
    print()
    print("    campo            antes     depois    (RGB565 -> gravado)")
    for off, nome, rgb in CAMPOS:
        antes = struct.unpack_from("<H", d, TAB + off)[0]
        novo = swap(rgb)
        print(f"    {nome:<14}  0x{antes:04X}    0x{novo:04X}"
              f"    (0x{rgb:04X} -> 0x{novo:04X})")
        struct.pack_into("<H", d, TAB + off, novo)
    print()

    # relendo da imagem, nao da variavel
    ok = all(struct.unpack_from("<H", d, TAB + off)[0] == swap(rgb)
             for off, _, rgb in CAMPOS)
    print(f"  conferencia: relido da tabela  {'OK' if ok else 'DIVERGE'}")
    if not ok:
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    fora = [i for i in dif if not (TAB <= i < TAB + 0x0C)]
    if fora:
        print(f"  ABORTADO: escreveu fora da faixa de cor da tabela, "
              f"em 0x{min(fora):06X}", file=sys.stderr)
        return 1
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido (R1).", file=sys.stderr)
        return 1
    print("  tudo dentro dos 12 bytes de cor da tabela   OK")
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}\n")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
