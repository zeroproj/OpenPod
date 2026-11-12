#!/usr/bin/env python3
"""
test_reload_2_0.py — ficha 016: a OpenPod Reload 2.0 e o B7b byte a byte.

Prova duas coisas que a ficha pede:

1. a receita `reload_2.0` e a MESMA lista da `reload_1.0_rc7_diag_b7b`;
2. a imagem gerada por ela tem o sha do B7b sem carimbo (`26ffa272…`).

E roda o `carrega_capa` do B7b no emulador para os tipos de capa da pergunta
4: baseline (v2.3/v2.4/cabecalho estendido) mostra a capa; progressiva, PNG,
sem capa, sem tag e menor que 56 px devolvem 0 (o `envia_path` manda o
quadrado cinza).

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
SHA_B7B = "26ffa2721afa73a4109158a3cac66170f97858192876893c7972e7a002b2073d"
ATIVOS = os.path.join(RAIZ, "tests", "assets", "rc7")


def sha(dados):
    return hashlib.sha256(dados).hexdigest()


class Reload20(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="openpod_016_", dir=RAIZ)
        cls.saida = os.path.join(cls.tmp, "reload_2.0.bin")
        cls.rc = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "tools", "build.py"),
             "--receita", "reload_2.0", "--saida", cls.saida],
            capture_output=True, text=True, cwd=RAIZ)
        cls.imagem = b""
        if os.path.exists(cls.saida):
            with open(cls.saida, "rb") as f:
                cls.imagem = f.read()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_10_receita_e_a_mesma_do_b7b(self):
        sys.path.insert(0, os.path.join(RAIZ, "tools"))
        import build as B
        self.assertEqual(B.RECEITAS["reload_2.0"],
                         B.RECEITAS["reload_1.0_rc7_diag_b7b"])

    def test_11_sha_sem_carimbo(self):
        self.assertEqual(self.rc.returncode, 0,
                         self.rc.stdout[-2000:] + self.rc.stderr[-2000:])
        self.assertEqual(len(self.imagem), 0x200000)
        self.assertEqual(sha(self.imagem), SHA_B7B)

    def test_12_capa_por_tipo(self):
        sys.path.insert(0, os.path.join(RAIZ, "tests"))
        import emu_rc7 as E

        def carrega(mp3):
            m = E.Maquina(self.imagem)
            tmp = m.aloca(0x2210, registra=False)
            path = b"0:/A/B.mp3"
            m.escreve(tmp + 0x110, path + b"\0")
            m.arquivos[path] = mp3
            m.u.mem_map(0xE000E000, 0x1000)
            m.falsas[0x00C43634] = lambda mq: 0
            r = m.chama(0x00DAA256, (tmp,), tempo=180)
            return m, r, m.le(tmp + 0x210, 0x2000)

        def ativo(nome):
            with open(os.path.join(ATIVOS, nome), "rb") as f:
                return f.read()

        # baseline v2.3, v2.4 e v2.4 com cabecalho estendido
        for nome in ("01_capa_v23.mp3", "02_capa_v24.mp3",
                     "03_capa_v24_cabecalho_estendido.mp3"):
            m, r, px = carrega(ativo(nome))
            self.assertEqual(m.erros, [], nome)
            self.assertEqual(r, 1, nome)
            self.assertTrue(any(px), nome)
            self.assertEqual(m.abertos, {}, nome)

        # progressiva, PNG, sem capa, sem tag, 48x48 -> cinza
        for nome in ("04_capa_progressiva.mp3", "05_capa_png.mp3",
                     "06_sem_capa.mp3", "07_sem_tag.mp3"):
            m, r, px = carrega(ativo(nome))
            self.assertEqual(m.erros, [], nome)
            self.assertEqual((r, px), (0, b"\0" * 0x2000), nome)
            self.assertEqual(m.abertos, {}, nome)

        jpeg48 = ativo("capa_pequena_48.jpg")
        mp3 = (E.tag_id3(3, [E.texto(3, b"TIT2", "48px"),
                             E.apic(3, jpeg48)])
               + ativo("_audio_6s.mp3"))
        m, r, px = carrega(mp3)
        self.assertEqual(m.erros, [])
        self.assertEqual((r, px), (0, b"\0" * 0x2000))
        self.assertEqual(m.abertos, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
