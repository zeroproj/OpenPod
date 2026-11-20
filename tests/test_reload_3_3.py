#!/usr/bin/env python3
"""Testes de aceite da ficha 025 (Reload 3.3, só a Parte 0.2).

Rode a mao (o `tools/ci.sh` tambem roda):

    python3 tests/test_reload_3_3.py -v

Cobre:

  - a receita 3.3 e reproduzivel e **byte a byte o Diag A** (sha
    368a7c8c98f6b6b6...), a imagem aprovada no aparelho; difere da 3.2 so
    na Parte 0.2, sem tocar abaixo de 0xE000, no setor 0xD000 nem na PSMP;
  - o trampolim da Parte 0.2: `bl`, bytes, `lv_mem_alloc(0x2210)`,
    `memset` e devolucao 0 sem memoria (unicorn);
  - o wrapper B7b REAL (0xDAAE20) chamado por um chamador de verdade
    (`emu_rc7.Maquina.chama`, frame de 16 B), com callback e yield
    stubs: SP, PC e r4-r6 voltam iguais aos da 3.2 (o antigo `add sp,#4`
    da Parte 1.1 reprovaria aqui);
  - o `envia_path` REAL (0xDAAC00) roda igual ao da 3.2: os 8 tipo 6, sem
    chamar a guarda do ring (que saiu da receita), preservando SP, PC e
    r4-r6. A reserva do ring fica para a tarefa da capa.
"""
import hashlib
import os
import struct
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
sys.path.insert(0, os.path.join(RAIZ, "tests"))
import fab_reload_3_3 as F  # noqa: E402
import capa_album_asm as A  # noqa: E402
import emu_rc7 as E  # noqa: E402

ORIG = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
BUILD = os.path.join(RAIZ, "tools/build.py")
WORK = os.path.join(RAIZ, "sdk/build/test_3_3")
IMG32 = os.path.join(WORK, "reload_3_2.bin")
IMG33A = os.path.join(WORK, "reload_3_3_a.bin")
IMG33B = os.path.join(WORK, "reload_3_3_b.bin")
SHA_DIAG_A = ("368a7c8c98f6b6b68c7e38853a69673bb05d5216219406f8ccdc9a858a73713d")


