#!/usr/bin/env python3
"""
test_diag_trava.py — as tres imagens de BISSECAO da ficha 008 (a RC7 trava
ao tocar).

NAO e um teste protegido: o `tools/ci.sh` roda so a lista fixa dele (esta
ficha nao pode mexer em `tests/PROTEGIDOS.sha256`). Rodado a mao:

    python3 tests/test_diag_trava.py

O QUE ESTE TESTE COBRE

    - a RC7 exata (sha 3af97713...) e as tres receitas de bissecao;
    - build REPRODUZIVEL: duas execucoes da mesma receita, o mesmo sha;
    - o diff RC7 -> diag e EXATAMENTE o esperado: A = 4 bytes em 0x1AA014,
      B = 2 bytes, C = 2 bytes, e nada mais em lugar nenhum;
    - a decodificacao de volta: o `b.w` novo da entrada TITULO aponta para
      o lv_label_set_text da fabrica (0x00D5ED94) e os 2 bytes novos dos
      niveis B e C sao `movs r0, #1`;
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
}
# o que fica no lugar, byte a byte (o nivel A e conferido pela decodificacao
# do b.w, que depende do endereco de execucao)
ESPERADO = {
    "a": None,
    "b": b"\x00\x20\x00\xbf",     # movs r0, #0 + nop
    "c": b"\x01\x20",             # movs r0, #1
}
# o par movw/movt da chamada externa do nivel C e o alvo
CHAMADA = {"c": (0x1AA316, 0x00D10B21)}
# o `carrega_capa` (nivel B): o prologo unico e o `bl` que o chama
CARREGA_CAPA = (0x1AA256, 0x1AA188)


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
        """RC7 -> diag: so os bytes do patch, e nada mais."""
        for n, (_receita, tam, offs) in NIVEL.items():
            img = self.diags[n][2]
            dif = [i for i in range(len(img)) if img[i] != self.rc7[i]]
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
            dif = [i for i in range(len(img)) if img[i] != self.rc7[i]]
            for i in dif:
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

    def test_6_aceita_a_rc7_exata(self):
        for n in NIVEL:
            rc, criou, intacta = self.roda(self.rc7, n)
            self.assertEqual((rc, criou), (0, True), n)
            self.assertTrue(intacta, n)

    def test_7_dry_run_nao_grava(self):
        for n in NIVEL:
            rc, criou, intacta = self.roda(self.rc7, n, ["--dry-run"])
            self.assertEqual((rc, criou), (0, False), n)
            self.assertTrue(intacta, n)

    def test_8_recusa_entradas_erradas(self):
        casos = {
            "rc6": self.rc6,
            "rc6_carimbada": self.rc6_carimbada(),
            "truncada": self.rc7[:0x100000],
        }
        b = bytearray(self.rc7)
        b[TABELA] ^= 0xFF                      # a tabela do lote mexida
        casos["lote_mexido"] = bytes(b)
        b = bytearray(self.rc7)
        b[0x1AA316 + 2] ^= 0x01                # o movw do jd_prepare mexido
        casos["chamada_mexida"] = bytes(b)
        b = bytearray(self.rc7)
        b[CARREGA_CAPA[0] + 4] ^= 0x01        # o sub sp,#12 do carrega_capa
        casos["prologo_mexido"] = bytes(b)
        b = bytearray(self.rc7)
        b[CARREGA_CAPA[1]] ^= 0xFF             # o bl do carrega_capa mexido
        casos["bl_mexido"] = bytes(b)
        for nome, entrada in casos.items():
            for n in NIVEL:
                rc, criou, intacta = self.roda(entrada, n)
                self.assertNotEqual(rc, 0, f"{n} aceitou {nome}")
                self.assertFalse(criou, f"{n} criou saida com {nome}")
                self.assertTrue(intacta, f"{n} mexeu na entrada ({nome})")

    def test_9_saida_igual_ou_link(self):
        for n in NIVEL:
            for tipo in ("mesmo", "symlink", "hardlink"):
                tmp = tempfile.mkdtemp(prefix="openpod_diag008l_")
                src, dst = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
                with open(src, "wb") as fh:
                    fh.write(self.rc7)
                if tipo == "mesmo":
                    dst = src
                else:
                    (os.symlink if tipo == "symlink" else os.link)(src, dst)
                r = subprocess.run([sys.executable,
                                    os.path.join(RAIZ, "tools/fab_diag_trava.py"),
                                    "--in", src, "--out", dst, "--nivel", n],
                                   capture_output=True, cwd=RAIZ)
                self.assertNotEqual(r.returncode, 0, f"{n} {tipo}")
                self.assertEqual(le(src), self.rc7, f"{n} {tipo}")

    def test_10_reprocessar_uma_saida(self):
        for n in NIVEL:
            rc, criou, intacta = self.roda(self.diags[n][2], n)
            self.assertNotEqual(rc, 0, f"{n} aceitou reprocessar")
            self.assertFalse(criou, f"{n} criou saida reprocessando")
            self.assertTrue(intacta, n)

    def test_11_em_errado_e_recusado(self):
        for n in NIVEL:
            rc, criou, _ = self.roda(self.rc7, n, ["--em", "0x1A9000"])
            self.assertNotEqual(rc, 0, n)
            self.assertFalse(criou, n)


class Premissas(Base):
    """As premissas da ferramenta, uma por uma (branco sobre preto)."""

    def test_12_rc7_passa_em_todas(self):
        for n in NIVEL:
            self.assertEqual(F.confere_premissas(bytearray(self.rc7), n), [], n)

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
            off, t, novos = G.bytes_do_patch(self.rc7, n)
            self.assertEqual(off, offs[0], n)
            self.assertEqual(t, tam, n)
            if ESPERADO[n] is not None:
                self.assertEqual(novos, ESPERADO[n], n)
        # o detector nao aceita meia-palavra qualquer
        self.assertFalse(G.e_blx(0x2800))
        self.assertFalse(G.e_mov(0x2800, 0x0000, 0xF240))
        self.assertTrue(G.e_blx(0x47E0))
        self.assertTrue(G.e_mov(0xF247, 0x7CCD, 0xF240))


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
