#!/usr/bin/env python3
# NÃO ALTERAR sem o arquiteto. O hash deste arquivo é conferido por tools/ci.sh
# (tests/PROTEGIDOS.sha256). Ficha: docs/tarefas/004-rc4-icones-barra-centro.md
"""
test_rc4.py — critérios de aceite da Reload 1.0 RC4 (ícones novos na home +
relógio, título e bateria no meio da barra).

Testa EFEITO na imagem. Constrói `reload_1.0_rc3` (catraca da RC3.1, aprovada
no aparelho) e `reload_1.0_rc4` a partir do ORIGINAL e confere byte a byte.

USO
    python3 tests/test_rc4.py

DEPENDÊNCIAS
    Python 3 + Pillow. Não abre o USB.
"""

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
import importlib.util

from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
SHA_ORIGINAL = "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f"
SHA_RC3 = "286e8ba8ed66f9fdb51af8d6c94a8dbc3e43513c6d554c85e2ea5f772363faa9"  # RC3.1, aprovada 2026-10-23

# --- barra: os três no meio (y 2 px acima). Endereço: (bytes na RC3, bytes na RC4)
CENTRO = {
    0x1217D6: (bytes.fromhex("0223"), bytes.fromhex("0023")),  # relógio align(1, 3, y) y 2 -> 0
    0x1226B6: (bytes.fromhex("0223"), bytes.fromhex("0023")),  # título  align(2, 6, y) y 2 -> 0
    0x12260E: (bytes.fromhex("0222"), bytes.fromhex("0022")),  # bateria set_pos(107, y) y 2 -> 0 (= fábrica)
}

# --- folha da home (128x160 INDEXED_8, paleta BGRA sem pré-inversão)
HOME_CAB, HOME_PAL, HOME_PX = 0x0CDD50, 0x0CDD5C, 0x0CE15C
LARG, ALT, BARRA = 128, 160, 16
HOME_FIM = HOME_PX + LARG * ALT
ASSET = os.path.join(RAIZ, "assets/IconesHome.png")
SHA_ASSET = "fbdd1dc714b1316b698cdf34bd1514595508f62250c5dc2da3fee910247d2b70"  # aprovado 2026-09-24
COR_TOPO, COR_BASE = (64, 70, 82), (14, 16, 19)

FERRAMENTAS = ("fab_barra_centro.py", "fab_icones_home.py")   # nomes e ordem fixados pela ficha

PERMITIDO_RC4 = [(a, a + len(v[1])) for a, v in CENTRO.items()] + [(HOME_PAL, HOME_FIM)]

PROIBIDAS = {
    "patch_logo.py", "patch_fundo_display.py", "patch_fundo_abertura.py",
    "patch_fundo_preto.py", "patch_nome_faixa.py", "patch_faixa_degrade.py",
    "patch_bateria_casca.py", "patch_bateria_verde.py", "patch_bateria_miolo.py",
    "relocate_lang_table.py", "aplica_textos.py",
    "patch_status_bar.py", "fix_status_bar.py", "patch_titulos.py",
    "patch_faixa_16px.py", "patch_faixa_alinha.py", "patch_faixa_cinza.py",
    "patch_home_barra.py", "patch_chrome_padrao.py",
    "patch_icones_home.py", "patch_bar_height.py",
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def constroi(receita, destino):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools/build.py"),
                        "--receita", receita, "--saida", destino],
                       capture_output=True, text=True, cwd=RAIZ)
    return r.returncode, r.stdout + r.stderr


def alvo_linha(y):
    t = y / (BARRA - 1)
    return tuple(round(COR_TOPO[k] + (COR_BASE[k] - COR_TOPO[k]) * t) for k in range(3))


def le(caminho):
    with open(caminho, "rb") as f:
        return f.read()


