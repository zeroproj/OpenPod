#!/usr/bin/env python3
# NÃO ALTERAR sem o arquiteto. O hash deste arquivo é conferido por tools/ci.sh
# (tests/PROTEGIDOS.sha256). Ficha: docs/tarefas/006-rc6-home-moldura.md
"""
test_rc6.py — critérios de aceite da Reload 1.0 RC6 (home sem nomes, grade
centralizada, moldura branca no ícone selecionado).

Constrói `reload_1.0_rc5` (catraca) e `reload_1.0_rc6` a partir do ORIGINAL.

USO
    python3 tests/test_rc6.py

DEPENDÊNCIAS
    Python 3 + capstone. Não abre o USB.
"""

import hashlib
import importlib.util
import os
import struct
import subprocess
import sys
import tempfile
import unittest

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
SHA_ORIGINAL = "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f"
SHA_RC5 = "f9f2e05990adb5d3882bbf093a6251673139004571af7698f3514b02f1e08f50"  # rodando 2026-10-23
XIP = 0x00C00000
SLP = 0x00D4CAC4                      # lv_obj_set_local_style_prop(obj, prop, valor, seletor)

# --- folha da home (RC4): 128x160 INDEXED_8
HOME_PAL, HOME_PX, LARG = 0x0CDD5C, 0x0CE15C, 128
# fileiras de ícones (31 px) com a sombra: 2 linhas acima (exceto a 1ª, colada na barra) e 3 abaixo
FAIXAS = ((16, 34, 29), (62, 36, 70), (110, 36, 114))   # (topo antigo, altura, topo novo)
# ícones passam a começar em y 29, 72, 116: grade centralizada entre a barra (y 16) e o fim (159)

# --- rótulos da home viram molduras
ROTULO_POS = 0x0486A0                 # 9 x (int16 x, int16 y), copiada em 0xD2EC5E
POS_NOVAS = [(x, y) for y in (27, 70, 114) for x in (5, 46, 87)]   # 2 px fora do ícone
TAMANHO = {0x12ED5C: (bytes.fromhex("0f22"), bytes.fromhex("2322")),   # altura 15 -> 35
           0x12ED5E: (bytes.fromhex("2821"), bytes.fromhex("2321"))}   # largura 40 -> 35

LOTE, LOTE_TAM = 0x1A6400, 0x80
DESEL, SEL, CRIA, VAZIO = 0xDA6400, 0xDA640A, 0xDA6414, 0xDA6448
GANCHOS = {   # endereço: (alvo de fábrica, alvo novo)
    0x12ED30: (0xD2108C, CRIA),       # texto do rótulo -> "" (e estilo da moldura)
    0x12ED46: (0xD4D10A, DESEL),      # criação: cor normal -> moldura apagada
    0x12E9CA: (0xD4D10A, DESEL),      # navegação: tira a seleção (4 direções)
    0x12EA26: (0xD4D10A, DESEL),
    0x12EABA: (0xD4D10A, DESEL),
    0x12EB12: (0xD4D10A, DESEL),
    0x12EB4C: (0xD4D10A, SEL),        # navegação: dá a seleção
    0x12EDBC: (0xD4D10A, SEL),        # criação: item inicial
}
ROTINA_ESPERADA = [
    ("movs", "r1, #0x31"), ("movs", "r2, #0"), ("movs", "r3, #0"), ("b", "#0xd4cac4"),
    ("movs", "r1, #0x31"), ("movs", "r2, #0xff"), ("movs", "r3, #0"), ("b", "#0xd4cac4"),
    ("push", "{r4, lr}"),
    ("mov", "r0, r6"), ("movw", "r1, #0x1032"), ("movs", "r2, #2"), ("movs", "r3, #0"), ("bl", "#0xd4cac4"),
    ("mov", "r0, r6"), ("movs", "r1, #0x60"), ("movs", "r2, #8"), ("movs", "r3, #0"), ("bl", "#0xd4cac4"),
    ("mov", "r0, r6"), ("movs", "r1, #0x30"), ("movw", "r2, #0xffff"), ("movs", "r3, #0"), ("bl", "#0xd4cac4"),
    ("movw", "r0, #0x6448"), ("movt", "r0, #0xda"), ("pop", "{r4, pc}"),
]
FERRAMENTAS = ("fab_home_moldura.py",)   # uma só: exige a RC5 exata (sha) na entrada
PROIBIDAS = {"patch_icones_home.py", "patch_home_barra.py", "patch_cor_selecao.py",
             "patch_menu_text.py", "aplica_textos.py"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def le(p):
    with open(p, "rb") as f:
        return f.read()


def constroi(receita, destino):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools/build.py"),
                        "--receita", receita, "--saida", destino],
                       capture_output=True, text=True, cwd=RAIZ)
    return r.returncode, r.stdout + r.stderr


