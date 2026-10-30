#!/usr/bin/env python3
# NÃO ALTERAR sem o arquiteto. O hash deste arquivo é conferido por tools/ci.sh
# (tests/PROTEGIDOS.sha256). Ficha: docs/tarefas/007-rc7-capa-album.md
"""
emu_rc7.py — arnês de emulação (unicorn) das rotinas da RC7 sobre a imagem.

O código novo da área livre roda DE VERDADE (Thumb-2, unicorn), e o TJpgDec
da fábrica (jd_prepare 0xD10B20 / jd_decomp 0xD11090) também. Só as funções
de fora que a ficha permite chamar são trocadas por stubs em Python (heap,
FatFs, caminho da faixa, LVGL, memset), que registram cada chamada.

Qualquer execução fora de: lote da RC7, faixa do TJpgDec, stubs → erro.
Qualquer acesso a memória não mapeada (inclusive aos objetos LVGL falsos,
que NÃO são mapeados) → erro.

USO (pelos testes)
    from emu_rc7 import Maquina, referencia, monta_mp3, frame_id3, tag_id3
    m = Maquina(imagem_bytes); m.arquivos[b"0:/a.mp3"] = dados; ...

DEPENDÊNCIAS
    Python 3 + unicorn (pip install --user unicorn). Não abre o USB.

LIMITAÇÕES
    Stubs de FatFs só leem (mode deve ser FA_READ=1). Tempo limite por
    chamada: 60 s.
"""

import struct

from unicorn import (Uc, UcError, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_BLOCK,
                     UC_HOOK_MEM_INVALID)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                               UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
                               UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                               UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

XIP = 0x00C00000
LOTE_XIP = (0x00DA8000, 0x00DAB000)          # lote da RC7 (arquivo 0x1A8000..0x1AB000)
TJPGDEC = (0x00D10900, 0x00D12000)           # TJpgDec da fábrica (traçado: 0xD10906..0xD11E60)
RAM = (0x00800000, 0x00040000)               # RAM do aparelho (globais da fábrica)
BAIXA = (0x00000000, 0x00010000)             # ROM baixa (memset 0xBAA)
HEAP = (0x20000000, 0x00100000)
PILHA = (0x30000000, 0x00010000)
FIM = 0x3F000000                             # endereço de parada (mapeado, nunca executado)
FALSAS = 0x3E000000                          # funções falsas da referência
OBJ = 0x50000000                             # objetos LVGL falsos: NÃO mapeados

PAGINAS = 0x0081CE2C                         # [PAGINAS] -> struct; +0xAC = view da página 4
AUDIO = 0x0081BC84                           # +0 (byte) origem, +0x20 índice da faixa

STUBS = {
    0x00CF7840: "calloc", 0x00CF780C: "malloc", 0x00CF7884: "free",
    0x00CFEFC4: "get_path",
    0x00D777CC: "f_open", 0x00D76854: "f_read", 0x00D76C0A: "f_lseek", 0x00D77C9C: "f_close",
    0x00D5D850: "img_create", 0x00D5D868: "img_set_src", 0x00D4A3A2: "obj_align",
    0x00D47064: "add_event_cb", 0x00D5ED94: "label_set_text",
    0x00000BAA: "memset",
}
SALVOS = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
          UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
ARGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)