class RC4(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orig = le(ORIGINAL)
        assert sha(cls.orig) == SHA_ORIGINAL, "ORIGINAL nao confere — PARE"
        cls.tmp = tempfile.mkdtemp(prefix="openpod_test_rc4_")
        p3, p4 = os.path.join(cls.tmp, "rc3.bin"), os.path.join(cls.tmp, "rc4.bin")
        constroi("reload_1.0_rc3", p3)
        cls.rc4_rc, cls.rc4_log = constroi("reload_1.0_rc4", p4)
        cls.rc3 = le(p3) if os.path.exists(p3) else b""
        cls.rc4 = le(p4) if os.path.exists(p4) else b""

    # --- C0/C1
    def test_c0_receita_rc4_constroi(self):
        self.assertEqual(self.rc4_rc, 0, "build reload_1.0_rc4 falhou:\n" + self.rc4_log[-2000:])
        self.assertEqual(len(self.rc4), 0x200000)

    def test_c1_rc3_reprodutivel(self):
        self.assertEqual(sha(self.rc3), SHA_RC3, "a RC3.1 aprovada mudou — catraca")

    # --- C2: receita = RC3 + as duas ferramentas, nada proibido
    def test_c2_receita(self):
        spec = importlib.util.spec_from_file_location("build", os.path.join(RAIZ, "tools/build.py"))
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
        r3 = [t for t, _, _ in b.RECEITAS["reload_1.0_rc3"]]
        r4 = [t for t, _, _ in b.RECEITAS["reload_1.0_rc4"]]
        self.assertEqual(r4[:len(r3)], r3)
        self.assertEqual(tuple(r4[len(r3):]), FERRAMENTAS)
        self.assertFalse(set(r4) & PROIBIDAS, "ferramenta proibida na receita")
        self.assertEqual(sha(le(ASSET)), SHA_ASSET, "PNG dos ícones mudou")

    # --- C3: barra centralizada
    def test_c3_centro(self):
        for a, (rc3, novo) in CENTRO.items():
            self.assertEqual(self.rc3[a:a + len(rc3)], rc3, f"premissa RC3 em 0x{a:X}")
            self.assertEqual(self.rc4[a:a + len(novo)], novo, f"0x{a:X}")

    # --- C4: folha da home
    def test_c4_cabecalho_intocado(self):
        self.assertEqual(self.rc4[HOME_CAB:HOME_PAL], self.orig[HOME_CAB:HOME_PAL])

    def paleta(self):
        p = self.rc4[HOME_PAL:HOME_PX]
        return [(p[i * 4 + 2], p[i * 4 + 1], p[i * 4], p[i * 4 + 3]) for i in range(256)]

    def test_c4_paleta_alfa_e_degrade_exato(self):
        pal = self.paleta()
        self.assertTrue(all(c[3] == 255 for c in pal), "toda entrada com alfa 255")
        for y in range(BARRA):
            self.assertEqual(pal[y][:3], alvo_linha(y), f"entrada {y} != cor exata da linha {y}")

    def test_c4_barra_linhas_0_15(self):
        for y in range(BARRA):
            linha = self.rc4[HOME_PX + LARG * y:HOME_PX + LARG * (y + 1)]
            self.assertEqual(set(linha), {y}, f"linha {y} da barra deve ser toda indice {y}")

    def test_c4_icones_fieis_ao_png(self):
        pal = self.paleta()
        img = Image.open(ASSET).convert("RGB")
        self.assertEqual(img.size, (LARG, ALT))
        px = img.load()
        erro, n = 0, 0
        for y in range(BARRA, ALT):
            for x in range(LARG):
                i = self.rc4[HOME_PX + LARG * y + x]
                c, a = pal[i][:3], px[x, y]
                if a == (0, 0, 0):
                    self.assertEqual(c, (0, 0, 0), f"fundo preto do PNG virou {c} em ({x},{y})")
                erro += sum(abs(c[k] - a[k]) for k in range(3))
                n += 3
        self.assertLessEqual(erro / n, 2.0, f"erro medio {erro / n:.2f} por canal")

    # --- C5: segurança
    def test_c5_so_regioes_permitidas(self):
        fora = [i for i in range(len(self.orig))
                if self.rc3[i] != self.rc4[i]
                and not any(a <= i < b for a, b in PERMITIDO_RC4)]
        self.assertEqual(fora, [], f"escreveu fora do permitido: {[hex(x) for x in fora[:8]]}")

    def test_c5_bootloader_r1_psmp(self):
        dif = [i for i in range(len(self.orig)) if self.orig[i] != self.rc4[i]]
        self.assertGreaterEqual(min(dif), 0xE000)
        self.assertFalse(any(i >= 0x1FC000 for i in dif), "PSMP tocada")


class Recusa(unittest.TestCase):
    """D3: com premissa errada, a ferramenta recusa ANTES de escrever."""

    @classmethod
    def setUpClass(cls):
        cls.o = le(ORIGINAL)
        cls.tmp = tempfile.mkdtemp(prefix="openpod_recusa4_")
        p3 = os.path.join(cls.tmp, "rc3.bin")
        constroi("reload_1.0_rc3", p3)
        cls.rc3 = le(p3)

    def roda(self, ferramenta, entrada, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_r4_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(entrada)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", ferramenta),
                            "--in", src, "--out", dst] + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), le(src) == entrada

    def inverte(self, base, a):
        b = bytearray(base)
        b[a] ^= 0xFF
        return bytes(b)

    def confere_recusa(self, ferramenta, casos, extra=()):
        for nome, entrada in casos.items():
            rc, criou, intacta = self.roda(ferramenta, entrada, extra)
            self.assertNotEqual(rc, 0, f"{ferramenta} aceitou {nome}")
            self.assertFalse(criou, f"{ferramenta} criou saida com {nome}")
            self.assertTrue(intacta, f"{ferramenta} alterou a entrada com {nome}")

    def test_d3_ferramentas_existem(self):
        for f in FERRAMENTAS:
            self.assertTrue(os.path.exists(os.path.join(RAIZ, "tools", f)), f)

    def test_d3_centro_recusa(self):
        pontos = [0x1217D6, 0x1217D2, 0x1217D8, 0x1217DA,      # relógio: y, align, x, bl align
                  0x1226B6, 0x1226BA, 0x1226BE, 0x1226C0,      # título:  y, x, align, bl align
                  0x12260E, 0x122612, 0x122614]                # bateria: y, x, bl set_pos
        casos = {hex(a): self.inverte(self.rc3, a) for a in pontos}
        casos["truncado"] = self.rc3[:0x100000]
        casos["original"] = self.o            # só roda sobre a RC3 (título e bateria da RC3.1)
        self.confere_recusa("fab_barra_centro.py", casos)

    def test_d3_icones_recusa(self):
        pontos = [HOME_CAB, HOME_CAB + 11, HOME_PAL, HOME_PAL + 1023,
                  HOME_PX + LARG * BARRA, HOME_FIM - 1, HOME_PX + LARG * 80 + 64]
        casos = {hex(a): self.inverte(self.rc3, a) for a in pontos}
        b = bytearray(self.rc3)
        b[HOME_PX + 5] ^= 0xFF                 # linha 0 da barra não uniforme
        casos["barra_nao_uniforme"] = bytes(b)
        casos["truncado"] = self.rc3[:0x100000]
        self.confere_recusa("fab_icones_home.py", casos)

    def test_d3_icones_recusa_png_adulterado(self):
        tmp = tempfile.mkdtemp(prefix="openpod_png4_")
        png = os.path.join(tmp, "x.png")
        img = Image.open(ASSET).convert("RGB")
        img.putpixel((64, 80), (1, 2, 3))
        img.save(png)
        self.confere_recusa("fab_icones_home.py", {"png": self.rc3}, ["--png", png])

    def test_d3_aceita_a_rc3(self):
        for f in FERRAMENTAS:
            for extra in ((), ("--dry-run",)):
                rc, criou, _ = self.roda(f, self.rc3, extra)
                self.assertEqual(rc, 0, f"{f} {extra} recusou a RC3")
                self.assertEqual(criou, not extra, f"{f} {extra}")

    def test_d3_segunda_passagem_recusa(self):
        for f in FERRAMENTAS:
            tmp = tempfile.mkdtemp(prefix="openpod_2x4_")
            a, b, c = (os.path.join(tmp, n) for n in ("a.bin", "b.bin", "c.bin"))
            with open(a, "wb") as fh:
                fh.write(self.rc3)
            r1 = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", f), "--in", a, "--out", b],
                                capture_output=True, cwd=RAIZ)
            self.assertEqual(r1.returncode, 0, f)
            r2 = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", f), "--in", b, "--out", c],
                                capture_output=True, cwd=RAIZ)
            self.assertNotEqual(r2.returncode, 0, f"{f} rodou duas vezes")
            self.assertFalse(os.path.exists(c))

    def test_d3_saida_igual_ou_link_da_entrada(self):
        for f in FERRAMENTAS:
            for tipo in ("mesmo", "symlink", "hardlink"):
                tmp = tempfile.mkdtemp(prefix="openpod_link4_")
                src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
                with open(src, "wb") as fh:
                    fh.write(self.rc3)
                if tipo == "mesmo":
                    dst = src
                else:
                    (os.symlink if tipo == "symlink" else os.link)(src, dst)
                r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", f),
                                    "--in", src, "--out", dst], capture_output=True, cwd=RAIZ)
                self.assertNotEqual(r.returncode, 0, f"{f} aceitou saida {tipo}")
                self.assertEqual(le(src), self.rc3, f"{f} alterou a entrada ({tipo})")

    def test_d3_dry_run_recusa_adulterado(self):
        for f, a in (("fab_barra_centro.py", 0x1217D6), ("fab_icones_home.py", HOME_CAB)):
            rc, criou, _ = self.roda(f, self.inverte(self.rc3, a), ["--dry-run"])
            self.assertNotEqual(rc, 0, f)
            self.assertFalse(criou)


if __name__ == "__main__":
    unittest.main(verbosity=2)
