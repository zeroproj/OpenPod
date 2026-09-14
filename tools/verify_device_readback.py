#!/usr/bin/env python3
"""
verify_device_readback.py — Compara um dump recem-lido do aparelho com o original.

PROPOSITO
    Fecha o pre-requisito da politica de gravacao (docs/FLASH_POLICY.md §7):
    provar que o caminho de recuperacao por USB funciona ANTES de precisar
    dele.

    Um `read_flash` bem sucedido prova tres coisas de uma vez:
      1. o aparelho enumera e responde por USB;
      2. conseguimos ler a flash inteira de volta;
      3. o conteudo confere com o nosso original — ou seja, o arquivo
         preservado e uma copia fiel do que esta no aparelho.

    ESTE SCRIPT NAO TOCA NO APARELHO. Ele compara dois arquivos locais.

USO
    python3 tools/verify_device_readback.py <dump_novo.bin> \
        [--ref firmware/ORIGINAL/GN438_original.bin]

COMO OBTER O DUMP NOVO (no Linux, somente leitura)
    sudo ./smtlink_dump --id 301a:2801 flash_id read_flash 0 2M readback.bin

DEPENDENCIAS
    Python 3 (biblioteca padrao)

INTERPRETACAO
    - FIRM e TONE devem bater byte a byte. Se nao baterem, o aparelho NAO
      esta com o firmware que voce acha que esta.
    - PSMP pode divergir legitimamente: e a area de configuracao gravada
      em runtime pelo proprio aparelho (docs/FIRMWARE_MAP.md §7).
    - A area livre (0xFF) pode divergir se algo ja foi gravado ali.
"""

import argparse
import hashlib
import sys

REGIOES = [
    ("cabecalho HLKJ",    0x000000, 0x000060, True),
    ("bootloader",        0x000060, 0x00C94C, True),
    ("tabela particoes",  0x00D000, 0x00D040, True),
    ("FIRM",              0x00E000, 0x1A0570, True),
    ("TONE",              0x1A1000, 0x1A3038, True),
    ("area livre (0xFF)", 0x1A3038, 0x1FC000, False),
    ("PSMP (config)",     0x1FC000, 0x200000, False),
]


def main():
    ap = argparse.ArgumentParser(description="Compara dump do aparelho com o original")
    ap.add_argument("dump")
    ap.add_argument("--ref", default="firmware/ORIGINAL/GN438_original.bin")
    args = ap.parse_args()

    new = open(args.dump, "rb").read()
    ref = open(args.ref, "rb").read()

    print("=" * 74)
    print("CONFERENCIA DE LEITURA DO APARELHO")
    print("=" * 74)
    print(f"  lido do aparelho : {args.dump}  ({len(new)} bytes)")
    print(f"    sha256         : {hashlib.sha256(new).hexdigest()}")
    print(f"  referencia       : {args.ref}  ({len(ref)} bytes)")
    print(f"    sha256         : {hashlib.sha256(ref).hexdigest()}")
    print()

    if len(new) != len(ref):
        print(f"  [FALHA] tamanhos diferentes: {len(new)} vs {len(ref)}")
        print("          o dump esta incompleto ou foi lido com tamanho errado.")
        return 1

    if new == ref:
        print("  [ OK ] imagens IDENTICAS — nada mudou no aparelho desde o dump\n")

    print(f"  {'REGIAO':<20}{'INTERVALO':<24}{'DIVERGENCIAS':>14}  VEREDITO")
    critico_falhou = False
    for nome, lo, hi, critico in REGIOES:
        d = sum(1 for i in range(lo, hi) if new[i] != ref[i])
        if d == 0:
            v = "identica"
        elif critico:
            v = "*** DIVERGENTE — INVESTIGAR ***"
            critico_falhou = True
        else:
            v = "diferente (esperado/aceitavel)"
        print(f"  {nome:<20}0x{lo:06X}-0x{hi:06X}{d:>14}  {v}")

    print()
    print("=" * 74)
    if critico_falhou:
        print("RESULTADO: DIVERGENCIA EM REGIAO CRITICA")
        print()
        print("  O aparelho NAO contem o mesmo firmware do arquivo de referencia.")
        print("  NAO grave nada ate entender por que. Preserve este dump novo:")
        print("  ele e uma evidencia, nao um erro.")
        return 1
    print("RESULTADO: LEITURA POR USB CONFIRMADA")
    print()
    print("  O caminho de recuperacao funciona:")
    print("    - o aparelho enumera e responde;")
    print("    - a flash pode ser lida por completo;")
    print("    - o original preservado confere com o aparelho.")
    print()
    print("  O pre-requisito de docs/FLASH_POLICY.md §7 esta atendido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
