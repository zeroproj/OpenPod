#!/usr/bin/env python3
"""
test_diag_trava.py — as tres imagens de BISSECAO da ficha 008 (a RC7 trava
ao tocar), o degrau B0 da ficha 009 e o degrau B1 da ficha 010 (o bug do
ring da fabrica).

NAO e um teste protegido: o `tools/ci.sh` roda so a lista fixa dele (esta
ficha nao pode mexer em `tests/PROTEGIDOS.sha256`). Rodado a mao:

    python3 tests/test_diag_trava.py

O QUE ESTE TESTE COBRE

    - a RC7 exata (sha 3af97713...) e as receitas de bissecao;
    - build REPRODUZIVEL: duas execucoes da mesma receita, o mesmo sha;
    - o diff RC7 -> diag e EXATAMENTE o esperado: A = 4 bytes em 0x1AA014,
      B = 2 bytes, C = 2 bytes, e nada mais em lugar nenhum;
    - a decodificacao de volta: o `b.w` novo da entrada TITULO aponta para
      o lv_label_set_text da fabrica (0x00D5ED94) e os 2 bytes novos dos
      niveis B e C sao `movs r0, #1`;
    - o nivel B1 (ficha 010): o diff de 2 bytes contra o Diag B, a
      decodificacao do caminho "ring cheio" em 0x00CF8438 (`movs r4,#0` +
      o `b` que agora aponta para o give do mutex), a recusa de entrada
      errada e a recusa da imagem ja patcheada;
    - o nivel B2 (ficha 010, adendo): o diff de 2 bytes contra o Diag B, a
      decodificacao do `bpl` do monitor do watchdog em 0x00D46B30 (que no
      B2 e um `nop`), a recusa de entrada errada e a da imagem ja
      patcheada;
    - as recusas: entrada errada (RC6, RC6 carimbada, truncada, lote
      mexido), `--dry-run` (nao grava), `--out` igual/symlink/hardlink da
      entrada e o reprocessamento de uma saida;
    - o MAPA do build.py e as receitas novas (e que as receitas de
      diagnostico NAO entraram na catraca).

DEPENDENCIAS

    Python 3 (stdlib). Nao abre o USB, nao grava no aparelho.
"""

import hashlib
import os
import struct
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
sys.path.insert(0, os.path.join(RAIZ, "tests"))

import diag_trava_asm as G  # noqa: E402
import fab_diag_trava as F  # noqa: E402
import fab_diag_b3 as F3  # noqa: E402
import fab_diag_b4 as F4  # noqa: E402
import fab_diag_b5 as F5  # noqa: E402
import fab_diag_b6 as F6  # noqa: E402
import fab_diag_b7 as F7  # noqa: E402
import emu_rc7 as E  # noqa: E402

SHA_RC7 = ("3af97713c9d8e28c2b36b872fd5883d18af9e65bff443c5e99ab6456"
           "78237d9e")
SHA_RC6 = ("af3a2b6d8aaa1bf9d709c20e3ccd8d3f1aeb37cc6843a6070938e122"
           "488f4bc8")
XIP = 0x00C00000
TABELA = 0x1AA010
SET_TEXT = 0x00D5ED94
CRIA, TITULO = 0x00DAA010, 0x00DAA014
TELA = 0x5E000000
ROT_CONT, ROT_TIT, ROT_LETRA = 0x5F000000, 0x5F000100, 0x5F000200
PH_DSC = 0x00DA8000                # o descritor do quadrado cinza
ATIVOS = os.path.join(RAIZ, "tests/assets/rc7")

# nivel: (receita, quantos bytes, a regiao do patch)
NIVEL = {
    "a": ("reload_1.0_rc7_diag_a", 4, (0x1AA014,)),
    "b": ("reload_1.0_rc7_diag_b", 4, (0x1AA188,)),
    "c": ("reload_1.0_rc7_diag_c", 2, (0x1AA31E,)),
    "b0": ("reload_1.0_rc7_diag_b0", 2, (0x1AA14C,)),
    "b1": ("reload_1.0_rc7_diag_b1", 2, (0x0F843A,)),
    "b2": ("reload_1.0_rc7_diag_b2", 2, (0x146B30,)),
}
# o nivel que cada nivel consome (a entrada da ferramenta): None = a RC7
BASE = {"a": None, "b": None, "c": None, "b0": None, "b1": "b", "b2": "b"}
# o que fica no lugar, byte a byte (o nivel A e conferido pela decodificacao
# do b.w, que depende do endereco de execucao)
ESPERADO = {
    "a": None,
    "b": b"\x00\x20\x00\xbf",     # movs r0, #0 + nop
    "c": b"\x01\x20",             # movs r0, #1
    "b0": b"\x00\x20",            # movs r0, #0 (o get_path "falha")
    "b1": b"\xf7\xe7",            # b 0x00CF842C (o give do mutex)
    "b2": b"\x00\xbf",            # nop (o monitor do watchdog)
}
# o par movw/movt da chamada externa do nivel C e o alvo
CHAMADA = {"c": (0x1AA316, 0x00D10B21),
           "b0": (0x1AA144, 0x00CFEFC5)}
# o `carrega_capa` (nivel B): o prologo unico e o `bl` que o chama
CARREGA_CAPA = (0x1AA256, 0x1AA188)

# o nivel B1 (ficha 010): o caminho "ring cheio" do envio a view
# (`0x00CF83E4`), no codigo da FABRICA (fora do lote da RC7)
RING_OFF = 0x0F843A          # o `b` (XIP 0x00CF843A)
RING_GIVE = 0x0F842C         # ldr r0,[pc,#0x10] + bl 0x80DB6E (o give)
RING_GIVE_BYTES = b"\x04\x48\x15\xf7\x9e\xf3"
RING_CHEIO = 0x0F8438        # movs r4,#0 (o caminho do ring cheio)
RING_CHEIO_BYTES = b"\x00\x24"
RING_ALVO_ANTES = 0x00CF8432  # o `b` da fabrica: pula o give (o bug)
RING_ALVO_DEPOIS = 0x00CF842C  # o `b` novo: o give do mutex

# o nivel B2 (ficha 010, adendo): o `bpl` do monitor do watchdog
# (0x00D46B30), no codigo da FABRICA (fora do lote da RC7)
MON_OFF = 0x146B30            # o `bpl` (XIP 0x00D46B30)
MON_ALVO_ANTES = 0x00D46B68   # o alvo do `bpl` na fabrica
# a regiao que cada nivel pode mexer FORA do lote (no codigo da fabrica)
FORA_LOTE = {"b1": (RING_OFF, 2), "b2": (MON_OFF, 2)}


def le(p):
    with open(p, "rb") as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def constroi(receita, destino):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools/build.py"),
                        "--receita", receita, "--saida", destino],
                       capture_output=True, text=True, cwd=RAIZ)
    return r.returncode, r.stdout + r.stderr


def desvio(b, a):
    """Alvo de um B.W (T4) no deslocamento `a`; None se nao for."""
    h1, h2 = struct.unpack_from("<HH", b, a)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xD000) not in (0xD000, 0x9000):
        return None
    S = (h1 >> 10) & 1
    I1 = 1 - (((h2 >> 13) & 1) ^ S)
    I2 = 1 - (((h2 >> 11) & 1) ^ S)
    off = (S << 24) | (I1 << 23) | (I2 << 22) \
        | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if S:
        off -= 1 << 25
    return XIP + a + 4 + off


def imm16(h1, h2):
    """O imm16 de um MOVW (T3) ou de um MOVT (T1)."""
    return (((h1 & 0xF) << 12) | (((h1 >> 10) & 1) << 11)
            | (((h2 >> 12) & 0x7) << 8) | (h2 & 0xFF))


def b16(b, a):
    """Alvo de um branch de 16 bits (T1) no deslocamento `a`.

    Aceita o `b` incondicional e o condicional (`bpl`); None se nao for."""
    h = struct.unpack_from("<H", b, a)[0]
    if (h & 0xF000) == 0xD000:               # condicional: 1101 cond imm8
        imm = h & 0xFF
        if imm & 0x80:
            imm -= 0x100
    elif (h & 0xF800) == 0xE000:             # incondicional: 11100 imm11
        imm = h & 0x7FF
        if imm & 0x400:
            imm -= 0x800
    else:
        return None
    return XIP + a + 4 + 2 * imm


def valor_carregado(b, a):
    """O valor carregado pelo par movw/movt no deslocamento `a` (ou None)."""
    h1, h2 = struct.unpack_from("<HH", b, a)
    n1, n2 = struct.unpack_from("<HH", b, a + 4)
    if (h1 & 0xFBF0) != 0xF240 or (n1 & 0xFBF0) != 0xF2C0:
        return None
    if (h2 & 0x8000) or (n2 & 0x8000):
        return None
    if ((h2 >> 8) & 0xF) != ((n2 >> 8) & 0xF):
        return None
    return (imm16(n1, n2) << 16) | imm16(h1, h2)


class Base(unittest.TestCase):

    _imgs = None

    @classmethod
    def setUpClass(cls):
        if Base._imgs is None:
            tmp = tempfile.mkdtemp(prefix="openpod_diag008_")
            p7 = os.path.join(tmp, "rc7.bin")
            rc, log = constroi("reload_1.0_rc7", p7)
            rc7 = le(p7) if os.path.exists(p7) else b""
            diags = {}
            for n, (receita, _tam, _offs) in NIVEL.items():
                p = os.path.join(tmp, receita + ".bin")
                rc2, log2 = constroi(receita, p)
                diags[n] = (rc2, log2, le(p) if os.path.exists(p) else b"")
            p6 = os.path.join(tmp, "rc6.bin")
            rc6, log6 = constroi("reload_1.0_rc6", p6)
            Base._imgs = (rc, log, rc7, diags, rc6, log6,
                          le(p6) if os.path.exists(p6) else b"", tmp)
        cls.rc7_rc, cls.rc7_log, cls.rc7 = Base._imgs[:3]
        cls.diags = Base._imgs[3]
        cls.rc6_rc, cls.rc6_log, cls.rc6 = Base._imgs[4:7]
        cls.tmp = Base._imgs[7]

    def base(self, n):
        """A imagem que o nivel `n` consome (a entrada da ferramenta)."""
        return self.diags[BASE[n]][2] if BASE[n] else self.rc7


class Imagens(Base):

    def test_0_rc7_exata(self):
        self.assertEqual(self.rc7_rc, 0, self.rc7_log[-2000:])
        self.assertEqual(len(self.rc7), 0x200000)
        self.assertEqual(sha(self.rc7), SHA_RC7)

    def test_1_diag_construidas(self):
        for n, (rc, log, img) in self.diags.items():
            self.assertEqual(rc, 0, f"{n}: {log[-2000:]}")
            self.assertEqual(len(img), 0x200000, n)

    def test_2_reprodutivel(self):
        """Duas execucoes da mesma receita, o mesmo sha."""
        tmp = tempfile.mkdtemp(prefix="openpod_diag008r_")
        for n, (receita, _tam, _offs) in NIVEL.items():
            shas = []
            for i in range(2):
                p = os.path.join(tmp, f"{n}{i}.bin")
                rc, log = constroi(receita, p)
                self.assertEqual(rc, 0, f"{receita}: {log[-1500:]}")
                shas.append(sha(le(p)))
            self.assertEqual(shas[0], shas[1], receita)

    def test_3_diff_exato(self):
        """A base -> diag: so os bytes do patch, e nada mais."""
        for n, (_receita, tam, offs) in NIVEL.items():
            img = self.diags[n][2]
            dif = [i for i in range(len(img)) if img[i] != self.base(n)[i]]
            off = offs[0]
            fora = [i for i in dif if not (off <= i < off + tam)]
            self.assertEqual(fora, [], f"{n}:_byte fora do patch")
            self.assertLessEqual(len(dif), tam, n)
            if ESPERADO[n] is not None:
                self.assertEqual(img[off:off + tam], ESPERADO[n], n)

    def test_4_decodificacao_de_volta(self):
        # A: a entrada TITULO virou b.w para o lv_label_set_text da fabrica
        a = self.diags["a"][2]
        self.assertEqual(desvio(a, TABELA + 4), SET_TEXT)
        # as outras duas entradas do lote continuam como estavam
        self.assertEqual(desvio(a, TABELA), 0x00DAA01C)
        self.assertEqual(desvio(a, TABELA + 8), 0x00DAA024)
        # B: o bl virou `movs r0, #0` + `nop` (e deixou de ser um branch)
        b = self.diags["b"][2]
        off = NIVEL["b"][2][0]
        self.assertEqual(b[off:off + 4], ESPERADO["b"], "b")
        h1 = struct.unpack_from("<H", b, off)[0]
        h2 = struct.unpack_from("<H", b, off + 2)[0]
        self.assertEqual((h1 & 0xF800), 0x2000, "b")     # movs
        self.assertEqual(((h1 >> 8) & 0x7), 0, "b")     # r0
        self.assertEqual(h1 & 0xFF, 0, "b")             # #0
        self.assertEqual(h2, 0xBF00, "b")               # nop
        self.assertIsNone(desvio(b, off), "b: o bl nao pode ter virado outro branch")
        # C: os 2 bytes novos sao `movs r0, #1` e o par movw/movt do
        # alvo continua logo antes (a chamada e que foi desligada)
        for n, (par, valor) in CHAMADA.items():
            img = self.diags[n][2]
            off = NIVEL[n][2][0]
            self.assertEqual(img[off:off + 2], ESPERADO[n], n)
            h = struct.unpack_from("<H", img, off)[0]
            self.assertEqual(h & 0xF800, 0x2000, n)      # movs
            self.assertEqual((h >> 8) & 0x7, 0, n)       # r0
            self.assertEqual(valor_carregado(img, par), valor, n)
            self.assertEqual(valor_carregado(img, off - 8), valor, n)

    def test_5_nada_alem_do_lote(self):
        for n, (_r, _t, _o) in NIVEL.items():
            img = self.diags[n][2]
            dif = [i for i in range(len(img)) if img[i] != self.base(n)[i]]
            for i in dif:
                if n in FORA_LOTE:
                    # o nivel mexe no codigo da FABRICA (o branch dele)
                    o, t = FORA_LOTE[n]
                    self.assertTrue(o <= i < o + t, f"{n}: 0x{i:06X}")
                else:
                    self.assertTrue(0x1A8000 <= i < 0x1AB000, f"{n}: 0x{i:06X}")
                self.assertGreaterEqual(i, 0x00E000)
                self.assertFalse(0xD000 <= i < 0xE000)
                self.assertLess(i, 0x1FC000)


