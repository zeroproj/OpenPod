#!/usr/bin/env python3
"""
diag_cores.py — pinta cada campo da tabela de uma cor inconfundivel.

NAO E UMA VERSAO. E um instrumento de medicao.

POR QUE

    Com o tema claro, apareceu um cinza atras do texto das listas. O
    mantenedor notou que ele parece **o mesmo cinza da faixa superior**.

    Duas horas de leitura estatica nao fecharam a questao: a linha esta
    mandada a ler `cor_tela` (0x0012177C -> 0x00DA5A20), mas o que se ve
    nao e branco. Ou outra coisa repinta depois, ou eu estou lendo o
    caminho errado.

    Em vez de continuar adivinhando, pergunta-se ao aparelho. Cada campo
    ganha uma cor impossivel de confundir, e UMA FOTO responde:

        quem pinta a linha?
        quem pinta o vao entre as linhas?
        quem pinta a faixa?
        de onde vem a cor do texto?

    E o mesmo metodo do `experiments/DIAGNOSTICO cores`, que ja resolveu
    a pergunta equivalente uma vez neste projeto.

AS CORES

    cor_tela        VERMELHO
    cor_faixa       VERDE
    cor_separador   AMARELO
    cor_texto       AZUL
    cor_texto_sel   MAGENTA
    cor_selecao     CIANO

    O aparelho vai ficar horroroso. E de proposito: cada cor tem de ser
    impossivel de confundir com as outras.

COMO LER A FOTO

    linha (onde esta o texto) VERMELHA -> le cor_tela, como mandamos
    linha VERDE                        -> le cor_faixa  <- a suspeita
    linha de outra cor                 -> le outro campo
    linha SEM MUDAR                    -> nao vem da tabela: e um dos 79
                                          pontos que pintam fundo fora dela

USO
    python3 tools/diag_cores.py --in <imagem.bin> --out <diag.bin>
"""

import argparse, hashlib, struct, sys

TAB = 0x001A5400
# (offset, nome, RGB565 puro)
CORES = [
    (0x00, "cor_tela",      0xF800, "VERMELHO"),
    (0x02, "cor_faixa",     0x07E0, "VERDE"),
    (0x04, "cor_separador", 0xFFE0, "AMARELO"),
    (0x06, "cor_texto",     0x001F, "AZUL"),
    (0x08, "cor_texto_sel", 0xF81F, "MAGENTA"),
    (0x0A, "cor_selecao",   0x07FF, "CIANO"),
]


def swap(v):
    return ((v & 0xFF) << 8) | (v >> 8)


def main():
    ap = argparse.ArgumentParser(description="instrumento: cores berrantes")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != 0x200000:
        print(f"ERRO: {a.src} tem {len(d)} B", file=sys.stderr)
        return 1
    if all(x == 0xFF for x in d[TAB:TAB + 0x14]):
        print("ABORTADO: tabela virgem.", file=sys.stderr)
        return 1

    print("\n  DIAGNOSTICO DE CORES — instrumento, nao versao\n")
    for off, nome, rgb, cor in CORES:
        struct.pack_into("<H", d, TAB + off, swap(rgb))
        print(f"    +{off:02X}  {nome:<14} -> {cor}")
    print()
    print("  O aparelho vai ficar horroroso. E de proposito.")
    print("  Fotografe CONFIGURAR e mande. Uma foto responde tudo.\n")
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    print(f"  sha256 : {hashlib.sha256(bytes(d)).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
