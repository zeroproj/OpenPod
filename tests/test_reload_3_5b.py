#!/usr/bin/env python3
"""Testes de aceite da ficha 028b (Reload 3.5 Diag 2).

Rode a mao (o `tools/ci.sh` tambem roda, via `tests/test_reload_3_5.py`):

    python3 tests/test_reload_3_5b.py -v

Cobre:

  - a receita `reload_3.5b` e reproduzivel e o sha e o da imagem
    ba56813d...; o ultimo passo (fab_reload_3_5b.py) rodado de novo sobre
    a 3.5 da o mesmo byte a byte;
  - a 3.5 publicada continua reproduzivel byte a byte (o fonte do player
    mudou, mas o SDK `jogos35` nao);
  - o diff contra a 3.5 e SO o lote do SDK (0x1AB000..0x1FC000), sem
    tocar abaixo de 0xE000, no setor 0xD000 nem na PSMP;
  - os quatro ganchos continuam apontando para 0xDAB000/0xDAB200/
    0xDAB600/0xDAB700, e as caudas dos wrappers para 0xDAA014 (TITULO
    da capa) e 0xD2EEE8 (o `cmp r3,#3` da fabrica);
  - as premissas do fab_reload_3_5b.py recusam sha, gancho e SDK errados,
    e recusam `--out` igual a `--in`;
  - a `page_home_label_process` REAL (0xD2EEC4) com um chamador real:
    a mensagem tipo 3 de indice 1 (o titulo da faixa) preenche o titulo
    do cartao; a de indice 0 (o contador da fila) preenche o contador e
    NAO vira titulo; e o titulo antigo some quando o contador muda sem
    um titulo novo (nunca o titulo de outra faixa);
  - a `page_music_play_label_process` REAL (0xD32204): o indice 1 (o
    rotulo do titulo, `[view+4]`) preenche o titulo, o indice 0 (o
    rotulo do contador, `[view+0]`) preenche o contador e o indice 2
    (o caminho) nao preenche nada.
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
import fab_reload_3_5b as B  # noqa: E402
import capa_album_asm as A  # noqa: E402
import emu_rc7 as E  # noqa: E402
import fw_common as fw  # noqa: E402

BUILD = os.path.join(RAIZ, "tools/build.py")
WORK = os.path.join(RAIZ, "sdk/build/test_3_5b")
IMG35 = os.path.join(WORK, "reload_3_5.bin")
IMG35B = os.path.join(WORK, "reload_3_5b_a.bin")
IMG35B2 = os.path.join(WORK, "reload_3_5b_b.bin")
UP = os.path.join(RAIZ, "release/OpenPod-Reload-3.5-Diag2",
                  "OpenPod_OpenPodReload3.5Diag2.up")

SHA_35 = "f49c819534a12756ed1ee72fbda4444cf4dadd627c164c85faa48131d4b1d05d"
SHA_35B = "ba56813d9c15d53f27dc684b21b4e1a92b094f0fd9f0db2bb4e7e122289d40f8"
SDK_TAM = 14048
SHA_SDK35B = ("1f4c9eb03c0bd916270af5428ec9a3114d54723ea6abcee5df5a313e2"
              "5161114")
MENU_NOVO, HOME_NOVO = 0xDAB000, 0xDAB200
TITLE_NOVO, LABEL_NOVO = 0xDAB600, 0xDAB700
TIMER_NOVO = 0xDAB800

# o estado do cartao (fw_player_state_t na 3.5b): magic, title[64],
# version, shown_version, card, title_label, counter[16], title_fresh
OFF_MAGIC, OFF_TITLE = 0, 4
OFF_VERSION, OFF_SHOWN = 68, 72
OFF_CARD, OFF_LABEL = 76, 80
OFF_COUNTER, OFF_FRESH = 84, 100

EL_COUNTER, EL_TITLE, EL_PATH = 0, 1, 2


class Maquina35b(E.Maquina):
    """O emu_rc7 libera o lote da capa; aqui liberamos tambem o SDK novo e
    as duas funcoes de fabrica que os testes chamam de verdade."""

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


def sha_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def build(receita, saida):
    r = subprocess.run([sys.executable, BUILD, "--receita", receita,
                        "--saida", saida], cwd=RAIZ,
                       capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(f"build {receita} falhou:\n{r.stdout}{r.stderr}")


class Reload35b(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(WORK, exist_ok=True)
        if not os.path.exists(IMG35):
            build("reload_3.5", IMG35)
        build("reload_3.5b", IMG35B)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools",
                                                         "fab_reload_3_5b.py"),
                            "--in", IMG35, "--out", IMG35B2,
                            "--em", hex(B.LOTE_INI)], cwd=RAIZ,
                           capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(f"fab_reload_3_5b falhou:\n{r.stdout}{r.stderr}")
        with open(IMG35, "rb") as f:
            cls.o35 = f.read()
        with open(IMG35B, "rb") as f:
            cls.o35b = f.read()
        with open(IMG35B2, "rb") as f:
            cls.o35b2 = f.read()

    # ------------------------------------------------------------------ imagem

    def test_repro_e_sha(self):
        self.assertEqual(sha_file(IMG35), SHA_35)
        self.assertEqual(sha_file(IMG35B), SHA_35B)
        self.assertEqual(self.o35b, self.o35b2)

    def test_a_3_5_publicada_continua_igual(self):
        """O fonte do player mudou, mas o SDK `jogos35` nao: a 3.5 e a
        mesma imagem, byte a byte."""
        self.assertEqual(sha_file(IMG35), SHA_35)

    def test_diff_so_no_lote_do_sdk(self):
        dif = [i for i in range(len(self.o35)) if self.o35[i] != self.o35b[i]]
        self.assertTrue(dif)
        fora = [i for i in dif if not (B.LOTE_INI <= i < B.LOTE_FIM)]
        self.assertEqual(fora, [], "mudou fora do lote do SDK")
        self.assertTrue(all(i >= 0xE000 for i in dif))
        self.assertFalse(any(0xD000 <= i < 0xE000 for i in dif))
        self.assertFalse(any(i >= 0x1FC000 for i in dif))

    def test_ganchos(self):
        self.assertEqual(A.desvio(self.o35b, B.PATCH_MENU - B.XIP),
                         ("bl", MENU_NOVO))
        self.assertEqual(A.desvio(self.o35b, B.PATCH_HOME - B.XIP),
                         ("bl", HOME_NOVO))
        self.assertEqual(A.desvio(self.o35b, B.PATCH_TITLE - B.XIP),
                         ("b.w", TITLE_NOVO))
        self.assertEqual(A.desvio(self.o35b, B.PATCH_HOME_LABEL - B.XIP),
                         ("b.w", LABEL_NOVO))

    def test_tails(self):
        for ini, alvo in ((0xDAB600, 0xDAA014), (0xDAB700, 0xD2EEE8)):
            off = ini - B.XIP
            self.assertTrue(
                any(A.desvio(self.o35b, a) == ("b.w", alvo)
                    for a in range(off, off + 0x40, 2)),
                f"falta a cauda 0x{alvo:06X} no wrapper 0x{ini:06X}")

    def test_sdk(self):
        sdk = self.o35b[B.LOTE_INI:B.LOTE_INI + SDK_TAM]
        self.assertEqual(len(sdk), SDK_TAM)
        self.assertEqual(hashlib.sha256(sdk).hexdigest(), SHA_SDK35B)
        self.assertTrue(all(b == 0xFF
                            for b in self.o35b[B.LOTE_INI + SDK_TAM:B.LOTE_FIM]))

    def test_premissas_recusam(self):
        d = bytearray(self.o35)
        d[0x1000] ^= 1
        self.assertTrue(B.confere_premissas(bytes(d)))

        d = bytearray(self.o35)
        d[B.PATCH_TITLE - B.XIP] ^= 1
        self.assertTrue(B.confere_premissas(bytes(d)))

        d = bytearray(self.o35)
        d[B.LOTE_INI] ^= 1
        self.assertTrue(B.confere_premissas(bytes(d)))

        antes = sha_file(IMG35)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "tools",
                                                         "fab_reload_3_5b.py"),
                            "--in", IMG35, "--out", IMG35], cwd=RAIZ,
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(sha_file(IMG35), antes)

    def test_kit_diag2(self):
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
        self.assertEqual(payload[0x1A4F00:0x1A4F12], b"Reload 3.5 Diag 2\0")
        dif = [i for i in range(tam) if payload[i] != self.o35b[i]]
        permitido = ((0x1A4F00, 0x1A4F12), (0x10A59C, 0x10A5A0))
        fora = [i for i in dif if not any(a <= i < b for a, b in permitido)]
        self.assertEqual(fora, [], "o .up mudou fora do carimbo")
        self.assertTrue(dif)

    # ------------------------------------------------------- unicorn: a home

    def _estado(self, m, estado=0x00803000, node=0x00804000):
        """A lista de timers do LVGL de mentira, com o nosso timer."""
        m.escreve32(0x0081D2D4, 0x18)
        m.escreve32(0x0081D2D8, node)
        m.escreve32(0x0081D2DC, node)
        m.escreve32(node + 8, TIMER_NOVO | 1)
        m.escreve32(node + 0xC, estado)
        m.escreve32(node + 0x18, 0)
        m.escreve32(node + 0x1C, 0)
        m.escreve32(estado + OFF_MAGIC, 0x4F503335)
        return estado

    def _home(self, m, estado, msg):
        """Prepara a home como a fabrica: a view da home com um rotulo
        por icone (0x24 + 4*indice) e a mensagem tipo 3."""
        ctx, view = 0x00806000, 0x00807000
        m.escreve32(0x0081CE2C, ctx)
        m.escreve32(ctx + 0xA0, view)
        for i in range(9):                       # os 9 rotulos dos icones
            m.escreve32(view + 0x24 + 4 * i, 0x00809000 + 4 * i)
        m.escreve(msg + 6, struct.pack("<H", 3))     # o tipo da mensagem
        m.escreve(msg + 0x14, b"Musica\0")
        return estado

    def _chama_home(self, m, msg, salvos):
        """Chama a page_home_label_process REAL com um chamador real."""
        return chama_stub(m, 0xD2EEC4, (msg, 0, 0, 0), salvos=salvos)

    def test_home_o_titulo(self):
        """O indice 1 da mensagem e o titulo da faixa."""
        m = Maquina35b(self.o35b)
        estado = self._estado(m)
        msg = 0x00808000
        self._home(m, estado, msg)
        m.escreve(msg + 4, struct.pack("<H", EL_TITLE))
        m.escreve(0x00823EB0, b"\x03")
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_TITLE, 7), b"Musica\0")
        self.assertEqual(m.le(estado + OFF_COUNTER, 2), b"\0\0")
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
        self.assertEqual(m.r(E.UC_ARM_REG_SP),
                         E.PILHA[0] + E.PILHA[1] - 0x100)
        self.assertEqual([m.r(x) for x in E.SALVOS], salvos)

    def test_home_o_contador_nao_e_titulo(self):
        """O indice 0 e o contador da fila: ele nao vira titulo."""
        m = Maquina35b(self.o35b)
        estado = self._estado(m)
        msg = 0x00808000
        self._home(m, estado, msg)
        m.escreve(msg + 4, struct.pack("<H", EL_COUNTER))
        m.escreve(msg + 0x14, b"31/165\0")
        m.escreve(0x00823EB0, b"\x03")
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_COUNTER, 7), b"31/165\0")
        self.assertEqual(m.le(estado + OFF_TITLE, 1), b"\0")
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
        self.assertEqual([m.r(x) for x in E.SALVOS], salvos)

    def test_home_o_caminho_e_ignorado(self):
        """O indice 2 (o caminho do arquivo) nao preenche nada."""
        m = Maquina35b(self.o35b)
        estado = self._estado(m)
        msg = 0x00808000
        self._home(m, estado, msg)
        m.escreve(msg + 4, struct.pack("<H", EL_PATH))
        m.escreve(msg + 0x14, b"/Musica.mp3\0")
        m.escreve(0x00823EB0, b"\x03")
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_TITLE, 1), b"\0")
        self.assertEqual(m.le(estado + OFF_COUNTER, 1), b"\0")
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)

    def test_home_o_titulo_novo_sobrevive_ao_contador(self):
        """A ordem da fabrica e titulo (1) e depois contador (0): o titulo
        e o da faixa que o contador conta."""
        m = Maquina35b(self.o35b)
        estado = self._estado(m)
        msg = 0x00808000
        self._home(m, estado, msg)
        m.escreve(0x00823EB0, b"\x03")
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]

        m.escreve(msg + 4, struct.pack("<H", EL_TITLE))
        m.escreve(msg + 0x14, b"Musica\0")
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_TITLE, 7), b"Musica\0")

        m.escreve(msg + 4, struct.pack("<H", EL_COUNTER))
        m.escreve(msg + 0x14, b"31/165\0")
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_COUNTER, 7), b"31/165\0")
        self.assertEqual(m.le(estado + OFF_TITLE, 7), b"Musica\0")
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)

    def test_home_contador_sem_titulo_descarta_o_antigo(self):
        """Troca de faixa sem o titulo: o titulo antigo e de outra faixa e
        some (o cartao mostra "Nada tocando")."""
        m = Maquina35b(self.o35b)
        estado = self._estado(m)
        msg = 0x00808000
        self._home(m, estado, msg)
        m.escreve(0x00823EB0, b"\x03")
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]

        m.escreve(msg + 4, struct.pack("<H", EL_TITLE))
        m.escreve(msg + 0x14, b"Musica\0")
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.le(estado + OFF_TITLE, 7), b"Musica\0")

        # a proxima faixa: titulo e contador, como a fabrica manda
        m.escreve(msg + 4, struct.pack("<H", EL_TITLE))
        m.escreve(msg + 0x14, b"Musica2\0")
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.le(estado + OFF_TITLE, 8), b"Musica2\0")
        m.escreve(msg + 4, struct.pack("<H", EL_COUNTER))
        m.escreve(msg + 0x14, b"31/165\0")
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.le(estado + OFF_COUNTER, 7), b"31/165\0")
        self.assertEqual(m.le(estado + OFF_TITLE, 8), b"Musica2\0")

        # a faixa seguinte: so o contador chega (o titulo foi perdido no
        # ring): o titulo que temos e de outra faixa e some
        m.escreve(msg + 4, struct.pack("<H", EL_COUNTER))
        m.escreve(msg + 0x14, b"32/165\0")
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_COUNTER, 7), b"32/165\0")
        self.assertEqual(m.le(estado + OFF_TITLE, 1), b"\0")
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)

    def test_home_a_ordem_da_abertura_tambem_valida(self):
        """Na abertura da pagina a fabrica manda o contador (0) e DEPOIS o
        titulo (1): o titulo tambem fica."""
        m = Maquina35b(self.o35b)
        estado = self._estado(m)
        msg = 0x00808000
        self._home(m, estado, msg)
        m.escreve(0x00823EB0, b"\x03")
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]

        m.escreve(msg + 4, struct.pack("<H", EL_COUNTER))
        m.escreve(msg + 0x14, b"31/165\0")
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.erros, [])

        m.escreve(msg + 4, struct.pack("<H", EL_TITLE))
        m.escreve(msg + 0x14, b"Musica\0")
        self._chama_home(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_COUNTER, 7), b"31/165\0")
        self.assertEqual(m.le(estado + OFF_TITLE, 7), b"Musica\0")
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)

    # ----------------------------------------------------- unicorn: o player

    def _player(self, m, msg):
        """A view da pagina 4: [view+0] contador, [view+4] titulo,
        [view+8] o rotulo do caminho."""
        ctx, view = 0x00806000, 0x00807000
        m.escreve32(0x0081CE2C, ctx)
        m.escreve32(ctx + 0xAC, view)
        m.escreve32(view + 0, 0x50000100)        # o contador
        m.escreve32(view + 4, 0x50000200)        # o titulo
        m.escreve32(view + 8, 0x50000300)        # o caminho
        m.escreve(msg + 6, struct.pack("<H", 3))
        m.escreve32(msg + 0x10, 1)               # o comprimento do texto
        m.escreve(msg + 0x14, b"Musica\0")
        m.escreve(0x00823EB0, b"\x03")

    def _chama_player(self, m, msg, salvos):
        return chama_stub(m, 0xD32204, (msg, 0, 0, 0), salvos=salvos)

    def test_player_o_rotulo_do_titulo(self):
        """O indice 1 escreve no rotulo do titulo ([view+4]) e o cartao
        recebe o texto."""
        m = Maquina35b(self.o35b)
        estado = self._estado(m)
        msg = 0x00808000
        self._player(m, msg)
        m.escreve(msg + 4, struct.pack("<H", EL_TITLE))
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
        self._chama_player(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_TITLE, 7), b"Musica\0")
        self.assertEqual(m.le(estado + OFF_COUNTER, 1), b"\0")
        self.assertIn(("label_set_text", 0x50000200, msg + 0x14), m.chamadas)
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
        self.assertEqual(m.r(E.UC_ARM_REG_SP),
                         E.PILHA[0] + E.PILHA[1] - 0x100)
        self.assertEqual([m.r(x) for x in E.SALVOS], salvos)

    def test_player_o_rotulo_do_contador(self):
        """O indice 0 escreve no rotulo do contador ([view+0]): o cartao
        guarda o contador, nao um titulo."""
        m = Maquina35b(self.o35b)
        estado = self._estado(m)
        msg = 0x00808000
        self._player(m, msg)
        m.escreve(msg + 4, struct.pack("<H", EL_COUNTER))
        m.escreve(msg + 0x14, b"31/165\0")
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
        self._chama_player(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_COUNTER, 7), b"31/165\0")
        self.assertEqual(m.le(estado + OFF_TITLE, 1), b"\0")
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)

    def test_player_o_caminho_nao_preenche_nada(self):
        """O indice 2 (o caminho) nao vira titulo nem contador."""
        m = Maquina35b(self.o35b)
        estado = self._estado(m)
        msg = 0x00808000
        self._player(m, msg)
        m.escreve(msg + 4, struct.pack("<H", EL_PATH))
        m.escreve(msg + 0x14, b"/Musica.mp3\0")
        m.falsas = {0x2B0: lambda mq: 0}
        salvos = [0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB]
        self._chama_player(m, msg, salvos)
        self.assertEqual(m.erros, [])
        self.assertEqual(m.le(estado + OFF_TITLE, 1), b"\0")
        self.assertEqual(m.le(estado + OFF_COUNTER, 1), b"\0")
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)

    def test_player_a_capa_continua(self):
        """A cauda do gancho do titulo e o TITULO da capa (0xDAA014): a
        capa do album continua carregando."""
        import test_reload_3_3 as T33
        t = T33.Reload33()
        m, chamadas, salvos = t._roda_wrapper(self.o35b)
        self.assertEqual(m.erros, [])
        self.assertEqual(chamadas, ["yield"])
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
        self.assertEqual(m.r(E.UC_ARM_REG_SP),
                         E.PILHA[0] + E.PILHA[1] - 0x100)
        self.assertEqual([m.r(x) for x in E.SALVOS], salvos)

        m, chamadas, salvos = t._roda_envia(self.o35b)
        self.assertEqual(m.erros, [])
        self.assertNotIn("ring_free", chamadas)
        self.assertEqual([c for c in chamadas if isinstance(c, tuple)],
                         [("send", 6)] * 8)
        self.assertEqual(m.r(E.UC_ARM_REG_PC), E.FIM)
        self.assertEqual([m.r(x) for x in E.SALVOS], salvos)


if __name__ == "__main__":
    unittest.main()
