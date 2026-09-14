#!/usr/bin/env python3
"""
patch_saturno_s3.py — SATURNO S3: a carcaça pinta tudo, explicitamente.

O PRINCIPIO (docs/PROJETO_SATURNO.md, P1)

    Toda vez que a carcaca nao pinta, o tema da LVGL pinta — e o tema nao
    e nosso. Foi essa a causa do raio da selecao (2 versoes), do texto
    cinza (1 versao) e, por eliminacao, da faixa clara vazia.

    O S3 fecha a porta: os tres helpers passam a setar tambem as
    propriedades que ninguem setava.

O QUE FALTAVA — auditado nos tres helpers do binario

    propriedade        FAIXA  CONTEINER  LINHA
    BG_OPA      (33)    nao      nao      nao
    BORDER_OPA  (49)    nao      nao      nao
    OUTLINE_W   (53)    nao      nao      nao
    SHADOW_W    (64)    nao      nao      nao

    Contorno e sombra sao justamente o que aparece como faixa clara onde
    nao se pediu nada: o tema padrao da LVGL poe contorno no estado
    focado e sombra nos "cards".

UMA VARIAVEL DE CADA VEZ

    Este patch mexe SO nessas quatro. NAO mexe em padding, que e layout.
    Se a faixa clara morrer, foi tema; se sobreviver, NAO e heranca de
    tema e o proximo passo investiga outra coisa — e saberemos qual, em
    vez de mudar tudo junto e nao aprender nada.

COMO E APLICADO

    Uma rotina `normaliza(obj)` na area livre, chamada dos tres helpers.
    Os ganchos NAO duplicam logica: cada um chama a rotina que ja existia
    e acrescenta a normalizacao.

        0x00D21716  bl RADIUS          -> faixa_base   (raio da TABELA + normaliza)
        0x00D216CC  bl cont_base       -> cont_novo    (cont_base + normaliza)
        0x00D217AA  bl cor_texto       -> linha_novo   (cor_texto + normaliza)

    `OUTLINE_WIDTH` e `SHADOW_WIDTH` nao tem casca no firmware (o linker
    descartou as que o codigo nao usava), entao vao pelo despachante
    comum `0x00D4CAC4(obj, prop, valor, seletor)` — o mesmo caminho que o
    raio usa desde a correcao do `fix_raio_selecao.py`.

USO
    python3 tools/patch_saturno_s3.py \\
        --in  firmware/WORKING/GN438_openpod_v061.bin \\
        --out firmware/WORKING/GN438_openpod_v062.bin [--dry-run]

DEPENDENCIAS
    Python 3 + capstone

SEGURANCA
    - exige que os tres pontos de gancho estejam como o S1/S2 deixou;
    - exige area livre virgem;
    - confere cada instrucao montada COM OPERANDOS (o S2 quase passou um
      `ldrb r1,[r0,#4]` porque so comparava mnemonico);
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

BG_OPA, BORDER_OPA, RADIUS = 0xD4D0B4, 0xD4D0EA, 0xD4D064
DESPACHANTE = 0xD4CAC4
PROP_OUTLINE_W, PROP_SHADOW_W = 53, 64

TAB = 0x00DA5400                 # tabela de tema do S1
CONT_BASE_ANT = 0x00DA531E       # rotina do conteiner (S1/S2)
COR_TEXTO_ANT = 0x00DA5200       # rotina da linha (1.9)

GANCHOS = {
    "faixa":  (0x00121716, bytes.fromhex("2bf0a5fc")),   # bl 0xd4d064
    "cont":   (0x001216CC, bytes.fromhex("83f027fe")),   # bl 0xda531e
    "linha":  (0x001217AA, bytes.fromhex("83f029fd")),   # bl 0xda5200
}

BLOB = 0x001A5500
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

    def lit(self, rt, valor):
        self.pend.append((len(self.c), rt, valor))
        self.c += b"\0\0"
        return self

    def call(self, alvo, link=True):
        self.c += bl(self.pc, alvo, link)
        return self

    def fecha(self):
        while len(self.c) % 4:
            self.h(0xBF00)
        base_lit = len(self.c)
        vals = []
        for pos, rt, v in self.pend:
            if v not in vals:
                vals.append(v)
        for v in vals:
            self.c += struct.pack("<I", v)
        for pos, rt, v in self.pend:
            alvo = self.base + base_lit + vals.index(v) * 4
            pc = (self.base + pos + 4) & ~3
            imm = alvo - pc
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

    def normaliza(m):
        m.h(0xB513)                       # push {r0, r1, r4, lr}
        m.h(0x4604)                       # mov  r4, r0
        m.h(0x21FF, 0x2200).call(BG_OPA)          # bg_opa = 255
        m.h(0x4620, 0x21FF, 0x2200).call(BORDER_OPA)
        m.h(0x4620, 0x2100 | PROP_OUTLINE_W, 0x2200, 0x2300).call(DESPACHANTE)
        m.h(0x4620, 0x2100 | PROP_SHADOW_W, 0x2200, 0x2300).call(DESPACHANTE)
        m.h(0xBD13)                       # pop  {r0, r1, r4, pc}
    emite("normaliza", normaliza)
    norm = out["normaliza"][0]

    def faixa(m):
        m.h(0xB501)                       # push {r0, lr}
        m.lit(1, TAB).h(0x7C09, 0x2200)   # ldrb r1,[r1,#0x10] (raio) ; r2=0
        m.call(RADIUS)
        m.h(0x9800).call(norm)            # ldr r0,[sp] ; bl normaliza
        m.h(0xBD01)                       # pop  {r0, pc}
    emite("faixa", faixa)

    def encadeia(antigo):
        def f(m):
            m.h(0xB501)                   # push {r0, lr}
            m.call(antigo)                # a rotina que ja existia
            m.h(0x9800).call(norm)
            m.h(0xBD01)
        return f
    emite("cont", encadeia(CONT_BASE_ANT))
    emite("linha", encadeia(COR_TEXTO_ANT))
    return out


ESPERADO = {
    "normaliza": [
        "push {r0, r1, r4, lr}", "mov r4, r0", "movs r1, #0xff", "movs r2, #0",
        "bl #0xd4d0b4", "mov r0, r4", "movs r1, #0xff", "movs r2, #0",
        "bl #0xd4d0ea", "mov r0, r4", "movs r1, #0x35", "movs r2, #0",
        "movs r3, #0", "bl #0xd4cac4", "mov r0, r4", "movs r1, #0x40",
        "movs r2, #0", "movs r3, #0", "bl #0xd4cac4", "pop {r0, r1, r4, pc}"],
    "faixa": ["push {r0, lr}", "ldrb r1, [r1, #0x10]", "movs r2, #0",
              "bl #0xd4d064", "ldr r0, [sp]", "bl", "pop {r0, pc}"],
    "cont": ["push {r0, lr}", "bl #0xda531e", "ldr r0, [sp]", "bl",
             "pop {r0, pc}"],
    "linha": ["push {r0, lr}", "bl #0xda5200", "ldr r0, [sp]", "bl",
              "pop {r0, pc}"],
}


def main():
    ap = argparse.ArgumentParser(description="Saturno S3: pintar tudo")
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
    for nome, (off, esperado) in GANCHOS.items():
        if bytes(data[off:off + 4]) != esperado:
            erros.append(f"gancho {nome} em 0x{off:06X} e "
                         f"{bytes(data[off:off+4]).hex()}, "
                         f"esperado {esperado.hex()}")
    if any(x != 0xFF for x in data[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB:06X} nao esta virgem")

    rots = monta(BLOB + XIP)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    for nome, (addr, b) in rots.items():
        got = [f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(b, addr)]
        got = [g for g in got if "[pc" not in g][:len(ESPERADO[nome])]
        alvo = [e if not e == "bl" else g
                for e, g in zip(ESPERADO[nome], got)]
        if got != alvo:
            erros.append(f"rotina {nome} nao confere:\n"
                         f"      esperado {alvo}\n      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print("  SATURNO S3 — a carcaça pinta tudo")
    print()
    print("  propriedades que NINGUEM setava, e que o tema decidia:")
    print("    BG_OPA(33)=255   BORDER_OPA(49)=255   "
          "OUTLINE_WIDTH(53)=0   SHADOW_WIDTH(64)=0")
    print("  aplicadas a FAIXA, CONTEINER e LINHA")
    print()
    print("  NAO mexe em padding — uma variavel de cada vez.")
    print()
    print("  ALTERACOES")
    total = 0
    for nome, (addr, b) in sorted(rots.items(), key=lambda x: x[1][0]):
        data[addr - XIP:addr - XIP + len(b)] = b
        total += len(b)
        print(f"    0x{addr - XIP:06X}  {nome:10s} {len(b):3d} B")
    for nome in ("faixa", "cont", "linha"):
        off = GANCHOS[nome][0]
        data[off:off + 4] = bl(off + XIP, rots[nome][0])
        print(f"    0x{off:06X}  gancho -> {nome}")
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
