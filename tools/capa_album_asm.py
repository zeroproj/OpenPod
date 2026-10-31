#!/usr/bin/env python3
"""
capa_album_asm.py — a montagem do código da capa do álbum (RC7, ficha 007).

PROPOSITO

    O módulo que o `fab_capa_album.py` usa para montar e conferir o código
    das rotinas novas da RC7 (a capa do álbum na Tocando Agora). Ele mora
    aqui, e não dentro da ferramenta, por causa da regra do projeto: uma
    ferramenta nova tem no máximo 350 linhas (D06).

    O código das rotinas é ASSEMBLY Thumb-2 (tools/capa_album.s), montado
    pelo clang (tools/asm.py). SEM compilador C: a saída mudaria com a
    versão do compilador e a catraca (o sha256 da imagem) quebraria.

    O que este módulo sabe:

      - o LAYOUT do lote 0x001A8000..0x001AB000 (o descritor do quadrado
        cinza, os 8192 pixels dele, a tabela das entradas e o código);
      - os ENCODERS do Thumb-2 (o `bl` do papel de parede, o `b.w` do
        set_text e os `b.w` da tabela de entradas), com o mesmo par
        encoder/leitor que o `tests/test_rc7.py` usa para conferir;
      - a MONTAGEM do código (o clang sobre tools/capa_album.s) e a
        CONFERÊNCIA dele (os três trampolins no lugar, o código dentro do
        lote e os alvos ciertos).

DEPENDENCIAS

    Python 3 (stdlib) + o clang (o montador, via tools/asm.py).

LIMITACOES

    - o código é montado na hora: é preciso ter o clang instalado;
    - o layout é FIXO: mudar a ordem do .text muda os endereços das
      rotinas, e a conferência recusa;
    - nada aqui escreve no binário: a escrita é da ferramenta.
"""

import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import monta  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XIP = 0x00C00000
TAMANHO = 0x200000

# --- a entrada: a RC6 exata (catraca, aprovada em 2026-10-30)
SHA_ENTRADA = ("af3a2b6d8aaa1bf9d709c20e3ccd8d3f1aeb37cc6843a6070938e122"
               "488f4bc8")

# --- o lote novo (o MAPA do build.py declara o mesmo)
LOTE, LOTE_TAM = 0x1A8000, 0x3000
DSC, DSC_TAM = 0x1A8000, 12             # o descritor da imagem cinza
PIX, PIX_TAM = 0x1A8010, 8192          # os pixels do quadrado cinza
TABELA = 0x1AA010                      # as três entradas (b.w)
CODIGO = 0x1AA01C                      # o código das rotinas
ENTRADAS = (0x00DAA01C, 0x00DAA020, 0x00DAA024)   # CRIA, TITULO, APAGA
HDR_64 = 0x08010004                    # cf 4 (TRUE_COLOR), 64 x 64
DSC_GRAY = 0x00DA8000                  # o endereço XIP do descritor
PIX_GRAY = 0x00DA8010                  # o endereço XIP dos pixels (o `data`)

# --- os ganchos na pagina da musica
TAM_VIEW = {0x131E80: (b"\x30\x20", b"\x34\x20"),   # lv_mem_alloc(0x30)
            0x131E9E: (b"\x30\x22", b"\x34\x22")}   # memset(view,0,0x30)
GANCHO_BL = (0x131EB6, 0x00D5D850, 0x00DAA010)      # lv_img_create -> CRIA
GANCHO_B = (0x13225E, 0x00D5ED94, 0x00DAA014)      # lv_label_set_text -> TITULO

# --- o TJpgDec da fabrica: e ele que decodifica a capa
TJPGDEC = (0x10900, 0x12000)          # os deslocamentos no arquivo
SHA_TJPGDEC = ("e6be1a9737738ff6117af4341339f2ade2ee22c22dad96d6c31e0"
               "902f1854477")

