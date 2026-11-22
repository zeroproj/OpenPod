#!/usr/bin/env python3
"""fab_reload_3_5.py - o player na tela inicial (ficha 028).

Entrada: a 3.3 publicada, sha256
368a7c8c98f6b6b68c7e38853a69673bb05d5216219406f8ccdc9a858a73713d.

Saida: a mesma imagem com:

  - o SDK `jogos35` (sdk/src + sdk/player) escrito em 0x1AB000..0x1FC000;
  - o gancho do menu em 0xD23CF8 -> hook_home_menu_create (0xDAB000);
  - o gancho da home em 0xD23B8C -> hook_home_create (0xDAB200);
  - o gancho do titulo em 0xD3225E -> fw_player_title_hook (0xDAB600);
  - o gancho do label da home em 0xD2EEE4 ->
    fw_player_title_hook_home_wrap (0xDAB700);
  - as tres faixas de icones movidas para 19..52, 58..93 e 97..132;
  - a tabela de posicoes das molduras em 0x486A0 nas posicoes novas.

Premissas: a 3.3 exata (sha), os quatro ganchos/bytes, o lote do SDK 3.3
com o resto em 0xFF, a folha/paleta (preto 16) e a tabela; `--out` nao e a
entrada. So se escreve no lote do SDK, nos quatro ganchos, na tabela
0x486A0..0x486C4 e nos pixels 0x0CE15C..0x0D315C.

Uso: python3 tools/fab_reload_3_5.py --in <3.3.bin> --out <3.5.bin>
                                    [--dry-run]
Dependencias: Python 3 + zig (build_sdk) + capstone.
"""

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import build_sdk  # noqa: E402
import capa_album_asm as A  # noqa: E402

XIP = 0x00C00000
TAMANHO = 0x200000
SHA_ENTRADA = ("368a7c8c98f6b6b68c7e38853a69673bb05d5216219406f8ccd"
               "c9a858a73713d")

LOTE_INI, LOTE_FIM = 0x1AB000, 0x1FC000
SDK_BASE = 0xDAB000
OLD_SDK_TAM = 11868
OLD_SDK_SHA = ("58611dd86c3878a7e92c06e4c72f3625d681c4a302e437465987"
               "f916f2990c6a")

PATCH_MENU = 0xD23CF8
PATCH_HOME = 0xD23B8C
PATCH_TITLE = 0xD3225E
PATCH_HOME_LABEL = 0xD2EEE4
MENU_FAB = 0xDAD23C
HOME_FAB = 0xD2EBB8
TITLE_FAB = 0xDAA014
BYTES_MENU = bytes.fromhex("89f0a0fa")
BYTES_HOME = bytes.fromhex("0bf014f8")
BYTES_TITLE = bytes.fromhex("77f0d9be")
BYTES_HOME_LABEL = bytes.fromhex("094b1b78")
LITERAL_HOME = 0xD2EF0C
LITERAL_HOME_VAL = 0x00823EB0

TABLE = 0x486A0
TABLE_FAB = [(5, 27), (46, 27), (87, 27),
             (5, 70), (46, 70), (87, 70),
             (5, 114), (46, 114), (87, 114)]
TABLE_NOVO = [(5, 17), (46, 17), (87, 17),
              (5, 58), (46, 58), (87, 58),
              (5, 97), (46, 97), (87, 97)]

SHEET_PAL, SHEET_PX = 0x0CDD5C, 0x0CE15C
SHEET_W, SHEET_H, SHEET_BARRA = 128, 160, 16
SHEET_SHA = ("e1449e41d88ad8bc608eb14b717ce109233ab9987e10343d49026"
             "1d8018d468f")
PAL_SHA = ("94df91f4840dc1153ea9c4a1729aa5144f94b47bf610c03d234c78"
           "79504a192e")
BLACK_IDX = 16
FAIXAS = ((29, 34, 19), (70, 36, 58), (114, 36, 97))


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def mesma_entrada(src, dst):
    if os.path.abspath(src) == os.path.abspath(dst):
        return True
    if not os.path.lexists(dst):
        return False
    try:
        return os.path.samefile(src, dst)
    except OSError:
        return False


def indice_preto(pal):
    achados = [i for i in range(256)
               if pal[i * 4:i * 4 + 3] == b"\0\0\0" and pal[i * 4 + 3] == 255]
    if not achados:
        raise ValueError("a paleta nao tem um preto exato (0,0,0,255)")
    return achados[0]


