#!/usr/bin/env python3
"""
patch_saturno_s9.py — SATURNO S9: as 14 telas que ficaram para tras.

O QUE A AUDITORIA ACHOU

    `tools/audita_chrome.py` confere as telas de LISTA. Mas ha telas que
    tem faixa superior e NAO tem lista — e elas ficaram de fora do escopo
    da 2.0, que so tratou as 36 de lista.

        telas com faixa           50
        telas de lista            36   faixa de 17 px, ligada na tabela
        telas com faixa sem lista 14   faixa de 22 px, CRUA

    As 14: 0x08 0x0D 0x0F 0x11 0x19 0x1F 0x2B 0x2C 0x2D 0x2F 0x31 0x44
           0x4F 0x52
    (seletores de hora, brilho, senha, leitura de e-book, gravacao em curso)

    Resultado visivel: "Definir alarme" com faixa mais gorda que
    "Despertador". E a mesma inconsistencia que o Saturno existe para
    acabar — eu so nao tinha olhado fora das listas.

O QUE FAZ

    Liga a ALTURA da faixa dessas 14 a tabela, pelos mesmos thunks que as
    36 ja usam. Depois disto **as 50 faixas do aparelho sao identicas**.

RESSALVA HONESTA — o que NAO faz

    Nao mexe no conteudo dessas telas. Elas posicionam o que desenham
    supondo 22 px; com a faixa em 17 sobra um vao de 5 px antes do
    conteudo, contra 2 px nas listas.

    Nao corrijo isso porque cada uma das 14 posiciona o seu conteudo de um
    jeito, e mover conteudo sem medir tela a tela e exatamente o atalho
    que este projeto ja pagou caro. **A faixa fica igual; o vao abaixo
    dela, nao.** Fica anotado.

USO
    python3 tools/patch_saturno_s9.py \\
        --in  firmware/WORKING/GN438_openpod_v067.bin \\
        --out firmware/WORKING/GN438_openpod_v068.bin [--dry-run]

SEGURANCA
    - localiza os pontos RASTREANDO o objeto devolvido por 0x00D216F0,
      nao por endereco fixo;
    - so mexe em ponto que ainda esteja cru (nao desviado);
    - confere que o alvo e mesmo set_height ou set_size;
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
THUNK_H, THUNK_SZ = 0x00DA5300, 0x00DA5306
TAB_PAGINAS = 0xD23B38


def bl(origem, destino):
    off = destino - (origem + 4)
    if off & 1 or not (-(1 << 24) <= off < (1 << 24)):
        raise ValueError("fora de alcance")
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = (0xD000 | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11)
           | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def main():
    ap = argparse.ArgumentParser(description="Saturno S9: as 14 que faltavam")
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

    pages = {}
    for n in range(0x53):
        t = TAB_PAGINAS + 2 * data[TAB_PAGINAS - XIP + n]
        k = ins(t)
        if k and k.mnemonic == "bl":
            pages.setdefault(int(k.op_str.strip("#"), 0), n + 1)
    fns = sorted(pages)

    def dono(x):
        o = max([f for f in fns if f <= x], default=None)
        return pages.get(o)

    def rastreia(ini, lim=250):
        obj = {ARM_REG_R0}
        x, out = ini + 4, []
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

    ch = {}
    for x in range(0xD20000, 0xD40000, 2):
        t = alvo(x)
        if t in (CRIA_BARRA, CRIA_CONT, CRIA_LINHA):
            ch.setdefault(t, []).append(x)
    com_faixa = {dono(x) for x in ch[CRIA_BARRA]} - {None}
    com_linha = {dono(x) for x in ch[CRIA_LINHA]} - {None}
    alvos_pg = sorted(com_faixa - com_linha)

    sites = []
    for p in alvos_pg:
        for x in ch[CRIA_BARRA]:
            if dono(x) != p:
                continue
            for pos, t in rastreia(x):
                if t == SET_H:
                    sites.append((p, pos, THUNK_H))
                elif t == SET_SIZE:
                    sites.append((p, pos, THUNK_SZ))

    erros = []
    if not sites:
        erros.append("nenhum ponto cru encontrado — ja aplicado?")
    for p, pos, _ in sites:
        if alvo(pos) in (THUNK_H, THUNK_SZ):
            erros.append(f"0x{pos - XIP:06X} ja esta desviado")
    if erros:
        print("RECUSADO:")
        for e in erros:
            print("   -", e)
        return 1

    print()
    print("  SATURNO S9 — as telas com faixa e sem lista")
    print()
    print(f"  telas com faixa e sem lista: {len(alvos_pg)}")
    print("    " + "  ".join(f"0x{p:02X}" for p in alvos_pg))
    print(f"  pontos de altura a ligar: {len(sites)}")
    print()
    print("  Depois disto as 50 faixas do aparelho sao identicas.")
    print("  O VAO abaixo da faixa continua diferente nessas 14 — ver o")
    print("  cabecalho da ferramenta. Nao e corrigido aqui, de proposito.")
    print()
    print("  ALTERACOES")
    for p, pos, th in sites:
        data[pos - XIP:pos - XIP + 4] = bl(pos, th)
        print(f"    0x{pos - XIP:06X}  pagina 0x{p:02X} -> "
              f"{'faixa_h' if th == THUNK_H else 'faixa_sz'}")
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
