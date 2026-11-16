#!/usr/bin/env python3
"""
test_reload_2_2_1.py — ficha 019: a Reload 2.2.1 e a 2.2 com o limite de
tamanho da capa do album.

Prova o que a ficha pede:

1. a receita `reload_2.2.1` e a MESMA lista da `reload_2.2`, com uma unica
   diferenca: o passo `fab_limite_capa.py` com os limites 1000 px e
   512 KiB;
2. a diferenca 2.2.1 x 2.2 (sem carimbo) fica SO nos dois pontos do
   `carrega_capa` e nas duas rotinas da area livre do lote da capa;
3. capa dentro dos dois limites mostra os MESMOS pixels da 2.2;
4. capa acima de 1000 px (mas abaixo de 512 KiB) vira cinza depois do
   `jd_prepare`, sem `jd_decomp`;
5. capa acima de 512 KiB vira cinza antes de ler a imagem (sem
   `jd_prepare`);
6. nada vaza (tmp e FIL liberados, arquivo fechado) e nada toca abaixo de
   `0xE000`, o setor `0xD000` ou a PSMP.

NAO roda no `tools/ci.sh`: e teste de aceite da ficha, rodado a mao.
"""
import hashlib
import importlib.util
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu_rc7 as E  # noqa: E402
import gera_mp3 as G  # noqa: E402
from unicorn import UC_HOOK_CODE  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATIVOS = os.path.join(RAIZ, "tests/assets/rc7")
ORIGINAL = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
SHA_22 = "4fdd31c03ad6672ca0b15b141345b7559b2517afca19f54de0d73753f842f769"
SHA_22_1 = "e477c1e78ac1c88db58d29b030f35d7f11c8d90f45ec695a9b63392ea9936402"

sys.path.insert(0, os.path.join(RAIZ, "tools"))
import capa_album_asm as A  # noqa: E402
import limite_capa_asm as L  # noqa: E402

CRIA, TITULO = 0xDAA010, 0xDAA014
PH_DSC = 0xDA8000
HDR_64 = 0x08010004
TELA, ROT_CONT, ROT_TIT, ROT_LETRA = 0x5E000000, 0x5F000000, 0x5F000100, 0x5F000200
JD_PREP, JD_DEC = 0xD10B20, 0xD11090
PROIBIDAS = {"patch_icones_home.py", "patch_home_barra.py",
             "patch_cor_selecao.py", "patch_menu_text.py",
             "aplica_textos.py", "patch_nome_faixa.py"}


def sha(dados):
    return hashlib.sha256(dados).hexdigest()


def le(p):
    with open(p, "rb") as f:
        return f.read()


def ativo(n):
    return le(os.path.join(ATIVOS, n))


def constroi(receita, destino):
    return subprocess.run(
        [sys.executable, os.path.join(RAIZ, "tools", "build.py"),
         "--receita", receita, "--saida", destino],
        capture_output=True, text=True, cwd=RAIZ)


