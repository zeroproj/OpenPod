#!/usr/bin/env python3
"""
test_reload_2_2.py — ficha 018: a Reload 2.2 e a 2.1 com a folha escura
de simbolos coloridos.

Prova o que a ficha pede:

1. a receita `reload_2.2` e a MESMA lista da `reload_2.1`, com uma unica
   diferenca: o passo `fab_icones_home.py` recebe
   `--png assets/IconesHome_escuro_colorido.png`;
2. a diferenca 2.2 x 2.1 (sem carimbo) fica SO na paleta e nos pixels da
   folha (`0x0CDD5C..0x0D315C`);
3. nenhum byte de codigo muda (lote `0x1A6000..0x1AB000`, `0xFF0C4`,
   `0x132242`);
4. nada abaixo de `0xE000`, nem no setor `0xD000`, nem na PSMP.

NAO roda no `tools/ci.sh`: e teste de aceite da ficha, rodado a mao.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA_21 = "956dffc18123fef465ffcf7811fc68ec4e7e50d9bc715510717625df166cadb4"
SHA_22 = "4fdd31c03ad6672ca0b15b141345b7559b2517afca19f54de0d73753f842f769"

# a folha da home: paleta + pixels
FOLHA = (0x0CDD5C, 0x0D315C)
PERMITIDO = (FOLHA,)

# regioes de codigo que tem de ficar byte a byte iguais
CODIGO = ((0x1A6000, 0x1AB000), (0xFF0C4, 0xFF0C5), (0x132242, 0x132243))


def sha(dados):
    return hashlib.sha256(dados).hexdigest()


def constroi(receita, destino):
    return subprocess.run(
        [sys.executable, os.path.join(RAIZ, "tools", "build.py"),
         "--receita", receita, "--saida", destino],
        capture_output=True, text=True, cwd=RAIZ)


class Reload22(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="openpod_018_", dir=RAIZ)
        cls.saidas = {}
        cls.rcs = {}
        for nome in ("reload_2.1", "reload_2.2"):
            destino = os.path.join(cls.tmp, nome + ".bin")
            cls.rcs[nome] = constroi(nome, destino)
            cls.saidas[nome] = b""
            if os.path.exists(destino):
                with open(destino, "rb") as f:
                    cls.saidas[nome] = f.read()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_09_estilos(self):
        # o padrao e o grafite continuam iguais aos de hoje; o escuro
        # colorido tem de sair igual ao PNG da previa aprovada.
        casos = [(None, "assets/IconesHome.png",
                  "fbdd1dc714b1316b698cdf34bd1514595508f62250c5dc2da3fee910247d2b70"),
                 ("grafite", "assets/IconesHome_grafite.png",
                  "1493e2a464089793b81a9705cc1ee40ba4ad84208387d66b355582e976db8544"),
                 ("escuro_colorido",
                  "assets/IconesHome_escuro_colorido.png",
                  "5eff7463214bd8004bce30352b660d75087bb3fa139731d52ab777bf57dffaa2")]
        for estilo, approved, esperado in casos:
            with self.subTest(estilo=estilo):
                saida = os.path.join(self.tmp, "folha.png")
                ampliada = os.path.join(self.tmp, "ampliada.png")
                env = dict(os.environ, GLIFO="255,255,255")
                env.pop("ESTILO", None)
                if estilo:
                    env["ESTILO"] = estilo
                r = subprocess.run(
                    [sys.executable, os.path.join(RAIZ, "tools",
                                                  "desenha_icones_home.py"),
                     saida, ampliada],
                    capture_output=True, text=True, cwd=RAIZ, env=env)
                self.assertEqual(r.returncode, 0, r.stderr[-2000:])
                with open(saida, "rb") as f:
                    self.assertEqual(sha(f.read()), esperado)
                with open(os.path.join(RAIZ, approved), "rb") as f:
                    self.assertEqual(sha(f.read()), esperado)

    def test_10_receita_difere_so_no_png(self):
        sys.path.insert(0, os.path.join(RAIZ, "tools"))
        import build as B
        velho = B.RECEITAS["reload_2.1"]
        novo = B.RECEITAS["reload_2.2"]
        self.assertEqual(len(velho), len(novo))
        diferentes = [(i, a, b) for i, (a, b) in enumerate(zip(velho, novo))
                      if a != b]
        self.assertEqual(len(diferentes), 1, diferentes)
        _, antes, depois = diferentes[0]
        self.assertEqual(antes[0], "fab_icones_home.py")
        self.assertEqual(depois[0], "fab_icones_home.py")
        self.assertEqual(depois[1],
                         ["--png",
                          "assets/IconesHome_escuro_colorido.png"])
        self.assertEqual(antes[2], depois[2])

    def test_11_imagens_construidas(self):
        for nome in ("reload_2.1", "reload_2.2"):
            self.assertEqual(
                self.rcs[nome].returncode, 0,
                self.rcs[nome].stdout[-2000:] + self.rcs[nome].stderr[-2000:])
            self.assertEqual(len(self.saidas[nome]), 0x200000, nome)
        self.assertEqual(sha(self.saidas["reload_2.1"]), SHA_21)
        self.assertEqual(sha(self.saidas["reload_2.2"]), SHA_22)

    def test_12_diferenca_so_na_folha(self):
        a = self.saidas["reload_2.1"]
        b = self.saidas["reload_2.2"]
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        self.assertTrue(dif, "a 2.2 nao mudou nada")
        fora = [i for i in dif
                if not any(ini <= i < fim for ini, fim in PERMITIDO)]
        self.assertEqual(fora, [])

    def test_13_codigo_intacto(self):
        a = self.saidas["reload_2.1"]
        b = self.saidas["reload_2.2"]
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        for ini, fim in CODIGO:
            self.assertEqual([i for i in dif if ini <= i < fim], [],
                             "mudou codigo em 0x%06X..0x%06X" % (ini, fim))

    def test_14_guardas(self):
        a = self.saidas["reload_2.1"]
        b = self.saidas["reload_2.2"]
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        self.assertEqual([i for i in dif if i < 0xE000], [],
                         "escreveu abaixo de 0xE000")
        self.assertEqual([i for i in dif if 0xD000 <= i < 0xE000], [],
                         "tocou o setor 0xD000")
        self.assertEqual([i for i in dif if i >= 0x1FC000], [],
                         "tocou a PSMP")


if __name__ == "__main__":
    unittest.main(verbosity=2)
