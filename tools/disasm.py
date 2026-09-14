#!/usr/bin/env python3
"""
disasm.py — Disassembly ARM Thumb-2 do firmware GN-438, com resolucao de
            enderecos e de referencias a strings.

PROPOSITO
    O firmware nao tem simbolos. Esta ferramenta:
      - converte offset de arquivo <-> endereco de execucao;
      - encontra referencias (xrefs) a um endereco, varrendo pools literais;
      - desmonta uma faixa em Thumb-2, anotando cada valor de pool literal
        que corresponda a uma string ASCII conhecida.

MAPEAMENTO DE ENDERECOS
    BOOTLOADER   payload em 0x60 carregado para 0x0081FBC0
                 addr = offset + 0x0081FB60
    FLASH XIP    a flash inteira e mapeada em 0x00C00000
                 addr = offset + 0x00C00000
    Os dois mapeamentos coexistem: o mesmo byte tem um endereco enquanto
    copiado em RAM e outro enquanto lido por XIP. Use --map para escolher.

USO
    python3 tools/disasm.py <bin> --xref 0x0082BCC5
    python3 tools/disasm.py <bin> --at 0x0082B000 --count 80
    python3 tools/disasm.py <bin> --off 0xC000 --count 40 --map boot

DEPENDENCIAS
    Python 3 + capstone   (pip3 install capstone)

LIMITACOES
    - Nao faz analise de fluxo: o inicio de funcao e estimado procurando
      para tras o `push {..., lr}` mais proximo. Pode errar.
    - Nao distingue codigo de dados. Faixas de pool literal aparecem como
      instrucoes sem sentido; isso e esperado.
"""

import argparse
import re
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

MAPS = {
    "boot": 0x0081FB60,   # payload@0x60 -> 0x0081FBC0
    "xip":  0x00C00000,   # flash mapeada
}


def off_to_addr(off, bias):
    return off + bias


def addr_to_off(addr, bias):
    return addr - bias


def find_xrefs(data, target, lo=0, hi=None):
    """Offsets de palavras de 32 bits iguais a `target` (pools literais)."""
    hi = hi if hi is not None else len(data)
    needle = struct.pack("<I", target)
    out, i = [], lo
    while True:
        i = data.find(needle, i, hi)
        if i < 0:
            break
        if i % 4 == 0:
            out.append(i)
        i += 1
    return out


def guess_func_start(data, off, back=0x400):
    """Procura para tras o `push {..., lr}` mais proximo (0xB5xx / 0xE92D)."""
    lo = max(0, off - back)
    best = None
    for o in range(lo, off, 2):
        if data[o + 1] == 0xB5:
            best = o
        elif data[o:o + 2] == b"\x2d\xe9":
            best = o
    return best


def ascii_at(data, off, maxlen=80):
    out = b""
    while off < len(data) and len(out) < maxlen:
        c = data[off]
        if c == 0:
            break
        if not (0x20 <= c <= 0x7E or c in (0x0D, 0x0A, 0x09)):
            return None
        out += bytes([c])
        off += 1
    return out.decode("ascii") if len(out) >= 4 else None


def disasm(data, start_off, count, bias, annotate=True):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = False
    addr = off_to_addr(start_off, bias)
    chunk = data[start_off:start_off + count * 4 + 8]
    lines = []
    n = 0
    for ins in md.disasm(chunk, addr):
        note = ""
        if annotate:
            # ldr rX, [pc, #imm] -> resolve o valor do pool literal
            m = re.search(r"\[pc, #(-?(?:0x[0-9a-fA-F]+|\d+))\]", ins.op_str)
            if m and ins.mnemonic.startswith("ldr"):
                pool = ((ins.address + 4) & ~3) + int(m.group(1), 0)
                po = addr_to_off(pool, bias)
                if 0 <= po + 4 <= len(data):
                    val = struct.unpack_from("<I", data, po)[0]
                    note = f"  ; = 0x{val:08X}"
                    for b in MAPS.values():
                        so = val - b
                        if 0 <= so < len(data):
                            s = ascii_at(data, so)
                            if s:
                                note += f'  "{s[:60]}"'
                                break
        lines.append(f"  {ins.address:08X}  "
                     f"{ins.bytes.hex():<8}  {ins.mnemonic:<8} {ins.op_str}{note}")
        n += 1
        if n >= count:
            break
    return lines


def main():
    ap = argparse.ArgumentParser(description="Disassembly Thumb-2 do firmware")
    ap.add_argument("path")
    ap.add_argument("--map", choices=list(MAPS), default="boot")
    ap.add_argument("--at", type=lambda s: int(s, 0), help="endereco de execucao")
    ap.add_argument("--off", type=lambda s: int(s, 0), help="offset de arquivo")
    ap.add_argument("--count", type=int, default=40)
    ap.add_argument("--xref", type=lambda s: int(s, 0),
                    help="lista pools literais que apontam para este endereco")
    ap.add_argument("--xref-range", default=None,
                    help="limita a busca de xref, ex: 0x0,0xD000")
    args = ap.parse_args()

    data = open(args.path, "rb").read()
    bias = MAPS[args.map]

    if args.xref is not None:
        lo, hi = 0, len(data)
        if args.xref_range:
            a, b = args.xref_range.split(",")
            lo, hi = int(a, 0), int(b, 0)
        offs = find_xrefs(data, args.xref, lo, hi)
        print(f"xrefs para 0x{args.xref:08X}: {len(offs)}")
        for o in offs:
            fs = guess_func_start(data, o)
            fs_txt = (f"  inicio de funcao provavel: off 0x{fs:05X} "
                      f"(addr 0x{off_to_addr(fs, bias):08X})") if fs else ""
            print(f"  pool em off 0x{o:05X} (addr 0x{off_to_addr(o, bias):08X}){fs_txt}")
        return 0

    if args.at is not None:
        start = addr_to_off(args.at, bias)
    elif args.off is not None:
        start = args.off
    else:
        return ap.error("informe --at, --off ou --xref")

    print(f"; map={args.map} bias=0x{bias:08X}  "
          f"off 0x{start:05X} -> addr 0x{off_to_addr(start, bias):08X}")
    for ln in disasm(data, start, args.count, bias):
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
