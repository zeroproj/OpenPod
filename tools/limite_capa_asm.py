#!/usr/bin/env python3
"""
limite_capa_asm.py — o layout e as rotinas do limite da capa (ficha 019).

PROPOSITO

    O modulo que o `fab_limite_capa.py` usa para montar e conferir as duas
    rotinas novas da Reload 2.2.1. Ele mora aqui, e nao dentro da
    ferramenta, pela regra do projeto: ate 350 linhas por ferramenta.

    As rotinas sao Thumb-2 montadas pelo clang (tools/asm.py). O
    `carrega_capa` de fabrica ja calcula o tamanho da imagem e as
    dimensoes; a ferramenta so troca os dois pontos por um `bl` para
    estas rotinas, que conferem os limites e devolvem o mesmo resultado
    quando passam.

    Nada aqui escreve no binario: a escrita e da ferramenta.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402
from asm import monta  # noqa: E402

# --- a entrada: a 2.2 exata (sem carimbo), catraca da ficha 018
SHA_22 = "4fdd31c03ad6672ca0b15b141345b7559b2517afca19f54de0d73753f842f769"
TAMANHO = 0x200000

# --- o lote da capa (o MAPA do build.py ja declara o lote da RC7)
LOTE, LOTE_TAM = 0x1A8000, 0x3000
LIVRE_INI, LIVRE_FIM = 0x1AAE82, 0x1AB000

# --- os dois pontos trocados por `bl` (deslocamentos no arquivo)
P_BYTES = 0x1AA882                    # sub.w r0, fp, r5
P_PX = 0x1AA334                       # movs.w fp, #0
ORIG_BYTES = b"\xab\xeb\x05\x00"
ORIG_PX = b"\x5f\xf0\x00\x0b"

# --- onde as rotinas novas moram (dentro da area livre, alinhadas)
R_BYTES = 0x1AAE90
R_PX = 0x1AAEC0

# --- os destinos de falha de fabrica (endereco XIP, sem o bit Thumb)
FALHA_BYTES = 0x00DAA8D6
FALHA_PX = 0x00DAA3C6

# --- os limites (a ficha manda estes valores; o decisor confirmou)
LIMITE_PX = 1000
LIMITE_BYTES = 512 * 1024


def fonte_bytes(limite, falha):
    lo, hi = limite & 0xFFFF, (limite >> 16) & 0xFFFF
    alvo = (falha | 1) & 0xFFFFFFFF
    return f"""
.syntax unified
.thumb
.text
.align 2
limite_bytes:
    sub.w r0, fp, r5
    movw r1, #{lo:#06x}
    movt r1, #{hi:#06x}
    cmp r0, r1
    bhi limite_bytes_falha
    bx lr
limite_bytes_falha:
    movw ip, #{alvo & 0xFFFF:#06x}
    movt ip, #{(alvo >> 16) & 0xFFFF:#06x}
    bx ip
"""


def fonte_px(limite, falha):
    if not 0 <= limite <= 0xFFFF:
        raise ValueError("o limite em pixels tem de caber em movw")
    alvo = (falha | 1) & 0xFFFFFFFF
    lo, hi = alvo & 0xFFFF, (alvo >> 16) & 0xFFFF
    return f"""
.syntax unified
.thumb
.text
.align 2
limite_px:
    movw r2, #{limite:#06x}
    cmp r0, r2
    bhi limite_px_falha
    cmp r1, r2
    bhi limite_px_falha
    movs.w fp, #0
    bx lr
limite_px_falha:
    movw ip, #{lo:#06x}
    movt ip, #{hi:#06x}
    bx ip
"""


def monta_rotinas(limite_px=LIMITE_PX, limite_bytes=LIMITE_BYTES):
    """Monta as duas rotinas e devolve (bytes, px)."""
    return (monta(fonte_bytes(limite_bytes, FALHA_BYTES)),
            monta(fonte_px(limite_px, FALHA_PX)))


def _conferir_com_capstone(cod, base, tipo, limite, falha):
    """Le de volta as instrucoes e confere os desvios e o alvo de falha."""
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB
    except ImportError as e:
        raise RuntimeError("capstone ausente: pip3 install capstone") from e
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    ins = list(md.disasm(cod, base))
    erros = []
    if not ins:
        return ["a rotina nao desmontou"]
    if ins[-1].mnemonic != "bx" or ins[-1].op_str != "ip":
        erros.append("a rotina nao termina com bx ip")
    if len(ins) < 3 or ins[-3].mnemonic != "movw" or ins[-2].mnemonic != "movt":
        erros.append("o alvo de falha nao esta em movw/movt")
    else:
        got = (ins[-3].operands[1].imm & 0xFFFF) | \
              ((ins[-2].operands[1].imm & 0xFFFF) << 16)
        if got != ((falha | 1) & 0xFFFFFFFF):
            erros.append(f"o alvo de falha e 0x{got:08X}, esperado "
                         f"0x{falha | 1:08X}")
    alvo_falha = ins[-3].address if len(ins) >= 3 else None
    for i in ins:
        if i.mnemonic == "bhi":
            if not i.operands or i.operands[0].imm != alvo_falha:
                erros.append(f"o bhi em 0x{i.address:08X} nao vai para a falha")
    if tipo == "bytes":
        if not ins[0].mnemonic.startswith("sub") or "fp, r5" not in ins[0].op_str:
            erros.append("a rotina de bytes nao comeca com sub.w r0, fp, r5")
        if not any(i.mnemonic == "cmp" and i.op_str == "r0, r1" for i in ins):
            erros.append("a rotina de bytes nao compara o tamanho com r1")
    else:
        if ins[0].mnemonic != "movw" or not ins[0].op_str.startswith("r2,"):
            erros.append("a rotina de px nao comeca com movw r2, #limite")
        if not any(i.mnemonic.startswith("movs") and "fp" in i.op_str
                   for i in ins):
            erros.append("a rotina de px nao repoe movs.w fp, #0")
    if not any(i.mnemonic == "bx" and i.op_str == "lr" for i in ins):
        erros.append("a rotina nao tem o caminho de sucesso (bx lr)")
    # o limite montado tem de ser o pedido
    if tipo == "bytes":
        vals = [i.operands[1].imm for i in ins
                if i.mnemonic in ("movw", "movt") and i.op_str.startswith("r1,")]
        got = (vals[0] & 0xFFFF) | ((vals[1] & 0xFFFF) << 16) if len(vals) >= 2 else None
        if got != limite:
            erros.append(f"o limite em bytes montou 0x{got:X}, esperado 0x{limite:X}")
    return erros


def confere_rotinas(cod_bytes, cod_px, limite_px=LIMITE_PX,
                    limite_bytes=LIMITE_BYTES):
    """Confere as duas rotinas montadas (tamanho, desvios e alvos)."""
    erros = []
    if len(cod_bytes) > R_PX - R_BYTES:
        erros.append(f"a rotina de bytes ({len(cod_bytes)} B) passa por cima da de px")
    if R_BYTES + len(cod_bytes) > LIVRE_FIM or R_PX + len(cod_px) > LIVRE_FIM:
        erros.append("as rotinas nao cabem na area livre")
    erros += _conferir_com_capstone(cod_bytes, A.XIP + R_BYTES, "bytes",
                                    limite_bytes, FALHA_BYTES)
    erros += _conferir_com_capstone(cod_px, A.XIP + R_PX, "px",
                                    limite_px, FALHA_PX)
    return erros
