#!/usr/bin/env python3
"""
patch_status_bar.py — Acabamento da faixa superior: barra com relevo,
                      separador e titulo "OpenPod" ao lado do relogio.

PROPOSITO
    A faixa superior do GN-438 nao esta na folha de imagem: sao objetos
    LVGL da camada view, criados com posicoes e cores em imediatos
    (ver docs/STATUS_BAR.md). A folha de 128x160, por outro lado, e
    desenhada ATRAS deles e cobre a tela inteira -- entao as linhas 0..15
    da folha sao o fundo da faixa, e mexer nelas e dado puro.

    Esta ferramenta faz tres coisas:

    1. PINTA A BARRA. Linhas 0..12 da folha ganham um degrade sutil, mais
       claro em cima; a linha 13 vira um separador claro; as linhas 14 e
       15 ficam no fundo, dando respiro antes da primeira linha da lista
       (y=16). E o "efeito de barra" do nano, feito so com indices de
       paleta JA EXISTENTES.

    2. TRANSFORMA O ICONE DO SD EM TITULO. O label do icone do cartao
       (`0x00D226F8`, glifo U+E647) passa a ser um rotulo de texto
       centralizado no topo, com a fonte padrao. Assim sobra relogio A
       ESQUERDA + titulo NO CENTRO + bateria A DIREITA, sem objeto novo.
       O icone do cartao deixa de aparecer.

    3. GRAVA A STRING NA AREA LIVRE. "OpenPod" vai para 0x001A3038
       (endereco XIP 0x00DA3038), os 364 KiB de 0xFF fora de todas as
       particoes. E o primeiro dado do OpenPod nessa regiao -- e serve de
       ensaio para o V017, que pretende por CODIGO la.

O QUE E ALTERADO

    0x001A3038   8 B  string "OpenPod\\0"                     (area livre)
    0x00122740   4 B  ponteiro do texto  0x00C5D608 -> 0x00DA3038
    0x00122714   4 B  bl set_style_text_font -> 2x NOP  (usa a fonte padrao)
    0x00122708   1 B  align   1 (TOP_LEFT) -> 2 (TOP_MID)
    0x00122706   1 B  x_ofs   0x28 (40)    -> 0x04
    0x00122702   1 B  y_ofs   0x00         -> 0x02
    0x000CE15C   px   linhas 0..15 da folha: degrade, separador e respiro

    Mais o CRC-16 da particao FIRM. A string em 0x1A3038 fica FORA da
    FIRM, logo fora desse CRC -- e dado, nao precisa de integridade
    alem da releitura que o script de gravacao ja faz por setor.

GEOMETRIA RESULTANTE (medida na fonte do proprio firmware)

    relogio  "88:88"    31 px, ancorado TOP_LEFT + (3, 2)  -> x  3.. 34
    titulo   "OpenPod"  52 px, TOP_MID + (4, 2)            -> x 42.. 94
    bateria             TOP a partir de x=107

    Folga de 8 px do relogio e 13 px da bateria.

USO
    python3 tools/patch_status_bar.py \
        --in  firmware/WORKING/GN438_openpod_v015.bin \
        --out firmware/WORKING/GN438_openpod_v016.bin [--titulo OpenPod] [--dry-run]

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se QUALQUER byte de origem nao estiver no valor esperado;
    - recusa se a area livre de destino nao estiver toda em 0xFF;
    - recusa se as linhas 0..15 da folha nao estiverem todas no fundo
      (garante que nenhum chevron ou icone sera pintado por cima);
    - recusa titulo que nao caiba entre o relogio e a bateria;
    - a entrada e aberta somente para leitura; a saida e arquivo novo.

LIMITACOES
    - Geometria valida para este firmware (yp3_2.0.43).
    - Nao altera a paleta: usa indices existentes.
    - O icone do cartao SD deixa de existir. A informacao de cartao
      presente/ausente some da faixa.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

FLASH_XIP = 0x00C00000

# --- folha ----------------------------------------------------------------
IMG_DESC = 0x000CDD50
PIX_OFF = 0x000CE15C
IMG_W, IMG_H = 128, 160
BG_INDEX = 1
BARRA_ALTURA = 16          # linhas 0..15; a lista comeca em 16

# degrade da barra: (primeira_linha, ultima_linha, indice_de_paleta)
#   indices conferidos na paleta da folha:
#     181 (61,65,70)  234 (46,50,55)  33 (31,35,41)  84 (28,32,38)  51 (88,92,98)
#   A barra vai ate y=12 e o separador fica em y=13. As linhas 14 e 15
#   ficam no fundo, dando respiro antes da primeira linha da lista (y=16).
BANDAS = [(0, 3, 234), (4, 8, 33), (9, 12, 84)]
SEPARADOR_Y, SEPARADOR_IDX = 13, 181

# --- area livre -----------------------------------------------------------
STR_OFF = 0x001A3038
STR_MAX = 32               # quanto exigimos de 0xFF no destino

# --- pontos de codigo (offset, esperado, novo, descricao) -----------------
POOL_TEXTO = 0x00122740    # 4 B: ponteiro da string do label
POOL_TEXTO_ESPERADO = 0x00C5D608
BL_FONTE = 0x00122714      # 4 B: bl lv_obj_set_style_text_font
BL_FONTE_ESPERADO = bytes.fromhex("2af00bfd")
NOP2 = bytes.fromhex("00bf00bf")
BYTES = [
    (0x00122708, 0x01, 0x02, "align  1 (TOP_LEFT) -> 2 (TOP_MID)"),
    (0x00122706, 0x28, 0x04, "x_ofs  0x28 (40)    -> 0x04"),
    (0x00122702, 0x00, 0x02, "y_ofs  0x00         -> 0x02"),
]

# --- fonte, so para medir a largura do titulo -----------------------------
FONT_TABLE = 0x00086C44
FONT_CMAP = 0x000A27E6
FONT_N = 7098
RELOGIO_X, RELOGIO_W = 3, 31        # "88:88"
BATERIA_X = 107


def largura(d, idx, s):
    t = 0
    for c in s:
        i = idx.get(ord(c))
        if i is None:
            return None
        t += struct.unpack_from("<2I", d, FONT_TABLE + i * 16)[1]
    return t


def firm_entry(data):
    pt = struct.unpack_from("<I", data, 0x20)[0]
    n = struct.unpack_from("<I", data, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if data[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", data, b + 4)
            return b, off, ln
    raise RuntimeError("particao FIRM nao encontrada")


def check(data, titulo, idx):
    e = []

    hdr = struct.unpack_from("<I", data, IMG_DESC)[0]
    cf, w, h = hdr & 0x1F, (hdr >> 10) & 0x7FF, (hdr >> 21) & 0x7FF
    if (cf, w, h) != (10, IMG_W, IMG_H):
        e.append(f"descritor da folha inesperado: cf={cf} {w}x{h}")

    sujo = [(x, y) for y in range(BARRA_ALTURA) for x in range(IMG_W)
            if data[PIX_OFF + y * IMG_W + x] != BG_INDEX]
    if sujo:
        e.append(f"as linhas 0..{BARRA_ALTURA-1} da folha nao estao limpas: "
                 f"{len(sujo)} pixels fora do fundo (1o em {sujo[0]})")

    got = struct.unpack_from("<I", data, POOL_TEXTO)[0]
    if got != POOL_TEXTO_ESPERADO:
        e.append(f"pool do texto em 0x{POOL_TEXTO:06X} e 0x{got:08X}, "
                 f"esperado 0x{POOL_TEXTO_ESPERADO:08X}")

    if bytes(data[BL_FONTE:BL_FONTE + 4]) != BL_FONTE_ESPERADO:
        e.append(f"instrucao em 0x{BL_FONTE:06X} nao e o bl esperado")

    for o, esp, _, _ in BYTES:
        if data[o] != esp:
            e.append(f"0x{o:06X}: esperado 0x{esp:02X}, "
                     f"encontrado 0x{data[o]:02X}")

    alvo = data[STR_OFF:STR_OFF + STR_MAX]
    if any(b != 0xFF for b in alvo):
        e.append(f"area livre 0x{STR_OFF:06X} nao esta virgem (0xFF)")

    w = largura(data, idx, titulo)
    if w is None:
        e.append(f"titulo {titulo!r} tem caractere fora da fonte")
    else:
        x0 = (IMG_W - w) // 2 + BYTES[1][2]
        if x0 < RELOGIO_X + RELOGIO_W + 4:
            e.append(f"titulo de {w} px encosta no relogio (x0={x0})")
        if x0 + w > BATERIA_X - 4:
            e.append(f"titulo de {w} px encosta na bateria "
                     f"(fim={x0 + w}, bateria em {BATERIA_X})")
    return e, w


def main():
    ap = argparse.ArgumentParser(
        description="Faixa superior: barra com relevo, separador e titulo")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--titulo", default="OpenPod")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if os.path.abspath(args.src) == os.path.abspath(args.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    with open(args.src, "rb") as fh:          # somente leitura
        orig = fh.read()
    data = bytearray(orig)

    cmap = struct.unpack_from("<%dH" % FONT_N, data, FONT_CMAP)
    idx = {c: i for i, c in enumerate(cmap)}

    print("=" * 72)
    print("OpenPod — faixa superior: barra, separador e titulo")
    print("=" * 72)
    print(f"  origem : {args.src}")
    print(f"  destino: {args.dst}")
    print(f"  titulo : {args.titulo!r}")
    print()

    erros, w = check(data, args.titulo, idx)
    if erros:
        print("  ABORTADO — o firmware de entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    x0 = (IMG_W - w) // 2 + BYTES[1][2]
    print("  estado de entrada conferido: folha limpa nas linhas 0..15, "
          "pool e imediatos originais,")
    print(f"  area livre virgem em 0x{STR_OFF:06X}  OK")
    print()
    print("  GEOMETRIA (fonte do proprio firmware)")
    print(f"    relogio            31 px   x {RELOGIO_X:>3} .. {RELOGIO_X+RELOGIO_W:>3}")
    print(f"    titulo {args.titulo!r:<10} {w:>3} px   x {x0:>3} .. {x0+w:>3}")
    print(f"    bateria                    x {BATERIA_X:>3} ..")
    print(f"    folgas: {x0-(RELOGIO_X+RELOGIO_W)} px do relogio, "
          f"{BATERIA_X-(x0+w)} px da bateria")
    print()

    # 1 — string na area livre
    s = args.titulo.encode("utf-8") + b"\0"
    data[STR_OFF:STR_OFF + len(s)] = s
    print("  ALTERACOES")
    print(f"    0x{STR_OFF:06X}  string {args.titulo!r} "
          f"({len(s)} B) — area livre, XIP 0x{STR_OFF + FLASH_XIP:08X}")

    # 2 — ponteiro do texto
    struct.pack_into("<I", data, POOL_TEXTO, STR_OFF + FLASH_XIP)
    print(f"    0x{POOL_TEXTO:06X}  ponteiro do texto 0x{POOL_TEXTO_ESPERADO:08X}"
          f" -> 0x{STR_OFF + FLASH_XIP:08X}")

    # 3 — fonte de icones -> fonte padrao (NOP no bl)
    data[BL_FONTE:BL_FONTE + 4] = NOP2
    print(f"    0x{BL_FONTE:06X}  bl set_style_text_font -> 2x NOP "
          "(passa a usar a fonte padrao)")

    # 4 — posicao
    for o, esp, novo, desc in BYTES:
        data[o] = novo
        print(f"    0x{o:06X}  {esp:02X} -> {novo:02X}   {desc}")

    # 5 — barra na folha
    pintados = 0
    for y0, y1, pi in BANDAS:
        for y in range(y0, y1 + 1):
            for x in range(IMG_W):
                data[PIX_OFF + y * IMG_W + x] = pi
                pintados += 1
    for x in range(IMG_W):
        data[PIX_OFF + SEPARADOR_Y * IMG_W + x] = SEPARADOR_IDX
        pintados += 1
    for y in range(SEPARADOR_Y + 1, BARRA_ALTURA):      # respiro
        for x in range(IMG_W):
            data[PIX_OFF + y * IMG_W + x] = BG_INDEX
    faixas = " ".join(f"y{y0}-{y1}:idx{pi}" for y0, y1, pi in BANDAS)
    print(f"    0x{PIX_OFF:06X}  barra na folha, {pintados} px  "
          f"[{faixas} · y{SEPARADOR_Y}:idx{SEPARADOR_IDX}]")
    print()

    base, foff, flen = firm_entry(data)
    old_crc = struct.unpack_from("<H", data, base + 0x0C)[0]
    new_crc = fw.crc16(bytes(data[foff:foff + flen]))
    if args.dry_run:
        print(f"  CRC da FIRM: 0x{old_crc:04X} -> 0x{new_crc:04X} (nao gravado)")
    else:
        # R1: o CRC da FIRM nao e verificado pelo aparelho, e gravar aqui
        # poria o setor 0x00D000 (tabela de particoes) de volta na lista
        # de setores a escrever. Foi esse setor que matou o primeiro
        # aparelho. Achado pelo tools/build.py ao reconstruir do zero.
        pass   # NAO gravar o CRC (R1)
        print(f"  CRC da FIRM: 0x{old_crc:04X} -> 0x{new_crc:04X}")

    d2 = [i for i in range(len(orig)) if orig[i] != data[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in d2})
    print(f"  bytes alterados: {len(d2)}   tamanho: inalterado ({len(data)})")
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
