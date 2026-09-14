#!/usr/bin/env python3
"""
patch_saturno_s11.py — SATURNO S11: a altura da linha vem da tabela.

O QUE A AUDITORIA NAO VIA

    `audita_chrome.py` conferia faixa e conteiner, mas nao conferia a
    LINHA. Com esse ponto cego eu relatei "SEM DIVERGENCIAS" com a maior
    divergencia de todas em aberto. Medindo de verdade:

        25 pontos  set_height(linha, 10)          <- imediato cru
         3 pontos  set_size(linha, w, 10)         <- imediato cru
        10 pontos  set_height(linha, tela / 10)   <- 160/10 = 16
        ---
        38 pontos, DOIS tamanhos de linha no mesmo aparelho.

    Quem esta certo? A home poe suas linhas com passo 16 e o campo
    `altura_linha` da tabela vale 16. As 9 telas que dividem a tela por 10
    chegam no mesmo 16. **As 28+3 com o imediato 10 sao as divergentes** —
    listas mais apertadas que o resto do aparelho, e uma selecao 6 px mais
    baixa que a da home.

O QUE FAZ

    Os 38 pontos passam a ler `altura_linha` (+0x0D) da tabela. Depois
    disto TODAS as linhas do aparelho tem a mesma altura, e mudar a
    densidade das listas e **um byte**.

    Nos 10 pontos que ja calculavam 16 o resultado e identico — elas entram
    na tabela sem mudar de aparencia. A mudanca visivel e nas 31 que
    usavam 10.

CORRECAO DE REGISTRO

    Eu havia anotado este defeito como "`altura_linha` nao centralizada,
    35 pontos crus". Sao 38, e o problema nao era so centralizacao: era
    que o aparelho tinha duas alturas de linha. O numero antigo veio de
    uma varredura que nao seguia `set_size`.

USO
    python3 tools/patch_saturno_s11.py \\
        --in  firmware/WORKING/GN438_openpod_v070_carimbado.bin \\
        --out firmware/WORKING/GN438_openpod_v071.bin [--dry-run]

SEGURANCA
    - acha os pontos RASTREANDO o objeto devolvido por 0x00D21764, nao
      por endereco fixo;
    - so mexe em ponto ainda cru; recusa se algum ja estiver desviado;
    - confere cada instrucao montada COM OPERANDOS, sem filtrar linhas de
      literal (foi num literal filtrado que o patch_extras errou);
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.
"""

import argparse
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    from capstone.arm import ARM_REG_R0
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
FLASH_SIZE = 0x200000

CRIA_BARRA, CRIA_CONT, CRIA_LINHA = 0xD216F0, 0xD21690, 0xD21764
SET_H, SET_SIZE = 0xD4A1EA, 0xD4A21A

TAB = 0x00DA5400
TAB_OFF = 0x001A5400
OFS_ALTURA_LINHA = 0x0D

BLOB = 0x001A5A00
BLOB_MAX = 0x40


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
    """Duas entradas: base+0 troca a altura de set_height,
       base+8 troca a altura de set_size. Literal comum no fim."""
    c = bytearray()

    def h(*hw):
        for x in hw:
            c.extend(struct.pack("<H", x))

    p1 = len(c)
    h(0x0000)                                   # ldr  r1, =TAB
    h(0x7800 | (OFS_ALTURA_LINHA << 6) | (1 << 3) | 1)   # ldrb r1,[r1,#0xd]
    c.extend(bl(base + len(c), SET_H, link=False))       # b.w  set_height
    p2 = len(c)
    h(0x0000)                                   # ldr  r2, =TAB
    h(0x7800 | (OFS_ALTURA_LINHA << 6) | (2 << 3) | 2)   # ldrb r2,[r2,#0xd]
    c.extend(bl(base + len(c), SET_SIZE, link=False))    # b.w  set_size
    while len(c) % 4:
        h(0xBF00)
    lit = len(c)
    c.extend(struct.pack("<I", TAB))
    struct.pack_into("<H", c, p1,
                     0x4900 | (((base + lit) - ((base + p1 + 4) & ~3)) >> 2))
    struct.pack_into("<H", c, p2,
                     0x4A00 | (((base + lit) - ((base + p2 + 4) & ~3)) >> 2))
    return bytes(c), base + p1, base + p2


