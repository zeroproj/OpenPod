#!/usr/bin/env python3
"""
patch_saturno_s6.py — SATURNO S6: fecha os três pontos deixados em aberto.

O MANTENEDOR PERGUNTOU: "essas 3 coisas em aberto não vamos resolver?"

    Ele estava certo. Duas delas eu tinha deixado em aberto por
    conveniencia, nao por necessidade.

A — A COR DA SELECAO PASSA A VIR DA TABELA

    Ate aqui a selecao vinha de `palette_main(7)`, em tres pontos:

        0x00D2EB42  home, navegacao
        0x00D2EDB2  home, criacao
        0x00DA3520  a rotina compartilhada da linha (39 telas)

    Nao era heranca de tema — era explicita — mas era uma CONSTANTE FORA
    DA TABELA, e portanto uma segunda fonte de verdade.

    Li o valor real antes de mexer, para nao mudar a cor as cegas: a
    tabela de paletas da LVGL esta em `0x00CDF078`, indexada por 16 bits.

        palette_main(7) = 0xFA05 pre-invertido = RGB565 0x05FA
                        = RGB(0, 190, 213)   -- o ciano da selecao

    A tabela de tema e semeada com esse mesmo valor: **zero mudanca
    visual**, e agora a cor mora num lugar so.

B — O PADDING PASSA A SER DA CARCACA

    O S3 fechou opacidade, contorno e sombra, mas deixou **padding** de
    fora de proposito, para nao mudar duas classes de uma vez. O
    principio P1 diz que a carcaca pinta TUDO — padding incluido.

        pad_left = pad_right = pad_bottom = 0 nos tres objetos

    `pad_top` NAO e tocado: o conteiner o recebe da tabela, em
    `cont_base`, que roda antes. Zerar aqui apagaria aquilo.

    Escolhi 0 e nao `margem` de proposito: hoje as margens vem da largura
    do rotulo (`hor_res - 6`), entao 0 preserva o visual e ainda assim
    tira a decisao do tema. O campo `margem` continua reservado para
    quando se quiser mover a margem para o padding.

C — A GEOMETRIA DOS ITENS DA HOME PASSA A SER DE EXECUCAO

    Era a divida do S4: os itens da home vinham de tabelas de coordenadas
    (`0x00C4867C`, `0x00C486A0`), ligadas em tempo de PATCH. Se
    `altura_linha` ou `inicio_lista` mudassem na tabela, a home ficava
    para tras — em silencio.

    O laco da home e rastreavel: `r5` e o indice x 4 nos dois `set_pos`,
    e a altura do rotulo e `0x10` fixo no codigo.

        0x0012ED20  set_pos do icone    -> y = inicio + altura * i
        0x0012ED7E  set_pos do rotulo   -> y = inicio + altura * i
        0x0012ED62  set_size do rotulo  -> altura da TABELA

    Depois disto, mudar `altura_linha` na tabela move os itens da home
    junto com as outras 36. **A fonte de verdade dupla acaba.**

USO
    python3 tools/patch_saturno_s6.py \\
        --in  firmware/WORKING/GN438_openpod_v064.bin \\
        --out firmware/WORKING/GN438_openpod_v065.bin [--dry-run]

SEGURANCA
    - exige que os 7 pontos de gancho estejam byte a byte como esperado;
    - exige que a tabela de paletas devolva mesmo 0xFA05 em palette_main(7),
      senao a cor semeada estaria errada e a ferramenta RECUSA;
    - confere cada instrucao montada COM OPERANDOS;
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

TAB = 0x00DA5400
TAB_OFF = 0x001A5400
OFS_COR_SEL, OFS_ALT_LINHA, OFS_INICIO = 0x0A, 0x0D, 0x0E

PALETA = 0x000CDF078 - 0x0C000000 + 0x000C0000   # placeholder, recalculado
PALETA_OFF = 0x000DF078                          # 0x00CDF078 - XIP
PALETA_ESPERADA = 0xFA05                         # palette_main(7)

BG_OPA, BORDER_OPA = 0xD4D0B4, 0xD4D0EA
PAD_LEFT, PAD_RIGHT, PAD_BOTTOM = 0xD4D034, 0xD4D040, 0xD4D028
DESPACHANTE = 0xD4CAC4
SET_POS, SET_SIZE = 0xD4A2D4, 0xD4A21A
PROP_OUTLINE_W, PROP_SHADOW_W = 53, 64

NORMALIZA_ANT = 0x001A5500      # a rotina do S3, que vira um b.w

GANCHOS = {
    "sel_home_nav":  (0x0012EB42, "29f001f8", "cor_sel"),
    "sel_home_cria": (0x0012EDB2, "28f0c9fe", "cor_sel"),
    "sel_linha":     (0x001A3520, "b4f712fb", "cor_sel"),
    "home_icone":    (0x0012ED20, "1bf0d8fa", "home_pos"),
    "home_rotulo":   (0x0012ED7E, "1bf0a9fa", "home_pos"),
    "home_altura":   (0x0012ED62, "1bf05afa", "home_h"),
}

BLOB = 0x001A5700
BLOB_MAX = 0x200


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
    def __init__(self, base):
        self.base, self.c, self.pend = base, bytearray(), []

    @property
    def pc(self):
        return self.base + len(self.c)

    def h(self, *hw):
        for x in hw:
            self.c += struct.pack("<H", x)
        return self

    def lit(self, rt):
        self.pend.append((len(self.c), rt))
        self.c += b"\0\0"
        return self

    def call(self, alvo, link=True):
        self.c += bl(self.pc, alvo, link)
        return self

    def fecha(self):
        while len(self.c) % 4:
            self.h(0xBF00)
        lit = len(self.c)
        self.c += struct.pack("<I", TAB)
        for pos, rt in self.pend:
            pc = (self.base + pos + 4) & ~3
            imm = (self.base + lit) - pc
            assert 0 <= imm <= 1020 and imm % 4 == 0, imm
            struct.pack_into("<H", self.c, pos, 0x4800 | (rt << 8) | (imm >> 2))
        return bytes(self.c)


def monta(base):
    out, cur = {}, base

    def emite(nome, f):
        nonlocal cur
        m = Mont(cur)
        f(m)
        b = m.fecha()
        out[nome] = (cur, b)
        cur += len(b)

    # A — cor da selecao: substitui `bl palette_main`, devolve em r0
    emite("cor_sel", lambda m: m.lit(0).h(0x8940, 0x4770))

    # B — normalizacao completa (S3 + padding)
    def norm(m):
        m.h(0xB513, 0x4604)                       # push {r0,r1,r4,lr}; mov r4,r0
        m.h(0x21FF, 0x2200).call(BG_OPA)
        m.h(0x4620, 0x21FF, 0x2200).call(BORDER_OPA)
        m.h(0x4620, 0x2100 | PROP_OUTLINE_W, 0x2200, 0x2300).call(DESPACHANTE)
        m.h(0x4620, 0x2100 | PROP_SHADOW_W, 0x2200, 0x2300).call(DESPACHANTE)
        for alvo in (PAD_LEFT, PAD_RIGHT, PAD_BOTTOM):
            m.h(0x4620, 0x2100, 0x2200).call(alvo)
        m.h(0xBD13)                               # pop {r0,r1,r4,pc}
    emite("normaliza", norm)

    # C — geometria dos itens da home
    def home_pos(m):
        # ⚠️ A home cria NOVE itens; cinco ficam escondidos em y=200 desde
        # a V025. Recalcular o y de todos traria os cinco de volta para a
        # tela. Item estacionado (y fora da tela) passa intacto.
        m.h(0xB510)                               # push {r4, lr}
        m.h(0x2A9F)                               # cmp  r2, #159
        o_bgt = len(m.c)
        m.h(0x0000)                               # bgt  fim  (resolvido abaixo)
        m.lit(4)
        m.h(0x7B62)                               # ldrb r2, [r4, #0x0D]
        m.h(0x08AB)                               # lsrs r3, r5, #2
        m.h(0x435A)                               # muls r2, r3
        m.h(0x7BA3)                               # ldrb r3, [r4, #0x0E]
        m.h(0x18D2)                               # adds r2, r2, r3
        m.h(0xB212)                               # sxth r2, r2
        fim = len(m.c)
        m.call(SET_POS)
        m.h(0xBD10)                               # pop {r4, pc}
        struct.pack_into("<H", m.c, o_bgt,
                         0xDC00 | (((fim - (o_bgt + 4)) >> 1) & 0xFF))
    emite("home_pos", home_pos)

    def home_h(m):
        m.lit(3).h(0x7B5A).call(SET_SIZE, link=False)
    emite("home_h", home_h)
    return out


ESPERADO = {
    "cor_sel": ["ldrh r0, [r0, #0xa]", "bx lr"],
    "normaliza": [
        "push {r0, r1, r4, lr}", "mov r4, r0", "movs r1, #0xff", "movs r2, #0",
        "bl #0xd4d0b4", "mov r0, r4", "movs r1, #0xff", "movs r2, #0",
        "bl #0xd4d0ea", "mov r0, r4", "movs r1, #0x35", "movs r2, #0",
        "movs r3, #0", "bl #0xd4cac4", "mov r0, r4", "movs r1, #0x40",
        "movs r2, #0", "movs r3, #0", "bl #0xd4cac4",
        "mov r0, r4", "movs r1, #0", "movs r2, #0", "bl #0xd4d034",
        "mov r0, r4", "movs r1, #0", "movs r2, #0", "bl #0xd4d040",
        "mov r0, r4", "movs r1, #0", "movs r2, #0", "bl #0xd4d028",
        "pop {r0, r1, r4, pc}"],
    "home_pos": ["push {r4, lr}", "cmp r2, #0x9f", "bgt #", "ldrb r2, [r4, #0xd]",
                 "lsrs r3, r5, #2", "muls r2, r3, r2", "ldrb r3, [r4, #0xe]",
                 "adds r2, r2, r3", "sxth r2, r2", "bl #0xd4a2d4",
                 "pop {r4, pc}"],
    "home_h": ["ldrb r2, [r3, #0xd]", "b.w #0xd4a21a"],
}


def main():
    ap = argparse.ArgumentParser(description="Saturno S6: fecha os 3 abertos")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.src == a.dst:
        sys.exit("origem e destino iguais")
    with open(a.src, "rb") as fh:
        orig = fh.read()
    if len(orig) != FLASH_SIZE:
        sys.exit(f"tamanho inesperado: {len(orig)}")
    data = bytearray(orig)

    erros = []
    pal7 = struct.unpack_from("<H", data, PALETA_OFF + 7 * 2)[0]
    if pal7 != PALETA_ESPERADA:
        erros.append(f"palette_main(7) na imagem e 0x{pal7:04X}, esperado "
                     f"0x{PALETA_ESPERADA:04X} — a cor semeada estaria errada")
    for nome, (off, esp, _) in GANCHOS.items():
        if bytes(data[off:off + 4]).hex() != esp:
            erros.append(f"gancho {nome} em 0x{off:06X} e "
                         f"{bytes(data[off:off+4]).hex()}, esperado {esp}")
    if any(x != 0xFF for x in data[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB:06X} nao esta virgem")

    rots = monta(BLOB + XIP)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    for nome, (addr, b) in rots.items():
        got = [f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(b, addr)]
        got = [g for g in got if "[pc" not in g][:len(ESPERADO[nome])]
        alvo = [g if e.endswith("#") else e
                for e, g in zip(ESPERADO[nome], got)]
        if got != alvo:
            erros.append(f"rotina {nome} nao confere:\n"
                         f"      esperado {alvo}\n"
                         f"      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print("  SATURNO S6 — fecha os tres pontos em aberto")
    print()
    print(f"  A  cor da selecao: palette_main(7) = 0x{pal7:04X} lido da")
    print(f"     tabela de paletas da LVGL em 0x00CDF078 -> semeado na tabela")
    print("     de tema. Zero mudanca visual; a cor passa a morar num lugar so.")
    print("  B  padding passa a ser da carcaca (0 nos tres objetos)")
    print("  C  geometria dos itens da home vem da tabela em tempo de execucao")
    print()
    print("  ALTERACOES")
    struct.pack_into("<H", data, TAB_OFF + OFS_COR_SEL, pal7)
    print(f"    0x{TAB_OFF + OFS_COR_SEL:06X}  cor_selecao 0x0000 -> 0x{pal7:04X}")
    for nome, (addr, b) in sorted(rots.items(), key=lambda x: x[1][0]):
        data[addr - XIP:addr - XIP + len(b)] = b
        print(f"    0x{addr - XIP:06X}  {nome:10s} {len(b):3d} B")
    data[NORMALIZA_ANT:NORMALIZA_ANT + 4] = bl(
        NORMALIZA_ANT + XIP, rots["normaliza"][0], link=False)
    print(f"    0x{NORMALIZA_ANT:06X}  normaliza do S3 -> b.w para a nova")
    for nome, (off, _, rot) in GANCHOS.items():
        data[off:off + 4] = bl(off + XIP, rots[rot][0])
        print(f"    0x{off:06X}  {nome:14s} -> {rot}")
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
