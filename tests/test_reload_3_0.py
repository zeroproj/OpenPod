#!/usr/bin/env python3
"""
test_reload_3_0.py — ficha 021: a Reload 3.0 e a 2.2.1 com o menu Apps.

Prova o que a ficha pede:

1. a receita `reload_3.0` e a MESMA lista da `reload_2.2.1`, com dois
   passos novos: o destino do indice 5 e o glifo Apps na folha;
2. a diferenca 3.0 x 2.2.1 (sem carimbo) fica so no bloco do indice 5, no
   id do rotulo 5 (4 -> 159) e nos pixels do icone 5;
3. o indice 5 da home leva a pagina 0x53 (o menu Apps), e a 0x52 e o
   "Desligar sozinho" — a ficha escreve 0x52, mas a medida e 0x53;
4. os outros oito icones continuam com o destino de fabrica;
5. a folha muda so no icone 5; a paleta da 2.2 fica intocada;
6. nada abaixo de 0xE000, nem no setor 0xD000, nem na PSMP;
7. o salto novo e Thumb, o rotulo 5 usa o id 159 de fabrica e o texto
   existe em todas as tabelas de idioma, sem realocar tabela nenhuma.

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

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
SHA_22_1 = "e477c1e78ac1c88db58d29b030f35d7f11c8d90f45ec695a9b63392ea9936402"
SHA_3_0 = "43aaf5d51c364e03f9934aba0348230dda4911c2e7264c34555f69554c36ec32"

XIP = 0xC00000
STUB = 0x1011AE                    # offset do bloco do indice 5
STUB_XIP = XIP + STUB
STUB_FAB = bytes.fromhex("fdf7b1fa0028c0d00020")
STUB_NOVO = bytes.fromhex("53230022022101201ce0")
TAIL = 0xD011F2
TAIL_OFF = TAIL - XIP
TAIL_BYTES = bytes.fromhex("bde8f0410cf073bc")
TBH = 0xD00FBE                     # tabela do `tbh` de page1_process
TBH_ENTRY5 = TBH + 10
PAGINA = 0x53
PAGINA_ERRADA = 0x52

ID_NOVO = 159
ROTULO = 0x486D8
ROTULOS = (1, 3, 5, 6, 2, 4, 9, 10, 8)

# 0x48774 aponta para o nome PT; 0x48778..0x48798 para as 9 tabelas.
VETOR = tuple(range(0x48774, 0x48774 + 10 * 4, 4))
TABELAS = (
    ("EN", 0xC52AA4),
    ("ZH", 0xC523E4),
    ("FR", 0xC52E04),
    ("DE", 0xC52744),
    ("IT", 0xC534C4),
    ("ES", 0xC53EE4),
    ("HE", 0xC53164),
    ("NL", 0xC53824),
    ("PT", 0xC53B84),
)
NOME_PT = 0xC54244

SHEET_2_2 = ("751ca714aeeb4c4810a52334b287fe6db359aa866e398f746f5e7734"
             "d6b4d742")
HOME_PAL, HOME_PX, HOME_FIM = 0x0CDD5C, 0x0CE15C, 0x0D315C
HOME_LARG, HOME_ALT = 128, 160
CAIXA_ICONE5 = (88, 70, 121, 101)

PROIBIDAS = {"patch_icones_home.py", "patch_home_barra.py",
             "patch_cor_selecao.py", "patch_menu_text.py",
             "aplica_textos.py", "patch_nome_faixa.py"}


def sha(dados):
    return hashlib.sha256(dados).hexdigest()


def le(p):
    with open(p, "rb") as f:
        return f.read()


def u32(d, off):
    return struct.unpack_from("<I", d, off)[0]


def u16(d, off):
    return struct.unpack_from("<H", d, off)[0]


def texto(d, p):
    q = p - XIP
    return bytes(d[q:d.find(b"\0", q)])


def constroi(receita, destino):
    return subprocess.run(
        [sys.executable, os.path.join(RAIZ, "tools", "build.py"),
         "--receita", receita, "--saida", destino, "--sem-validar"],
        capture_output=True, text=True, cwd=RAIZ)


def bl_alvo(d, endereco):
    """Decodifica um `bl` de 32 bits em `endereco` (XIP) -> alvo XIP."""
    h1, h2 = struct.unpack_from("<HH", d, endereco - XIP)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xD000) != 0xD000:
        return None
    s = (h1 >> 10) & 1
    j1 = (h2 >> 13) & 1
    j2 = (h2 >> 11) & 1
    i1 = 1 ^ (j1 ^ s)
    i2 = 1 ^ (j2 ^ s)
    imm = ((s << 24) | (i1 << 23) | (i2 << 22)
           | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1))
    if s:
        imm -= 1 << 25
    return (endereco + 4 + imm) & 0xFFFFFFFF


class Reload30(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="openpod_021_", dir=RAIZ)
        cls.saidas, cls.rcs = {}, {}
        for nome in ("reload_2.2.1", "reload_3.0"):
            destino = os.path.join(cls.tmp, nome + ".bin")
            cls.rcs[nome] = constroi(nome, destino)
            cls.saidas[nome] = le(destino) if os.path.exists(destino) else b""
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
        velho = b.RECEITAS["reload_2.2.1"]
        novo = b.RECEITAS["reload_3.0"]
        self.assertEqual(len(novo), len(velho) + 2)
        self.assertEqual(novo[:len(velho)], velho)
        nome, args, _por = novo[-2]
        self.assertEqual(nome, "fab_apps_home.py")
        self.assertEqual(args, [])
        nome, args, _por = novo[-1]
        self.assertEqual(nome, "fab_icones_home_apps.py")
        self.assertIn("--png", args)
        self.assertIn("assets/IconesHome_escuro_colorido_apps.png", args)
        self.assertNotIn("fab_apps_home.py", b.MAPA)
        self.assertIsNone(b.MAPA.get("fab_icones_home_apps.py"))
        self.assertFalse(any("relocate_lang_table" in x for x, _, _ in novo))
        self.assertFalse(set(x for x, _, _ in novo) & PROIBIDAS)

    def test_02_imagens(self):
        for nome in ("reload_2.2.1", "reload_3.0"):
            self.assertEqual(
                self.rcs[nome].returncode, 0,
                self.rcs[nome].stdout[-2000:] + self.rcs[nome].stderr[-2000:])
            self.assertEqual(len(self.saidas[nome]), 0x200000)
        self.assertEqual(sha(self.saidas["reload_2.2.1"]), SHA_22_1)
        self.assertEqual(sha(self.saidas["reload_3.0"]), SHA_3_0)

    def test_03_indice_5_leva_ao_apps_0x53(self):
        a, b = self.saidas["reload_2.2.1"], self.saidas["reload_3.0"]
        self.assertEqual(u16(self.orig, TBH_ENTRY5 - XIP), 0x00F8)
        self.assertEqual(TBH + 2 * 0x00F8, STUB_XIP)
        self.assertEqual(a[STUB:STUB + 10], STUB_FAB)
        self.assertEqual(b[STUB:STUB + 10], STUB_NOVO)
        h = u16(b, STUB + 8)
        self.assertEqual(h & 0xF800, 0xE000)
        imm = h & 0x7FF
        if imm & 0x400:
            imm -= 0x800
        self.assertEqual(STUB_XIP + 8 + 4 + imm * 2, TAIL)
        self.assertEqual(b[TAIL_OFF:TAIL_OFF + 8], TAIL_BYTES)
        self.assertEqual(a[TAIL_OFF:TAIL_OFF + 8], TAIL_BYTES)
        self.assertEqual(PAGINA, 0x53)
        # a pagina 0x53 e a `page_home_menu_create`; a 0x52 e o
        # `page_set_timershut_time_create`. A tabela do `view_page_create`
        # e indexada por pagina-1 (TBB em 0xD23B34, base 0xD23B38).
        tbb = 0xD23B38
        alvo53 = tbb + 2 * a[tbb - XIP + 0x52]
        alvo52 = tbb + 2 * a[tbb - XIP + 0x51]
        self.assertEqual(bl_alvo(a, alvo53), 0xD2F0A0)
        self.assertEqual(bl_alvo(a, alvo52), 0xD3CAA8)
        self.assertEqual(PAGINA_ERRADA, 0x52)

    def test_04_outros_icones(self):
        a, b = self.saidas["reload_2.2.1"], self.saidas["reload_3.0"]
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        self.assertEqual([i for i in dif
                          if TBH - XIP <= i < STUB], [])
        self.assertEqual([i for i in dif
                          if STUB + 10 <= i < TAIL_OFF], [])
        for i in range(9):
            if i == 5:
                continue
            ea = TBH - XIP + 2 * i
            eb = TBH - XIP + 2 * i
            self.assertEqual(a[ea:ea + 2], b[eb:eb + 2])
            alvo = TBH + 2 * u16(a, ea)
            self.assertEqual(a[alvo - XIP:alvo - XIP + 10],
                             b[alvo - XIP:alvo - XIP + 10],
                             f"indice {i} mudou de bloco")

    def test_05_folha_so_icone_5(self):
        a, b = self.saidas["reload_2.2.1"], self.saidas["reload_3.0"]
        self.assertEqual(sha(a[HOME_PAL:HOME_FIM]), SHEET_2_2)
        self.assertEqual(b[HOME_PAL:HOME_PX], a[HOME_PAL:HOME_PX])
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        px = [i for i in dif if HOME_PX <= i < HOME_FIM]
        self.assertTrue(px, "o icone 5 nao mudou")
        xs, ys = [], []
        for i in px:
            xs.append((i - HOME_PX) % HOME_LARG)
            ys.append((i - HOME_PX) // HOME_LARG)
        self.assertGreaterEqual(min(xs), CAIXA_ICONE5[0])
        self.assertGreaterEqual(min(ys), CAIXA_ICONE5[1])
        self.assertLess(max(xs) + 1, CAIXA_ICONE5[2])
        self.assertLess(max(ys) + 1, CAIXA_ICONE5[3])
        self.assertEqual([i for i in dif
                          if 0x0CDD50 <= i < HOME_PAL], [])

    def test_06_id_159_e_vetor_de_idiomas(self):
        a, b = self.saidas["reload_2.2.1"], self.saidas["reload_3.0"]
        self.assertEqual(tuple(u32(a, 0x486C4 + 4 * i) for i in range(9)),
                         ROTULOS)
        self.assertEqual(u32(a, ROTULO), 4)
        self.assertEqual(u32(b, ROTULO), ID_NOVO)
        self.assertEqual(tuple(u32(b, 0x486C4 + 4 * i) for i in range(9)),
                         ROTULOS[:5] + (ID_NOVO,) + ROTULOS[6:])
        # os 10 ponteiros do vetor de idiomas: o primeiro e o nome PT,
        # os outros 9 sao as tabelas. Nenhum foi repontado.
        self.assertEqual(len(VETOR), 10)
        self.assertEqual(tuple(u32(a, off) for off in VETOR),
                         (NOME_PT,) + tuple(base for _, base in TABELAS))
        self.assertEqual(tuple(u32(b, off) for off in VETOR),
                         tuple(u32(a, off) for off in VETOR))
        for off in VETOR:
            self.assertEqual(texto(a, u32(a, off)), texto(b, u32(b, off)))
        # id 159 aponta para texto valido nas 9 tabelas, sem tocar nelas.
        for nome, base in TABELAS:
            off = base - XIP + 4 * ID_NOVO
            self.assertEqual(u32(a, off), u32(b, off))
            self.assertGreaterEqual(u32(b, off), XIP)
            self.assertLess(u32(b, off), XIP + len(b))
            self.assertTrue(texto(b, u32(b, off)))
            self.assertEqual(a[base - XIP:base - XIP + 4 * 216],
                             b[base - XIP:base - XIP + 4 * 216])
        self.assertEqual(texto(b, u32(b, 0xC53B84 - XIP + 4 * ID_NOVO)),
                         b"Aplicativos")
        self.assertEqual(texto(b, u32(b, 0xC52AA4 - XIP + 4 * ID_NOVO)),
                         b"APP")
        self.assertEqual(texto(b, u32(b, 0xC53824 - XIP + 4 * ID_NOVO)),
                         b"Toepassing")
        self.assertEqual(texto(b, u32(b, 0xC523E4 - XIP + 4 * ID_NOVO)),
                         "应用".encode())
        self.assertEqual(b[0x1A3600:0x1A3D00], b"\xff" * 0x700)
        self.assertEqual(b[0x1A3600:0x1A3D00], a[0x1A3600:0x1A3D00])

    def test_07_seguranca_e_thumb(self):
        a, b = self.saidas["reload_2.2.1"], self.saidas["reload_3.0"]
        dif = [i for i in range(len(a)) if a[i] != b[i]]
        self.assertEqual([i for i in dif if i < 0xE000], [])
        self.assertEqual([i for i in dif if 0xD000 <= i < 0xE000], [])
        self.assertEqual([i for i in dif if i >= 0x1FC000], [])
        self.assertEqual(b[:0xE000], self.orig[:0xE000])
        self.assertEqual(b[0x1FC000:], self.orig[0x1FC000:])
        permitido = [
            (STUB, STUB + len(STUB_NOVO)),
            (ROTULO, ROTULO + 4),
            (HOME_PX + CAIXA_ICONE5[1] * HOME_LARG + CAIXA_ICONE5[0],
             HOME_PX + CAIXA_ICONE5[3] * HOME_LARG + CAIXA_ICONE5[2]),
        ]
        fora = [i for i in dif
                if not any(x <= i < y for x, y in permitido)]
        self.assertEqual(fora, [])
        self.assertEqual(TAIL % 2, 0)
        self.assertEqual(STUB_XIP % 2, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
