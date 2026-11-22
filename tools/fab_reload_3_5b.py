#!/usr/bin/env python3
"""fab_reload_3_5b.py - o nome da musica no cartao da home (ficha 028b).

Entrada: a 3.5 publicada (a imagem do kit "Reload 3.5 Diag"), sha256
f49c819534a12756ed1ee72fbda4444cf4dadd627c164c85faa48131d4b1d05d.

Saida: a mesma imagem com o SDK `jogos35b` no lugar do SDK `jogos35`:

  - o gancho da home (0xD2EEE4) passa a ler o indice do elemento da
    mensagem (o halfword de msg+4): 1 e o titulo da faixa, 0 e o contador
    da fila.  Antes ele copiava qualquer tipo 3 como titulo, e o contador
    (que a fabrica manda logo depois do titulo) ficava por cima;
  - o gancho do titulo (0xD3225E) filtra [view+4] (o rotulo do titulo) e
    nao [view+0] (o rotulo do contador da fila).

Prova no ORIGINAL: docs/tarefas/028b-analise.md.

O resto da imagem (os quatro ganchos, a tabela das molduras, a folha dos
icones) fica byte a byte: a diferenca e SO o lote do SDK
(0x1AB000..0x1FC000).

Premissas: a 3.5 exata (sha), os quatro ganchos, o SDK antigo com o sha
esperado, o resto do lote em 0xFF e `--out` diferente da entrada. So se
escreve no lote do SDK.

Uso: python3 tools/fab_reload_3_5b.py --in <3.5.bin> --out <3.5b.bin>
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
SHA_ENTRADA = ("f49c819534a12756ed1ee72fbda4444cf4dadd627c164c85faa481"
               "31d4b1d05d")

LOTE_INI, LOTE_FIM = 0x1AB000, 0x1FC000
SDK_BASE = 0xDAB000
OLD_SDK_TAM = 13944
OLD_SDK_SHA = ("ee4636f4b21067bf59032adb0e17513e6df7d829f70d3276274157e"
               "4ad34af66")

# os quatro ganchos que a 3.5 ja tem (o destino e o SDK, que nao muda)
PATCH_MENU = 0xD23CF8
PATCH_HOME = 0xD23B8C
PATCH_TITLE = 0xD3225E
PATCH_HOME_LABEL = 0xD2EEE4
ALVO_MENU = 0xDAB000
ALVO_HOME = 0xDAB200
ALVO_TITLE = 0xDAB600
ALVO_HOME_LABEL = 0xDAB700

# as caudas dos dois wrappers: o TITULO da capa e o `cmp r3,#3` da home
CAUDA_TITLE = 0xDAA014
CAUDA_HOME_LABEL = 0xD2EEE8


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


def confere_premissas(d):
    """Confere a imagem de entrada antes de escrever qualquer coisa."""
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} B, esperado {TAMANHO} (2 MiB)"]
    got = sha(d)
    if got != SHA_ENTRADA:
        erros.append(f"sha256 da entrada {got[:16]}..., esperado "
                     f"{SHA_ENTRADA[:16]}... (a 3.5 publicada)")

    for nome, addr, alvo, largo in (
            ("menu", PATCH_MENU, ALVO_MENU, True),
            ("home", PATCH_HOME, ALVO_HOME, True),
            ("titulo", PATCH_TITLE, ALVO_TITLE, False),
            ("label da home", PATCH_HOME_LABEL, ALVO_HOME_LABEL, False)):
        lido = A.desvio(d, addr - XIP)
        if not lido or lido[1] != alvo:
            erros.append(f"{nome}: o desvio de 0x{addr:06X} nao vai a "
                         f"0x{alvo:06X} ({lido})")
        elif (lido[0] == "bl") != largo:
            erros.append(f"{nome}: tipo de desvio errado em 0x{addr:06X} "
                         f"({lido[0]})")

    velho = bytes(d[LOTE_INI:LOTE_INI + OLD_SDK_TAM])
    if sha(velho) != OLD_SDK_SHA:
        erros.append("o SDK da 3.5 em 0x1AB000 nao tem o sha esperado")
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
    for ini, alvo in ((0xDAB600, CAUDA_TITLE), (0xDAB700, CAUDA_HOME_LABEL)):
        base = ini - 0xDAB000
        for off in range(base, base + 0x40, 2):
            lido = A.desvio(sdk, off, base=SDK_BASE)
            if lido and lido[0] == "b.w" and lido[1] == SDK_BASE + off:
                sdk[off:off + 4] = A.enc(SDK_BASE + off, alvo, False)
                break
        else:
            raise SystemExit(f"PARE: o wrapper 0x{ini:06X} nao tem o b.w .")
    return bytes(sdk)


def monta(d, sdk_bin):
    """Escreve o SDK novo no lote; nada mais da imagem muda."""
    novo = bytearray(d)
    novo[LOTE_INI:LOTE_FIM] = b"\xFF" * (LOTE_FIM - LOTE_INI)
    novo[LOTE_INI:LOTE_INI + len(sdk_bin)] = sdk_bin
    return bytes(novo)


def confere_saida(d, novo, sdk_bin):
    """Confere a saida: a diff so no lote do SDK, e o resto igual."""
    erros = []
    if novo[LOTE_INI:LOTE_INI + len(sdk_bin)] != sdk_bin:
        erros.append("o SDK escrito nao e o app.bin")
    if any(b != 0xFF for b in novo[LOTE_INI + len(sdk_bin):LOTE_FIM]):
        erros.append("o resto do lote do SDK nao ficou 0xFF")

    for nome, addr, alvo, largo in (
            ("menu", PATCH_MENU, ALVO_MENU, True),
            ("home", PATCH_HOME, ALVO_HOME, True),
            ("titulo", PATCH_TITLE, ALVO_TITLE, False),
            ("label da home", PATCH_HOME_LABEL, ALVO_HOME_LABEL, False)):
        lido = A.desvio(novo, addr - XIP)
        if not lido or lido[1] != alvo:
            erros.append(f"{nome}: a saida de 0x{addr:06X} nao vai a "
                         f"0x{alvo:06X} ({lido})")
        elif (lido[0] == "bl") != largo:
            erros.append(f"{nome}: tipo de desvio errado em 0x{addr:06X} "
                         f"({lido[0]})")

    for ini, alvo in ((0xDAB600, CAUDA_TITLE),
                       (0xDAB700, CAUDA_HOME_LABEL)):
        base = ini - 0xDAB000
        if not any(A.desvio(sdk_bin, off, base=SDK_BASE) == ("b.w", alvo)
                   for off in range(base, base + 0x40, 2)):
            erros.append(f"o wrapper 0x{ini:06X} nao tem a cauda 0x{alvo:06X}")

    dif = [i for i in range(len(d)) if d[i] != novo[i]]
    fora = [i for i in dif if not (LOTE_INI <= i < LOTE_FIM)]
    if fora:
        erros.append(f"escreveu fora do lote do SDK: 0x{min(fora):06X}.."
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

    tmp = tempfile.mkdtemp(prefix="openpod_35b_")
    try:
        out = os.path.join(tmp, "sdk")
        build_sdk.build("jogos35b", out)
        sdk_bin = patch_sdk(open(os.path.join(out, "app.bin"), "rb").read())
        info = json.load(open(os.path.join(out, "app.json")))
        symbols = dict(info["symbols"])
        if len(sdk_bin) > LOTE_FIM - LOTE_INI:
            sys.exit("PARE: o SDK nao cabe no lote 0x1AB000..0x1FC000")
        for nome in ("hook_home_menu_create", "hook_home_create",
                     "fw_player_title_hook",
                     "fw_player_title_hook_home_wrap"):
            if nome not in symbols:
                sys.exit(f"PARE: o SDK nao exporta {nome}")

        novo = monta(d, sdk_bin)
        erros, dif = confere_saida(d, novo, sdk_bin)
        if erros:
            sys.stderr.write("PARE: a conferencia da saida falhou.\n")
            for e in erros:
                sys.stderr.write(f"  - {e}\n")
            return 1

        print(f"entrada: {sha(d)}")
        print(f"SDK jogos35b: {len(sdk_bin)} B, sha {sha(sdk_bin)}")
        print(f"  menu      0x{PATCH_MENU:06X} -> "
              f"0x{symbols['hook_home_menu_create']:06X} (como na 3.5)")
        print(f"  home      0x{PATCH_HOME:06X} -> "
              f"0x{symbols['hook_home_create']:06X} (como na 3.5)")
        print(f"  titulo    0x{PATCH_TITLE:06X} -> "
              f"0x{symbols['fw_player_title_hook']:06X} (como na 3.5)")
        print(f"  label     0x{PATCH_HOME_LABEL:06X} -> "
              f"0x{symbols['fw_player_title_hook_home_wrap']:06X} "
              f"(como na 3.5)")
        print(f"  a cauda do titulo vai para 0x{CAUDA_TITLE:06X} "
              f"(TITULO da capa)")
        print(f"  a cauda do label da home vai para 0x{CAUDA_HOME_LABEL:06X} "
              f"(o cmp r3,#3 da fabrica)")
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
