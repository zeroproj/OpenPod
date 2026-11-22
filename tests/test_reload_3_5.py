#!/usr/bin/env python3
"""Testes de aceite da ficha 028 (Reload 3.5).

Rode a mao (o `tools/ci.sh` tambem roda):

    python3 tests/test_reload_3_5.py -v

Cobre:

  - a receita `reload_3.5` e reproduzivel e o sha e o da imagem
    f0faee10...; o ultimo passo (fab_reload_3_5.py) rodado de novo sobre a
    3.3 da o mesmo byte a byte;
  - o diff contra a 3.3 so nos quatro ganchos, na tabela, na folha e no lote
    do SDK (0x1AB000..0x1FC000), sem tocar abaixo de 0xE000, no setor
    0xD000 nem na PSMP;
  - os quatro ganchos apontam para 0xDAB000/0xDAB200/0xDAB600/0xDAB700;
  - o SDK novo e o `jogos35` (13912 B), e o resto do lote e 0xFF;
  - as premissas do fab_reload_3_5.py recusam sha, gancho, tabela e folha
    errados, e recusam `--out` igual a `--in`;
  - o wrapper REAL do label da home (0xDAB700) roda no unicorn com a lista
    de timers do LVGL de mentira: copia o titulo de `msg+0x14`, devolve
    r3=0x00823EB0, preserva SP/PC e o texto;
  - o hook REAL do titulo (0xDAB600) so copia o rotulo `[view+0]`; o
    `[view+4]` (artista) nao vira titulo.
"""
import hashlib
import json
import os
import struct
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
sys.path.insert(0, os.path.join(RAIZ, "tests"))
import fab_reload_3_5 as F  # noqa: E402
import capa_album_asm as A  # noqa: E402
import fw_common as fw  # noqa: E402

ORIG = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
BUILD = os.path.join(RAIZ, "tools/build.py")
WORK = os.path.join(RAIZ, "sdk/build/test_3_5")
IMG33 = os.path.join(WORK, "reload_3_3.bin")
IMG35 = os.path.join(WORK, "reload_3_5_a.bin")
IMG35B = os.path.join(WORK, "reload_3_5_b.bin")
UP = os.path.join(RAIZ, "release/OpenPod-Reload-3.5-Diag",
                  "OpenPod_OpenPodReload3.5Diag.up")
SHA_35 = "f0faee10930e46cfd3338a265601ceee8323504925cf01f4926cf9465d95919d"
SHA_SDK35 = "8431fe15cf1705441f9969697584fedddc378eb61d4af067a5c85d7f748f6a6e"
SDK_TAM = 13912
MENU_NOVO, HOME_NOVO = 0xDAB000, 0xDAB200
TITLE_NOVO, LABEL_NOVO = 0xDAB600, 0xDAB700
TIMER_NOVO = 0xDAB800


