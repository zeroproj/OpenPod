#!/usr/bin/env python3
r"""
fab_diag_b3.py — o degrau B3 da ficha 011 (RC7: duas tarefas).

A ficha 011 mediu que o `get_path` na ViewTask reinicia o aparelho (B) e
que o monitor do watchdog e o que o leva ao reset (B2). O B3 tira o
`get_path` da ViewTask: a MainTask captura o caminho na rajada do play (o
`bl 0xD084F8` de `page4_media_cb`, 0x001088D8) e guarda em 0x00DAAB00; o
TITULO le esse global (0x001AA144) em vez de chamar o `get_path`, confere
que parece um caminho (`0:\` ou `0:/`) e mostra o quadrado cinza. Sem
`f_open`, sem JPEG, sem heap novo.

O codigo novo e ASSEMBLY Thumb-2 (tools/diag_b3.s, montado pelo clang via
tools/asm.py), para a saida ser reproduzivel.

PATCH (tres pontos + o codigo novo)

    1. 0x001088D8 (4 B, fabrica): `bl 0xD084F8` -> `bl guarda_path`;
    2. 0x001AA144 (10 B): `movw/movt + blx get_path` -> `bl le_global` +
       3 `nop`;
    3. 0x001AA188 (4 B): `bl carrega_capa` -> `movs r0, #0` + `nop`;
    4. 0x001AAA00: o blob (guarda_path em 0xDAAA00, le_global em
       0xDAAA40); o global 0x001AAB00..0x001AABFF fica 0xFF.

PREMISSAS, conferidas ANTES de escrever (senao recusa sem criar a saida)

    - 2 MiB e sha256 da RC7 exata (3af97713...);
    - a tabela 0x001AA010/14/18 decodifica para CRIA/TITULO/APAGA;
    - o `bl` de 0x001088D8 ainda chama 0xD084F8;
    - o par movw/movt de 0x00CFEFC5 aparece 1x no lote, seguido do `blx`;
    - o prologo do `carrega_capa` e o `bl` que o chama estao no lugar;
    - 0x001AAA00..0x001AAC00 esta virgem (0xFF) e o blob cabe antes do
      global, com as rotinas nos deslocamentos certos.

SAIDA E SEGURANCA

    Depois de escrever, RELE e confere o `bl`/`nop`/`movs` novos e o blob.
    O diff so pode tocar as tres regioes e o blob. `--out` igual/symlink/
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
    - o lote NAO e remontado: a RC7 fica byte a byte, salvo os 3 pontos e
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

# o codigo novo e o global (arquivo / XIP)
BLOB = 0x1AAA00
BLOB_XIP = A.XIP + BLOB                 # 0x00DAAA00
GUARDA = BLOB_XIP                       # guarda_path
LE_GLOBAL = BLOB_XIP + 0x40             # le_global
GLOBAL = 0x1AAB00                       # o caminho capturado (0x100 B)
GLOBAL_XIP = A.XIP + GLOBAL             # 0x00DAAB00
BLOB_MAX = GLOBAL - BLOB                # o codigo tem de caber antes

# as tres regioes do patch
P_CAPTURA = 0x1088D8                    # `bl 0xD084F8` (fabrica)
P_GET_PATH = 0x1AA144                   # `movw/movt` + `blx get_path`
P_CARREGA = 0x1AA188                    # `bl carrega_capa`
FALHA_BL = b"\x00\x20\x00\xBF"          # movs r0, #0 + nop
NOP = b"\x00\xBF"
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
    """O codigo novo tem de caber e ter as duas rotinas nos lugares certos."""
    erros = []
    if len(cod) > BLOB_MAX:
        erros.append(f"o codigo novo tem {len(cod)} bytes e nao cabe antes "
                     f"do global 0x{GLOBAL:06X} ({BLOB_MAX} bytes)")
    if len(cod) < 0x40:
        erros.append(f"o codigo novo tem {len(cod)} bytes: nao chega ao "
                     f"le_global (0x40)")
        return erros
    # o le_global comeca com o par movw/movt que carrega o global
    if G.imm16(*struct.unpack_from("<HH", cod, 0x40)) != GLOBAL_XIP & 0xFFFF:
        erros.append("o le_global nao comeca com movw r1, #0xab00")
    if G.imm16(*struct.unpack_from("<HH", cod, 0x44)) != (GLOBAL_XIP >> 16):
        erros.append("o le_global nao continua com movt r1, #0xda")
    # o guarda_path chama o 0xD084F8: o par movw/movt com o bit do Thumb
    pares = []
    for i in range(0, 0x40 - 8, 2):
        h1, h2 = struct.unpack_from("<HH", cod, i)
        n1, n2 = struct.unpack_from("<HH", cod, i + 4)
        if G.e_mov(h1, h2, 0xF240) and G.e_mov(n1, n2, 0xF2C0) \
                and ((h2 >> 8) & 0xF) == ((n2 >> 8) & 0xF) \
                and ((G.imm16(n1, n2) << 16) | G.imm16(h1, h2)) == ALVO_CAPTURA | 1:
            pares.append(i)
    if len(pares) != 1:
        erros.append(f"o guarda_path nao tem o par movw/movt do "
                     f"0x{ALVO_CAPTURA:08X} (achou {len(pares)})")
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
    # 1. a captura: o bl da fabrica ainda chama o 0xD084F8
    lido = A.desvio(d, P_CAPTURA)
    if lido is not None and lido[0] == "bl" and lido[1] == GUARDA:
        erros.append(f"o bl de 0x{P_CAPTURA:06X} ja aponta para o "
                     f"guarda_path (a imagem ja foi patcheada)")
    elif lido is None or lido[0] != "bl" or lido[1] != ALVO_CAPTURA:
        erros.append(f"em 0x{P_CAPTURA:06X} nao ha um bl para o "
                     f"0x{ALVO_CAPTURA:08X} da fabrica — o codigo mudou")
    # 2. a leitura: o par movw/movt do get_path, e o blx que o usa
    pares = G.acha_pares(d, G.GET_PATH)
    if len(pares) != 1:
        lido = A.desvio(d, P_GET_PATH)
        if lido is not None and lido[0] == "bl" and lido[1] == LE_GLOBAL:
            erros.append(f"o get_path de 0x{P_GET_PATH:06X} ja foi trocado "
                         f"pelo le_global (a imagem ja foi patcheada)")
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
    if any(b != 0xFF for b in d[BLOB:GLOBAL + 0x100]):
        erros.append(f"a area livre 0x{BLOB:06X}..0x{GLOBAL + 0x100:06X} "
                     f"nao esta virgem (todo 0xFF)")
    erros.extend(confere_blob(cod))
    return erros


# ---------------------------------------------------------------------------
# o patch
# ---------------------------------------------------------------------------

def bytes_do_patch(cod):
    """As (deslocamento, bytes novos) do B3, na ordem em que sao aplicadas."""
    captura = A.enc(A.XIP + P_CAPTURA, GUARDA, True)
    leitura = A.enc(A.XIP + P_GET_PATH, LE_GLOBAL, True) + NOP * 3
    return [(P_CAPTURA, captura),
            (P_GET_PATH, leitura),
            (P_CARREGA, FALHA_BL),
            (BLOB, cod)]


def confere_patch(d, cod):
    """Rele o patch e confere: os bytes novos e a decodificacao deles."""
    erros = []
    lido = A.desvio(d, P_CAPTURA)
    if lido is None or lido[0] != "bl" or lido[1] != GUARDA:
        erros.append(f"o bl de 0x{P_CAPTURA:06X} nao ficou um bl para "
                     f"0x{GUARDA:08X}")
    lido = A.desvio(d, P_GET_PATH)
    if lido is None or lido[0] != "bl" or lido[1] != LE_GLOBAL:
        erros.append(f"o bl de 0x{P_GET_PATH:06X} nao ficou um bl para "
                     f"0x{LE_GLOBAL:08X}")
    if bytes(d[P_GET_PATH + 4:P_GET_PATH + 10]) != NOP * 3:
        erros.append("os 3 nop depois do bl do le_global nao estao no lugar")
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
    print(f"  B3: o caminho da MainTask, sem get_path na ViewTask")

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
    print(f"    - o bl da captura (0x{P_CAPTURA:06X}) ainda e o da fabrica")
    print(f"    - o get_path (0x{G.GET_PATH:08X}) aparece 1x no lote")
    print(f"    - o carrega_capa e o bl que o chama estao no lugar")
    print(f"    - a area livre 0x{BLOB:06X}..0x{GLOBAL + 0x100:06X} esta virgem")

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
