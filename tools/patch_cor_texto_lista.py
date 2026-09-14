#!/usr/bin/env python3
"""
patch_cor_texto_lista.py — Texto branco nas listas do sistema.

O QUE O MANTENEDOR VIU (2026-09-14, com a 1.8 no aparelho)

    "so mesmo a fonte que esta cinza e deveria ser branca"

    As listas do sistema (Extras, Configurar e as outras 37) ficam com o
    texto num cinza; a home usa branco.

A CAUSA — a mesma estrutura da cor da selecao

    A home **pinta o texto explicitamente**: chama o getter de cor do
    tema (`0x00D2E948`) e aplica no rotulo.

    O rotulo das listas do sistema **nao define cor nenhuma**:

        00D3A824  bl 0xd5e2e8     ; cria o rotulo
        00D3A83C  bl 0xd4a1ba     ; largura
        00D3A844  bl 0xd5ef04     ; modo
        00D3A854  bl 0xd5ed94     ; texto
                                  ; <- nenhuma cor de texto

    Entao ele herda o padrao do tema, que e o cinza.

    A V013 trocou os DOIS getters de cor de texto para devolverem branco
    (`mov.w r0, #-1`), e por isso a home ficou branca. **Quem nao chama
    getter nenhum nao foi beneficiado** -- e nenhuma das 39 telas de
    lista chama.

    E exatamente a mesma forma do problema da cor da selecao
    (`ROADMAP_1.1.md` 3b): *"a home pinta explicitamente; as listas caem
    no tema"*.

A CORRECAO

    `LV_STYLE_TEXT_COLOR` (propriedade 87) tem o **bit de heranca**
    (`0x0400`, ver `GUI_ANALYSIS.md`), entao pintar a **linha** pinta o
    rotulo filho. E a linha ja tem gancho: o criador compartilhado
    `0x00D21764`, que serve as 39 telas, ja desvia para uma rotina na
    area livre que resolve borda, cor de selecao e raio.

    Essa rotina (`0x00DA3518`) termina colada nas strings e nao tem para
    onde crescer. Entao esta ferramenta poe uma rotina NOVA na area
    livre, que **chama a antiga** e acrescenta a cor do texto, e repoe o
    gancho para a nova. Nada e duplicado.

        openpod_linha:
            push {r4, lr}
            mov  r4, r0            ; a linha
            bl   0x00DA3518        ; tudo o que ja fazia
            bl   0x00D21384        ; cor de texto do tema (= branco, V013)
            mov  r1, r0
            mov  r0, r4
            movs r2, #0            ; seletor 0: todos os estados
            bl   0x00D4D10A        ; set_style_text_color
            pop  {r4, pc}

USO
    python3 tools/patch_cor_texto_lista.py \\
        --in  firmware/WORKING/GN438_openpod_v057.bin \\
        --out firmware/WORKING/GN438_openpod_v058.bin [--dry-run]

DEPENDENCIAS
    Python 3 + capstone

SEGURANCA
    - PROVA A PREMISSA na imagem: desmonta `0x00D4D10A` e exige que ele
      fixe a propriedade 87 (TEXT_COLOR) com o bit de heranca;
    - exige que `0x00D21384` devolva branco (senao o patch nao teria
      efeito e o problema seria outro);
    - exige que o gancho atual aponte para `0x00DA3518`;
    - exige area livre virgem no destino;
    - desmonta a rotina montada e confere instrucao por instrucao;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.

LIMITACOES
    Pinta a linha, e o rotulo herda. Se alguma tela definir cor propria
    no rotulo dela, aquela tela continua como esta -- nenhuma define
    hoje, mas isto nao foi verificado nas 39.
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

ROTINA_ANTIGA = 0x00DA3518
COR_TEMA = 0x00D21384          # getter de cor de texto do tema
SET_TEXT_COLOR = 0x00D4D10A    # wrapper: propriedade 87 | 0x400
PROP_TEXT_COLOR = 87

GANCHO = 0x001217AA            # dentro do criador de linha 0x00D21764
BLOB_OFF = 0x001A5200          # mesmo setor das outras rotinas
BLOB_MAX = 0x200


def ins_em(d, a):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    return next(md.disasm(d[a - XIP:a - XIP + 4], a), None)


def bl(origem, destino):
    off = destino - (origem + 4)
    if off & 1 or not (-(1 << 24) <= off < (1 << 24)):
        raise ValueError("bl fora de alcance")
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = (0xD000 | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11)
           | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def prop_do_wrapper(d, addr):
    """A casca de cor de 32 bits monta o valor com bfi; a propriedade
    aparece num movw/movs logo antes do salto ao despachante."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    prop = None
    for i in md.disasm(d[addr - XIP:addr - XIP + 40], addr):
        if i.mnemonic in ("movs", "movw") and i.op_str.startswith("r1, #"):
            prop = int(i.op_str.split("#")[1], 0)
        if i.mnemonic == "b.w" and "0xd4cac4" in i.op_str:
            return prop
    return None


