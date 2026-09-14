#!/usr/bin/env python3
"""
make_update_up.py — Gera e valida um pacote update.up a partir de uma imagem de flash.

PROPOSITO
    Implementa o mesmo algoritmo de `fwhelper dump2fw` (upstream
    smartlink_flash, commit 49d51d17), com validacao adicional e relatorio
    detalhado.

    ESTE SCRIPT NAO TOCA NO HARDWARE. Ele apenas le uma imagem de flash e
    escreve um arquivo .up local. Nenhuma operacao USB e realizada.

FORMATO PRODUZIDO
    0x0000  "CONFIG"          6 bytes
    0x0006  uint32  0x100     tamanho do cabecalho = deslocamento flash->arquivo
    0x0010  uint32  fw_size   tamanho do payload
    0x0014  uint16  crc16     CRC-16/CCITT-FALSE do payload
    0x0016  char[]  chip      "SL6801" ou "SL6806", terminado em NUL
    0x00FE  uint8   0x55
    0x00FF  uint8   0xAA
    0x0100  payload           copia literal de flash[0 : fw_size]

    fw_size = maior (offset + tamanho) entre as particoes, EXCLUINDO PSMP.

USO
    python3 tools/make_update_up.py --in <imagem.bin> --out <pacote.up> [--verify-only <pacote.up>]

DEPENDENCIAS
    Python 3 + tools/fw_common.py

LIMITACOES
    - Aborta se qualquer CRC de particao da imagem de entrada divergir.
      O pacote so pode ser montado a partir de uma imagem ja integra.
    - Nao altera o timestamp. Se a verificacao de timestamp do bootloader
      estiver ativa, um pacote gerado de uma imagem com o mesmo timestamp
      do firmware instalado pode ser recusado. Ver docs/UPDATE_MECHANISM.md.
"""

import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

HDR_LEN = 0x100


def analyze(data):
    """Reproduz a analise de particoes de dump2fw. Devolve (fw_size, chip, entradas)."""
    if len(data) < 0x60 or data[0:4] != b"HLKJ":
        raise SystemExit("ABORTADO: cabecalho de bootloader invalido")
    pt = struct.unpack_from("<I", data, 0x20)[0]
    if len(data) < pt or len(data) - pt < 0x100:
        raise SystemExit("ABORTADO: tabela de particoes fora do arquivo")
    n, _, ver, _ = struct.unpack_from("<4I", data, pt)
    if n > 15:
        raise SystemExit("ABORTADO: particoes demais")
    fw_size, ents = 0, []
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        name = data[b:b + 4]
        off, ln = struct.unpack_from("<2I", data, b + 4)
        crc_off = 14 if ver >= 0x30 else 12
        stored = struct.unpack_from("<H", data, b + crc_off)[0]
        if name == b"PSMP":
            ents.append((name, off, ln, stored, None, True))
            continue
        if len(data) < off or len(data) - off < ln:
            raise SystemExit(f"ABORTADO: particao {name!r} fora do arquivo")
        calc = fw.crc16(data[off:off + ln])
        if calc != stored:
            raise SystemExit(
                f"ABORTADO: CRC da particao {name.decode()} diverge "
                f"(0x{calc:04X}, esperado 0x{stored:04X})")
        ents.append((name, off, ln, stored, calc, False))
        fw_size = max(fw_size, off + ln)
    if not fw_size:
        raise SystemExit("ABORTADO: nenhuma particao de firmware encontrada")
    chip = b"SL6806" if ver >= 0x30 else b"SL6801"
    return fw_size, chip, ver, pt, ents


def build(data, fw_size, chip):
    buf = bytearray(HDR_LEN)
    buf[0:6] = b"CONFIG"
    struct.pack_into("<I", buf, 0x06, HDR_LEN)
    struct.pack_into("<I", buf, 0x10, fw_size)
    struct.pack_into("<H", buf, 0x14, fw.crc16(data[:fw_size]))
    buf[0x16:0x16 + len(chip) + 1] = chip + b"\x00"
    buf[0xFE] = 0x55
    buf[0xFF] = 0xAA
    return bytes(buf) + data[:fw_size]


