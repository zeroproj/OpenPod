#!/usr/bin/env python3
r"""
fab_diag_b3.py — o degrau B3 da ficha 011 (RC7: duas tarefas).

A ficha 011 mediu que o `get_path` na ViewTask reinicia o aparelho (B) e
que o monitor do watchdog e o que o leva ao reset (B2). O B3 tira o
`get_path` da ViewTask sem inventar RAM: a mensagem que o `0xD084F8` manda
ja leva o caminho em `+0x14`; o `page_music_play_label_process`
(0x00D32204) passa esse texto em `r1` para o TITULO, que o guarda em `r5`.
O B3 troca a chamada do `get_path` (0x001AA144) por uma copia desse `r5`
para `ext+0x110` (a mesma RAM que o `get_path` usava; `ext` =
[[[0x81CE2C]+0xAC]+0x30], como no TITULO em 0x00DAA10C..0x00DAA11A).
Sem `f_open`, sem JPEG, sem heap novo, sem escrita na flash XIP.

O codigo novo e ASSEMBLY Thumb-2 (tools/diag_b3.s, montado pelo clang via
tools/asm.py), para a saida ser reproduzivel.

PATCH (dois pontos + o codigo novo)

    1. 0x001AA144 (10 B): `movw/movt + blx get_path` -> `mov r0,r2` +
       `mov r1,r5` + `bl copia_path` + `nop`;
    2. 0x001AA188 (4 B): `bl carrega_capa` -> `movs r0, #0` + `nop`;
    3. 0x001AAA00: o blob (copia_path em 0xDAAA00).
    A captura 0x001088D8 (`bl 0xD084F8`) NAO e tocada: o caminho continua
    sendo mandado pela MainTask.

PREMISSAS, conferidas ANTES de escrever (senao recusa sem criar a saida)

    - 2 MiB e sha256 da RC7 exata (3af97713...);
    - a tabela 0x001AA010/14/18 decodifica para CRIA/TITULO/APAGA;
    - a captura de 0x001088D8 ainda chama 0xD084F8 (a fabrica);
    - o par movw/movt de 0x00CFEFC5 aparece 1x no lote, seguido do `blx`;
    - o prologo do `carrega_capa` e o `bl` que o chama estao no lugar;
    - 0x001AAA00..0x001AB000 esta virgem (0xFF) e o blob cabe.

SAIDA E SEGURANCA

    Depois de escrever, RELE e confere o `bl`/`nop`/`movs` novos e o blob.
    O diff so pode tocar as duas regioes e o blob. `--out` igual/symlink/
    hardlink da entrada e recusado. Nada abaixo de 0x00E000; setor 0x00D000
    e PSMP (0x001FC000+) intocados.

USO

    python3 tools/fab_diag_b3.py --in <rc7.bin> --out <b3.bin>
                                 [--em 0x1a8000] [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib) + clang (tools/asm.py) + tools/diag_trava_asm.py +
    tools/capa_album_asm.py. Nao abre USB, nao grava no aparelho.

LIMITACOES

    - so serve na RC7 exata; a saida ja patcheada e recusada;
    - o lote NAO e remontado: a RC7 fica byte a byte, salvo os 2 pontos e
      o blob.
"""

import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402
import diag_trava_asm as G  # noqa: E402
from asm import monta  # noqa: E402

TAMANHO = 0x200000
SHA_RC7 = G.SHA_RC7

# o codigo novo (arquivo / XIP)
BLOB = 0x1AAA00
BLOB_XIP = A.XIP + BLOB                 # 0x00DAAA00
BLOB_MAX = 0x600                        # a area livre ate 0x1AB000

# as duas regioes do patch (a captura 0x1088D8 fica da fabrica)
P_CAPTURA = 0x1088D8                    # `bl 0xD084F8` (fabrica; so confere)
P_GET_PATH = 0x1AA144                   # `movw/movt` + `blx get_path`
P_CARREGA = 0x1AA188                    # `bl carrega_capa`
FALHA_BL = b"\x00\x20\x00\xBF"          # movs r0, #0 + nop
NOP = b"\x00\xBF"
MOV_R0_R2 = b"\x10\x46"                 # mov r0, r2 (destino = ext+0x110)
MOV_R1_R5 = b"\x29\x46"                 # mov r1, r5 (origem = o caminho)
ALVO_CAPTURA = 0x00D084F8               # o `0xD084F8` da fabrica
CARREGA_CAPA = 0x00DAA256               # o alvo do `bl` de 0x001AA188
FONTE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "diag_b3.s")


# ---------------------------------------------------------------------------
# o codigo novo
# ---------------------------------------------------------------------------

def monta_blob():
    """Monta tools/diag_b3.s e devolve os bytes do .text."""
    with open(FONTE, "r") as f:
        return monta(f.read())


