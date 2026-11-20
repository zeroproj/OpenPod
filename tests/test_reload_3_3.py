#!/usr/bin/env python3
"""Testes de aceite da ficha 025 (Reload 3.3, Parte 0).

Rode a mao:

    python3 tests/test_reload_3_3.py -v

Nao entra no tools/ci.sh (que e protegido); o teste cobre:

  - a receita 3.3 e reproduzivel e difere da 3.2 so nos quatro intervalos
    do lote da capa (alloc, os dois FREE e o trampolim), sem tocar abaixo
    de 0xE000, no setor 0xD000 nem na PSMP;
  - o `bl` do `corpo_cria` aponta para o trampolim e o trampolim usa
    `lv_mem_alloc`/`memset` (provados por capstone);
  - o trampolim, em unicorn, chama `lv_mem_alloc(0x2210)`, zera os
    `0x2210` B e devolve o ponteiro; se o alocador devolve 0, nao chama
    o memset e devolve 0 (o `cmp r7,#0` de fabrica leva ao cinza);
  - `corpo_cria` e `corpo_apaga` nao chamam mais `0xCF7840`/`0xCF7885`
    (heap do FreeRTOS na CPU1), mas o `carrega_capa` da CPU0 continua
    chamando o heap de fabrica.
"""
import hashlib
import os
import struct
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import fab_reload_3_3 as F  # noqa: E402
import capa_album_asm as A  # noqa: E402

