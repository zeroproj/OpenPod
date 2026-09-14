#!/usr/bin/env python3
"""
patch_saturno.py — PROJETO SATURNO, etapas S1 e S2: a tabela de tema.

O QUE E O SATURNO

    Ver `docs/PROJETO_SATURNO.md`. Em uma frase: **toda vez que a carcaca
    nao pinta, o tema da LVGL pinta — e o tema nao e nosso.** Foi essa a
    causa do raio da selecao (2 versoes), do texto cinza (1 versao) e da
    faixa clara vazia.

    S1  tabela de tema na area livre
    S2  as 6 rotinas compartilhadas passam a ler da tabela   <- ESTE PATCH
    S3  os 3 helpers pintam TUDO explicitamente
    S4  page_home_create reescrito sobre os helpers
    S5  a folha de imagem deixa de desenhar a faixa

O QUE JA EXISTIA, E QUE ESTE PATCH APROVEITA

    A versao 2.0 criou **6 rotinas compartilhadas** e **77 ganchos**
    apontando para elas. Eu a chamei de forca bruta; revendo, os ganchos
    sao justamente o mecanismo que neutraliza os overrides por tela. O que
    faltava era a tabela.

    Os enderecos de entrada das 6 rotinas sao PRESERVADOS: cada uma vira
    um `b.w` para a versao nova, dirigida por tabela. Assim os 77 ganchos
    continuam valendo e nao e preciso reescreve-los.

A TABELA  (XIP 0x00DA5400)

    +00 u16  cor de fundo da tela        (reservado, S3)
    +02 u16  cor de fundo da faixa
    +04 u16  cor do separador
    +06 u16  cor do texto
    +08 u16  cor do texto selecionado    (reservado, S3)
    +0A u16  cor da selecao              (reservado, S3)
    +0C u8   altura da faixa
    +0D u8   altura da linha             (reservado, S3)
    +0E u8   inicio da lista
    +0F u8   margem lateral              (reservado, S3)
    +10 u8   raio
    +11 u8   pad do topo do conteiner

    Cores em RGB565 PRE-INVERTIDAS (COLOR_SOURCE.md 9).
    A altura do conteiner nao e campo: e `160 - inicio_da_lista`,
    para que os dois nunca possam divergir.

O TESTE QUE DEFINE "PRONTO"

    Mudar um campo da tabela e ver as telas mudarem juntas. Use
    `--altura-faixa N` para provar isso sem reescrever nada.

USO
    python3 tools/patch_saturno.py \\
        --in  firmware/WORKING/GN438_openpod_v060.bin \\
        --out firmware/WORKING/GN438_openpod_v061.bin [--dry-run]

    Campos ajustaveis na linha de comando (todos opcionais):
        --altura-faixa --inicio-lista --raio --pad-topo
        --cor-faixa --cor-separador --cor-texto     (RGB565, NAO invertido)

DEPENDENCIAS
    Python 3 + capstone

SEGURANCA
    - exige que as 6 rotinas da 2.0 estejam byte a byte como esperado;
    - exige area livre virgem para a tabela e as rotinas novas;
    - desmonta tudo o que monta e confere instrucao por instrucao;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.

LIMITACOES
    S1+S2 so. As cores de selecao e de texto selecionado ficam na tabela
    mas ainda nao sao lidas — quem as le e o S3.
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

SET_H, SET_SIZE, ALIGN = 0xD4A1EA, 0xD4A21A, 0xD4A3A2
RADIUS, PAD_TOP_W, BORDER_COLOR = 0xD4D064, 0xD4D01C, 0xD4D0C8

# As 6 entradas criadas pela 2.0. Os 77 ganchos apontam para ca.
ENTRADAS = {
    "faixa_h":   (0x001A5300, bytes.fromhex("1121" "a4f772bf")),
    "faixa_sz":  (0x001A5306, bytes.fromhex("1122" "a4f787bf")),
    "cont_h":    (0x001A530C, bytes.fromhex("8d21" "a4f76cbf")),
    "cont_al":   (0x001A5312, bytes.fromhex("1323" "a5f745b8")),
    "tema_bg":   (0x001A5318, bytes.fromhex("48f20820" "7047")),
    "borda":     (0x001A5344, bytes.fromhex("4cf23171" "a7f7bebe")),
}
CONT_BASE = 0x001A531E          # a 7a rotina, maior; tambem vira b.w

TAB_OFF = 0x001A5400
NOVO_OFF = 0x001A5420
LIVRE_MAX = 0x200

# valores de fabrica da tabela — os mesmos que a 2.0 tinha como imediatos
PADRAO = dict(cor_tela=0x0000, cor_faixa=0x0882, cor_separador=0x31C7,
              cor_texto=0xFFFF, cor_texto_sel=0xFFFF, cor_selecao=0x0000,
              altura_faixa=17, altura_linha=16, inicio_lista=19,
              margem=3, raio=0, pad_topo=1)


def inv(v):
    """RGB565 -> pre-invertido (LV_COLOR_16_SWAP)."""
    return ((v >> 8) | (v << 8)) & 0xFFFF


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


class Mont:
    """Montador minimo: emite Thumb-2 e resolve o literal da tabela."""

    def __init__(self, base, tab_addr):
        self.base, self.tab, self.c = base, tab_addr, bytearray()

    @property
    def pc(self):
        return self.base + len(self.c)

    def h(self, *hw):
        for x in hw:
            self.c += struct.pack("<H", x)
        return self

    def ldr_tab(self, rt):
        """ldr rT, =TAB — o literal fica no fim, alinhado."""
        self.pend = getattr(self, "pend", [])
        self.pend.append((len(self.c), rt))
        self.c += b"\0\0"
        return self

    def bw(self, alvo, link=False):
        self.c += bl(self.pc, alvo, link)
        return self

    def fecha(self):
        while len(self.c) % 4:
            self.h(0xBF00)
        lit = len(self.c)
        self.c += struct.pack("<I", self.tab)
        for pos, rt in getattr(self, "pend", []):
            pc = (self.base + pos + 4) & ~3
            imm = (self.base + lit) - pc
            assert 0 <= imm <= 1020 and imm % 4 == 0, imm
            struct.pack_into("<H", self.c, pos, 0x4800 | (rt << 8) | (imm >> 2))
        return bytes(self.c)


def monta_rotinas(base, tab):
    """Devolve {nome: (endereco, bytes)} — cada rotina e independente."""
    out, cur = {}, base
    def emite(nome, f):
        nonlocal cur
        m = Mont(cur, tab)
        f(m)
        b = m.fecha()
        out[nome] = (cur, b)
        cur += len(b)

    # altura da faixa -> r1 (set_height)
    emite("faixa_h", lambda m: m.ldr_tab(1).h(0x7B09).bw(SET_H))
    # altura da faixa -> r2 (set_size)
    emite("faixa_sz", lambda m: m.ldr_tab(2).h(0x7B12).bw(SET_SIZE))
    # altura do conteiner = 160 - inicio_lista  -> r1
    emite("cont_h", lambda m: m.ldr_tab(1).h(0x7B89, 0xF1C1, 0x01A0).bw(SET_H))
    # inicio da lista -> r3 (align y_ofs)
    emite("cont_al", lambda m: m.ldr_tab(3).h(0x7B9B).bw(ALIGN))
    # cor de fundo da faixa -> r0, e retorna
    emite("tema_bg", lambda m: m.ldr_tab(0).h(0x8840, 0x4770))
    # cor do separador -> r1 (border_color)
    emite("borda", lambda m: m.ldr_tab(1).h(0x8889).bw(BORDER_COLOR))

    def base_cont(m):
        m.h(0xB530)                       # push {r4, r5, lr}
        m.h(0x4604)                       # mov  r4, r0
        m.ldr_tab(5)
        m.h(0x2200)                       # movs r2, #0
        m.h(0x7C29)                       # ldrb r1, [r5, #0x10]  raio
        m.bw(RADIUS, link=True)
        m.h(0x4620, 0x2200)               # mov r0,r4 ; movs r2,#0
        m.h(0x7C69)                       # ldrb r1, [r5, #0x11]  pad
        m.bw(PAD_TOP_W, link=True)
        m.h(0x4620)                       # mov r0, r4
        m.h(0x7BA9, 0xF1C1, 0x01A0)       # ldrb r1,[r5,#0x0E] ; rsb r1,r1,#160
        m.bw(SET_H, link=True)
        m.h(0x4620, 0x2102, 0x2200)       # mov r0,r4 ; movs r1,#2 ; movs r2,#0
        m.h(0x7BAB)                       # ldrb r3, [r5, #0x0E]
        m.bw(ALIGN, link=True)
        m.h(0xBD30)                       # pop  {r4, r5, pc}
    emite("cont_base", base_cont)
    return out


# Conferencia por INSTRUCAO COMPLETA, nao so mnemonico. A primeira versao
# comparava so o mnemonico e deixou passar `ldrb r1,[r0,#4]` no lugar de
# `ldrb r1,[r1,#0xc]` -- registrador e deslocamento errados, mnemonico certo.
ESPERADO = {
    "faixa_h":  ["ldrb r1, [r1, #0xc]", "b.w #0xd4a1ea"],
    "faixa_sz": ["ldrb r2, [r2, #0xc]", "b.w #0xd4a21a"],
    "cont_h":   ["ldrb r1, [r1, #0xe]", "rsb.w r1, r1, #0xa0", "b.w #0xd4a1ea"],
    "cont_al":  ["ldrb r3, [r3, #0xe]", "b.w #0xd4a3a2"],
    "tema_bg":  ["ldrh r0, [r0, #2]", "bx lr"],
    "borda":    ["ldrh r1, [r1, #4]", "b.w #0xd4d0c8"],
    "cont_base": ["push {r4, r5, lr}", "mov r4, r0", "movs r2, #0",
                  "ldrb r1, [r5, #0x10]", "bl #0xd4d064",
                  "mov r0, r4", "movs r2, #0", "ldrb r1, [r5, #0x11]",
                  "bl #0xd4d01c", "mov r0, r4", "ldrb r1, [r5, #0xe]",
                  "rsb.w r1, r1, #0xa0", "bl #0xd4a1ea", "mov r0, r4",
                  "movs r1, #2", "movs r2, #0", "ldrb r3, [r5, #0xe]",
                  "bl #0xd4a3a2", "pop {r4, r5, pc}"],
}


def main():
    ap = argparse.ArgumentParser(description="Saturno S1+S2: tabela de tema")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    for k in ("altura-faixa", "inicio-lista", "raio", "pad-topo",
              "altura-linha", "margem"):
        ap.add_argument("--" + k, type=int)
    for k in ("cor-faixa", "cor-separador", "cor-texto", "cor-tela",
              "cor-selecao", "cor-texto-sel"):
        ap.add_argument("--" + k, type=lambda x: int(x, 0))
    a = ap.parse_args()
    if a.src == a.dst:
        sys.exit("origem e destino iguais")
    with open(a.src, "rb") as fh:
        orig = fh.read()
    if len(orig) != FLASH_SIZE:
        sys.exit(f"tamanho inesperado: {len(orig)}")
    data = bytearray(orig)

    v = dict(PADRAO)
    for k in list(v):
        got = getattr(a, k, None)
        if got is not None:
            v[k] = got

    erros = []
    for nome, (off, esperado) in ENTRADAS.items():
        if bytes(data[off:off + len(esperado)]) != esperado:
            erros.append(f"{nome} em 0x{off:06X} nao esta como a 2.0 deixou "
                         f"({bytes(data[off:off+len(esperado)]).hex()})")
    if any(x != 0xFF for x in data[TAB_OFF:TAB_OFF + LIVRE_MAX]):
        erros.append(f"area livre 0x{TAB_OFF:06X} nao esta virgem")

    tab_addr = TAB_OFF + XIP
    rots = monta_rotinas(NOVO_OFF + XIP, tab_addr)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    for nome, (addr, b) in rots.items():
        # o `ldr rX,=TAB` sai do montador com o literal so no fim; conferimos
        # tudo menos ele, com operando incluido
        got = [f"{i.mnemonic} {i.op_str}".strip()
               for i in md.disasm(b, addr) if not i.op_str.startswith(("r0, [pc", "r1, [pc", "r2, [pc", "r3, [pc", "r5, [pc"))]
        got = got[:len(ESPERADO[nome])]
        if got != ESPERADO[nome]:
            erros.append(f"rotina {nome} nao confere:\n"
                         f"      esperado {ESPERADO[nome]}\n"
                         f"      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    tabela = struct.pack(
        "<6H6B", inv(v["cor_tela"]), inv(v["cor_faixa"]),
        inv(v["cor_separador"]), inv(v["cor_texto"]),
        inv(v["cor_texto_sel"]), inv(v["cor_selecao"]),
        v["altura_faixa"], v["altura_linha"], v["inicio_lista"],
        v["margem"], v["raio"], v["pad_topo"])

    print()
    print("  PROJETO SATURNO — S1 tabela + S2 rotinas dirigidas por tabela")
    print()
    print(f"  tabela em 0x{TAB_OFF:06X} (XIP 0x{tab_addr:08X}), "
          f"{len(tabela)} bytes")
    for k in ("cor_tela", "cor_faixa", "cor_separador", "cor_texto",
              "cor_texto_sel", "cor_selecao"):
        print(f"    {k:16s} 0x{v[k]:04X}  (gravado pre-invertido "
              f"0x{inv(v[k]):04X})")
    for k in ("altura_faixa", "altura_linha", "inicio_lista", "margem",
              "raio", "pad_topo"):
        print(f"    {k:16s} {v[k]}")
    print(f"    altura_conteiner  {160 - v['inicio_lista']}  "
          "(derivada: 160 - inicio_lista)")
    print()
    print("  ALTERACOES")
    data[TAB_OFF:TAB_OFF + len(tabela)] = tabela
    total = 0
    for nome, (addr, b) in sorted(rots.items(), key=lambda x: x[1][0]):
        data[addr - XIP:addr - XIP + len(b)] = b
        total += len(b)
    print(f"    0x{NOVO_OFF:06X}  {total} B de rotinas novas")
    for nome, (off, _) in ENTRADAS.items():
        data[off:off + 4] = bl(off + XIP, rots[nome][0], link=False)
    data[CONT_BASE:CONT_BASE + 4] = bl(CONT_BASE + XIP, rots["cont_base"][0],
                                       link=False)
    print(f"    7 entradas da 2.0 viram `b.w` para as novas "
          "(os 77 ganchos continuam valendo)")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X} (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}  "
          + "  ".join(f"0x{s:06X}" for s in secs))
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