def bl_alvo(b, a):
    h1, h2 = struct.unpack_from("<HH", b, a)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xD000) != 0xD000:
        return None
    S = (h1 >> 10) & 1
    J1, J2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    I1, I2 = 1 - (J1 ^ S), 1 - (J2 ^ S)
    off = (S << 24) | (I1 << 23) | (I2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if S:
        off -= 1 << 25
    return XIP + a + 4 + off


def preto(b):
    p = b[HOME_PAL:HOME_PX]
    return [i for i in range(256) if p[i * 4:i * 4 + 3] == b"\0\0\0" and p[i * 4 + 3] == 255][0]


def folha_esperada(rc5):
    px = bytearray(rc5[HOME_PX:HOME_PX + LARG * 160])
    velho = bytes(px)
    k = preto(rc5)
    for y in range(16, 160):
        px[LARG * y:LARG * (y + 1)] = bytes([k]) * LARG
    for a, h, n in FAIXAS:
        px[LARG * n:LARG * (n + h)] = velho[LARG * a:LARG * (a + h)]
    return bytes(px)


class RC6(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orig = le(ORIGINAL)
        assert sha(cls.orig) == SHA_ORIGINAL, "ORIGINAL nao confere — PARE"
        tmp = tempfile.mkdtemp(prefix="openpod_test_rc6_")
        p5, p6 = os.path.join(tmp, "rc5.bin"), os.path.join(tmp, "rc6.bin")
        constroi("reload_1.0_rc5", p5)
        cls.rc6_rc, cls.rc6_log = constroi("reload_1.0_rc6", p6)
        cls.rc5 = le(p5) if os.path.exists(p5) else b""
        cls.rc6 = le(p6) if os.path.exists(p6) else b""

    def test_c0_constroi(self):
        self.assertEqual(self.rc6_rc, 0, "build reload_1.0_rc6 falhou:\n" + self.rc6_log[-2000:])
        self.assertEqual(len(self.rc6), 0x200000)

    def test_c1_rc5_reprodutivel(self):
        self.assertEqual(sha(self.rc5), SHA_RC5, "a RC5 mudou — catraca")

    def test_c2_receita_e_lote(self):
        spec = importlib.util.spec_from_file_location("build", os.path.join(RAIZ, "tools/build.py"))
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
        r5 = [x for x, _, _ in b.RECEITAS["reload_1.0_rc5"]]
        r6 = [x for x, _, _ in b.RECEITAS["reload_1.0_rc6"]]
        self.assertEqual(r6[:len(r5)], r5)
        self.assertEqual(tuple(r6[len(r5):]), FERRAMENTAS)
        self.assertFalse(set(r6) & PROIBIDAS)
        self.assertEqual(b.MAPA.get("fab_home_moldura.py"), (LOTE, LOTE_TAM))
        for nome, (ini, tam) in b.MAPA.items():
            if nome != "fab_home_moldura.py":
                self.assertFalse(ini < LOTE + LOTE_TAM and LOTE < ini + tam, f"lote cruza {nome}")

    # --- C3: grade centralizada (só move linhas de índices; paleta da RC4 intocada)
    def test_c3_folha(self):
        self.assertEqual(self.rc6[HOME_PAL:HOME_PX], self.rc5[HOME_PAL:HOME_PX], "paleta mudou")
        self.assertEqual(self.rc6[HOME_PX:HOME_PX + LARG * 160], folha_esperada(self.rc5))

    # --- C4: rótulos viram molduras
    def test_c4_posicoes_e_tamanho(self):
        self.assertEqual([struct.unpack_from("<hh", self.orig, ROTULO_POS + 4 * i) for i in range(9)],
                         [(3, 48), (44, 48), (86, 48), (3, 96), (44, 96), (86, 96),
                          (3, 144), (44, 145), (86, 145)], "premissa")
        self.assertEqual([struct.unpack_from("<hh", self.rc6, ROTULO_POS + 4 * i) for i in range(9)], POS_NOVAS)
        for a, (fab, novo) in TAMANHO.items():
            self.assertEqual(self.orig[a:a + 2], fab)
            self.assertEqual(self.rc6[a:a + 2], novo)

    def test_c4_ganchos(self):
        for a, (fab, novo) in GANCHOS.items():
            self.assertEqual(bl_alvo(self.orig, a), fab, f"premissa 0x{a:X}")
            self.assertEqual(bl_alvo(self.rc6, a), novo, f"0x{a:X}")

    def test_c4_rotinas(self):
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        got = []
        for i in md.disasm(self.rc6[LOTE:LOTE + LOTE_TAM], XIP + LOTE):
            got.append((i.mnemonic.replace(".w", ""), i.op_str))
            if len(got) == len(ROTINA_ESPERADA):
                fim = i.address + i.size - XIP
                break
        self.assertEqual(got, ROTINA_ESPERADA)
        self.assertEqual((DESEL, SEL, CRIA), (XIP + LOTE, XIP + LOTE + 0xA, XIP + LOTE + 0x14))
        self.assertEqual(fim, VAZIO - XIP)
        self.assertEqual(self.rc6[fim], 0, "string vazia")
        self.assertTrue(all(x == 0xFF for x in self.rc6[fim + 1:LOTE + LOTE_TAM]))

    def test_c4_funcao_de_estilo_intocada(self):
        o = SLP - XIP
        self.assertEqual(self.rc6[o:o + 0x40], self.orig[o:o + 0x40])

    # --- C5: segurança
    def test_c5_so_regioes_permitidas(self):
        ok = [(HOME_PX + LARG * 16, HOME_PX + LARG * 160), (ROTULO_POS, ROTULO_POS + 36),
              (LOTE, LOTE + LOTE_TAM)] + [(a, a + 2) for a in TAMANHO] + [(a, a + 4) for a in GANCHOS]
        fora = [i for i in range(len(self.orig))
                if self.rc5[i] != self.rc6[i] and not any(a <= i < b for a, b in ok)]
        self.assertEqual(fora, [], f"escreveu fora: {[hex(x) for x in fora[:8]]}")

    def test_c5_bootloader_r1_psmp(self):
        dif = [i for i in range(len(self.orig)) if self.orig[i] != self.rc6[i]]
        self.assertGreaterEqual(min(dif), 0xE000)
        self.assertFalse(any(i >= 0x1FC000 for i in dif))


class Recusa(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        tmp = tempfile.mkdtemp(prefix="openpod_recusa6_")
        p5, p4 = os.path.join(tmp, "rc5.bin"), os.path.join(tmp, "rc4.bin")
        constroi("reload_1.0_rc5", p5)
        constroi("reload_1.0_rc4", p4)
        cls.rc5, cls.rc4 = le(p5), le(p4)

    def roda(self, ferramenta, entrada, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_r6_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(entrada)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", ferramenta),
                            "--in", src, "--out", dst] + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), le(src) == entrada

    def inverte(self, a):
        b = bytearray(self.rc5)
        b[a] ^= 0xFF
        return bytes(b)

    def confere(self, ferramenta, casos):
        for nome, entrada in casos.items():
            rc, criou, intacta = self.roda(ferramenta, entrada)
            self.assertNotEqual(rc, 0, f"{ferramenta} aceitou {nome}")
            self.assertFalse(criou, f"{ferramenta} criou saida com {nome}")
            self.assertTrue(intacta)

    def test_d3_existem(self):
        for f in FERRAMENTAS:
            self.assertTrue(os.path.exists(os.path.join(RAIZ, "tools", f)), f)

    def test_d3_recusa(self):
        for f in FERRAMENTAS:   # exige a RC5 exata (sha) como entrada
            casos = {"rc4": self.rc4, "truncado": self.rc5[:0x100000]}
            for a in (HOME_PAL, HOME_PX + LARG * 20, ROTULO_POS, 0x12ED30, 0x12EB4C, 0x12ED5C,
                      LOTE, LOTE + LOTE_TAM - 1, SLP - XIP):
                casos[hex(a)] = self.inverte(a)
            self.confere(f, casos)

    def test_d3_aceita_rc5_e_dry_run(self):
        for f in FERRAMENTAS:
            self.assertEqual(self.roda(f, self.rc5)[:2], (0, True), f)
            self.assertEqual(self.roda(f, self.rc5, ["--dry-run"])[:2], (0, False), f)

    def test_d3_saida_igual_ou_link(self):
        for f in FERRAMENTAS:
            for tipo in ("mesmo", "symlink", "hardlink"):
                tmp = tempfile.mkdtemp(prefix="openpod_link6_")
                src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
                with open(src, "wb") as fh:
                    fh.write(self.rc5)
                if tipo == "mesmo":
                    dst = src
                else:
                    (os.symlink if tipo == "symlink" else os.link)(src, dst)
                r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", f),
                                    "--in", src, "--out", dst], capture_output=True, cwd=RAIZ)
                self.assertNotEqual(r.returncode, 0, f"{f} {tipo}")
                self.assertEqual(le(src), self.rc5, f"{f} {tipo}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
