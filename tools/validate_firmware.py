#!/usr/bin/env python3
"""
validate_firmware.py — Valida uma imagem de flash do GN-438 e compara duas imagens.

PROPOSITO
    Verificacao independente do rebuild. Confere, sem depender do
    rebuilder:
      - tamanho exato da imagem
      - magic e campos do cabecalho HLKJ
      - headerCrc (CRC-16 de [0x00:0x5C])
      - loadCrc do payload do bootloader
      - tabela de particoes: contagem, nomes, offsets, tamanhos, limites
      - CRC de cada particao
      - cabecalho da imagem FIRM e seu loadCrc
      - SHA-256

    Com --compare, faz ainda comparacao BYTE A BYTE entre duas imagens e
    reporta a posicao e o valor de cada divergencia.

USO
    python3 tools/validate_firmware.py <imagem.bin> [--compare outra.bin]
                                       [--expect-sha256 HEX]

DEPENDENCIAS
    Python 3 (biblioteca padrao) + tools/fw_common.py

EXEMPLO
    python3 tools/validate_firmware.py firmware/WORKING/GN438_rebuilt_original.bin \
        --compare firmware/ORIGINAL/GN438_original.bin \
        --expect-sha256 b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f

SAIDA
    Codigo de saida 0 se tudo passou, 1 se qualquer verificacao falhou.

LIMITACOES
    Valida o container, nao o conteudo executavel. Um firmware pode passar
    em todas estas verificacoes e mesmo assim nao inicializar.
"""

import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw


class Checker:
    def __init__(self):
        self.ok = 0
        self.fail = 0

    def check(self, label, cond, detail=""):
        if cond:
            self.ok += 1
            print(f"  [ OK ] {label}" + (f"  — {detail}" if detail else ""))
        else:
            self.fail += 1
            print(f"  [FALHA] {label}" + (f"  — {detail}" if detail else ""))
        return cond


def validate(data, c: Checker):
    print("-" * 74)
    print("TAMANHO")
    print("-" * 74)
    c.check("tamanho da imagem", len(data) == fw.FLASH_SIZE,
            f"{len(data)} bytes (esperado {fw.FLASH_SIZE})")
    if len(data) != fw.FLASH_SIZE:
        return

    print()
    print("-" * 74)
    print("CABECALHO HLKJ @ 0x00000000")
    print("-" * 74)
    h = fw.BootHeader(data[:fw.BOOT_HDR_LEN])
    c.check("magic", h.magic == fw.BOOT_MAGIC, h.magic.decode("latin1"))
    c.check("firmware_header_len", h.header_len == fw.BOOT_HDR_LEN,
            f"0x{h.header_len:X}")
    c.check("runFromRam com bit Thumb", bool(h.run_from_ram & 1),
            f"0x{h.run_from_ram:08X}")
    c.check("payload dentro da flash",
            h.header_len + h.load_length <= len(data),
            f"fim 0x{h.header_len + h.load_length:X}")
    hc = fw.crc16(data[:fw.BOOT_HDR_CRC_OFF])
    c.check("headerCrc (+0x5C)", hc == h.header_crc,
            f"gravado 0x{h.header_crc:04X} / calculado 0x{hc:04X}")
    payload = data[h.header_len:h.header_len + h.load_length]
    pc = fw.crc16(payload)
    c.check("loadCrc do bootloader", pc == h.load_crc,
            f"gravado 0x{h.load_crc:04X} / calculado 0x{pc:04X}")

    print()
    print("-" * 74)
    print(f"TABELA DE PARTICOES @ 0x{h.ptable_off:08X}")
    print("-" * 74)
    pt = h.ptable_off
    c.check("tabela dentro da flash", pt + fw.PT_HDR_LEN <= len(data))
    n1, n2 = struct.unpack_from("<2I", data, pt)
    c.check("contagem de particoes consistente", n1 == n2, f"{n1} / {n2}")
    parts = []
    for i in range(n1):
        b = pt + fw.PT_HDR_LEN + i * fw.PT_ENTRY_SIZE
        name = data[b:b + 4]
        off, size, crc = struct.unpack_from("<3I", data, b + 4)
        parts.append(fw.Partition(name, off, size, crc))
    for p in parts:
        nm = p.name.decode("latin1")
        c.check(f"particao {nm}: limites",
                p.offset + p.size <= len(data),
                f"0x{p.offset:08X}..0x{p.end:08X}")
        calc = fw.crc16(data[p.offset:p.end])
        if p.name in fw.PARTICOES_SEM_CRC:
            # politica declarada: esta particao nao e verificada pelo boot
            c.check(f"particao {nm}: campo de CRC zerado conforme politica",
                    p.crc == 0,
                    f"gravado 0x{p.crc:04X} — calculado seria 0x{calc:04X}")
        else:
            c.check(f"particao {nm}: CRC nao esta zerado", p.crc != 0)
            c.check(f"particao {nm}: CRC", calc == p.crc,
                    f"gravado 0x{p.crc:04X} / calculado 0x{calc:04X}")

    # sobreposicao
    ordenadas = sorted(parts, key=lambda p: p.offset)
    sobrepoe = any(ordenadas[i].end > ordenadas[i + 1].offset
                   for i in range(len(ordenadas) - 1))
    c.check("particoes sem sobreposicao", not sobrepoe)

    firm = next((p for p in parts if p.name == b"FIRM"), None)
    if firm:
        print()
        print("-" * 74)
        print(f"CABECALHO FIRM @ 0x{firm.offset:08X}")
        print("-" * 74)
        f = fw.FirmHeader(data[firm.offset:firm.offset + fw.FIRM_HDR_LEN])
        c.check("FIRM firmware_header_len", f.header_len == fw.FIRM_HDR_LEN,
                f"0x{f.header_len:X}")
        c.check("FIRM runFromRam com bit Thumb", bool(f.run_from_ram & 1),
                f"0x{f.run_from_ram:08X}")
        body = data[firm.offset + f.header_len:firm.end]
        c.check("FIRM loadLength cabe no corpo", f.load_length <= len(body),
                f"0x{f.load_length:X} <= 0x{len(body):X}")
        fc = fw.crc16(body[:f.load_length])
        c.check("FIRM loadCrc", fc == f.load_crc,
                f"gravado 0x{f.load_crc:04X} / calculado 0x{fc:04X}")
    return parts


