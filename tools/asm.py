#!/usr/bin/env python3
"""
asm.py — monta Thumb-2 com o clang e devolve os bytes do `.text`.

POR QUE ISTO EXISTE

    Ate agora cada rotina nova era codificada A MAO, halfword por
    halfword. Ja custou caro duas vezes:

        `ldrb r1,[r0,#4]` em vez de `ldrb r1,[r1,#0xc]`  (Saturno S2)
        `ldr r3,=MAPA`    em vez de `adr r3,MAPA`        (patch_extras)

    Nos dois casos o verificador tambem estava errado, porque eu o
    escrevi a partir da mesma suposicao. Montar de verdade elimina a
    classe inteira.

    `keystone` nao carrega neste ambiente (biblioteca nativa). O clang
    esta instalado e tem o back-end ARM.

USO
    from asm import monta
    bytes_ = monta(".syntax unified\\n.thumb\\n...")
"""

import os
import struct
import subprocess
import tempfile


def monta(fonte):
    """Monta o fonte e devolve os bytes da secao .text."""
    with tempfile.TemporaryDirectory() as t:
        s, o = os.path.join(t, "a.s"), os.path.join(t, "a.o")
        open(s, "w").write(fonte)
        r = subprocess.run(
            ["clang", "-target", "thumbv7m-none-eabi", "-c", s, "-o", o],
            capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("clang falhou:\n" + r.stderr)
        d = open(o, "rb").read()
        # ELF32 LE: acha a secao .text pelo cabecalho, sem adivinhar offset
        shoff = struct.unpack_from("<I", d, 0x20)[0]
        shent = struct.unpack_from("<H", d, 0x2E)[0]
        shnum = struct.unpack_from("<H", d, 0x30)[0]
        shstr = struct.unpack_from("<H", d, 0x32)[0]
        stroff = struct.unpack_from("<I", d, shoff + shstr * shent + 0x10)[0]
        for i in range(shnum):
            b = shoff + i * shent
            nome_off = struct.unpack_from("<I", d, b)[0]
            fim = d.index(b"\0", stroff + nome_off)
            nome = d[stroff + nome_off:fim].decode()
            if nome == ".text":
                off = struct.unpack_from("<I", d, b + 0x10)[0]
                tam = struct.unpack_from("<I", d, b + 0x14)[0]
                return d[off:off + tam]
        raise RuntimeError("secao .text nao encontrada")
