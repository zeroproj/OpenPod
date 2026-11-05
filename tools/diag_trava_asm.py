#!/usr/bin/env python3
"""
diag_trava_asm.py — o layout do lote e o scanner das chamadas externas, para
as imagens de bissecao da ficha 008 e o degrau B1 da ficha 010 (o bug do
ring da fabrica).

PROPOSITO

    O modulo que o `fab_diag_trava.py` usa: ele sabe o LAYOUT do lote
    (0x001A8000..0x001AB000: a tabela das entradas e onde o codigo
    comeca), o SCANNER do Thumb-2 que acha o par `movw/movt` que carrega
    um endereco e o `blx` que o usa (as chamadas para fora do codigo da
    RC7 sao todas assim: o montador nao tem linkador), o SCANNER dos `bl`
    INTERNOS do lote e a assinatura do `carrega_capa` (a rotina que o
    nivel B corta), o PATCH de cada nivel (onde ele e, quantos bytes sao,
    o que fica no lugar e a conferencia lida de volta) e o BUG DO RING DA
    FABRICA (o nivel B1: o `b` de 16 bits do caminho "ring cheio", que
    fica FORA do lote, no codigo da fabrica).

    O leitor e o encoder do `b.w` vem do `capa_album_asm.py` (o mesmo par
    que o `tests/test_rc7.py` usa).

DEPENDENCIAS

    Python 3 (stdlib) + o `tools/capa_album_asm.py`.

LIMITACOES

    - o layout e FIXO: e o layout do lote que a RC7 montou;
    - o scanner le meia-palavras de 2 em 2 (o codigo do lote e Thumb-2 com
      os instrucoes em endereco par, o montador garante);
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
# a entrada do nivel B1: o Diag B exato (a RC7 + o nivel B), que e o que o
# B1 consome — a receita monta um a partir do outro.
SHA_DIAG_B = ("952c79fb3e6a4d2bdd2ae477060795ce8ea7e88c8523384bb62e468"
              "234844896")

# os alvos dos niveis
SET_TEXT = 0x00D5ED94        # o lv_label_set_text da fabrica (nivel A)
JD_PREP = 0x00D10B21         # jd_prepare | Thumb (nivel C)
GET_PATH = 0x00CFEFC5        # pstr_audio_get_path | Thumb (nivel B0)
FALHA = b"\x01\x20"          # movs r0, #1 (a chamada externa "falhada")
FALHA_BL = b"\x00\x20\x00\xBF"   # movs r0, #0 + nop (o bl interno, cortado)
FALHA_ZERO = b"\x00\x20"     # movs r0, #0 (a chamada externa "falhada" de
                            # verdade: o get_path devolve 0 = falha)

# ---------------------------------------------------------------------------
# O BUG DO RING DA FABRICA (nivel B1, ficha 010)
#
# O envio ao ring da view (`0x00CF83E4`) pega o mutex `0x81BBCC` (take em
# `0x00CF83FA`, `bl 0x80DB48`) e, quando o ring esta CHEIO (`blo 0x00CF8408`
# -> `0x00CF8438`, `movs r4,#0`), salta para `0x00CF843A` — um `b 0x00CF8432`
# que PULA o give do mutex (`0x00CF842E`, `bl 0x80DB6E`): o mutex fica preso
# e toda a tarefa que manda mensagem para a view trava.
#
# O B1 troca esse `b` por `b 0x00CF842C`: o caminho "cheio" passa pelo give
# e devolve 0 (a mensagem e descartada, o mutex e solto). Sao 2 bytes, no
# codigo da FABRICA (fora do lote da RC7).
# ---------------------------------------------------------------------------
RING_OFF = 0x00F843A          # o deslocamento no arquivo (XIP 0x00CF843A)
RING_BYTES_ORIG = b"\xfa\xe7"  # b 0x00CF8432 (o bug: sem o give)
RING_BYTES_NOVO = b"\xf7\xe7"  # b 0x00CF842C (com o give)
RING_ALVO_ANTES = 0x00CF8432  # o alvo do `b` na fabrica (o bug)
RING_ALVO_DEPOIS = 0x00CF842C  # o alvo novo (o give)
GIVE_OFF = 0x00F842C          # ldr r0,[pc,#0x10] + bl 0x80DB6E (o give)
GIVE_BYTES = b"\x04\x48\x15\xf7\x9e\xf3"   # o give da fabrica, byte a byte

# o `carrega_capa` (nivel B): a UNICA rotina do lote que guarda nove
# registradores e tem `sub sp,#12` no prologo — as outras seis usam
# `sub sp,#4`. O nivel B corta o `bl` interno que a chama.
PROLOGO_CARREGA_CAPA = (0xE92D, 0x4FF0, 0xB083)   # push {r4-r11,lr}; sub sp,#12

# nivel: o que o degrau mede
NIVEL = {
    "a": "TITULO so faz o set_text",
    "b": "A + get_path, sem arquivo",
    "c": "B + f_open/f_close",
    "b0": "TITULO ligado, get_path cortado (cinza)",
    "b1": "B + o bug do ring corrigido (o mutex e solto)",
}

# o texto do patch de cada nivel (a conferencia de saida da ferramenta)
DESCRICAO = {
    "a": f"a entrada TITULO vira b.w 0x{SET_TEXT:08X} (o lv_label_set_text)",
    "b": "o bl do carrega_capa vira movs r0, #0 + nop (o TITULO para depois "
         "do get_path)",
    "c": "o blx da chamada vira movs r0, #1 (a chamada falha)",
    "b0": "o blx do get_path vira movs r0, #0 (o get_path 'falha': o "
          "caminho guardado fica vazio e o quadrado cinza aparece)",
    "b1": f"o `b` do ring cheio vira b 0x{RING_ALVO_DEPOIS:08X} (o caminho "
          f"'cheio' passa pelo give do mutex)",
}
# a premissa ja conferida, no texto da ferramenta
PREMISSA = {
    "a": "a entrada TITULO ainda e o TITULO_impl (nao patcheada)",
    "b": "o carrega_capa (prologo unico) e o bl que o chama: 1x",
    "c": f"a chamada a 0x{JD_PREP:08X} aparece 1x no lote",
    "b0": f"a chamada ao get_path (0x{GET_PATH:08X}) aparece 1x no lote",
    "b1": f"o `b` do ring cheio (0x{RING_OFF:06X}) ainda e o da fabrica "
          f"(b 0x{RING_ALVO_ANTES:08X}) e o give esta no lugar",
}


def sha_esperado(nivel):
    """O sha256 da entrada que a ferramenta consome neste nivel."""
    return SHA_DIAG_B if nivel == "b1" else SHA_RC7


# Thumb-2: o par movw/movt que carrega um endereco, e o blx que o usa

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


def alvo_b16(d, off):
    """O alvo de um `b` de 16 bits (T1) no deslocamento `off`; None se nao for."""
    h = struct.unpack_from("<H", d, off)[0]
    if (h & 0xF800) != 0xE000:
        return None
    imm = h & 0x7FF
    if imm & 0x400:
        imm -= 0x800
    return XIP + off + 4 + 2 * imm


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
    proprio binario (o `desvio` do `capa_album_asm.py`)."""
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
# o nivel B1: o bug do ring da fabrica (FORA do lote, no codigo da fabrica)
# ---------------------------------------------------------------------------

