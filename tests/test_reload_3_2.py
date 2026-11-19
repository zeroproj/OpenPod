#!/usr/bin/env python3
"""Acceptance tests for ficha 024 (Reload 3.2, Parte A: direcoes absolutas).

Run by hand (it is not part of tools/ci.sh):

    python3 tests/test_reload_3_2.py -v

The test builds the 3.2 image twice through the recipe, checks
reproducibility, no .data/.bss, the Thumb bit, the absolute direction map in
the Cobrinha source, the bilingual help text, and the difference against the
published 3.1c (only the free lot, the hook BL and the 3.1c version stamp).
"""
import hashlib
import os
import re
import struct
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import build_sdk
import fab_sdk_jogos

ORIG = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
FW_H = os.path.join(RAIZ, "sdk/include/fw.h")
COBRA = os.path.join(RAIZ, "sdk/apps/cobrinha/main.c")
BUILD = os.path.join(RAIZ, "tools/build.py")
WORK = os.path.join(RAIZ, "sdk/build/test_3_2")
BASE30 = os.path.join(WORK, "base30.bin")
IMG32 = os.path.join(WORK, "reload_3_2.bin")
UP31C = os.path.join(RAIZ, "release/OpenPod-Reload-3.1c/OpenPod_OpenPodReload3.1c.up")
SHA_3_0 = "43aaf5d51c364e03f9934aba0348230dda4911c2e7264c34555f69554c36ec32"
LOTE = 0x001AB000
LOTE_FIM = 0x001FC000
APPBASE = 0x00DAB000
GANCHO = 0x00123CF8
ORIGEM = 0x00C00000
PSMP = 0x001FC000

CHAVES = {
    "FW_KEY_M": 0xA0,
    "FW_KEY_M_LONG": 0xA2,
    "FW_KEY_PREV": 0x14,
    "FW_KEY_NEXT": 0x13,
    "FW_KEY_PREV_LONG": 0x87,
    "FW_KEY_NEXT_LONG": 0x89,
    "FW_KEY_PLAY": 0x0A,
    "FW_KEY_BACK": 0x81,
}


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def sh(cmd, ok=True):
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True)
    if ok and r.returncode:
        raise AssertionError(f"falhou: {' '.join(cmd)}\n{r.stdout}{r.stderr}")
    return r


def elf_sections(path):
    d = open(path, "rb").read()
    shoff, = struct.unpack_from("<I", d, 0x20)
    shent, shnum, shstr = struct.unpack_from("<HHH", d, 0x2E)
    secs = [struct.unpack_from("<IIIIIIIIII", d, shoff + i * shent) for i in range(shnum)]
    st = secs[shstr]
    out = {}
    for s in secs:
        n = d[st[4] + s[0]:d.index(0, st[4] + s[0])].decode()
        out[n] = s
    return out


def func_symbols(path):
    d = open(path, "rb").read()
    shoff, = struct.unpack_from("<I", d, 0x20)
    shent, shnum = struct.unpack_from("<HH", d, 0x2E)
    secs = [struct.unpack_from("<IIIIIIIIII", d, shoff + i * shent) for i in range(shnum)]
    out = []
    for s in secs:
        if s[1] != 2:
            continue
        st = secs[s[6]]
        for o in range(s[4], s[4] + s[5], 16):
            name, value, _size, info, _other, shndx = struct.unpack_from("<IIIBBH", d, o)
            if name and shndx and (info & 0xF) == 2:
                out.append((d[st[4] + name:d.index(0, st[4] + name)].decode(), value))
    return out


def imagem_3_1c(orig):
    """Rebuild the published 3.1c image from its .up payload (full image)."""
    d = open(UP31C, "rb").read()
    off, tam = struct.unpack_from("<I", d, 6)[0], struct.unpack_from("<I", d, 0x10)[0]
    base = bytearray(orig)
    base[:tam] = d[off:off + tam]
    return bytes(base)


