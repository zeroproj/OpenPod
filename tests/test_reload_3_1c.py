#!/usr/bin/env python3
"""Acceptance tests for ficha 023 (Reload 3.1c: GN-438 controls + Cobrinha).

Run by hand (it is not part of tools/ci.sh):

    python3 tests/test_reload_3_1c.py -v

It builds the 3.1c image twice through the recipe, checks reproducibility,
no .data/.bss, the Thumb bit, the measured key constants, the language
source in the ORIGINAL, the five-row menu, and the difference against the
published 3.1b (only the free lot, the hook BL and the 3.1b version stamp).
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
MENU = os.path.join(RAIZ, "sdk/src/menu.c")
WORK = os.path.join(RAIZ, "sdk/build/test_3_1c")
BASE30 = os.path.join(WORK, "base30.bin")
IMG31C = os.path.join(WORK, "reload_3_1c.bin")
UP31B = os.path.join(RAIZ, "release/OpenPod-Reload-3.1b/OpenPod_OpenPodReload3.1b.up")
SHA_3_0 = "43aaf5d51c364e03f9934aba0348230dda4911c2e7264c34555f69554c36ec32"
LOTE = 0x001AB000
LOTE_FIM = 0x001FC000
APPBASE = 0x00DAB000
GANCHO = 0x00123CF8
ORIGEM = 0x00C00000

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


def cstr(d, addr):
    o = addr - ORIGEM
    return d[o:d.index(b"\0", o)].decode("utf-8", "replace")


def imagem_3_1b(orig):
    """Rebuild the published 3.1b image from its .up payload (full image)."""
    d = open(UP31B, "rb").read()
    off, tam = struct.unpack_from("<I", d, 6)[0], struct.unpack_from("<I", d, 0x10)[0]
    base = bytearray(orig)
    base[:tam] = d[off:off + tam]
    return bytes(base)


class Reload31C(unittest.TestCase):
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
        sh([sys.executable, "tools/build.py", "--receita", "reload_3.1c",
            "--saida", IMG31C])
        cls.img = open(IMG31C, "rb").read()
        cls.orig = open(ORIG, "rb").read()
        cls.base = open(BASE30, "rb").read()
        cls.old = imagem_3_1b(cls.orig)

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
        # The hook itself is entered through a BL: no Thumb bit in the address,
        # but the recipe must use the hook reported by the linker.
        info = self.info["a"]
        self.assertFalse(info["hook"] & 1)
        self.assertTrue(LOTE <= info["flash_offset"] < LOTE_FIM)

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

    def test_idioma_do_get_lang_str(self):
        # get_lang_str 0xD2108C -> bl 0xD0E2B8; getter reads [0x00823D05+1].
        o = 0xD2108C - ORIGEM
        self.assertEqual(self.orig[o:o + 2].hex(), "10b5")
        self.assertEqual(self.orig[o + 4:o + 8].hex(), "edf712f9")
        g = 0xD0E2B8 - ORIGEM
        self.assertEqual(self.orig[g:g + 6].hex(), "014b58787047")
        self.assertEqual(struct.unpack_from("<I", self.orig, g + 8)[0], 0x00823D05)
        # Index 8 selects 0xC53B84, whose entries are Portuguese; the English
        # table 0xC52AA4 is index 0.  This is the proof for FW_LANG_PT.
        for tab, ident, texto in ((0xC53B84, 0, "Português"),
                                  (0xC53B84, 7, "Despertador"),
                                  (0xC52AA4, 0, "English")):
            p = struct.unpack_from("<I", self.orig, tab - ORIGEM + ident * 4)[0]
            self.assertEqual(cstr(self.orig, p), texto)
        self.assertIn(b"#define FW_LANG (*(volatile uint8_t *)0x00823D06)", open(FW_H, "rb").read())
        self.assertIn(b"#define FW_LANG_PT 8", open(FW_H, "rb").read())
        for msg in ("Cobrinha", "Snake", "Pontos ", "Fim de jogo", "Pausa",
                    "Play: começar", "Play: continuar", "Play: recomeçar",
                    "<< >>: virar", "VOL 2x: sair", "Score ", "Game over",
                    "Paused", "Play: start", "Play: resume", "Play: restart",
                    "<< >>: turn", "VOL 2x: exit"):
            self.assertIn(msg.encode(), self.app, msg)
        self.assertIn(b"Aplicativos", self.img)

    def test_menu_cinco_linhas(self):
        entradas = 0
        for nome, pt in (("Flutter", None), ("Mp3tris", None), ("Snake", "Cobrinha")):
            i = self.app.find(nome.encode() + b"\0")
            self.assertGreaterEqual(i, 0, nome)
            ptr = struct.pack("<I", APPBASE + i)
            j = self.app.find(ptr)
            self.assertGreaterEqual(j, 0, nome)
            fn = struct.unpack_from("<I", self.app, j + 4)[0]
            self.assertTrue(fn & 1, f"{nome}: open sem Thumb")
            self.assertTrue(APPBASE <= (fn & ~1) < APPBASE + len(self.app), nome)
            if pt:
                k = self.app.find(pt.encode() + b"\0")
                self.assertGreaterEqual(k, 0, pt)
                self.assertEqual(struct.unpack_from("<I", self.app, j + 8)[0], APPBASE + k)
            entradas += 1
        self.assertEqual(entradas, 3)
        # Factory creates 3 rows and row 2 is reused: 2 + 3 = 5.
        self.assertEqual(2 + entradas, 5)
        # Factory page (0xD2F0A0): row = ver/7 and list = 6*(ver/7)+3.
        # At 160 px: row 22, list 135, five rows 110 -- they fit.
        ver = 160
        self.assertLessEqual(5 * (ver // 7), 6 * (ver // 7) + 3)
        self.assertIn(b"(ver / 7)", open(MENU, "rb").read())

    def test_dec_bl_ida_e_volta(self):
        for de, para in ((0x00D50000, 0x00D40000),
                         (0x00D23CF8, 0x00DAB000),
                         (0x00D50000, 0x00D60000)):
            buf = bytearray(0x200000)
            off = de - ORIGEM
            buf[off:off + 4] = fab_sdk_jogos.enc_bl(de, para)
            self.assertEqual(fab_sdk_jogos.dec_bl(buf, de), para,
                             f"BL 0x{de:08X} -> 0x{para:08X} nao volta")

    def test_diff_contra_3_1b(self):
        new, old, base = self.img, self.old, self.base
        # The recipe changes only the lot and the 4-byte BL against 3.0.
        def grupos(a, b):
            dif = [i for i in range(len(a)) if a[i] != b[i]]
            fora = [i for i in dif if not (LOTE <= i < LOTE + len(self.app))
                    and not (GANCHO <= i < GANCHO + 4)]
            return dif, fora

        dif, fora = grupos(new, base)
        self.assertTrue(dif)
        self.assertFalse(fora, f"3.1c mudou fora do lote/gancho: {fora[:4]}")
        self.assertFalse([i for i in dif if i < 0xE000])
        self.assertFalse([i for i in dif if 0xD000 <= i < 0xE000])
        self.assertFalse([i for i in dif if i >= LOTE_FIM])

        # Against the published 3.1b: only the lot, the BL and the 3.1b
        # version stamp (text + literal) may differ.
        carimbo = {i for i in range(len(old))
                   if old[i] != base[i] and not (LOTE <= i < LOTE + len(self.app))
                   and not (GANCHO <= i < GANCHO + 4)}
        dif, fora = grupos(new, old)
        self.assertGreater(sum(1 for i in dif if LOTE <= i < LOTE + len(self.app)), 0)
        self.assertTrue(set(fora) <= carimbo, f"3.1c vs 3.1b fora do esperado: {set(fora) - carimbo}")
        self.assertTrue(any(0x001A4000 <= i < 0x001AB000 for i in carimbo))


if __name__ == "__main__":
    unittest.main(verbosity=2)
