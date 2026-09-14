#!/usr/bin/env python3
"""
patch_chrome_padrao.py — O chrome da home, aplicado a TODAS as telas de lista.

POR QUE ESTA FERRAMENTA EXISTE

    Pedido do mantenedor em 2026-09-14, depois de ver a 1.9:

        "eu quero um padrao de design, tudo tem que parecer com a home (...)
         o projeto rockbox faz isso e precisamos desse padrao, senao vai
         ficar sempre tudo aleatorio"

    Ele esta certo, e a critica e de metodo. As versoes 1.6 a 1.9 foram
    ajustes tela a tela, cada um correto isolado e o conjunto incoerente.

A REGUA — a home, medida pixel a pixel na folha 0x000CE15C

    y  0.. 4   RGB( 20, 22, 26)      y 16       RGB(52,56,62)  SEPARADOR
    y  5.. 9   RGB( 14, 16, 19)      y 17..18   preto          respiro
    y 10..15   RGB(  9, 10, 12)      y 19..     lista

O QUE ESTAVA ERRADO, MEDIDO

    A faixa das subtelas e um objeto LVGL de altura `160 / divisor`, e o
    divisor e uma constante POR TELA:

        divisor  7 -> 22 px : 50 telas      divisor 10 -> 16 px : 1 tela
        divisor  8 -> 20 px :  1 tela       home                  16 px

    51 das 52 divergem da home. Nao e descuido: e a mesma constante errada
    espalhada por 52 funcoes.

    ATENCAO -- NAO se corrige trocando o divisor. Ele tambem alimenta o
    espacador inferior (`160 - 7*altura`), que iria de 6 px para 48 px e
    cobriria a lista. O patch "obvio" quebraria as 51.

AS TRES FORMAS QUE O FIRMWARE USA

    Foi preciso rastrear o objeto pelos registradores, porque as telas nao
    usam a mesma sequencia de chamadas:

        faixa       set_height(0xD4A1EA)  ou  set_size(0xD4A21A)
        conteiner   set_height + set_align BOTTOM_MID (0xD4A39C)   28 telas
                    set_height + lv_obj_align TOP_MID (0xD4A3A2)    8 telas

    Nos dois casos o topo da lista da em `160/divisor`. A regra abaixo vale
    para as duas.

A REGRA APLICADA

    faixa       altura  17   (16 de banda + 1 de separador)
    faixa       fundo   RGB(14,16,19), separador RGB(52,56,62)
    conteiner   altura  141  ->  com BOTTOM_MID, topo em 160-141 = 19
    conteiner   y_ofs   19   ->  onde ha align explicito
    conteiner   pad_top  1   ->  a linha 0 (em `16*i - 1`) cai em 19

    Resultado, identico a home:  faixa 0..15 | separador 16 | respiro
    17..18 | lista 19.

    A faixa vira cor SOLIDA no tom do meio, nao degrade de tres faixas.
    Entre RGB(20,22,26) e RGB(9,10,12) a diferenca e imperceptivel neste
    LCD. Simplificacao assumida, nao descuido.

USO
    python3 tools/patch_chrome_padrao.py \\
        --in  firmware/WORKING/GN438_openpod_v059.bin \\
        --out firmware/WORKING/GN438_openpod_v060.bin [--dry-run]

DEPENDENCIAS
    Python 3 + capstone

SEGURANCA
    - RECUSA TUDO se uma unica tela de lista nao tiver os pontos
      localizados. Aplicar em parte das telas seria repetir o remendo que
      esta ferramenta existe para acabar;
    - confere as propriedades dos wrappers de cor na imagem;
    - desmonta cada rotina montada e confere instrucao por instrucao;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.

LIMITACOES
    - Cor: as cores sao pre-invertidas (LV_COLOR_16_SWAP, COLOR_SOURCE 9).
      Se essa regra estiver errada, as cores saem trocadas -- visivel na
      hora e reversivel.
    - Nao mexe nas telas que tem faixa mas nao tem lista (seletores de
      hora, leitura de e-book). Elas continuam com faixa de 22 px.
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
SET_SIZE, SET_H, ALIGN = 0xD4A21A, 0xD4A1EA, 0xD4A3A2
BG_COLOR, BORDER_COLOR = 0xD4D092, 0xD4D0C8
TEMA_BG = 0xD2138A                      # getter de cor de fundo do tema
TAB_PAGINAS = 0xD23B38

ALTURA_FAIXA = 17
ALTURA_CONT = 141
Y_CONT = 19
PAD_TOP = 1

COR_FUNDO = 0x8208      # RGB(14,16,19) = 0x0882, pre-invertido
COR_SEPAR = 0xC731      # RGB(52,56,62) = 0x31C7, pre-invertido

RADIUS, PAD_TOP_W = 0xD4D064, 0xD4D01C
GANCHO_CONT = 0x001216CC                # o `bl set_style_radius` em 0xD21690

BLOB_OFF = 0x001A5300
BLOB_MAX = 0x300


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


class Analise:
    def __init__(self, d):
        self.d = d
        self.md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        self.md.detail = True

    def ins(self, a):
        try:
            return next(self.md.disasm(self.d[a - XIP:a - XIP + 4], a), None)
        except Exception:
            return None

    def paginas(self):
        pages = {}
        for i in range(0x53):
            t = TAB_PAGINAS + 2 * self.d[TAB_PAGINAS - XIP + i]
            k = self.ins(t)
            if k and k.mnemonic == "bl":
                pages.setdefault(int(k.op_str.strip("#"), 0), i + 1)
        return pages

    def rastreia(self, inicio, alvos, limite=250):
        """Segue o objeto devolvido em r0 e devolve as chamadas a `alvos`
        em que ele e o 1o argumento, rastreando copias entre registradores.
        Foi preciso fazer assim porque as telas NAO usam a mesma sequencia
        de chamadas -- casar padrao de instrucoes achava menos da metade."""
        obj = {ARM_REG_R0}
        a = inicio + 4
        achados = []
        for _ in range(limite):
            k = self.ins(a)
            if k is None:
                break
            if k.mnemonic == "bl" and k.op_str.startswith("#"):
                t = int(k.op_str.strip("#"), 0)
                if ARM_REG_R0 in obj and t in alvos:
                    achados.append((a, t))
                obj -= {ARM_REG_R0 + i for i in range(4)}
                if t in (CRIA_BARRA, CRIA_CONT, CRIA_LINHA):
                    break
            elif (k.mnemonic == "mov" and len(k.operands) == 2
                  and k.operands[0].type == 1 and k.operands[1].type == 1):
                src, dst = k.operands[1].reg, k.operands[0].reg
                if src in obj:
                    obj.add(dst)
                else:
                    obj.discard(dst)
            else:
                for r in k.regs_access()[1]:
                    obj.discard(r)
            a += k.size
        return achados

    def chamadas(self):
        out = {}
        for a in range(0xD20000, 0xD40000, 2):
            k = self.ins(a)
            if not (k and k.mnemonic == "bl" and k.op_str.startswith("#")):
                continue
            t = int(k.op_str.strip("#"), 0)
            if t in (CRIA_BARRA, CRIA_CONT, CRIA_LINHA):
                out.setdefault(t, []).append(a)
        return out


def main():
    ap = argparse.ArgumentParser(description="Chrome padrao da home")
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
    an = Analise(data)

    pages = an.paginas()
    fns = sorted(pages)

    def dono(x):
        o = max([f for f in fns if f <= x], default=None)
        return pages.get(o)

    ch = an.chamadas()
    lista = {dono(x) for x in ch[CRIA_LINHA]} & {dono(x) for x in ch[CRIA_BARRA]}
    lista = {p for p in lista if p}

    faixa_h, faixa_sz, cont_h, cont_al = [], [], [], []
    falta, sem_cont = [], []
    for p in sorted(lista):
        b = []
        for x in ch[CRIA_BARRA]:
            if dono(x) == p:
                b += an.rastreia(x, {SET_SIZE, SET_H})
        c = []
        for x in ch[CRIA_CONT]:
            if dono(x) == p:
                c += an.rastreia(x, {SET_H, ALIGN})
        bh = [s for s, t in b if t == SET_H]
        bs = [s for s, t in b if t == SET_SIZE]
        chh = [s for s, t in c if t == SET_H]
        cal = [s for s, t in c if t == ALIGN]
        if not (bh or bs):
            falta.append((p, len(bh), len(bs), len(chh), len(cal)))
            continue
        if not chh and not cal:
            sem_cont.append(p)
        faixa_h += bh
        faixa_sz += bs
        cont_h += chh
        cont_al += cal

    erros = []
    if falta:
        erros.append("telas de lista sem o ponto da FAIXA: "
                     + ", ".join(f"0x{p:02X}" for p, *_ in falta))
    if any(x != 0xFF for x in data[BLOB_OFF:BLOB_OFF + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB_OFF:06X} nao esta virgem")

    # --- rotinas -----------------------------------------------------------
    base = BLOB_OFF + XIP
    rots, pos = {}, 0
    corpo = bytearray()

    def add(nome, cab, destino):
        nonlocal pos
        rots[nome] = base + pos
        corpo.extend(cab)
        corpo.extend(bl(base + pos + len(cab), destino, link=False))
        pos = len(corpo)

    add("faixa_h", struct.pack("<H", 0x2100 | ALTURA_FAIXA), SET_H)
    add("faixa_sz", struct.pack("<H", 0x2200 | ALTURA_FAIXA), SET_SIZE)
    add("cont_h", struct.pack("<H", 0x2100 | ALTURA_CONT), SET_H)
    add("cont_al", struct.pack("<H", 0x2300 | Y_CONT), ALIGN)
    rots["tema_bg"] = base + pos
    corpo.extend(struct.pack("<HH", 0xF240 | ((COR_FUNDO >> 12) & 0xF) | (((COR_FUNDO >> 11) & 1) << 10),
                             ((COR_FUNDO >> 8) & 7) << 12 | (COR_FUNDO & 0xFF)))
    corpo.extend(struct.pack("<H", 0x4770))               # bx lr
    pos = len(corpo)
    rots["cont_base"] = base + pos
    cb = bytearray(struct.pack("<H", 0xB501))            # push {r0, lr}
    cb += bl(base + pos + len(cb), RADIUS)               # bl radius(r0,0,0)
    for reg1, val, alvo in ((1, PAD_TOP, PAD_TOP_W),):
        cb += struct.pack("<H", 0x9800)                  # ldr r0,[sp]
        cb += struct.pack("<H", 0x2100 | val)            # movs r1,#pad
        cb += struct.pack("<H", 0x2200)                  # movs r2,#0
        cb += bl(base + pos + len(cb), alvo)
    cb += struct.pack("<H", 0x9800)                      # ldr r0,[sp]
    cb += struct.pack("<H", 0x2100 | ALTURA_CONT)        # movs r1,#141
    cb += bl(base + pos + len(cb), SET_H)
    cb += struct.pack("<H", 0x9800)                      # ldr r0,[sp]
    cb += struct.pack("<H", 0x2102)                      # movs r1,#2 TOP_MID
    cb += struct.pack("<H", 0x2200)                      # movs r2,#0
    cb += struct.pack("<H", 0x2300 | Y_CONT)             # movs r3,#19
    cb += bl(base + pos + len(cb), ALIGN)
    cb += struct.pack("<H", 0xBD01)                      # pop {r0, pc}
    corpo.extend(cb)
    pos = len(corpo)

    rots["borda"] = base + pos
    corpo.extend(struct.pack("<HH", 0xF240 | ((COR_SEPAR >> 12) & 0xF) | (((COR_SEPAR >> 11) & 1) << 10),
                             0x0100 | (((COR_SEPAR >> 8) & 7) << 12) | (COR_SEPAR & 0xFF)))
    corpo.extend(bl(base + pos + 4, BORDER_COLOR, link=False))
    pos = len(corpo)

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    got = [f"{i.mnemonic} {i.op_str}" for i in md.disasm(bytes(corpo), base)]
    esperado = ["movs r1, #0x11", "b.w #0xd4a1ea", "movs r2, #0x11", "b.w #0xd4a21a",
                "movs r1, #0x8d", "b.w #0xd4a1ea", "movs r3, #0x13", "b.w #0xd4a3a2",
                f"movw r0, #0x{COR_FUNDO:x}", "bx lr",
                "push {r0, lr}", "bl #0xd4d064",
                "ldr r0, [sp]", "movs r1, #1", "movs r2, #0", "bl #0xd4d01c",
                "ldr r0, [sp]", "movs r1, #0x8d", "bl #0xd4a1ea",
                "ldr r0, [sp]", "movs r1, #2", "movs r2, #0", "movs r3, #0x13",
                "bl #0xd4a3a2", "pop {r0, pc}",
                f"movw r1, #0x{COR_SEPAR:x}", "b.w #0xd4d0c8"]
    if got != esperado:
        erros.append("rotinas montadas nao conferem:\n      esperado "
                     f"{esperado}\n      obtido   {got}")

    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print("  OPENPOD — CHROME PADRAO DA HOME")
    print()
    print(f"  telas de lista: {len(lista)}   TODAS com os pontos localizados")
    print(f"    altura da faixa      {len(faixa_h):3d} via set_height  "
          f"{len(faixa_sz):3d} via set_size")
    print(f"    altura do conteiner  {len(cont_h):3d}")
    print(f"    align do conteiner   {len(cont_al):3d} "
          "(as demais usam set_align BOTTOM_MID)")
    print(f"    telas que nao mexem no conteiner: {len(sem_cont)} "
          f"-> pegam o padrao do criador")
    print()
    print(f"  faixa 0..15 | separador 16 | respiro 17..18 | lista {Y_CONT}")
    print()
    print("  ALTERACOES")
    data[BLOB_OFF:BLOB_OFF + len(corpo)] = corpo
    print(f"    0x{BLOB_OFF:06X}  {len(corpo)} B de rotinas")
    for sites, nome in ((faixa_h, "faixa_h"), (faixa_sz, "faixa_sz"),
                        (cont_h, "cont_h"), (cont_al, "cont_al")):
        for s in sites:
            data[s - XIP:s - XIP + 4] = bl(s, rots[nome])
        print(f"    {len(sites):3d} ganchos -> {nome}")
    for s, nome in ((0xD2171A, "tema_bg"), (0xD21742, "borda"),
                    (GANCHO_CONT + XIP, "cont_base")):
        data[s - XIP:s - XIP + 4] = bl(s, rots[nome])
        print(f"      1 gancho  -> {nome}  (criador compartilhado da faixa)")
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
