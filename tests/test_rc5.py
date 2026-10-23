#!/usr/bin/env python3
# NÃO ALTERAR sem o arquiteto. O hash deste arquivo é conferido por tools/ci.sh
# (tests/PROTEGIDOS.sha256). Ficha: docs/tarefas/005-rc5-textos.md
"""
test_rc5.py — critérios de aceite da Reload 1.0 RC5 (textos em português
revisados + nomes curtos na home).

Constrói `reload_1.0_rc4` (catraca) e `reload_1.0_rc5` a partir do ORIGINAL
e confere a tabela de textos em português ponteiro a ponteiro.

USO
    python3 tests/test_rc5.py

DEPENDÊNCIAS
    Python 3. Não abre o USB.
"""

import hashlib
import importlib.util
import os
import re
import struct
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
SHA_ORIGINAL = "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f"
SHA_RC4 = "74e8cb315958b053f9e36e366a32f103ba995f7a18316c1c01e3de89e3f3b6d4"  # rodando no aparelho 2026-10-23
XIP = 0x00C00000

# --- fatos do ORIGINAL (ficha §Evidência)
TABELA_PT = 0x053B84          # 216 ponteiros XIP; idioma 8 em 0xD2108C (literal 0x121104)
N_TEXTOS = 216
RC1_IDS = (40, 91)            # repontados pela RC1 ("Atualizar por SD"): intocáveis
TBL, CMAP, N_GLIFOS = 0x086C44, 0x0A27E6, 7098   # fonte dos menus: avanço em TBL+g*16+4
LOTE, LOTE_TAM = 0x1A5000, 0x1000
HOME_IDS = (1, 2, 3, 4, 5, 8, 9, 10)               # rótulos da home: largura 40 px (0xD2ED5E)
HOME_LARGURA = 40
TEXTOS = os.path.join(RAIZ, "assets/textos_pt.tsv")
SHA_TEXTOS = "c9cc64bda98520f0e690ef746a6efad156ef3f39804186c06a0673884c1ad2e2"
FORMATO = re.compile(r"%[-+ #0]*\d*(?:\.\d+)?[a-zA-Z%]")

FERRAMENTA = "fab_textos.py"
PROIBIDAS = {"aplica_textos.py", "patch_menu_text.py", "relocate_lang_table.py",
             "propoe_textos.py", "patch_titulos.py"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def le(p):
    with open(p, "rb") as f:
        return f.read()


def textos():
    out = {}
    with open(TEXTOS, encoding="utf-8") as f:
        for linha in f:
            if linha.startswith("#") or not linha.strip():
                continue
            i, t = linha.rstrip("\n").split("\t", 1)
            out[int(i)] = t.replace("\\n", "\n")
    return out


def constroi(receita, destino):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools/build.py"),
                        "--receita", receita, "--saida", destino],
                       capture_output=True, text=True, cwd=RAIZ)
    return r.returncode, r.stdout + r.stderr


def ponteiro(b, i):
    return struct.unpack_from("<I", b, TABELA_PT + 4 * i)[0]


def string(b, p):
    o = p - XIP
    return b[o:b.index(b"\0", o)]


