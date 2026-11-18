#!/usr/bin/env python3
"""Acceptance tests for ficha 022 (OpenPod Reload 3.1: SDK + games).

Run by hand (it is not part of tools/ci.sh):

    python3 tests/test_reload_3_1.py -v

It builds the 3.0 image, builds both SDK variants twice (reproducibility),
runs the fabrication tool and checks the premises, the lot, the hook, the
Thumb bits of the function symbols and the 3.0 image outside the lot.
"""
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import build_sdk

ORIG = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
FW_H = os.path.join(RAIZ, "sdk/include/fw.h")
WORK = os.path.join(RAIZ, "sdk/build/test")
BASE30 = os.path.join(WORK, "base30.bin")
SHA_3_0 = "43aaf5d51c364e03f9934aba0348230dda4911c2e7264c34555f69554c36ec32"
LOTE = 0x001AB000
LOTE_FIM = 0x001FC000
GANCHO = 0x00123CF8
FABRICA = 0x00D2F0A0

# First 4 bytes of every function in fw.h, read from the ORIGINAL (XIP).
PROLOGOS = {
    "lv_mem_alloc": "30b50546",
    "lv_mem_free": "044b9842",
    "lv_disp_get_scr_act": "13b50446",
    "lv_disp_get_layer_top": "13b50446",
    "lv_disp_get_hor_res": "10b9084b",
    "lv_disp_get_ver_res": "10b9084b",
    "lv_obj_create": "10b50146",
    "lv_obj_del": "f7b50646",
    "lv_obj_set_size": "38b50446",
    "lv_obj_set_width": "37b50023",
    "lv_obj_set_height": "37b50023",
    "lv_obj_set_pos": "38b50446",
    "lv_obj_align": "70b50446",
    "lv_obj_add_flag": "f8b50d46",
    "lv_obj_clear_flag": "70b50446",
    "lv_obj_invalidate": "37b50446",
    "lv_obj_get_width": "038b808a",
    "fw_obj_parent": "00b14068",
    "lv_timer_create": "f0b50646",
    "lv_timer_del": "10b50146",
    "lv_tick_get": "044b1868",
    "lv_obj_add_event_cb": "2de9ff41",
    "lv_obj_remove_event_cb": "f0b58468",
    "lv_obj_set_style_align": "13460a46",
    "lv_obj_set_style_pad_top": "13460a46",
    "lv_obj_set_style_pad_bottom": "13460a46",
    "lv_obj_set_style_pad_left": "13460a46",
    "lv_obj_set_style_pad_right": "13460a46",
    "lv_obj_set_style_radius": "13460a46",
    "lv_obj_set_style_bg_color": "17b40023",
    "lv_obj_set_style_bg_opa": "13460a46",
    "lv_obj_set_style_border_color": "17b40023",
    "lv_obj_set_style_border_width": "13460a46",
    "lv_obj_set_style_border_side": "13460a46",
    "lv_obj_set_style_text_color": "17b40023",
    "lv_obj_set_style_text_font": "13460a46",
    "lv_obj_set_style_text_align": "13460a46",
    "lv_label_create": "10b50146",
    "lv_label_set_text": "f0b50446",
    "lv_label_set_long_mode": "38b50446",
    "lv_img_create": "10b50146",
    "lv_img_set_src": "2de9f041",
    "lv_event_get_code": "007a7047",
    "lv_event_get_param": "00697047",
    "lv_group_get_default": "014b1868",
    "lv_group_add_obj": "7fb50c46",
    "lv_group_focus_obj": "f8b50646",
    "lv_group_focus_next": "037edb07",
    "lv_group_focus_prev": "037edb07",
    "lv_group_get_focused": "10b1c068",
    "FW_MENU_PAGE_CREATE": "2de9f04f",
    "FW_MENU_LIST_ITEM_CREATE": "10b53af0",
    "FW_MENU_LIST_ITEM_LAYOUT": "70b50446",
}


