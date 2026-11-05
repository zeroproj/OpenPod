#!/usr/bin/env python3
"""
diag_trava_asm.py — o layout do lote e o scanner das chamadas externas, para
as imagens de bissecao da ficha 008 e os degraus B1 e B2 da ficha 010 (o bug
do ring e o monitor do watchdog, na fabrica).

PROPOSITO

    O modulo que o `fab_diag_trava.py` usa: ele sabe o LAYOUT do lote
    (0x001A8000..0x001AB000: a tabela das entradas e onde o codigo
    comeca), o SCANNER do Thumb-2 que acha o par `movw/movt` que carrega
    um endereco e o `blx` que o usa (as chamadas para fora do codigo da
    RC7 sao todas assim: o montador nao tem linkador), o SCANNER dos `bl`
    INTERNOS do lote e a assinatura do `carrega_capa` (a rotina que o
    nivel B corta), o PATCH de cada nivel (onde ele e, quantos bytes sao,
    o que fica no lugar e a conferencia lida de volta) e os alvos que
    ficam FORA do lote, no codigo da FABRICA (o `b` do ring cheio e o
    `bpl` do monitor do watchdog).
    O leitor e o encoder do `b.w` vem do `capa_album_asm.py` (o mesmo par
    que o `tests/test_rc7.py` usa).

DEPENDENCIAS

    Python 3 (stdlib) + o `tools/capa_album_asm.py`.

LIMITACOES

    - o layout e FIXO: e o layout do lote que a RC7 montou;
    - nada aqui escreve no binario: a escrita e da ferramenta.
"""

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402

# o layout (o mesmo lote da RC7 — o codigo ja esta montado)
XIP, LOTE, LOTE_TAM = A.XIP, A.LOTE, A.LOTE_TAM
TABELA, CODIGO, ENTRADAS = A.TABELA, A.CODIGO, A.ENTRADAS

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
FALHA_ZERO = b"\x00\x20"     # movs r0, #0 (o get_path devolve 0 = falha)

# ---------------------------------------------------------------------------
# Os niveis que mexem NO CODIGO DA FABRICA (fora do lote da RC7):
#
#   b1  o `b` do caminho "ring cheio" do envio a view (0x00CF83E4): com o
#       ring cheio, ele PULA o give do mutex (0x00CF842E) e devolve 0 com
#       o mutex 0x81BBCC preso. O B1 aponta o `b` para o give.
#   b2  o `bpl` do monitor do watchdog (0x00D46B30): se alguma tarefa
#       registrada nao bateu, o monitor salta para 0x00D46B68 ("-task %d is
#       dead") e RETORNA sem alimentar o watchdog. O B2 troca o branch por
#       `nop`: o watchdog e sempre alimentado.
#
# ---------------------------------------------------------------------------
FORA_LOTE = {
    "b1": {"off": 0x00F843A, "orig": b"\xfa\xe7", "novo": b"\xf7\xe7",
           "antes": 0x00CF8432, "depois": 0x00CF842C,
           "extra": (0x00F842C, b"\x04\x48\x15\xf7\x9e\xf3",
                     "o give do mutex (ldr r0,[pc,#0x10] + bl 0x80DB6E)")},
    "b2": {"off": 0x146B30, "orig": b"\x1a\xd5", "novo": b"\x00\xbf",
           "antes": 0x00D46B68, "depois": None},
}

# o `carrega_capa` (nivel B): a UNICA rotina do lote que guarda nove
# registradores e tem `sub sp,#12` no prologo (as outras seis, `sub sp,#4`).
# O nivel B corta o `bl` interno que a chama.
PROLOGO_CARREGA_CAPA = (0xE92D, 0x4FF0, 0xB083)   # push {r4-r11,lr}; sub sp,#12

# nivel: o que o degrau mede
NIVEL = {
    "a": "TITULO so faz o set_text",
    "b": "A + get_path, sem arquivo",
    "c": "B + f_open/f_close",
    "b0": "TITULO ligado, get_path cortado (cinza)",
    "b1": "B + o bug do ring corrigido (o mutex e solto)",
    "b2": "B + o monitor do watchdog neutralizado (sem watchdog)",
}

