#!/usr/bin/env python3
"""
fw_common.py — Estruturas e CRC compartilhados das ferramentas do OpenPod.

PROPOSITO
    Centraliza o algoritmo de integridade e o layout dos cabecalhos do
    firmware GN-438 / YP3, para que rebuild e validacao usem exatamente
    a mesma implementacao e nao possam divergir silenciosamente.

ALGORITMO DE INTEGRIDADE — CRC-16/CCITT-FALSE
    poly=0x1021  init=0xFFFF  refin=false  refout=false  xorout=0x0000
    Confirmado em 5 regioes independentes deste firmware.

DEPENDENCIAS
    Apenas biblioteca padrao do Python 3.

LIMITACOES
    Os campos +0x18, +0x1C e +0x2C do cabecalho HLKJ permanecem
    NAO IDENTIFICADOS e sao tratados como opacos (preservados).
"""

import struct

FLASH_SIZE = 0x200000
FLASH_XIP_BASE = 0x00C00000

BOOT_MAGIC = b"HLKJ"
BOOT_HDR_LEN = 0x60
BOOT_HDR_CRC_OFF = 0x5C      # CRC-16 do proprio cabecalho, sobre [0x00:0x5C]

PT_ENTRY_SIZE = 0x10
PT_HDR_LEN = 0x10

FIRM_HDR_LEN = 0x30

# Particoes cujo campo de CRC esta zerado na imagem original, isto e, que
# aparentemente NAO sao verificadas pelo boot.
#
# ATENCAO: isto e uma POLITICA EXPLICITA derivada da observacao de UMA
# imagem (yp3_2.0.43). NAO foi confirmado por disassembly que o bootloader
# ignora o CRC dessas particoes. A lista existe para que o comportamento
# seja declarado em um lugar so, em vez de inferido do dado de entrada —
# inferir do dado faria a ferramenta propagar um CRC zerado invalido.
PARTICOES_SEM_CRC = {b"PSMP"}

_TAB = []
for _b in range(256):
    _c = _b << 8
    for _ in range(8):
        _c = ((_c << 1) ^ 0x1021) & 0xFFFF if _c & 0x8000 else (_c << 1) & 0xFFFF
    _TAB.append(_c)


def crc16(data: bytes, crc: int = 0xFFFF) -> int:
    """CRC-16/CCITT-FALSE."""
    for byte in data:
        crc = ((crc << 8) & 0xFFFF) ^ _TAB[((crc >> 8) ^ byte) & 0xFF]
    return crc


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


class BootHeader:
    """Cabecalho HLKJ em 0x00000000 (0x60 bytes).

    Nomes dos campos extraidos da string de depuracao do proprio
    bootloader em 0x0000A061:
        firmware_header_len / timestamp / loadToRam / runFromRam /
        loadLength / loadCrc
    """

    def __init__(self, raw: bytes):
        assert len(raw) == BOOT_HDR_LEN
        self.raw = raw
        self.magic = raw[0:4]
        self.load_to_ram = u32(raw, 0x04)
        self.run_from_ram = u32(raw, 0x08)
        self.header_len = u32(raw, 0x0C)
        self.load_length = u32(raw, 0x10)
        self.load_crc = u32(raw, 0x14)
        self.unk_18 = u32(raw, 0x18)          # NAO IDENTIFICADO
        self.unk_1c = u32(raw, 0x1C)          # NAO IDENTIFICADO
        self.ptable_off = u32(raw, 0x20)
        self.unk_2c = u32(raw, 0x2C)          # NAO IDENTIFICADO
        self.header_crc = u32(raw, BOOT_HDR_CRC_OFF)

    def rebuild(self, payload: bytes) -> bytes:
        """Reemite o cabecalho, recalculando loadCrc e headerCrc."""
        h = bytearray(BOOT_HDR_LEN)
        h[0:4] = self.magic
        struct.pack_into("<I", h, 0x04, self.load_to_ram)
        struct.pack_into("<I", h, 0x08, self.run_from_ram)
        struct.pack_into("<I", h, 0x0C, self.header_len)
        struct.pack_into("<I", h, 0x10, len(payload))
        struct.pack_into("<I", h, 0x14, crc16(payload))          # RECALCULADO
        struct.pack_into("<I", h, 0x18, self.unk_18)             # preservado
        struct.pack_into("<I", h, 0x1C, self.unk_1c)             # preservado
        struct.pack_into("<I", h, 0x20, self.ptable_off)
        struct.pack_into("<I", h, 0x2C, self.unk_2c)             # preservado
        struct.pack_into("<I", h, BOOT_HDR_CRC_OFF,
                         crc16(bytes(h[:BOOT_HDR_CRC_OFF])))      # RECALCULADO
        return bytes(h)


class FirmHeader:
    """Cabecalho da imagem FIRM (0x30 bytes, no inicio da particao)."""

    def __init__(self, raw: bytes):
        assert len(raw) == FIRM_HDR_LEN
        self.raw = raw
        self.header_len = u32(raw, 0x00)
        self.timestamp = u32(raw, 0x04)       # nome vindo da string de debug
        self.load_to_ram = u32(raw, 0x10)
        self.run_from_ram = u32(raw, 0x14)
        self.load_length = u32(raw, 0x18)
        self.load_crc = u32(raw, 0x1C)

    def rebuild(self, body: bytes) -> bytes:
        """Reemite o cabecalho, recalculando loadCrc sobre os primeiros
        load_length bytes do corpo da particao."""
        h = bytearray(FIRM_HDR_LEN)
        struct.pack_into("<I", h, 0x00, self.header_len)
        struct.pack_into("<I", h, 0x04, self.timestamp)          # preservado
        struct.pack_into("<I", h, 0x10, self.load_to_ram)
        struct.pack_into("<I", h, 0x14, self.run_from_ram)
        struct.pack_into("<I", h, 0x18, self.load_length)
        struct.pack_into("<I", h, 0x1C,
                         crc16(body[:self.load_length]))          # RECALCULADO
        return bytes(h)


class Partition:
    def __init__(self, name, offset, size, crc):
        self.name = name
        self.offset = offset
        self.size = size
        self.crc = crc

    @property
    def end(self):
        return self.offset + self.size

    def __repr__(self):
        return (f"<Partition {self.name} @0x{self.offset:06X} "
                f"size=0x{self.size:X} crc=0x{self.crc:04X}>")