class Recusa(Base):

    def roda(self, entrada, nivel, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_diag008x_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(entrada)
        r = subprocess.run([sys.executable,
                            os.path.join(RAIZ, "tools/fab_diag_trava.py"),
                            "--in", src, "--out", dst, "--nivel", nivel]
                           + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), le(src) == entrada

    def rc6_carimbada(self):
        """A RC6 com um carimbo de versao (a entrada que o decisor gravou)."""
        p = os.path.join(self.tmp, "rc6_carimbada.bin")
        if os.path.exists(p):
            return le(p)
        r = subprocess.run([sys.executable,
                            os.path.join(RAIZ, "tools/patch_versao.py"),
                            "--in", os.path.join(self.tmp, "rc6.bin"),
                            "--out", p, "--em", "0x1A4F00",
                            "--texto", "RC6 carimbada"],
                           capture_output=True, text=True, cwd=RAIZ)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return le(p)

    def test_6_aceita_a_imagem_exata(self):
        for n in NIVEL:
            rc, criou, intacta = self.roda(self.base(n), n)
            self.assertEqual((rc, criou), (0, True), n)
            self.assertTrue(intacta, n)

    def test_7_dry_run_nao_grava(self):
        for n in NIVEL:
            rc, criou, intacta = self.roda(self.base(n), n, ["--dry-run"])
            self.assertEqual((rc, criou), (0, False), n)
            self.assertTrue(intacta, n)

    def test_8_recusa_entradas_erradas(self):
        comum = {
            "rc6": self.rc6,
            "rc6_carimbada": self.rc6_carimbada(),
            "truncada": self.rc7[:0x100000],
        }
        b = bytearray(self.rc7)
        b[TABELA] ^= 0xFF                      # a tabela do lote mexida
        comum["lote_mexido"] = bytes(b)
        # cada nivel tem o seu alvo: a corrupcao vai no par da chamada dele
        casos = {n: dict(comum) for n in NIVEL}
        b = bytearray(self.rc7)
        b[0x1AA316 + 2] ^= 0x01                # o movw do jd_prepare mexido
        casos["c"]["chamada_mexida"] = bytes(b)
        b = bytearray(self.rc7)
        b[0x1AA144 + 2] ^= 0x01                # o movw do get_path mexido
        casos["b0"]["chamada_mexida"] = bytes(b)
        b = bytearray(self.rc7)
        b[CARREGA_CAPA[0] + 4] ^= 0x01        # o sub sp,#12 do carrega_capa
        casos["b"]["prologo_mexido"] = bytes(b)
        b = bytearray(self.rc7)
        b[CARREGA_CAPA[1]] ^= 0xFF             # o bl do carrega_capa mexido
        casos["b"]["bl_mexido"] = bytes(b)
        # os niveis B1 e B2 consomem o Diag B: as outras sao entradas erradas
        for n, outro in (("b1", "b0"), ("b2", "b0")):
            casos[n]["rc7"] = self.rc7
            casos[n][outro] = self.diags[outro][2]
        casos["b1"]["b1_ja_patcheada"] = self.diags["b1"][2]
        casos["b2"]["b2_ja_patcheada"] = self.diags["b2"][2]
        b = bytearray(self.diags["b"][2])
        b[RING_OFF] ^= 0x01                   # o `b` do ring mexido
        casos["b1"]["ring_mexido"] = bytes(b)
        b = bytearray(self.diags["b"][2])
        b[RING_GIVE] ^= 0x01                  # o give do mutex mexido
        casos["b1"]["give_mexido"] = bytes(b)
        b = bytearray(self.diags["b"][2])
        b[MON_OFF] ^= 0x01                    # o `bpl` do monitor mexido
        casos["b2"]["monitor_mexido"] = bytes(b)
        for n in NIVEL:
            for nome, entrada in casos[n].items():
                rc, criou, intacta = self.roda(entrada, n)
                self.assertNotEqual(rc, 0, f"{n} aceitou {nome}")
                self.assertFalse(criou, f"{n} criou saida com {nome}")
                self.assertTrue(intacta, f"{n} mexeu na entrada ({nome})")

    def test_9_saida_igual_ou_link(self):
        for n in NIVEL:
            for tipo in ("mesmo", "symlink", "hardlink"):
                tmp = tempfile.mkdtemp(prefix="openpod_diag008l_")
                src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
                entrada = self.base(n)
                with open(src, "wb") as fh:
                    fh.write(entrada)
                if tipo == "mesmo":
                    dst = src
                else:
                    (os.symlink if tipo == "symlink" else os.link)(src, dst)
                r = subprocess.run([sys.executable,
                                    os.path.join(RAIZ, "tools/fab_diag_trava.py"),
                                    "--in", src, "--out", dst, "--nivel", n],
                                   capture_output=True, cwd=RAIZ)
                self.assertNotEqual(r.returncode, 0, f"{n} {tipo}")
                self.assertEqual(le(src), entrada, f"{n} {tipo}")

    def test_10_reprocessar_uma_saida(self):
        for n in NIVEL:
            rc, criou, intacta = self.roda(self.diags[n][2], n)
            self.assertNotEqual(rc, 0, f"{n} aceitou reprocessar")
            self.assertFalse(criou, f"{n} criou saida reprocessando")
            self.assertTrue(intacta, n)

    def test_11_em_errado_e_recusado(self):
        for n in NIVEL:
            rc, criou, _ = self.roda(self.base(n), n, ["--em", "0x1A9000"])
            self.assertNotEqual(rc, 0, n)
            self.assertFalse(criou, n)


class Premissas(Base):
    """As premissas da ferramenta, uma por uma (branco sobre preto)."""

    def test_12_rc7_passa_em_todas(self):
        for n in NIVEL:
            self.assertEqual(F.confere_premissas(bytearray(self.base(n)), n),
                             [], n)

    def test_13_entrada_titulo_ja_patcheada(self):
        d = bytearray(self.rc7)
        d[TABELA + 4:TABELA + 8] = F.A.enc(XIP + TABELA + 4, SET_TEXT, False)
        erros = F.confere_premissas(d, "a")
        self.assertTrue(any("patchead" in e for e in erros), erros)

    def test_14_bl_do_carrega_capa_ja_patcheado(self):
        """O nivel B: o `bl` ja cortado e recusado (reprocessar)."""
        d = bytearray(self.rc7)
        off = CARREGA_CAPA[1]
        d[off:off + 4] = ESPERADO["b"]
        erros = F.confere_premissas(d, "b")
        self.assertTrue(any("patchead" in e for e in erros), erros)

    def test_14b_chamada_ja_patcheada(self):
        """O nivel C: o `blx` ja cortado e recusado (reprocessar)."""
        d = bytearray(self.rc7)
        off = NIVEL["c"][2][0]
        d[off:off + 2] = ESPERADO["c"]
        erros = F.confere_premissas(d, "c")
        self.assertTrue(any("patchead" in e for e in erros), erros)

    def test_14c_get_path_ja_patcheado(self):
        """O nivel B0: o `blx` ja cortado e recusado (reprocessar)."""
        d = bytearray(self.rc7)
        off = NIVEL["b0"][2][0]
        d[off:off + 2] = ESPERADO["b0"]
        erros = F.confere_premissas(d, "b0")
        self.assertTrue(any("patchead" in e for e in erros), erros)

    def test_15_chamada_inexistente(self):
        """O par movw/movt do alvo tem de aparecer exatamente uma vez."""
        d = bytearray(self.rc7)
        d[0x1AA316 + 2] ^= 0x01             # o imm8 do movw do jd_prepare
        erros = F.confere_premissas(d, "c")
        self.assertTrue(any("aparece 0x" in e for e in erros), erros)
        self.assertEqual(G.acha_pares(d, 0x00D10B21), [])

    def test_15b_carrega_capa_inexistente(self):
        """O nivel B: o prologo tem de ser unico, e o `bl` tambem."""
        d = bytearray(self.rc7)
        d[CARREGA_CAPA[0] + 4] ^= 0x01      # o sub sp,#12 do prologo
        erros = F.confere_premissas(d, "b")
        self.assertTrue(any("prologo" in e for e in erros), erros)
        self.assertEqual(G.acha_carrega_capa(d), [])
        d = bytearray(self.rc7)
        d[CARREGA_CAPA[1]] ^= 0xFF           # o bl do carrega_capa
        erros = F.confere_premissas(d, "b")
        self.assertTrue(any("bl interno" in e for e in erros), erros)

    def test_16_scanner(self):
        self.assertEqual(G.acha_pares(self.rc7, 0x00D10B21), [0x1AA316])
        self.assertEqual(G.achado_unico(self.rc7, 0x00D10B21), 0x1AA31E)
        # o carrega_capa: o prologo unico e o bl que o chama
        self.assertEqual(G.acha_carrega_capa(self.rc7), [CARREGA_CAPA[0]])
        self.assertEqual(G.acha_bl_para(self.rc7, CARREGA_CAPA[0] + XIP),
                         [CARREGA_CAPA[1]])
        self.assertEqual(G.acha_bl_para(self.rc7, 0x00DAA020), [])
        # o patch de cada nivel
        for n, (_r, tam, offs) in NIVEL.items():
            off, t, novos = G.bytes_do_patch(self.base(n), n)
            self.assertEqual(off, offs[0], n)
            self.assertEqual(t, tam, n)
            if ESPERADO[n] is not None:
                self.assertEqual(novos, ESPERADO[n], n)
        # o detector nao aceita meia-palavra qualquer
        self.assertFalse(G.e_blx(0x2800))
        self.assertFalse(G.e_mov(0x2800, 0x0000, 0xF240))
        self.assertTrue(G.e_blx(0x47E0))
        self.assertTrue(G.e_mov(0xF247, 0x7CCD, 0xF240))


class B1(Base):
    """O nivel B1 (ficha 010): o bug do ring da fabrica, consertado.

    O B1 mexe no codigo da FABRICA (nao no lote da RC7): o `b` do caminho
    "ring cheio" do envio a view (`0x00CF83E4`)."""

    def test_25_diff_de_2_bytes_contra_o_b(self):
        """O B1 e o Diag B + a regiao de 2 bytes do `b` do ring.

        A regiao (`fa e7` -> `f7 e7`) e de 2 bytes, mas so o primeiro muda
        de valor: o `0xE7` (o bit alto da meia-palavra) e o mesmo."""
        b = self.diags["b"][2]
        b1 = self.diags["b1"][2]
        dif = [i for i in range(len(b)) if b[i] != b1[i]]
        self.assertEqual(dif, [RING_OFF])
        self.assertEqual(b[RING_OFF:RING_OFF + 2], b"\xfa\xe7")
        self.assertEqual(b1[RING_OFF:RING_OFF + 2], ESPERADO["b1"])
        # e nada mais: o resto do Diag B continua byte a byte
        self.assertEqual(b[:RING_OFF], b1[:RING_OFF])
        self.assertEqual(b[RING_OFF + 2:], b1[RING_OFF + 2:])

    def test_26_decodificacao_em_cf8438(self):
        """O caminho "ring cheio": `movs r4,#0` e o `b` que agora da o give."""
        b = self.diags["b"][2]
        b1 = self.diags["b1"][2]
        # 0x00CF8438: movs r4, #0 (o caminho do ring cheio)
        self.assertEqual(b[RING_CHEIO:RING_CHEIO + 2], RING_CHEIO_BYTES)
        self.assertEqual(b1[RING_CHEIO:RING_CHEIO + 2], RING_CHEIO_BYTES)
        h = struct.unpack_from("<H", b1, RING_CHEIO)[0]
        self.assertEqual(h & 0xF800, 0x2000)      # movs
        self.assertEqual((h >> 8) & 0x7, 4)       # r4
        self.assertEqual(h & 0xFF, 0)             # #0
        # 0x00CF843A: o `b` — na fabrica ele pula o give (o bug), no B1 nao
        self.assertEqual(b16(b, RING_OFF), RING_ALVO_ANTES)
        self.assertEqual(b16(b1, RING_OFF), RING_ALVO_DEPOIS)
        # 0x00CF842C: o give do mutex (ldr r0,[pc,#0x10] + bl 0x80DB6E)
        self.assertEqual(b[RING_GIVE:RING_GIVE + 6], RING_GIVE_BYTES)
        self.assertEqual(b1[RING_GIVE:RING_GIVE + 6], RING_GIVE_BYTES)

    def test_27_imagem_ja_patcheada_recusada(self):
        """A B1 nao entra na B1: nem pelas premissas nem pela ferramenta."""
        d = bytearray(self.diags["b1"][2])
        erros = F.confere_premissas(d, "b1")
        self.assertTrue(any("ja esta aplicado" in e for e in erros), erros)
        tmp = tempfile.mkdtemp(prefix="openpod_diag010x_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(bytes(d))
        r = subprocess.run([sys.executable,
                            os.path.join(RAIZ, "tools/fab_diag_trava.py"),
                            "--in", src, "--out", dst, "--nivel", "b1"],
                           capture_output=True, text=True, cwd=RAIZ)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(dst))

    def test_28_premissas_do_b1(self):
        """O `b` e o give tem de ser os da fabrica."""
        d = bytearray(self.diags["b"][2])
        d[RING_OFF] ^= 0x01                      # o `b` do ring mexido
        erros = F.confere_premissas(d, "b1")
        self.assertTrue(any("fabrica" in e for e in erros), erros)
        d = bytearray(self.diags["b"][2])
        d[RING_GIVE] ^= 0x01                     # o give do mutex mexido
        erros = F.confere_premissas(d, "b1")
        self.assertTrue(any("give" in e for e in erros), erros)
        # a RC7 e a B0 nao sao a entrada do B1
        for outra in (self.rc7, self.diags["b0"][2], self.diags["a"][2]):
            erros = F.confere_premissas(bytearray(outra), "b1")
            self.assertTrue(erros)

    def test_29_a_receita_do_b1_monta_o_b(self):
        """A receita do B1 e o Diag B mais o nivel b1 (e o resto do B)."""
        b, b1 = self.diags["b"][2], self.diags["b1"][2]
        dif = [i for i in range(len(b)) if b[i] != b1[i]]
        self.assertEqual(dif, [RING_OFF])
        self.assertEqual(b1[RING_OFF:RING_OFF + 2], ESPERADO["b1"])
        # o TITULO do B continua ligado (o B1 nao mexe no lote)
        self.assertEqual(b1[0x1AA014:0x1AA018], b[0x1AA014:0x1AA018])


class B2(Base):
    """O nivel B2 (ficha 010, adendo): o monitor do watchdog neutralizado.

    O B2 mexe no codigo da FABRICA (nao no lote da RC7): o `bpl` do monitor
    (`0x00D46B30`), que voltaria sem alimentar o watchdog quando alguma
    tarefa registrada nao bate."""

    def test_30_diff_de_2_bytes_contra_o_b(self):
        """O B2 e o Diag B + a regiao de 2 bytes do `bpl` do monitor."""
        b = self.diags["b"][2]
        b2 = self.diags["b2"][2]
        dif = [i for i in range(len(b)) if b[i] != b2[i]]
        self.assertEqual(dif, [MON_OFF, MON_OFF + 1])
        self.assertEqual(b[MON_OFF:MON_OFF + 2], b"\x1a\xd5")
        self.assertEqual(b2[MON_OFF:MON_OFF + 2], ESPERADO["b2"])
        # e nada mais: o resto do Diag B continua byte a byte
        self.assertEqual(b[:MON_OFF], b2[:MON_OFF])
        self.assertEqual(b[MON_OFF + 2:], b2[MON_OFF + 2:])

    def test_31_decodificacao_do_bpl(self):
        """Na fabrica o `bpl` pula a "-task %d is dead"; no B2 ele e um nop."""
        b = self.diags["b"][2]
        b2 = self.diags["b2"][2]
        # o `bpl` da fabrica: 0xD51A -> bpl 0x00D46B68
        h = struct.unpack_from("<H", b, MON_OFF)[0]
        self.assertEqual(h, 0xD51A)
        self.assertEqual(b16(b, MON_OFF), MON_ALVO_ANTES)
        # no B2: 0xBF00 = nop (e nenhum branch)
        h2 = struct.unpack_from("<H", b2, MON_OFF)[0]
        self.assertEqual(h2, 0xBF00)
        self.assertIsNone(b16(b2, MON_OFF))

    def test_32_imagem_ja_patcheada_recusada(self):
        """A B2 nao entra na B2: nem pelas premissas nem pela ferramenta."""
        d = bytearray(self.diags["b2"][2])
        erros = F.confere_premissas(d, "b2")
        self.assertTrue(any("ja esta aplicado" in e for e in erros), erros)
        tmp = tempfile.mkdtemp(prefix="openpod_diag010b2x_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(bytes(d))
        r = subprocess.run([sys.executable,
                            os.path.join(RAIZ, "tools/fab_diag_trava.py"),
                            "--in", src, "--out", dst, "--nivel", "b2"],
                           capture_output=True, text=True, cwd=RAIZ)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(dst))

    def test_33_premissas_do_b2(self):
        """O `bpl` tem de ser o da fabrica."""
        d = bytearray(self.diags["b"][2])
        d[MON_OFF] ^= 0x01                    # o `bpl` do monitor mexido
        erros = F.confere_premissas(d, "b2")
        self.assertTrue(any("fabrica" in e for e in erros), erros)
        # a RC7 e o B0 nao sao a entrada do B2
        for outra in (self.rc7, self.diags["b0"][2], self.diags["b1"][2]):
            erros = F.confere_premissas(bytearray(outra), "b2")
            self.assertTrue(erros)


class B3(Base):
    r"""O degrau B3 da ficha 011 (o caminho do rotulo 2, sem get_path).

    O B3 tira o get_path da ViewTask sem inventar RAM: o caminho NAO esta
    no r5 do TITULO (esse e o texto do titulo); esta no rotulo 2, que a
    mensagem do 0xD084F8 preenche antes do titulo (a fila e serial). O B3
    le o texto do rotulo 2 com o lv_label_get_text da fabrica (le
    [rotulo+0x24], como o lv_label_set_text em 0xD5ED94) e copia para
    ext+0x110. O caminho valido NAO mostra o cinza (src nulo); o invalido
    continua cinza. A captura 0x001088D8 NAO e tocada e a regiao XIP
    (0xC00000..0xDFFFFF) e so leitura: uma escrita nela falha o teste."""

    RECEITA = "reload_1.0_rc7_diag_b3"
    BLOB = 0x1AAA00
    BLOB_XIP = 0x00DAAA00
    CAPTURA = 0x1088D8
    ALVO_CAPTURA = 0x00D084F8
    GET = 0x1AA144
    CAPA = 0x1AA174
    FALHA = 0x1AA1BE
    CARREGA = 0x1AA188
    PH_DSC = 0x00DA8000

    @classmethod
    def setUpClass(cls):
        tmp = tempfile.mkdtemp(prefix="openpod_diag011_")
        p7 = os.path.join(tmp, "rc7.bin")
        rc7, log7 = constroi("reload_1.0_rc7", p7)
        cls.rc7_rc, cls.rc7_log = rc7, log7
        cls.rc7 = le(p7) if os.path.exists(p7) else b""
        p6 = os.path.join(tmp, "rc6.bin")
        rc6, log6 = constroi("reload_1.0_rc6", p6)
        cls.rc6_rc, cls.rc6_log = rc6, log6
        cls.rc6 = le(p6) if os.path.exists(p6) else b""
        p3 = os.path.join(tmp, "b3.bin")
        rc3, log3 = constroi(cls.RECEITA, p3)
        cls.b3_rc, cls.b3_log = rc3, log3
        cls.b3 = le(p3) if os.path.exists(p3) else b""
        cls.tmp = tmp
        cls.blob = F3.monta_blob()

    def roda(self, entrada, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_diag011x_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(entrada)
        r = subprocess.run([sys.executable,
                            os.path.join(RAIZ, "tools/fab_diag_b3.py"),
                            "--in", src, "--out", dst]
                           + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), le(src) == entrada

    def test_40_b3_construida(self):
        self.assertEqual(self.rc7_rc, 0, self.rc7_log[-2000:])
        self.assertEqual(self.b3_rc, 0, self.b3_log[-2000:])
        self.assertEqual(sha(self.rc7), SHA_RC7)
        self.assertEqual(len(self.b3), 0x200000)
        self.assertEqual(self.b3[self.CAPTURA:self.CAPTURA + 4],
                         self.rc7[self.CAPTURA:self.CAPTURA + 4])

    def test_41_reprodutivel(self):
        tmp = tempfile.mkdtemp(prefix="openpod_diag011r_")
        shas = []
        for i in range(2):
            p = os.path.join(tmp, f"{i}.bin")
            rc, log = constroi(self.RECEITA, p)
            self.assertEqual(rc, 0, log[-1500:])
            shas.append(sha(le(p)))
        self.assertEqual(shas[0], shas[1])

    def test_42_diff_exato(self):
        dif = [i for i in range(len(self.b3)) if self.b3[i] != self.rc7[i]]
        regioes = [(self.GET, 10), (self.CAPA, 8), (self.CARREGA, 4),
                   (self.BLOB, len(self.blob))]
        for i in dif:
            self.assertTrue(any(o <= i < o + t for o, t in regioes),
                            f"byte fora do patch: 0x{i:06X}")
            self.assertGreaterEqual(i, 0x00E000)
            self.assertFalse(0xD000 <= i < 0xE000)
            self.assertLess(i, 0x1FC000)
            self.assertFalse(self.CAPTURA <= i < self.CAPTURA + 4,
                             "a captura 0x001088D8 nao pode mudar")
        self.assertEqual(self.b3[self.GET:self.GET + 2], b"\xB0\x68")
        self.assertEqual(self.b3[self.GET + 6:self.GET + 10],
                         b"\x00\xbf\x00\xbf")
        self.assertEqual(self.b3[self.CAPA:self.CAPA + 8],
                         b"\x00\x21\x00\xbf\x00\xbf\x00\xbf")
        self.assertEqual(self.b3[self.CARREGA:self.CARREGA + 4],
                         b"\x00\x20\x00\xbf")
        self.assertEqual(self.b3[self.BLOB:self.BLOB + len(self.blob)],
                         self.blob)

    def test_43_decodificacao(self):
        self.assertEqual(desvio(self.b3, self.CAPTURA), self.ALVO_CAPTURA)
        self.assertEqual(self.b3[self.GET:self.GET + 2], b"\xB0\x68")
        self.assertEqual(desvio(self.b3, self.GET + 2), self.BLOB_XIP)
        self.assertEqual(self.b3[self.GET + 6:self.GET + 10],
                         b"\x00\xbf\x00\xbf")
        self.assertEqual(self.b3[self.CAPA:self.CAPA + 2], b"\x00\x21")
        self.assertEqual(self.b3[self.CARREGA:self.CARREGA + 2], b"\x00\x20")
        self.assertEqual(self.b3[self.CARREGA + 2:self.CARREGA + 4],
                         b"\x00\xbf")
        for v in (0x2930, 0x293A, 0x292F, 0x295C):
            self.assertIn(struct.pack("<H", v), self.blob, hex(v))

    def test_44_recusas(self):
        for nome, entrada in (("rc6", self.rc6),
                              ("truncada", self.rc7[:0x100000]),
                              ("b3", self.b3)):
            rc, criou, intacta = self.roda(entrada, ["--em", "0x1a8000"])
            self.assertNotEqual(rc, 0, nome)
            self.assertFalse(criou, nome)
            self.assertTrue(intacta, nome)
        for extra in (["--em", "0x1A9000"], ["--dry-run"]):
            rc, criou, intacta = self.roda(self.rc7, extra + ["--em", "0x1a8000"]
                                           if extra[0] == "--dry-run" else extra)
            if extra[0] == "--dry-run":
                self.assertEqual((rc, criou), (0, False), extra)
            else:
                self.assertNotEqual(rc, 0, extra)
            self.assertTrue(intacta, extra)
        for tipo in ("mesmo", "symlink", "hardlink"):
            tmp = tempfile.mkdtemp(prefix="openpod_diag011l_")
            src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
            with open(src, "wb") as f:
                f.write(self.rc7)
            if tipo == "mesmo":
                dst = src
            else:
                (os.symlink if tipo == "symlink" else os.link)(src, dst)
            r = subprocess.run([sys.executable,
                                os.path.join(RAIZ, "tools/fab_diag_b3.py"),
                                "--in", src, "--out", dst],
                               capture_output=True, cwd=RAIZ)
            self.assertNotEqual(r.returncode, 0, tipo)
            self.assertEqual(le(src), self.rc7, tipo)

    def test_45_premissas(self):
        self.assertEqual(F3.confere_premissas(bytearray(self.rc7), self.blob),
                         [])
        for outra in (self.rc6, self.b3):
            self.assertTrue(F3.confere_premissas(bytearray(outra), self.blob))
        d = bytearray(self.rc7)
        d[self.CAPTURA + 1] ^= 0x01
        self.assertTrue(F3.confere_premissas(d, self.blob))
        d = bytearray(self.rc7)
        d[self.CAPA] ^= 0x01
        self.assertTrue(F3.confere_premissas(d, self.blob))
        d = bytearray(self.rc7)
        d[self.BLOB] ^= 0xFF
        self.assertTrue(any("virgem" in e
                            for e in F3.confere_premissas(d, self.blob)))
        d = bytearray(self.rc7)
        d[self.CARREGA:self.CARREGA + 4] = b"\x00\x20\x00\xbf"
        self.assertTrue(any("carrega_capa" in e
                            for e in F3.confere_premissas(d, self.blob)))

    def xip_rom(self, m):
        from unicorn import UC_HOOK_MEM_WRITE

        def _hook(uc, acesso, end, tam, val, ud):
            if end < E.XIP + 0x200000 and end + tam > E.XIP:
                m.erros.append(f"escrita em XIP 0x{end:08X} ({tam} B)")
            return True

        m.u.hook_add(UC_HOOK_MEM_WRITE, _hook)

    def aparelho(self, img):
        m = E.Maquina(img)
        self.xip_rom(m)
        m.u.mem_map(0x5F000000, 0x1000)
        pag, view = m.aloca(0x200, registra=False), m.aloca(0x34, registra=False)
        m.escreve32(E.PAGINAS, pag)
        m.escreve32(pag + 0xAC, view)
        m.escreve32(view + 0, ROT_CONT)
        m.escreve32(view + 4, ROT_TIT)
        m.escreve32(view + 8, ROT_LETRA)
        m.escreve(E.AUDIO, b"\x02")
        m.escreve32(E.AUDIO + 0x20, 7)
        salvos = [0x11110000 + i for i in range(8)]
        salvos[1] = view
        m.chama(CRIA, (TELA,), salvos=salvos)
        self.assertEqual(m.erros, [])
        return m, view

    def titulo_b3(self, m, view, path, titulo=b"TITULO",
                  rotulo2=None, texto2=None):
        ctx = m.le32(view + 0x30)
        pp = m.aloca(0x100, registra=False)
        m.escreve(pp, path + b"\0")
        pt = m.aloca(0x100, registra=False)
        m.escreve(pt, titulo + b"\0")
        m.escreve32(view + 8, ROT_LETRA if rotulo2 is None else rotulo2)
        m.escreve32(ROT_LETRA + 0x24, pp if texto2 is None else texto2)
        m.escreve32(ROT_TIT + 0x24, pt)
        m.escreve(ctx + 0x10, b"\0" * 0x100)
        m.escreve(ctx + 0x110, b"\0" * 0x100)
        n0 = len(m.chamadas)
        m.chama(TITULO, (ROT_TIT, pt))
        self.assertEqual(m.erros, [])
        return ctx, m.chamadas[n0:]

    def test_46_emulacao_copia_path(self):
        m = E.Maquina(self.b3)
        self.xip_rom(m)
        dest = m.aloca(0x100, registra=False)
        src = m.aloca(0x40, registra=False)
        lab = m.aloca(0x40, registra=False)
        m.escreve32(lab + 0x24, src)
        for path, ok in ((b"0:/A/B.mp3", 1), (b"0:\\A.mp3", 1),
                         (b"lixo", 0), (b"", 0)):
            m.escreve(src, path + b"\0")
            m.escreve(dest, b"\xAA" * 0x100)
            r = m.chama(self.BLOB_XIP, (lab, 0, dest))
            self.assertEqual(m.erros, [], path)
            self.assertEqual(r, ok, path)
            if path:
                self.assertEqual(m.cstr(dest), path, path)
            else:
                self.assertEqual(m.le32(dest), 0xAAAAAAAA, "texto vazio nao copia")

    def test_47_emulacao_titulo(self):
        m, view = self.aparelho(self.b3)
        for path in (b"0:/MUSICA/teste.mp3", b"0:\\MUSICA\\teste.mp3"):
            ctx, novas = self.titulo_b3(m, view, path)
            nomes = [c[0] for c in novas]
            self.assertEqual(nomes, ["label_set_text", "img_set_src"], path)
            self.assertEqual(nomes.count("get_path"), 0, path)
            self.assertEqual(nomes.count("calloc"), 0, path)
            self.assertEqual(nomes.count("free"), 0, path)
            self.assertEqual(nomes.count("f_open"), 0, path)
            self.assertEqual(m.cstr(ctx + 0x110), path, path)
            self.assertEqual(m.cstr(ctx + 0x10), path, path)
            srcs = [c[2] for c in novas if c[0] == "img_set_src"]
            self.assertEqual(srcs, [0], path)          # o sucesso: src nulo
        # caminho invalido/vazio: cinza, e o caminho copiado fica como veio
        for path in (b"lixo", b""):
            ctx, novas = self.titulo_b3(m, view, path)
            self.assertEqual([c[0] for c in novas],
                             ["label_set_text", "img_set_src"])
            self.assertEqual(m.cstr(ctx + 0x10), b"")
            self.assertEqual(m.cstr(ctx + 0x110), path)
            srcs = [c[2] for c in novas if c[0] == "img_set_src"]
            self.assertEqual(srcs, [self.PH_DSC])      # a falha: cinza
        # o rotulo 1 (o titulo) NUNCA e lido como caminho
        ctx, novas = self.titulo_b3(m, view, b"0:/MUSICA", b"0:/TITULO")
        self.assertEqual(m.cstr(ctx + 0x110), b"0:/MUSICA")
        self.assertEqual(m.cstr(ctx + 0x10), b"0:/MUSICA")

    def test_48_emulacao_xip_rom(self):
        m = E.Maquina(self.b3)
        self.xip_rom(m)
        src = m.aloca(0x40, registra=False)
        m.escreve(src, b"0:/A\0")
        lab = m.aloca(0x40, registra=False)
        m.escreve32(lab + 0x24, src)
        m.chama(self.BLOB_XIP, (lab, 0, E.XIP + 0x1000))
        self.assertTrue(any("XIP" in e for e in m.erros))

    def test_49_mapa_e_receita(self):
        import build as B
        self.assertIn(self.RECEITA, B.RECEITAS)
        passo = B.RECEITAS[self.RECEITA][-1]
        self.assertEqual(passo[0], "fab_diag_b3.py")
        self.assertIn("--em", passo[1])
        self.assertIn("0x1a8000", passo[1])
        self.assertNotIn("fab_diag_b3.py", B.MAPA)
        t = le(os.path.join(RAIZ, "tests/test_catraca.py")).decode()
        self.assertNotIn(self.RECEITA, t)


    def test_50_guarda_rotulo_2(self):
        """Rotulo 2 nulo, texto nulo ou texto vazio: cinza sem deref/fault."""
        m, view = self.aparelho(self.b3)
        casos = (("rotulo 0", dict(rotulo2=0)),
                 ("texto 0", dict(texto2=0)),
                 ("texto vazio", dict()))
        for nome, kw in casos:
            path = b"" if nome == "texto vazio" else b"0:/MUSICA/teste.mp3"
            ctx, novas = self.titulo_b3(m, view, path, **kw)
            nomes = [c[0] for c in novas]
            self.assertEqual(nomes, ["label_set_text", "img_set_src"], nome)
            self.assertEqual(nomes.count("get_path"), 0, nome)
            srcs = [c[2] for c in novas if c[0] == "img_set_src"]
            self.assertEqual(srcs, [self.PH_DSC], nome)   # cinza, sem parar
            self.assertEqual(m.cstr(ctx + 0x110), b"", nome)
            self.assertEqual(m.cstr(ctx + 0x10), b"", nome)


class B4(Base):
    r"""O degrau B4 da ficha 012 (o caminho completo vindo da MainTask).

    A rajada 0x00CFF0A8 passa a mandar, logo depois do get_path, uma
    mensagem da propria fabrica (classe 3, tipo 5) com o caminho no texto.
    A view trata o tipo 5 em 0x00D32204 (o `cmp r3,#5` + o `bl
    label_dispatch`), copia o texto para ext+0x110, valida com as guardas do
    B3 e aplica: valido -> img_set_src(img, 0); invalido/vazio -> cinza
    0x00DA8000. O TITULO volta a fazer so o set_text (0x001AA0FE ->
    `b.w 0xDAA1D0`); o carrega_capa continua cortado (0x001AA188). O tipo 5
    NAO pode cair no `bhi 0xD322A0` e a view/ext/img/texto podem ser nulos."""

    RECEITA = "reload_1.0_rc7_diag_b4"
    BLOB = 0x1AAA00
    BLOB_XIP = 0x00DAAA00
    BLOB_ENVIA = 0x1AAC00
    BLOB_ENVIA_XIP = 0x00DAAC00
    CAPTURA = 0x1088D8
    ALVO_CAPTURA = 0x00D084F8
    P_BURST = 0x0FF0C4
    P_TYPE = 0x13223E
    P_TBB = 0x132242
    P_TITULO = 0x1AA0FE
    P_CARREGA = 0x1AA188
    TITULO_EPILOGO = 0x00DAA1D0
    PH_DSC = 0x00DA8000

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        p4 = os.path.join(cls.tmp, "b4.bin")
        rc4, log4 = constroi(cls.RECEITA, p4)
        cls.b4_rc, cls.b4_log = rc4, log4
        cls.b4 = le(p4) if os.path.exists(p4) else b""
        cls.blob = F4.monta_blob()

    def roda(self, entrada, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_diag012x_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(entrada)
        r = subprocess.run([sys.executable,
                            os.path.join(RAIZ, "tools/fab_diag_b4.py"),
                            "--in", src, "--out", dst]
                           + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), le(src) == entrada

    def test_60_b4_construida(self):
        self.assertEqual(self.rc7_rc, 0, self.rc7_log[-2000:])
        self.assertEqual(self.b4_rc, 0, self.b4_log[-2000:])
        self.assertEqual(sha(self.rc7), SHA_RC7)
        self.assertEqual(len(self.b4), 0x200000)
        self.assertEqual(self.b4[self.CAPTURA:self.CAPTURA + 4],
                         self.rc7[self.CAPTURA:self.CAPTURA + 4])

    def test_61_reprodutivel(self):
        tmp = tempfile.mkdtemp(prefix="openpod_diag012r_")
        shas = []
        for i in range(2):
            p = os.path.join(tmp, f"{i}.bin")
            rc, log = constroi(self.RECEITA, p)
            self.assertEqual(rc, 0, log[-1500:])
            shas.append(sha(le(p)))
        self.assertEqual(shas[0], shas[1])

    def test_62_diff_exato(self):
        dif = [i for i in range(len(self.b4)) if self.b4[i] != self.rc7[i]]
        regioes = [(self.P_TYPE, 2), (self.P_TBB, 4), (self.P_BURST, 12),
                   (self.P_TITULO, 4), (self.P_CARREGA, 4),
                   (self.BLOB, len(self.blob))]
        for i in dif:
            self.assertTrue(any(o <= i < o + t for o, t in regioes),
                            f"byte fora do patch: 0x{i:06X}")
            self.assertGreaterEqual(i, 0x00E000)
            self.assertFalse(0xD000 <= i < 0xE000)
            self.assertLess(i, 0x1FC000)
            self.assertFalse(self.CAPTURA <= i < self.CAPTURA + 4,
                             "a captura 0x001088D8 nao pode mudar")
        self.assertEqual(self.b4[self.P_TYPE:self.P_TYPE + 2], b"\x05\x2b")
        self.assertEqual(self.b4[self.P_TYPE + 2:self.P_TYPE + 4],
                         self.rc7[self.P_TYPE + 2:self.P_TYPE + 4])
        self.assertEqual(self.b4[self.P_BURST + 4:self.P_BURST + 12],
                         b"\x00\xbf\x00\xbf\x00\xbf\x00\xbf")
        self.assertEqual(self.b4[self.P_CARREGA:self.P_CARREGA + 4],
                         b"\x00\x20\x00\xbf")
        self.assertEqual(self.b4[self.BLOB:self.BLOB + len(self.blob)],
                         self.blob)

    def test_63_decodificacao(self):
        self.assertEqual(desvio(self.b4, self.CAPTURA), self.ALVO_CAPTURA)
        self.assertEqual(desvio(self.b4, self.P_TBB), self.BLOB_XIP)
        self.assertEqual(desvio(self.b4, self.P_BURST), self.BLOB_ENVIA_XIP)
        self.assertEqual(desvio(self.b4, self.P_TITULO), self.TITULO_EPILOGO)
        for v in (0x2830, 0x283A, 0x282F, 0x285C):
            self.assertIn(struct.pack("<H", v), self.blob, hex(v))
        self.assertEqual(self.blob[self.BLOB_ENVIA - self.BLOB:
                                   self.BLOB_ENVIA - self.BLOB + 4],
                         b"\x2d\xe9\xf0\x41")

    def test_64_recusas(self):
        for nome, entrada in (("rc6", self.rc6),
                              ("truncada", self.rc7[:0x100000]),
                              ("b4", self.b4)):
            rc, criou, intacta = self.roda(entrada, ["--em", "0x1a8000"])
            self.assertNotEqual(rc, 0, nome)
            self.assertFalse(criou, nome)
            self.assertTrue(intacta, nome)
        for extra in (["--em", "0x1A9000"], ["--dry-run"]):
            rc, criou, intacta = self.roda(self.rc7, extra + ["--em", "0x1a8000"]
                                           if extra[0] == "--dry-run" else extra)
            if extra[0] == "--dry-run":
                self.assertEqual((rc, criou), (0, False), extra)
            else:
                self.assertNotEqual(rc, 0, extra)
            self.assertTrue(intacta, extra)
        for tipo in ("mesmo", "symlink", "hardlink"):
            tmp = tempfile.mkdtemp(prefix="openpod_diag012l_")
            src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
            with open(src, "wb") as f:
                f.write(self.rc7)
            if tipo == "mesmo":
                dst = src
            else:
                (os.symlink if tipo == "symlink" else os.link)(src, dst)
            r = subprocess.run([sys.executable,
                                os.path.join(RAIZ, "tools/fab_diag_b4.py"),
                                "--in", src, "--out", dst],
                               capture_output=True, cwd=RAIZ)
            self.assertNotEqual(r.returncode, 0, tipo)
            self.assertEqual(le(src), self.rc7, tipo)

    def test_65_premissas(self):
        self.assertEqual(F4.confere_premissas(bytearray(self.rc7), self.blob),
                         [])
        for outra in (self.rc6, self.b4):
            self.assertTrue(F4.confere_premissas(bytearray(outra), self.blob))
        d = bytearray(self.rc7)
        d[self.CAPTURA + 1] ^= 0x01
        self.assertTrue(F4.confere_premissas(d, self.blob))
        d = bytearray(self.rc7)
        d[self.P_BURST] ^= 0x01
        self.assertTrue(F4.confere_premissas(d, self.blob))
        d = bytearray(self.rc7)
        d[self.P_TYPE] ^= 0x01
        self.assertTrue(F4.confere_premissas(d, self.blob))
        d = bytearray(self.rc7)
        d[self.P_TBB] ^= 0x01
        self.assertTrue(F4.confere_premissas(d, self.blob))
        d = bytearray(self.rc7)
        d[self.P_TITULO] ^= 0x01
        self.assertTrue(F4.confere_premissas(d, self.blob))
        d = bytearray(self.rc7)
        d[self.BLOB] ^= 0xFF
        self.assertTrue(any("virgem" in e
                            for e in F4.confere_premissas(d, self.blob)))
        d = bytearray(self.rc7)
        d[self.P_CARREGA:self.P_CARREGA + 4] = b"\x00\x20\x00\xbf"
        self.assertTrue(any("carrega_capa" in e
                            for e in F4.confere_premissas(d, self.blob)))

    def xip_rom(self, m):
        from unicorn import UC_HOOK_MEM_WRITE

        def _hook(uc, acesso, end, tam, val, ud):
            if end < E.XIP + 0x200000 and end + tam > E.XIP:
                m.erros.append(f"escrita em XIP 0x{end:08X} ({tam} B)")
            return True

        m.u.hook_add(UC_HOOK_MEM_WRITE, _hook)

    @staticmethod
    def _epilogo(mq):
        from unicorn.arm_const import UC_ARM_REG_LR
        mq.u.reg_write(UC_ARM_REG_LR, E.FIM | 1)
        return None

    def aparelho(self, img):
        m = E.Maquina(img)
        self.xip_rom(m)
        m.u.mem_map(0x5F000000, 0x1000)
        pag, view = m.aloca(0x200, registra=False), m.aloca(0x34, registra=False)
        m.escreve32(E.PAGINAS, pag)
        m.escreve32(pag + 0xAC, view)
        m.escreve32(view + 0, ROT_CONT)
        m.escreve32(view + 4, ROT_TIT)
        m.escreve32(view + 8, ROT_LETRA)
        m.escreve(E.AUDIO, b"\x02")
        m.escreve32(E.AUDIO + 0x20, 7)
        salvos = [0x11110000 + i for i in range(8)]
        salvos[1] = view
        m.chama(CRIA, (TELA,), salvos=salvos)
        self.assertEqual(m.erros, [])
        m.falsas[0x00D322A0] = self._epilogo
        return m, view

    def tipo5(self, m, view, path, texto=True, alvo=None):
        ext = m.le32(view + 0x30)
        msg = m.aloca(0x414, registra=False)
        m.escreve(msg, b"\0" * 0x414)
        m.escreve(msg + 0, b"\x04")
        m.escreve(msg + 2, b"\x03")
        m.escreve(msg + 4, b"\x05")
        m.escreve(msg + 6, b"\x03")
        m.escreve(msg + 0xC, b"\x01")
        m.escreve(msg + 0x10, struct.pack("<I", len(path)))
        m.escreve(msg + 0x14, path + b"\0")
        n0 = len(m.chamadas)
        salvos = [msg, view, msg + 0x14 if texto else 0]
        salvos += [0x11110000 + i for i in range(5)]
        m.chama(alvo or self.BLOB_XIP, (0, 0, 0, 5), salvos=salvos)
        return ext, m.chamadas[n0:]

    def titulo(self, m, view, texto=b"TIT"):
        pt = m.aloca(0x100, registra=False)
        m.escreve(pt, texto + b"\0")
        n0 = len(m.chamadas)
        m.chama(TITULO, (ROT_TIT, pt))
        return m.chamadas[n0:]

    def test_66_emulacao_tipo5(self):
        m, view = self.aparelho(self.b4)
        for path, src in ((b"0:/A/B.mp3", 0), (b"0:\\A.mp3", 0),
                          (b"lixo", self.PH_DSC), (b"", self.PH_DSC)):
            ext, novas = self.tipo5(m, view, path)
            self.assertEqual(m.erros, [], path)
            self.assertEqual([c[0] for c in novas], ["img_set_src"], path)
            self.assertEqual([c[2] for c in novas], [src], path)
            self.assertEqual(m.cstr(ext + 0x110), path, path)
        # ausente: sem o tipo 5, o TITULO so faz set_text e nao toca a imagem
        novas = self.titulo(m, view)
        self.assertEqual([c[0] for c in novas], ["label_set_text"])

    def test_67_emulacao_titulo_so_set_text(self):
        m, view = self.aparelho(self.b4)
        ext, novas = self.tipo5(m, view, b"0:/A.mp3")
        self.assertEqual([c[0] for c in novas], ["img_set_src"])
        self.assertEqual([c[2] for c in novas], [0])
        n0 = len(m.chamadas)
        novas = self.titulo(m, view, b"TIT")
        self.assertEqual([c[0] for c in novas], ["label_set_text"])
        self.assertEqual([c[0] for c in m.chamadas[n0:]], ["label_set_text"])
        self.assertNotIn("img_set_src", [c[0] for c in m.chamadas[n0:]])

    def test_68_emulacao_xip_rom(self):
        m, view = self.aparelho(self.b4)
        self.tipo5(m, view, b"0:/A.mp3")
        self.assertFalse(any("XIP" in e for e in m.erros), m.erros)

    def test_69_mapa_e_receita(self):
        import build as B
        self.assertIn(self.RECEITA, B.RECEITAS)
        passo = B.RECEITAS[self.RECEITA][-1]
        self.assertEqual(passo[0], "fab_diag_b4.py")
        self.assertIn("--em", passo[1])
        self.assertIn("0x1a8000", passo[1])
        self.assertNotIn("fab_diag_b4.py", B.MAPA)
        t = le(os.path.join(RAIZ, "tests/test_catraca.py")).decode()
        self.assertNotIn(self.RECEITA, t)

    def test_70_guarda_nulos(self):
        for nome in ("pagina", "view", "titulo", "ext", "img", "texto"):
            m, view = self.aparelho(self.b4)
            ext = m.le32(view + 0x30)
            if nome == "pagina":
                m.escreve32(E.PAGINAS, 0)
            elif nome == "view":
                m.escreve32(m.le32(E.PAGINAS) + 0xAC, 0)
            elif nome == "titulo":
                m.escreve32(view + 4, 0)
            elif nome == "ext":
                m.escreve32(view + 0x30, 0)
            elif nome == "img":
                m.escreve32(ext + 0xC, 0)
            n0 = len(m.chamadas)
            self.tipo5(m, view, b"0:/A.mp3", texto=(nome != "texto"))
            self.assertEqual(m.erros, [], nome)
            self.assertEqual([c[0] for c in m.chamadas[n0:]], [], nome)

    def test_71_bit_thumb_nos_indiretos(self):
        """Todo bx/blx do blob leva o bit Thumb (|1).

        No Cortex-M, bx/blx com bit0=0 gera UsageFault INVSTATE e reinicia
        o aparelho. O emulador (Unicorn) NAO aplica essa checagem e ainda
        normaliza o endereco do bloco, entao ele nao pega: a trava tem de
        ser estatica. A RC7 (0x1AA17C, o img_set_src do TITULO) e a
        referencia: 0xD5D869, impar."""
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
        from capstone import CS_MODE_LITTLE_ENDIAN
        from capstone.arm import ARM_OP_REG

        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True

        def indiretos(cod, base):
            achados, mov = [], {}
            for i in md.disasm(cod, base):
                if i.mnemonic in ("movw", "movt"):
                    rd = i.reg_name(i.operands[0].reg)
                    imm = i.operands[1].imm
                    if i.mnemonic == "movw":
                        mov[rd] = imm & 0xFFFF
                    else:
                        mov[rd] = (mov.get(rd, 0) & 0xFFFF) | (imm << 16)
                elif i.mnemonic in ("bx", "blx") and i.operands:
                    op = i.operands[0]
                    if op.type == ARM_OP_REG and i.reg_name(op.reg) in mov:
                        rd = i.reg_name(op.reg)
                        achados.append((i.address, rd, mov.pop(rd)))
            return achados

        for cod, base, nome in ((self.blob, self.BLOB_XIP, "B4"),
                                (F3.monta_blob(), 0x00DAAA00, "B3")):
            for end, reg, alvo in indiretos(cod, base):
                self.assertTrue(alvo & 1,
                                f"{nome}: {reg}=0x{alvo:08X} par em "
                                f"0x{end:08X} (falta o bit Thumb)")
        for end, reg, alvo in indiretos(self.rc7[0x1AA17C:0x1AA186],
                                        0x00DAA17C):
            self.assertTrue(alvo & 1, f"RC7: {reg}=0x{alvo:08X} par")

    def test_72_envia_path_guarda(self):
        """O envia_path so manda o tipo 5 vindo da ViewTask (0x8238F1).

        O lr salvo pela rajada em [r7+0x14] chega com o bit0 de Thumb
        (impar: 0xD088E1 etc.); a guarda limpa o bit0 (bic) e compara com
        a tabela par dos cinco chamadores da ViewTask. A MainTask
        (0xD00C29) e a MediaTask (0xCFF213) pulam a mensagem e o 0xD0D880,
        mas mantem o like getter. A fabrica termina a mensagem de rotulo
        com o 0xD0D880."""
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                       UC_ARM_REG_R2)
        m = E.Maquina(self.b4)

        def strncpy(mq):
            dst, src, n = (mq.r(UC_ARM_REG_R0), mq.r(UC_ARM_REG_R1),
                           mq.r(UC_ARM_REG_R2))
            s = mq.cstr(src)
            mq.escreve(dst, s + b"\0" * (n - len(s)))
            return dst

        def strlen(mq):
            return len(mq.cstr(mq.r(UC_ARM_REG_R0)))

        def send(mq):
            msg = mq.r(UC_ARM_REG_R0)
            mq.chamadas.append(("send", msg, mq.le(msg, 0x14)))
            return 0

        def send_view(mq):
            mq.chamadas.append(("send_view", mq.r(UC_ARM_REG_R0)))
            return 0

        def like(mq):
            mq.chamadas.append(("like", mq.r(UC_ARM_REG_R0),
                                mq.r(UC_ARM_REG_R1)))
            return 1

        m.falsas[0x00D9FD54] = strncpy
        m.falsas[0x00000AA2] = strlen
        m.falsas[0x00D0D818] = send
        m.falsas[0x00D0D880] = send_view
        m.falsas[0x00D6DB90] = like
        sp = E.PILHA[0] + E.PILHA[1] - 0x100
        path = b"0:/A/B.mp3"

        def envia(lr):
            m.chamadas.clear()
            m.erros.clear()
            buf = m.aloca(0x100, registra=False)
            m.escreve(buf, path + b"\0")
            m.escreve32(sp + 0x14, lr)
            m.escreve32(sp + 4, 0)
            m.chama(self.BLOB_ENVIA_XIP, (1, 0, 0, 0),
                    salvos=[buf, E.AUDIO] + [0x11110000 + i for i in range(6)])
            self.assertEqual(m.erros, [], hex(lr))
            return [c for c in m.chamadas
                    if c[0] in ("send", "send_view", "like")]

        for lr in (0xD088E1, 0xD08971, 0xD08BEF, 0xD0902D, 0xD0EED5):
            c = envia(lr)
            self.assertEqual([x[0] for x in c],
                             ["send", "send_view", "like"], hex(lr))
            msg = c[0][1]
            self.assertEqual(c[0][2][0:2], b"\x04\x00", hex(lr))
            self.assertEqual(c[0][2][2:3], b"\x03", hex(lr))
            self.assertEqual(c[0][2][4:5], b"\x05", hex(lr))
            self.assertEqual(c[0][2][6:7], b"\x03", hex(lr))
            self.assertEqual(c[0][2][0xC:0xD], b"\x01", hex(lr))
            self.assertEqual(struct.unpack("<I", c[0][2][0x10:0x14])[0],
                             len(path), hex(lr))
            self.assertEqual(m.cstr(msg + 0x14), path, hex(lr))
            self.assertEqual(c[2][2], sp + 4, hex(lr))
        for lr in (0xD00C29, 0xCFF213):
            c = envia(lr)
            self.assertEqual([x[0] for x in c], ["like"], hex(lr))
            self.assertEqual(c[0][2], sp + 4, hex(lr))

    def test_73_tabela_alinhada(self):
        """A tabela chamadores fica 4-alinhada e o adr aponta para ela."""
        from capstone import (Cs, CS_ARCH_ARM, CS_MODE_THUMB,
                              CS_MODE_LITTLE_ENDIAN)
        tabela = b"".join(struct.pack("<I", a) for a in
                          (0xD088E0, 0xD08970, 0xD08BEE, 0xD0902C,
                           0xD0EED4))
        off = self.blob.index(tabela)
        end = self.BLOB_XIP + off
        self.assertEqual(end % 4, 0,
                         f"a tabela em 0x{end:08X} nao e 4-alinhada")
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True
        achou = False
        for i in md.disasm(self.blob[self.BLOB_ENVIA - self.BLOB:],
                           self.BLOB_ENVIA_XIP):
            if i.mnemonic == "adr":
                imm = i.operands[1].imm
            elif i.mnemonic == "addw":
                imm = i.operands[2].imm
            else:
                continue
            if i.reg_name(i.operands[0].reg) != "r1":
                continue
            alvo = ((i.address + 4) & ~3) + imm
            self.assertEqual(alvo, end,
                             f"o adr em 0x{i.address:08X} aponta 0x{alvo:08X}")
            achou = True
            break
        self.assertTrue(achou, "o envia_path nao tem o adr r1, chamadores")


class Comportamento(Base):
    """As tres imagens no arnes de emulacao (unicorn, o de verdade).

    O arnes (`tests/emu_rc7.py`, protegido) troca por stubs so o que a
    ficha da RC7 permite: heap, FatFs, caminho da faixa e LVGL. Cada stub
    REGISTRA a chamada, entao a sequencia de chamadas de cada degrau diz
    o que o degrau realmente fez."""

    def aparelho(self, img):
        m = E.Maquina(img)
        pag, view = m.aloca(0x200, registra=False), m.aloca(0x34, registra=False)
        m.escreve32(E.PAGINAS, pag)
        m.escreve32(pag + 0xAC, view)
        m.escreve32(view + 0, ROT_CONT)
        m.escreve32(view + 4, ROT_TIT)
        m.escreve32(view + 8, ROT_LETRA)
        m.escreve(E.AUDIO, b"\x02")
        m.escreve32(E.AUDIO + 0x20, 7)
        salvos = [0x11110000 + i for i in range(8)]
        salvos[1] = view
        m.chama(CRIA, (TELA,), salvos=salvos)
        self.assertEqual(m.erros, [])
        return m

    def titulo(self, m, dados):
        caminho = b"0:/MUSICA/teste.mp3"
        m.caminho = caminho
        m.arquivos = {caminho: dados} if dados is not None else {}
        txt = m.aloca(16, registra=False)
        m.escreve(txt, b"titulo\0")
        n0 = len(m.chamadas)
        m.chama(TITULO, (ROT_TIT, txt))
        novas = m.chamadas[n0:]
        self.assertEqual(m.erros, [])
        self.assertEqual(m.abertos, {}, "o arquivo ficou aberto")
        return novas

    def ativo(self, nome):
        with open(os.path.join(ATIVOS, nome), "rb") as f:
            return f.read()

    def test_20_a_so_o_set_text(self):
        """A: o TITULO e o da fabrica — so o set_text."""
        m = self.aparelho(self.diags["a"][2])
        novas = self.titulo(m, self.ativo("01_capa_v23.mp3"))
        self.assertEqual([c[0] for c in novas], ["label_set_text"])
        self.assertEqual(novas[0][1], ROT_TIT)

    def test_21_b_get_path_sem_arquivo(self):
        """B: o get_path de verdade e NADA mais — nem heap, nem arquivo.

        A sequencia tem de ser EXATA: `label_set_text`, `get_path` e o
        `img_set_src` do quadrado cinza. Zero calloc, zero free, zero
        f_open (e o `free(NULL)` do caminho de erro da RC7 nao aparece
        aqui — e o que a R1 da analise do diff apontou)."""
        m = self.aparelho(self.diags["b"][2])
        novas = self.titulo(m, self.ativo("01_capa_v23.mp3"))
        nomes = [c[0] for c in novas]
        self.assertEqual(nomes, ["label_set_text", "get_path", "img_set_src"])
        self.assertEqual(nomes.count("calloc"), 0)
        self.assertEqual(nomes.count("free"), 0)
        self.assertEqual(nomes.count("f_open"), 0)
        self.assertEqual(nomes.count("f_read"), 0)
        self.assertEqual(nomes.count("f_close"), 0)
        # o quadrado cinza (e so ele) e o caminho novo guardado
        srcs = [c[2] for c in novas if c[0] == "img_set_src"]
        self.assertEqual(set(srcs), {PH_DSC})
        gp = [c for c in novas if c[0] == "get_path"]
        self.assertEqual(gp[0][1:3], (2, 7))

    def test_22_c_f_open_e_f_close_sem_jpeg(self):
        """C: o f_open e o f_close de verdade, mas o jd_prepare nao roda."""
        m = self.aparelho(self.diags["c"][2])
        novas = self.titulo(m, self.ativo("01_capa_v23.mp3"))
        nomes = [c[0] for c in novas]
        self.assertEqual(nomes.count("get_path"), 1)
        self.assertEqual(nomes.count("f_open"), 1)
        self.assertEqual(nomes.count("f_close"), 1)
        # o jd_prepare e o jd_decomp NAO rodaram: o TJpgDec da fabrica
        # leria o arquivo e o arnes nao registraria nenhuma leitura dele
        # (o quadrado cinza e o unico src)
        srcs = [c[2] for c in novas if c[0] == "img_set_src"]
        self.assertEqual(set(srcs), {PH_DSC})

    def test_23_da_rc7_mostra_a_capa(self):
        """A RC7 (D) mostra a capa: o degrau C para antes do JPEG."""
        m = self.aparelho(self.rc7)
        novas = self.titulo(m, self.ativo("01_capa_v23.mp3"))
        nomes = [c[0] for c in novas]
        self.assertEqual(nomes.count("f_open"), 1)
        self.assertEqual(nomes.count("f_close"), 1)
        srcs = [c[2] for c in novas if c[0] == "img_set_src"]
        self.assertTrue(srcs and srcs[-1] != PH_DSC, "a RC7 tem de mostrar a capa")

    def test_24_b0_rotina_ativa_sem_get_path(self):
        """B0: a ROTINA do TITULO roda inteira, mas o get_path NAO.

        A sequencia tem de ser `label_set_text` e o `img_set_src` do
        quadrado cinza — e NENHUM get_path (a chamada foi cortada e
        devolve "falha"). E o que separa "a rotina" de "o get_path"."""
        m = self.aparelho(self.diags["b0"][2])
        novas = self.titulo(m, self.ativo("01_capa_v23.mp3"))
        nomes = [c[0] for c in novas]
        self.assertEqual(nomes, ["label_set_text", "img_set_src"])
        self.assertEqual(nomes.count("get_path"), 0)
        self.assertEqual(nomes.count("calloc"), 0)
        self.assertEqual(nomes.count("free"), 0)
        self.assertEqual(nomes.count("f_open"), 0)
        srcs = [c[2] for c in novas if c[0] == "img_set_src"]
        self.assertEqual(set(srcs), {PH_DSC})


class B5(Base):
    r"""Os degraus B5a/B5b da ficha 013 (abrir a capa no tipo 5).

    O B5a abre o MP3 e le 10 bytes: "ID3" -> img_set_src(img, NULL); qualquer
    falha -> cinza. O B5b compara o caminho com ext+0x10, desliga o monitor
    da ViewTask, chama carrega_capa(ext), religa e, no sucesso, faz
    img_set_src(img, ext). O envia_path do B4 continua, agora em +0x500."""

    RECEITA_A = "reload_1.0_rc7_diag_b5a"
    RECEITA_B = "reload_1.0_rc7_diag_b5b"
    BLOB = 0x1AAA00
    BLOB_XIP = 0x00DAAA00
    BLOB_B = 0x1AAC00
    BLOB_B_XIP = 0x00DAAC00
    BLOB_ENVIA = 0x1AAF00
    BLOB_ENVIA_XIP = 0x00DAAF00
    BLOB_MAX = 0x600
    P_BURST = 0x0FF0C4
    P_TYPE = 0x13223E
    P_TBB = 0x132242
    P_TITULO = 0x1AA0FE
    P_CARREGA = 0x1AA188
    TITULO_EPILOGO = 0x00DAA1D0
    CARREGA = 0x00DAA256
    GET_TASK = 0x00D6AE38
    UNREG = 0x00D46ACC
    REG = 0x00D46A20
    PH_DSC = 0x00DA8000

    aparelho = B4.aparelho
    tipo5 = B4.tipo5
    titulo = B4.titulo
    xip_rom = B4.xip_rom
    _epilogo = staticmethod(B4._epilogo)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        p4 = os.path.join(cls.tmp, "b4.bin")
        rc4, log4 = constroi("reload_1.0_rc7_diag_b4", p4)
        cls.b4_rc, cls.b4_log = rc4, log4
        cls.b4 = le(p4) if os.path.exists(p4) else b""
        cls.blob_a = F5.monta_blob("a")
        cls.blob_b = F5.monta_blob("b")
        p5a = os.path.join(cls.tmp, "b5a.bin")
        rc5a, log5a = constroi(cls.RECEITA_A, p5a)
        cls.b5a_rc, cls.b5a_log = rc5a, log5a
        cls.b5a = le(p5a) if os.path.exists(p5a) else b""
        p5b = os.path.join(cls.tmp, "b5b.bin")
        rc5b, log5b = constroi(cls.RECEITA_B, p5b)
        cls.b5b_rc, cls.b5b_log = rc5b, log5b
        cls.b5b = le(p5b) if os.path.exists(p5b) else b""

    def roda(self, entrada, degrau, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_diag013x_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(entrada)
        r = subprocess.run([sys.executable,
                            os.path.join(RAIZ, "tools/fab_diag_b5.py"),
                            "--in", src, "--out", dst, "--degrau", degrau]
                           + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), le(src) == entrada

    def monitor(self, m, get_ret=0x12345678, unreg_ret=1):
        from unicorn.arm_const import UC_ARM_REG_R0

        def get(mq):
            m.chamadas.append(("get_task", mq.r(UC_ARM_REG_R0)))
            return get_ret

        def unreg(mq):
            m.chamadas.append(("unreg", mq.r(UC_ARM_REG_R0)))
            return unreg_ret

        def reg(mq):
            m.chamadas.append(("reg", mq.r(UC_ARM_REG_R0)))
            return 1

        m.falsas[self.GET_TASK] = get
        m.falsas[self.UNREG] = unreg
        m.falsas[self.REG] = reg

    def ativo(self, nome):
        with open(os.path.join(ATIVOS, nome), "rb") as f:
            return f.read()

    def test_80_b5_construida(self):
        self.assertEqual(self.b5a_rc, 0, self.b5a_log[-2000:])
        self.assertEqual(self.b5b_rc, 0, self.b5b_log[-2000:])
        self.assertEqual(len(self.b5a), 0x200000)
        self.assertEqual(len(self.b5b), 0x200000)
        self.assertEqual(self.b5a[self.P_TYPE:self.P_TYPE + 2], b"\x05\x2b")
        self.assertEqual(self.b5b[self.P_TYPE:self.P_TYPE + 2], b"\x05\x2b")

    def test_81_reprodutivel(self):
        tmp = tempfile.mkdtemp(prefix="openpod_diag013r_")
        for receita in (self.RECEITA_A, self.RECEITA_B):
            shas = []
            for i in range(2):
                p = os.path.join(tmp, f"{receita}{i}.bin")
                rc, log = constroi(receita, p)
                self.assertEqual(rc, 0, log[-1500:])
                shas.append(sha(le(p)))
            self.assertEqual(shas[0], shas[1], receita)

    def test_82_diff_exato(self):
        for nome, img, alvo in (("a", self.b5a, self.BLOB_XIP),
                                ("b", self.b5b, self.BLOB_B_XIP)):
            dif = [i for i in range(len(img)) if img[i] != self.b4[i]]
            regioes = [(self.P_TBB, 4), (self.P_BURST, 12),
                       (self.BLOB, self.BLOB_MAX)]
            for i in dif:
                self.assertTrue(any(o <= i < o + t for o, t in regioes),
                                f"B5{nome}: byte fora do patch: 0x{i:06X}")
                self.assertGreaterEqual(i, 0x00E000)
                self.assertFalse(0xD000 <= i < 0xE000)
                self.assertLess(i, 0x1FC000)
            self.assertEqual(img[self.P_TYPE:self.P_TYPE + 2], b"\x05\x2b")
            self.assertEqual(img[self.P_TITULO:self.P_TITULO + 4],
                             self.b4[self.P_TITULO:self.P_TITULO + 4])
            self.assertEqual(img[self.P_CARREGA:self.P_CARREGA + 4],
                             self.b4[self.P_CARREGA:self.P_CARREGA + 4])
            self.assertEqual(desvio(img, self.P_TBB), alvo)
            self.assertEqual(desvio(img, self.P_BURST), self.BLOB_ENVIA_XIP)
            self.assertEqual(img[self.P_BURST + 4:self.P_BURST + 12],
                             b"\x00\xbf" * 4)

    def test_83_decodificacao(self):
        self.assertEqual(self.b5a[self.BLOB:self.BLOB + 2], b"\x05\x2b")
        self.assertEqual(self.b5b[self.BLOB + 0x200:self.BLOB + 0x202],
                         b"\x05\x2b")
        for img in (self.b5a, self.b5b):
            self.assertEqual(img[self.BLOB_ENVIA:self.BLOB_ENVIA + 4],
                             b"\x2d\xe9\xf0\x41")
            self.assertEqual(desvio(img, self.P_BURST), self.BLOB_ENVIA_XIP)
        self.assertEqual(self.b5a[self.BLOB + 0x200:self.BLOB + 0x500],
                         b"\x00" * 0x300)
        self.assertEqual(self.b5b[self.BLOB:self.BLOB + 0x200],
                         b"\x00" * 0x200)

    def test_84_recusas(self):
        for nome, entrada in (("rc7", self.rc7), ("b5a", self.b5a)):
            rc, criou, intacta = self.roda(entrada, "a", ["--em", "0x1a8000"])
            self.assertNotEqual(rc, 0, nome)
            self.assertFalse(criou, nome)
            self.assertTrue(intacta, nome)
        rc, criou, intacta = self.roda(self.b4, "a", ["--em", "0x1A9000"])
        self.assertNotEqual(rc, 0)
        self.assertFalse(criou)
        self.assertTrue(intacta)
        rc, criou, intacta = self.roda(self.b4, "a", ["--dry-run"])
        self.assertEqual((rc, criou), (0, False))
        self.assertTrue(intacta)
        rc, criou, intacta = self.roda(self.b4, "c")
        self.assertNotEqual(rc, 0)
        self.assertFalse(criou)
        self.assertTrue(intacta)
        for tipo in ("mesmo", "symlink", "hardlink"):
            tmp = tempfile.mkdtemp(prefix="openpod_diag013l_")
            src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
            with open(src, "wb") as f:
                f.write(self.b4)
            if tipo == "mesmo":
                dst = src
            else:
                (os.symlink if tipo == "symlink" else os.link)(src, dst)
            r = subprocess.run([sys.executable,
                                os.path.join(RAIZ, "tools/fab_diag_b5.py"),
                                "--in", src, "--out", dst, "--degrau", "a"],
                               capture_output=True, cwd=RAIZ)
            self.assertNotEqual(r.returncode, 0, tipo)
            self.assertEqual(le(src), self.b4, tipo)

    def test_85_premissas(self):
        self.assertEqual(F5.confere_premissas(bytearray(self.b4),
                                              self.blob_a, "a"), [])
        self.assertEqual(F5.confere_premissas(bytearray(self.b4),
                                              self.blob_b, "b"), [])
        for outra in (self.rc7, self.b5a):
            self.assertTrue(F5.confere_premissas(bytearray(outra),
                                                 self.blob_a, "a"))
        for off in (self.P_TBB, self.P_BURST, self.P_TYPE,
                    self.P_TITULO, self.P_CARREGA):
            d = bytearray(self.b4)
            d[off] ^= 0x01
            self.assertTrue(F5.confere_premissas(d, self.blob_a, "a"), hex(off))
        d = bytearray(self.b4)
        d[self.BLOB + 0x2D9] ^= 0xFF
        self.assertTrue(any("virgem" in e
                            for e in F5.confere_premissas(d, self.blob_a, "a")))
        d = bytearray(self.b4)
        d[self.BLOB] ^= 0xFF
        self.assertTrue(F5.confere_premissas(d, self.blob_a, "a"))

    def test_86_emulacao_b5a(self):
        m, view = self.aparelho(self.b5a)
        m.arquivos[b"0:/A/B.mp3"] = b"ID3\x04\x00\x00\x00\x00\x00\x00"
        m.arquivos[b"0:/A/C.mp3"] = b"RIFF\x00\x00\x00\x00\x00\x00"
        for path, src, nomes in (
                (b"0:/A/B.mp3", 0,
                 ["calloc", "f_open", "f_read", "f_close", "free",
                  "img_set_src"]),
                (b"0:/A/C.mp3", self.PH_DSC,
                 ["calloc", "f_open", "f_read", "f_close", "free",
                  "img_set_src"]),
                (b"0:/A/FALTA.mp3", self.PH_DSC,
                 ["calloc", "f_open", "free", "img_set_src"]),
                (b"lixo", self.PH_DSC, ["img_set_src"]),
                (b"", self.PH_DSC, ["img_set_src"])):
            ext, novas = self.tipo5(m, view, path)
            self.assertEqual(m.erros, [], path)
            self.assertEqual([c[0] for c in novas], nomes, path)
            self.assertEqual([c[2] for c in novas if c[0] == "img_set_src"],
                             [src], path)
            self.assertEqual(m.cstr(ext + 0x110), path, path)
            self.assertNotIn("get_task", [c[0] for c in novas], path)

    def test_87_emulacao_b5b(self):
        path = b"0:/A/B.mp3"
        dados = self.ativo("01_capa_v23.mp3")
        m, view = self.aparelho(self.b5b)
        self.monitor(m)
        m.arquivos[path] = dados
        m.arquivos[b"0:/A/C.mp3"] = dados
        ext, novas = self.tipo5(m, view, path, alvo=self.BLOB_B_XIP)
        self.assertEqual(m.erros, [])
        nomes = [c[0] for c in novas]
        self.assertEqual(nomes[0], "img_set_src")
        self.assertEqual(nomes[1:3], ["get_task", "unreg"])
        self.assertEqual(nomes[-3:], ["get_task", "reg", "img_set_src"])
        self.assertIn("calloc", nomes)
        self.assertIn("f_open", nomes)
        self.assertIn("f_close", nomes)
        self.assertEqual(m.abertos, {})
        srcs = [c[2] for c in novas if c[0] == "img_set_src"]
        self.assertEqual(srcs, [self.PH_DSC, ext])
        self.assertEqual(m.cstr(ext + 0x10), path)
        self.assertEqual(novas[1][1], 3)
        self.assertEqual(novas[2][1], 0x12345678)
        self.assertEqual(novas[-2][1], 0x12345678 + 0x50)
        n0 = len(m.chamadas)
        self.tipo5(m, view, path, alvo=self.BLOB_B_XIP)
        self.assertEqual(m.chamadas[n0:], [])
        n0 = len(m.chamadas)
        self.tipo5(m, view, b"0:/A/C.mp3", alvo=self.BLOB_B_XIP)
        self.assertEqual([c[0] for c in m.chamadas[n0:]][0], "img_set_src")
        self.assertEqual(m.cstr(ext + 0x10), b"0:/A/C.mp3")

    def test_88_emulacao_b5b_falhas(self):
        path = b"0:/A/B.mp3"
        dados = self.ativo("01_capa_v23.mp3")
        m, view = self.aparelho(self.b5b)
        self.monitor(m)
        m.arquivos[path] = b"notjpeg"
        _, novas = self.tipo5(m, view, path, alvo=self.BLOB_B_XIP)
        self.assertEqual(m.erros, [])
        nomes = [c[0] for c in novas]
        self.assertEqual(nomes[0], "img_set_src")
        self.assertEqual(nomes[1:3], ["get_task", "unreg"])
        self.assertEqual(nomes[-2:], ["get_task", "reg"])
        self.assertEqual([c[2] for c in novas if c[0] == "img_set_src"],
                         [self.PH_DSC])
        self.assertEqual(m.abertos, {})
        m, view = self.aparelho(self.b5b)
        self.monitor(m, unreg_ret=0)
        m.arquivos[path] = dados
        ext, novas = self.tipo5(m, view, path, alvo=self.BLOB_B_XIP)
        self.assertEqual([c[0] for c in novas if c[0] == "reg"], [])
        self.assertEqual([c[2] for c in novas if c[0] == "img_set_src"],
                         [self.PH_DSC, ext])
        m, view = self.aparelho(self.b5b)
        self.monitor(m, get_ret=0)
        m.arquivos[path] = dados
        ext, novas = self.tipo5(m, view, path, alvo=self.BLOB_B_XIP)
        self.assertEqual(novas[1][1], 3)
        self.assertNotIn("unreg", [c[0] for c in novas])
        self.assertNotIn("reg", [c[0] for c in novas])
        self.assertEqual([c[2] for c in novas if c[0] == "img_set_src"],
                         [self.PH_DSC, ext])
        m, view = self.aparelho(self.b5b)
        self.monitor(m)
        _, novas = self.tipo5(m, view, b"lixo", alvo=self.BLOB_B_XIP)
        self.assertEqual([c[0] for c in novas], ["img_set_src"])

    def test_89_guarda_nulos(self):
        for img, alvo in ((self.b5a, self.BLOB_XIP),
                          (self.b5b, self.BLOB_B_XIP)):
            for nome in ("pagina", "view", "titulo", "ext", "img", "texto"):
                m, view = self.aparelho(img)
                self.monitor(m)
                ext = m.le32(view + 0x30)
                if nome == "pagina":
                    m.escreve32(E.PAGINAS, 0)
                elif nome == "view":
                    m.escreve32(m.le32(E.PAGINAS) + 0xAC, 0)
                elif nome == "titulo":
                    m.escreve32(view + 4, 0)
                elif nome == "ext":
                    m.escreve32(view + 0x30, 0)
                elif nome == "img":
                    m.escreve32(ext + 0xC, 0)
                n0 = len(m.chamadas)
                self.tipo5(m, view, b"0:/A.mp3", texto=(nome != "texto"),
                           alvo=alvo)
                self.assertEqual(m.erros, [], nome)
                self.assertEqual(m.chamadas[n0:], [], nome)

    def test_90_mapa_e_receita(self):
        import build as B
        for rec in (self.RECEITA_A, self.RECEITA_B):
            self.assertIn(rec, B.RECEITAS)
            passo = B.RECEITAS[rec][-1]
            self.assertEqual(passo[0], "fab_diag_b5.py")
            self.assertIn("--degrau", passo[1])
            self.assertNotIn("fab_diag_b5.py", B.MAPA)
        t = le(os.path.join(RAIZ, "tests/test_catraca.py")).decode()
        self.assertNotIn(self.RECEITA_A, t)
        self.assertNotIn(self.RECEITA_B, t)

    def test_91_bit_thumb_nos_indiretos(self):
        from capstone import (Cs, CS_ARCH_ARM, CS_MODE_THUMB,
                              CS_MODE_LITTLE_ENDIAN)
        from capstone.arm import ARM_OP_REG

        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True

        def indiretos(cod, base):
            achados, mov = [], {}
            for i in md.disasm(cod, base):
                if i.mnemonic in ("movw", "movt"):
                    rd = i.reg_name(i.operands[0].reg)
                    imm = i.operands[1].imm
                    if i.mnemonic == "movw":
                        mov[rd] = imm & 0xFFFF
                    else:
                        mov[rd] = (mov.get(rd, 0) & 0xFFFF) | (imm << 16)
                elif i.mnemonic in ("bx", "blx") and i.operands:
                    op = i.operands[0]
                    if op.type == ARM_OP_REG and i.reg_name(op.reg) in mov:
                        rd = i.reg_name(op.reg)
                        achados.append((i.address, rd, mov.pop(rd)))
            return achados

        for cod, base, nome in ((self.blob_a, self.BLOB_XIP, "B5a"),
                                (self.blob_b, self.BLOB_B_XIP, "B5b")):
            for end, reg, alvo in indiretos(cod, base):
                self.assertTrue(alvo & 1,
                                f"{nome}: {reg}=0x{alvo:08X} par em "
                                f"0x{end:08X} (falta o bit Thumb)")

    def test_92_tabela_alinhada(self):
        from capstone import (Cs, CS_ARCH_ARM, CS_MODE_THUMB,
                              CS_MODE_LITTLE_ENDIAN)
        tabela = b"".join(struct.pack("<I", a) for a in
                          (0xD088E0, 0xD08970, 0xD08BEE, 0xD0902C,
                           0xD0EED4))
        for cod, base in ((self.blob_a, self.BLOB_XIP),
                          (self.blob_b, self.BLOB_B_XIP)):
            off = cod.index(tabela)
            end = self.BLOB_ENVIA_XIP + (off - (self.BLOB_ENVIA - self.BLOB))
            self.assertEqual(end % 4, 0,
                             f"a tabela em 0x{end:08X} nao e 4-alinhada")
            md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
            md.detail = True
            achou = False
            for i in md.disasm(cod[self.BLOB_ENVIA - self.BLOB:],
                               self.BLOB_ENVIA_XIP):
                if i.mnemonic == "adr":
                    imm = i.operands[1].imm
                elif i.mnemonic == "addw":
                    imm = i.operands[2].imm
                else:
                    continue
                if i.reg_name(i.operands[0].reg) != "r1":
                    continue
                alvo = ((i.address + 4) & ~3) + imm
                self.assertEqual(alvo, end,
                                 f"o adr em 0x{i.address:08X} aponta 0x{alvo:08X}")
                achou = True
                break
            self.assertTrue(achou, "o envia_path nao tem o adr r1, chamadores")


class B6(Base):
    r"""Os degraus B6a/B6b da ficha 014 (a capa sai da ViewTask).

    O B6a e o B4 exato, mas o envia_path da PreTask abre o MP3, le 10 B e
    manda o tipo 5 com o caminho ("ID3") ou vazio. O B6b decodifica a capa
    na PreTask (carrega_capa 0xDAA256), manda 8 mensagens tipo 6 de 1024 B
    e a view so copia os pixels para ext+0x210+offset; no ultimo pedaco faz
    img_set_src(img, ext). Nenhuma funcao de arquivo e alcancavel da view.
    """

    RECEITA_A = "reload_1.0_rc7_diag_b6a"
    RECEITA_B = "reload_1.0_rc7_diag_b6b"
    BLOB = 0x1AAA00
    BLOB_XIP = 0x00DAAA00
    BLOB_ENVIA = 0x1AAC00
    BLOB_ENVIA_XIP = 0x00DAAC00
    BLOB_MAX = 0x600
    P_BURST = 0x0FF0C4
    P_TYPE = 0x13223E
    P_TBB = 0x132242
    P_TITULO = 0x1AA0FE
    P_CARREGA = 0x1AA188
    CARREGA = 0x00DAA256
    PH_DSC = 0x00DA8000
    FALHA_BURST = 0x00CFF0DE
    ENVIA_LR = (0xD088E1, 0xD08971, 0xD08BEF, 0xD0902D, 0xD0EED5)
    OUTROS_LR = (0xD00C29, 0xCFF213)

    aparelho = B4.aparelho
    tipo5 = B4.tipo5
    titulo = B4.titulo
    xip_rom = B4.xip_rom
    _epilogo = staticmethod(B4._epilogo)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        p4 = os.path.join(cls.tmp, "b4.bin")
        rc4, log4 = constroi("reload_1.0_rc7_diag_b4", p4)
        cls.b4_rc, cls.b4_log = rc4, log4
        cls.b4 = le(p4) if os.path.exists(p4) else b""
        cls.blob_a = F6.monta_blob("a")
        cls.blob_b = F6.monta_blob("b")
        cls.b6a_rc, cls.b6a_log = constroi(cls.RECEITA_A,
                                           os.path.join(cls.tmp, "b6a.bin"))
        cls.b6a = (le(os.path.join(cls.tmp, "b6a.bin"))
                   if os.path.exists(os.path.join(cls.tmp, "b6a.bin")) else b"")
        cls.b6b_rc, cls.b6b_log = constroi(cls.RECEITA_B,
                                           os.path.join(cls.tmp, "b6b.bin"))
        cls.b6b = (le(os.path.join(cls.tmp, "b6b.bin"))
                   if os.path.exists(os.path.join(cls.tmp, "b6b.bin")) else b"")

    def roda(self, entrada, degrau, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_diag014x_")
        src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
        with open(src, "wb") as f:
            f.write(entrada)
        r = subprocess.run([sys.executable,
                            os.path.join(RAIZ, "tools/fab_diag_b6.py"),
                            "--in", src, "--out", dst, "--degrau", degrau]
                           + list(extra),
                           capture_output=True, text=True, cwd=RAIZ)
        return r.returncode, os.path.exists(dst), le(src) == entrada

    def ativo(self, nome):
        with open(os.path.join(ATIVOS, nome), "rb") as f:
            return f.read()

    @staticmethod
    def jpeg_do_mp3(mp3):
        """O primeiro JPEG de um APIC do ID3v2.3/v2.4 (o ativo da RC7)."""
        if mp3[:3] != b"ID3":
            return None
        n = ((mp3[6] & 0x7F) << 21) | ((mp3[7] & 0x7F) << 14) \
            | ((mp3[8] & 0x7F) << 7) | (mp3[9] & 0x7F)
        pos, fim = 10, 10 + n
        while pos + 10 <= fim:
            fid = mp3[pos:pos + 4]
            tam = struct.unpack(">I", mp3[pos + 4:pos + 8])[0]
            corpo = mp3[pos + 10:pos + 10 + tam]
            if fid == b"APIC":
                z = corpo.index(b"\0", 1)
                p = z + 1 + 1
                z = corpo.index(b"\0", p)
                return corpo[z + 1:]
            pos += 10 + tam
        return None

    def falsas(self, m, send_ret=1):
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                       UC_ARM_REG_R2, UC_ARM_REG_LR)

        def send(mq):
            p = mq.r(UC_ARM_REG_R0)
            n = struct.unpack("<H", mq.le(p + 0xA, 2))[0] + 0xC
            mq.chamadas.append(("send", p, mq.le(p, n)))
            return send_ret

        def send_view(mq):
            mq.chamadas.append(("send_view", mq.r(UC_ARM_REG_R0)))
            return 0

        def strncpy(mq):
            dst, src, n = (mq.r(UC_ARM_REG_R0), mq.r(UC_ARM_REG_R1),
                           mq.r(UC_ARM_REG_R2))
            s = mq.cstr(src, n)
            mq.escreve(dst, s + b"\0" * (n - len(s)))
            return dst

        def strlen(mq):
            return len(mq.cstr(mq.r(UC_ARM_REG_R0), 0x1000))

        def like(mq):
            mq.chamadas.append(("like", mq.r(UC_ARM_REG_R0),
                                mq.r(UC_ARM_REG_R1)))
            return 1

        def fim(mq):
            mq.u.reg_write(UC_ARM_REG_LR, E.FIM | 1)
            return 0

        m.falsas[0x00D0D818] = send
        m.falsas[0x00D0D880] = send_view
        m.falsas[0x00D6DB90] = like
        m.falsas[0x00D9FD54] = strncpy
        m.falsas[0x00000AA2] = strlen
        m.falsas[self.FALHA_BURST] = fim
        m.falsas[0x00D322A0] = self._epilogo

    def envia(self, m, path, dados, lr=0xD0EED5, ret=1):
        from unicorn.arm_const import UC_ARM_REG_R0
        m.chamadas.clear()
        m.erros.clear()
        buf = m.aloca(0x100, registra=False)
        m.escreve(buf, path + b"\0")
        if dados is None:
            m.arquivos.pop(path, None)
        else:
            m.arquivos[path] = dados
        sp = E.PILHA[0] + E.PILHA[1] - 0x100
        m.escreve32(sp + 0x14, lr)
        m.escreve32(sp + 4, 0)
        m.chama(self.BLOB_ENVIA_XIP, (ret, 0, 0, 0),
                salvos=[buf, E.AUDIO] + [0x11110000 + i for i in range(6)])
        self.assertEqual(m.erros, [], hex(lr))
        return sp, [c for c in m.chamadas
                    if c[0] in ("send", "send_view", "like")]

    LABEL_PROCESS = 0x00D32204

    def _msg_tipo6(self, m, off, dados, tipo):
        msg = m.aloca(0x414, registra=False)
        m.escreve(msg, b"\0" * 0x414)
        m.escreve(msg + 0, b"\x04")
        m.escreve(msg + 2, b"\x03")
        m.escreve(msg + 4, bytes([tipo]))
        m.escreve(msg + 6, b"\x03")
        m.escreve(msg + 0xC, b"\x01")
        m.escreve32(msg + 0x10, off)
        if dados is not None:
            m.escreve(msg + 0x14, dados)
        return msg

    def tipo6(self, m, view, off, dados=None, tipo=6):
        """Tipo 6 pelo label_process inteiro (0xD32204; push em 0xD3220C)."""
        ext = m.le32(view + 0x30)
        msg = self._msg_tipo6(m, off, dados, tipo)
        n0 = len(m.chamadas)
        salvos = [msg, view, msg + 0x14] + [0x11110000 + i for i in range(5)]
        epilogo = m.falsas.pop(0x00D322A0, None)
        tj = E.TJPGDEC
        E.TJPGDEC = (tj[0], 0x00D32300)
        try:
            m.chama(self.LABEL_PROCESS, (msg, 0, 0, 0), salvos=salvos)
        finally:
            E.TJPGDEC = tj
            if epilogo is not None:
                m.falsas[0x00D322A0] = epilogo
        return ext, m.chamadas[n0:]

    def tipo6_direto(self, m, view, off, dados=None, tipo=6):
        """Tipo 6 direto na view (guardas que o label_process nao alcanca)."""
        ext = m.le32(view + 0x30)
        msg = self._msg_tipo6(m, off, dados, tipo)
        n0 = len(m.chamadas)
        salvos = [msg, view, msg + 0x14] + [0x11110000 + i for i in range(5)]
        m.chama(self.BLOB_XIP, (0, 0, 0, tipo), salvos=salvos)
        return ext, m.chamadas[n0:]

    def test_100_b6_construida(self):
        self.assertEqual(self.b4_rc, 0, self.b4_log[-1500:])
        self.assertEqual(self.b6a_rc, 0, self.b6a_log[-2000:])
        self.assertEqual(self.b6b_rc, 0, self.b6b_log[-2000:])
        for img, tipo in ((self.b6a, b"\x05\x2b"), (self.b6b, b"\x06\x2b")):
            self.assertEqual(len(img), 0x200000)
            self.assertEqual(img[self.P_TYPE:self.P_TYPE + 2], tipo)
            self.assertEqual(desvio(img, self.P_TBB), self.BLOB_XIP)
            self.assertEqual(desvio(img, self.P_BURST), self.BLOB_ENVIA_XIP)
        self.assertEqual(self.b6a[self.BLOB:self.BLOB + 2], b"\x05\x2b")
        self.assertEqual(self.b6b[self.BLOB:self.BLOB + 2], b"\x06\x2b")

    def test_101_reprodutivel(self):
        tmp = tempfile.mkdtemp(prefix="openpod_diag014r_")
        for receita in (self.RECEITA_A, self.RECEITA_B):
            shas = []
            for i in range(2):
                p = os.path.join(tmp, f"{receita}{i}.bin")
                rc, log = constroi(receita, p)
                self.assertEqual(rc, 0, log[-1500:])
                shas.append(sha(le(p)))
            self.assertEqual(shas[0], shas[1], receita)

    def test_102_diff_exato(self):
        for nome, img, blob, tipo in (
                ("a", self.b6a, self.blob_a, b"\x05\x2b"),
                ("b", self.b6b, self.blob_b, b"\x06\x2b")):
            dif = [i for i in range(len(img)) if img[i] != self.b4[i]]
            regioes = [(self.P_TBB, 4), (self.P_BURST, 12),
                       (self.BLOB, self.BLOB_MAX)]
            if nome == "b":
                regioes.append((self.P_TYPE, 2))
            for i in dif:
                self.assertTrue(any(o <= i < o + t for o, t in regioes),
                                f"B6{nome}: byte fora do patch: 0x{i:06X}")
                self.assertGreaterEqual(i, 0x00E000)
                self.assertFalse(0xD000 <= i < 0xE000)
                self.assertLess(i, 0x1FC000)
            self.assertEqual(img[self.P_TYPE:self.P_TYPE + 2], tipo)
            self.assertEqual(img[self.P_TITULO:self.P_TITULO + 4],
                             self.b4[self.P_TITULO:self.P_TITULO + 4])
            self.assertEqual(img[self.P_CARREGA:self.P_CARREGA + 4],
                             self.b4[self.P_CARREGA:self.P_CARREGA + 4])
            self.assertEqual(img[self.P_BURST + 4:self.P_BURST + 12],
                             b"\x00\xbf" * 4)
            self.assertEqual(img[self.BLOB:self.BLOB + len(blob)], blob)

    def test_103_decodificacao(self):
        self.assertEqual(self.b6a[self.BLOB:self.BLOB + 0x200],
                         self.b4[self.BLOB:self.BLOB + 0x200])
        self.assertEqual(self.b6b[self.BLOB:self.BLOB + 2], b"\x06\x2b")
        self.assertIn(b"\x05\x2b", self.b6b[self.BLOB:self.BLOB + 0x200])
        for img, tipo in ((self.b6a, b"\x05\x2b"), (self.b6b, b"\x06\x2b")):
            self.assertEqual(img[self.P_TYPE:self.P_TYPE + 2], tipo)
            self.assertEqual(desvio(img, self.P_TBB), self.BLOB_XIP)
            self.assertEqual(desvio(img, self.P_BURST), self.BLOB_ENVIA_XIP)
            self.assertEqual(img[self.BLOB_ENVIA:self.BLOB_ENVIA + 4],
                             b"\x2d\xe9\xf0\x41")
        self.assertIn(b"\x40\xf2\x5c\x21", self.blob_a)  # movw r1,#0x25C
        self.assertIn(b"\x42\xf2\x10\x21", self.blob_b)  # movw r1,#0x2210
        self.assertIn(b"\xb3\xf5\xe0\x5f", self.blob_b)  # cmp.w r3,#0x1C00

    def test_104_recusas(self):
        for degrau, img in (("a", self.b6a), ("b", self.b6b)):
            for nome, entrada in (("rc7", self.rc7), ("propria", img)):
                rc, criou, intacta = self.roda(entrada, degrau,
                                               ["--em", "0x1a8000"])
                self.assertNotEqual(rc, 0, f"{degrau}:{nome}")
                self.assertFalse(criou, f"{degrau}:{nome}")
                self.assertTrue(intacta, f"{degrau}:{nome}")
            rc, criou, intacta = self.roda(self.b4, degrau,
                                           ["--em", "0x1A9000"])
            self.assertNotEqual(rc, 0, degrau)
            self.assertFalse(criou, degrau)
            self.assertTrue(intacta, degrau)
            rc, criou, intacta = self.roda(self.b4, degrau, ["--dry-run"])
            self.assertEqual((rc, criou), (0, False), degrau)
            self.assertTrue(intacta, degrau)
            for tipo in ("mesmo", "symlink", "hardlink"):
                tmp = tempfile.mkdtemp(prefix="openpod_diag014l_")
                src = os.path.join(tmp, "in.bin")
                dst = os.path.join(tmp, "out.bin")
                with open(src, "wb") as f:
                    f.write(self.b4)
                if tipo == "mesmo":
                    dst = src
                else:
                    (os.symlink if tipo == "symlink" else os.link)(src, dst)
                r = subprocess.run([sys.executable,
                                    os.path.join(RAIZ, "tools/fab_diag_b6.py"),
                                    "--in", src, "--out", dst,
                                    "--degrau", degrau],
                                   capture_output=True, cwd=RAIZ)
                self.assertNotEqual(r.returncode, 0, f"{degrau}:{tipo}")
                self.assertEqual(le(src), self.b4, f"{degrau}:{tipo}")

    def test_105_premissas(self):
        self.assertEqual(F6.confere_premissas(bytearray(self.b4),
                                              self.blob_a, "a"), [])
        self.assertEqual(F6.confere_premissas(bytearray(self.b4),
                                              self.blob_b, "b"), [])
        for outra in (self.rc7, self.b6a, self.b6b):
            self.assertTrue(F6.confere_premissas(bytearray(outra),
                                                 self.blob_a, "a"))
        for off in (self.P_TBB, self.P_BURST, self.P_TYPE,
                    self.P_TITULO, self.P_CARREGA, self.BLOB):
            d = bytearray(self.b4)
            d[off] ^= 0x01
            self.assertTrue(F6.confere_premissas(d, self.blob_a, "a"),
                            hex(off))
        d = bytearray(self.b4)
        d[self.BLOB + 0x2D9] ^= 0xFF
        self.assertTrue(any("virgem" in e for e in
                            F6.confere_premissas(d, self.blob_a, "a")))
        self.assertTrue(F6.confere_premissas(bytearray(self.b4),
                                             self.blob_b, "a"))
        self.assertTrue(F6.confere_premissas(bytearray(self.b4),
                                             self.blob_a, "b"))

    def test_106_emulacao_b6a(self):
        path = b"0:/A/B.mp3"
        m, view = self.aparelho(self.b6a)
        self.falsas(m)
        for p, src in ((b"0:/A/B.mp3", 0), (b"0:\\A.mp3", 0),
                       (b"lixo", self.PH_DSC), (b"", self.PH_DSC)):
            ext, novas = self.tipo5(m, view, p)
            self.assertEqual(m.erros, [], p)
            self.assertEqual([c[0] for c in novas], ["img_set_src"], p)
            self.assertEqual([c[2] for c in novas], [src], p)
        sp, c = self.envia(m, path, b"ID3\x04\x00\x00\x00\x00\x00\x00")
        self.assertEqual([x[0] for x in c], ["send", "send_view", "like"])
        msg = c[0][1]
        self.assertEqual(c[0][2][4], 5)
        self.assertEqual(struct.unpack("<I", c[0][2][0x10:0x14])[0], len(path))
        self.assertEqual(struct.unpack("<H", c[0][2][0xA:0xC])[0], len(path) + 9)
        self.assertEqual(m.cstr(msg + 0x14), path)
        self.assertEqual(c[2][2], sp + 4)
        sp, c = self.envia(m, path, b"RIFF\x00\x00\x00\x00\x00\x00")
        self.assertEqual([x[0] for x in c], ["send", "send_view", "like"])
        self.assertEqual(struct.unpack("<I", c[0][2][0x10:0x14])[0], 0)
        self.assertEqual(struct.unpack("<H", c[0][2][0xA:0xC])[0], 9)
        self.assertEqual(m.cstr(c[0][1] + 0x14), b"")
        sp, c = self.envia(m, path, None)
        self.assertEqual([x[0] for x in c], ["send", "send_view", "like"])
        self.assertEqual(struct.unpack("<I", c[0][2][0x10:0x14])[0], 0)
        sp, c = self.envia(m, path, b"ID3\x04\x00\x00\x00\x00\x00\x00",
                           ret=0)
        self.assertEqual([x[0] for x in c], ["send", "send_view"])
        self.assertEqual(c[0][2][4], 5)
        for lr in self.ENVIA_LR:
            _, c = self.envia(m, path, b"ID3\x04\x00\x00\x00\x00\x00\x00",
                              lr=lr)
            self.assertEqual([x[0] for x in c], ["send", "send_view", "like"], hex(lr))
        for lr in self.OUTROS_LR:
            _, c = self.envia(m, path, b"ID3\x04\x00\x00\x00\x00\x00\x00",
                              lr=lr)
            self.assertEqual([x[0] for x in c], ["like"], hex(lr))
        self.assertEqual(m.abertos, {})

    def test_107_emulacao_b6b_view(self):
        m, view = self.aparelho(self.b6b)
        self.falsas(m)
        m.chamadas.clear()
        ext = m.le32(view + 0x30)
        m.escreve(ext + 0x210, b"\xAA" * 0x2000)
        for off in range(0, 0x2000, 0x400):
            _, novas = self.tipo6(m, view, off,
                                  bytes([off // 0x400]) * 0x400)
            self.assertEqual(m.erros, [], hex(off))
            nomes = [c[0] for c in novas]
            self.assertEqual(nomes.count("img_set_src"),
                             1 if off == 0x1C00 else 0, hex(off))
            self.assertFalse(any(n in nomes for n in
                                 ("f_open", "f_read", "f_close", "calloc",
                                  "free")), hex(off))
        self.assertEqual(m.le(ext + 0x210, 0x2000),
                         b"".join(bytes([i]) * 0x400 for i in range(8)))
        self.assertEqual([c[2] for c in m.chamadas if c[0] == "img_set_src"],
                         [ext])
        for off in (0x1C01, 0x1C02, 0x2000):
            _, novas = self.tipo6(m, view, off, b"\x00" * 0x400)
            self.assertEqual(m.erros, [], hex(off))
            self.assertEqual([c[0] for c in novas], [], hex(off))
        for nome in ("pagina", "view", "ext", "img"):
            m, view = self.aparelho(self.b6b)
            self.falsas(m)
            ext = m.le32(view + 0x30)
            if nome == "pagina":
                m.escreve32(E.PAGINAS, 0)
            elif nome == "view":
                m.escreve32(m.le32(E.PAGINAS) + 0xAC, 0)
            elif nome == "ext":
                m.escreve32(view + 0x30, 0)
            else:
                m.escreve32(ext + 0xC, 0)
            _, novas = self.tipo6_direto(m, view, 0, b"\x00" * 0x400)
            self.assertEqual(m.erros, [], nome)
            self.assertEqual([c[0] for c in novas], [], nome)

    def test_108_emulacao_b6b_envia(self):
        path = b"0:/A/B.mp3"
        dados = self.ativo("01_capa_v23.mp3")
        jpeg = self.jpeg_do_mp3(dados)
        self.assertIsNotNone(jpeg)
        ref = E.referencia(le(os.path.join(RAIZ, "firmware/ORIGINAL/"
                                           "GN438_original.bin")), jpeg)
        m, view = self.aparelho(self.b6b)
        self.falsas(m)
        sp, c = self.envia(m, path, dados)
        self.assertEqual([x[0] for x in c], ["send"] * 8 + ["send_view", "like"])
        self.assertEqual([x[2][4] for x in c[:8]], [6] * 8)
        self.assertEqual([struct.unpack("<I", x[2][0x10:0x14])[0]
                          for x in c[:8]], list(range(0, 0x2000, 0x400)))
        self.assertEqual([struct.unpack("<H", x[2][0xA:0xC])[0]
                          for x in c[:8]], [0x408] * 8)
        self.assertEqual(b"".join(x[2][0x14:0x414] for x in c[:8]), ref)
        self.assertEqual(m.abertos, {})
        m, view = self.aparelho(self.b6b)
        self.falsas(m, send_ret=0)
        sp, c = self.envia(m, path, dados)
        self.assertEqual([x[0] for x in c], ["send", "send", "send_view", "like"])
        self.assertEqual(c[0][2][4], 6)
        self.assertEqual(c[1][2][4], 5)
        self.assertEqual(struct.unpack("<I", c[1][2][0x10:0x14])[0], 0)
        self.assertEqual(m.abertos, {})
        m, view = self.aparelho(self.b6b)
        self.falsas(m)
        sp, c = self.envia(m, path, b"notjpeg")
        self.assertEqual([x[0] for x in c], ["send", "send_view", "like"])
        self.assertEqual(c[0][2][4], 5)
        self.assertEqual(m.abertos, {})
        sp, c = self.envia(m, path, dados, ret=0)
        self.assertEqual([x[0] for x in c], ["send", "send_view"])
        self.assertEqual(c[0][2][4], 5)
        for lr in self.ENVIA_LR:
            _, c = self.envia(m, path, dados, lr=lr)
            self.assertEqual([x[0] for x in c],
                             ["send"] * 8 + ["send_view", "like"],
                             hex(lr))
        for lr in self.OUTROS_LR:
            _, c = self.envia(m, path, dados, lr=lr)
            self.assertEqual([x[0] for x in c], ["like"], hex(lr))

    def test_109_bit_thumb_nos_indiretos(self):
        from capstone import (Cs, CS_ARCH_ARM, CS_MODE_THUMB,
                              CS_MODE_LITTLE_ENDIAN)
        from capstone.arm import ARM_OP_REG

        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True

        def indiretos(cod, base):
            achados, mov = [], {}
            for i in md.disasm(cod, base):
                if i.mnemonic in ("movw", "movt"):
                    rd = i.reg_name(i.operands[0].reg)
                    imm = i.operands[1].imm
                    if i.mnemonic == "movw":
                        mov[rd] = imm & 0xFFFF
                    else:
                        mov[rd] = (mov.get(rd, 0) & 0xFFFF) | (imm << 16)
                elif i.mnemonic in ("bx", "blx") and i.operands:
                    op = i.operands[0]
                    if op.type == ARM_OP_REG and i.reg_name(op.reg) in mov:
                        rd = i.reg_name(op.reg)
                        achados.append((i.address, rd, mov.pop(rd)))
            return achados

        for cod, nome in ((self.blob_a, "B6a"), (self.blob_b, "B6b")):
            for end, reg, alvo in indiretos(cod, self.BLOB_XIP):
                self.assertTrue(alvo & 1,
                                f"{nome}: {reg}=0x{alvo:08X} par em "
                                f"0x{end:08X} (falta o bit Thumb)")

    def test_110_tabela_alinhada(self):
        from capstone import (Cs, CS_ARCH_ARM, CS_MODE_THUMB,
                              CS_MODE_LITTLE_ENDIAN)
        tabela = b"".join(struct.pack("<I", a) for a in
                          (0xD088E0, 0xD08970, 0xD08BEE, 0xD0902C,
                           0xD0EED4))
        for cod in (self.blob_a, self.blob_b):
            off = cod.index(tabela)
            end = self.BLOB_XIP + off
            self.assertEqual(end % 4, 0,
                             f"a tabela em 0x{end:08X} nao e 4-alinhada")
            md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
            md.detail = True
            achou = False
            for i in md.disasm(cod[self.BLOB_ENVIA - self.BLOB:],
                               self.BLOB_ENVIA_XIP):
                if i.mnemonic == "adr":
                    imm = i.operands[1].imm
                elif i.mnemonic == "addw":
                    imm = i.operands[2].imm
                else:
                    continue
                if i.reg_name(i.operands[0].reg) != "r1":
                    continue
                alvo = ((i.address + 4) & ~3) + imm
                self.assertEqual(alvo, end,
                                 f"o adr em 0x{i.address:08X} aponta "
                                 f"0x{alvo:08X}")
                achou = True
                break
            self.assertTrue(achou, "o envia_path nao tem o adr r1, chamadores")

    def test_111_pilha(self):
        from unicorn import UC_HOOK_CODE
        from unicorn.arm_const import UC_ARM_REG_SP
        path = b"0:/A/B.mp3"
        dados = self.ativo("01_capa_v23.mp3")
        m, view = self.aparelho(self.b6b)
        self.falsas(m)
        buf = m.aloca(0x100, registra=False)
        m.escreve(buf, path + b"\0")
        m.arquivos[path] = dados
        sp = E.PILHA[0] + E.PILHA[1] - 0x100
        m.escreve32(sp + 0x14, 0xD0EED5)
        mn = [0xFFFFFFFF]

        def cb(uc, a, tam, ud):
            s = uc.reg_read(UC_ARM_REG_SP)
            if s < mn[0]:
                mn[0] = s

        m.u.hook_add(UC_HOOK_CODE, cb)
        m.chama(self.BLOB_ENVIA_XIP, (1, 0, 0, 0),
                salvos=[buf, E.AUDIO] + [0x11110000 + i for i in range(6)])
        self.assertEqual(m.erros, [])
        usado = sp - mn[0]
        self.assertLessEqual(usado, 512, f"o B6b usa {usado} B de pilha")
        self.assertGreaterEqual(2048 - 152 - usado, 512,
                                f"sobram {2048 - 152 - usado} B")

    def test_113_view_sem_arquivo(self):
        """A view nao alcanca f_open/f_read/f_lseek/f_close/carrega_capa."""
        from capstone import (Cs, CS_ARCH_ARM, CS_MODE_THUMB,
                              CS_MODE_LITTLE_ENDIAN)
        from capstone.arm import ARM_OP_REG, ARM_OP_IMM
        arquivo = {0xD777CC, 0xD76854, 0xD76C0A, 0xD77C9C, self.CARREGA}
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True
        for cod, nome in ((self.blob_a, "B6a"), (self.blob_b, "B6b")):
            alvos, mov = set(), {}
            for i in md.disasm(cod[:0x200], self.BLOB_XIP):
                if i.mnemonic in ("movw", "movt"):
                    rd = i.reg_name(i.operands[0].reg)
                    imm = i.operands[1].imm
                    if i.mnemonic == "movw":
                        mov[rd] = imm & 0xFFFF
                    else:
                        mov[rd] = (mov.get(rd, 0) & 0xFFFF) | (imm << 16)
                elif i.mnemonic in ("bl", "blx", "bx") and i.operands:
                    op = i.operands[0]
                    if op.type == ARM_OP_IMM:
                        alvos.add(op.imm & ~1)
                    elif op.type == ARM_OP_REG and i.reg_name(op.reg) in mov:
                        alvos.add(mov.pop(i.reg_name(op.reg)) & ~1)
            self.assertFalse(arquivo & alvos,
                             f"{nome}: a view alcanca {arquivo & alvos}")
        for marca in (b"\x47\xf2\xcd\x7c\xc0\xf2\xd7\x0c\xe0\x47",
                      b"\x46\xf6\x55\x0c\xc0\xf2\xd7\x0c\xe0\x47",
                      b"\x47\xf6\x9d\x4c\xc0\xf2\xd7\x0c\xe0\x47"):
            self.assertIn(marca, self.blob_a[self.BLOB_ENVIA - self.BLOB:])
        self.assertIn(b"\x4a\xf2\x57\x2c\xc0\xf2\xda\x0c\xe0\x47",
                      self.blob_b[self.BLOB_ENVIA - self.BLOB:])

    def test_114_emulacao_b6b_ativos(self):
        path = b"0:/A/B.mp3"
        validos = ("01_capa_v23.mp3", "02_capa_v24.mp3",
                   "03_capa_v24_cabecalho_estendido.mp3")
        falhas = ("04_capa_progressiva.mp3", "05_capa_png.mp3",
                  "06_sem_capa.mp3", "07_sem_tag.mp3")
        m, view = self.aparelho(self.b6b)
        self.falsas(m)
        for nome in validos:
            _, c = self.envia(m, path, self.ativo(nome))
            self.assertEqual([x[0] for x in c],
                             ["send"] * 8 + ["send_view", "like"], nome)
            self.assertEqual([x[2][4] for x in c[:8]], [6] * 8, nome)
            self.assertEqual(m.abertos, {}, nome)
        for nome in falhas:
            _, c = self.envia(m, path, self.ativo(nome))
            self.assertEqual([x[0] for x in c],
                             ["send", "send_view", "like"], nome)
            self.assertEqual(c[0][2][4], 5, nome)
            self.assertEqual(struct.unpack("<I", c[0][2][0x10:0x14])[0], 0,
                             nome)
            self.assertEqual(m.abertos, {}, nome)

    def test_112_mapa_e_receita(self):
        import build as B
        for rec in (self.RECEITA_A, self.RECEITA_B):
            self.assertIn(rec, B.RECEITAS)
            passo = B.RECEITAS[rec][-1]
            self.assertEqual(passo[0], "fab_diag_b6.py")
            self.assertIn("--degrau", passo[1])
            self.assertNotIn("fab_diag_b6.py", B.MAPA)
        t = le(os.path.join(RAIZ, "tests/test_catraca.py")).decode()
        self.assertNotIn(self.RECEITA_A, t)
        self.assertNotIn(self.RECEITA_B, t)


class B7(Base):
    r"""Os degraus B7a/B7b da ficha 015 (a capa de 500 nao engasga).

    O B7a e o B6b exato + a regra de escala 56 no carrega_capa: as quatro
    comparacoes com 64 viram 56. O B7b e o B7a + dois wrappers que chamam
    o callback original do TJpgDec e depois vPortYield (0xC43634), N=1.
    Nao ha sleep; a primeira pausa e depois da primeira leitura.
    """

    RECEITA_A = "reload_1.0_rc7_diag_b7a"
    RECEITA_B = "reload_1.0_rc7_diag_b7b"
    BLOB = 0x1AAA00
    BLOB_XIP = 0x00DAAA00
    BLOB_ENVIA_XIP = 0x00DAAC00
    WRAP = 0x1AAE00
    WRAP_XIP = 0x00DAAE00
    WRAP_IN = 0x00DAAE01
    WRAP_OUT = 0x00DAAE21
    P_IN = 0x1AA30C
    P_OUT = 0x1AA376
    P_VIEW6 = 0x1AAABC
    VIEW6 = 0x1AAE60
    VIEW6_LEN = 0x22
    ESCALA = (0x1AA32C, 0x1AA330, 0x1AA346, 0x1AA34E)
    P_TYPE = 0x13223E
    P_TBB = 0x132242
    P_BURST = 0x0FF0C4
    P_CARREGA = 0x1AA188
    CARREGA = 0x00DAA256
    YIELD = 0x00C43634
    LABEL_PROCESS = 0x00D32204
    FALHA_BURST = 0x00CFF0DE

    aparelho = B6.aparelho
    xip_rom = B4.xip_rom
    falsas = B6.falsas
    _epilogo = staticmethod(B4._epilogo)
    tipo6 = B6.tipo6
    tipo6_direto = B6.tipo6_direto

    def _msg_tipo6(self, m, off, dados, tipo):
        # O B7b exige o comprimento 0x408 em msg+0xA antes de copiar.
        msg = B6._msg_tipo6(self, m, off, dados, tipo)
        m.escreve(msg + 0xA, struct.pack("<H", 0x408))
        return msg

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.b6b_rc, cls.b6b_log = constroi(
            "reload_1.0_rc7_diag_b6b",
            os.path.join(cls.tmp, "b6b_015.bin"))
        cls.b6b = (le(os.path.join(cls.tmp, "b6b_015.bin"))
                   if os.path.exists(os.path.join(cls.tmp, "b6b_015.bin"))
                   else b"")
        cls.b7a_rc, cls.b7a_log = constroi(
            cls.RECEITA_A, os.path.join(cls.tmp, "b7a.bin"))
        cls.b7a = (le(os.path.join(cls.tmp, "b7a.bin"))
                   if os.path.exists(os.path.join(cls.tmp, "b7a.bin")) else b"")
        cls.b7b_rc, cls.b7b_log = constroi(
            cls.RECEITA_B, os.path.join(cls.tmp, "b7b.bin"))
        cls.b7b = (le(os.path.join(cls.tmp, "b7b.bin"))
                   if os.path.exists(os.path.join(cls.tmp, "b7b.bin")) else b"")
        cls.blob = F7.monta_blob()

    def roda(self, entrada, degrau, extra=()):
        tmp = tempfile.mkdtemp(prefix="openpod_diag015x_", dir=RAIZ)
        try:
            src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
            with open(src, "wb") as f:
                f.write(entrada)
            r = subprocess.run([sys.executable,
                                os.path.join(RAIZ, "tools/fab_diag_b7.py"),
                                "--in", src, "--out", dst, "--degrau", degrau]
                               + list(extra),
                               capture_output=True, text=True, cwd=RAIZ)
            return r.returncode, os.path.exists(dst), le(src) == entrada
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def ativo(self, nome):
        with open(os.path.join(ATIVOS, nome), "rb") as f:
            return f.read()

    @staticmethod
    def jpeg_do_mp3(mp3):
        return B6.jpeg_do_mp3(mp3)

    @staticmethod
    def escala_b7(w, h):
        """Maior s em 0..3 com (w>>s) >= 56 e (h>>s) >= 56; None se < 56."""
        if w < 56 or h < 56:
            return None
        return max(s for s in range(4) if (w >> s) >= 56 and (h >> s) >= 56)

    def referencia_b7(self, jpeg):
        old = E.escala_de
        E.escala_de = self.escala_b7
        try:
            return E.referencia(
                le(os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")),
                jpeg)
        finally:
            E.escala_de = old

    def carrega(self, img, jpeg, conta=False, pausa=False):
        from unicorn import UC_HOOK_CODE
        from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_SP

        m = E.Maquina(img)
        tmp = m.aloca(0x2210, registra=False)
        path = b"0:/A/B.mp3"
        m.escreve(tmp + 0x110, path + b"\0")
        m.arquivos[path] = E.tag_id3(3, [E.apic(3, jpeg)])
        c = {"in": 0, "out": 0, "yield": 0}
        sp0 = E.PILHA[0] + E.PILHA[1] - 0x100
        mn = [sp0]

        def code(uc, a, tam, ud):
            if a == 0x00DAA404:
                c["in"] += 1
            elif a == 0x00DAA476:
                c["out"] += 1

        def spcb(uc, a, tam, ud):
            s = uc.reg_read(UC_ARM_REG_SP)
            if s < mn[0]:
                mn[0] = s

        m.u.hook_add(UC_HOOK_CODE, spcb)

        if conta:
            m.u.hook_add(UC_HOOK_CODE, code,
                         begin=0x00DAA404, end=0x00DAA405)
            m.u.hook_add(UC_HOOK_CODE, code,
                         begin=0x00DAA476, end=0x00DAA477)
        if pausa:
            m.u.mem_map(0xE000E000, 0x1000)

            def yld(mq):
                c["yield"] += 1
                mq.chamadas.append(("yield", mq.r(UC_ARM_REG_R0)))
                return 0

            m.falsas[self.YIELD] = yld
        r = m.chama(self.CARREGA, (tmp,), tempo=180)
        px = m.le(tmp + 0x210, 0x2000)
        c["sp"] = mn[0]
        c["sp0"] = sp0
        return m, r, px, c

    def test_115_b7_construida(self):
        self.assertEqual(self.b6b_rc, 0, self.b6b_log[-2000:])
        self.assertEqual(self.b7a_rc, 0, self.b7a_log[-2000:])
        self.assertEqual(self.b7b_rc, 0, self.b7b_log[-2000:])
        self.assertEqual(len(self.b7a), 0x200000)
        self.assertEqual(len(self.b7b), 0x200000)
        for off in self.ESCALA:
            self.assertEqual(self.b6b[off], 0x40, hex(off))
            self.assertEqual(self.b7a[off], 0x38, hex(off))
        self.assertEqual(self.b7a[self.BLOB:self.BLOB + 0x600],
                         self.b6b[self.BLOB:self.BLOB + 0x600])
        self.assertEqual(self.b7b[self.P_IN:self.P_IN + 4],
                         bytes.fromhex("dff8401b"))
        self.assertEqual(self.b7b[self.P_OUT:self.P_OUT + 4],
                         bytes.fromhex("dff8dc1a"))
        self.assertEqual(self.b7b[self.WRAP:self.WRAP + 0x58],
                         self.blob[0x400:0x458])
        self.assertEqual((self.WRAP + 0x50) % 4, 0)
        self.assertEqual(self.b7b[self.WRAP + 0x50:self.WRAP + 0x58],
                         struct.pack("<II", self.WRAP_IN, self.WRAP_OUT))
        for marca in ("4af2054c", "4af2774c", "43f2356c",
                      "4af6c32c", "4af6fb2c"):
            self.assertIn(bytes.fromhex(marca), self.blob)
        self.assertEqual(self.b6b[self.P_VIEW6:self.P_VIEW6 + 4],
                         b"\xb3\xf5\xe0\x5f")
        self.assertEqual(self.b7a[self.P_VIEW6:self.P_VIEW6 + 4],
                         b"\xb3\xf5\xe0\x5f")
        self.assertEqual(self.b7b[self.P_VIEW6:self.P_VIEW6 + 4],
                         F7.BRANCH_VIEW6)
        self.assertEqual(self.b7b[self.VIEW6:self.VIEW6 + self.VIEW6_LEN],
                         F7.VIEW6_COD)
        self.assertEqual(self.b7b[self.P_TYPE:self.P_TYPE + 2], b"\x06\x2b")
        self.assertEqual(desvio(self.b7b, self.P_TBB), self.BLOB_XIP)
        self.assertEqual(desvio(self.b7b, self.P_BURST), self.BLOB_ENVIA_XIP)
        self.assertEqual(self.b7b[self.P_CARREGA:self.P_CARREGA + 4],
                         b"\x00\x20\x00\xbf")

    def test_116_reprodutivel(self):
        tmp = tempfile.mkdtemp(prefix="openpod_diag015r_", dir=RAIZ)
        try:
            for receita in (self.RECEITA_A, self.RECEITA_B):
                shas = []
                for i in range(2):
                    p = os.path.join(tmp, f"{receita}{i}.bin")
                    rc, log = constroi(receita, p)
                    self.assertEqual(rc, 0, log[-1500:])
                    shas.append(sha(le(p)))
                self.assertEqual(shas[0], shas[1], receita)
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_117_diff_exato(self):
        dif_a = [i for i in range(len(self.b6b))
                 if self.b7a[i] != self.b6b[i]]
        self.assertEqual(dif_a, list(self.ESCALA))
        regioes_b = [(self.P_IN, 4), (self.P_OUT, 4),
                     (self.P_VIEW6, 4), (self.WRAP, 0x58),
                     (self.VIEW6, self.VIEW6_LEN)] \
                    + [(o, 1) for o in self.ESCALA]
        dif_b = [i for i in range(len(self.b6b))
                 if self.b7b[i] != self.b6b[i]]
        for i in dif_b:
            self.assertTrue(any(o <= i < o + t for o, t in regioes_b),
                            f"B7b: byte fora do patch: 0x{i:06X}")
            self.assertGreaterEqual(i, 0x00E000)
            self.assertFalse(0xD000 <= i < 0xE000)
            self.assertLess(i, 0x1FC000)
        self.assertEqual(self.b7b[self.WRAP:self.WRAP + 0x58],
                         self.blob[0x400:0x458])
        for off in self.ESCALA:
            self.assertEqual(self.b7a[off], 0x38)
            self.assertEqual(self.b7a[off + 1], self.b6b[off + 1])

    def test_118_recusas(self):
        for degrau, img in (("a", self.b7a), ("b", self.b7b)):
            for nome, entrada in (("rc7", self.rc7),
                                  ("propria", img)):
                rc, criou, intacta = self.roda(entrada, degrau,
                                               ["--em", "0x1a8000"])
                self.assertNotEqual(rc, 0, f"{degrau}:{nome}")
                self.assertFalse(criou, f"{degrau}:{nome}")
                self.assertTrue(intacta, f"{degrau}:{nome}")
            rc, criou, intacta = self.roda(self.b6b, degrau,
                                           ["--em", "0x1A9000"])
            self.assertNotEqual(rc, 0, degrau)
            self.assertFalse(criou, degrau)
            self.assertTrue(intacta, degrau)
            rc, criou, intacta = self.roda(self.b6b, degrau, ["--dry-run"])
            self.assertEqual((rc, criou), (0, False), degrau)
            self.assertTrue(intacta, degrau)
            for tipo in ("mesmo", "symlink", "hardlink"):
                tmp = tempfile.mkdtemp(prefix="openpod_diag015l_", dir=RAIZ)
                try:
                    src = os.path.join(tmp, "in.bin")
                    dst = os.path.join(tmp, "out.bin")
                    with open(src, "wb") as f:
                        f.write(self.b6b)
                    if tipo == "mesmo":
                        dst = src
                    else:
                        (os.symlink if tipo == "symlink" else os.link)(src, dst)
                    r = subprocess.run([sys.executable,
                                        os.path.join(RAIZ, "tools/fab_diag_b7.py"),
                                        "--in", src, "--out", dst,
                                        "--degrau", degrau],
                                       capture_output=True, cwd=RAIZ)
                    self.assertNotEqual(r.returncode, 0, f"{degrau}:{tipo}")
                    self.assertEqual(le(src), self.b6b, f"{degrau}:{tipo}")
                finally:
                    import shutil
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_119_premissas(self):
        for degrau in ("a", "b"):
            self.assertEqual(F7.confere_premissas(bytearray(self.b6b),
                                                  self.blob, degrau), [])
        for outra in (self.rc7, self.b7a, self.b7b):
            self.assertTrue(F7.confere_premissas(bytearray(outra),
                                                 self.blob, "b"))
        for off in self.ESCALA + (self.P_IN, self.P_OUT,
                                  self.BLOB, self.WRAP):
            d = bytearray(self.b6b)
            d[off] ^= 0x01
            self.assertTrue(F7.confere_premissas(d, self.blob, "b"), hex(off))
        d = bytearray(self.b6b)
        d[self.P_TYPE] ^= 0x01
        self.assertTrue(F7.confere_premissas(d, self.blob, "b"))
        self.assertEqual(F7.confere_premissas(bytearray(self.b6b),
                                              self.blob, "a"), [])

    def test_120_emulacao_b7a(self):
        casos = (("capa_a_300.jpg", 34, 361),
                 ("capa_b_500.jpg", 77, 961),
                 ("capa_d_1000.jpg", 164, 3969))
        for nome, n_in, n_out in casos:
            jpeg = self.ativo(nome)
            m, r, px, c = self.carrega(self.b7a, jpeg, conta=True)
            self.assertEqual(m.erros, [], nome)
            self.assertEqual(r, 1, nome)
            self.assertEqual(px, self.referencia_b7(jpeg), nome)
            self.assertEqual((c["in"], c["out"]), (n_in, n_out), nome)
            self.assertEqual(m.abertos, {}, nome)
        m, r, px, _ = self.carrega(self.b7a, self.ativo("capa_pequena_48.jpg"))
        self.assertEqual((r, px), (0, b"\0" * 0x2000))
        self.assertEqual(m.erros, [])

    def test_121_emulacao_b7b(self):
        jpeg = self.ativo("capa_b_500.jpg")
        _, _, px_a, c_a = self.carrega(self.b7a, jpeg, conta=True)
        m, r, px_b, c_b = self.carrega(self.b7b, jpeg, conta=True, pausa=True)
        self.assertEqual(m.erros, [])
        self.assertEqual(r, 1)
        self.assertEqual(px_b, px_a)
        self.assertEqual((c_b["in"], c_b["out"]), (c_a["in"], c_a["out"]))
        self.assertEqual(c_b["yield"], c_a["in"] + c_a["out"])
        nomes = m.nomes()
        i_y = nomes.index("yield")
        self.assertIn("f_open", nomes[:i_y])
        self.assertIn("f_read", nomes[:i_y])
        self.assertEqual(m.abertos, {})
        self.assertEqual(self.b7b[self.YIELD - XIP:self.YIELD - XIP + 2],
                         b"\x38\xb1")  # cbz r0, +4 (o yield so com r0 != 0)

    def test_123_guarda_view(self):
        m, view = self.aparelho(self.b7b)
        self.falsas(m)
        ext = m.le32(view + 0x30)
        m.escreve(ext + 0x210, b"\xAA" * 0x2000)
        for off in range(0, 0x2000, 0x400):
            _, novas = self.tipo6(m, view, off,
                                  bytes([off // 0x400]) * 0x400)
            self.assertEqual(m.erros, [], hex(off))
            self.assertEqual([c[0] for c in novas].count("img_set_src"),
                             1 if off == 0x1C00 else 0, hex(off))
        m.escreve(ext + 0x210, b"\xAA" * 0x2000)
        msg = self._msg_tipo6(m, 0, b"\xBB" * 0x400, 6)
        m.escreve(msg + 0xA, struct.pack("<H", 0x400))
        n0 = len(m.chamadas)
        m.chama(self.BLOB_XIP, (0, 0, 0, 6),
                salvos=[msg, view, msg + 0x14] + [0x11110000 + i
                                                  for i in range(5)])
        self.assertEqual(m.erros, [])
        self.assertEqual([c[0] for c in m.chamadas[n0:]], [])
        self.assertEqual(m.le(ext + 0x210, 0x400), b"\xAA" * 0x400)

    def test_124_pilha_b7b(self):
        _, _, _, c = self.carrega(self.b7b, self.ativo("capa_b_500.jpg"),
                                  pausa=True)
        usado = c["sp0"] - c["sp"]
        self.assertLessEqual(usado, 512, f"o B7b usa {usado} B de pilha")
        self.assertGreaterEqual(2048 - 152 - usado, 512,
                                f"sobram {2048 - 152 - usado} B")

    def test_122_callback_sem_trava(self):
        # O leitor 0xDAA404 chama f_read/f_lseek; a saida 0xDAA476 so
        # escreve pixels. O f_read adquire e solta a trava (0xD7533E /
        # 0xD75328) dentro da propria chamada.
        self.assertEqual(desvio(self.b6b, 0x17686A), 0x00D7533E)
        self.assertEqual(desvio(self.b6b, 0x17688A), 0x00D75328)
        self.assertEqual(desvio(self.b6b, 0x17693C), 0x00D75328)
        self.assertIn(bytes.fromhex("4af2054cc0f2da0ce047"),
                      self.blob[0x400:0x442])
        self.assertIn(bytes.fromhex("4af2774cc0f2da0ce047"),
                      self.blob[0x400:0x442])
        self.assertIn(bytes.fromhex("43f2356cc0f2c40ce047"),
                      self.blob[0x400:0x442])
        self.assertEqual(self.b7b[self.P_VIEW6:self.P_VIEW6 + 4],
                         F7.BRANCH_VIEW6)
        self.assertEqual(self.b7b[self.VIEW6:self.VIEW6 + self.VIEW6_LEN],
                         F7.VIEW6_COD)
        self.assertEqual(self.b7a[self.P_VIEW6:self.P_VIEW6 + 4],
                         b"\xb3\xf5\xe0\x5f")


class Mapa(Base):

    def test_17_mapa_e_receitas(self):
        import build as B
        self.assertEqual(B.MAPA["fab_capa_album.py"], (0x001A8000, 0x3000))
        self.assertEqual(B.AREA_FIM, 0x001AB000)
        # a ferramenta de bissecao NAO entra no MAPA: o tests/test_rc7.py
        # (protegido, C2) recusa qualquer lote do MAPA que cruze o lote da
        # RC7. O endereco do lote viaja na receita.
        self.assertNotIn("fab_diag_trava.py", B.MAPA)
        for n, (receita, _t, _o) in NIVEL.items():
            self.assertIn(receita, B.RECEITAS, n)
            passo = B.RECEITAS[receita][-1]
            self.assertEqual(passo[0], "fab_diag_trava.py", n)
            self.assertIn("--nivel", passo[1], n)
            self.assertIn("0x1a8000", passo[1], n)

    def test_19_nenhum_lote_cruza_o_da_rc7(self):
        import build as B
        for nome, (ini, tam) in B.MAPA.items():
            if nome == "fab_capa_album.py":
                continue
            self.assertFalse(ini < 0x1AB000 and 0x1A8000 < ini + tam, nome)

    def test_18_diag_fora_da_catraca(self):
        t = le(os.path.join(RAIZ, "tests/test_catraca.py")).decode()
        for n, (receita, _t, _o) in NIVEL.items():
            self.assertNotIn(receita, t, n)


if __name__ == "__main__":
    unittest.main(verbosity=2)
