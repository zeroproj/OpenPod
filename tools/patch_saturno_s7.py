#!/usr/bin/env python3
"""
patch_saturno_s7.py — SATURNO S7: os ícones das listas viram campo da tabela.

O MANTENEDOR PERGUNTOU: "a tela que mostrava ícones ela ainda continua?"

    Continuava. Nenhum passo do Saturno tinha tocado nos icones.

O QUE ESTAVA ERRADO

    A V039 tirou o icone de UMA tela — a Configurar — apagando a string
    de glifo dela (`0x0013A8BC`). Todas as outras continuaram com o seu.
    Resultado, visivel nas fotos do mantenedor:

        Configurar   sem icone
        Despertador  icone ≡
        Musica       icone ♪
        home         sem icone

    E exatamente o padrao que o Saturno existe para matar: **decisao de
    aparencia tomada tela a tela**.

A MEDICAO

    Varri as chamadas a `lv_obj_set_style_text_font` (0x00D4D12E) e agrupei
    por fonte:

        fonte 0x00CA671C  ->  44 pontos, em 32 telas   <- a de icones
        (as outras fontes sao texto, relogio, etc.)

    Um rotulo cuja fonte e a de icones E um icone. Nao ha ambiguidade.

A CORRECAO

    Campo novo na tabela de tema, em +0x12:

        icones   0 = escondidos (padrao)   1 = visiveis

    Os 44 pontos passam por uma rotina que faz o `set_style_text_font` que
    ja faziam e, se o campo for 0, marca o objeto como **oculto**
    (`LV_OBJ_FLAG_HIDDEN`, bit 0, via `lv_obj_add_flag` 0x00D49204).

    Esconder e melhor que apagar a string: funciona seja qual for o texto
    que a tela ponha depois, e e reversivel mudando 1 byte da tabela.

    O padrao escolhido e **0**, por tres razoes convergentes: a home nao
    tem icone, a Configurar ja nao tinha desde a V039, e o tema de
    referencia NanoClone traz `show icons: off`.

RESSALVA HONESTA — o que este patch NAO resolve

    Esconder o icone NAO reposiciona o texto da linha. Se uma tela reserva
    espaco a esquerda para o icone e outra nao, o recuo do texto continua
    diferente entre elas. **Isso eu nao medi**, e portanto nao afirmo que
    esta resolvido. E questao separada, e menor.

USO
    python3 tools/patch_saturno_s7.py \\
        --in  firmware/WORKING/GN438_openpod_v065.bin \\
        --out firmware/WORKING/GN438_openpod_v066.bin [--dry-run]
    Opcional: --icones 1   (para ligar os icones)

SEGURANCA
    - localiza os pontos pela FONTE carregada, nao por endereco fixo;
    - recusa se algum ponto ja estiver desviado;
    - exige que o byte +0x12 da tabela esteja virgem (0xFF);
    - confere a rotina montada com operandos;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.
"""

import argparse
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
FLASH_SIZE = 0x200000

SET_FONT = 0xD4D12E
ADD_FLAG = 0xD49204
FONTE_ICONES = 0x00CA671C
FLAG_HIDDEN = 1

TAB = 0x00DA5400
TAB_OFF = 0x001A5400
OFS_ICONES = 0x12

BLOB = 0x001A5800
BLOB_MAX = 0x80