def verify(pkg, ref=None):
    ok = fail = 0

    def chk(label, cond, detail=""):
        nonlocal ok, fail
        print(f"  [{'OK' if cond else 'FALHA'}] {label}" + (f" — {detail}" if detail else ""))
        if cond:
            ok += 1
        else:
            fail += 1
        return cond

    chk("tamanho minimo", len(pkg) > HDR_LEN, f"{len(pkg)} bytes")
    chk("magic \"CONFIG\"", pkg[0:6] == b"CONFIG", pkg[0:6].decode("latin1"))
    hlen = struct.unpack_from("<I", pkg, 0x06)[0]
    chk("codeOffsetInByte == 0x100", hlen == HDR_LEN, f"0x{hlen:X}")
    fw_size = struct.unpack_from("<I", pkg, 0x10)[0]
    chk("fw_size coerente com o arquivo", len(pkg) == HDR_LEN + fw_size,
        f"0x100 + 0x{fw_size:X} = {HDR_LEN+fw_size} vs {len(pkg)}")
    stored = struct.unpack_from("<H", pkg, 0x14)[0]
    calc = fw.crc16(pkg[HDR_LEN:HDR_LEN + fw_size])
    chk("CRC-16 do payload", stored == calc, f"gravado 0x{stored:04X} / calculado 0x{calc:04X}")
    chip = pkg[0x16:0x20].split(b"\x00")[0]
    chk("chip id", chip in (b"SL6801", b"SL6806"), chip.decode("latin1"))
    chk("assinatura 0x55 0xAA", pkg[0xFE] == 0x55 and pkg[0xFF] == 0xAA,
        f"0x{pkg[0xFE]:02X} 0x{pkg[0xFF]:02X}")
    chk("resto do cabecalho zerado",
        all(b == 0 for b in pkg[0x20:0xFE]) and all(b == 0 for b in pkg[0x0A:0x10]))
    chk("payload comeca com HLKJ", pkg[HDR_LEN:HDR_LEN + 4] == b"HLKJ")

    if ref is not None:
        payload = pkg[HDR_LEN:HDR_LEN + fw_size]
        chk("payload identico a flash[0:fw_size] da imagem",
            payload == ref[:fw_size], f"{fw_size} bytes")
        diffs = sum(1 for i in range(fw_size) if payload[i] != ref[i])
        chk("bytes divergentes no payload = 0", diffs == 0, str(diffs))
    return ok, fail


def main():
    ap = argparse.ArgumentParser(description="Gera e valida um pacote update.up")
    ap.add_argument("--in", dest="src", required=True, help="imagem de flash de origem")
    ap.add_argument("--out", dest="dst", default=None)
    ap.add_argument("--verify-only", dest="vonly", default=None,
                    help="apenas valida um pacote existente")
    args = ap.parse_args()

    data = open(args.src, "rb").read()

    if args.vonly:
        pkg = open(args.vonly, "rb").read()
        print("=" * 72)
        print(f"VALIDACAO — {args.vonly}")
        print("=" * 72)
        print(f"  sha256: {hashlib.sha256(pkg).hexdigest()}\n")
        ok, fail = verify(pkg, data)
        print(f"\n  RESULTADO: {ok} OK, {fail} falha(s)")
        return 1 if fail else 0

    fw_size, chip, ver, pt, ents = analyze(data)
    print("=" * 72)
    print("ANALISE DA IMAGEM")
    print("=" * 72)
    print(f"  origem      : {args.src} ({len(data)} bytes)")
    print(f"  sha256      : {hashlib.sha256(data).hexdigest()}")
    print(f"  ptable      : 0x{pt:06X}   ver = 0x{ver:X}   chip = {chip.decode()}")
    for name, off, ln, stored, calc, skipped in ents:
        s = "PULADA (PSMP)" if skipped else f"CRC 0x{stored:04X} OK"
        print(f"    {name.decode():<6} off=0x{off:06X} len=0x{ln:06X} fim=0x{off+ln:06X}  {s}")
    print(f"  fw_size     : 0x{fw_size:X} ({fw_size})")

    pkg = build(data, fw_size, chip)
    print(f"  pacote      : 0x100 + 0x{fw_size:X} = {len(pkg)} bytes")

    if not args.dst:
        print("\n  (sem --out: nada gravado)")
        return 0
    if os.path.exists(args.dst):
        print(f"\nRECUSADO: {args.dst} ja existe.", file=sys.stderr)
        return 2
    with open(args.dst, "wb") as fh:
        fh.write(pkg)
    print(f"  gravado     : {args.dst}")
    print(f"  sha256      : {hashlib.sha256(pkg).hexdigest()}")

    print()
    print("=" * 72)
    print("VALIDACAO DO PACOTE RECEM-GERADO")
    print("=" * 72)
    ok, fail = verify(pkg, data)
    print(f"\n  RESULTADO: {ok} OK, {fail} falha(s)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