class RC5(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orig = le(ORIGINAL)
        assert sha(cls.orig) == SHA_ORIGINAL, "ORIGINAL nao confere — PARE"
        tmp = tempfile.mkdtemp(prefix="openpod_test_rc5_")
        p4, p5 = os.path.join(tmp, "rc4.bin"), os.path.join(tmp, "rc5.bin")
        constroi("reload_1.0_rc4", p4)
        cls.rc5_rc, cls.rc5_log = constroi("reload_1.0_rc5", p5)
        cls.rc4 = le(p4) if os.path.exists(p4) else b""
        cls.rc5 = le(p5) if os.path.exists(p5) else b""
        cls.t = textos()
        cls.cmap = {c: g for g, c in enumerate(struct.unpack_from("<%dH" % N_GLIFOS, cls.orig, CMAP))}

    def largura(self, t):
        return sum(struct.unpack_from("<I", self.orig, TBL + self.cmap[ord(c)] * 16 + 4)[0]
                   for c in t if c != "\n")

    # --- C0/C1
    def test_c0_constroi(self):
        self.assertEqual(self.rc5_rc, 0, "build reload_1.0_rc5 falhou:\n" + self.rc5_log[-2000:])
        self.assertEqual(len(self.rc5), 0x200000)

    def test_c1_rc4_reprodutivel(self):
        self.assertEqual(sha(self.rc4), SHA_RC4, "a RC4 mudou — catraca")

    # --- C2: receita, lote, conteúdo
    def test_c2_receita_e_lote(self):
        spec = importlib.util.spec_from_file_location("build", os.path.join(RAIZ, "tools/build.py"))
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
        r4 = [x for x, _, _ in b.RECEITAS["reload_1.0_rc4"]]
        r5 = [x for x, _, _ in b.RECEITAS["reload_1.0_rc5"]]
        self.assertEqual(r5, r4 + [FERRAMENTA])
        self.assertFalse(set(r5) & PROIBIDAS)
        self.assertEqual(b.MAPA.get(FERRAMENTA), (LOTE, LOTE_TAM))
        for nome, (ini, tam) in b.MAPA.items():
            if nome != FERRAMENTA:
                self.assertFalse(ini < LOTE + LOTE_TAM and LOTE < ini + tam, f"lote cruza {nome}")

    def test_c2_conteudo(self):
        self.assertEqual(sha(le(TEXTOS)), SHA_TEXTOS, "textos_pt.tsv mudou sem o arquiteto")
        self.assertFalse(set(self.t) & set(RC1_IDS))
        self.assertTrue(all(0 <= i < N_TEXTOS for i in self.t))

    # --- C3: cada texto no lugar, o resto intocado
    def test_c3_textos_novos(self):
        for i, t in self.t.items():
            p = ponteiro(self.rc5, i)
            self.assertTrue(XIP + LOTE <= p < XIP + LOTE + LOTE_TAM, f"id {i}: ponteiro 0x{p:X} fora do lote")
            self.assertEqual(string(self.rc5, p), t.encode("utf-8"), f"id {i}")

    def test_c3_outros_ids_intocados(self):
        for i in range(N_TEXTOS):
            if i not in self.t:
                self.assertEqual(ponteiro(self.rc5, i), ponteiro(self.rc4, i), f"id {i} mudou")

    def test_c3_strings_de_fabrica_intocadas(self):
        for i in self.t:
            p = ponteiro(self.orig, i) - XIP
            n = len(string(self.orig, ponteiro(self.orig, i))) + 1
            self.assertEqual(self.rc5[p:p + n], self.orig[p:p + n], f"string de fabrica {i} editada no lugar")

    # --- C4: fonte, formato, largura
    def test_c4_glifos_existem(self):
        for i, t in self.t.items():
            faltam = [c for c in t if c != "\n" and ord(c) not in self.cmap]
            self.assertEqual(faltam, [], f"id {i}: sem glifo para {faltam}")

    def test_c4_formato_igual(self):
        for i, t in self.t.items():
            fab = string(self.orig, ponteiro(self.orig, i)).decode("utf-8")
            self.assertEqual(FORMATO.findall(t), FORMATO.findall(fab), f"id {i}: especificadores %")

    def test_c4_home_cabe(self):
        for i in HOME_IDS:
            self.assertIn(i, self.t)
            self.assertLessEqual(self.largura(self.t[i]), HOME_LARGURA, f"id {i} {self.t[i]!r}")

    def test_c4_nao_alarga_alem_da_fabrica(self):
        # revisão R0: cada linha cabe em 113 px OU não é mais larga que a de fábrica
        def maior(t):
            return max(self.largura(x) for x in t.replace("%%", "%").split("\n"))
        for i, t in self.t.items():
            fab = string(self.orig, ponteiro(self.orig, i)).decode("utf-8")
            self.assertLessEqual(maior(t), max(113, maior(fab)), f"id {i} {t!r}")

    def test_c4_home_nomes(self):
        esperado = {1: "Música", 2: "Livros", 3: "Vídeo", 4: "Fotos", 5: "Gravar",
                    8: "Pastas", 9: "BT", 10: "Config"}
        self.assertEqual({i: self.t[i] for i in HOME_IDS}, esperado)

    # --- C5: segurança
    def test_c5_so_regioes_permitidas(self):
        ok = [(TABELA_PT + 4 * i, TABELA_PT + 4 * i + 4) for i in self.t] + [(LOTE, LOTE + LOTE_TAM)]
        fora = [i for i in range(len(self.orig))
                if self.rc4[i] != self.rc5[i] and not any(a <= i < b for a, b in ok)]
        self.assertEqual(fora, [], f"escreveu fora: {[hex(x) for x in fora[:8]]}")

    def test_c5_bootloader_r1_psmp(self):
        dif = [i for i in range(len(self.orig)) if self.orig[i] != self.rc5[i]]
        self.assertGreaterEqual(min(dif), 0xE000)
        self.assertFalse(any(i >= 0x1FC000 for i in dif))


class Recusa(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="openpod_recusa5_")
        p4 = os.path.join(cls.tmp, "rc4.bin")
        constroi("reload_1.0_rc4", p4)
        cls.rc4 = le(p4)
        p3 = os.path.join(cls.tmp, "rc3.bin")
        constroi("reload_1.0_rc3", p3)
        cls.rc3 = le(p3)

    def roda(self, entrada, extra=(), dst=None):
        tmp = tempfile.mkdtemp(prefix="openpod_r5_")
        src = os.path.join(tmp, "in.bin")
        dst = dst or os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(entrada)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", FERRAMENTA),
                            "--in", src, "--out", dst] + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), le(src) == entrada

    def muda(self, a, v=None):
        b = bytearray(self.rc4)
        if v is None:
            b[a] ^= 0xFF
        else:
            b[a:a + len(v)] = v
        return bytes(b)

    def test_d3_existe(self):
        self.assertTrue(os.path.exists(os.path.join(RAIZ, "tools", FERRAMENTA)))

    def test_d3_recusa(self):
        casos = {
            "truncado": self.rc4[:0x100000],
            "ponteiro_id1": self.muda(TABELA_PT + 4 * 1, struct.pack("<I", 0x00C53B00)),
            "ponteiro_id215": self.muda(TABELA_PT + 4 * 215),
            "rc1_id40": self.muda(TABELA_PT + 4 * 40, struct.pack("<I", ponteiro(le(ORIGINAL), 40))),
            "rc1_id91": self.muda(TABELA_PT + 4 * 91 + 3),
            "lote_inicio": self.muda(LOTE, b"\0"),
            "lote_fim": self.muda(LOTE + LOTE_TAM - 1, b"\0"),
            "fonte_cmap": self.muda(CMAP + 2 * 100),
            "literal_tabela": self.muda(0x121104),
            "original": le(ORIGINAL),          # sem a RC1, os ids 40/91 não batem
            "rc3": self.rc3,                   # revisão R0: só a RC4 exata (sha) é entrada válida
        }
        for nome, entrada in casos.items():
            rc, criou, intacta = self.roda(entrada)
            self.assertNotEqual(rc, 0, f"aceitou {nome}")
            self.assertFalse(criou, f"criou saida com {nome}")
            self.assertTrue(intacta)

    def test_d3_recusa_textos_adulterados(self):
        tmp = tempfile.mkdtemp(prefix="openpod_tsv5_")
        p = os.path.join(tmp, "t.tsv")
        with open(TEXTOS, encoding="utf-8") as f:
            s = f.read()
        with open(p, "w", encoding="utf-8") as f:
            f.write(s.replace("\tFotos\n", "\tFotografias\n"))
        rc, criou, _ = self.roda(self.rc4, ["--textos", p])
        self.assertNotEqual(rc, 0)
        self.assertFalse(criou)

    def test_d3_aceita_rc4_e_dry_run(self):
        rc, criou, _ = self.roda(self.rc4)
        self.assertEqual((rc, criou), (0, True))
        rc, criou, _ = self.roda(self.rc4, ["--dry-run"])
        self.assertEqual((rc, criou), (0, False))
        rc, criou, _ = self.roda(self.muda(LOTE, b"\0"), ["--dry-run"])
        self.assertNotEqual(rc, 0)

    def test_d3_segunda_passagem(self):
        tmp = tempfile.mkdtemp(prefix="openpod_2x5_")
        a, b, c = (os.path.join(tmp, n) for n in ("a.bin", "b.bin", "c.bin"))
        with open(a, "wb") as f:
            f.write(self.rc4)
        ferr = os.path.join(RAIZ, "tools", FERRAMENTA)
        self.assertEqual(subprocess.run([sys.executable, ferr, "--in", a, "--out", b], cwd=RAIZ,
                                        capture_output=True).returncode, 0)
        self.assertNotEqual(subprocess.run([sys.executable, ferr, "--in", b, "--out", c], cwd=RAIZ,
                                           capture_output=True).returncode, 0)
        self.assertFalse(os.path.exists(c))

    def test_d3_saida_igual_ou_link(self):
        for tipo in ("mesmo", "symlink", "hardlink"):
            tmp = tempfile.mkdtemp(prefix="openpod_link5_")
            src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
            with open(src, "wb") as f:
                f.write(self.rc4)
            if tipo == "mesmo":
                dst = src
            else:
                (os.symlink if tipo == "symlink" else os.link)(src, dst)
            r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", FERRAMENTA),
                                "--in", src, "--out", dst], capture_output=True, cwd=RAIZ)
            self.assertNotEqual(r.returncode, 0, tipo)
            self.assertEqual(le(src), self.rc4, tipo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