def compare(a, b, c: Checker, name_a, name_b):
    print()
    print("-" * 74)
    print("COMPARACAO BYTE A BYTE")
    print("-" * 74)
    print(f"  A = {name_a}  ({len(a)} bytes)")
    print(f"  B = {name_b}  ({len(b)} bytes)")
    c.check("tamanhos iguais", len(a) == len(b))
    n = min(len(a), len(b))
    diffs = [i for i in range(n) if a[i] != b[i]]
    c.check("diferencas de byte = 0", len(diffs) == 0,
            f"{len(diffs)} byte(s) divergente(s)")
    if diffs:
        print("\n  primeiras 40 divergencias:")
        for i in diffs[:40]:
            print(f"      0x{i:08X}: A=0x{a[i]:02X}  B=0x{b[i]:02X}")
        if len(diffs) > 40:
            print(f"      ... (+{len(diffs)-40})")
    return diffs


def main():
    ap = argparse.ArgumentParser(description="Valida e compara imagens de flash")
    ap.add_argument("path")
    ap.add_argument("--compare", default=None)
    ap.add_argument("--expect-sha256", default=None)
    args = ap.parse_args()

    data = open(args.path, "rb").read()
    c = Checker()

    print("=" * 74)
    print(f"VALIDACAO — {args.path}")
    print("=" * 74)
    sha = hashlib.sha256(data).hexdigest()
    print(f"  sha256: {sha}\n")
    validate(data, c)

    if args.expect_sha256:
        print()
        print("-" * 74)
        print("SHA-256")
        print("-" * 74)
        c.check("sha256 confere com o esperado",
                sha.lower() == args.expect_sha256.lower(),
                f"{sha}")

    if args.compare:
        other = open(args.compare, "rb").read()
        sha_o = hashlib.sha256(other).hexdigest()
        compare(other, data, c, args.compare, args.path)
        print()
        c.check("sha256 das duas imagens iguais", sha_o == sha,
                f"{sha_o} vs {sha}")

    print()
    print("=" * 74)
    print(f"RESULTADO: {c.ok} verificacoes OK, {c.fail} falha(s)")
    print("=" * 74)
    return 0 if c.fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
