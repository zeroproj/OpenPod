#!/usr/bin/env python3
"""
fix_raio_selecao.py — Corrige a tentativa falha do raio: 1 byte.

O QUE ESTA ERRADO NO APARELHO HOJE

    A rotina da cor da selecao, na area livre, termina com uma chamada ao
    despachante de estilo que NAO faz nada de util:

        00DA3530   movs r1, #0x0b       <- propriedade errada
        00DA3536   bl   0xd4cac4        ; despachante(linha, 0x0B, 0, 0)

    `patch_raio_selecao.py` deduziu `LV_STYLE_RADIUS = 11` da documentacao
    da LVGL. Neste binario (LVGL v8) a propriedade 11 e
    `LV_STYLE_TRANSFORM_HEIGHT`. A chamada e valida, executa, e seta
    transform_height = 0 -- que ja era o padrao. Dai o "sem efeito".

    Duas versoes foram gastas nisso, e o codigo morto continua gravado.
    Um patch morto nao e inofensivo (STATUS_BAR.md secao 9.3).

O QUE E A PROPRIEDADE CERTA, E COMO ISSO FOI DETERMINADO

    NAO foi deduzido da documentacao. Foi lido do proprio firmware,
    enumerando a familia INTEIRA de wrappers de estilo -- cada um e uma
    casca de 4 instrucoes que fixa uma propriedade e salta para o
    despachante comum `0xD4CAC4`:

        0x00D4CFE0  prop   1  WIDTH          0x00D4D0B4  prop  33  BG_OPA
        0x00D4D01C  prop  16  PAD_TOP        0x00D4D0F4  prop  50  BORDER_WIDTH
        0x00D4D064  prop  96  RADIUS   <--   0x00D4D12E  prop  89  TEXT_FONT

    A tabela fecha sem sobra contra o enum da LVGL v8, e dois membros ja
    eram conhecidos por uso: `0xD4D12E` e a fonte (V016) e `0xD4D092` e a
    cor de fundo (V021). Isso valida o mapeamento inteiro.

    `lv_obj_set_style_radius` EXISTE no binario: e `0x00D4D064`. A
    afirmacao contraria, no cabecalho de `patch_raio_selecao.py`, esta
    errada.

    Corroboracao independente: ha **51** chamadas a `0x00D4D064` no
    firmware, quase todas na forma `(obj, 0, 0)`. Esse e o idioma do
    proprio firmware para deixar um objeto quadrado. A faixa superior
    (`0xD21716`) e o conteiner da lista (`0xD3A71A`, `0xD2F114`) recebem;
    o criador de linha compartilhado `0x00D21764` NAO recebe -- e por
    isso a linha fica com o raio do tema. Bate exatamente com o sintoma.

O QUE ESTA FERRAMENTA FAZ

    Troca UM byte: `0x0B` -> `0x60` (96) em 0x001A3530.

    A chamada morta vira `set_style_radius(linha, 0, 0)`, com seletor 0,
    isto e, valendo para todos os estados da linha.

    A home NAO e afetada: ela nao usa `0x00D21764` (MENU_LISTA.md 20).

USO
    python3 tools/fix_raio_selecao.py \
        --in  firmware/WORKING/GN438_openpod_v054.bin \
        --out firmware/WORKING/GN438_openpod_v055.bin [--dry-run]

DEPENDENCIAS
    Python 3 + capstone

SEGURANCA
    - PROVA A PROPRIA PREMISSA na imagem de entrada: desmonta o wrapper
      0x00D4D064 e exige que ele fixe a propriedade 96. Se um dia a
      analise estiver errada, a ferramenta recusa em vez de gravar;
    - exige que o gancho em 0x00D217AA chame a rotina da area livre;
    - exige que os 8 bytes ao redor do alvo sejam exatamente os
      esperados (impede aplicar sobre outra versao ou duas vezes);
    - recusa qualquer diferenca abaixo de 0x00E000 (regra R1);
    - nao toca no campo de CRC da FIRM (regra R1);
    - entrada aberta so para leitura, saida e arquivo novo.

LIMITACOES
    Prova que a propriedade certa passa a ser setada. NAO prova que fica
    bonito -- decisao visual e do aparelho (STATUS_BAR.md secao 13).
"""

import argparse
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
FLASH_SIZE = 0x200000

WRAPPER_RADIUS = 0x00D4D064     # esperado: fixa a propriedade 96
PROP_RADIUS = 96
PROP_ERRADA = 0x0B              # LV_STYLE_TRANSFORM_HEIGHT