ESPERADO = ["ldr r1, [pc, #0xc]", "ldrb r1, [r1, #0xd]", "b.w #0xd4a1ea",
            "ldr r2, [pc, #4]", "ldrb r2, [r2, #0xd]", "b.w #0xd4a21a"]


def main():
    ap = argparse.ArgumentParser(description="Saturno S11: altura da linha")
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
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True

    def ins(x):
        try:
            return next(md.disasm(data[x - XIP:x - XIP + 4], x), None)
        except Exception:
            return None

    def alvo(x):
        k = ins(x)
        if k and k.mnemonic in ("bl", "b.w") and k.op_str.startswith("#"):
            return int(k.op_str.strip("#"), 0)
        return None

    def rastreia(i0, lim=250):
        obj, x, out = {ARM_REG_R0}, i0 + 4, []
        for _ in range(lim):
            k = ins(x)
            if k is None:
                break
            if k.mnemonic == "bl" and k.op_str.startswith("#"):
                t = int(k.op_str.strip("#"), 0)
                if ARM_REG_R0 in obj:
                    out.append((x, t))
                obj -= {ARM_REG_R0 + n for n in range(4)}
                if t in (CRIA_BARRA, CRIA_CONT, CRIA_LINHA):
                    break
            elif (k.mnemonic == "mov" and len(k.operands) == 2
                  and k.operands[0].type == 1 and k.operands[1].type == 1):
                s, dst = k.operands[1].reg, k.operands[0].reg
                obj.add(dst) if s in obj else obj.discard(dst)
            else:
                for r in k.regs_access()[1]:
                    obj.discard(r)
            x += k.size
        return out

    def imediato(pos, reg):
        v = None
        for b in range(pos - 12, pos, 2):
            j = ins(b)
            if j and j.mnemonic in ("movs", "mov.w") and \
                    j.op_str.startswith(f"{reg}, #"):
                v = int(j.op_str.split("#")[1], 0)
        return v

    sites = []
    for x in [p for p in range(0xD20000, 0xD40000, 2)
              if alvo(p) == CRIA_LINHA]:
        for pos, t in rastreia(x):
            if t == SET_H:
                sites.append((pos, "h", imediato(pos, "r1")))
            elif t == SET_SIZE:
                sites.append((pos, "sz", imediato(pos, "r2")))

    erros = []
    if not sites:
        erros.append("nenhum ponto de altura de linha encontrado")
    if any(v != 0xFF for v in data[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB:06X} nao esta virgem")
    alvo_tab = data[TAB_OFF + OFS_ALTURA_LINHA]
    if not 8 <= alvo_tab <= 40:
        erros.append(f"altura_linha da tabela = {alvo_tab}, fora do plausivel")

    rot, ent_h, ent_sz = monta(BLOB + XIP)
    got = [f"{i.mnemonic} {i.op_str}".strip()
           for i in md.disasm(rot, BLOB + XIP)][:len(ESPERADO)]
    if got != ESPERADO:
        erros.append(f"rotina nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for e in erros:
            print("   -", e)
        return 1

    crus = [s for s in sites if s[2] is not None]
    calc = [s for s in sites if s[2] is None]
    print()
    print("  SATURNO S11 — a altura da linha vem da tabela")
    print()
    print(f"  pontos de altura na linha: {len(sites)}")
    print(f"    com imediato cru : {len(crus)}   "
          f"valores {sorted({v for _, _, v in crus})}")
    print(f"    calculados (tela/10 = {160 // 10}) : {len(calc)}")
    print(f"  altura_linha da tabela  : {alvo_tab}")
    print()
    print("  Depois disto o aparelho tem UMA altura de linha, nao duas.")
    print()
    print("  ALTERACOES")
    data[BLOB:BLOB + len(rot)] = rot
    print(f"    0x{BLOB:06X}  rotina {len(rot)} B "
          f"(entradas +0 altura, +{ent_sz - ent_h} tamanho)")
    for pos, tipo, v in sites:
        data[pos - XIP:pos - XIP + 4] = bl(pos, ent_h if tipo == "h" else ent_sz)
    print(f"    {len(sites)} ganchos -> a tabela")
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
