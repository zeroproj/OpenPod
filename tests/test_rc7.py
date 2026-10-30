#!/usr/bin/env python3
# NÃO ALTERAR sem o arquiteto. O hash deste arquivo é conferido por tools/ci.sh
# (tests/PROTEGIDOS.sha256). Ficha: docs/tarefas/007-rc7-capa-album.md
"""
test_rc7.py — critérios de aceite da Reload 1.0 RC7 (capa do álbum, ID3v2 APIC,
64x64 na Tocando Agora; sem capa → quadrado cinza com nota).

Constrói `reload_1.0_rc6` (catraca) e `reload_1.0_rc7` a partir do ORIGINAL e
RODA as rotinas novas no unicorn (tests/emu_rc7.py), com o TJpgDec da fábrica
de verdade e stubs só para heap, FatFs, caminho da faixa e LVGL.

USO
    python3 tests/test_rc7.py

DEPENDÊNCIAS
    Python 3 + capstone + unicorn (pip install --user unicorn). Não abre o USB.
"""

import hashlib
import importlib.util
import os
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu_rc7 as E  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATIVOS = os.path.join(RAIZ, "tests/assets/rc7")
ORIGINAL = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
SHA_ORIGINAL = "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f"
SHA_RC6 = "af3a2b6d8aaa1bf9d709c20e3ccd8d3f1aeb37cc6843a6070938e122488f4bc8"  # aprovada 2026-10-30
XIP = 0x00C00000

LOTE, LOTE_TAM = 0x1A8000, 0x3000
PH_DSC, PH_PX = 0xDA8000, 0xDA8010                   # quadrado cinza com nota (flash)
CRIA, TITULO, APAGA = 0xDAA010, 0xDAA014, 0xDAA018    # tabela de entradas (b.w)
HDR_64 = 0x08010004                                   # cf 4 TRUE_COLOR, w 64, h 64
GANCHO_BL = (0x131EB6, 0xD5D850, CRIA)                # lv_img_create do fundo -> CRIA
GANCHO_B = (0x13225E, 0xD5ED94, TITULO)               # b.w lv_label_set_text -> TITULO
TAMANHO = {0x131E80: (b"\x30\x20", b"\x34\x20"),      # lv_mem_alloc(0x30) -> 0x34
           0x131E9E: (b"\x30\x22", b"\x34\x22")}      # memset(.., 0x30)  -> 0x34
EXT_MAX, PICO_MAX = 0x2400, 0x1800
FERRAMENTAS = ("fab_capa_album.py",)
PROIBIDAS = {"patch_icones_home.py", "patch_home_barra.py", "patch_cor_selecao.py",
             "patch_menu_text.py", "aplica_textos.py", "patch_nome_faixa.py"}
SHA_ATIVOS = {
    "_audio_6s.mp3": "53beb9085b385cd111b5335ad6a8c43c4d0b6002191c50d423aeb80a67e7325b",
    "01_capa_v23.mp3": "2ec77d043aedfaa634af69e2a1792b213ca5da28975e63ed7a3d2c778b65d244",
    "02_capa_v24.mp3": "02613f4f6284f8bdcab15ec3df4ea8d377443a5189648e8a12e8366788ae735d",
    "03_capa_v24_cabecalho_estendido.mp3": "1bee1032d06d4fbde02e861c13aa45b013ecdc79d29525efa6a00352d3e5b526",
    "04_capa_progressiva.mp3": "a1dc5d8b860624db81b0409587560b9ecdc1e51e4d2ac37067c39b70fb9e776a",
    "05_capa_png.mp3": "5577de23365b73b33df557a78620c13c90d1d2dcb277e047e66586642b39aa74",
    "06_sem_capa.mp3": "5314bdee98595469f90f2a774541f43f6f1fe634cd18d011a4a7473d78a3657f",
    "07_sem_tag.mp3": "53beb9085b385cd111b5335ad6a8c43c4d0b6002191c50d423aeb80a67e7325b",
    "capa_a_300.jpg": "f377e63ab8c36bfbfa2ab3377197f0316430ee41a584c299b8b017240fd10f61",
    "capa_a_progressiva.jpg": "770a858a0abb6c7f35a492332eed6439b4639bfd7ab3d52b89710ce2893049e3",
    "capa_b_500.jpg": "8d52ddaaa03ecffa1020256ba0b0e97aed1c44bd6606a52e67f0a64e7a2cba92",
    "capa_c_200x120.jpg": "802e23dd1a1bc2da997201ce52acdaf0019cb3ac47d7d7b7e0987478de3c1fce",
    "capa_pequena_48.jpg": "8f4e33cb6adf834f101ba41da8778049e0a355a3c346a7eccf7b2cdaddf9d1b3",
    "capa_a.png": "7729fb78e72f14234ad220260f39ee60a7318a08e2774aa47c9e0315ed78b784",
    "placeholder_64x64.rgb565swap": "a2609171002492a88383fc5b506f24a0ef47fcda3949908fed320459e21b0bac",
}
TELA, ROT_CONT, ROT_TIT, ROT_LETRA = 0x5E000000, 0x5F000000, 0x5F000100, 0x5F000200


