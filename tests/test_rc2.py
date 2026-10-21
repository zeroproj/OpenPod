#!/usr/bin/env python3
# NÃO ALTERAR sem o arquiteto. O hash deste arquivo é conferido por tools/ci.sh
# (tests/PROTEGIDOS.sha256). Ficha: docs/tarefas/001-rc2-logo-fundo.md
"""
test_rc2.py — critérios de aceite da Reload 1.0 RC2 (logo + fundo preto).

Testa EFEITO na imagem, não a ferramenta que o produz. Constrói as
receitas `reload_1.0_rc1` e `reload_1.0_rc2` a partir do ORIGINAL, num
diretório temporário, e confere byte a byte contra o ORIGINAL.

USO
    python3 tests/test_rc2.py            (ou python3 -m unittest tests.test_rc2)

DEPENDÊNCIAS
    Python 3 + Pillow. Não abre o USB.
"""

import hashlib
import importlib.util
import os
import struct
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
SHA_ORIGINAL = "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f"
SHA_RC1 = "a427c62ec7da0170ef4296ebda6a55ec5d287c4058d3c5a9e80e645f28e5c3f2"
XIP = 0x00C00000

# --- fatos do firmware de fábrica (verificados no ORIGINAL, ficha §Evidência)
LOGO_CAB, LOGO_DADOS, LOGO_FIM = 0x0CC7C4, 0x0CC7D0, 0x0CDD50   # 128x35 INDEXED_8
PAPEL_CAB, PAPEL_DADOS = 0x0C73B8, 0x0C73C4                      # 128x160 INDEXED_8
PAPEL_FIM = PAPEL_DADOS + 1024 + 128 * 160
ABERTURA_BL = (0x12285A, 0x1228E4)      # bl lv_color_white antes do bg da abertura
COR_BRANCA, COR_PRETA = 0x00D21384, 0x00D2138A
FUNDO_DISPLAY = 0x1567F6                # movs r3,#0xff -> bg do display

PAPEL_PALETA_FIM = PAPEL_DADOS + 1024
SHA_LOGO_PNG = "1e459938eddc15416d01fb9f29d7486400a2c9166ed159eac1ba0c58edf90d4d"
FERRAMENTAS = ("fab_logo.py", "fab_fundo_preto.py")   # nomes fixados pela ficha

PERMITIDO_RC2 = (
    [(LOGO_DADOS, LOGO_FIM), (PAPEL_DADOS, PAPEL_PALETA_FIM),
     (FUNDO_DISPLAY, FUNDO_DISPLAY + 2)]
    + [(a, a + 4) for a in ABERTURA_BL]
)