def sha_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


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
        with open(IMG32, "rb") as f:
            cls.o32 = f.read()
        with open(IMG33A, "rb") as f:
            cls.o33 = f.read()
        cls.o33b = open(IMG33B, "rb").read()

    def test_repro(self):
        self.assertEqual(sha_file(IMG33A), sha_file(IMG33B))

    def test_imagem_e_o_diag_a(self):
        self.assertEqual(sha_file(IMG33A), SHA_DIAG_A)

    def test_diff_so_no_lote_da_capa(self):
        self.assertEqual(len(self.o32), len(self.o33))
        dif = [i for i in range(len(self.o32)) if self.o32[i] != self.o33[i]]
        self.assertTrue(dif)
        permitido = ((F.ALLOC, F.ALLOC + 16), (F.FREE1, F.FREE1 + 8),
                     (F.FREE2, F.FREE2 + 8), (F.TRAMP, F.TRAMP + 40))
        fora = [i for i in dif if not any(a <= i < b for a, b in permitido)]
        self.assertEqual(fora, [], "mudou fora dos intervalos permitidos")
        self.assertTrue(all(i >= 0xE000 for i in dif))
        self.assertFalse(any(0xD000 <= i < 0xE000 for i in dif))
        self.assertFalse(any(i >= 0x1FC000 for i in dif))
        self.assertEqual({i // 0x1000 * 0x1000 for i in dif}, {0x1AA000})

    def test_bl_e_trampolim(self):
        lido = A.desvio(self.o33, F.ALLOC + 12)
        self.assertEqual(lido, ("bl", F.X_TRAMP))
        self.assertEqual(bytes(self.o33[F.ALLOC:F.ALLOC + 12]), F.NOP * 6)
        self.assertEqual(bytes(self.o33[F.TRAMP:F.TRAMP + 40]),
                         F.monta_trampolim())
        self.assertEqual(F.confere_trampolim(F.monta_trampolim()), [])

    def test_free_vai_para_o_lvgl(self):
        free = F.enc_free()
        self.assertEqual(bytes(self.o33[F.FREE1:F.FREE1 + 8]), free)
        self.assertEqual(bytes(self.o33[F.FREE2:F.FREE2 + 8]), free)
        self.assertEqual(bytes(self.o32[F.FREE1:F.FREE1 + 8]), F.ORIG_FREE)
        self.assertEqual(bytes(self.o32[F.FREE2:F.FREE2 + 8]), F.ORIG_FREE)

    def test_cpu1_sem_heap_de_fabrica(self):
        for ini, fim, nome in ((0x1AA028, 0x1AA0E4, "CRIA"),
                               (0x1AA212, 0x1AA254, "APAGA")):
            d = bytes(self.o33[ini:fim])
            self.assertNotIn(bytes.fromhex("47f6410cc0f2cf0c"), d,
                             f"{nome} ainda chama CALLOC 0xCF7840")
            self.assertNotIn(bytes.fromhex("47f6850cc0f2cf0c"), d,
                             f"{nome} ainda chama FREE 0xCF7885")
        self.assertIn(bytes.fromhex("47f6410cc0f2cf0c"),
                      self.o33[0x1AA256:0x1AA4A0])
        self.assertIn(bytes.fromhex("47f6850cc0f2cf0c"),
                      self.o33[0x1AA256:0x1AA4A0])

    def _roda_trampolim(self, aloca):
        from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_BLOCK)
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                       UC_ARM_REG_R2, UC_ARM_REG_PC,
                                       UC_ARM_REG_SP, UC_ARM_REG_LR)
        XIP, PILHA, HEAP, FIM = 0x00C00000, 0x30000000, 0x20000000, 0x3F000000
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

    def _roda_wrapper(self, imagem):
        m = E.Maquina(imagem)
        jd = 0x00810000
        m.escreve32(jd, 0x12345678)
        chamadas = []

        def yield_(_mq):
            chamadas.append("yield")
            return 0

        # o callback 0xDAA476 e codigo do lote da RC7: roda de verdade
        m.falsas = {0x00C43634: yield_, 0x00C43635: yield_}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
        m.chama(0xDAAE20, (jd, 0, 0, 0), salvos=salvos)
        self.assertEqual(m.erros, [])
        return m, chamadas, salvos

    def test_wrapper_real_frame(self):
        m32, c32, salvos = self._roda_wrapper(self.o32)
        m33, c33, _ = self._roda_wrapper(self.o33)
        self.assertEqual(c32, ["yield"])
        self.assertEqual(c33, c32)
        for m in (m32, m33):
            self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
            self.assertEqual(m.r(E.UC_ARM_REG_SP),
                             E.PILHA[0] + E.PILHA[1] - 0x100)
            self.assertEqual([m.r(x) for x in E.SALVOS], salvos)

    def _roda_envia(self, imagem):
        m = E.Maquina(imagem)
        sp = E.PILHA[0] + E.PILHA[1] - 0x100
        # o guarda de chamadores do envia_path le [sp+0x14]
        m.escreve32(sp + 0x14, 0xD088E0)
        caminho = 0x00810000
        m.escreve(caminho, b"0:/a.mp3\0")
        with open(os.path.join(RAIZ, "tests/assets/rc7/01_capa_v23.mp3"),
                  "rb") as f:
            m.arquivos[b"0:/a.mp3"] = f.read()
        m.escreve32(0x0081BBC8, 0x20001000)
        chamadas = []

        def ring_free(_mq):
            chamadas.append("ring_free")
            return 0

        def send(mq):
            tipo = mq.le(mq.r(E.UC_ARM_REG_R0) + 4, 1)[0]
            chamadas.append(("send", tipo))
            return 1

        def fim(_mq):
            chamadas.append("fim")
            return 0

        def yield_(_mq):
            return 0

        def like(_mq):
            return 0

        m.falsas = {0x00D6A9EA: ring_free,
                    0x00D0D818: send, 0x00D0D819: send,
                    0x00D0D880: fim, 0x00D0D881: fim,
                    0x00C43634: yield_, 0x00C43635: yield_,
                    0x00D6DB90: like, 0x00D6DB91: like}
        salvos = [caminho, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
        m.chama(0xDAAC00, (1, 0, 0, 0), salvos=salvos)
        self.assertEqual(m.erros, [])
        return m, chamadas, salvos

    def test_envia_path_igual_ao_da_3_2(self):
        self.assertEqual(self.o33[0x1AAC00:0x1AAD58],
                         self.o32[0x1AAC00:0x1AAD58])
        m32, c32, salvos = self._roda_envia(self.o32)
        m33, c33, _ = self._roda_envia(self.o33)
        self.assertNotIn("ring_free", c32)
        self.assertNotIn("ring_free", c33)
        self.assertEqual([c for c in c32 if isinstance(c, tuple)],
                         [("send", 6)] * 8)
        self.assertEqual([c for c in c33 if isinstance(c, tuple)],
                         [("send", 6)] * 8)
        for m in (m32, m33):
            self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
            self.assertEqual(m.r(E.UC_ARM_REG_SP),
                             E.PILHA[0] + E.PILHA[1] - 0x100)
            self.assertEqual([m.r(x) for x in E.SALVOS], salvos)


if __name__ == "__main__":
    unittest.main()
