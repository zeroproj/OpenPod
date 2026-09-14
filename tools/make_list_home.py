#!/usr/bin/env python3
"""
make_list_home.py — Transforma o menu principal do GN-438 de GRADE 3x3 em
                    LISTA VERTICAL no estilo iPod nano 2G.

PROPOSITO
    O menu principal (page_home_create, 0x00D2EBB8) e montado a partir de
    DADOS: duas tabelas de coordenadas, uma tabela de ids de texto e uma
    folha de imagem de 128x160. Os 9 objetos de imagem do laco NAO recebem
    fonte de imagem -- lv_img_set_src (0xd5d868) e chamada UMA vez, fora do
    laco, sobre a folha inteira. Ou seja: o que se ve como "icone" sao
    PIXELS DA FOLHA.

    Isto torna a mudanca de layout um patch de DADO, nao de codigo:

      - nenhum malloc muda;
      - nenhum offset de estrutura muda;
      - nenhuma aritmetica de ponteiro e tocada;
      - nenhuma tecla e remapeada (+-1 ja existe nativamente);
      - qualquer erro aparece na tela imediatamente.

    Ver docs/MENU_LISTA.md secoes 16 e 18 para a analise completa.

O QUE E ALTERADO (5 pontos)

    1  0x0004867C  36 B  9 pares int16 (x,y) das areas de icone
    2  0x000486A0  36 B  9 pares int16 (x,y) dos rotulos
    3  0x0012ED5E   1 B  largura do rotulo  0x28 (40) -> 0x64 (100)
    4  0x0012ED54   1 B  text_align  2 (centro) -> 0 (esquerda)
    5  0x000CE15C   pixels da folha 128x160 INDEXED_8, redesenhada

    Mais o CRC-16 da particao FIRM, recalculado (fw_common.crc16).

LAYOUT PRODUZIDO (--style nano)

    y =  0..15   faixa de status, intocada (preta na folha, como hoje)
    linha i:     y = 16 + 16*i,  i = 0..8
                 rotulo  100x15 em x = 6, alinhado a esquerda
                 chevron   6x9  em x = 116, centrado na linha
    ultima linha y = 144..159  -> fecha exatamente em 160

    Fiel a referencia do nano 2G: sem icone a esquerda, chevron a direita.
    A selecao continua sendo cor de texto (paleta 7), que e o que a pagina
    da grade sabe fazer -- barra de realce exigiria objeto novo (codigo).

USO
    python3 tools/make_list_home.py \
        --in  firmware/WORKING/GN438_openpod_v013.bin \
        --out firmware/WORKING/GN438_openpod_v014.bin [--dry-run]

    --dry-run  analisa, confere o estado de entrada e relata, sem gravar.

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se o descritor da imagem nao for INDEXED_8 128x160;
    - recusa se as tabelas de entrada nao contiverem EXATAMENTE a grade
      3x3 original (garante que a base e o V013/original, nao um patch
      ja aplicado ou outro firmware);
    - recusa se os dois bytes de constante nao forem 0x28 e 0x02;
    - a entrada e aberta somente para leitura; a saida e arquivo novo.

LIMITACOES
    - Geometria valida para este firmware (yp3_2.0.43). Outra versao exige
      nova analise.
    - Nao altera a paleta.
    - Nao mexe em teclas: os ramos de +-3 (key_id 0xa0 / 0x81) passam a
      pular 3 linhas. Estranho, nao quebrado. Decidir depois de ver no
      aparelho.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

# --- geometria do firmware -------------------------------------------------
TBL_ICON = 0x0004867C          # 9 pares int16 (x, y) das areas de icone
TBL_LABEL = 0x000486A0         # 9 pares int16 (x, y) dos rotulos
OFF_ALIGN = 0x0012ED54         # imm de `movs r1, #2`  (text_align)
OFF_WIDTH = 0x0012ED5E         # imm de `movs r1, #0x28` (largura do rotulo)

IMG_DESC = 0x000CDD50
PIX_OFF = 0x000CE15C
IMG_W, IMG_H = 128, 160

BG_INDEX = 1                   # preto puro (0,0,0) na paleta da folha
FG_INDEX = 0                   # (229,233,237), o mais claro da paleta

# estado de entrada esperado: a grade 3x3 original
GRID_ICON = [(9, 17), (49, 17), (89, 17),
             (9, 65), (49, 65), (89, 65),
             (9, 113), (49, 113), (89, 113)]
GRID_LABEL = [(3, 48), (44, 48), (86, 48),
              (3, 96), (44, 96), (86, 96),
              (3, 144), (44, 145), (86, 145)]

# --- layout da lista -------------------------------------------------------
ROW_H = 16
ROW_Y0 = 16
LABEL_X = 6
LABEL_W = 100
CHEVRON_X = 116

# chevron 6x9, 2 px de espessura
CHEVRON = [
    "##....",
    ".##...",
    "..##..",
    "...##.",
    "....##",
    "...##.",
    "..##..",
    ".##...",
    "##....",
]

ITEMS = ["Musica", "video", "Gravacao", "Radio", "Livro digital",
         "Imagem", "Bluetooth", "Configurar", "Ver pastas"]


def read_pairs(data, off, n=9):
    return [struct.unpack_from("<hh", data, off + i * 4) for i in range(n)]


def write_pairs(data, off, pairs):
    for i, (x, y) in enumerate(pairs):
        struct.pack_into("<hh", data, off + i * 4, x, y)


def firm_entry(data):
    """Devolve (base_da_entrada, offset, tamanho) da particao FIRM."""
    pt = struct.unpack_from("<I", data, 0x20)[0]
    n = struct.unpack_from("<I", data, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if data[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", data, b + 4)
            return b, off, ln
    raise RuntimeError("particao FIRM nao encontrada")


def check_input(data):
    """Confere que a base e o firmware esperado. Devolve lista de erros."""
    erros = []

    hdr = struct.unpack_from("<I", data, IMG_DESC)[0]
    cf, w, h = hdr & 0x1F, (hdr >> 10) & 0x7FF, (hdr >> 21) & 0x7FF
    if (cf, w, h) != (10, IMG_W, IMG_H):
        erros.append(f"descritor da folha inesperado: cf={cf} {w}x{h}")

    got = read_pairs(data, TBL_ICON)
    if got != GRID_ICON:
        erros.append(f"tabela de icones nao e a grade original: {got}")

    got = read_pairs(data, TBL_LABEL)
    if got != GRID_LABEL:
        erros.append(f"tabela de rotulos nao e a grade original: {got}")

    if data[OFF_WIDTH] != 0x28:
        erros.append(f"largura do rotulo em 0x{OFF_WIDTH:06X} "
                     f"e 0x{data[OFF_WIDTH]:02X}, esperado 0x28")
    if data[OFF_ALIGN] != 0x02:
        erros.append(f"text_align em 0x{OFF_ALIGN:06X} "
                     f"e 0x{data[OFF_ALIGN]:02X}, esperado 0x02")

    return erros


def draw_sheet(data):
    """Reescreve os pixels da folha: fundo preto + 9 chevrons a direita."""
    for i in range(IMG_W * IMG_H):
        data[PIX_OFF + i] = BG_INDEX

    ch_h = len(CHEVRON)
    for i in range(9):
        y0 = ROW_Y0 + i * ROW_H + (ROW_H - ch_h) // 2
        for dy, linha in enumerate(CHEVRON):
            for dx, c in enumerate(linha):
                if c != "#":
                    continue
                x, y = CHEVRON_X + dx, y0 + dy
                if 0 <= x < IMG_W and 0 <= y < IMG_H:
                    data[PIX_OFF + y * IMG_W + x] = FG_INDEX


def setores(diffs, size=0x1000):
    return sorted({o // size * size for o in diffs})


def main():
    ap = argparse.ArgumentParser(
        description="Menu principal: grade 3x3 -> lista vertical estilo nano")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--style", default="nano", choices=["nano"],
                    help="nano: so texto + chevron (fiel a referencia)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if os.path.abspath(args.src) == os.path.abspath(args.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    with open(args.src, "rb") as fh:          # somente leitura
        orig = fh.read()
    data = bytearray(orig)

    print("=" * 72)
    print("OpenPod — menu principal em LISTA (estilo iPod nano 2G)")
    print("=" * 72)
    print(f"  origem : {args.src}")
    print(f"  destino: {args.dst}")
    print()

    erros = check_input(data)
    if erros:
        print("  ABORTADO — o firmware de entrada nao e o esperado:")
        for e in erros:
            print(f"    - {e}")
        return 1
    print("  estado de entrada conferido: grade 3x3 original, "
          "folha INDEXED_8 128x160, constantes 0x28/0x02  OK")
    print()

    # 1 e 2 — tabelas de coordenadas
    novo_icone = [(CHEVRON_X, ROW_Y0 + i * ROW_H) for i in range(9)]
    novo_rotulo = [(LABEL_X, ROW_Y0 + i * ROW_H) for i in range(9)]
    write_pairs(data, TBL_ICON, novo_icone)
    write_pairs(data, TBL_LABEL, novo_rotulo)

    print("  LAYOUT")
    print(f"    {'#':>2}  {'item':<14} {'rotulo (x,y)':<14} {'chevron (x,y)'}")
    for i, nome in enumerate(ITEMS):
        print(f"    {i:>2}  {nome:<14} "
              f"{str(novo_rotulo[i]):<14} {str(novo_icone[i])}")
    print()

    # 3 e 4 — constantes
    data[OFF_WIDTH] = LABEL_W
    data[OFF_ALIGN] = 0x00
    print("  CONSTANTES")
    print(f"    0x{OFF_WIDTH:06X}  largura do rotulo  0x28 (40) -> "
          f"0x{LABEL_W:02X} ({LABEL_W})")
    print(f"    0x{OFF_ALIGN:06X}  text_align         0x02 (centro) -> "
          f"0x00 (esquerda)")
    print()

    # 5 — folha
    draw_sheet(data)

    # diferencas
    diffs = [i for i in range(len(orig)) if orig[i] != data[i]]
    print("  ALTERACOES")
    print(f"    bytes alterados : {len(diffs)}")
    print(f"    faixa           : 0x{diffs[0]:06X} .. 0x{diffs[-1]:06X}")
    print(f"    tamanho         : inalterado ({len(data)} bytes)")
    print(f"    paleta          : NAO alterada")
    print()

    # CRC da FIRM — NAO e recalculado, de proposito.
    #
    # Regra R1 (docs/PROTOCOLO_GRAVACAO.md): o CRC da FIRM **nao e
    # verificado** pelo aparelho, e o setor 0x00D000 (tabela de
    # particoes) NUNCA deve ser escrito — foi ele que matou o primeiro
    # aparelho. Regravar o CRC aqui poria 0x00D000 de volta na lista de
    # setores a gravar.
    #
    # Esta ferramenta recalculava e gravava. Ninguem percebeu porque a
    # cadeia historica nunca foi reconstruida do zero; o `tools/build.py`
    # reconstruiu, comparou com a imagem que boota, e achou os 2 bytes.
    base, foff, flen = firm_entry(data)
    old_crc = struct.unpack_from("<H", data, base + 0x0C)[0]
    calc = fw.crc16(bytes(data[foff:foff + flen]))
    print(f"  CRC da FIRM: campo intocado (R1). "
          f"valor no arquivo 0x{old_crc:04X}, calculado 0x{calc:04X}")

    # setores de 4 KiB a regravar (com o CRC ja aplicado)
    d2 = [i for i in range(len(orig)) if orig[i] != data[i]]
    secs = setores(d2)
    print(f"  setores de 4 KiB a regravar: {len(secs)}")
    print("    " + "  ".join(f"0x{s:06X}" for s in secs))
    print()

    if args.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0

    with open(args.dst, "wb") as fh:
        fh.write(data)
    print(f"  gravado: {args.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