def monta(base):
    c = []
    c.append(struct.pack("<H", 0xB510))                 # push {r4, lr}
    c.append(struct.pack("<H", 0x4604))                 # mov  r4, r0
    c.append(bl(base + 4, ROTINA_ANTIGA))               # bl   rotina antiga
    c.append(bl(base + 8, COR_TEMA))                    # bl   cor do tema
    c.append(struct.pack("<H", 0x4601))                 # mov  r1, r0
    c.append(struct.pack("<H", 0x4620))                 # mov  r0, r4
    c.append(struct.pack("<H", 0x2200))                 # movs r2, #0
    c.append(bl(base + 18, SET_TEXT_COLOR))             # bl   set_text_color
    c.append(struct.pack("<H", 0xBD10))                 # pop  {r4, pc}
    return b"".join(c)


ESPERADO = ["push", "mov", "bl", "bl", "mov", "mov", "movs", "bl", "pop"]


def main():
    ap = argparse.ArgumentParser(description="Texto branco nas listas")
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

    erros = []

    prop = prop_do_wrapper(data, SET_TEXT_COLOR)
    if prop is None:
        erros.append(f"0x{SET_TEXT_COLOR:08X} nao parece um wrapper de estilo")
    elif (prop & 0x3FF) != PROP_TEXT_COLOR:
        erros.append(f"0x{SET_TEXT_COLOR:08X} fixa a propriedade "
                     f"{prop & 0x3FF}, esperado {PROP_TEXT_COLOR} (TEXT_COLOR)")
    elif not (prop & 0x400):
        erros.append(f"propriedade {prop:#06x} sem o bit de heranca: o "
                     "rotulo filho NAO herdaria a cor")

    i = ins_em(data, COR_TEMA)
    if not (i and i.mnemonic == "mov.w" and i.op_str in ("r0, #-1",)):
        erros.append(f"0x{COR_TEMA:08X} nao devolve branco "
                     f"({i.mnemonic + ' ' + i.op_str if i else '?'}) — "
                     "o cinza viria de outro lugar e este patch nao resolve")

    g = ins_em(data, GANCHO + XIP)
    if not (g and g.mnemonic == "bl"
            and int(g.op_str.strip("#"), 0) == ROTINA_ANTIGA):
        erros.append(f"0x{GANCHO:06X} nao chama 0x{ROTINA_ANTIGA:08X}")

    if any(b != 0xFF for b in data[BLOB_OFF:BLOB_OFF + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB_OFF:06X} nao esta virgem")

    base = BLOB_OFF + XIP
    blob = monta(base)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    got = [x.mnemonic for x in md.disasm(blob, base)]
    if got != ESPERADO:
        erros.append(f"rotina montada nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")

    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print("  OPENPOD — TEXTO BRANCO NAS LISTAS DO SISTEMA")
    print()
    print(f"  premissa conferida: 0x{SET_TEXT_COLOR:08X} fixa "
          f"{prop:#06x} = propriedade {prop & 0x3FF} (TEXT_COLOR) + heranca")
    print(f"  premissa conferida: 0x{COR_TEMA:08X} devolve branco")
    print(f"  gancho conferido:   0x{GANCHO:06X} -> 0x{ROTINA_ANTIGA:08X}")
    print()
    print("  ALTERACOES")
    data[BLOB_OFF:BLOB_OFF + len(blob)] = blob
    print(f"    0x{BLOB_OFF:06X}  rotina nova {len(blob)} B — chama a antiga "
          f"e acrescenta a cor do texto")
    data[GANCHO:GANCHO + 4] = bl(GANCHO + XIP, base)
    print(f"    0x{GANCHO:06X}  bl 0x{ROTINA_ANTIGA:08X} -> bl 0x{base:08X}")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X}, abaixo de 0x00E000 (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   tamanho: inalterado ({len(data)})")
    print(f"  setores de 4 KiB: {len(secs)}  "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print("  CRC da FIRM: campo intocado (R1)")
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