class Maquina:
    """Uma instância = um aparelho emulado com a imagem dada."""

    def __init__(self, imagem):
        assert len(imagem) == 0x200000
        u = self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(XIP, 0x200000)
        u.mem_write(XIP, bytes(imagem))
        for ini, tam in (RAM, BAIXA, HEAP, PILHA):
            u.mem_map(ini, tam)
        u.mem_map(FIM & ~0xFFF, 0x1000)
        u.mem_map(FALSAS, 0x1000)
        u.mem_write(FALSAS, b"\x70\x47" * 0x800)       # bx lr
        self.topo_heap = HEAP[0]
        self.vivos = {}          # ptr -> tamanho
        self.vivos_bytes = 0
        self.pico = 0
        self.nega_aloc = None    # função(tamanho) -> True para falhar a alocação
        self.caminho = None      # bytes devolvidos pelo get_path (None = falha)
        self.arquivos = {}       # caminho (bytes) -> conteúdo
        self.abertos = {}        # FIL* -> [dados, pos]
        self.chamadas = []       # (nome, args...)
        self.erros = []
        self.falsas = {}         # endereço -> função python (referência)
        self.n_obj = 0
        self.nega_obj = set()    # índices de img_create que devolvem 0
        # o lote da RC7 e o TJpgDec rodam sem gancho (são os permitidos); o resto
        # da flash, a ROM baixa e as funções falsas passam por _bloco
        u.hook_add(UC_HOOK_BLOCK, self._bloco, begin=XIP, end=TJPGDEC[0] - 1)
        u.hook_add(UC_HOOK_BLOCK, self._bloco, begin=TJPGDEC[1], end=LOTE_XIP[0] - 1)
        u.hook_add(UC_HOOK_BLOCK, self._bloco, begin=LOTE_XIP[1], end=XIP + 0x200000 - 1)
        u.hook_add(UC_HOOK_BLOCK, self._bloco, begin=BAIXA[0], end=BAIXA[0] + BAIXA[1] - 1)
        u.hook_add(UC_HOOK_BLOCK, self._bloco, begin=FALSAS, end=FALSAS + 0xFFF)
        u.hook_add(UC_HOOK_MEM_INVALID, self._invalido)

    # ------------------------------------------------------------ utilitários
    def r(self, reg):
        return self.u.reg_read(reg)

    def le(self, a, n):
        return bytes(self.u.mem_read(a, n))

    def le32(self, a):
        return struct.unpack("<I", self.le(a, 4))[0]

    def escreve(self, a, b):
        self.u.mem_write(a, bytes(b))

    def escreve32(self, a, v):
        self.escreve(a, struct.pack("<I", v & 0xFFFFFFFF))

    def cstr(self, a, maximo=512):
        b = self.le(a, maximo)
        return b.split(b"\0", 1)[0]

    def aloca(self, tam, zera=True, registra=True):
        if registra and self.nega_aloc and self.nega_aloc(tam):
            return 0
        p = (self.topo_heap + 7) & ~7
        self.topo_heap = p + tam + 16
        assert self.topo_heap < HEAP[0] + HEAP[1], "heap do arnês esgotado"
        self.escreve(p, (b"\0" if zera else b"\xA5") * tam)
        if registra:
            self.vivos[p] = tam
            self.vivos_bytes += tam
            self.pico = max(self.pico, self.vivos_bytes)
        return p

    def objeto(self):
        self.n_obj += 1
        return OBJ + 0x100 * self.n_obj

    def nomes(self):
        return [c[0] for c in self.chamadas]

    def de(self, nome):
        return [c for c in self.chamadas if c[0] == nome]

    # ------------------------------------------------------------ ganchos
    def _invalido(self, uc, acesso, end, tam, val, ud):
        self.erros.append(f"acesso invalido a 0x{end:08X} (tipo {acesso}) pc=0x{self.r(UC_ARM_REG_PC):08X}")
        return False

    def _retorna(self, r0=None):
        if r0 is not None:
            self.u.reg_write(UC_ARM_REG_R0, r0 & 0xFFFFFFFF)
        self.u.reg_write(UC_ARM_REG_PC, self.r(UC_ARM_REG_LR) | 1)

    def _bloco(self, uc, a, tam, ud):
        if a in self.falsas:
            self._retorna(self.falsas[a](self))
            return
        if TJPGDEC[0] <= a < TJPGDEC[1]:
            return
        nome = STUBS.get(a)
        if nome is None:
            self.erros.append(f"executou fora do permitido: 0x{a:08X}")
            uc.emu_stop()
            return
        r0, r1, r2, r3 = (self.r(x) for x in ARGS)
        self._retorna(getattr(self, "_" + nome)(r0, r1, r2, r3))

    # ------------------------------------------------------------ stubs
    def _calloc(self, n, tam, *_):
        self.chamadas.append(("calloc", n, tam))
        return self.aloca(n * tam)

    def _malloc(self, tam, *_):
        self.chamadas.append(("malloc", tam))
        return self.aloca(tam, zera=False)

    def _free(self, p, *_):
        self.chamadas.append(("free", p))
        if p == 0:
            return 0
        if p not in self.vivos:
            self.erros.append(f"free de ponteiro nao alocado/duplo: 0x{p:08X}")
            return 0
        tam = self.vivos.pop(p)
        self.vivos_bytes -= tam
        self.escreve(p, b"\xDD" * tam)
        return 0

    def _get_path(self, origem, indice, buf, *_):
        self.chamadas.append(("get_path", origem, indice, buf))
        if self.caminho is None:
            return 0
        c = self.caminho[:0xFF]
        self.escreve(buf, c + b"\0" * (0xFF - len(c)))      # strncpy(buf, p, 0xFF)
        return 1

    def _f_open(self, fil, caminho, modo, *_):
        c = self.cstr(caminho)
        self.chamadas.append(("f_open", fil, c, modo))
        if modo != 1:
            self.erros.append(f"f_open com modo {modo} (so leitura = 1)")
            return 7
        if fil in self.abertos:
            self.erros.append(f"f_open sobre FIL ja aberto 0x{fil:08X}")
        if c not in self.arquivos:
            return 4                                        # FR_NO_FILE
        self.abertos[fil] = [self.arquivos[c], 0]
        self._fptr(fil)
        return 0

    def _fptr(self, fil):
        self.escreve(fil + 0x38, struct.pack("<Q", self.abertos[fil][1]))

    def _f_read(self, fil, buf, n, pbr):
        self.chamadas.append(("f_read", fil, buf, n))
        if fil not in self.abertos:
            self.erros.append(f"f_read em FIL nao aberto 0x{fil:08X}")
            return 9
        dados, pos = self.abertos[fil]
        d = dados[pos:pos + n]
        if d:
            self.escreve(buf, d)
        self.abertos[fil][1] = pos + len(d)
        self._fptr(fil)
        self.escreve32(pbr, len(d))
        return 0

    def _f_lseek(self, fil, _r1, lo, hi):
        ofs = lo | (hi << 32)                               # FSIZE_t de 64 bits em r2:r3
        self.chamadas.append(("f_lseek", fil, ofs))
        if fil not in self.abertos:
            self.erros.append(f"f_lseek em FIL nao aberto 0x{fil:08X}")
            return 9
        self.abertos[fil][1] = min(ofs, len(self.abertos[fil][0]))
        self._fptr(fil)
        return 0

    def _f_close(self, fil, *_):
        self.chamadas.append(("f_close", fil))
        if self.abertos.pop(fil, None) is None:
            self.erros.append(f"f_close em FIL nao aberto 0x{fil:08X}")
            return 9
        return 0

    def _img_create(self, pai, *_):
        k = len(self.de("img_create"))
        o = 0 if k in self.nega_obj else self.objeto()
        self.chamadas.append(("img_create", pai, o))
        return o

    def _img_set_src(self, obj, src, *_):
        self.chamadas.append(("img_set_src", obj, src))
        return 0

    def _obj_align(self, obj, alinh, x, y):
        s16 = lambda v: ((v & 0xFFFF) ^ 0x8000) - 0x8000
        self.chamadas.append(("obj_align", obj, alinh & 0xFF, s16(x), s16(y)))
        return 0

    def _add_event_cb(self, obj, cb, filtro, ud):
        self.chamadas.append(("add_event_cb", obj, cb, filtro & 0xFF, ud))
        return self.aloca(12, registra=False)

    def _label_set_text(self, obj, txt, *_):
        self.chamadas.append(("label_set_text", obj, txt))
        return 0

    def _memset(self, p, v, n, *_):
        self.escreve(p, bytes([v & 0xFF]) * n)
        return p

    # ------------------------------------------------------------ chamada
    def chama(self, alvo, regs=(), salvos=None, tempo=60):
        """Chama `alvo` (endereço XIP, Thumb) com r0..r3 = regs.
        `salvos` (opcional) = valores de r4..r11; conferidos na volta."""
        u = self.u
        for reg, v in zip(ARGS, regs):
            u.reg_write(reg, v & 0xFFFFFFFF)
        salvos = list(salvos or [0x11110000 + i for i in range(8)])
        for reg, v in zip(SALVOS, salvos):
            u.reg_write(reg, v)
        sp = PILHA[0] + PILHA[1] - 0x100
        u.reg_write(UC_ARM_REG_SP, sp)
        u.reg_write(UC_ARM_REG_LR, FIM | 1)
        try:
            u.emu_start(alvo | 1, FIM, timeout=tempo * 1_000_000)
        except UcError as e:
            self.erros.append(f"unicorn: {e} pc=0x{self.r(UC_ARM_REG_PC):08X}")
        if self.r(UC_ARM_REG_PC) != FIM:
            self.erros.append(f"nao voltou (pc=0x{self.r(UC_ARM_REG_PC):08X}): laco, trava ou estouro de tempo")
        if self.r(UC_ARM_REG_SP) != sp:
            self.erros.append("pilha desbalanceada")
        if [self.r(x) for x in SALVOS] != salvos:
            self.erros.append("r4..r11 nao preservados")
        return self.r(UC_ARM_REG_R0)


