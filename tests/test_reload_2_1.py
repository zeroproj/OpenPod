#!/usr/bin/env python3
"""
test_reload_2_1.py — ficha 017: a Reload 2.1 e a 2.0 com a folha em grafite.

Prova o que a ficha pede:

1. a receita `reload_2.1` e a MESMA lista da `reload_2.0`, com uma unica
   diferenca: o passo `fab_icones_home.py` recebe
   `--png assets/IconesHome_grafite.png`;
2. a diferenca 2.1 x 2.0 (sem carimbo) fica SO na paleta e nos pixels da
   folha (`0x0CDD5C..0x0D315C`, e onde a `fab_home_moldura` regrava a folha,
   `0x0CE000..0x0D2000`);
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
SHA_20 = "26ffa2721afa73a4109158a3cac66170f97858192876893c7972e7a002b2073d"

# a folha da home: paleta + pixels. A segunda faixa e onde a moldura
# reescreve a folha (interseccao com a primeira).
FOLHA = (0x0CDD5C, 0x0D315C)
MOLDURA = (0x0CE000, 0x0D2000)
PERMITIDO = (FOLHA, MOLDURA)

# regioes de codigo que tem de ficar byte a byte iguais
CODIGO = ((0x1A6000, 0x1AB000), (0xFF0C4, 0xFF0C5), (0x132242, 0x132243))


def sha(dados):
    return hashlib.sha256(dados).hexdigest()


def constroi(receita, destino):
    return subprocess.run(
        [sys.executable, os.path.join(RAIZ, "tools", "build.py"),
         "--receita", receita, "--saida", destino],
        capture_output=True, text=True, cwd=RAIZ)


class Reload21(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="openpod_017_", dir=RAIZ)
        cls.saidas = {}
        cls.rcs = {}
        for nome in ("reload_2.0", "reload_2.1"):
            destino = os.path.join(cls.tmp, nome + ".bin")
            cls.rcs[nome] = constroi(nome, destino)
            cls.saidas[nome] = b""
            if os.path.exists(destino):
                with open(destino, "rb") as f:
                    cls.saidas[nome] = f.read()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_09_estilo_padrao_intacto(self):
        # sem ESTILO a folha tem de sair igual a de hoje; com ESTILO=grafite,
        # igual ao PNG versionado. As duas saidas sao refeitas aqui.
        casos = [(None, "assets/IconesHome.png",
                  "fbdd1dc714b1316b698cdf34bd1514595508f62250c5dc2da3fee910247d2b70"),
                 ("grafite", "assets/IconesHome_grafite.png",
                  "1493e2a464089793b81a9705cc1ee40ba4ad84208387d66b355582e976db8544")]
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
        velho = B.RECEITAS["reload_2.0"]
        novo = B.RECEITAS["reload_2.1"]
        self.assertEqual(len(velho), len(novo))
        diferentes = [(i, a, b) for i, (a, b) in enumerate(zip(velho, novo))
                      if a != b]
        self.assertEqual(len(diferentes), 1, diferentes)
        _, antes, depois = diferentes[0]
        self.assertEqual(antes[0], "fab_icones_home.py")
        self.assertEqual(depois[0], "fab_icones_home.py")
        self.assertEqual(depois[1],
                         ["--png", "assets/IconesHome_grafite.png"])
        self.assertEqual(antes[2], depois[2])

    def test_11_imagens_construidas(self):
        for nome in ("reload_2.0", "reload_2.1"):
            self.assertEqual(
                self.rcs[nome].returncode, 0,
                self.rcs[nome].stdout[-2000:] + self.rcs[nome].stderr[-2000:])
            self.assertEqual(len(self.saidas[nome]), 0x200000, nome)
        self.assertEqual(sha(self.saidas["reload_2.0"]), SHA_20)

    def test_12_diferenca_so_na_folha(self):
        a = self.saidas["reload_2.0"]
        b = self.saidas["reload_2.1"]
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        self.assertTrue(dif, "a 2.1 nao mudou nada")
        fora = [i for i in dif
                if not any(ini <= i < fim for ini, fim in PERMITIDO)]
        self.assertEqual(fora, [])

    def test_13_codigo_intacto(self):
        a = self.saidas["reload_2.0"]
        b = self.saidas["reload_2.1"]
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        for ini, fim in CODIGO:
            self.assertEqual([i for i in dif if ini <= i < fim], [],
                             "mudou codigo em 0x%06X..0x%06X" % (ini, fim))

    def test_14_guardas(self):
        a = self.saidas["reload_2.0"]
        b = self.saidas["reload_2.1"]
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        self.assertEqual([i for i in dif if i < 0xE000], [],
                         "escreveu abaixo de 0xE000")
        self.assertEqual([i for i in dif if 0xD000 <= i < 0xE000], [],
                         "tocou o setor 0xD000")
        self.assertEqual([i for i in dif if i >= 0x1FC000], [],
                         "tocou a PSMP")


if __name__ == "__main__":
    unittest.main(verbosity=2)
