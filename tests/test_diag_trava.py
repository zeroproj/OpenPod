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
    r"""O degrau B3 da ficha 011 (o caminho sem o get_path na ViewTask).

    A MainTask captura o caminho na rajada do play (0x001088D8), o guarda
    em 0x00DAAB00; o TITULO le esse global (0x001AA144) em vez de chamar o
    get_path, confere o `0:\`/`0:/` e mostra o cinza."""

    RECEITA = "reload_1.0_rc7_diag_b3"
    BLOB = 0x1AAA00
    BLOB_XIP = 0x00DAAA00
    LE = 0x00DAAA40
    GLOBAL = 0x1AAB00
    GLOBAL_XIP = 0x00DAAB00
    CAPTURA = 0x1088D8
    GET = 0x1AA144
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
        regioes = [(self.CAPTURA, 4), (self.GET, 10), (self.CARREGA, 4),
                   (self.BLOB, len(self.blob))]
        for i in dif:
            self.assertTrue(any(o <= i < o + t for o, t in regioes),
                            f"byte fora do patch: 0x{i:06X}")
            self.assertGreaterEqual(i, 0x00E000)
            self.assertFalse(0xD000 <= i < 0xE000)
            self.assertLess(i, 0x1FC000)
        self.assertEqual(self.b3[self.GET + 4:self.GET + 10], b"\x00\xbf" * 3)
        self.assertEqual(self.b3[self.CARREGA:self.CARREGA + 4],
                         b"\x00\x20\x00\xbf")
        self.assertEqual(self.b3[self.BLOB:self.BLOB + len(self.blob)],
                         self.blob)

    def test_43_decodificacao(self):
        self.assertEqual(desvio(self.b3, self.CAPTURA), self.BLOB_XIP)
        self.assertEqual(desvio(self.b3, self.GET), self.LE)
        self.assertEqual(valor_carregado(self.b3, self.BLOB + 0x40),
                         self.GLOBAL_XIP)
        self.assertEqual(valor_carregado(self.b3, self.BLOB + 0x26),
                         0x00D084F9)

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
        d[self.BLOB] ^= 0xFF
        self.assertTrue(any("virgem" in e
                            for e in F3.confere_premissas(d, self.blob)))

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
        return m, view

    def titulo_b3(self, m, view, path):
        ctx = m.le32(view + 0x30)
        m.escreve(self.GLOBAL_XIP, path + b"\0")
        m.escreve(ctx + 0x10, b"\0" * 0x100)
        m.escreve(ctx + 0x110, b"\0" * 0x100)
        txt = m.aloca(16, registra=False)
        m.escreve(txt, b"titulo\0")
        n0 = len(m.chamadas)
        m.chama(TITULO, (ROT_TIT, txt))
        self.assertEqual(m.erros, [])
        return ctx, m.chamadas[n0:]

    def test_46_emulacao_guarda_path(self):
        m = E.Maquina(self.b3)
        path = m.aloca(64, registra=False)
        m.escreve(path, b"0:/A/B.mp3\0")
        vistos = []

        def fake(mq):
            vistos.append(mq.r(E.UC_ARM_REG_R0))
            return 0

        m.falsas[0x00D084F8] = fake
        m.escreve(self.GLOBAL_XIP, b"\xff" * 0x100)
        m.chama(self.BLOB_XIP, (path,))
        self.assertEqual(m.erros, [])
        self.assertEqual(m.cstr(self.GLOBAL_XIP), b"0:/A/B.mp3")
        self.assertEqual(vistos, [path])

    def test_47_emulacao_le_global(self):
        m = E.Maquina(self.b3)
        ctx = m.aloca(0x220, registra=False)
        for path, ok in ((b"0:/A.mp3", 1), (b"0:\\A.mp3", 1),
                         (b"lixo", 0), (b"", 0)):
            m.escreve(self.GLOBAL_XIP, path + b"\0")
            m.escreve(ctx + 0x110, b"\xAA" * 0x100)
            salvos = [0x11110000 + i for i in range(8)]
            salvos[3] = ctx                      # r7 = o contexto
            r = m.chama(self.LE, (), salvos=salvos)
            self.assertEqual(m.erros, [], path)
            self.assertEqual(r, ok, path)
            self.assertEqual(m.cstr(ctx + 0x110), path, path)

    def test_48_emulacao_titulo(self):
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
            self.assertEqual(set(srcs), {self.PH_DSC}, path)
        # caminho invalido: cinza, e o caminho guardado fica vazio
        ctx, novas = self.titulo_b3(m, view, b"lixo")
        self.assertEqual([c[0] for c in novas], ["label_set_text", "img_set_src"])
        self.assertEqual(m.cstr(ctx + 0x10), b"")
        self.assertEqual(m.cstr(ctx + 0x110), b"lixo")

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