def folha_nova(px, pal):
    """As faixas movidas, o resto preto, a paleta intocada."""
    k = indice_preto(pal)
    velho = bytes(px)
    novo = bytearray(velho)
    for y in range(SHEET_BARRA, SHEET_H):
        novo[SHEET_W * y:SHEET_W * (y + 1)] = bytes([k]) * SHEET_W
    for antigo, altura, novo_topo in FAIXAS:
        novo[SHEET_W * novo_topo:SHEET_W * (novo_topo + altura)] = \
            velho[SHEET_W * antigo:SHEET_W * (antigo + altura)]
    return bytes(novo), k


def confere_premissas(d):
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} B, esperado {TAMANHO} (2 MiB)"]
    got = sha(d)
    if got != SHA_ENTRADA:
        erros.append(f"sha256 da entrada {got[:16]}..., esperado "
                     f"{SHA_ENTRADA[:16]}... (a 3.3 publicada)")

    for nome, addr, esperado, alvo in (
            ("menu", PATCH_MENU, BYTES_MENU, MENU_FAB),
            ("home", PATCH_HOME, BYTES_HOME, HOME_FAB),
            ("titulo", PATCH_TITLE, BYTES_TITLE, TITLE_FAB)):
        off = addr - XIP
        if bytes(d[off:off + 4]) != esperado:
            erros.append(f"{nome}: 0x{addr:06X} nao tem os bytes da 3.3")
            continue
        lido = A.desvio(d, off)
        if not lido or lido[1] != alvo:
            erros.append(f"{nome}: o desvio de 0x{addr:06X} nao vai a "
                         f"0x{alvo:06X} ({lido})")
    off = PATCH_HOME_LABEL - XIP
    if bytes(d[off:off + 4]) != BYTES_HOME_LABEL:
        erros.append(f"label da home: 0x{PATCH_HOME_LABEL:06X} nao tem o "
                     f"ldr da 3.3")
    lit = struct.unpack_from("<I", d, LITERAL_HOME - XIP)[0]
    if lit != LITERAL_HOME_VAL:
        erros.append(f"o literal de 0x{LITERAL_HOME:06X} e 0x{lit:08X}, "
                     f"esperado 0x{LITERAL_HOME_VAL:08X}")

    lida = [struct.unpack_from("<hh", d, TABLE + i * 4)
            for i in range(9)]
    if [tuple(p) for p in lida] != TABLE_FAB:
        erros.append(f"a tabela de 0x{TABLE:06X} nao e a da 3.3: {lida}")

    pal = bytes(d[SHEET_PAL:SHEET_PX])
    px = bytes(d[SHEET_PX:SHEET_PX + SHEET_W * SHEET_H])
    if sha(pal) != PAL_SHA:
        erros.append("a paleta da folha nao e a da 3.3")
    if sha(px) != SHEET_SHA:
        erros.append("os pixels da folha nao sao os da 3.3")
    try:
        k = indice_preto(pal)
        if k != BLACK_IDX:
            erros.append(f"o preto da paleta e o indice {k}, esperado "
                         f"{BLACK_IDX}")
    except ValueError as e:
        erros.append(str(e))

    velho = bytes(d[LOTE_INI:LOTE_INI + OLD_SDK_TAM])
    if sha(velho) != OLD_SDK_SHA:
        erros.append("o SDK da 3.3 em 0x1AB000 nao tem o sha esperado")
    if any(b != 0xFF for b in d[LOTE_INI + OLD_SDK_TAM:LOTE_FIM]):
        erros.append("o resto do lote do SDK nao esta virgem (0xFF)")
    return erros


def patch_sdk(sdk):
    """Troca os dois `b.w .` dos wrappers pela cauda certa.

    O assembler nao aceita um alvo absoluto numerico no `b.w` inline (o
    linker o trata como offset de secao); por isso o SDK nasce com
    `b.w .` e a ferramenta escreve o desvio depois, com o encoder Thumb-2.
    """
    sdk = bytearray(sdk)
    for ini, alvo in ((0xDAB600, 0xDAA014), (0xDAB700, 0xD2EEE8)):
        base = ini - 0xDAB000
        for off in range(base, base + 0x40, 2):
            lido = A.desvio(sdk, off, base=SDK_BASE)
            if lido and lido[0] == "b.w" and lido[1] == SDK_BASE + off:
                sdk[off:off + 4] = A.enc(SDK_BASE + off, alvo, False)
                break
        else:
            raise SystemExit(f"PARE: o wrapper 0x{ini:06X} nao tem o b.w .")
    return bytes(sdk)


