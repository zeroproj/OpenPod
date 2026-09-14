#!/usr/bin/env python3
"""
patch_scrollbar.py — Tira a barra de rolagem da home.

POR QUE ELA APARECE

    A V025 contornou um defeito mantendo 9 objetos e escondendo 5 deles
    em y=200 -- fora da tela, mas AINDA DENTRO do conteiner. Para a LVGL
    o conteudo passa a ter 200+ px de altura num conteiner de 160, entao
    ela desenha a barra de rolagem. Efeito colateral, nao decisao.

    Confirmado: a folha de fundo nao tem linha vertical nenhuma nas
    colunas 122..127. A barra e desenhada em tempo de execucao.

A CORRECAO

    Limpar `LV_OBJ_FLAG_SCROLLABLE` (0x10) do conteiner. Sem rolagem, sem
    barra. A home nao precisa rolar: a navegacao e por indice, e os 4
    itens visiveis cabem na tela.

        lv_obj_add_flag     0x00D49204   (orrs  [r4,#0x1c])
        lv_obj_clear_flag   0x00D4924A   (bic.w [r4,#0x1c])

    Os dois foram identificados por desmontagem: mesma estrutura, mesmo
    campo de flags, um com OR e outro com BIC.

O GANCHO

    0x0012EC0E   bl 0x00D4A21A   set_size(conteiner, w, h)

    `set_size` retorna void e e chamado uma unica vez sobre o conteiner,
    entao desviar essa chamada e seguro. A rotina na area livre faz a
    chamada original e depois limpa a flag.

O QUE E ALTERADO

    0x0012EC0E    4 B   bl set_size -> bl <rotina>
    area livre   14 B   a rotina (FORA da FIRM, nao afeta o CRC)

USO
    python3 tools/patch_scrollbar.py \
        --in  firmware/WORKING/GN438_openpod_v033.bin \
        --out firmware/WORKING/GN438_openpod_v034.bin [--dry-run]

SEGURANCA
    - recusa se o gancho nao apontar hoje para set_size;
    - acha sozinho o proximo endereco livre e recusa se nao estiver virgem;
    - recusa se a rotina cair dentro da FIRM (afetaria o CRC);
    - decodifica de volta os dois saltos e compara os alvos;
    - recusa se algum setor alterado for <= 0x00D000.
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
HOOK = 0x0012EC0E
SET_SIZE = 0x00D4A21A
CLEAR_FLAG = 0x00D4924A
SCROLLABLE = 0x10
LIVRE_INI, LIVRE_FIM = 0x001A3038, 0x001FC000
FIRM_FIM = 0x00E000 + 0x192570
PROIBIDO = 0x0000D000


def enc(origem, destino, link):
    off = destino - (origem + 4)
    if not -(1 << 24) <= off < (1 << 24) or off & 1:
        raise ValueError("fora de alcance")
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack("<HH", 0xF000 | (s << 10) | ((off >> 12) & 0x3FF),
                       (0xD000 if link else 0x9000) | (j1 << 13) | (j2 << 11)
                       | ((off >> 1) & 0x7FF))


def dec(origem, blob):
    h1, h2 = struct.unpack("<HH", blob)
    s = (h1 >> 10) & 1
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if s:
        off -= 1 << 25
    return origem + 4 + off, bool(h2 & 0x4000)


def proximo_livre(d):
    fim = LIVRE_INI
    for i in range(LIVRE_INI, LIVRE_INI + 0x4000):
        if d[i] != 0xFF:
            fim = i + 1
    return (fim + 3) & ~3


def main():
    ap = argparse.ArgumentParser(description="Tira a barra de rolagem da home")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — sem barra de rolagem na home")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    alvo, link = dec(HOOK + XIP, bytes(d[HOOK:HOOK + 4]))
    if (alvo, link) != (SET_SIZE, True):
        print(f"  ABORTADO: 0x{HOOK:06X} aponta para 0x{alvo:08X} "
              f"(link={link}), esperado bl set_size 0x{SET_SIZE:08X}",
              file=sys.stderr)
        return 1
    rot = proximo_livre(d)
    if rot < FIRM_FIM:
        print("  ABORTADO: a rotina cairia dentro da FIRM.", file=sys.stderr)
        return 1
    if any(b != 0xFF for b in d[rot:rot + 0x20]):
        print(f"  ABORTADO: 0x{rot:06X} nao esta virgem.", file=sys.stderr)
        return 1
    print(f"  gancho 0x{HOOK:06X} -> bl set_size   OK")
    print(f"  area livre: proximo endereco 0x{rot:06X} "
          f"(XIP 0x{rot + XIP:08X}), virgem  OK")
    print()

    corpo = bytearray()
    corpo += struct.pack("<H", 0xB501)                    # push {r0, lr}
    corpo += enc(rot + XIP + 0x02, SET_SIZE, True)        # bl set_size
    corpo += struct.pack("<H", 0x9800)                    # ldr r0, [sp]
    corpo += struct.pack("<H", 0x2000 | SCROLLABLE)       # movs r1, #0x10 -> corrigido abaixo
    corpo[-2:] = struct.pack("<H", 0x2100 | SCROLLABLE)   # movs r1, #0x10
    corpo += enc(rot + XIP + 0x0A, CLEAR_FLAG, True)      # bl clear_flag
    corpo += struct.pack("<H", 0xBD01)                    # pop {r0, pc}
    assert len(corpo) == 0x10
    d[rot:rot + len(corpo)] = corpo
    novo = enc(HOOK + XIP, rot + XIP, True)
    d[HOOK:HOOK + 4] = novo

    print("  ROTINA")
    linhas = [(0x00, "push  {r0, lr}", "preserva o conteiner e o retorno"),
              (0x02, "bl    0x%08X" % SET_SIZE, "set_size original"),
              (0x06, "ldr   r0, [sp]", "recupera o conteiner"),
              (0x08, "movs  r1, #0x%02X" % SCROLLABLE, "LV_OBJ_FLAG_SCROLLABLE"),
              (0x0A, "bl    0x%08X" % CLEAR_FLAG, "lv_obj_clear_flag"),
              (0x0E, "pop   {r0, pc}", "volta")]
    for off, asm, com in linhas:
        n = 4 if off in (0x02, 0x0A) else 2
        print(f"    +0x{off:02X}  {bytes(corpo[off:off+n]).hex():<8}  "
              f"{asm:<20} ; {com}")
    print()

    t1, l1 = dec(rot + XIP + 0x02, bytes(corpo[0x02:0x06]))
    t2, l2 = dec(rot + XIP + 0x0A, bytes(corpo[0x0A:0x0E]))
    t3, l3 = dec(HOOK + XIP, bytes(novo))
    ok = (t1, l1) == (SET_SIZE, True) and (t2, l2) == (CLEAR_FLAG, True) \
        and (t3, l3) == (rot + XIP, True)
    print("  conferencia dos saltos (decodificando de volta):")
    print(f"    bl set_size   -> 0x{t1:08X} link={l1}")
    print(f"    bl clear_flag -> 0x{t2:08X} link={l2}")
    print(f"    gancho        -> 0x{t3:08X} link={l3}")
    if not ok:
        print("  ABORTADO: codificacao nao confere.", file=sys.stderr)
        return 1
    print("    todos conferem  OK")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido.", file=sys.stderr)
        return 1
    print(f"  tabela de particoes (0x{PROIBIDO:06X}) NAO tocada   OK")
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