# ------------------------------------------------------------------ referência
def escala_de(w, h):
    """Maior s em 0..3 com (w>>s) >= 64 e (h>>s) >= 64; None se < 64."""
    if w < 64 or h < 64:
        return None
    return max(s for s in range(4) if (w >> s) >= 64 and (h >> s) >= 64)


def decodifica_fabrica(original, jpeg):
    """Decodifica com o TJpgDec da FÁBRICA (emulado) na escala da ficha.
    Devolve (w, h, s, img) com img = {(x, y): rgb565}; img None se falhar."""
    m = Maquina(original)
    jd, pool = m.aloca(0x118, registra=False), m.aloca(0xE00, registra=False)
    pos, img = [0], {}

    def entra(mq):
        buf, n = mq.r(UC_ARM_REG_R1), mq.r(UC_ARM_REG_R2)
        d = jpeg[pos[0]:pos[0] + n]
        pos[0] += len(d)
        if buf and d:
            mq.escreve(buf, d)
        return len(d)

    def sai(mq):
        bm, rr = mq.r(UC_ARM_REG_R1), mq.r(UC_ARM_REG_R2)
        l, r, t, b = struct.unpack("<4H", mq.le(rr, 8))
        px = mq.le(bm, (r - l + 1) * (b - t + 1) * 2)
        k = 0
        for y in range(t, b + 1):
            for x in range(l, r + 1):
                img[(x, y)] = struct.unpack_from("<H", px, k)[0]
                k += 2
        return 1

    m.falsas = {FALSAS: entra, FALSAS + 2: sai}
    if m.chama(0x00D10B20, (jd, FALSAS | 1, pool, 0xE00)) != 0 or m.erros:
        return None, None, None, None
    w, h = struct.unpack("<HH", m.le(jd + 0x1C, 4))
    s = escala_de(w, h)
    if s is None:
        return w, h, None, None
    if m.chama(0x00D11090, (jd, (FALSAS + 2) | 1, s)) != 0 or m.erros:
        return w, h, s, None
    return w, h, s, img