# o texto do patch de cada nivel (a conferencia de saida da ferramenta)
DESCRICAO = {
    "a": f"a entrada TITULO vira b.w 0x{SET_TEXT:08X} (o lv_label_set_text)",
    "b": "o bl do carrega_capa vira movs r0, #0 + nop (o TITULO para depois "
         "do get_path)",
    "c": "o blx da chamada vira movs r0, #1 (a chamada falha)",
    "b0": "o blx do get_path vira movs r0, #0 (o get_path 'falha': o "
          "caminho guardado fica vazio e o quadrado cinza aparece)",
    "b1": "o `b` do ring cheio vira b 0x00CF842C (o caminho 'cheio' passa "
          "pelo give do mutex)",
    "b2": "o `bpl` do monitor vira nop (o watchdog e sempre alimentado)",
}
# a premissa ja conferida, no texto da ferramenta
PREMISSA = {
    "a": "a entrada TITULO ainda e o TITULO_impl (nao patcheada)",
    "b": "o carrega_capa (prologo unico) e o bl que o chama: 1x",
    "c": f"a chamada a 0x{JD_PREP:08X} aparece 1x no lote",
    "b0": f"a chamada ao get_path (0x{GET_PATH:08X}) aparece 1x no lote",
    "b1": "o `b` do ring cheio (0x0F843A) ainda e o da fabrica "
          "(b 0x00CF8432) e o give esta no lugar",
    "b2": "o `bpl` do monitor (0x146B30) ainda e o da fabrica "
          "(bpl 0x00D46B68)",
}


def sha_esperado(nivel):
    """O sha256 da entrada que a ferramenta consome neste nivel."""
    return SHA_DIAG_B if nivel in FORA_LOTE else SHA_RC7


# Thumb-2: o par movw/movt que carrega um endereco, e o blx que o usa

def imm16(h1, h2):
    """O imm16 de um MOVW (T3) ou de um MOVT (T1)."""
    return (((h1 & 0xF) << 12) | (((h1 >> 10) & 1) << 11)
            | (((h2 >> 12) & 0x7) << 8) | (h2 & 0xFF))  # noqa: E501


def e_mov(h1, h2, esp):
    """A meia-palavra dupla e um MOVW (esp=0xF240) ou um MOVT (0xF2C0)?"""
    return (h1 & 0xFBF0) == esp and (h2 & 0x8000) == 0


def e_blx(h):
    """A meia-palavra e um BLX (registro)? (0x4780 | Rm<<3)"""
    return (h & 0xFF80) == 0x4780


