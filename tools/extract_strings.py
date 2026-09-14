#!/usr/bin/env python3
"""
extract_strings.py — Extrai strings de um binario bruto registrando offsets.

PROPOSITO
    Extrair strings ASCII, UTF-16LE e UTF-16BE de um dump de firmware,
    preservando o offset de cada ocorrencia para permitir correlacao
    posterior com tabelas, referencias e regioes do binario.

USO
    python3 tools/extract_strings.py <arquivo.bin> --enc ascii --min 4 \
        [--start 0x0] [--end 0x200000] [--out saida.txt]

    --enc aceita: ascii | utf16le | utf16be | all

DEPENDENCIAS
    Apenas biblioteca padrao do Python 3.

EXEMPLO
    python3 tools/extract_strings.py firmware/WORKING/GN438_analysis.bin \
        --enc ascii --min 5 --out analysis/strings/ascii_min5.txt

LIMITACOES
    - Nao distingue string real de sequencia de bytes que por acaso e imprimivel.
    - UTF-16 e detectado por padrao byte/0x00 alternado; textos CJK reais
      nao seguem esse padrao e podem escapar da deteccao.
"""

import argparse
import re
import sys

ASCII_OK = rb"[\x09\x20-\x7E]"


def extract_ascii(data: bytes, minlen: int):
    pat = re.compile(ASCII_OK + b"{" + str(minlen).encode() + b",}")
    for m in pat.finditer(data):
        yield m.start(), m.group().decode("ascii", "replace")


def extract_utf16(data: bytes, minlen: int, big: bool):
    # Padrao: caractere ASCII intercalado com 0x00.
    if big:
        pat = re.compile(b"(?:\x00" + ASCII_OK + b"){" + str(minlen).encode() + b",}")
        enc = "utf-16-be"
    else:
        pat = re.compile(b"(?:" + ASCII_OK + b"\x00){" + str(minlen).encode() + b",}")
        enc = "utf-16-le"
    for m in pat.finditer(data):
        raw = m.group()
        if len(raw) % 2:
            raw = raw[:-1]
        yield m.start(), raw.decode(enc, "replace")


def main():
    ap = argparse.ArgumentParser(description="Extrai strings com offsets")
    ap.add_argument("path")
    ap.add_argument("--enc", default="ascii",
                    choices=["ascii", "utf16le", "utf16be", "all"])
    ap.add_argument("--min", type=int, default=4, help="comprimento minimo")
    ap.add_argument("--start", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--end", type=lambda s: int(s, 0), default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    with open(args.path, "rb") as fh:
        data = fh.read()
    end = args.end if args.end is not None else len(data)
    window = data[args.start:end]

    results = []
    if args.enc in ("ascii", "all"):
        results += [(o, "A", s) for o, s in extract_ascii(window, args.min)]
    if args.enc in ("utf16le", "all"):
        results += [(o, "L", s) for o, s in extract_utf16(window, args.min, False)]
    if args.enc in ("utf16be", "all"):
        results += [(o, "B", s) for o, s in extract_utf16(window, args.min, True)]
    results.sort()

    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    try:
        for off, kind, s in results:
            out.write(f"0x{args.start + off:08X}  {kind}  {s}\n")
    finally:
        if args.out:
            out.close()
            print(f"{len(results)} strings -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