def monta(d, sdk_bin, symbols):
    novo = bytearray(d)
    novo[LOTE_INI:LOTE_FIM] = b"\xFF" * (LOTE_FIM - LOTE_INI)
    novo[LOTE_INI:LOTE_INI + len(sdk_bin)] = sdk_bin

    novo[PATCH_MENU - XIP:PATCH_MENU - XIP + 4] = A.enc(
        PATCH_MENU, symbols["hook_home_menu_create"], True)
    novo[PATCH_HOME - XIP:PATCH_HOME - XIP + 4] = A.enc(
        PATCH_HOME, symbols["hook_home_create"], True)
    novo[PATCH_TITLE - XIP:PATCH_TITLE - XIP + 4] = A.enc(
        PATCH_TITLE, symbols["fw_player_title_hook"], False)
    novo[PATCH_HOME_LABEL - XIP:PATCH_HOME_LABEL - XIP + 4] = A.enc(
        PATCH_HOME_LABEL, symbols["fw_player_title_hook_home_wrap"], False)

    novo[TABLE:TABLE + 36] = struct.pack(
        "<18h", *[v for p in TABLE_NOVO for v in p])

    pal = bytes(d[SHEET_PAL:SHEET_PX])
    px = bytes(d[SHEET_PX:SHEET_PX + SHEET_W * SHEET_H])
    px_novo, _ = folha_nova(px, pal)
    novo[SHEET_PX:SHEET_PX + SHEET_W * SHEET_H] = px_novo
    return bytes(novo)