PROIBIDAS = {
    # ferramentas de projetos antigos (linha Core / Alphas): decisão do mantenedor
    "patch_logo.py", "patch_fundo_display.py", "patch_fundo_abertura.py",
    "patch_fundo_preto.py", "patch_nome_faixa.py", "patch_faixa_degrade.py",
    "patch_bateria_casca.py", "patch_bateria_verde.py", "patch_bateria_miolo.py",
    "relocate_lang_table.py", "aplica_textos.py",
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def carrega_build():
    spec = importlib.util.spec_from_file_location(
        "build", os.path.join(RAIZ, "tools/build.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


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


def decodifica(b, cab):
    h, tam, ptr = struct.unpack_from("<3I", b, cab)
    w, hh = (h >> 10) & 0x7FF, (h >> 21) & 0x7FF
    d = ptr - XIP
    pal, px = b[d:d + 1024], b[d + 1024:d + 1024 + w * hh]
    return w, hh, [(pal[i * 4 + 2], pal[i * 4 + 1], pal[i * 4], pal[i * 4 + 3]) for i in px]


class RC2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orig = open(ORIGINAL, "rb").read()
        assert sha(cls.orig) == SHA_ORIGINAL, "ORIGINAL nao confere — PARE"
        cls.tmp = tempfile.mkdtemp(prefix="openpod_test_rc2_")
        p1 = os.path.join(cls.tmp, "rc1.bin")
        p2 = os.path.join(cls.tmp, "rc2.bin")
        cls.rc1_rc, cls.rc1_log = constroi("reload_1.0_rc1", p1)
        cls.rc2_rc, cls.rc2_log = constroi("reload_1.0_rc2", p2)
        cls.rc1 = open(p1, "rb").read() if os.path.exists(p1) else b""
        cls.rc2 = open(p2, "rb").read() if os.path.exists(p2) else b""

    # --- C0: a receita existe, roda e valida
    def test_c0_receita_rc2_constroi_e_valida(self):
        self.assertEqual(self.rc2_rc, 0, "build reload_1.0_rc2 falhou:\n" + self.rc2_log[-2000:])
        self.assertEqual(len(self.rc2), 0x200000)

    # --- C1: RC1 (aprovada no aparelho) continua reprodutível e intacta dentro da RC2
    def test_c1_rc1_reprodutivel(self):
        self.assertEqual(self.rc1_rc, 0, self.rc1_log[-2000:])
        self.assertEqual(sha(self.rc1), SHA_RC1, "a RC1 mudou — catraca")

    def test_c1_rc2_contem_rc1(self):
        dif1 = [i for i in range(len(self.orig)) if self.orig[i] != self.rc1[i]]
        self.assertTrue(dif1)
        ruins = [i for i in dif1 if self.rc2[i] != self.rc1[i]]
        self.assertEqual(ruins, [], f"RC2 desfez bytes da RC1 em {[hex(x) for x in ruins[:8]]}")

    # --- C2: só ferramentas novas; nada de projetos antigos
    def test_c2_receita_sem_ferramentas_antigas(self):
        rec = carrega_build().RECEITAS["reload_1.0_rc2"]
        nomes = [t for t, _, _ in rec]
        self.assertEqual(set(nomes[1:]), set(FERRAMENTAS), "RC2 = RC1 + as duas ferramentas da ficha")
        self.assertEqual(nomes[0], "patch_update_sd.py", "RC2 = RC1 + passos novos")
        self.assertFalse(PROIBIDAS & set(nomes), f"ferramenta antiga na receita: {PROIBIDAS & set(nomes)}")
        for t in nomes[1:]:
            src = open(os.path.join(RAIZ, "tools", t), encoding="utf8").read()
            for p in PROIBIDAS:
                self.assertNotIn(p.replace(".py", ""), src, f"{t} usa {p}")

    # --- C3: logo do OpenPod na abertura
    def test_c3_logo_cabecalho_intocado(self):
        self.assertEqual(self.rc2[LOGO_CAB:LOGO_DADOS], self.orig[LOGO_CAB:LOGO_DADOS])

    def test_c3_logo_e_a_do_openpod(self):
        from PIL import Image
        w, h, px = decodifica(self.rc2, LOGO_CAB)
        self.assertEqual((w, h), (128, 35))
        png = os.path.join(RAIZ, "assets/OpenLogo.png")
        self.assertEqual(sha(open(png, "rb").read()), SHA_LOGO_PNG, "OpenLogo.png mudou")
        img = Image.open(png)
        self.assertEqual(img.size, (128, 35))
        ref = img.convert("RGB").tobytes()
        got = bytes(c for p in px for c in p[:3])
        self.assertEqual(len(ref), len(got))
        difs = [abs(a - b) for a, b in zip(ref, got)]
        self.assertLessEqual(sum(difs) / len(difs), 2.0, "logo longe do PNG")
        self.assertLessEqual(max(difs), 64)
        self.assertTrue(all(p[3] == 255 for p in px), "logo com alfa != 255")

    # --- C4: fundo da abertura preto, usando a função preta da própria fábrica
    def test_c4_abertura_chama_cor_preta(self):
        for a in ABERTURA_BL:
            self.assertEqual(bl_alvo(self.orig, a), COR_BRANCA, f"premissa de fabrica em 0x{a:X}")
            self.assertEqual(bl_alvo(self.rc2, a), COR_PRETA, f"abertura ainda branca em 0x{a:X}")

    def test_c4_funcao_preta_intocada(self):
        o = COR_PRETA - XIP
        self.assertEqual(self.rc2[o:o + 6], bytes.fromhex("4ff000007047"))

    # --- C5: fundo do display preto
    def test_c5_fundo_display_preto(self):
        self.assertEqual(self.orig[FUNDO_DISPLAY:FUNDO_DISPLAY + 2], b"\xff\x23", "premissa")
        self.assertEqual(self.rc2[FUNDO_DISPLAY:FUNDO_DISPLAY + 2], b"\x00\x23")

    # --- C6: papel de parede da Tocando Agora preto
    def test_c6_papel_de_parede_preto(self):
        self.assertEqual(self.rc2[PAPEL_CAB:PAPEL_DADOS], self.orig[PAPEL_CAB:PAPEL_DADOS])
        w, h, px = decodifica(self.rc2, PAPEL_CAB)
        self.assertEqual((w, h), (128, 160))
        pal = self.rc2[PAPEL_DADOS:PAPEL_PALETA_FIM]
        opal = self.orig[PAPEL_DADOS:PAPEL_PALETA_FIM]
        for i in range(256):
            self.assertEqual(pal[i * 4:i * 4 + 3], b"\0\0\0", f"cor {i} da paleta nao e preta")
            self.assertEqual(pal[i * 4 + 3], opal[i * 4 + 3], f"alfa {i} mudou")
        self.assertEqual(self.rc2[PAPEL_PALETA_FIM:PAPEL_FIM],
                         self.orig[PAPEL_PALETA_FIM:PAPEL_FIM], "pixels do papel mudaram")

    # --- C7: segurança — nada fora do declarado
    def test_c7_so_regioes_permitidas(self):
        dif1 = {i for i in range(len(self.orig)) if self.orig[i] != self.rc1[i]}
        fora = [i for i in range(len(self.orig))
                if self.orig[i] != self.rc2[i] and i not in dif1
                and not any(a <= i < b for a, b in PERMITIDO_RC2)]
        self.assertEqual(fora, [], f"escreveu fora do permitido: {[hex(x) for x in fora[:8]]}")

    def test_c7_bootloader_r1_psmp(self):
        dif = [i for i in range(len(self.orig)) if self.orig[i] != self.rc2[i]]
        self.assertGreaterEqual(min(dif), 0xE000, "bootloader ou setor 0xD000 tocado")
        self.assertFalse(any(i >= 0x1FC000 for i in dif), "PSMP tocada")


class Recusa(unittest.TestCase):
    """D3: com premissa errada, a ferramenta recusa ANTES de escrever."""

    def roda(self, ferramenta, entrada):
        tmp = tempfile.mkdtemp(prefix="openpod_recusa_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        open(src, "wb").write(entrada)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", ferramenta),
                            "--in", src, "--out", dst], capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), open(src, "rb").read() == entrada

    def casos(self):
        o = open(ORIGINAL, "rb").read()
        def troca(a, v):
            b = bytearray(o); b[a:a + len(v)] = v; return bytes(b)
        return {
            "truncado": o[:0x100000],
            "logo_cab": troca(LOGO_CAB, b"\0\0\0\0"),
            "papel_cab": troca(PAPEL_CAB + 8, b"\0\0\0\0"),
            "bl1": troca(ABERTURA_BL[0], b"\0\xbf\0\xbf"),
            "bl2": troca(ABERTURA_BL[1], b"\0\xbf\0\xbf"),
            "display": troca(FUNDO_DISPLAY, b"\x12\x23"),
            "preta": troca(COR_PRETA - XIP, b"\0\0\0\0"),
        }

    def test_d3_ferramentas_existem(self):
        for f in FERRAMENTAS:
            self.assertTrue(os.path.exists(os.path.join(RAIZ, "tools", f)), f)

    def test_d3_logo_recusa(self):
        for nome in ("truncado", "logo_cab"):
            rc, criou, intacta = self.roda("fab_logo.py", self.casos()[nome])
            self.assertNotEqual(rc, 0, f"fab_logo aceitou {nome}")
            self.assertFalse(criou, f"fab_logo criou saida com {nome}")
            self.assertTrue(intacta)

    def test_d3_fundo_recusa(self):
        for nome in ("truncado", "papel_cab", "bl1", "bl2", "display", "preta"):
            rc, criou, intacta = self.roda("fab_fundo_preto.py", self.casos()[nome])
            self.assertNotEqual(rc, 0, f"fab_fundo_preto aceitou {nome}")
            self.assertFalse(criou, f"fab_fundo_preto criou saida com {nome}")
            self.assertTrue(intacta)

    # R1 (achado MÉDIA da análise do diff): o cabeçalho inteiro é premissa,
    # inclusive always_zero (bits 5-7) e reservados (bits 8-9).
    def test_r1_cabecalho_bits_reservados(self):
        o = open(ORIGINAL, "rb").read()
        for ferramenta, cab in (("fab_logo.py", LOGO_CAB), ("fab_fundo_preto.py", PAPEL_CAB)):
            h = struct.unpack_from("<I", o, cab)[0]
            for bit in range(5, 10):
                b = bytearray(o)
                struct.pack_into("<I", b, cab, h ^ (1 << bit))
                rc, criou, intacta = self.roda(ferramenta, bytes(b))
                self.assertNotEqual(rc, 0, f"{ferramenta} aceitou bit {bit} de 0x{cab:X}")
                self.assertFalse(criou)
                self.assertTrue(intacta)

    # R1 (achado BAIXA): saída que é a própria entrada por link não pode ser gravada.
    def test_r1_saida_link_para_entrada(self):
        o = open(ORIGINAL, "rb").read()
        for ferramenta in FERRAMENTAS:
            for tipo in ("symlink", "hardlink"):
                tmp = tempfile.mkdtemp(prefix="openpod_link_")
                src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
                open(src, "wb").write(o)
                (os.symlink if tipo == "symlink" else os.link)(src, dst)
                r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", ferramenta),
                                    "--in", src, "--out", dst], capture_output=True, text=True, cwd=RAIZ)
                self.assertNotEqual(r.returncode, 0, f"{ferramenta} aceitou saida {tipo} da entrada")
                self.assertEqual(open(src, "rb").read(), o, f"{ferramenta} alterou a entrada via {tipo}")

    def test_d3_aceita_o_original(self):
        o = open(ORIGINAL, "rb").read()
        for f in FERRAMENTAS:
            rc, criou, _ = self.roda(f, o)
            self.assertEqual(rc, 0, f"{f} recusou o ORIGINAL")
            self.assertTrue(criou)


if __name__ == "__main__":
    unittest.main(verbosity=2)
