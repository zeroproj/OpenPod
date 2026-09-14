#!/usr/bin/env python3
"""
patch_saturno_s4.py — SATURNO S4: a home entra na carcaça.

O OBJETIVO

    Ate aqui o Saturno vale para 36 telas. A home ficava de fora porque
    ela nao usa os helpers compartilhados: tem widget proprio (classe
    0x00CDAAA8) e desenha a faixa como PIXELS na folha de imagem
    0x000CDD50.

    Depois deste patch, **a faixa da home e o MESMO objeto das outras 36**,
    criado pelo mesmo helper `0x00D216F0`, com altura e cores vindas da
    tabela de tema. Mudar a tabela passa a mudar 37 telas.

O QUE ESTE PATCH *NAO* FAZ, E POR QUE

    NAO reescreve `page_home_create` inteiro. Mapeei a home:

        0x00D2EBF0  widget proprio, nao os helpers
        0x00D2ECF0  por item: objeto de imagem (icone) + rotulo,
                    posicionados por tabela de coordenadas

    Troca-la pelos helpers exigiria trocar junto o `event_cb` e todo o
    modelo de `ctrl_id` — isto e, **mexer na navegacao que o mantenedor
    aprovou**, e e a classe de mudanca que ja custou tres gravacoes
    (MENU_LISTA.md 14).

    O ganho que sobraria seria a home ler a tabela em tempo de execucao
    para posicao dos itens. Como os itens dela ja comecam em y=19 — o
    mesmo valor da tabela — o ganho visual e zero hoje.

    **Ressalva honesta:** a posicao dos itens da home continua em tabela
    de coordenadas (`0x00C4867C`, `0x00C486A0`), ligada em tempo de
    patch, nao de execucao. Se `inicio_lista` ou `altura_linha` mudarem
    na tabela, as coordenadas da home precisam ser regeradas junto. Isso
    esta ANOTADO como divida, nao resolvido.

COMO

    Um gancho, no `bl lv_obj_set_style_bg_color` do widget da home:

        0x0012EC3E   bl 0xd4d092   ->   bl <rotina>

    A rotina faz o `bg_color` que ja fazia e, em seguida:

        tela = lv_disp_get_scr_act()
        faixa = 0x00D216F0(tela)        <- o MESMO helper das 36
        0x00DA5300(faixa)               <- altura vinda da TABELA

    A faixa nasce depois do widget da home, entao e desenhada por cima —
    e antes do relogio/titulo/bateria, que a camada VIEW cria depois da
    pagina, e portanto ficam acima dela. A ordem sai certa sozinha.

USO
    python3 tools/patch_saturno_s4.py \\
        --in  firmware/WORKING/GN438_openpod_v062.bin \\
        --out firmware/WORKING/GN438_openpod_v063.bin [--dry-run]

DEPENDENCIAS
    Python 3 + capstone

SEGURANCA
    - exige que o ponto de gancho seja exatamente o `bl bg_color` da home;
    - exige area livre virgem;
    - confere cada instrucao montada COM OPERANDOS;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.

LIMITACOES
    Depois deste patch a faixa da home fica DESENHADA DUAS VEZES: o objeto
    novo por cima dos pixels da folha. Como as duas ocupam y 0..16 e a
    folha ja tem as cores da tabela, o resultado e identico — mas e
    desperdicio, e o S5 e quem limpa a folha. **Separado de proposito:**
    se algo sair errado, da para saber se foi o objeto ou a folha.
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

BG_COLOR = 0xD4D092
CRIA_FAIXA = 0xD216F0          # o helper compartilhado por 50 telas
FAIXA_H = 0xDA5300             # thunk do S2: altura vinda da tabela
PRE_SCR = 0xD56898             # o firmware chama isto antes de pegar a tela
SCR_ACT = 0xD46E24             # lv_disp_get_scr_act

GANCHO = 0x0012EC3E
GANCHO_ESPERADO = bytes.fromhex("1ef028fa")     # bl 0xd4d092

BLOB = 0x001A5600
BLOB_MAX = 0x100


def bl(origem, destino, link=True):
    off = destino - (origem + 4)
    if off & 1 or not (-(1 << 24) <= off < (1 << 24)):
        raise ValueError("fora de alcance")
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = ((0xD000 if link else 0x9000)
           | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def monta(base):
    c = bytearray()

    def h(*hw):
        for x in hw:
            c.extend(struct.pack("<H", x))

    def call(alvo):
        c.extend(bl(base + len(c), alvo))

    h(0xB500)            # push {lr}
    call(BG_COLOR)       # o bg_color que a home ja fazia (r0,r1,r2 intactos)
    call(PRE_SCR)
    call(SCR_ACT)        # r0 = tela ativa
    call(CRIA_FAIXA)     # r0 = faixa, criada pelo helper compartilhado
    call(FAIXA_H)        # altura vinda da tabela de tema
    h(0xBD00)            # pop {pc}
    return bytes(c)


ESPERADO = ["push {lr}", "bl #0xd4d092", "bl #0xd56898", "bl #0xd46e24",
            "bl #0xd216f0", "bl #0xda5300", "pop {pc}"]


def main():
    ap = argparse.ArgumentParser(description="Saturno S4: a home na carcaça")
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
    if bytes(data[GANCHO:GANCHO + 4]) != GANCHO_ESPERADO:
        erros.append(f"0x{GANCHO:06X} e {bytes(data[GANCHO:GANCHO+4]).hex()}, "
                     f"esperado {GANCHO_ESPERADO.hex()} (bl bg_color da home)")
    if any(x != 0xFF for x in data[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB:06X} nao esta virgem")

    rot = monta(BLOB + XIP)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    got = [f"{i.mnemonic} {i.op_str}".strip()
           for i in md.disasm(rot, BLOB + XIP)]
    if got != ESPERADO:
        erros.append(f"rotina nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")

    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print("  SATURNO S4 — a home entra na carcaça")
    print()
    print("  a faixa da home passa a ser o MESMO objeto das outras 36:")
    print(f"    0x{CRIA_FAIXA:08X}  helper compartilhado (50 telas)")
    print(f"    0x{FAIXA_H:08X}  altura vinda da tabela de tema")
    print()
    print("  NAO reescreve page_home_create — ver o cabecalho da ferramenta.")
    print("  A faixa fica desenhada DUAS vezes ate o S5 limpar a folha.")
    print()
    print("  ALTERACOES")
    data[BLOB:BLOB + len(rot)] = rot
    print(f"    0x{BLOB:06X}  rotina {len(rot)} B")
    data[GANCHO:GANCHO + 4] = bl(GANCHO + XIP, BLOB + XIP)
    print(f"    0x{GANCHO:06X}  bl bg_color -> bl 0x{BLOB + XIP:08X}")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X} (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}  "
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