ORIG = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
BUILD = os.path.join(RAIZ, "tools/build.py")
WORK = os.path.join(RAIZ, "sdk/build/test_3_3")
IMG32 = os.path.join(WORK, "reload_3_2.bin")
IMG33A = os.path.join(WORK, "reload_3_3_a.bin")
IMG33B = os.path.join(WORK, "reload_3_3_b.bin")


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def build(receita, saida):
    r = subprocess.run([sys.executable, BUILD, "--receita", receita,
                        "--saida", saida], cwd=RAIZ,
                       capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(f"build {receita} falhou:\n{r.stdout}{r.stderr}")


class Reload33(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(WORK, exist_ok=True)
        if not os.path.exists(IMG32):
            build("reload_3.2", IMG32)
        build("reload_3.3", IMG33A)
        build("reload_3.3", IMG33B)
        cls.o32 = open(IMG32, "rb").read()
        cls.o33 = open(IMG33A, "rb").read()
        cls.o33b = open(IMG33B, "rb").read()

    def test_repro(self):
        self.assertEqual(sha_file(IMG33A), sha_file(IMG33B))

    def test_diff_so_no_lote_da_capa(self):
        self.assertEqual(len(self.o32), len(self.o33))
        dif = [i for i in range(len(self.o32)) if self.o32[i] != self.o33[i]]
        self.assertTrue(dif)
        permitido = ((F.ALLOC, F.ALLOC + 16), (F.FREE1, F.FREE1 + 8),
                     (F.FREE2, F.FREE2 + 8), (F.TRAMP, F.TRAMP + 40))
        fora = [i for i in dif if not any(a <= i < b for a, b in permitido)]
        self.assertEqual(fora, [], "mudou fora dos quatro intervalos")
        self.assertTrue(all(i >= 0xE000 for i in dif))
        self.assertFalse(any(0xD000 <= i < 0xE000 for i in dif))
        self.assertFalse(any(i >= 0x1FC000 for i in dif))
        self.assertEqual({i // 0x1000 * 0x1000 for i in dif}, {0x1AA000})

    def test_bl_e_trampolim(self):
        lido = A.desvio(self.o33, F.ALLOC + 12)
        self.assertEqual(lido, ("bl", F.X_TRAMP))
        self.assertEqual(bytes(self.o33[F.ALLOC:F.ALLOC + 12]),
                         F.NOP * 6)
        self.assertEqual(bytes(self.o33[F.TRAMP:F.TRAMP + 40]),
                         F.monta_trampolim())
        self.assertEqual(F.confere_trampolim(F.monta_trampolim()), [])

    def test_free_vai_para_o_lvgl(self):
        free = F.enc_free()
        self.assertEqual(bytes(self.o33[F.FREE1:F.FREE1 + 8]), free)
        self.assertEqual(bytes(self.o33[F.FREE2:F.FREE2 + 8]), free)
        self.assertEqual(bytes(self.o32[F.FREE1:F.FREE1 + 8]),
                         F.ORIG_FREE)
        self.assertEqual(bytes(self.o32[F.FREE2:F.FREE2 + 8]),
                         F.ORIG_FREE)

    def test_cpu1_sem_heap_de_fabrica(self):
        # corpo_cria 0xDAA028..0xDAA0E4 e corpo_apaga 0xDAA212..0xDAA254
        for ini, fim, nome in ((0x1AA028, 0x1AA0E4, "CRIA"),
                               (0x1AA212, 0x1AA254, "APAGA")):
            d = bytes(self.o33[ini:fim])
            self.assertNotIn(bytes.fromhex("47f6410cc0f2cf0c"), d,
                             f"{nome} ainda chama CALLOC 0xCF7840")
            self.assertNotIn(bytes.fromhex("47f6850cc0f2cf0c"), d,
                             f"{nome} ainda chama FREE 0xCF7885")
        # carrega_capa (CPU0) mantem os dois de fabrica
        self.assertIn(bytes.fromhex("47f6410cc0f2cf0c"),
                      self.o33[0x1AA256:0x1AA4A0])
        self.assertIn(bytes.fromhex("47f6850cc0f2cf0c"),
                      self.o33[0x1AA256:0x1AA4A0])

    def _roda_trampolim(self, aloca):
        try:
            from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_BLOCK,
                                 UC_HOOK_MEM_INVALID)
            from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                           UC_ARM_REG_R2, UC_ARM_REG_PC,
                                           UC_ARM_REG_SP, UC_ARM_REG_LR)
        except ImportError:
            self.skipTest("unicorn ausente")
        XIP = 0x00C00000
        PILHA = 0x30000000
        HEAP = 0x20000000
        FIM = 0x3F000000
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(XIP, 0x200000)
        u.mem_write(XIP, self.o33)
        u.mem_map(PILHA, 0x1000)
        u.mem_map(HEAP, 0x3000)
        u.mem_map(0x00000000, 0x10000)
        u.mem_write(0x00000BAA, b"\x70\x47")
        u.mem_map(FIM & ~0xFFF, 0x1000)
        u.mem_write(HEAP, b"\xAA" * 0x3000)
        chamadas = {"alloc": [], "memset": []}

        def bloco(uc, a, tam, _ud):
            if a == F.LV_ALLOC:
                chamadas["alloc"].append(uc.reg_read(UC_ARM_REG_R0))
                uc.reg_write(UC_ARM_REG_R0, HEAP if aloca else 0)
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            elif a == 0x00000BAA:
                p = uc.reg_read(UC_ARM_REG_R0)
                v = uc.reg_read(UC_ARM_REG_R1)
                n = uc.reg_read(UC_ARM_REG_R2)
                chamadas["memset"].append((p, v, n))
                uc.mem_write(p, bytes([v & 0xFF]) * n)
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            elif a == FIM:
                uc.emu_stop()
            elif not (F.X_TRAMP <= a < F.X_TRAMP + 40):
                raise AssertionError(f"executou fora do trampolim: 0x{a:08X}")

        u.hook_add(UC_HOOK_BLOCK, bloco)
        u.reg_write(UC_ARM_REG_SP, PILHA + 0x800)
        u.reg_write(UC_ARM_REG_LR, FIM | 1)
        u.emu_start(F.X_TRAMP | 1, FIM | 1, count=200)
        return u, chamadas, HEAP

    def test_trampolim_aloca_e_zera(self):
        u, ch, heap = self._roda_trampolim(True)
        self.assertEqual(ch["alloc"], [0x2210])
        self.assertEqual(ch["memset"], [(heap, 0, 0x2210)])
        self.assertEqual(bytes(u.mem_read(heap, 0x2210)), b"\0" * 0x2210)
        from unicorn.arm_const import UC_ARM_REG_R0
        self.assertEqual(u.reg_read(UC_ARM_REG_R0), heap)

    def test_trampolim_sem_memoria_devolve_zero(self):
        u, ch, _heap = self._roda_trampolim(False)
        self.assertEqual(ch["alloc"], [0x2210])
        self.assertEqual(ch["memset"], [])
        from unicorn.arm_const import UC_ARM_REG_R0
        self.assertEqual(u.reg_read(UC_ARM_REG_R0), 0)


if __name__ == "__main__":
    unittest.main()