# --- o quadrado cinza (o modelo aprovado)
PLACEHOLDER = os.path.join(RAIZ, "tests/assets/rc7/placeholder_64x64.rgb565swap")
SHA_PLACEHOLDER = ("a2609171002492a88383fc5b506f24a0ef47fcda3949908fed3204"
                   "59e21b0bac")
FONTE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capa_album.s")

PERMITIDO = ([(a, a + 2) for a in sorted(TAM_VIEW)]
             + [(GANCHO_BL[0], GANCHO_BL[0] + 4),
                (GANCHO_B[0], GANCHO_B[0] + 4),
                (LOTE, LOTE + LOTE_TAM)])


# ---------------------------------------------------------------------------
# Thumb-2: os alvos dos ganchos, lidos e escritos de volta
# ---------------------------------------------------------------------------

def desvio(b, a, base=XIP):
    """Alvo de um BL (T1) ou B.W (T4) no deslocamento `a`; None se nao for.

    `base` e o endereco XIP de onde o bloco `b` foi tirado."""
    if a + 4 > len(b):
        return None
    h1, h2 = struct.unpack_from("<HH", b, a)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xD000) not in (0xD000, 0x9000):
        return None
    S = (h1 >> 10) & 1
    I1 = 1 - (((h2 >> 13) & 1) ^ S)
    I2 = 1 - (((h2 >> 11) & 1) ^ S)
    off = (S << 24) | (I1 << 23) | (I2 << 22) \
        | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if S:
        off -= 1 << 25
    return ("bl" if h2 & 0x4000 else "b.w"), base + a + 4 + off


def enc(desde, para, largo):
    """4 bytes de um BL (largo=True) ou de um B.W (largo=False)."""
    off = para - (desde + 4)
    if not -(1 << 24) <= off < (1 << 24):
        raise ValueError(f"0x{desde:08X} -> 0x{para:08X} fora do alcance")
    S = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = 1 - (i1 ^ S), 1 - (i2 ^ S)
    h1 = 0xF000 | (S << 10) | ((off >> 12) & 0x3FF)
    h2 = (0xD000 if largo else 0x9000) | (j1 << 13) | (j2 << 11) \
        | ((off >> 1) & 0x7FF)
    return struct.pack("<HH", h1, h2)


# ---------------------------------------------------------------------------
# o codigo das rotinas
# ---------------------------------------------------------------------------

def monta_codigo():
    """Monta tools/capa_album.s e devolve os bytes do .text."""
    with open(FONTE, "r") as f:
        return monta(f.read())


def confere_codigo(cod):
    """O codigo tem de ter os tres trampolins no lugar e caber no lote.

    Os tres `b.w` do comeco do .text (CRIA, TITULO e APAGA) sao os alvos
    da tabela de entradas; cada um tem de apontar para dentro do lote, e o
    codigo todo tem de caber no espaco que sobra."""
    erros = []
    if len(cod) < 12:
        return ["o codigo tem menos de 12 bytes: nao cabem os tres trampolins"]
    for i, (nome, _alvo) in enumerate(zip(("CRIA", "TITULO", "APAGA"),
                                          ENTRADAS)):
        lido = desvio(cod, 4 * i, XIP + CODIGO)
        if lido is None or lido[0] != "b.w":
            erros.append(f"o trampolim de {nome} (0x{4 * i:X}) nao e um b.w")
        elif not (XIP + CODIGO <= lido[1] < XIP + LOTE + LOTE_TAM):
            erros.append(f"o trampolim de {nome} aponta para 0x{lido[1]:08X}, "
                         f"fora do lote")
    if CODIGO + len(cod) > LOTE + LOTE_TAM:
        erros.append(f"o codigo tem {len(cod)} bytes e nao cabe no lote")
    return erros


def sha_placeholder():
    """O sha256 do quadrado cinza (o modelo aprovado) e o seu tamanho."""
    with open(PLACEHOLDER, "rb") as f:
        quad = f.read()
    return quad, hashlib.sha256(quad).hexdigest()