class Reload32(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(WORK, exist_ok=True)
        if not os.path.exists(BASE30) or sha_file(BASE30) != SHA_3_0:
            sh([sys.executable, "tools/build.py", "--receita", "reload_3.0",
                "--saida", BASE30])
        cls.info, cls.bins = {}, {}
        for suf in ("a", "b"):
            cls.info[suf] = build_sdk.build("jogos", os.path.join(WORK, "sdk_" + suf))[0]
        cls.app = open(os.path.join(WORK, "sdk_a", "app.bin"), "rb").read()
        sh([sys.executable, "tools/build.py", "--receita", "reload_3.2",
            "--saida", IMG32])
        cls.img = open(IMG32, "rb").read()
        cls.orig = open(ORIG, "rb").read()
        cls.base = open(BASE30, "rb").read()
        cls.old = imagem_3_1c(cls.orig)

    def test_repro_sem_data_bss_thumb(self):
        self.assertEqual(self.info["a"]["sha256"], self.info["b"]["sha256"])
        for suf in ("a", "b"):
            secs = elf_sections(os.path.join(WORK, "sdk_" + suf, "app.elf"))
            for n in (".data", ".bss"):
                self.assertEqual(secs[n][5] if n in secs else 0, 0, n)
        n = 0
        for root, _dirs, files in os.walk(os.path.join(WORK, "sdk_a", "obj")):
            for f in files:
                if f.endswith(".o"):
                    for name, value in func_symbols(os.path.join(root, f)):
                        n += 1
                        self.assertTrue(value & 1, f"{name} sem bit Thumb")
        self.assertGreater(n, 0)
        info = self.info["a"]
        self.assertFalse(info["hook"] & 1)
        self.assertTrue(APPBASE <= info["hook"] < APPBASE + info["size"])
        self.assertTrue(LOTE <= info["flash_offset"] < LOTE_FIM)

    def test_receita_existe(self):
        src = open(BUILD).read()
        self.assertIn('"reload_3.2": RELOAD_3_2', src)
        self.assertIn('"fab_sdk_jogos.py", ["--variante", "jogos"]', src)

    def test_direcoes_absolutas_na_fonte(self):
        src = open(COBRA).read()
        self.assertIn("static void turn_abs(game_t *g, uint8_t d)", src)
        self.assertIn("if (g->state != PLAYING || g->next_dir != g->dir)", src)
        self.assertIn("if (d == ((g->dir + 2) & 3))", src)
        self.assertIn("case FW_KEY_PREV:\n\tcase FW_KEY_PREV_LONG:\n\t\tturn_abs(g, 2);", src)
        self.assertIn("case FW_KEY_NEXT:\n\tcase FW_KEY_NEXT_LONG:\n\t\tturn_abs(g, 0);", src)
        self.assertIn("case FW_KEY_M:\n\t\tturn_abs(g, 3);", src)
        self.assertIn("case FW_KEY_M_LONG:\n\t\ttoggle_pause(g);", src)
        self.assertIn("case FW_KEY_PLAY:\n\t\tif (g->press_handled)", src)
        self.assertIn("play_key(g);", src)
        self.assertIn("turn_abs(g, 1); /* down */", src)
        self.assertNotIn("static void turn(game_t *g, uint8_t delta)", src)
        self.assertNotIn("play_action", src)
        # The pressed event must not pause: it is Play (start/restart/down).
        m = re.search(r"if \(code == LV_EVENT_PRESSED\) \{(.*?)\}", src, re.S)
        self.assertIsNotNone(m)
        self.assertIn("play_key(g);", m.group(1))
        self.assertNotIn("toggle_pause", m.group(1))

    def test_ajuda_bilingue_e_caixa(self):
        src = open(COBRA).read()
        self.assertIn("#define MSG_H 112", src)
        self.assertIn("MSG_H, lv_rgb", src)
        self.assertIn("(FIELD_H - MSG_H) / 2", src)
        self.assertIn("Play: baixo\\nM: cima\\n<<: esquerda\\n>>: direita\\nSegure M: pausa\\nVOL 2x: sair", src)
        self.assertIn("Play: down\\nM: up\\n<<: left\\n>>: right\\nHold M: pause\\nVOL 2x: exit", src)
        self.assertIn("Segure M: continuar", src)
        self.assertIn("Hold M: resume", src)
        self.assertNotIn("<< >>: virar", src)
        self.assertNotIn("<< >>: turn", src)
        for msg in ("Play: baixo", "M: cima", "esquerda", "direita",
                    "Segure M: pausa", "Play: down", "M: up", "left", "right",
                    "Hold M: pause"):
            self.assertIn(msg.encode(), self.app, msg)

    def test_chaves_medidas(self):
        src = open(FW_H).read()
        for nome, valor in CHAVES.items():
            m = re.search(r"#define\s+%s\s+(0x[0-9A-Fa-f]+)" % nome, src)
            self.assertIsNotNone(m, nome)
            self.assertEqual(int(m.group(1), 16), valor, nome)
        for p in ("sdk/apps/keytest/main.c", "sdk/apps/mp3tris/main.c",
                  "sdk/apps/flutter/main.c", "sdk/apps/cobrinha/main.c"):
            s = open(os.path.join(RAIZ, p)).read()
            self.assertIsNone(re.search(r"FW_KEY_UP|FW_KEY_DOWN|LV_KEY_UP|LV_KEY_DOWN|0x11|0x12", s),
                              f"{p} ainda usa cima/baixo")

    def test_diff_contra_3_0_e_3_1c(self):
        new, old, base = self.img, self.old, self.base

        def grupos(a, b):
            dif = [i for i in range(len(a)) if a[i] != b[i]]
            fora = [i for i in dif if not (LOTE <= i < LOTE + len(self.app))
                    and not (GANCHO <= i < GANCHO + 4)]
            return dif, fora

        dif, fora = grupos(new, base)
        self.assertTrue(dif)
        self.assertFalse(fora, f"3.2 mudou fora do lote/gancho: {fora[:4]}")
        self.assertFalse([i for i in dif if i < 0xE000])
        self.assertFalse([i for i in dif if 0xD000 <= i < 0xE000])
        self.assertFalse([i for i in dif if i >= LOTE_FIM])

        # The published 3.1c carries its own version stamp.  Against it, only
        # the lot, the BL and those stamp bytes may differ.
        carimbo = {i for i in range(len(old))
                   if old[i] != base[i] and not (LOTE <= i < LOTE + len(self.app))
                   and not (GANCHO <= i < GANCHO + 4)}
        dif, fora = grupos(new, old)
        self.assertGreater(sum(1 for i in dif if LOTE <= i < LOTE + len(self.app)), 0)
        self.assertTrue(set(fora) <= carimbo,
                        f"3.2 vs 3.1c fora do esperado: {set(fora) - carimbo}")

        # Hook: the recipe must point the factory BL at the SDK entry.
        self.assertEqual(fab_sdk_jogos.dec_bl(new, GANCHO + ORIGEM), self.info["a"]["hook"])
        # PSMP and the 0xD000 sector are factory bytes, not ours.
        self.assertEqual(new[0xD000:0xE000], self.orig[0xD000:0xE000])
        self.assertEqual(new[PSMP:], self.orig[PSMP:])


if __name__ == "__main__":
    unittest.main(verbosity=2)
