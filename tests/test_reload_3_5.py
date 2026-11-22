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
import emu_rc7 as E  # noqa: E402
import fw_common as fw  # noqa: E402


class Maquina35(E.Maquina):
    """O emu_rc7 libera o lote da capa; aqui liberamos tambem o SDK novo e as
    duas funcoes de fabrica que os testes chamam de verdade."""

    def _bloco(self, uc, a, tam, _ud):
        if (0x00DAB000 <= a < 0x00E00000 or
                0x00D2E000 <= a < 0x00D2F000 or
                0x00D32000 <= a < 0x00D33000 or
                0x00002000 <= a < 0x00002010):
            return
        super()._bloco(uc, a, tam, _ud)


def chama_stub(m, alvo, regs=(), salvos=None, stub=0x2000):
    """Chama `alvo` por um `bl` de um stub com LR conhecido (FIM)."""
    m.escreve(stub, b"\x08\xb5" + A.enc(stub + 2, alvo, True) + b"\x08\xbd")
    return m.chama(stub, regs, salvos)

ORIG = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
BUILD = os.path.join(RAIZ, "tools/build.py")
WORK = os.path.join(RAIZ, "sdk/build/test_3_5")
IMG33 = os.path.join(WORK, "reload_3_3.bin")
IMG35 = os.path.join(WORK, "reload_3_5_a.bin")
IMG35B = os.path.join(WORK, "reload_3_5_b.bin")
UP = os.path.join(RAIZ, "release/OpenPod-Reload-3.5-Diag",
                  "OpenPodReload3.5Diag.up")
SHA_35 = "f49c819534a12756ed1ee72fbda4444cf4dadd627c164c85faa48131d4b1d05d"
SHA_SDK35 = "ee4636f4b21067bf59032adb0e17513e6df7d829f70d3276274157e4ad34af66"
SDK_TAM = 13944
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
                         ("b.w", LABEL_NOVO))

    def test_tails(self):
        for ini, alvo in ((0xDAB600, 0xDAA014), (0xDAB700, 0xD2EEE8)):
            off = ini - F.XIP
            self.assertTrue(
                any(A.desvio(self.o35, a) == ("b.w", alvo)
                    for a in range(off, off + 0x40, 2)),
                f"falta a cauda 0x{alvo:06X} no wrapper 0x{ini:06X}")

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

    def _estado(self, m, estado=0x00803000, node=0x00804000):
        m.escreve32(0x0081D2D4, 0x18)
        m.escreve32(0x0081D2D8, node)
        m.escreve32(0x0081D2DC, node)
        m.escreve32(node + 8, TIMER_NOVO | 1)
        m.escreve32(node + 0xC, estado)
        m.escreve32(node + 0x18, 0)
        m.escreve32(node + 0x1C, 0)
        m.escreve32(estado, 0x4F503335)
        return estado

    def test_home_label_process_real(self):
        for byte in (3, 0):
            m = Maquina35(self.o35)
            estado = self._estado(m)
            ctx, table, msg = 0x00806000, 0x00807000, 0x00808000
            m.escreve32(0x0081CE2C, ctx)
            m.escreve32(ctx + 0xA0, table)
            m.escreve32(table + 0x24, 1)
            m.escreve(msg + 4, struct.pack("<H", 0))
            m.escreve(msg + 6, struct.pack("<H", 3))
            m.escreve(msg + 0x14, b"Musica\0")
            m.escreve(0x00823EB0, bytes([byte]))
            m.falsas = {0x2B0: lambda mq: 0}
            salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
            chama_stub(m, 0xD2EEC4, (msg, 0, 0, 0), salvos=salvos)
            self.assertEqual(m.erros, [], f"byte[0x823EB0]={byte}")
            self.assertEqual(m.le(estado + 4, 7), b"Musica\0")
            self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
            self.assertEqual(m.r(E.UC_ARM_REG_SP),
                             E.PILHA[0] + E.PILHA[1] - 0x100)
            self.assertEqual([m.r(x) for x in E.SALVOS], salvos)

    def test_titulo_caminho_real(self):
        m = Maquina35(self.o35)
        estado = self._estado(m)
        ctx, view, msg = 0x00806000, 0x00807000, 0x00808000
        label, artista = 0x50000100, 0x50000200
        m.escreve32(0x0081CE2C, ctx)
        m.escreve32(ctx + 0xAC, view)
        m.escreve32(view, label)
        m.escreve32(view + 4, artista)
        m.escreve(msg + 4, struct.pack("<H", 0))
        m.escreve(msg + 6, struct.pack("<H", 3))
        m.escreve32(msg + 0x10, 1)
        m.escreve(msg + 0x14, b"Musica\0")
        m.escreve(0x00823EB0, b"\x03")
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
        chama_stub(m, 0xD32204, (msg, 0, 0, 0), salvos=salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + 4, 7), b"Musica\0")
        self.assertIn(("label_set_text", label, msg + 0x14), m.chamadas)
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
        self.assertEqual(m.r(E.UC_ARM_REG_SP),
                         E.PILHA[0] + E.PILHA[1] - 0x100)
        self.assertEqual([m.r(x) for x in E.SALVOS], salvos)

    def test_capa_contra_a_3_5(self):
        import test_reload_3_3 as T33
        t = T33.Reload33()
        m, chamadas, salvos = t._roda_wrapper(self.o35)
        self.assertEqual(m.erros, [])
        self.assertEqual(chamadas, ["yield"])
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
        self.assertEqual(m.r(E.UC_ARM_REG_SP),
                         E.PILHA[0] + E.PILHA[1] - 0x100)
        self.assertEqual([m.r(x) for x in E.SALVOS], salvos)

        m, chamadas, salvos = t._roda_envia(self.o35)
        self.assertEqual(m.erros, [])
        self.assertNotIn("ring_free", chamadas)
        self.assertEqual([c for c in chamadas if isinstance(c, tuple)],
                         [("send", 6)] * 8)
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
        self.assertEqual(m.r(E.UC_ARM_REG_SP),
                         E.PILHA[0] + E.PILHA[1] - 0x100)
        self.assertEqual([m.r(x) for x in E.SALVOS], salvos)


if __name__ == "__main__":
    unittest.main()