def bl(origem, destino, link=True):
    off = destino - (origem + 4)
    if off & 1 or not (-(1 << 24) <= off < (1 << 24)):
        raise ValueError("fora de alcance")
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = ((0xD000 if link else 0x9000)
           | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def monta(base):
    c = bytearray()

    def h(*hw):
        for x in hw:
            c.extend(struct.pack("<H", x))

    def call(alvo):
        c.extend(bl(base + len(c), alvo))

    h(0xB501)                       # push {r0, lr}
    call(SET_FONT)                  # a fonte que a tela ja pedia
    pos_lit = len(c)
    h(0x0000)                       # ldr r1, =TAB  (resolvido abaixo)
    h(0x7C89)                       # ldrb r1, [r1, #0x12]
    h(0x2900)                       # cmp  r1, #0
    h(0xD103)                       # bne  fim
    h(0x9800)                       # ldr  r0, [sp]
    h(0x2100 | FLAG_HIDDEN)         # movs r1, #1
    call(ADD_FLAG)
    h(0xBD01)                       # fim: pop {r0, pc}
    while len(c) % 4:
        h(0xBF00)
    lit = len(c)
    c.extend(struct.pack("<I", TAB))
    pc = (base + pos_lit + 4) & ~3
    struct.pack_into("<H", c, pos_lit, 0x4900 | (((base + lit) - pc) >> 2))
    return bytes(c)


ESPERADO = ["push {r0, lr}", "bl #0xd4d12e", "ldrb r1, [r1, #0x12]",
            "cmp r1, #0", "bne #", "ldr r0, [sp]", "movs r1, #1",
            "bl #0xd49204", "pop {r0, pc}"]


def main():
    ap = argparse.ArgumentParser(description="Saturno S7: icones na tabela")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--icones", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.src == a.dst:
        sys.exit("origem e destino iguais")
    with open(a.src, "rb") as fh:
        orig = fh.read()
    if len(orig) != FLASH_SIZE:
        sys.exit(f"tamanho inesperado: {len(orig)}")
    data = bytearray(orig)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    def ins(x):
        try:
            return next(md.disasm(data[x - XIP:x - XIP + 4], x), None)
        except Exception:
            return None

    # localizar os pontos PELA FONTE carregada, nao por endereco fixo
    sites = []
    for x in range(0xD20000, 0xD40000, 2):
        k = ins(x)
        if not (k and k.mnemonic == "bl" and k.op_str.startswith("#")):
            continue
        if int(k.op_str.strip("#"), 0) != SET_FONT:
            continue
        f = None
        for b in range(x - 12, x, 2):
            j = ins(b)
            if j and j.mnemonic == "ldr" and "r1, [pc" in j.op_str:
                imm = int(j.op_str.split("#")[-1].rstrip("]"), 0)
                f = struct.unpack_from("<I", data,
                                       (((b + 4) & ~3) + imm) - XIP)[0]
        if f == FONTE_ICONES:
            sites.append(x)

    erros = []
    if not sites:
        erros.append("nenhum ponto com a fonte de icones encontrado")
    if data[TAB_OFF + OFS_ICONES] != 0xFF:
        erros.append(f"tabela +0x{OFS_ICONES:02X} nao esta virgem "
                     f"(vale {data[TAB_OFF + OFS_ICONES]})")
    if any(v != 0xFF for v in data[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB:06X} nao esta virgem")

    rot = monta(BLOB + XIP)
    got = [f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(rot, BLOB + XIP)]
    got = [g for g in got if "[pc" not in g][:len(ESPERADO)]
    ok = len(got) == len(ESPERADO) and all(
        g.startswith(e) if e.endswith("#") else g == e
        for g, e in zip(got, ESPERADO))
    if not ok:
        erros.append(f"rotina nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print("  SATURNO S7 — os icones viram campo da tabela")
    print()
    print(f"  fonte de icones 0x{FONTE_ICONES:08X}: {len(sites)} pontos")
    print(f"  campo novo: tabela +0x{OFS_ICONES:02X}  icones = {a.icones}"
          f"   ({'escondidos' if a.icones == 0 else 'visiveis'})")
    print()
    print("  NAO reposiciona o texto da linha — ver o cabecalho.")
    print()
    print("  ALTERACOES")
    data[TAB_OFF + OFS_ICONES] = a.icones
    print(f"    0x{TAB_OFF + OFS_ICONES:06X}  campo icones = {a.icones}")
    data[BLOB:BLOB + len(rot)] = rot
    print(f"    0x{BLOB:06X}  rotina {len(rot)} B")
    for x in sites:
        data[x - XIP:x - XIP + 4] = bl(x, BLOB + XIP)
    print(f"    {len(sites)} ganchos -> a rotina")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X} (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}")
    print("    " + "  ".join(f"0x{s:06X}" for s in secs))
    print("  CRC da FIRM: campo intocado (R1)")
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as fh:
        fh.write(data)
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