def confere_blob(cod):
    """O codigo novo tem de caber e ter a validacao do caminho."""
    erros = []
    if not cod:
        erros.append("o codigo novo esta vazio")
        return erros
    if len(cod) > BLOB_MAX:
        erros.append(f"o codigo novo tem {len(cod)} bytes e nao cabe na "
                     f"area livre ({BLOB_MAX} bytes)")
    for v in (0x2B30, 0x2B3A, 0x2B5C, 0x2B2F):   # cmp r3, #'0'/':'/'\\'/'/'
        if struct.pack("<H", v) not in cod:
            erros.append(f"o copia_path nao tem a validacao 0x{v:04X}")
    return erros


# ---------------------------------------------------------------------------
# premissas
# ---------------------------------------------------------------------------

def confere_premissas(d, cod):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != SHA_RC7:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{SHA_RC7[:16]}... — a receita e a RC7 exata mais esta "
                     f"ferramenta, e so ela entra")
    for i, alvo in enumerate(G.ENTRADAS):
        lido = A.desvio(d, G.TABELA + 4 * i)
        if lido is None or lido[0] != "b.w" or lido[1] != alvo:
            erros.append(f"a entrada {i} da tabela (0x{G.TABELA + 4 * i:06X}) "
                         f"nao e um b.w para 0x{alvo:08X} — o lote da RC7 "
                         f"nao esta no lugar")
    # 1. a captura da fabrica continua no lugar (nao e patcheada)
    lido = A.desvio(d, P_CAPTURA)
    if lido is not None and lido[0] == "bl" and lido[1] == BLOB_XIP:
        erros.append(f"o bl de 0x{P_CAPTURA:06X} ja aponta para o codigo "
                     f"novo (a imagem ja foi patcheada)")
    elif lido is None or lido[0] != "bl" or lido[1] != ALVO_CAPTURA:
        erros.append(f"em 0x{P_CAPTURA:06X} nao ha um bl para o "
                     f"0x{ALVO_CAPTURA:08X} da fabrica — o codigo mudou")
    # 2. a leitura: o par movw/movt do get_path, e o blx que o usa
    pares = G.acha_pares(d, G.GET_PATH)
    if len(pares) != 1:
        lido = A.desvio(d, P_GET_PATH + 4)
        if lido is not None and lido[0] == "bl" and lido[1] == BLOB_XIP:
            erros.append(f"o get_path de 0x{P_GET_PATH:06X} ja foi trocado "
                         f"pelo copia_path (a imagem ja foi patcheada)")
        else:
            erros.append(f"o par movw/movt que carrega 0x{G.GET_PATH:08X} "
                         f"aparece {len(pares)}x no codigo do lote, esperado 1")
    else:
        off = G.achado_unico(d, G.GET_PATH)
        if off != P_GET_PATH + 8:
            erros.append(f"o blx do get_path esta em 0x{off:06X}, esperado "
                         f"0x{P_GET_PATH + 8:06X}")
    # 3. a capa: o carrega_capa (prologo unico) e o bl que o chama
    if bytes(d[P_CARREGA:P_CARREGA + 4]) == FALHA_BL:
        erros.append(f"o bl do carrega_capa em 0x{P_CARREGA:06X} ja esta "
                     f"patcheado (movs r0, #0 + nop)")
    else:
        prologos = G.acha_carrega_capa(d)
        if len(prologos) != 1:
            erros.append(f"o prologo do carrega_capa aparece {len(prologos)}x "
                         f"no codigo do lote, esperado 1")
        else:
            alvo = prologos[0] + A.XIP
            bls = G.acha_bl_para(d, alvo)
            if len(bls) != 1:
                erros.append(f"o bl interno que chama o carrega_capa aparece "
                             f"{len(bls)}x no codigo do lote, esperado 1")
            elif bls[0] != P_CARREGA:
                erros.append(f"o bl do carrega_capa esta em 0x{bls[0]:06X}, "
                             f"esperado 0x{P_CARREGA:06X}")
    # 4. a area livre e o codigo novo
    if any(b != 0xFF for b in d[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"a area livre 0x{BLOB:06X}..0x{BLOB + BLOB_MAX:06X} "
                     f"nao esta virgem (todo 0xFF)")
    erros.extend(confere_blob(cod))
    return erros


# ---------------------------------------------------------------------------
# o patch
# ---------------------------------------------------------------------------

def bytes_do_patch(cod):
    """As (deslocamento, bytes novos) do B3, na ordem em que sao aplicadas."""
    leitura = (MOV_R0_R2 + MOV_R1_R5
               + A.enc(A.XIP + P_GET_PATH + 4, BLOB_XIP, True) + NOP)
    return [(P_GET_PATH, leitura),
            (P_CARREGA, FALHA_BL),
            (BLOB, cod)]


def confere_patch(d, cod):
    """Rele o patch e confere: os bytes novos e a decodificacao deles."""
    erros = []
    if bytes(d[P_GET_PATH:P_GET_PATH + 4]) != MOV_R0_R2 + MOV_R1_R5:
        erros.append(f"os 4 bytes de 0x{P_GET_PATH:06X} nao sao "
                     f"mov r0,r2 + mov r1,r5")
    lido = A.desvio(d, P_GET_PATH + 4)
    if lido is None or lido[0] != "bl" or lido[1] != BLOB_XIP:
        erros.append(f"o bl de 0x{P_GET_PATH + 4:06X} nao ficou um bl para "
                     f"0x{BLOB_XIP:08X}")
    if bytes(d[P_GET_PATH + 8:P_GET_PATH + 10]) != NOP:
        erros.append("o nop depois do bl do copia_path nao esta no lugar")
    if bytes(d[P_CARREGA:P_CARREGA + 4]) != FALHA_BL:
        erros.append("os 4 bytes do carrega_capa nao sao movs r0,#0 + nop")
    if bytes(d[BLOB:BLOB + len(cod)]) != cod:
        erros.append("o codigo novo nao ficou como o montado")
    erros.extend(confere_blob(cod))
    return erros


# ---------------------------------------------------------------------------
# a escrita
# ---------------------------------------------------------------------------

def mesma_entrada(src, dst):
    """--out aponta para a propria entrada? (mesmo caminho, symlink, hardlink)"""
    if os.path.abspath(src) == os.path.abspath(dst):
        return True
    if not os.path.lexists(dst):
        return False
    try:
        return os.path.samefile(src, dst)
    except OSError:
        return False


def main():
    ap = argparse.ArgumentParser(
        description="RC7: o degrau B3 da ficha 011 (o caminho sem get_path)")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", default=None,
                    help=f"endereco do lote (tem de ser {G.LOTE:#x})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.em is not None:
        try:
            em = int(a.em, 0)
        except ValueError:
            print(f"RECUSADO: --em {a.em!r} nao e um endereco.",
                  file=sys.stderr)
            return 2
        if em != G.LOTE:
            print(f"RECUSADO: --em {em:#x}; o lote desta ferramenta esta em "
                  f"{G.LOTE:#x} (e a receita passa esse endereco).",
                  file=sys.stderr)
            return 2
    if not os.path.exists(a.src):
        print(f"RECUSADO: {a.src} nao existe.", file=sys.stderr)
        return 2
    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)
    cod = monta_blob()
    print("=" * 72)
    print("OpenPod — RC7: o degrau B3 da ficha 011")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")
    print(f"  B3: o caminho da mensagem, sem get_path na ViewTask")

    erros = confere_premissas(d, cod)
    if erros:
        print("\n  RECUSADO — a entrada nao e a imagem que o B3 mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print("    - 2 MiB")
    print(f"    - sha256 {SHA_RC7[:16]}... (a RC7 exata)")
    print("    - a tabela de entradas do lote esta no lugar (CRIA/TITULO/APAGA)")
    print(f"    - a captura (0x{P_CAPTURA:06X}) ainda e o bl da fabrica")
    print(f"    - o get_path (0x{G.GET_PATH:08X}) aparece 1x no lote")
    print(f"    - o carrega_capa e o bl que o chama estao no lugar")
    print(f"    - a area livre 0x{BLOB:06X}..0x{BLOB + BLOB_MAX:06X} esta "
          f"virgem")

    patches = bytes_do_patch(cod)
    print("\n  PATCH")
    for off, novos in patches:
        print(f"    0x{off:06X}..0x{off + len(novos):06X}  {len(novos)} byte(s)")
    for off, novos in patches:
        d[off:off + len(novos)] = novos
    erros = confere_patch(d, cod)
    if erros:
        print("\n  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    permitido = [(off, off + len(novos)) for off, novos in patches]
    fora = [i for i in dif if not any(ini <= i < fim for ini, fim in permitido)]
    if fora:
        print(f"\n  RECUSADO: o diff final tem {len(fora)} byte(s) FORA do "
              f"patch (0x{min(fora):06X}..0x{max(fora):06X})")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    if any(i < 0x00E000 for i in dif) or any(0xD000 <= i < 0xE000 for i in dif) \
            or any(i >= 0x1FC000 for i in dif):
        print("  RECUSADO: tocou o bootloader, o setor 0xD000 ou a PSMP.",
              file=sys.stderr)
        return 1
    print(f"\n  bytes alterados: {len(dif)}")
    print("  nada fora do patch, nada abaixo de 0x00E000; setor 0xD000 e "
          "PSMP intocados   OK")

    if a.dry_run:
        print("\n  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as f:
        f.write(bytes(d))
    print(f"\n  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
