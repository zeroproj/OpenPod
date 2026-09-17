#!/usr/bin/env python3
"""
peripheral_offsets.py — Mapeia offsets acessados dentro de uma base de periférico.

Uso:
    python3 tools/peripheral_offsets.py <base_hex> [base_hex2 ...]

Exemplo:
    python3 tools/peripheral_offsets.py 0x40085000 0x40080000 0x400D0000

O script disassembla o firmware original e reporta:
- endereços absolutos acessados dentro da faixa da base;
- offset relativo à base;
- número de acessos via literal pool vs. relativo a registrador;
- número de funções distintas que acessam cada offset.

Limitações:
- Só rastreia acessos quando a própria base é carregada em um registrador
  e usada diretamente. Acessos que copiam a base para outro registrador
  antes do uso podem não ser detectados.
"""

import json
import struct
import sys
from collections import defaultdict
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from capstone.arm import (
    ARM_INS_LDR, ARM_INS_STR, ARM_INS_LDRB, ARM_INS_STRB,
    ARM_INS_LDRH, ARM_INS_STRH, ARM_OP_MEM, ARM_OP_REG, ARM_REG_PC,
)

FIRMWARE = "firmware/ORIGINAL/GN438_original.bin"
FUNCMAP = "analysis/funcmap.json"
XIP_BASE = 0x00C00000
RANGE_SIZE = 0x1000


def load_firmware():
    with open(FUNCMAP) as f:
        funcs = json.load(f)["inicios"]
    with open(FIRMWARE, "rb") as f:
        data = f.read()
    return sorted(funcs), data


def scan_base(base_addr, funcs, data):
    lo = base_addr
    hi = base_addr + RANGE_SIZE - 1
    hits = defaultdict(lambda: {"literal": 0, "reloff": 0, "funcs": set()})

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True

    for i, fs in enumerate(funcs):
        addr = fs
        off = addr - XIP_BASE
        if off < 0 or off >= len(data):
            continue
        end = min(off + 4096, len(data))
        if i + 1 < len(funcs):
            end2 = funcs[i + 1] - XIP_BASE
            if end2 > off and end2 < end:
                end = end2
        code = data[off:end]

        base_reg = None
        for insn in md.disasm(code, addr):
            # LDR literal dentro da faixa
            if insn.id == ARM_INS_LDR and len(insn.operands) == 2:
                op0 = insn.operands[0]
                op1 = insn.operands[1]
                if op1.type == ARM_OP_MEM and op1.value.mem.base == ARM_REG_PC:
                    pc = (insn.address + 4) & ~3
                    target = pc + op1.value.mem.disp
                    t_off = target - XIP_BASE
                    if 0 <= t_off + 4 <= len(data):
                        val = struct.unpack("<I", data[t_off : t_off + 4])[0]
                        if lo <= val <= hi:
                            hits[val]["literal"] += 1
                            hits[val]["funcs"].add(fs)
                            if val == lo and op0.type == ARM_OP_REG:
                                base_reg = op0.value.reg

            # Acesso relativo ao registrador base
            if base_reg is not None and insn.id in (
                ARM_INS_LDR, ARM_INS_STR, ARM_INS_LDRB, ARM_INS_STRB,
                ARM_INS_LDRH, ARM_INS_STRH,
            ):
                if len(insn.operands) >= 2:
                    op1 = insn.operands[1]
                    if op1.type == ARM_OP_MEM and op1.value.mem.base == base_reg:
                        val = lo + op1.value.mem.disp
                        hits[val]["reloff"] += 1
                        hits[val]["funcs"].add(fs)

            # Invalida base_reg se for modificado (exceto pelo próprio LDR)
            if base_reg is not None and len(insn.operands) > 0:
                op0 = insn.operands[0]
                if (
                    op0.type == ARM_OP_REG
                    and op0.value.reg == base_reg
                    and insn.id != ARM_INS_LDR
                ):
                    base_reg = None

    return hits


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    bases = [int(x, 0) for x in sys.argv[1:]]
    funcs, data = load_firmware()

    for base_addr in bases:
        print(f"=== Base 0x{base_addr:08x} ===")
        hits = scan_base(base_addr, funcs, data)
        if not hits:
            print("  (nenhum acesso detectado)")
        for val in sorted(hits.keys()):
            if val < base_addr:
                continue
            info = hits[val]
            offset = val - base_addr
            print(
                f"  0x{val:08x} +0x{offset:03x} "
                f"lit={info['literal']:3d} rel={info['reloff']:3d} "
                f"funcs={len(info['funcs']):3d}"
            )
        print()


if __name__ == "__main__":
    main()
