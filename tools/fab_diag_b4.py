#!/usr/bin/env python3
r"""
fab_diag_b4.py — o degrau B4 da ficha 012 (RC7: o caminho da MainTask).

A rajada (0x00CFF0A8) manda, logo depois do get_path, uma mensagem da
fabrica (classe 3, tipo 5) com o caminho no texto (ou vazio se o get_path
falhar). A view (0x00D32204) trata o tipo 5: copia o texto para ext+0x110,
valida com as guardas do B3 e aplica img_set_src(img, NULL) no sucesso ou
img_set_src(img, 0x00DA8000) no invalido/vazio. O TITULO (0x00DAA0E6)
volta a fazer so o set_text: 0x001AA0FE vira `b.w 0xDAA1D0`. O
carrega_capa continua cortado (0x001AA188 = movs r0,#0 + nop).

PATCH: 0x0013223E (2 B) cmp r3,#5; 0x00132242 (4 B) bl label_dispatch;
0x000FF0C4 (12 B) bl envia_path + 4 nop; 0x001AA0FE (4 B) b.w 0xDAA1D0;
0x001AA188 (4 B) movs r0,#0 + nop; e o blob em 0x001AAA00.

PREMISSAS (antes de escrever; senao recusa sem criar a saida): 2 MiB e
sha256 da RC7 exata; a tabela CRIA/TITULO/APAGA; a captura 0x001088D8; o
TITULO da RC7; a rajada e o dispatch da view; a area livre virgem.

USO: python3 tools/fab_diag_b4.py --in <rc7.bin> --out <b4.bin>
[--em 0x1a8000] [--dry-run].
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
BLOB_ENVIA = BLOB + 0x200               # o envia_path dentro do blob
BLOB_ENVIA_XIP = A.XIP + BLOB_ENVIA     # 0x00DAAC00
BLOB_MAX = 0x600                        # a area livre ate 0x1AB000

# os cinco pontos do patch (a captura 0x1088D8 fica da fabrica)
P_CAPTURA = 0x1088D8                    # `bl 0xD084F8` (fabrica; so confere)
P_BURST = 0x0FF0C4                      # o get_path/like getter da rajada
P_TYPE = 0x13223E                       # `cmp r3,#4` da classe 3
P_TBB = 0x132242                        # o `tbb [pc,r3]`
P_TITULO = 0x1AA0FE                     # o inicio da logica da capa
P_CARREGA = 0x1AA188                    # `bl carrega_capa`

# os alvos da fabrica (XIP)
ALVO_CAPTURA = 0x00D084F8
TITULO_EPILOGO = 0x00DAA1D0
CARREGA_CAPA = 0x00DAA256
GET_PATH = 0x00CFEFC4
LIKE_GETTER = 0x00D6DB90
SEND = 0x00D0D818
IMG_SET_SRC = 0x00D5D868
SET_TEXT = 0x00D5ED94
COMMON = 0x00D3224E
EPILOGO = 0x00D322A0

NOP = b"\x00\xBF"
FALHA_BL = b"\x00\x20\x00\xBF"          # movs r0,#0 + nop
CMP_R3_5 = b"\x05\x2B"                  # cmp r3,#5
RC7_BURST = bytes.fromhex("01280ad101a920466ef060fd")
RC7_TYPE = bytes.fromhex("042b")        # cmp r3,#4
RC7_BHI = bytes.fromhex("2ed8")         # bhi 0xD322A0
RC7_TBB = bytes.fromhex("dfe803f0")     # tbb [pc,r3]
RC7_COMUM = bytes.fromhex("38b3")       # cbz r0 (o comum)
RC7_EPILOGO = bytes.fromhex("70bd")     # pop {r4,r5,r6,pc}
RC7_SET_TEXT = bytes.fromhex("4ef6955cc0f2d50ce047")
RC7_IMG = bytes.fromhex("4df6690cc0f2d50ce047")
RC7_TITULO = bytes.fromhex("4cf62c60")  # movw r0,#0xce2c (o inicio da capa)
RC7_CARREGA = bytes.fromhex("00f065f8")  # bl 0xDAA256
P_IMG = 0x1AA17C                        # o img_set_src do TITULO (prova)
FONTE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "diag_b4.s")

# a estrutura do TITULO da RC7 (arquivo, bytes, o que e)
ESTRUTURA = (
    (0x1AA0E6, "2de9f04f", "o prologo do TITULO"),
    (0x1AA0F4, RC7_SET_TEXT.hex(), "o lv_label_set_text do TITULO"),
    (P_TITULO, RC7_TITULO.hex(), "o inicio da logica da capa"),
    (P_IMG, RC7_IMG.hex(), "o img_set_src do TITULO (0xD5D868)"),
    (P_CARREGA, RC7_CARREGA.hex(), "o bl do carrega_capa"),
)


# ---------------------------------------------------------------------------
# o codigo novo
# ---------------------------------------------------------------------------

def monta_blob():
    """Monta tools/diag_b4.s e devolve os bytes do .text."""
    with open(FONTE, "r") as f:
        return monta(f.read())

def confere_blob(cod):
    """O codigo novo tem de caber e ter o tipo 5, as guardas e a capa."""
    erros = []
    if not cod:
        erros.append("o codigo novo esta vazio")
        return erros
    if len(cod) > BLOB_MAX:
        erros.append(f"o codigo novo tem {len(cod)} bytes e nao cabe na "
                     f"area livre ({BLOB_MAX} bytes)")
    if cod[:2] != CMP_R3_5:
        erros.append("o label_dispatch nao comeca com cmp r3,#5")
    if cod[BLOB_ENVIA - BLOB:BLOB_ENVIA - BLOB + 4] != b"\x2d\xe9\xf0\x41":
        erros.append("o envia_path nao comeca em +0x200 com push {r4-r8,lr}")
    for v in (0x2830, 0x283A, 0x282F, 0x285C):   # cmp r0,#'0'/':'/'/'/'\\'
        if struct.pack("<H", v) not in cod:
            erros.append(f"o label_dispatch nao tem a validacao 0x{v:04X}")
    for hexa, nome in (
            ("48f20000c0f2da00", "o cinza 0xDA8000"),
            ("4df6690cc0f2d50ce047", "o img_set_src 0xD5D869"),
            ("43f6f108c0f28208", "a mensagem 0x008238F1"),
            ("052088f80400", "o tipo 5 em msg+4"),
            ("012088f80c00", "o msg+0xc = 1"),
            ("4df61903c0f2d003", "o 0xD0D819"),
            ("4df68103c0f2d003", "o 0xD0D881"),
            ("4df69133c0f2d603", "o like getter 0xD6DB91"),
            ("4ff65553c0f2d903", "o strncpy 0xD9FD55"),
            ("40f6a323", "o strlen 0xAA3"),
            ("40f6ab33", "o memset 0xBAB"),
            ("4ff2df0cc0f2cf0c", "a falha 0xCFF0DF"),
            ("42f24f2cc0f2d30c", "o comum 0xD3224F"),
            ("42f2a12cc0f2d30c", "o epilogo 0xD322A1")):
        if bytes.fromhex(hexa) not in cod:
            erros.append(f"o codigo novo nao tem {nome}")
    for chamador in (0xD088E0, 0xD08970, 0xD08BEE, 0xD0902C, 0xD0EED4):
        if struct.pack("<I", chamador) not in cod:
            erros.append(f"sem o chamador 0x{chamador:08X} da ViewTask")
    return erros

# ---------------------------------------------------------------------------
# premissas
# ---------------------------------------------------------------------------
def confere_premissas(d, cod):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]
    erros = []
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != SHA_RC7:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{SHA_RC7[:16]}... (a RC7 exata)")
    for i, alvo in enumerate(G.ENTRADAS):
        lido = A.desvio(d, G.TABELA + 4 * i)
        if lido is None or lido[0] != "b.w" or lido[1] != alvo:
            erros.append(f"a entrada {i} da tabela nao e b.w para 0x{alvo:08X}")
    lido = A.desvio(d, P_CAPTURA)
    if lido is None or lido[0] != "bl" or lido[1] != ALVO_CAPTURA:
        erros.append(f"0x{P_CAPTURA:06X} nao e o bl da captura da fabrica")
    for off, hexa, nome in ESTRUTURA:
        b = bytes.fromhex(hexa)
        if bytes(d[off:off + len(b)]) != b:
            erros.append(f"0x{off:06X} nao e {nome} da RC7")
    if bytes(d[P_CARREGA:P_CARREGA + 4]) == FALHA_BL:
        erros.append("o bl do carrega_capa ja esta patcheado")
    if bytes(d[P_BURST:P_BURST + 12]) != RC7_BURST:
        erros.append(f"0x{P_BURST:06X} nao e a rajada da RC7")
    lido = A.desvio(d, P_BURST - 4)
    if lido is None or lido[0] != "bl" or lido[1] != GET_PATH:
        erros.append(f"o bl do get_path (0x{P_BURST - 4:06X}) nao aponta "
                     f"para 0x{GET_PATH:08X}")
    lido = A.desvio(d, P_BURST + 8)
    if lido is None or lido[0] != "bl" or lido[1] != LIKE_GETTER:
        erros.append(f"o bl do like getter (0x{P_BURST + 8:06X}) nao aponta "
                     f"para 0x{LIKE_GETTER:08X}")
    if bytes(d[P_TYPE:P_TYPE + 2]) != RC7_TYPE:
        erros.append(f"0x{P_TYPE:06X} nao e cmp r3,#4 da classe 3")
    if bytes(d[P_TYPE + 2:P_TYPE + 4]) != RC7_BHI:
        erros.append(f"0x{P_TYPE + 2:06X} nao e o bhi 0xD322A0")
    if bytes(d[P_TBB:P_TBB + 4]) != RC7_TBB:
        erros.append(f"0x{P_TBB:06X} nao e o tbb [pc,r3]")
    if bytes(d[COMMON - A.XIP:COMMON - A.XIP + 2]) != RC7_COMUM:
        erros.append("o comum 0xD3224E nao e o cbz r0")
    if bytes(d[EPILOGO - A.XIP:EPILOGO - A.XIP + 2]) != RC7_EPILOGO:
        erros.append("o epilogo 0xD322A0 nao e o pop")
    if bytes(d[P_CARREGA:P_CARREGA + 4]) != FALHA_BL:
        prologos = G.acha_carrega_capa(d)
        if len(prologos) != 1:
            erros.append(f"o prologo do carrega_capa aparece {len(prologos)}x")
        else:
            bls = G.acha_bl_para(d, prologos[0] + A.XIP)
            if len(bls) != 1 or bls[0] != P_CARREGA:
                erros.append(f"o bl do carrega_capa nao esta em "
                             f"0x{P_CARREGA:06X}")
    if any(b != 0xFF for b in d[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"a area livre 0x{BLOB:06X} nao esta virgem (0xFF)")
    if BLOB + BLOB_MAX > A.LOTE + A.LOTE_TAM:
        erros.append("a area livre passa do lote")
    erros.extend(confere_blob(cod))
    return erros


# ---------------------------------------------------------------------------
# o patch
# ---------------------------------------------------------------------------

def bytes_do_patch(cod):
    """As (deslocamento, bytes novos) do B4, na ordem em que sao aplicadas."""
    return [(P_TYPE, CMP_R3_5),
            (P_TBB, A.enc(A.XIP + P_TBB, BLOB_XIP, True)),
            (P_BURST, A.enc(A.XIP + P_BURST, BLOB_ENVIA_XIP, True) + NOP * 4),
            (P_TITULO, A.enc(A.XIP + P_TITULO, TITULO_EPILOGO, False)),
            (P_CARREGA, FALHA_BL),
            (BLOB, cod)]


def confere_patch(d, cod):
    """Rele o patch e confere: os bytes novos e a decodificacao deles."""
    erros = []
    if bytes(d[P_TYPE:P_TYPE + 2]) != CMP_R3_5:
        erros.append(f"os 2 bytes de 0x{P_TYPE:06X} nao sao cmp r3,#5")
    lido = A.desvio(d, P_TBB)
    if lido is None or lido[0] != "bl" or lido[1] != BLOB_XIP:
        erros.append(f"o bl de 0x{P_TBB:06X} nao ficou um bl para "
                     f"0x{BLOB_XIP:08X}")
    lido = A.desvio(d, P_BURST)
    if lido is None or lido[0] != "bl" or lido[1] != BLOB_ENVIA_XIP:
        erros.append(f"o bl de 0x{P_BURST:06X} nao ficou um bl para "
                     f"0x{BLOB_ENVIA_XIP:08X}")
    if bytes(d[P_BURST + 4:P_BURST + 12]) != NOP * 4:
        erros.append("os 4 nop depois do bl do envia_path nao estao no lugar")
    lido = A.desvio(d, P_TITULO)
    if lido is None or lido[0] != "b.w" or lido[1] != TITULO_EPILOGO:
        erros.append(f"o b.w de 0x{P_TITULO:06X} nao pula para "
                     f"0x{TITULO_EPILOGO:08X}")
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
        description="RC7: o degrau B4 da ficha 012 (o caminho da MainTask)")
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
    print("OpenPod — RC7: o degrau B4 da ficha 012\n"
          f"  origem : {a.src}\n  destino: {a.dst}")
    print("=" * 72)
    print("  B4: o caminho da MainTask numa mensagem tipo 5; o TITULO so "
          "set_text")

    erros = confere_premissas(d, cod)
    if erros:
        print("\n  RECUSADO — a entrada nao e a imagem que o B4 mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print(f"  entrada conferida: RC7 exata ({SHA_RC7[:16]}...); tabela, "
          f"captura, TITULO, rajada/dispatch e area livre no lugar")

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