ROTINA = 0x001A3518             # rotina da cor da selecao, na area livre
GANCHO = 0x001217AA             # a chamada dentro de 0x00D21764

# `movs r1, #0x0b` ; `movs r2, #0` ; `movs r3, #0` ; `bl 0xd4cac4`
ALVO = 0x001A3530
CONTEXTO_ESPERADO = bytes.fromhex("0b21" "0022" "0023" "a9f7c5fa")


def prop_do_wrapper(d, addr):
    """Desmonta um wrapper de estilo e devolve a propriedade que ele fixa."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    ins = list(md.disasm(d[addr - XIP:addr - XIP + 12], addr))
    if len(ins) < 4:
        return None, "nao desmonta"
    if ins[0].op_str != "r3, r2" or ins[1].op_str != "r2, r1":
        return None, f"nao parece wrapper ({ins[0].mnemonic} {ins[0].op_str})"
    if ins[2].mnemonic not in ("movs", "movw") or not ins[2].op_str.startswith("r1, #"):
        return None, "nao carrega propriedade"
    if ins[3].mnemonic != "b.w" or "0xd4cac4" not in ins[3].op_str:
        return None, "nao salta para o despachante 0xD4CAC4"
    return int(ins[2].op_str.split("#")[1], 0) & 0x3FF, None


def check(d):
    e = []

    # 1 — a premissa: 0x00D4D064 realmente fixa a propriedade 96?
    prop, err = prop_do_wrapper(d, WRAPPER_RADIUS)
    if err:
        e.append(f"0x{WRAPPER_RADIUS:08X} {err}")
    elif prop != PROP_RADIUS:
        e.append(f"0x{WRAPPER_RADIUS:08X} fixa a propriedade {prop}, "
                 f"esperado {PROP_RADIUS} (RADIUS). A analise esta errada.")

    # 2 — o gancho ainda aponta para a rotina da area livre?
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    ins = next(md.disasm(d[GANCHO:GANCHO + 4], GANCHO + XIP), None)
    destino = None
    if ins and ins.mnemonic == "bl":
        destino = int(ins.op_str.strip("#"), 0)
    if destino != ROTINA + XIP:
        e.append(f"0x{GANCHO:06X} deveria ser `bl 0x{ROTINA + XIP:08X}`, "
                 f"e {'`%s %s`' % (ins.mnemonic, ins.op_str) if ins else '?'}")

    # 3 — os bytes do alvo estao como esperado?
    got = bytes(d[ALVO:ALVO + len(CONTEXTO_ESPERADO)])
    if got != CONTEXTO_ESPERADO:
        e.append(f"0x{ALVO:06X}: contexto inesperado {got.hex()} "
                 f"(esperado {CONTEXTO_ESPERADO.hex()}) — "
                 "imagem errada, ou o patch ja foi aplicado")
    return e


def main():
    ap = argparse.ArgumentParser(
        description="Raio da selecao: corrige a propriedade, 1 byte")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.src == a.dst:
        sys.exit("origem e destino iguais")
    with open(a.src, "rb") as fh:
        orig = fh.read()
    if len(orig) != FLASH_SIZE:
        sys.exit(f"tamanho inesperado: {len(orig)}")
    data = bytearray(orig)

    erros = check(data)
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    prop, _ = prop_do_wrapper(data, WRAPPER_RADIUS)
    print()
    print("  OPENPOD — RAIO DA SELECAO")
    print()
    print(f"  premissa conferida na imagem: 0x{WRAPPER_RADIUS:08X} fixa a "
          f"propriedade {prop} (RADIUS)")
    print(f"  gancho conferido: 0x{GANCHO:06X} -> bl 0x{ROTINA + XIP:08X}")
    print()
    print("  ALTERACAO")
    print(f"    0x{ALVO:06X}  movs r1, #0x0b  ->  movs r1, #0x60")
    print(f"                 despachante(linha, TRANSFORM_HEIGHT, 0, 0)")
    print(f"              -> despachante(linha, RADIUS, 0, 0)")
    data[ALVO] = PROP_RADIUS
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X}, abaixo de 0x00E000 (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   tamanho: inalterado ({len(data)})")
    print(f"  setores de 4 KiB: {len(secs)}  "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print("  CRC da FIRM: intocado (R1) — o alvo esta fora da particao")
    print()

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as fh:
        fh.write(data)
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
