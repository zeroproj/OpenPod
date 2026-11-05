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
      - o SCANNER dos `bl` INTERNOS do lote (o montador resolve o
        deslocamento) e a assinatura do `carrega_capa`, a rotina que o
        nivel B corta;
      - o PATCH de cada nivel: onde ele e, quantos bytes sao e o que fica
        no lugar (`movs r0, #1` — a chamada externa "falhada" — ou
        `movs r0, #0` + `nop` — o `bl` interno, cortado) e a conferencia
        desses bytes lidos de volta.

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
JD_PREP = 0x00D10B21         # jd_prepare | Thumb (nivel C)
GET_PATH = 0x00CFEFC5        # pstr_audio_get_path | Thumb (nivel B0)
FALHA = b"\x01\x20"          # movs r0, #1 (a chamada externa "falhada")
FALHA_BL = b"\x00\x20\x00\xBF"   # movs r0, #0 + nop (o bl interno, cortado)
FALHA_ZERO = b"\x00\x20"     # movs r0, #0 (a chamada externa "falhada" de
                            # verdade: o get_path devolve 0 = falha)

# o `carrega_capa` (nivel B): a UNICA rotina do lote que guarda nove
# registradores e tem `sub sp,#12` no prologo — as outras seis (CRIA,
# TITULO, APAGA, comparou_caminho, copia_caminho e o leitor) usam
# `sub sp,#4`. O TITULO o chama com um `bl` interno de 4 bytes; e esse
# `bl` que o nivel B corta: o `cmp r0,#0; beq fim_titulo` que ja existe
# logo depois dele termina o TITULO (depois do get_path, da comparacao,
# do caminho guardado e do quadrado cinza) — sem calloc, sem free e sem
# arquivo.
PROLOGO_CARREGA_CAPA = (0xE92D, 0x4FF0, 0xB083)   # push {r4-r11,lr}; sub sp,#12

# nivel: o que o degrau mede
NIVEL = {
    "a": "TITULO so faz o set_text",
    "b": "A + get_path, sem arquivo",
    "c": "B + f_open/f_close",
    "b0": "TITULO ligado, get_path cortado (cinza)",
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


# ---------------------------------------------------------------------------
# os `bl` internos do lote (o nivel B)
# ---------------------------------------------------------------------------

def acha_carrega_capa(d):
    """Os deslocamentos do prologo do `carrega_capa` (tem de ser 1).

    A assinatura e `push {r4-r11,lr}` + `sub sp,#12`: as outras seis
    rotinas do lote que guardam nove registradores usam `sub sp,#4`."""
    achados = []
    for i in range(CODIGO, fim_do_codigo(d) - 6, 2):
        if struct.unpack_from("<HHH", d, i) == PROLOGO_CARREGA_CAPA:
            achados.append(i)
    return achados


def acha_bl_para(d, alvo):
    """Os deslocamentos dos `bl` INTERNOS cujo alvo (XIP) e `alvo`.

    O `bl` interno e um Thumb-2 de 4 bytes (T1); o alvo e decodificado do
    proprio binario (o mesmo leitor do `b.w`, o `desvio` do
    `capa_album_asm.py`)."""
    achados = []
    for i in range(CODIGO, fim_do_codigo(d) - 4, 2):
        lido = A.desvio(d, i)
        if lido is not None and lido[0] == "bl" and lido[1] == alvo:
            achados.append(i)
    return achados


def acha_bytes(d, alvo):
    """Os deslocamentos onde `alvo` (bytes) aparece no codigo do lote.

    Serve para dizer "ja esta patcheado" quando o `bl` do `carrega_capa`
    ja virou `movs r0, #0` + `nop` (e o branch sumiu do codigo)."""
    achados = []
    for i in range(CODIGO, fim_do_codigo(d) - len(alvo), 2):
        if bytes(d[i:i + len(alvo)]) == alvo:
            achados.append(i)
    return achados


# ---------------------------------------------------------------------------
# o patch de cada nivel: onde ele e, quantos bytes, e o que fica no lugar
# ---------------------------------------------------------------------------

def bytes_do_patch(d, nivel):
    """(deslocamento, tamanho, bytes novos) do patch do nivel.

    Devolve (None, 0, b"") quando o alvo nao e encontrado — quem decide
    (a ferramenta) e o que recusar."""
    if nivel == "a":
        return TABELA + 4, 4, A.enc(XIP + TABELA + 4, SET_TEXT, False)
    if nivel == "b":
        prologo = acha_carrega_capa(d)
        if len(prologo) != 1:
            return None, 0, b""
        bls = acha_bl_para(d, prologo[0] + XIP)
        if len(bls) != 1:
            return None, 0, b""
        return bls[0], 4, FALHA_BL
    if nivel == "b0":
        # a chamada ao get_path: o par movw/movt que carrega o endereco e o
        # blx que a usa. O blx vira `movs r0, #0`: o get_path "devolve
        # falha", e o TITULO cai no caminho que ja existe (o caminho
        # guardado fica vazio e o quadrado cinza aparece).
        off = achado_unico(d, GET_PATH)
        if off is None:
            return None, 0, b""
        return off, 2, FALHA_ZERO
    if achado_unico(d, JD_PREP) is None:
        return None, 0, b""
    return achado_unico(d, JD_PREP), 2, FALHA


def confere_patch(d, nivel, off, tam, novos):
    """Rele o patch e confere: os bytes novos e a decodificacao deles.

    O `b.w` do nivel A e lido de volta (o alvo tem de ser o
    lv_label_set_text da fabrica); os bytes do nivel B tem de decodificar
    como `movs r0, #0` + `nop`; os do nivel C como `movs r0, #1`."""
    erros = []
    if bytes(d[off:off + tam]) != novos:
        erros.append(f"os {tam} bytes do patch nao ficaram como o esperado")
        return erros
    if nivel == "a":
        lido = A.desvio(d, off)
        if lido is None or lido[0] != "b.w" or lido[1] != SET_TEXT:
            erros.append(f"a entrada TITULO nao ficou um b.w para "
                         f"0x{SET_TEXT:08X}")
    elif nivel == "b":
        h1 = struct.unpack_from("<H", d, off)[0]
        h2 = struct.unpack_from("<H", d, off + 2)[0]
        if (h1 & 0xF800) != 0x2000 or ((h1 >> 8) & 0x7) != 0 or (h1 & 0xFF):
            erros.append("os 2 primeiros bytes nao decodificam como movs r0, #0")
        if h2 != 0xBF00:
            erros.append("os 2 ultimos bytes nao decodificam como nop")
    elif nivel == "b0":
        h = struct.unpack_from("<H", d, off)[0]
        if (h & 0xF800) != 0x2000 or ((h >> 8) & 0x7) != 0 or (h & 0xFF):
            erros.append("os 2 bytes novos nao decodificam como movs r0, #0")
    else:

        h = struct.unpack_from("<H", d, off)[0]
        if (h & 0xF800) != 0x2000 or ((h >> 8) & 0x7) != 0:
            erros.append("os 2 bytes novos nao decodificam como movs r0, #1")
    return erros