def alvo_b16(d, off):
    """O alvo de um branch de 16 bits (T1) no deslocamento `off`.

    Aceita o `b` incondicional (0xE000) e o condicional (0xD000, o `bpl`
    do monitor do watchdog). Devolve None se nao for um branch T1."""
    h = struct.unpack_from("<H", d, off)[0]
    if (h & 0xF000) == 0xD000:          # condicional: 1101 cond imm8
        imm = h & 0xFF
        if imm & 0x80:
            imm -= 0x100
    elif (h & 0xF800) == 0xE000:        # incondicional: 11100 imm11
        imm = h & 0x7FF
        if imm & 0x400:
            imm -= 0x800
    else:
        return None
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

    Devolve o deslocamento do BLX (o par + 8), ou None."""
    pares = acha_pares(d, valor)
    if len(pares) != 1:
        return None
    off = pares[0] + 8
    h = struct.unpack_from("<H", d, off)[0]
    _, h2 = struct.unpack_from("<HH", d, pares[0])
    if not e_blx(h) or ((h >> 3) & 0xF) != ((h2 >> 8) & 0xF):
        return None
    return off


# os `bl` internos do lote (o nivel B)

def acha_carrega_capa(d):
    """Os deslocamentos do prologo do `carrega_capa` (tem de ser 1).

    A assinatura e `push {r4-r11,lr}` + `sub sp,#12`."""
    achados = []
    for i in range(CODIGO, fim_do_codigo(d) - 6, 2):
        if struct.unpack_from("<HHH", d, i) == PROLOGO_CARREGA_CAPA:
            achados.append(i)
    return achados


def acha_bl_para(d, alvo):
    """Os deslocamentos dos `bl` INTERNOS cujo alvo (XIP) e `alvo`.

    O alvo e decodificado do binario (o `desvio` do `capa_album_asm.py`)."""
    achados = []
    for i in range(CODIGO, fim_do_codigo(d) - 4, 2):
        lido = A.desvio(d, i)
        if lido is not None and lido[0] == "bl" and lido[1] == alvo:
            achados.append(i)
    return achados


def acha_bytes(d, alvo):
    """Os deslocamentos onde `alvo` (bytes) aparece no codigo do lote.

    Serve para dizer "ja esta patcheado" quando o `bl` do `carrega_capa`
    ja virou `movs r0, #0` + `nop`."""
    achados = []
    for i in range(CODIGO, fim_do_codigo(d) - len(alvo), 2):
        if bytes(d[i:i + len(alvo)]) == alvo:
            achados.append(i)
    return achados


# os niveis que mexem no codigo da FABRICA (fora do lote): o B1 (o `b` do
# ring cheio) e o B2 (o `bpl` do monitor do watchdog)

def premissa_fora(d, nivel):
    """As premissas dos niveis que mexem no codigo da FABRICA.

    Devolve a lista de erros (vazia = a entrada e a imagem exata do nivel)."""
    f = FORA_LOTE[nivel]
    off, orig, novo = f["off"], f["orig"], f["novo"]
    erros = []
    if bytes(d[off:off + 2]) == novo:
        return [f"o patch em 0x{off:06X} ja esta aplicado"]
    if bytes(d[off:off + 2]) != orig:
        return [f"em 0x{off:06X} nao esta o codigo da fabrica "
                f"({orig.hex(' ')})"]
    alvo = alvo_b16(d, off)
    if alvo != f["antes"]:
        erros.append(f"o branch em 0x{off:06X} decodifica para 0x{alvo:08X}, "
                     f"esperado 0x{f['antes']:08X} — o codigo da fabrica mudou")
    if "extra" in f:
        eoff, ebytes, enome = f["extra"]
        if bytes(d[eoff:eoff + len(ebytes)]) != ebytes:
            erros.append(f"{enome} nao e o da fabrica")
    return erros


def byte_permitido(nivel, i):
    """O byte `i` pode mudar neste nivel?"""
    if nivel in FORA_LOTE:
        off = FORA_LOTE[nivel]["off"]
        return off <= i < off + 2
    return LOTE <= i < LOTE + LOTE_TAM


# o patch de cada nivel: onde ele e, quantos bytes, e o que fica no lugar

def bytes_do_patch(d, nivel):
    """(deslocamento, tamanho, bytes novos) do patch do nivel.

    Devolve (None, 0, b"") quando o alvo nao e encontrado."""
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
    if nivel in FORA_LOTE:
        # o patch no codigo da FABRICA: o `b` do ring cheio (b1) ou o
        # `bpl` do monitor do watchdog (b2). 2 bytes, e nada mais.
        f = FORA_LOTE[nivel]
        return f["off"], 2, f["novo"]
    if achado_unico(d, JD_PREP) is None:
        return None, 0, b""
    return achado_unico(d, JD_PREP), 2, FALHA


def confere_patch(d, nivel, off, tam, novos):
    """Rele o patch e confere: os bytes novos e a decodificacao deles."""
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
    elif nivel in FORA_LOTE:
        depois = FORA_LOTE[nivel]["depois"]
        if depois is None:                 # o branch virou um nop
            h = struct.unpack_from("<H", d, off)[0]
            if h != 0xBF00:
                erros.append("os 2 bytes novos nao decodificam como nop")
        else:
            alvo = alvo_b16(d, off)
            if alvo != depois:
                erros.append(f"o branch novo nao decodifica para "
                             f"0x{depois:08X}")
    else:

        h = struct.unpack_from("<H", d, off)[0]
        if (h & 0xF800) != 0x2000 or ((h >> 8) & 0x7) != 0:
            erros.append("os 2 bytes novos nao decodificam como movs r0, #1")
    return erros
