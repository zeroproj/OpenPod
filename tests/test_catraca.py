#!/usr/bin/env python3
# NÃO ALTERAR sem o arquiteto. O hash deste arquivo é conferido por tools/ci.sh
# (tests/PROTEGIDOS.sha256).
"""
test_catraca.py — a última RC aprovada no aparelho continua reprodutível.

As RCs anteriores já são conferidas pelos test_rcN.py (cada um constrói a
receita anterior e confere o sha). Este arquivo fixa a mais recente até que
a próxima ficha leve o sha para o seu próprio teste.

USO
    python3 tests/test_catraca.py
"""

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APROVADAS = {
    # receita: (sha256 sem carimbo, data da aprovação no aparelho)
    "reload_1.0_rc6": ("af3a2b6d8aaa1bf9d709c20e3ccd8d3f1aeb37cc6843a6070938e122488f4bc8", "2026-10-30"),
}


class Catraca(unittest.TestCase):

    def test_rcs_aprovadas_reprodutiveis(self):
        tmp = tempfile.mkdtemp(prefix="openpod_catraca_")
        for receita, (esperado, _) in APROVADAS.items():
            saida = os.path.join(tmp, receita + ".bin")
            r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools/build.py"),
                                "--receita", receita, "--saida", saida],
                               capture_output=True, text=True, cwd=RAIZ)
            self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-1500:])
            with open(saida, "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), esperado, receita)


if __name__ == "__main__":
    unittest.main(verbosity=2)
