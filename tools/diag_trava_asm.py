#!/usr/bin/env python3
"""
diag_trava_asm.py — o layout do lote e o scanner das chamadas externas, para
as imagens de bissecao da ficha 008 (a RC7 trava ao tocar).

PROPOSITO

    O modulo que o `fab_diag_trava.py` usa para achar, no codigo JA
    MONTADO do lote 0x001A8000..0x001AB000, a chamada externa que cada
    nivel de bissecao desliga. Ele mora aqui (e nao dentro da
    ferramenta) por causa da regra do projeto: uma ferramenta nova tem no
    maximo 350 linhas (D06).

    O que este modulo sabe:

      - o LAYOUT do lote (a tabela das entradas, onde o codigo comeca);
      - o SCANNER do Thumb-2 que acha o par `movw/movt` que carrega um
        endereco (com o bit do Thumb) e o `blx` que o usa — as chamadas
        para fora do codigo da RC7 sao todas assim (o montador nao tem
        linkador, entao o endereco vai em `movw/movt` e a chamada e um
        `blx` para o registrador);
      - os alvos de cada nivel (o f_open e o jd_prepare) e o codigo que
        substitui a chamada: `movs r0, #1` (a chamada "falhada").

    O leitor e o encoder do `b.w` vem do `capa_album_asm.py` (o mesmo par
    que o `tests/test_rc7.py` usa).

DEPENDENCIAS

    Python 3 (stdlib) + o `tools/capa_album_asm.py`.

LIMITACOES

    - o layout e FIXO: e o layout do lote que a RC7 montou;
    - o scanner le meia-palavras de 2 em 2: o codigo do lote e Thumb-2
      com os instrucoes comecando em endereco par (o montador garante);
    - nada aqui escreve no binario: a escrita e da ferramenta.
"""

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402

# o layout (o mesmo lote da RC7 — o codigo ja esta montado)
XIP = A.XIP
LOTE, LOTE_TAM = A.LOTE, A.LOTE_TAM
TABELA = A.TABELA
CODIGO = A.CODIGO
ENTRADAS = A.ENTRADAS

# a entrada: a RC7 exata (catraca, aprovada em 2026-10-31)
SHA_RC7 = ("3af97713c9d8e28c2b36b872fd5883d18af9e65bff443c5e99ab6456"
           "78237d9e")

# os alvos dos niveis
SET_TEXT = 0x00D5ED94        # o lv_label_set_text da fabrica (nivel A)
F_OPEN = 0x00D777CD          # f_open | Thumb (nivel B)
JD_PREP = 0x00D10B21         # jd_prepare | Thumb (nivel C)
FALHA = b"\x01\x20"          # movs r0, #1 (a chamada "falhada")

# nivel: (o que o degrau mede, o alvo da chamada a desligar)
NIVEL = {
    "a": ("TITULO so faz o set_text", None),
    "b": ("A + get_path, sem arquivo", F_OPEN),
    "c": ("B + f_open/f_close", JD_PREP),
}


# ---------------------------------------------------------------------------
# Thumb-2: o par movw/movt que carrega um endereco, e o blx que o usa
# ---------------------------------------------------------------------------

def imm16(h1, h2):
    """O imm16 de um MOVW (T3) ou de um MOVT (T1)."""
    return (((h1 & 0xF) << 12) | (((h1 >> 10) & 1) << 11)
            | (((h2 >> 12) & 0x7) << 8) | (h2 & 0xFF))


def e_mov(h1, h2, esp):
    """A meia-palavra dupla e um MOVW (esp=0xF240) ou um MOVT (0xF2C0)?"""
    return (h1 & 0xFBF0) == esp and (h2 & 0x8000) == 0


def e_blx(h):
    """A meia-palavra e um BLX (registro)? (0x4780 | Rm<<3)"""
    return (h & 0xFF80) == 0x4780


def fim_do_codigo(d):
    """O fim do codigo do lote: o byte depois do ultimo que nao e 0xFF."""
    f = LOTE + LOTE_TAM - 1
    while f >= CODIGO and d[f] == 0xFF:
        f -= 1
    return f + 1


def acha_pares(d, valor):
    """Os deslocamentos dos pares `movw/movt` que carregam `valor`.

    `valor` e o endereco COM o bit do Thumb (o que o blx recebe)."""
    achados = []
    for i in range(CODIGO, fim_do_codigo(d) - 8, 2):
        h1, h2 = struct.unpack_from("<HH", d, i)
        if not e_mov(h1, h2, 0xF240):
            continue
        n1, n2 = struct.unpack_from("<HH", d, i + 4)
        if not e_mov(n1, n2, 0xF2C0):
            continue
        if ((h2 >> 8) & 0xF) != ((n2 >> 8) & 0xF):
            continue
        if (imm16(n1, n2) << 16) | imm16(h1, h2) != valor:
            continue
        achados.append(i)
    return achados


def achado_unico(d, valor):
    """O (ou None) achado do par `movw/movt` que carrega `valor`.

    Devolve o deslocamento do BLX (o par + 8) se o par aparecer uma vez
    so e o `blx` estiver no lugar; None caso contrario."""
    pares = acha_pares(d, valor)
    if len(pares) != 1:
        return None
    off = pares[0] + 8
    h = struct.unpack_from("<H", d, off)[0]
    _, h2 = struct.unpack_from("<HH", d, pares[0])
    if not e_blx(h) or ((h >> 3) & 0xF) != ((h2 >> 8) & 0xF):
        return None
    return off