def sh(cmd, ok=True):
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True)
    if ok and r.returncode:
        raise AssertionError(f"falhou: {' '.join(cmd)}\n{r.stdout}{r.stderr}")
    return r


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def dec_bl(d, addr):
    h1, h2 = struct.unpack_from("<HH", d, addr - 0x00C00000)
    assert (h1 & 0xF800) == 0xF000 and (h2 & 0xD000) == 0xD000, "nao e bl"
    s = (h1 >> 10) & 1
    i1, i2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    j1, j2 = 1 - i1, 1 - i2
    imm = (s << 24) | (j1 << 23) | (j2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if imm & (1 << 24):
        imm -= 1 << 25
    return (addr + 4 + imm) & 0xFFFFFFFF


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
            if name and shndx and (info & 0xF) == 2:  # STT_FUNC defined
                n = d[st[4] + name:d.index(0, st[4] + name)].decode()
                out.append((n, value))
    return out


class Reload31(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(WORK, exist_ok=True)
        if not os.path.exists(BASE30) or sha_file(BASE30) != SHA_3_0:
            sh([sys.executable, "tools/build.py", "--receita", "reload_3.0",
                "--saida", BASE30])
        cls.info, cls.images, cls.bins = {}, {}, {}
        for v in ("diag", "jogos"):
            d1 = build_sdk.build(v, os.path.join(WORK, v + "_a"))[0]
            d2 = build_sdk.build(v, os.path.join(WORK, v + "_b"))[0]
            assert d1["sha256"] == d2["sha256"], "build nao reproduzivel"
            out = os.path.join(WORK, v + ".bin")
            if os.path.exists(out):
                os.remove(out)
            r = sh([sys.executable, "tools/fab_sdk_jogos.py", "--in", BASE30,
                    "--out", out, "--variante", v,
                    "--build-dir", os.path.join(WORK, v + "_fab")], ok=False)
            assert r.returncode == 0, r.stdout + r.stderr
            cls.info[v] = d1
            cls.images[v] = open(out, "rb").read()
            cls.bins[v] = open(os.path.join(WORK, v + "_a", "app.bin"), "rb").read()
        cls.base = open(BASE30, "rb").read()

    def test_repro(self):
        for v in ("diag", "jogos"):
            a = sha_file(os.path.join(WORK, v + "_a", "app.bin"))
            b = sha_file(os.path.join(WORK, v + "_b", "app.bin"))
            self.assertEqual(a, b)

    def test_sem_data_bss(self):
        for v in ("diag", "jogos"):
            secs = elf_sections(os.path.join(WORK, v + "_a", "app.elf"))
            for n in (".data", ".bss"):
                self.assertEqual(secs[n][5] if n in secs else 0, 0, f"{v} {n}")

    def test_fw_h_addresses(self):
        orig = open(ORIG, "rb").read()
        names = set()
        for line in open(FW_H):
            m = re.search(r"#define\s+(\w+)\s+FW_FN\((0x[0-9A-Fa-f]+)", line)
            if not m:
                continue
            name, addr = m.group(1), int(m.group(2), 16)
            names.add(name)
            if addr < 0x00C00000:
                self.assertEqual(name, "fw_log", f"{name} fora da XIP")
                continue
            self.assertIn(name, PROLOGOS, f"sem prologo esperado para {name}")
            got = orig[addr - 0x00C00000:addr - 0x00C00000 + 4].hex()
            self.assertEqual(got, PROLOGOS[name], f"{name} 0x{addr:08X}")
        self.assertEqual(names, set(PROLOGOS) | {"fw_log"})
        # FW_PAGE_MENU_EVENT_CB has an explicit Thumb bit and no FW_FN.
        self.assertEqual(orig[0xD2EF5C - 0x00C00000:0xD2EF5C - 0x00C00000 + 4].hex(),
                         "454b1b68")
        # fw_log is the boot ROM printf; the factory event cb calls it.
        self.assertEqual(orig[0xD2EF72 - 0x00C00000:0xD2EF72 - 0x00C00000 + 4].hex(),
                         "d1f69d91")

    def test_thumb_symbols(self):
        for v in ("diag", "jogos"):
            objdir = os.path.join(WORK, v + "_a", "obj")
            n = 0
            for root, _dirs, files in os.walk(objdir):
                for f in files:
                    if not f.endswith(".o"):
                        continue
                    for name, value in func_symbols(os.path.join(root, f)):
                        n += 1
                        self.assertTrue(value & 1, f"{v}:{name} sem bit Thumb")
            self.assertGreater(n, 0)

    def test_app_table_thumb(self):
        for v, names in (("diag", ("Teste de teclas",)),
                         ("jogos", ("Flutter", "Mp3tris"))):
            for name in names:
                s = name.encode() + b"\0"
                i = self.bins[v].find(s)
                self.assertGreaterEqual(i, 0, f"{v}: string {name}")
                ptr = struct.pack("<I", 0x00DAB000 + i)
                j = self.bins[v].find(ptr)
                self.assertGreaterEqual(j, 0, f"{v}: ponteiro para {name}")
                fn = struct.unpack_from("<I", self.bins[v], j + 4)[0]
                self.assertTrue(fn & 1, f"{v}: {name} open sem Thumb")
                self.assertTrue(0x00DAB000 <= (fn & ~1) < 0x00DAB000 + len(self.bins[v]),
                                f"{v}: {name} open fora do lote")

    def test_hooks(self):
        for v in ("diag", "jogos"):
            d = self.images[v]
            info = self.info[v]
            hook = dec_bl(d, GANCHO + 0x00C00000)
            self.assertEqual(hook, info["hook"])
            self.assertTrue(0x00DAB000 <= hook < 0x00DAB000 + len(self.bins[v]))
            self.assertFalse(hook & 1)
            self.assertEqual(d[LOTE:LOTE + len(self.bins[v])], self.bins[v])
            dif = [i for i in range(len(d)) if d[i] != self.base[i]]
            allow = set(range(LOTE, LOTE + len(self.bins[v]))) | set(range(GANCHO, GANCHO + 4))
            self.assertFalse([i for i in dif if i not in allow], "mudou fora do lote")
            self.assertFalse([i for i in dif if i < 0xE000], "mudou abaixo de 0xE000")
            self.assertFalse([i for i in dif if 0xD000 <= i < 0xE000], "tocou 0xD000")
            self.assertFalse([i for i in dif if i >= 0x001FC000], "tocou a PSMP")

    def test_premissas_recusam(self):
        casos = []
        ruim = bytearray(self.base)
        ruim[GANCHO:GANCHO + 4] = b"\x00\x00\x00\x00"
        p = os.path.join(WORK, "ruim_hook.bin")
        open(p, "wb").write(ruim)
        casos.append(p)
        ruim = bytearray(self.base)
        ruim[LOTE] ^= 0xFF
        p = os.path.join(WORK, "ruim_lote.bin")
        open(p, "wb").write(ruim)
        casos.append(p)
        ruim = bytearray(self.base)
        ruim[0x00100000] ^= 0xFF
        p = os.path.join(WORK, "ruim_sha.bin")
        open(p, "wb").write(ruim)
        casos.append(p)
        for i, inp in enumerate(casos):
            out = os.path.join(WORK, f"nao_deve_{i}.bin")
            if os.path.exists(out):
                os.remove(out)
            r = sh([sys.executable, "tools/fab_sdk_jogos.py", "--in", inp,
                    "--out", out, "--variante", "diag",
                    "--build-dir", os.path.join(WORK, "diag_fab")], ok=False)
            self.assertNotEqual(r.returncode, 0, inp)
            self.assertFalse(os.path.exists(out), "criou saida em premissa falha")
        out = os.path.join(WORK, "mesmo.bin")
        open(out, "wb").write(self.base)
        r = sh([sys.executable, "tools/fab_sdk_jogos.py", "--in", out,
                "--out", out, "--variante", "diag",
                "--build-dir", os.path.join(WORK, "diag_fab")], ok=False)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
