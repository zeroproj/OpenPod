#!/usr/bin/env python3
# NÃO ALTERAR sem o arquiteto. O hash deste arquivo é conferido por tools/ci.sh
# (tests/PROTEGIDOS.sha256). Ficha: docs/tarefas/002-rc3-barra-openpod-degrade.md
"""
test_rc3.py — critérios de aceite da Reload 1.0 RC3 (barra com "OpenPod" + degradê).

Testa EFEITO na imagem, não a ferramenta que o produz. Constrói as
receitas `reload_1.0_rc2` e `reload_1.0_rc3` a partir do ORIGINAL, num
diretório temporário, e confere byte a byte contra o ORIGINAL e a RC2.

USO
    python3 tests/test_rc3.py

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
SHA_RC2 = "fcca5fdc99b828fb135cae77f5915c42cfddf1a537eb0a619f0c135313ccd123"  # aprovada 2026-10-21
XIP = 0x00C00000

# --- fatos do firmware de fábrica (verificados no ORIGINAL, ficha §Evidência)
CRIA_FAIXA, CRIA_FAIXA_FIM = 0x1216F0, 0x121764     # 52 telas chamam
GANCHO_BG = 0x121724                 # bl set_style_bg_color dentro da CRIA_FAIXA
SET_BG_COLOR = 0x00D4D092            # wrapper prop 0x20
SET_LOCAL_PROP = 0x00D4CAC4          # lv_obj_set_local_style_prop(obj, prop, valor, seletor)
ROTINA, ROTINA_LOTE = 0x1A7000, 0x40
TEXTO, TEXTO_LOTE = 0x1A7040, 0x10
COR_TOPO, COR_BASE = (64, 70, 82), (14, 16, 19)      # RGB 8 bits
TOPO_SWAP, BASE_SWAP = 0x2A42, 0x8208                # RGB565 pré-invertido (LV_COLOR_16_SWAP)

HOME_CAB, HOME_PAL, HOME_PX = 0x0CDD50, 0x0CDD5C, 0x0CE15C   # folha 128x160 INDEXED_8
HOME_LINHAS = 16                                            # y 0..15, todas índice 1 na fábrica

SD_LABEL, SD_LABEL_FIM = 0x1226AC, 0x1226F8          # cria view_p[0x14] (só home/0x51, com cartão)
TITULO = {   # endereço: (bytes de fábrica, bytes da RC3)
    0x1226BA: (bytes.fromhex("6ff01d02"), bytes.fromhex("042200bf")),  # x_ofs -30 -> movs r2,#4; nop (revisão R0)
    0x1226BE: (bytes.fromhex("0321"), bytes.fromhex("0221")),          # align 3 -> 2 (TOP_MID)
    0x1226CA: (None, bytes.fromhex("00bf00bf")),                       # bl set_style_text_font -> nop nop
    0x1226F4: (struct.pack("<I", 0x00C5D614), struct.pack("<I", XIP + TEXTO)),  # ponteiro do texto
}

FERRAMENTAS = ("fab_barra_degrade.py", "fab_barra_titulo.py")   # nomes e ordem fixados pela ficha

ROTINA_ESPERADA = [
    ("push", "{r4, lr}"),
    ("mov", "r4, r0"),
    ("movw", "r1, #0x2a42"),
    ("movs", "r2, #0"),
    ("bl", "#0xd4d092"),
    ("mov", "r0, r4"),
    ("movs", "r1, #0x21"),
    ("movs", "r2, #0xff"),
    ("movs", "r3, #0"),
    ("bl", "#0xd4cac4"),
    ("mov", "r0, r4"),
    ("movs", "r1, #0x22"),
    ("movw", "r2, #0x8208"),
    ("movs", "r3, #0"),
    ("bl", "#0xd4cac4"),
    ("mov", "r0, r4"),
    ("movs", "r1, #0x23"),
    ("movs", "r2, #1"),
    ("movs", "r3, #0"),
    ("pop", "{r4, lr}"),
    ("b", "#0xd4cac4"),
]

PERMITIDO_RC3 = [
    (GANCHO_BG, GANCHO_BG + 4),
    (ROTINA, ROTINA + ROTINA_LOTE),
    (TEXTO, TEXTO + TEXTO_LOTE),
    (HOME_PX, HOME_PX + 128 * HOME_LINHAS),
] + [(a, a + len(v[1])) for a, v in TITULO.items()]

PROIBIDAS = {
    # ferramentas de projetos antigos (linha Core / Alphas): decisão do mantenedor
    "patch_logo.py", "patch_fundo_display.py", "patch_fundo_abertura.py",
    "patch_fundo_preto.py", "patch_nome_faixa.py", "patch_faixa_degrade.py",
    "patch_bateria_casca.py", "patch_bateria_verde.py", "patch_bateria_miolo.py",
    "relocate_lang_table.py", "aplica_textos.py",
    # as da faixa da linha Core
    "patch_status_bar.py", "fix_status_bar.py", "patch_titulos.py",
    "patch_faixa_16px.py", "patch_faixa_alinha.py", "patch_faixa_cinza.py",
    "patch_home_barra.py", "patch_chrome_padrao.py",
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


def rgb565_swap(c):
    v = ((c[0] >> 3) << 11) | ((c[1] >> 2) << 5) | (c[2] >> 3)
    return ((v & 0xFF) << 8) | (v >> 8)


def alvo_linha(y):
    t = y / (HOME_LINHAS - 1)
    return tuple(round(COR_TOPO[k] + (COR_BASE[k] - COR_TOPO[k]) * t) for k in range(3))


class RC3(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orig = open(ORIGINAL, "rb").read()
        assert sha(cls.orig) == SHA_ORIGINAL, "ORIGINAL nao confere — PARE"
        cls.tmp = tempfile.mkdtemp(prefix="openpod_test_rc3_")
        p2 = os.path.join(cls.tmp, "rc2.bin")
        p3 = os.path.join(cls.tmp, "rc3.bin")
        cls.rc2_rc, cls.rc2_log = constroi("reload_1.0_rc2", p2)
        cls.rc3_rc, cls.rc3_log = constroi("reload_1.0_rc3", p3)
        cls.rc2 = open(p2, "rb").read() if os.path.exists(p2) else b""
        cls.rc3 = open(p3, "rb").read() if os.path.exists(p3) else b""

    # --- C0: a receita existe, roda e valida
    def test_c0_receita_rc3_constroi_e_valida(self):
        self.assertEqual(self.rc3_rc, 0, "build reload_1.0_rc3 falhou:\n" + self.rc3_log[-2000:])
        self.assertEqual(len(self.rc3), 0x200000)

    # --- C1: a RC2 (aprovada no aparelho) continua inteira dentro da RC3
    def test_c1_rc2_reprodutivel(self):
        self.assertEqual(sha(self.rc2), SHA_RC2, "a RC2 aprovada mudou — catraca")

    def test_c1_rc3_contem_rc2(self):
        dif2 = [i for i in range(len(self.orig)) if self.orig[i] != self.rc2[i]]
        ruins = [i for i in dif2 if self.rc3[i] != self.rc2[i]]
        self.assertEqual(ruins, [], f"RC3 desfez bytes da RC2 em {[hex(x) for x in ruins[:8]]}")

    # --- C2: receita = RC2 + as duas ferramentas novas; nada de projetos antigos
    def test_c2_receita(self):
        b = carrega_build()
        rec2 = [t for t, _, _ in b.RECEITAS["reload_1.0_rc2"]]
        rec3 = [t for t, _, _ in b.RECEITAS["reload_1.0_rc3"]]
        self.assertEqual(rec3[:len(rec2)], rec2, "RC3 = RC2 + passos novos, na ordem")
        self.assertEqual(tuple(rec3[len(rec2):]), FERRAMENTAS)
        self.assertFalse(PROIBIDAS & set(rec3), f"ferramenta antiga: {PROIBIDAS & set(rec3)}")
        for t in FERRAMENTAS:
            src = open(os.path.join(RAIZ, "tools", t), encoding="utf8").read()
            for p in PROIBIDAS:
                self.assertNotIn(p.replace(".py", ""), src, f"{t} usa {p}")

    def test_c2_lotes_declarados_no_mapa(self):
        m = carrega_build().MAPA
        self.assertEqual(m.get("fab_barra_degrade.py"), (ROTINA, ROTINA_LOTE))
        self.assertEqual(m.get("fab_barra_titulo.py"), (TEXTO, TEXTO_LOTE))
        for nome, (ini, tam) in m.items():
            if nome in FERRAMENTAS:
                continue
            self.assertFalse(ini < TEXTO + TEXTO_LOTE and ROTINA < ini + tam,
                             f"lote da RC3 cruza o de {nome}")

    # --- C3: degradê nas 52 telas que usam a CRIA_FAIXA
    def test_c3_gancho_chama_a_rotina(self):
        self.assertEqual(bl_alvo(self.orig, GANCHO_BG), SET_BG_COLOR, "premissa de fabrica")
        self.assertEqual(bl_alvo(self.rc3, GANCHO_BG), XIP + ROTINA)

    def test_c3_resto_da_cria_faixa_intocado(self):
        for i in range(CRIA_FAIXA, CRIA_FAIXA_FIM):
            if GANCHO_BG <= i < GANCHO_BG + 4:
                continue
            self.assertEqual(self.rc3[i], self.orig[i], f"CRIA_FAIXA mudou em 0x{i:X}")

    def test_c3_rotina_e_a_da_ficha(self):
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        got, fim = [], ROTINA
        for ins in md.disasm(self.rc3[ROTINA:ROTINA + ROTINA_LOTE], XIP + ROTINA):
            got.append((ins.mnemonic.replace(".w", ""), ins.op_str))
            fim = ins.address - XIP + ins.size
            if len(got) == len(ROTINA_ESPERADA):
                break
        self.assertEqual(got, ROTINA_ESPERADA)
        self.assertTrue(all(x == 0xFF for x in self.rc3[fim:ROTINA + ROTINA_LOTE]),
                        "lixo depois da rotina")

    def test_c3_cores_pre_invertidas(self):
        self.assertEqual(rgb565_swap(COR_TOPO), TOPO_SWAP)
        self.assertEqual(rgb565_swap(COR_BASE), BASE_SWAP)

    def test_c3_funcoes_chamadas_intocadas(self):
        for f, n in ((SET_BG_COLOR, 0x22), (SET_LOCAL_PROP, 0x40)):
            o = f - XIP
            self.assertEqual(self.rc3[o:o + n], self.orig[o:o + n], f"0x{f:X} mudou")

    # --- C4: degradê na home (folha de imagem, linhas 0..15)
    def test_c4_home_cabecalho_e_paleta_intocados(self):
        self.assertEqual(self.rc3[HOME_CAB:HOME_PX], self.orig[HOME_CAB:HOME_PX])

    def test_c4_home_linhas_em_degrade(self):
        self.assertTrue(all(x == 1 for x in self.orig[HOME_PX:HOME_PX + 128 * HOME_LINHAS]),
                        "premissa: linhas 0..15 pretas (indice 1) na fabrica")
        pal = self.rc3[HOME_PAL:HOME_PX]
        lum_ant = None
        for y in range(HOME_LINHAS):
            linha = self.rc3[HOME_PX + 128 * y:HOME_PX + 128 * (y + 1)]
            self.assertEqual(len(set(linha)), 1, f"linha {y} nao e uniforme")
            i = linha[0]
            b, g, r, a = pal[i * 4:i * 4 + 4]
            self.assertEqual(a, 255, f"linha {y}: indice {i} com alfa {a}")
            alvo = alvo_linha(y)
            self.assertLessEqual(max(abs(r - alvo[0]), abs(g - alvo[1]), abs(b - alvo[2])), 12,
                                 f"linha {y}: ({r},{g},{b}) longe de {alvo}")
            lum = 299 * r + 587 * g + 114 * b
            if lum_ant is not None:
                self.assertLessEqual(lum, lum_ant, f"linha {y} mais clara que a anterior")
            lum_ant = lum
        self.assertNotEqual(self.rc3[HOME_PX], 1, "a primeira linha continua preta")

    def test_c4_home_icones_intocados(self):
        ini = HOME_PX + 128 * HOME_LINHAS
        self.assertEqual(self.rc3[ini:HOME_PX + 128 * 160], self.orig[ini:HOME_PX + 128 * 160])

    # --- C5: "OpenPod" no rótulo do cartão (home), centralizado, fonte do tema
    def test_c5_titulo_bytes(self):
        for a, (fab, novo) in TITULO.items():
            if fab is not None:
                self.assertEqual(self.orig[a:a + len(fab)], fab, f"premissa em 0x{a:X}")
            self.assertEqual(self.rc3[a:a + len(novo)], novo, f"0x{a:X}")
        self.assertEqual(bl_alvo(self.orig, 0x1226CA), 0x00D4D12E, "premissa: bl set_style_text_font")

    def test_c5_texto_openpod(self):
        self.assertEqual(self.rc3[TEXTO:TEXTO + 8], b"OpenPod\0")
        self.assertTrue(all(x == 0xFF for x in self.rc3[TEXTO + 8:TEXTO + TEXTO_LOTE]))

    def test_c5_resto_do_rotulo_intocado(self):
        mudam = set()
        for a, (_, novo) in TITULO.items():
            mudam |= set(range(a, a + len(novo)))
        for i in range(SD_LABEL, SD_LABEL_FIM + 4):
            if i not in mudam:
                self.assertEqual(self.rc3[i], self.orig[i], f"rotulo mudou em 0x{i:X}")

    # --- C6: segurança — nada fora do declarado
    def test_c6_so_regioes_permitidas(self):
        dif2 = {i for i in range(len(self.orig)) if self.orig[i] != self.rc2[i]}
        fora = [i for i in range(len(self.orig))
                if self.rc2[i] != self.rc3[i] and i not in dif2
                and not any(a <= i < b for a, b in PERMITIDO_RC3)]
        self.assertEqual(fora, [], f"escreveu fora do permitido: {[hex(x) for x in fora[:8]]}")

    def test_c6_bootloader_r1_psmp(self):
        dif = [i for i in range(len(self.orig)) if self.orig[i] != self.rc3[i]]
        self.assertGreaterEqual(min(dif), 0xE000, "bootloader ou setor 0xD000 tocado")
        self.assertFalse(any(i >= 0x1FC000 for i in dif), "PSMP tocada")


class Recusa(unittest.TestCase):
    """D3: com premissa errada, a ferramenta recusa ANTES de escrever."""

    @classmethod
    def setUpClass(cls):
        cls.o = open(ORIGINAL, "rb").read()

    def roda(self, ferramenta, entrada, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_recusa3_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        open(src, "wb").write(entrada)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", ferramenta),
                            "--in", src, "--out", dst] + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), open(src, "rb").read() == entrada

    def inverte(self, a):
        b = bytearray(self.o)
        b[a] ^= 0xFF
        return bytes(b)

    def troca(self, a, v):
        b = bytearray(self.o)
        b[a:a + len(v)] = v
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

    def test_d3_degrade_recusa(self):
        self.confere_recusa("fab_barra_degrade.py", {
            "truncado": self.o[:0x100000],
            "gancho": self.troca(GANCHO_BG, b"\0\xbf\0\xbf"),
            "cria_faixa": self.troca(0x12174C, b"\0\xbf\0\xbf"),
            "set_bg_color": self.troca(SET_BG_COLOR - XIP + 0x12, b"\x21\x21"),
            "set_local_prop": self.troca(SET_LOCAL_PROP - XIP, b"\0\xbf\0\xbf"),
            "lote_ocupado": self.troca(ROTINA + 0x30, b"\x00"),
            "home_cab": self.troca(HOME_CAB + 4, b"\0\0\0\0"),
            "home_linha": self.troca(HOME_PX + 128 * 7 + 5, b"\x02"),
            "home_paleta": self.troca(HOME_PAL + 4 * 200, b"\x10\x10\x10"),
        })

    def test_d3_titulo_recusa(self):
        self.confere_recusa("fab_barra_titulo.py", {
            "truncado": self.o[:0x100000],
            "x_ofs": self.troca(0x1226BA, b"\x6f\xf0\x1c\x02"),
            "align": self.troca(0x1226BE, b"\x01\x21"),
            "fonte": self.troca(0x1226CA, b"\0\xbf\0\xbf"),
            "ponteiro": self.troca(0x1226F4, struct.pack("<I", 0x00C5D610)),
            "rotulo": self.troca(0x1226E6, b"\x02\x21"),
            "chamador": self.troca(0x123898, b"\0\xbf\0\xbf"),
            "lote_ocupado": self.troca(TEXTO + 9, b"\x00"),
        })

    def test_d3_degrade_recusa_bordas(self):
        # revisão R0: as premissas valem para a faixa inteira, não para um byte
        pontos = [CRIA_FAIXA, CRIA_FAIXA_FIM - 1,
                  SET_BG_COLOR - XIP, SET_BG_COLOR - XIP + 0x21,
                  SET_LOCAL_PROP - XIP + 0x20, SET_LOCAL_PROP - XIP + 0x3F,
                  HOME_CAB, HOME_CAB + 11, HOME_PAL, HOME_PAL + 4 * 255,
                  HOME_PX, HOME_PX + 128 * 15 + 127,
                  ROTINA, ROTINA + ROTINA_LOTE - 1]
        self.confere_recusa("fab_barra_degrade.py", {hex(a): self.inverte(a) for a in pontos})

    def test_d3_titulo_recusa_bordas(self):
        pontos = [SD_LABEL, SD_LABEL_FIM - 1, 0x1226D0, 0x123E9C, TEXTO, TEXTO + TEXTO_LOTE - 1]
        self.confere_recusa("fab_barra_titulo.py", {hex(a): self.inverte(a) for a in pontos})

    def test_d3_saida_igual_a_entrada(self):
        for f in FERRAMENTAS:
            tmp = tempfile.mkdtemp(prefix="openpod_mesmo3_")
            src = os.path.join(tmp, "in.bin")
            open(src, "wb").write(self.o)
            r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", f), "--in", src, "--out", src],
                               capture_output=True, text=True, cwd=RAIZ)
            self.assertNotEqual(r.returncode, 0, f"{f} aceitou --out igual a --in")
            self.assertEqual(open(src, "rb").read(), self.o, f"{f} alterou a entrada")

    def test_d3_dry_run_recusa_adulterado(self):
        for f, a in (("fab_barra_degrade.py", GANCHO_BG), ("fab_barra_titulo.py", 0x1226F4)):
            rc, criou, _ = self.roda(f, self.inverte(a), ["--dry-run"])
            self.assertNotEqual(rc, 0, f"{f} --dry-run aceitou entrada adulterada")
            self.assertFalse(criou)

    def test_d3_em_diferente_do_mapa_recusa(self):
        self.confere_recusa("fab_barra_degrade.py", {"em_errado": self.o}, ["--em", "0x1a7100"])
        self.confere_recusa("fab_barra_titulo.py", {"em_errado": self.o}, ["--em", "0x1a7100"])

    def test_d3_saida_link_para_entrada(self):
        for ferramenta in FERRAMENTAS:
            for tipo in ("symlink", "hardlink"):
                tmp = tempfile.mkdtemp(prefix="openpod_link3_")
                src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
                open(src, "wb").write(self.o)
                (os.symlink if tipo == "symlink" else os.link)(src, dst)
                r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", ferramenta),
                                    "--in", src, "--out", dst], capture_output=True, text=True, cwd=RAIZ)
                self.assertNotEqual(r.returncode, 0, f"{ferramenta} aceitou saida {tipo}")
                self.assertEqual(open(src, "rb").read(), self.o, f"{ferramenta} alterou a entrada via {tipo}")

    def test_d3_aceita_o_original(self):
        for f, em in (("fab_barra_degrade.py", ROTINA), ("fab_barra_titulo.py", TEXTO)):
            for extra in ((), ("--em", hex(em))):
                rc, criou, _ = self.roda(f, self.o, extra)
                self.assertEqual(rc, 0, f"{f} {extra} recusou o ORIGINAL")
                self.assertTrue(criou)

    def test_d3_segunda_passagem_recusa(self):
        for f in FERRAMENTAS:
            tmp = tempfile.mkdtemp(prefix="openpod_2x_")
            a, b, c = (os.path.join(tmp, n) for n in ("a.bin", "b.bin", "c.bin"))
            open(a, "wb").write(self.o)
            r1 = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", f), "--in", a, "--out", b],
                                capture_output=True, cwd=RAIZ)
            self.assertEqual(r1.returncode, 0, f)
            r2 = subprocess.run([sys.executable, os.path.join(RAIZ, "tools", f), "--in", b, "--out", c],
                                capture_output=True, cwd=RAIZ)
            self.assertNotEqual(r2.returncode, 0, f"{f} rodou duas vezes")
            self.assertFalse(os.path.exists(c))

    def test_d3_dry_run_nao_cria_saida(self):
        for f in FERRAMENTAS:
            rc, criou, _ = self.roda(f, self.o, ["--dry-run"])
            self.assertEqual(rc, 0, f)
            self.assertFalse(criou, f"{f} criou saida em --dry-run")


if __name__ == "__main__":
    unittest.main(verbosity=2)