def premissa_b1(d):
    """As premissas do nivel B1: o `b` do ring cheio e o give do mutex.

    Devolve a lista de erros (vazia = a entrada e a imagem exata do nivel)."""
    erros = []
    if bytes(d[RING_OFF:RING_OFF + 2]) == RING_BYTES_NOVO:
        erros.append(f"o `b` do ring ja esta patcheado "
                     f"(b 0x{RING_ALVO_DEPOIS:08X})")
        return erros
    if bytes(d[RING_OFF:RING_OFF + 2]) != RING_BYTES_ORIG:
        erros.append(f"em 0x{RING_OFF:06X} nao esta o `b` da fabrica "
                     f"({RING_BYTES_ORIG.hex(' ')})")
        return erros
    alvo = alvo_b16(d, RING_OFF)
    if alvo != RING_ALVO_ANTES:
        erros.append(f"o `b` em 0x{RING_OFF:06X} decodifica para "
                     f"0x{alvo:08X}, esperado 0x{RING_ALVO_ANTES:08X} "
                     f"— o codigo da fabrica mudou")
    if bytes(d[GIVE_OFF:GIVE_OFF + len(GIVE_BYTES)]) != GIVE_BYTES:
        erros.append(f"o give do mutex (0x{GIVE_OFF:06X}..) nao e o da "
                     f"fabrica (ldr r0,[pc,#0x10] + bl 0x80DB6E)")
    return erros


def byte_permitido(nivel, i):
    """O byte `i` pode mudar neste nivel?"""
    if nivel == "b1":
        return RING_OFF <= i < RING_OFF + 2
    return LOTE <= i < LOTE + LOTE_TAM


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
        # falha" e o TITULO cai no caminho que ja existe (o quadrado cinza).
        off = achado_unico(d, GET_PATH)
        if off is None:
            return None, 0, b""
        return off, 2, FALHA_ZERO
    if nivel == "b1":
        # o `b` do caminho "ring cheio": ele pula o give do mutex. O B1
        # aponta para o give (0xCF842C), e a mensagem e descartada (0).
        return RING_OFF, 2, RING_BYTES_NOVO
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
    elif nivel == "b1":
        alvo = alvo_b16(d, off)
        if alvo != RING_ALVO_DEPOIS:
            erros.append(f"o `b` novo nao decodifica para "
                         f"0x{RING_ALVO_DEPOIS:08X} (o give do mutex)")
    else:

        h = struct.unpack_from("<H", d, off)[0]
        if (h & 0xF800) != 0x2000 or ((h >> 8) & 0x7) != 0:
            erros.append("os 2 bytes novos nao decodificam como movs r0, #1")
    return erros
