#!/usr/bin/env python3
# NÃO ALTERAR sem o arquiteto. O hash deste arquivo é conferido por tools/ci.sh
# (tests/PROTEGIDOS.sha256). Ficha: docs/tarefas/007-rc7-capa-album.md
"""
test_rc7_trava.py — regressão permanente dos achados da 1ª análise do diff da
ficha 007 (glm-5.3), pedida no Pacote ao arquiteto:

  007-D1 (MÉDIA): nenhuma instrução de divisão por hardware (UDIV/SDIV) no
         código novo do lote 0x1A8000. A fábrica tem zero UDIV em 1,75 MiB; o
         unicorn executa UDIV em qualquer ARMv7, então o arnês sozinho não pega.
  007-D2 (BAIXA): o id do quadro é conferido inteiro ("APIC"); um quadro com
         o mesmo corpo e id diferente (ex.: "ZPIC") não vira capa.

USO
    python3 tests/test_rc7_trava.py

DEPENDÊNCIAS
    As mesmas de tests/test_rc7.py (capstone, unicorn). Não abre o USB.
"""

import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu_rc7 as E  # noqa: E402
import test_rc7 as T  # noqa: E402

CODIGO_INI, CODIGO_FIM = 0x1AA010, 0x1AB000   # depois do quadrado cinza (0x1A8000..0x1AA010)


def divisoes(img, ini, fim):
    """Endereços (offset no arquivo) com UDIV/SDIV Thumb-2 T1, em todo alinhamento de 2."""
    achados = []
    for a in range(ini, fim - 2, 2):
        h1, h2 = struct.unpack_from("<HH", img, a)
        if (h1 & 0xFFF0) in (0xFBB0, 0xFB90) and (h2 & 0xF0F0) == 0xF0F0:
            achados.append(a)
    return achados


class Trava(T.Base):
    aparelho = T.Comportamento.aparelho
    titulo = T.Comportamento.titulo
    srcs = T.Comportamento.srcs
    ve_cinza = T.Comportamento.ve_cinza

    def test_t0_rc7_construida(self):
        self.assertEqual(self.rc7_rc, 0, self.rc7_log)
        self.assertEqual(len(self.rc7), 0x200000)

    def test_t1_sem_divisao_por_hardware(self):
        self.assertEqual(divisoes(self.rc7, T.LOTE, T.LOTE + T.LOTE_TAM), [],
                         "UDIV/SDIV no lote da RC7 (007-D1)")
        self.assertEqual(divisoes(self.rc7, CODIGO_INI, CODIGO_FIM), [])

    def test_t1_detector_funciona(self):
        falso = bytearray(16)
        struct.pack_into("<HH", falso, 4, 0xFBB1, 0xF0F2)    # udiv r0, r1, r2
        struct.pack_into("<HH", falso, 10, 0xFB93, 0xF4F5)   # sdiv r4, r3, r5
        self.assertEqual(divisoes(bytes(falso), 0, 16), [4, 10])

    def test_t2_id_do_quadro_inteiro(self):
        a = T.ativo("capa_a_300.jpg")
        bom = E.apic(3, a)
        for falso in (b"ZPIC", b"AXIC", b"APXC", b"APIX", b"apic"):
            with self.subTest(falso):
                m = self.aparelho()
                self.ve_cinza(m, self.titulo(m, E.tag_id3(3, [falso + bom[4:]])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