class Reload221(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="openpod_019_", dir=RAIZ)
        cls.saidas, cls.rcs = {}, {}
        for nome in ("reload_2.2", "reload_2.2.1"):
            destino = os.path.join(cls.tmp, nome + ".bin")
            cls.rcs[nome] = constroi(nome, destino)
            cls.saidas[nome] = le(destino) if os.path.exists(destino) else b""
        cls.audio = ativo("_audio_6s.mp3")
        cls.orig = le(ORIGINAL)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ------------------------------------------------------------ estatico
    def test_01_receita(self):
        spec = importlib.util.spec_from_file_location(
            "build", os.path.join(RAIZ, "tools/build.py"))
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
        velho = b.RECEITAS["reload_2.2"]
        novo = b.RECEITAS["reload_2.2.1"]
        self.assertEqual(len(novo), len(velho) + 1)
        self.assertEqual(novo[:len(velho)], velho)
        nome, args, _por = novo[-1]
        self.assertEqual(nome, "fab_limite_capa.py")
        self.assertEqual(args, ["--limite-px", "1000",
                                "--limite-bytes", str(512 * 1024)])
        self.assertFalse(set(x for x, _, _ in novo) & PROIBIDAS)
        self.assertIsNone(b.MAPA.get("fab_limite_capa.py"))

    def test_02_imagens(self):
        for nome in ("reload_2.2", "reload_2.2.1"):
            self.assertEqual(
                self.rcs[nome].returncode, 0,
                self.rcs[nome].stdout[-2000:] + self.rcs[nome].stderr[-2000:])
            self.assertEqual(len(self.saidas[nome]), 0x200000)
        self.assertEqual(sha(self.saidas["reload_2.2"]), SHA_22)
        self.assertEqual(sha(self.saidas["reload_2.2.1"]), SHA_22_1)

    def test_03_pontos_e_rotinas(self):
        a, b = self.saidas["reload_2.2"], self.saidas["reload_2.2.1"]
        self.assertEqual(a[L.P_BYTES:L.P_BYTES + 4], L.ORIG_BYTES)
        self.assertEqual(a[L.P_PX:L.P_PX + 4], L.ORIG_PX)
        self.assertEqual(a[L.LIVRE_INI:L.LIVRE_FIM],
                         b"\0" * (L.LIVRE_FIM - L.LIVRE_INI))
        self.assertEqual(A.desvio(b, L.P_BYTES),
                         ("bl", A.XIP + L.R_BYTES))
        self.assertEqual(A.desvio(b, L.P_PX), ("bl", A.XIP + L.R_PX))
        cod_b, cod_p = L.monta_rotinas()
        self.assertEqual(b[L.R_BYTES:L.R_BYTES + len(cod_b)], cod_b)
        self.assertEqual(b[L.R_PX:L.R_PX + len(cod_p)], cod_p)
        self.assertEqual(L.confere_rotinas(cod_b, cod_p), [])

    def test_04_diferenca_so_no_lote_da_capa(self):
        a, b = self.saidas["reload_2.2"], self.saidas["reload_2.2.1"]
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        cod_b, cod_p = L.monta_rotinas()
        permitido = ((L.P_BYTES, L.P_BYTES + 4), (L.P_PX, L.P_PX + 4),
                     (L.R_BYTES, L.R_BYTES + len(cod_b)),
                     (L.R_PX, L.R_PX + len(cod_p)))
        fora = [i for i in dif
                if not any(x <= i < y for x, y in permitido)]
        self.assertEqual(fora, [])
        self.assertEqual([i for i in dif if i < 0xE000], [])
        self.assertEqual([i for i in dif if 0xD000 <= i < 0xE000], [])
        self.assertEqual([i for i in dif if i >= 0x1FC000], [])

    # ------------------------------------------------------------ emulador
    def carrega(self, imagem, mp3):
        m = E.Maquina(imagem)
        log = self.instrumenta(m)
        tmp = m.aloca(0x2210, registra=False)
        path = b"0:/A/B.mp3"
        m.escreve(tmp + 0x110, path + b"\0")
        m.arquivos[path] = mp3
        m.u.mem_map(0xE000E000, 0x1000)
        m.falsas[0x00C43634] = lambda mq: 0
        vivos0 = dict(m.vivos)
        r = m.chama(0x00DAA256, (tmp,), tempo=180)
        px = m.le(tmp + 0x210, 0x2000)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.abertos, {}, "arquivo ficou aberto")
        self.assertEqual(m.vivos, vivos0, "vazou ou liberou memoria alheia")
        return r, px, log

    def instrumenta(self, m):
        log = []
        for a, nome in ((JD_PREP, "prepare"), (JD_DEC, "decomp")):
            m.u.hook_add(
                UC_HOOK_CODE,
                lambda uc, ad, tam, ud, nome=nome: log.append(nome),
                begin=a, end=a + 3)
        return log

    def test_05_dentro_do_limite_mesmos_pixels(self):
        casos = [("capa_a_300.jpg", ativo("capa_a_300.jpg")),
                 ("capa_b_500.jpg", ativo("capa_b_500.jpg")),
                 ("gerada_640", G.jpeg(640))]
        for nome, jpg in casos:
            with self.subTest(nome):
                mp3 = E.tag_id3(3, [E.apic(3, jpg)]) + self.audio
                r21, px21, log21 = self.carrega(self.saidas["reload_2.2"], mp3)
                self.assertEqual((r21, log21), (1, ["prepare", "decomp"]))
                r, px, log = self.carrega(self.saidas["reload_2.2.1"], mp3)
                self.assertEqual((r, log), (1, ["prepare", "decomp"]))
                self.assertEqual(px, px21, "a 2.2.1 mudou os pixels da 2.2")
                self.assertTrue(any(px))
                if nome != "capa_b_500.jpg":
                    # a 500 px o B7 escolhe a escala 3 (minimo 56), e a
                    # referencia da fabrica usa 64; o que importa aqui e a
                    # 2.2.1 mostrar os mesmos pixels da 2.2.
                    self.assertEqual(px, E.referencia(self.orig, jpg))

    def test_06_acima_do_limite_px(self):
        jpg = G.jpeg(1200)
        self.assertGreater(len(jpg), 0)
        self.assertLessEqual(len(jpg), L.LIMITE_BYTES)
        mp3 = E.tag_id3(3, [E.apic(3, jpg)]) + self.audio
        r, px, log = self.carrega(self.saidas["reload_2.2.1"], mp3)
        self.assertEqual((r, px, log), (0, b"\0" * 0x2000, ["prepare"]))

    def test_07_acima_do_limite_bytes(self):
        for lado in (1500, 3000):
            with self.subTest(lado=lado):
                jpg = G.jpeg(lado)
                self.assertGreater(len(jpg), L.LIMITE_BYTES)
                mp3 = E.tag_id3(3, [E.apic(3, jpg)]) + self.audio
                r, px, log = self.carrega(self.saidas["reload_2.2.1"], mp3)
                self.assertEqual((r, px, log), (0, b"\0" * 0x2000, []),
                                 "leu a imagem antes do limite")

if __name__ == "__main__":
    unittest.main(verbosity=2)
