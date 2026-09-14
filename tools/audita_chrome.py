#!/usr/bin/env python3
"""
audita_chrome.py — Confere, tela a tela, se o chrome esta padronizado.

PARA QUE SERVE

    O Projeto Saturno poe o design dos menus numa tabela de 19 bytes e
    liga as telas a ela por ganchos. Esta ferramenta le a imagem final e
    pergunta, para cada tela: **voce esta ligada na tabela?**

    Ela nao conserta nada. So audita — e serve para responder "esta tudo
    certo?" com uma lista, nao com uma opiniao.

O QUE CONFERE

    Por tela:
      faixa        a altura passa por um thunk da tabela?
      conteiner    altura e posicao passam pelos thunks?
      linha        usa o helper compartilhado E a ALTURA vem da tabela?
    Global:
      icones       todo ponto que carrega a fonte de icones esta ligado?
      selecao      todo palette_main(7) esta ligado?
      recuo        todo align(LEFT_MID, 13) esta ligado?
      helpers      os tres helpers chamam a normalizacao?

USO
    python3 tools/audita_chrome.py firmware/WORKING/GN438_openpod_v067.bin
"""

import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    from capstone.arm import ARM_REG_R0
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
CRIA_BARRA, CRIA_CONT, CRIA_LINHA = 0xD216F0, 0xD21690, 0xD21764
SET_SIZE, SET_H, ALIGN, SET_FONT = 0xD4A21A, 0xD4A1EA, 0xD4A3A2, 0xD4D12E
PALETTE, TAB_PAGINAS = 0xD57B48, 0xD23B38
FONTE_ICONES = 0x00CA671C
TAB_OFF = 0x001A5400

ROTINAS = {
    0xDA5300: "faixa_h", 0xDA5306: "faixa_sz", 0xDA530C: "cont_h",
    0xDA5312: "cont_al", 0xDA5318: "cor_faixa", 0xDA531E: "cont_base",
    0xDA5344: "cor_separador", 0xDA5500: "normaliza", 0xDA5530: "faixa_base",
    0xDA5548: "cont_novo", 0xDA5558: "linha_nova", 0xDA5600: "home_faixa",
    0xDA5700: "cor_selecao", 0xDA570C: "normaliza2", 0xDA5760: "home_pos",
    0xDA577C: "home_altura", 0xDA5800: "icone", 0xDA5880: "recuo",
    0xDA5900: "extras_rota", 0xDA5980: "cor_texto", 0xDA598C: "linha_s10",
    0xDA5A00: "linha_altura", 0xDA5A08: "linha_tamanho",
}

# S11: por onde a altura da linha tem de passar.
THUNK_LINHA_H, THUNK_LINHA_SZ = 0xDA5A00, 0xDA5A08