def sha_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def build(receita, saida):
    r = subprocess.run([sys.executable, BUILD, "--receita", receita,
                        "--saida", saida], cwd=RAIZ,
                       capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(f"build {receita} falhou:\n{r.stdout}{r.stderr}")


class Reload35(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(WORK, exist_ok=True)
        if not os.path.exists(IMG33):
            build("reload_3.3", IMG33)
        build("reload_3.5", IMG35)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools",
                                                         "fab_reload_3_5.py"),
                            "--in", IMG33, "--out", IMG35B,
                            "--em", hex(F.LOTE_INI)], cwd=RAIZ,
                           capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(f"fab_reload_3_5 falhou:\n{r.stdout}{r.stderr}")
        with open(IMG33, "rb") as f:
            cls.o33 = f.read()
        with open(IMG35, "rb") as f:
            cls.o35 = f.read()
        with open(IMG35B, "rb") as f:
            cls.o35b = f.read()

    def test_repro_e_sha(self):
        self.assertEqual(sha_file(IMG35), SHA_35)
        self.assertEqual(self.o35, self.o35b)

    def test_diff_so_no_permitido(self):
        dif = [i for i in range(len(self.o33)) if self.o33[i] != self.o35[i]]
        self.assertTrue(dif)
        permitido = ((F.LOTE_INI, F.LOTE_FIM),
                     (F.PATCH_MENU - F.XIP, F.PATCH_MENU - F.XIP + 4),
                     (F.PATCH_HOME - F.XIP, F.PATCH_HOME - F.XIP + 4),
                     (F.PATCH_TITLE - F.XIP, F.PATCH_TITLE - F.XIP + 4),
                     (F.PATCH_HOME_LABEL - F.XIP,
                      F.PATCH_HOME_LABEL - F.XIP + 4),
                     (F.TABLE, F.TABLE + 36),
                     (F.SHEET_PX, F.SHEET_PX + F.SHEET_W * F.SHEET_H))
        fora = [i for i in dif if not any(a <= i < b for a, b in permitido)]
        self.assertEqual(fora, [], "mudou fora dos intervalos permitidos")
        self.assertTrue(all(i >= 0xE000 for i in dif))
        self.assertFalse(any(0xD000 <= i < 0xE000 for i in dif))
        self.assertFalse(any(i >= 0x1FC000 for i in dif))

    def test_ganchos(self):
        self.assertEqual(A.desvio(self.o35, F.PATCH_MENU - F.XIP),
                         ("bl", MENU_NOVO))
        self.assertEqual(A.desvio(self.o35, F.PATCH_HOME - F.XIP),
                         ("bl", HOME_NOVO))
        self.assertEqual(A.desvio(self.o35, F.PATCH_TITLE - F.XIP),
                         ("b.w", TITLE_NOVO))
        self.assertEqual(A.desvio(self.o35, F.PATCH_HOME_LABEL - F.XIP),
                         ("bl", LABEL_NOVO))

    def test_sdk(self):
        sdk = self.o35[F.LOTE_INI:F.LOTE_INI + SDK_TAM]
        self.assertEqual(len(sdk), SDK_TAM)
        self.assertEqual(hashlib.sha256(sdk).hexdigest(), SHA_SDK35)
        self.assertTrue(all(b == 0xFF
                            for b in self.o35[F.LOTE_INI + SDK_TAM:F.LOTE_FIM]))

    def test_tabela_e_folha(self):
        lida = [tuple(struct.unpack_from("<hh", self.o35,
                                          F.TABLE + i * 4))
                for i in range(9)]
        self.assertEqual(lida, F.TABLE_NOVO)
        pal = self.o33[F.SHEET_PAL:F.SHEET_PX]
        px = self.o33[F.SHEET_PX:F.SHEET_PX + F.SHEET_W * F.SHEET_H]
        esperado, k = F.folha_nova(px, pal)
        self.assertEqual(k, F.BLACK_IDX)
        self.assertEqual(self.o35[F.SHEET_PX:F.SHEET_PX +
                                  F.SHEET_W * F.SHEET_H], esperado)
        for antigo, altura, novo in F.FAIXAS:
            self.assertEqual(
                self.o35[F.SHEET_PX + F.SHEET_W * novo:
                         F.SHEET_PX + F.SHEET_W * (novo + altura)],
                self.o33[F.SHEET_PX + F.SHEET_W * antigo:
                         F.SHEET_PX + F.SHEET_W * (antigo + altura)])

    def test_premissas_recusam(self):
        d = bytearray(self.o33)
        d[0x1000] ^= 1
        self.assertTrue(F.confere_premissas(bytes(d)))

        d = bytearray(self.o33)
        d[F.PATCH_MENU - F.XIP] ^= 1
        self.assertTrue(F.confere_premissas(bytes(d)))

        d = bytearray(self.o33)
        d[F.TABLE] ^= 1
        self.assertTrue(F.confere_premissas(bytes(d)))

        d = bytearray(self.o33)
        d[F.SHEET_PX] ^= 1
        self.assertTrue(F.confere_premissas(bytes(d)))

        antes = sha_file(IMG33)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools",
                                                         "fab_reload_3_5.py"),
                            "--in", IMG33, "--out", IMG33], cwd=RAIZ,
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(sha_file(IMG33), antes)

    def test_kit_diag(self):
        with open(UP, "rb") as f:
            up = f.read()
        self.assertEqual(up[:6], b"CONFIG")
        self.assertEqual(struct.unpack_from("<I", up, 6)[0], 0x100)
        self.assertEqual(up[0x16:0x1C], b"SL6801")
        self.assertEqual(up[0xFE:0x100], b"\x55\xAA")
        tam = struct.unpack_from("<I", up, 0x10)[0]
        crc = struct.unpack_from("<H", up, 0x14)[0]
        self.assertEqual(len(up), 0x100 + tam)
        payload = up[0x100:]
        self.assertEqual(tam, 0x1AF000)
        self.assertEqual(crc, fw.crc16(payload))
        self.assertLessEqual(0x1AF000, 0x1FC000)
        self.assertEqual(payload[0x1A4F00:0x1A4F10], b"Reload 3.5 Diag\0")
        dif = [i for i in range(tam) if payload[i] != self.o35[i]]
        permitido = ((0x1A4F00, 0x1A4F10), (0x10A59C, 0x10A5A0))
        fora = [i for i in dif if not any(a <= i < b for a, b in permitido)]
        self.assertEqual(fora, [], "o .up mudou fora do carimbo")
        self.assertTrue(dif)

    def _roda(self, addr, regs, mem):
        from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB,
                             UC_HOOK_BLOCK)
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                       UC_ARM_REG_R3, UC_ARM_REG_PC,
                                       UC_ARM_REG_SP, UC_ARM_REG_LR)
        XIP, PILHA, FIM = 0x00C00000, 0x20000000, 0x10000000
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(XIP, 0x200000)
        u.mem_write(XIP, self.o35)
        u.mem_map(0x00800000, 0x40000)
        u.mem_map(PILHA, 0x1000)
        u.mem_map(FIM, 0x1000)
        for a, b in mem.items():
            u.mem_write(a, b)
        u.reg_write(UC_ARM_REG_SP, PILHA + 0x800)
        u.reg_write(UC_ARM_REG_LR, FIM | 1)
        for reg, val in regs.items():
            u.reg_write(reg, val)

        def bloco(uc, a, tam, _ud):
            if a == FIM:
                uc.emu_stop()
            elif not (XIP <= a < XIP + 0x200000):
                raise AssertionError(f"executou fora da flash: 0x{a:08X}")

        u.hook_add(UC_HOOK_BLOCK, bloco)
        u.emu_start(addr | 1, FIM | 1, count=2000)
        return u

    def _lista_de_timers(self, estado, node):
        mem = {
            0x0081D2D4: struct.pack("<I", 0x18),
            0x0081D2D8: struct.pack("<I", node),
            0x0081D2DC: struct.pack("<I", node),
            node + 8: struct.pack("<I", TIMER_NOVO | 1),
            node + 0xC: struct.pack("<I", estado),
            node + 0x18: struct.pack("<I", 0),
            node + 0x1C: struct.pack("<I", 0),
        }
        return mem

    def test_wrapper_home_real(self):
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R3,
                                       UC_ARM_REG_PC, UC_ARM_REG_SP)
        estado, node, msg = 0x00803000, 0x00804000, 0x00805000
        mem = self._lista_de_timers(estado, node)
        mem[estado] = struct.pack("<I", 0x4F503335)
        mem[msg + 0x14] = b"Teste\0"
        u = self._roda(LABEL_NOVO, {UC_ARM_REG_R0: msg}, mem)
        self.assertEqual(u.mem_read(estado + 4, 6), b"Teste\0")
        self.assertEqual(u.reg_read(UC_ARM_REG_R3), 0x00823EB0)
        self.assertEqual(u.reg_read(UC_ARM_REG_SP), 0x20000800)
        self.assertEqual(u.reg_read(UC_ARM_REG_PC), 0x10000000)

    def test_titulo_so_do_rotulo_zero(self):
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                       UC_ARM_REG_PC)
        estado, node, msg = 0x00803000, 0x00804000, 0x00805000
        ctx, view = 0x00807000, 0x00806000
        mem = self._lista_de_timers(estado, node)
        mem[estado] = struct.pack("<I", 0x4F503335)
        mem[0x0081CE2C] = struct.pack("<I", ctx)
        mem[ctx + 0xAC] = struct.pack("<I", view)
        mem[view] = struct.pack("<I", 0x1234)
        mem[view + 4] = struct.pack("<I", 0x5678)
        mem[msg + 0x14] = b"Musica\0"
        mem[0x00D5ED94] = b"\x70\x47"  # lv_label_set_text: bx lr

        u = self._roda(TITLE_NOVO, {
            UC_ARM_REG_R0: 0x1234, UC_ARM_REG_R1: msg + 0x14,
        }, mem)
        self.assertEqual(u.mem_read(estado + 4, 7), b"Musica\0")
        self.assertEqual(u.reg_read(UC_ARM_REG_PC), 0x10000000)

        mem[msg + 0x14] = b"Artista\0"
        u = self._roda(TITLE_NOVO, {
            UC_ARM_REG_R0: 0x5678, UC_ARM_REG_R1: msg + 0x14,
        }, mem)
        self.assertEqual(u.mem_read(estado + 4, 7), b"\0" * 7)
        self.assertEqual(u.reg_read(UC_ARM_REG_PC), 0x10000000)


if __name__ == "__main__":
    unittest.main()
