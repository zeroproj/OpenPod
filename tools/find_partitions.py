#!/usr/bin/env python3
"""
find_partitions.py — Le e valida a tabela de particoes do firmware GN-438 / YP3.

PROPOSITO
    Localiza a tabela de particoes, decodifica cada entrada
    (nome, offset, tamanho, CRC) e valida o CRC de cada particao,
    alem do cabecalho de boot "HLKJ" no offset 0.

    Algoritmo de integridade identificado por forca bruta e confirmado
    em multiplas regioes: CRC-16/CCITT-FALSE
        poly=0x1021  init=0xFFFF  refin=false  refout=false  xorout=0x0000

USO
    python3 tools/find_partitions.py <arquivo.bin> [--table 0xD000]

DEPENDENCIAS
    Apenas biblioteca padrao do Python 3.

EXEMPLO
    python3 tools/find_partitions.py firmware/WORKING/GN438_analysis.bin

LIMITACOES
    - O offset da tabela e lido do campo +0x20 do cabecalho HLKJ; a
      interpretacao desse campo e uma hipotese sustentada por evidencia
      indireta (o valor aponta exatamente para a tabela).
    - Os campos +0x18 e +0x1C do cabecalho HLKJ permanecem NAO IDENTIFICADOS.
"""

import argparse
import struct
import sys

BOOT_MAGIC = b"HLKJ"
ENTRY_SIZE = 0x10

_TAB = []
for _b in range(256):
    _c = _b << 8
    for _ in range(8):
        _c = ((_c << 1) ^ 0x1021) & 0xFFFF if _c & 0x8000 else (_c << 1) & 0xFFFF
    _TAB.append(_c)


def crc16_ccitt_false(data: bytes, crc: int = 0xFFFF) -> int:
    """CRC-16/CCITT-FALSE — algoritmo de integridade usado por este firmware."""
    for byte in data:
        crc = ((crc << 8) & 0xFFFF) ^ _TAB[((crc >> 8) ^ byte) & 0xFF]
    return crc


def parse_boot_header(data: bytes):
    if data[0:4] != BOOT_MAGIC:
        return None
    f = struct.unpack_from("<9I", data, 4)
    return {
        "load_addr":     f[0],  # +0x04
        "entry":         f[1],  # +0x08 (bit0=1 -> Thumb)
        "payload_off":   f[2],  # +0x0C
        "payload_size":  f[3],  # +0x10
        "crc16":         f[4],  # +0x14
        "unk_0x18":      f[5],
        "unk_0x1C":      f[6],
        "ptable_off":    f[7],  # +0x20
        "unk_0x24":      f[8],
    }


def parse_table(data: bytes, off: int):
    n1, n2 = struct.unpack_from("<2I", data, off)
    entries = []
    for i in range(n1):
        base = off + 0x10 + i * ENTRY_SIZE
        name = data[base:base + 4]
        p_off, p_size, p_crc = struct.unpack_from("<3I", data, base + 4)
        entries.append({
            "name": name.decode("ascii", "replace"),
            "offset": p_off,
            "size": p_size,
            "crc16": p_crc,
            "entry_off": base,
        })
    return n1, n2, entries


def main():
    ap = argparse.ArgumentParser(description="Le e valida a tabela de particoes")
    ap.add_argument("path")
    ap.add_argument("--table", type=lambda s: int(s, 0), default=None,
                    help="offset da tabela (padrao: campo +0x20 do header HLKJ)")
    args = ap.parse_args()

    data = open(args.path, "rb").read()

    hdr = parse_boot_header(data)
    print("=" * 72)
    print("CABECALHO DE BOOT @ 0x00000000")
    print("=" * 72)
    if not hdr:
        print("  magic 'HLKJ' ausente — abortando")
        return 1
    print(f"  magic         : HLKJ")
    print(f"  load_addr     : 0x{hdr['load_addr']:08X}")
    print(f"  entry         : 0x{hdr['entry']:08X}  "
          f"(Thumb={'sim' if hdr['entry'] & 1 else 'nao'}, "
          f"addr real 0x{hdr['entry'] & ~1:08X})")
    print(f"  payload_off   : 0x{hdr['payload_off']:08X}")
    print(f"  payload_size  : 0x{hdr['payload_size']:08X} ({hdr['payload_size']} bytes)")
    print(f"  payload_end   : 0x{hdr['payload_off'] + hdr['payload_size']:08X}")
    print(f"  ptable_off    : 0x{hdr['ptable_off']:08X}")
    print(f"  +0x18 (NAO ID): 0x{hdr['unk_0x18']:08X}")
    print(f"  +0x1C (NAO ID): 0x{hdr['unk_0x1C']:08X}")
    print(f"  +0x24 (NAO ID): 0x{hdr['unk_0x24']:08X}")

    payload = data[hdr["payload_off"]:hdr["payload_off"] + hdr["payload_size"]]
    calc = crc16_ccitt_false(payload)
    ok = calc == hdr["crc16"]
    print(f"  crc16 gravado : 0x{hdr['crc16']:04X}")
    print(f"  crc16 calc.   : 0x{calc:04X}   {'OK' if ok else 'DIVERGENTE'}")

    toff = args.table if args.table is not None else hdr["ptable_off"]
    n1, n2, entries = parse_table(data, toff)
    print()
    print("=" * 72)
    print(f"TABELA DE PARTICOES @ 0x{toff:08X}")
    print("=" * 72)
    print(f"  word0 = {n1}   word1 = {n2}   (contagem de entradas)")
    print()
    print(f"  {'NOME':<6}{'OFFSET':>12}{'TAMANHO':>12}{'FIM':>12}"
          f"{'CRC16':>8}{'CALC':>8}  STATUS")
    for e in entries:
        blob = data[e["offset"]:e["offset"] + e["size"]]
        c = crc16_ccitt_false(blob)
        if e["crc16"] == 0:
            status = "sem CRC (campo zerado)"
        elif c == e["crc16"]:
            status = "OK"
        else:
            status = "DIVERGENTE"
        print(f"  {e['name']:<6}  0x{e['offset']:08X}  0x{e['size']:08X}  "
              f"0x{e['offset']+e['size']:08X}  0x{e['crc16']:04X}  0x{c:04X}  {status}")

    print()
    print("=" * 72)
    print("COBERTURA DA FLASH")
    print("=" * 72)
    regions = [("BOOT+tabela", 0, 0xE000)] + \
              [(e["name"], e["offset"], e["offset"] + e["size"]) for e in entries]
    regions.sort(key=lambda r: r[1])
    cur = 0
    for name, s, e in regions:
        if s > cur:
            gap = data[cur:s]
            fill = f"fill 0x{gap[0]:02X}" if len(set(gap)) == 1 else "misto"
            print(f"  0x{cur:08X} .. 0x{s-1:08X}  ({s-cur:>8} bytes)  [LACUNA — {fill}]")
        print(f"  0x{s:08X} .. 0x{e-1:08X}  ({e-s:>8} bytes)  {name}")
        cur = max(cur, e)
    if cur < len(data):
        gap = data[cur:]
        fill = f"fill 0x{gap[0]:02X}" if len(set(gap)) == 1 else "misto"
        print(f"  0x{cur:08X} .. 0x{len(data)-1:08X}  ({len(data)-cur:>8} bytes)  [LACUNA — {fill}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