class A:
    def __init__(self, d):
        self.d = d
        self.md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        self.md.detail = True

    def i(self, a):
        try:
            return next(self.md.disasm(self.d[a - XIP:a - XIP + 4], a), None)
        except Exception:
            return None

    def alvo(self, a):
        k = self.i(a)
        if k and k.mnemonic in ("bl", "b.w") and k.op_str.startswith("#"):
            return int(k.op_str.strip("#"), 0)
        return None

    def paginas(self):
        p = {}
        for n in range(0x53):
            t = TAB_PAGINAS + 2 * self.d[TAB_PAGINAS - XIP + n]
            k = self.i(t)
            if k and k.mnemonic == "bl":
                p.setdefault(int(k.op_str.strip("#"), 0), n + 1)
        return p

    def rastreia(self, ini, lim=250):
        obj = {ARM_REG_R0}
        a, out = ini + 4, []
        for _ in range(lim):
            k = self.i(a)
            if k is None:
                break
            if k.mnemonic == "bl" and k.op_str.startswith("#"):
                t = int(k.op_str.strip("#"), 0)
                if ARM_REG_R0 in obj:
                    out.append(t)
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
            a += k.size
        return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d = open(sys.argv[1], "rb").read()
    an = A(d)
    pages = an.paginas()
    fns = sorted(pages)

    def dono(x):
        o = max([f for f in fns if f <= x], default=None)
        return pages.get(o)

    ch = {}
    for a in range(0xD20000, 0xD40000, 2):
        t = an.alvo(a)
        if t in (CRIA_BARRA, CRIA_CONT, CRIA_LINHA):
            ch.setdefault(t, []).append(a)

    lista = sorted({dono(x) for x in ch[CRIA_LINHA]}
                   & {dono(x) for x in ch[CRIA_BARRA]} - {None})

    print()
    print("=" * 68)
    print("  AUDITORIA DO CHROME —", sys.argv[1].split("/")[-1])
    print("=" * 68)
    campos = [("cor_tela", 0, 2), ("cor_faixa", 2, 2), ("cor_separador", 4, 2),
              ("cor_texto", 6, 2), ("cor_texto_sel", 8, 2),
              ("cor_selecao", 10, 2), ("altura_faixa", 12, 1),
              ("altura_linha", 13, 1), ("inicio_lista", 14, 1),
              ("margem", 15, 1), ("raio", 16, 1), ("pad_topo", 17, 1),
              ("icones", 18, 1)]
    print("\n  TABELA DE TEMA")
    for n, o, t in campos:
        v = struct.unpack_from("<H" if t == 2 else "<B", d, TAB_OFF + o)[0]
        print(f"    +{o:02X}  {n:16s} {'0x%04X' % v if t == 2 else v}")

    print(f"\n  TELAS DE LISTA: {len(lista)}")
    print(f"  {'pg':>5}  {'faixa':>10}  {'conteiner':>18}  {'linha':>18}")
    ruins = []
    for p in lista:
        fx = set()
        for x in ch[CRIA_BARRA]:
            if dono(x) == p:
                fx |= set(an.rastreia(x))
        ct = set()
        for x in ch[CRIA_CONT]:
            if dono(x) == p:
                ct |= set(an.rastreia(x))
        ln = set()
        for x in ch[CRIA_LINHA]:
            if dono(x) == p:
                ln |= set(an.rastreia(x))
        l_ok = bool(ln & {THUNK_LINHA_H, THUNK_LINHA_SZ})
        l_cru = bool(ln & {SET_H, SET_SIZE})
        f_ok = bool(fx & {0xDA5300, 0xDA5306})
        f_cru = bool(fx & {SET_H, SET_SIZE})
        c_ok = bool(ct & {0xDA530C, 0xDA5312})
        c_cru = bool(ct & {SET_H, ALIGN})
        fs = "TABELA" if f_ok else ("CRUA!" if f_cru else "padrao")
        cs = ("TABELA" if c_ok else
              ("CRUA!" if c_cru else "padrao do criador"))
        ls = "TABELA" if l_ok else ("CRUA!" if l_cru else "helper")
        print(f"  0x{p:02X}  {fs:>10}  {cs:>18}  {ls:>18}")
        if f_cru and not f_ok:
            ruins.append(f"0x{p:02X}: faixa dimensionada fora da tabela")
        if c_cru and not c_ok:
            ruins.append(f"0x{p:02X}: conteiner dimensionado fora da tabela")
        if l_cru and not l_ok:
            ruins.append(f"0x{p:02X}: ALTURA DA LINHA fora da tabela")

    print("\n  PONTOS GLOBAIS")
    # icones
    livres = []
    for a in range(0xD20000, 0xD40000, 2):
        if an.alvo(a) != SET_FONT:
            continue
        f = None
        for b in range(a - 12, a, 2):
            j = an.i(b)
            if j and j.mnemonic == "ldr" and "r1, [pc" in j.op_str:
                imm = int(j.op_str.split("#")[-1].rstrip("]"), 0)
                f = struct.unpack_from("<I", d, (((b + 4) & ~3) + imm) - XIP)[0]
        if f == FONTE_ICONES:
            livres.append(a)
    print(f"    icones      {len(livres)} pontos ainda com a fonte crua"
          f"   {'OK' if not livres else 'DIVERGENTE'}")
    if livres:
        ruins += [f"icone cru em 0x{x - XIP:06X}" for x in livres]

    pal = [a for a in range(0xD20000, 0xDB0000, 2)
           if an.alvo(a) == PALETTE
           and (j := an.i(a - 4)) and j.mnemonic == "movs"
           and j.op_str == "r0, #7"]
    print(f"    selecao     {len(pal)} pontos ainda em palette_main(7)"
          f"   {'OK' if not pal else 'ver abaixo'}")
    for x in pal:
        ruins.append(f"palette_main(7) cru em 0x{x - XIP:06X}")

    rec = []
    for a in range(0xD20000, 0xD40000, 2):
        if an.alvo(a) != ALIGN:
            continue
        v = {}
        for b in range(a - 16, a, 2):
            j = an.i(b)
            if j and j.mnemonic == "movs" and ", #" in j.op_str:
                r, val = j.op_str.split(", #")
                if r in ("r1", "r2"):
                    v[r] = int(val, 0)
        if v.get("r1") == 7 and v.get("r2") == 13:
            rec.append(a)
    print(f"    recuo       {len(rec)} pontos ainda com x_ofs=13 cru"
          f"   {'OK' if not rec else 'DIVERGENTE'}")
    ruins += [f"recuo cru em 0x{x - XIP:06X}" for x in rec]

    for nome, fn in (("faixa", CRIA_BARRA), ("conteiner", CRIA_CONT),
                     ("linha", CRIA_LINHA)):
        alvos = {an.alvo(a) for a in range(fn, fn + 0x80, 2)}
        norm = bool(alvos & set(ROTINAS))
        print(f"    helper {nome:10s} chama rotina da carcaca: "
              f"{'sim' if norm else 'NAO'}")
        if not norm:
            ruins.append(f"helper {nome} nao chama a carcaca")

    h = {an.alvo(a) for a in range(0xD2EBB8, 0xD2EE00, 2)}
    print(f"    home        faixa do helper: "
          f"{'sim' if 0xDA5600 in h else 'NAO'}   "
          f"geometria da tabela: {'sim' if 0xDA5760 in h else 'NAO'}")
    if 0xDA5600 not in h or 0xDA5760 not in h:
        ruins.append("home fora da carcaca")

    print()
    print("=" * 68)
    if ruins:
        print(f"  {len(ruins)} DIVERGENCIA(S):")
        for r in ruins:
            print("   -", r)
    else:
        print("  SEM DIVERGENCIAS — todas as telas lidas estao na tabela.")
    print("=" * 68)
    print()
    return 1 if ruins else 0


if __name__ == "__main__":
    sys.exit(main())