def confere_saida(d, novo, sdk_bin, symbols):
    erros = []
    if novo[LOTE_INI:LOTE_INI + len(sdk_bin)] != sdk_bin:
        erros.append("o SDK escrito nao e o app.bin")
    if any(b != 0xFF for b in novo[LOTE_INI + len(sdk_bin):LOTE_FIM]):
        erros.append("o resto do lote do SDK nao ficou 0xFF")
    for nome, addr, alvo, largo in (
            ("menu", PATCH_MENU, symbols["hook_home_menu_create"], True),
            ("home", PATCH_HOME, symbols["hook_home_create"], True),
            ("titulo", PATCH_TITLE, symbols["fw_player_title_hook"], False),
            ("label da home", PATCH_HOME_LABEL,
             symbols["fw_player_title_hook_home_wrap"], False)):
        lido = A.desvio(novo, addr - XIP)
        if not lido or lido[1] != alvo:
            erros.append(f"{nome}: a saida de 0x{addr:06X} nao vai a "
                         f"0x{alvo:06X} ({lido})")
        if lido and (lido[0] == "bl") != largo:
            erros.append(f"{nome}: tipo de desvio errado ({lido[0]})")
    for ini, alvo in ((0xDAB600, 0xDAA014), (0xDAB700, 0xD2EEE8)):
        base = ini - 0xDAB000
        if not any(A.desvio(sdk_bin, off, base=SDK_BASE) == ("b.w", alvo)
                   for off in range(base, base + 0x40, 2)):
            erros.append(f"o wrapper 0x{ini:06X} nao tem a cauda 0x{alvo:06X}")
    lida = [tuple(struct.unpack_from("<hh", novo, TABLE + i * 4))
            for i in range(9)]
    if lida != TABLE_NOVO:
        erros.append(f"a tabela da saida nao e a nova: {lida}")
    pal = bytes(d[SHEET_PAL:SHEET_PX])
    px = bytes(d[SHEET_PX:SHEET_PX + SHEET_W * SHEET_H])
    esperado, _ = folha_nova(px, pal)
    if novo[SHEET_PX:SHEET_PX + SHEET_W * SHEET_H] != esperado:
        erros.append("a folha da saida nao e a folha_nova")

    permitido = ((LOTE_INI, LOTE_FIM),
                 (PATCH_MENU - XIP, PATCH_MENU - XIP + 4),
                 (PATCH_HOME - XIP, PATCH_HOME - XIP + 4),
                 (PATCH_TITLE - XIP, PATCH_TITLE - XIP + 4),
                 (PATCH_HOME_LABEL - XIP, PATCH_HOME_LABEL - XIP + 4),
                 (TABLE, TABLE + 36),
                 (SHEET_PX, SHEET_PX + SHEET_W * SHEET_H))
    dif = [i for i in range(len(d)) if d[i] != novo[i]]
    fora = [i for i in dif if not any(a <= i < b for a, b in permitido)]
    if fora:
        erros.append(f"escreveu fora do permitido: 0x{min(fora):06X}.."
                     f"0x{max(fora):06X} ({len(fora)} B)")
    if dif and min(dif) < 0xE000:
        erros.append(f"escreveu abaixo de 0xE000: 0x{min(dif):06X}")
    if any(0xD000 <= i < 0xE000 for i in dif):
        erros.append("tocou no setor 0xD000")
    if any(i >= 0x1FC000 for i in dif):
        erros.append("tocou na PSMP (0x1FC000+)")
    return erros, dif


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="entrada", required=True)
    ap.add_argument("--out", dest="saida", required=True)
    ap.add_argument("--em", default=None, help="lote; so 0x1AB000")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.em is not None and int(a.em, 0) != LOTE_INI:
        sys.exit(f"PARE: --em {a.em} difere do lote fixo 0x{LOTE_INI:06X}")
    if mesma_entrada(a.entrada, a.saida):
        sys.exit("PARE: --out e a propria entrada")

    with open(a.entrada, "rb") as f:
        d = f.read()
    erros = confere_premissas(d)
    if erros:
        sys.stderr.write("PARE: premissas falharam.\n")
        for e in erros:
            sys.stderr.write(f"  - {e}\n")
        return 1

    tmp = tempfile.mkdtemp(prefix="openpod_35_")
    try:
        out = os.path.join(tmp, "sdk")
        build_sdk.build("jogos35", out)
        sdk_bin = patch_sdk(open(os.path.join(out, "app.bin"), "rb").read())
        info = json.load(open(os.path.join(out, "app.json")))
        symbols = {k: v for k, v in info["symbols"].items()}
        if len(sdk_bin) > LOTE_FIM - LOTE_INI:
            sys.exit("PARE: o SDK nao cabe no lote 0x1AB000..0x1FC000")
        for nome in ("hook_home_menu_create", "hook_home_create",
                     "fw_player_title_hook",
                     "fw_player_title_hook_home_wrap"):
            if nome not in symbols:
                sys.exit(f"PARE: o SDK nao exporta {nome}")

        novo = monta(d, sdk_bin, symbols)
        erros, dif = confere_saida(d, novo, sdk_bin, symbols)
        if erros:
            sys.stderr.write("PARE: a conferencia da saida falhou.\n")
            for e in erros:
                sys.stderr.write(f"  - {e}\n")
            return 1

        print(f"entrada: {sha(d)}")
        print(f"SDK jogos35: {len(sdk_bin)} B, sha {sha(sdk_bin)}")
        print(f"  menu      0x{PATCH_MENU:06X} -> "
              f"0x{symbols['hook_home_menu_create']:06X}")
        print(f"  home      0x{PATCH_HOME:06X} -> "
              f"0x{symbols['hook_home_create']:06X}")
        print(f"  titulo    0x{PATCH_TITLE:06X} -> "
              f"0x{symbols['fw_player_title_hook']:06X}")
        print(f"  label     0x{PATCH_HOME_LABEL:06X} -> "
              f"0x{symbols['fw_player_title_hook_home_wrap']:06X}")
        print(f"  folha: faixas {FAIXAS[0][2]}..{FAIXAS[0][2] + FAIXAS[0][1]},"
              f" {FAIXAS[1][2]}..{FAIXAS[1][2] + FAIXAS[1][1]},"
              f" {FAIXAS[2][2]}..{FAIXAS[2][2] + FAIXAS[2][1]}")
        print(f"  tabela: {TABLE_NOVO}")
        print(f"saida: {sha(novo)} ({len(dif)} B diferentes)")
        if a.dry_run:
            print("dry-run: nada gravado")
            return 0
        with open(a.saida, "wb") as f:
            f.write(novo)
        print(f"gravado: {a.saida}")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