def referencia(original, jpeg):
    """Os 8192 bytes esperados da capa (64x64, RGB565 com bytes trocados):
    pixel (ox, oy) = imagem reduzida (ox*W//64, oy*H//64), W = w>>s, H = h>>s."""
    w, h, s, img = decodifica_fabrica(original, jpeg)
    assert img is not None, "referencia: o TJpgDec da fabrica nao decodificou"
    W, H = w >> s, h >> s
    out = bytearray()
    for oy in range(64):
        for ox in range(64):
            out += struct.pack(">H", img[(ox * W // 64, oy * H // 64)])
    return bytes(out)


# ------------------------------------------------------------------ ID3 / MP3
def synchsafe(n):
    return bytes([(n >> 21) & 0x7F, (n >> 14) & 0x7F, (n >> 7) & 0x7F, n & 0x7F])


def frame_id3(ver, fid, corpo, flags=b"\0\0"):
    tam = synchsafe(len(corpo)) if ver == 4 else struct.pack(">I", len(corpo))
    return fid + tam + flags + corpo


def texto(ver, fid, s):
    return frame_id3(ver, fid, b"\x03" + s.encode() if ver == 4 else b"\x00" + s.encode("latin-1"))


def apic(ver, imagem, mime=b"image/jpeg", enc=0, desc="", tipo=3, flags=b"\0\0"):
    if enc in (1, 2):
        d = (b"\xff\xfe" + desc.encode("utf-16-le") if enc == 1 else desc.encode("utf-16-be")) + b"\0\0"
    else:
        d = desc.encode("latin-1" if enc == 0 else "utf-8") + b"\0"
    return frame_id3(ver, b"APIC", bytes([enc]) + mime + b"\0" + bytes([tipo]) + d + imagem, flags)


def tag_id3(ver, frames, flags=0, ext=b"", padding=64):
    corpo = ext + b"".join(frames) + b"\0" * padding
    return b"ID3" + bytes([ver, 0, flags]) + synchsafe(len(corpo)) + corpo


def ext_header(ver):
    if ver == 3:   # tamanho (exclui os 4 bytes) = 6, flags 0, padding 0
        return struct.pack(">I", 6) + b"\0\0" + b"\0\0\0\0"
    return synchsafe(6) + b"\x01\x00"     # v2.4: tamanho inclui a si mesmo


def monta_mp3(tag, audio):
    return tag + audio