def sha(b):
    return hashlib.sha256(b).hexdigest()


def le(p):
    with open(p, "rb") as f:
        return f.read()


def ativo(n):
    return le(os.path.join(ATIVOS, n))


def constroi(receita, destino):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools/build.py"),
                        "--receita", receita, "--saida", destino],
                       capture_output=True, text=True, cwd=RAIZ)
    return r.returncode, r.stdout + r.stderr


def desvio(b, a):
    """Alvo de BL (T1) ou B.W (T4) em `a` (offset no arquivo); None se não for."""
    h1, h2 = struct.unpack_from("<HH", b, a)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xD000) not in (0xD000, 0x9000):
        return None
    S = (h1 >> 10) & 1
    I1, I2 = 1 - (((h2 >> 13) & 1) ^ S), 1 - (((h2 >> 11) & 1) ^ S)
    off = (S << 24) | (I1 << 23) | (I2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if S:
        off -= 1 << 25
    return ("bl" if h2 & 0x4000 else "b.w"), XIP + a + 4 + off


class Base(unittest.TestCase):

    _imgs = None   # construídas uma vez para todas as classes

    @classmethod
    def setUpClass(cls):
        cls.orig = le(ORIGINAL)
        assert sha(cls.orig) == SHA_ORIGINAL, "ORIGINAL nao confere — PARE"
        if Base._imgs is None:
            tmp = tempfile.mkdtemp(prefix="openpod_test_rc7_")
            p6, p7 = os.path.join(tmp, "rc6.bin"), os.path.join(tmp, "rc7.bin")
            constroi("reload_1.0_rc6", p6)
            rc, log = constroi("reload_1.0_rc7", p7)
            Base._imgs = (rc, log, le(p6) if os.path.exists(p6) else b"",
                          le(p7) if os.path.exists(p7) else b"")
        cls.rc7_rc, cls.rc7_log, cls.rc6, cls.rc7 = Base._imgs


class Arnes(unittest.TestCase):
    """O arnês e os ativos (verdes já na RC6: provam que o teste mede certo)."""

    def test_a0_ativos(self):
        for n, h in SHA_ATIVOS.items():
            self.assertEqual(sha(ativo(n)), h, n)

    def test_a1_tjpgdec_da_fabrica(self):
        orig = le(ORIGINAL)
        w, h, s, img = E.decodifica_fabrica(orig, ativo("capa_b_500.jpg"))
        self.assertEqual((w, h, s, len(img)), (500, 500, 2, 125 * 125))
        # CONFIRMADO: o jd_prepare desta build ACEITA progressivo (lixo) -> a recusa é nossa
        self.assertIsNotNone(E.decodifica_fabrica(orig, ativo("capa_a_progressiva.jpg"))[3])
        self.assertEqual(len(E.referencia(orig, ativo("capa_c_200x120.jpg"))), 8192)

    def test_a2_guarda_e_stubs(self):
        m = E.Maquina(le(ORIGINAL))
        p = m.chama(0xCF7840, (1, 16))
        self.assertIn(p, m.vivos)
        m.chama(0xD08448)                                  # função da fábrica fora da lista
        self.assertTrue(any("fora do permitido" in e for e in m.erros), m.erros)


class Estatico(Base):

    def test_c0_constroi(self):
        self.assertEqual(self.rc7_rc, 0, "build reload_1.0_rc7 falhou:\n" + self.rc7_log[-2000:])
        self.assertEqual(len(self.rc7), 0x200000)

    def test_c1_rc6_reprodutivel(self):
        self.assertEqual(sha(self.rc6), SHA_RC6, "a RC6 mudou — catraca")

    def test_c2_receita_e_lote(self):
        spec = importlib.util.spec_from_file_location("build", os.path.join(RAIZ, "tools/build.py"))
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
        r6 = [x for x, _, _ in b.RECEITAS["reload_1.0_rc6"]]
        r7 = [x for x, _, _ in b.RECEITAS["reload_1.0_rc7"]]
        self.assertEqual(r7[:len(r6)], r6)
        self.assertEqual(tuple(r7[len(r6):]), FERRAMENTAS)
        self.assertFalse(set(r7) & PROIBIDAS)
        self.assertEqual(b.MAPA.get("fab_capa_album.py"), (LOTE, LOTE_TAM))
        self.assertGreaterEqual(b.AREA_FIM, LOTE + LOTE_TAM, "lote fora da area vigiada")
        for nome, (ini, tam) in b.MAPA.items():
            if nome != "fab_capa_album.py":
                self.assertFalse(ini < LOTE + LOTE_TAM and LOTE < ini + tam, f"lote cruza {nome}")

    def test_c3_ganchos_e_tamanho(self):
        for a, fab, novo in (GANCHO_BL, GANCHO_B):
            tipo = "bl" if a == GANCHO_BL[0] else "b.w"
            self.assertEqual(desvio(self.orig, a), (tipo, fab), f"premissa 0x{a:X}")
            self.assertEqual(desvio(self.rc7, a), (tipo, novo), f"0x{a:X}")
        for a, (fab, novo) in TAMANHO.items():
            self.assertEqual(self.orig[a:a + 2], fab)
            self.assertEqual(self.rc7[a:a + 2], novo)

    def test_c3_tabela_e_placeholder(self):
        o = LOTE
        self.assertEqual(self.rc7[o:o + 12], struct.pack("<III", HDR_64, 8192, PH_PX))
        self.assertEqual(self.rc7[o + 12:o + 16], b"\xff" * 4)
        self.assertEqual(self.rc7[PH_PX - XIP:PH_PX - XIP + 8192], ativo("placeholder_64x64.rgb565swap"))
        for e in (CRIA, TITULO, APAGA):
            tipo, alvo = desvio(self.rc7, e - XIP) or (None, 0)
            self.assertEqual(tipo, "b.w", hex(e))
            self.assertTrue(APAGA + 4 <= alvo < XIP + LOTE + LOTE_TAM, f"0x{e:X} -> 0x{alvo:X}")

    def test_c5_so_regioes_permitidas(self):
        ok = [(LOTE, LOTE + LOTE_TAM)] + [(a, a + 2) for a in TAMANHO] + \
             [(GANCHO_BL[0], GANCHO_BL[0] + 4), (GANCHO_B[0], GANCHO_B[0] + 4)]
        fora = [i for i in range(len(self.rc6)) if self.rc6[i] != self.rc7[i]
                and not any(a <= i < b for a, b in ok)]
        self.assertEqual(fora, [], f"escreveu fora: {[hex(x) for x in fora[:8]]}")

    def test_c5_bootloader_r1_psmp(self):
        dif = [i for i in range(len(self.orig)) if self.orig[i] != self.rc7[i]]
        self.assertGreaterEqual(min(dif), 0xE000)
        self.assertFalse(any(i >= 0x1FC000 for i in dif))


class Comportamento(Base):
    """As rotinas rodando (unicorn) — o efeito na tela é o `src` do lv_img."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ref = {}

    def refer(self, nome):
        if nome not in self.ref:
            self.ref[nome] = E.referencia(self.orig, ativo(nome))
        return self.ref[nome]

    def aparelho(self, sem_ext=False):
        self.assertEqual(len(self.rc7), 0x200000, "sem imagem RC7")
        m = E.Maquina(self.rc7)
        pag, view = m.aloca(0x200, registra=False), m.aloca(0x34, registra=False)
        m.escreve32(E.PAGINAS, pag)
        m.escreve32(pag + 0xAC, view)
        m.escreve32(view + 0, ROT_CONT)
        m.escreve32(view + 4, ROT_TIT)
        m.escreve32(view + 8, ROT_LETRA)
        m.escreve(E.AUDIO, b"\x02")
        m.escreve32(E.AUDIO + 0x20, 7)
        if sem_ext:
            m.nega_aloc = lambda t: True
        salvos = [0x11110000 + i for i in range(8)]
        salvos[1] = view                                    # r5 = view na criação
        fundo = m.chama(CRIA, (TELA,), salvos=salvos)
        m.nega_aloc = None
        self.assertEqual(m.erros, [])
        cr = m.de("img_create")
        self.assertGreaterEqual(len(cr), 2)
        self.assertEqual(fundo, cr[0][2], "CRIA tem de devolver o fundo (1o lv_img da tela)")
        self.assertTrue(all(c[1] == TELA for c in cr[:2]))
        m.img, m.view = cr[1][2], view
        return m

    def titulo(self, m, dados, caminho=b"0:/MUSICA/teste.mp3", rotulo=ROT_TIT, nega=None):
        m.caminho = caminho
        m.arquivos = {caminho: dados} if dados is not None else {}
        txt = m.aloca(16, registra=False)
        m.escreve(txt, b"titulo\0")
        n0, vivos0 = len(m.chamadas), dict(m.vivos)
        m.pico = m.vivos_bytes
        base = m.vivos_bytes
        m.nega_aloc = nega
        m.chama(TITULO, (rotulo, txt))
        m.nega_aloc = None
        novas = m.chamadas[n0:]
        self.assertEqual(m.erros, [])
        self.assertEqual(novas[0], ("label_set_text", rotulo, txt), "set_text primeiro")
        self.assertEqual(len([c for c in novas if c[0] == "label_set_text"]), 1)
        self.assertEqual(m.abertos, {}, "arquivo ficou aberto")
        self.assertEqual(m.vivos, vivos0, "vazou ou liberou memoria alheia")
        self.assertLessEqual(m.pico - base, PICO_MAX, "pico de memoria")
        for c in novas:
            if c[0] == "f_open":
                self.assertEqual(c[2], caminho)
            if c[0] == "get_path":
                self.assertEqual(c[1:3], (2, 7))
        return novas

    def srcs(self, m, novas):
        return [c[2] for c in novas if c[0] == "img_set_src" and c[1] == m.img]

    def ve_capa(self, m, novas, nome_jpg):
        s = self.srcs(m, novas)
        self.assertTrue(s and s[-1] != PH_DSC, "devia mostrar a capa")
        hdr, tam, px = struct.unpack("<III", m.le(s[-1], 12))
        self.assertEqual((hdr, tam), (HDR_64, 8192))
        dono = [p for p, t in m.vivos.items() if p <= s[-1] and s[-1] + 12 <= p + t and p <= px
                and px + 8192 <= p + t]
        self.assertTrue(dono, "dsc/pixels fora da memoria viva da capa")
        got, exp = m.le(px, 8192), self.refer(nome_jpg)
        dif = [i // 2 for i in range(0, 8192, 2) if got[i:i + 2] != exp[i:i + 2]]
        self.assertEqual(dif[:5], [], f"{len(dif)} pixels diferentes (erro maximo por pixel = 0)")

    def ve_cinza(self, m, novas):
        s = self.srcs(m, novas)
        self.assertTrue(s, "devia trocar para o quadrado cinza")
        self.assertEqual(set(s), {PH_DSC}, "mostrou algo que nao e o quadrado cinza")

    # --- criação
    def test_d1_cria(self):
        m = self.aparelho()
        self.assertIn(("img_set_src", m.img, PH_DSC), m.chamadas)
        self.assertIn(("obj_align", m.img, 2, 0, 42), m.chamadas)
        ext = m.le32(m.view + 0x30)
        self.assertIn(ext, m.vivos)
        self.assertLessEqual(m.vivos[ext], EXT_MAX)
        self.assertEqual(m.de("add_event_cb"), [("add_event_cb", m.img, APAGA | 1, 0x21, ext)])
        self.assertEqual(m.de("f_open"), [])

    def test_d1_cria_sem_memoria(self):
        m = self.aparelho(sem_ext=True)
        self.assertEqual(m.le32(m.view + 0x30), 0)
        self.assertIn(("img_set_src", m.img, PH_DSC), m.chamadas)
        self.assertIn(("obj_align", m.img, 2, 0, 42), m.chamadas)
        self.titulo(m, ativo("01_capa_v23.mp3"))
        self.assertEqual(m.de("get_path"), [])

    def test_d1_cria_lvgl_sem_objeto(self):
        m = E.Maquina(self.rc7) if len(self.rc7) == 0x200000 else self.fail("sem RC7")
        view = m.aloca(0x34, registra=False)
        m.nega_obj = {1}
        salvos = [0x11110000 + i for i in range(8)]
        salvos[1] = view
        m.chama(CRIA, (TELA,), salvos=salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le32(view + 0x30), 0)
        self.assertEqual(m.vivos, {}, "ext sem objeto tem de ser liberado")
        self.assertFalse([c for c in m.chamadas if c[0] in ("img_set_src", "obj_align") and c[1] == 0])

    # --- capa encontrada (pixels exatos)
    def test_d2_capas(self):
        a, b, c = ativo("capa_a_300.jpg"), ativo("capa_b_500.jpg"), ativo("capa_c_200x120.jpg")
        casos = {
            "01_capa_v23": (ativo("01_capa_v23.mp3"), "capa_a_300.jpg"),
            "02_capa_v24_utf16": (ativo("02_capa_v24.mp3"), "capa_b_500.jpg"),
            "03_v24_ext": (ativo("03_capa_v24_cabecalho_estendido.mp3"), "capa_c_200x120.jpg"),
            "v23_ext": (E.tag_id3(3, [E.apic(3, a)], flags=0x40, ext=E.ext_header(3)), "capa_a_300.jpg"),
            "v23_grande_be32": (E.tag_id3(3, [E.texto(3, b"TIT2", "x"), E.apic(3, b, enc=2, desc="d")]),
                                "capa_b_500.jpg"),
            "mime_errado": (E.tag_id3(3, [E.apic(3, c, mime=b"image/jpg")]), "capa_c_200x120.jpg"),
        }
        for nome, (dados, jpg) in casos.items():
            with self.subTest(nome):
                m = self.aparelho()
                self.ve_capa(m, self.titulo(m, dados), jpg)

    # --- recusas: quadrado cinza, sem travar, sem vazar
    def test_d3_recusas(self):
        a = ativo("capa_a_300.jpg")
        corpo = b"\x00image/jpeg\x00\x03\x00" + a
        maior = b"APIC" + struct.pack(">I", len(corpo) + 5000) + b"\0\0" + corpo
        casos = {
            "progressiva": ativo("04_capa_progressiva.mp3"),
            "png": ativo("05_capa_png.mp3"),
            "sem_capa": ativo("06_sem_capa.mp3"),
            "sem_tag": ativo("07_sem_tag.mp3"),
            "v22": b"ID3\x02\x00\x00" + E.synchsafe(len(a) + 20) + b"PIC" + b"\0" * (len(a) + 17),
            "unsync": E.tag_id3(3, [E.apic(3, a)], flags=0x80),
            "v23_comprimido": E.tag_id3(3, [E.apic(3, a, flags=b"\0\x80")]),
            "v24_cifrado": E.tag_id3(4, [E.apic(4, a, flags=b"\0\x04")]),
            "v24_dli": E.tag_id3(4, [E.apic(4, a, flags=b"\0\x01")]),
            "enc_invalida": E.tag_id3(3, [E.apic(3, a, enc=7)]),
            "pequena_48": E.tag_id3(3, [E.apic(3, ativo("capa_pequena_48.jpg"))]),
            "jpeg_truncado": E.tag_id3(3, [E.apic(3, a[:len(a) * 6 // 10])]),
            "frame_maior_que_tag": b"ID3\x03\x00\x00" + E.synchsafe(len(maior)) + maior,
            "synchsafe_invalido": b"ID3\x03\x00\x00\x00\x00\x80\x00" + E.apic(3, a),
            "1o_apic_png": E.tag_id3(3, [E.apic(3, ativo("capa_a.png"), mime=b"image/png"), E.apic(3, a)]),
            "vazio": b"",
        }
        for nome, dados in casos.items():
            with self.subTest(nome):
                m = self.aparelho()
                self.ve_cinza(m, self.titulo(m, dados))

    def test_d3_falhas_do_sistema(self):
        m = self.aparelho()
        m.caminho = None
        novas = self.titulo(m, None, caminho=None)
        self.ve_cinza(m, novas)
        self.assertEqual([c for c in novas if c[0] == "f_open"], [])
        m = self.aparelho()
        self.ve_cinza(m, self.titulo(m, None))                     # arquivo não existe
        m = self.aparelho()
        self.ve_cinza(m, self.titulo(m, ativo("01_capa_v23.mp3"), nega=lambda t: True))

    # --- quando agir
    def test_d4_so_o_titulo(self):
        m = self.aparelho()
        for rot in (ROT_CONT, ROT_LETRA):
            novas = self.titulo(m, ativo("01_capa_v23.mp3"), rotulo=rot)
            self.assertEqual(novas, [novas[0]], "so o set_text quando nao e o titulo")
        m = self.aparelho()
        m.escreve32(m.le32(E.PAGINAS) + 0xAC, 0)
        novas = self.titulo(m, ativo("01_capa_v23.mp3"))
        self.assertEqual(novas, [novas[0]], "sem view: so o set_text")

    def test_d4_mesmo_caminho_e_troca(self):
        m = self.aparelho()
        self.ve_capa(m, self.titulo(m, ativo("01_capa_v23.mp3")), "capa_a_300.jpg")
        novas = self.titulo(m, ativo("01_capa_v23.mp3"))
        self.assertFalse([c for c in novas if c[0] in ("f_open", "img_set_src")], "mesma faixa: nada")
        self.ve_cinza(m, self.titulo(m, ativo("06_sem_capa.mp3"), caminho=b"0:/b.mp3"))
        self.ve_capa(m, self.titulo(m, ativo("02_capa_v24.mp3"), caminho=b"0:/c.mp3"), "capa_b_500.jpg")

    # --- liberação (LV_EVENT_DELETE do lv_img)
    def test_d5_apaga(self):
        m = self.aparelho()
        self.titulo(m, ativo("01_capa_v23.mp3"))
        ext = m.le32(m.view + 0x30)
        e = m.aloca(0x14, registra=False)
        m.escreve(e, struct.pack("<IIIII", m.img, m.img, 0x21, ext, 0))
        m.chama(APAGA, (e,))
        self.assertEqual(m.erros, [])
        self.assertNotIn(ext, m.vivos)
        self.assertEqual(m.vivos, {})
        self.assertEqual(m.le32(m.view + 0x30), 0)


class Recusa(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        tmp = tempfile.mkdtemp(prefix="openpod_recusa7_")
        p6, p5 = os.path.join(tmp, "rc6.bin"), os.path.join(tmp, "rc5.bin")
        constroi("reload_1.0_rc6", p6)
        constroi("reload_1.0_rc5", p5)
        cls.rc6, cls.rc5 = le(p6), le(p5)

    def roda(self, ferramenta, entrada, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_r7_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(entrada)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", ferramenta),
                            "--in", src, "--out", dst] + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), le(src) == entrada

    def test_d6_existem(self):
        for f in FERRAMENTAS:
            self.assertTrue(os.path.exists(os.path.join(RAIZ, "tools", f)), f)

    def test_d6_recusa(self):
        for f in FERRAMENTAS:   # exige a RC6 exata (sha) como entrada
            casos = {"rc5": self.rc5, "truncado": self.rc6[:0x100000]}
            for a in (GANCHO_BL[0], GANCHO_B[0], 0x131E80, 0x131E9E, LOTE, LOTE + LOTE_TAM - 1,
                      0x10B20, 0x11090):
                b = bytearray(self.rc6)
                b[a] ^= 0xFF
                casos[hex(a)] = bytes(b)
            for nome, entrada in casos.items():
                rc, criou, intacta = self.roda(f, entrada)
                self.assertNotEqual(rc, 0, f"{f} aceitou {nome}")
                self.assertFalse(criou, f"{f} criou saida com {nome}")
                self.assertTrue(intacta)

    def test_d6_aceita_rc6_e_dry_run(self):
        for f in FERRAMENTAS:
            self.assertEqual(self.roda(f, self.rc6)[:2], (0, True), f)
            self.assertEqual(self.roda(f, self.rc6, ["--dry-run"])[:2], (0, False), f)

    def test_d6_saida_igual_ou_link(self):
        for f in FERRAMENTAS:
            for tipo in ("mesmo", "symlink", "hardlink"):
                tmp = tempfile.mkdtemp(prefix="openpod_link7_")
                src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
                with open(src, "wb") as fh:
                    fh.write(self.rc6)
                if tipo == "mesmo":
                    dst = src
                else:
                    (os.symlink if tipo == "symlink" else os.link)(src, dst)
                r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", f),
                                    "--in", src, "--out", dst], capture_output=True, cwd=RAIZ)
                self.assertNotEqual(r.returncode, 0, f"{f} {tipo}")
                self.assertEqual(le(src), self.rc6, f"{f} {tipo}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
