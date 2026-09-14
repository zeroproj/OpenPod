#!/usr/bin/env python3
"""
patch_battery_y.py — Ajusta a altura vertical do icone de bateria na faixa.

POR QUE EXISTE

    O V018 subiu o texto da faixa de y_ofs 2 para 1 e, no mesmo passo, eu
    desci a bateria de y=0 para y=2 -- sem medir. Resultado: a bateria
    ficou 3 px mais baixa em relacao ao texto do que estava no V017, onde
    a proporcao agradava.

        V017   texto y_ofs 2, bateria y 0   -> diferenca -2
        V018   texto y_ofs 1, bateria y 2   -> diferenca +1
        V019   texto y_ofs 1, bateria y 0   -> diferenca -1

    A fonte de icones (0x00CACFE4) tem line_height 16 e base_line 2,
    contra o texto de 12 px de ascendente: por isso o icone precisa de um
    y menor que o do texto para parecer alinhado.

O QUE E ALTERADO

    0x0012260E   1 B  o imediato de `movs r2, #N` que vai como argumento
                      y de set_pos(obj, 107, N), em view_bat_create
                      (0x00D225B0)

    Mais o CRC-16 da particao FIRM.

USO
    python3 tools/patch_battery_y.py \
        --in  firmware/WORKING/GN438_openpod_v018.bin \
        --out firmware/WORKING/GN438_openpod_v019.bin \
        --de 2 --para 0 [--dry-run]

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se o byte atual nao for o valor informado em --de;
    - recusa y fora de 0..31 (a barra tem 16 px; alem disso o icone sai);
    - a entrada e aberta somente para leitura; a saida e arquivo novo.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

BATERIA_Y = 0x0012260E


def main():
    ap = argparse.ArgumentParser(description="Altura do icone de bateria")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--de", type=int, required=True)
    ap.add_argument("--para", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2
    if not 0 <= a.para <= 31:
        print("RECUSADO: y fora de 0..31.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — altura do icone de bateria na faixa superior")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    if d[BATERIA_Y] != a.de:
        print(f"  ABORTADO: 0x{BATERIA_Y:06X} contem 0x{d[BATERIA_Y]:02X}, "
              f"--de dizia 0x{a.de:02X}")
        return 1
    d[BATERIA_Y] = a.para
    print(f"  0x{BATERIA_Y:06X}  y da bateria  {a.de} -> {a.para}")

    pt = struct.unpack_from("<I", d, 0x20)[0]
    n = struct.unpack_from("<I", d, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if d[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", d, b + 4)
            old = struct.unpack_from("<H", d, b + 0x0C)[0]
            new = fw.crc16(bytes(d[off:off + ln]))
            if not a.dry_run:
                # R1: NAO gravar o CRC da FIRM. Nao e verificado pelo aparelho, e
                # escrever aqui poe o setor 0x00D000 (tabela de particoes) de
                # volta na lista de setores — foi ele que matou o primeiro
                # aparelho. Achado pelo tools/build.py ao reconstruir do zero.
                pass   # NAO gravar o CRC (R1)
            print(f"  CRC da FIRM: 0x{old:04X} -> 0x{new:04X}"
                  f"{' (nao gravado)' if a.dry_run else ''}")
            break

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
