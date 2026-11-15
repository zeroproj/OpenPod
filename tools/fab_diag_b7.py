#!/usr/bin/env python3
r"""
fab_diag_b7.py — os degraus B7a/B7b da ficha 015 (a capa nao engasga).

O B7a e o B6b exato + a regra de escala nova no carrega_capa (0xDAA256):
as quatro comparacoes com 0x40 (64) viram 0x38 (56). O B7b e o B7a + dois
wrappers no lote (0xDAAE00/0xDAAE20): cada callback do TJpgDec chama o
original, salva o retorno e chama vPortYield (0xC43634) uma vez (N=1).
Nao ha sleep e a primeira pausa so acontece depois da primeira leitura.
O B7b tambem poe a guarda do tipo 6: msg+0xA tem de ser 0x408 antes de
copiar; o cmp.w r3,#0x1c00 em 0xDAAABC desvia para a guarda 0xDAAE60.

PATCH (contra o B6b; o B6b e conferido por sha256):
    0x001AA32C (1 B)  cmp r0,#0x38    (era #0x40)
    0x001AA330 (1 B)  cmp r1,#0x38    (era #0x40)
    0x001AA346 (1 B)  cmp r2,#0x38    (era #0x40)
    0x001AA34E (1 B)  cmp r2,#0x38    (era #0x40)
    0x001AA30C (4 B)  ldr.w r1,[pc,#0xB40]  (so no B7b; era orr r1,#1)
    0x001AA376 (4 B)  ldr.w r1,[pc,#0xADC]  (so no B7b)
    0x001AAABC (4 B)  b.w guarda da view   (so no B7b; era cmp.w r3,#0x1c00)
    0x001AAE00 (0x58 B) wrappers + literais  (so no B7b)
    0x001AAE60 (0x22 B) guarda msg+0xA==0x408 (so no B7b)

PREMISSAS (antes de escrever; senao recusa sem criar a saida): 2 MiB e
sha256 do B6b exato; o blob do B6b; os quatro cmp; os dois orr; a area
dos wrappers virgem; o codigo novo montado e os destinos conferidos.

USO: python3 tools/fab_diag_b7.py --in <b6b.bin> --out <b7.bin>
--degrau a|b [--em 0x1a8000] [--dry-run].
"""

import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402
import diag_trava_asm as G  # noqa: E402
import fab_diag_b6 as F6  # noqa: E402
from asm import monta  # noqa: E402

TAMANHO = 0x200000
SHA_B6B = ("5f5020b3b0fcb5fd225451bef5af22c580852925dc4beba9c2fef47877aaec67")
# ficha 017: o mesmo B6b com a folha da home em grafite
SHA_B6B_21 = ("73e1f8ba60f71635e59d9d0255d3e2e91c1a6f4fb72c1f479fbe68"
              "3f38576258")
# ficha 018: o mesmo B6b com a folha escura de simbolos coloridos
SHA_B6B_22 = ("3062de544500b1d8c91fd1f5c1db2de852e0e1cfc5b93b0c802dd3"
              "986b8495f4")
SHAS_B6B = (SHA_B6B, SHA_B6B_21, SHA_B6B_22)

BLOB = 0x1AAA00
BLOB_XIP = A.XIP + BLOB
BLOB_ENVIA_XIP = A.XIP + BLOB + 0x200
BLOB_MAX = 0x600

P_TYPE = 0x13223E
P_TBB = 0x132242
P_BURST = 0x0FF0C4
P_CARREGA = 0x1AA188
P_VIEW6 = 0x1AAABC
VIEW6 = 0x1AAE60
VIEW6_LEN = 0x22
TITULO_EPILOGO = 0x00DAA1D0

# (deslocamento no arquivo, bytes originais de 2 B)
ESCALA = ((0x1AA32C, b"\x40\x28"), (0x1AA330, b"\x40\x29"),
          (0x1AA346, b"\x40\x2a"), (0x1AA34E, b"\x40\x2a"))
NOVA_ESCALA = 0x38

P_IN = 0x1AA30C
P_OUT = 0x1AA376
ORR = b"\x41\xf0\x01\x01"
LDR_IN = b"\xdf\xf8\x40\x1b"       # ldr.w r1,[pc,#0xB40] -> 0xDAAE50
LDR_OUT = b"\xdf\xf8\xdc\x1a"      # ldr.w r1,[pc,#0xADC] -> 0xDAAE54
WRAP = 0x1AAE00
WRAP_BYTES = 0x58
VIEW6_ORIG = b"\xb3\xf5\xe0\x5f"   # cmp.w r3,#0x1c00 do B6b
WRAP_IN = 0x00DAAE01
WRAP_OUT = 0x00DAAE21

NOP = b"\x00\xbf"
CMP_R3_6 = b"\x06\x2b"
FALHA_BL = b"\x00\x20\x00\xbf"
FONTE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "diag_b7.s")

MARCAS_COMUM = (
    "70b50446", "4af2054cc0f2da0ce0470fe0",
    "70b50446", "4af2774cc0f2da0ce047ffe7",
    "0546012043f2356cc0f2c40ce047284670bd",
)
BRANCH_VIEW6 = b"\x00\xf0\xd0\xb9"  # b.w 0xDAAE60
VIEW6_COD = bytes.fromhex(
    "6089b0f5816f07d1b3f5e05f04d84af6c32cc0f2da0c6047"
    "4af6fb2cc0f2da0c6047")


def monta_blob():
    with open(FONTE, "r") as f:
        return monta(f.read())


def confere_blob(cod):
    erros = []
    if len(cod) != BLOB_MAX:
        return [f"o codigo novo tem {len(cod)} bytes, esperado {BLOB_MAX}"]
    for hexa in MARCAS_COMUM:
        if bytes.fromhex(hexa) not in cod[0x400:0x442]:
            erros.append(f"o wrapper nao tem {hexa}")
    if struct.unpack_from("<I", cod, 0x450)[0] != WRAP_IN:
        erros.append("o literal do wrapper de entrada nao e 0xDAAE01")
    if struct.unpack_from("<I", cod, 0x454)[0] != WRAP_OUT:
        erros.append("o literal do wrapper de saida nao e 0xDAAE21")
    if cod[0x458:0x460] != b"\x00" * 8:
        erros.append("os wrappers passam do espaco reservado")
    if cod[0x0BC:0x0C0] != BRANCH_VIEW6:
        erros.append("o branch da guarda nao esta em +0xBC")
    if cod[0x460:0x482] != VIEW6_COD:
        erros.append("a guarda da view nao esta em +0x460")
    if cod[0x482:] != b"\x00" * (BLOB_MAX - 0x482):
        erros.append("a guarda da view passa do espaco reservado")
    return erros


def desvio(d, a):
    return A.desvio(d, a)


def confere_premissas(d, cod, degrau):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]
    erros = []
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha not in SHAS_B6B:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{SHA_B6B[:16]}... (ou o B6b grafite da 2.1, "
                     f"{SHA_B6B_21[:16]}...; ou o escuro_colorido da 2.2, "
                     f"{SHA_B6B_22[:16]}...) (o B6b exato)")
    if bytes(d[P_TYPE:P_TYPE + 2]) != CMP_R3_6:
        erros.append(f"0x{P_TYPE:06X} nao e cmp r3,#6 do B6b")
    lido = desvio(d, P_TBB)
    if lido is None or lido[0] != "b.w" or lido[1] != BLOB_XIP:
        erros.append(f"0x{P_TBB:06X} nao e o b.w do B6b para 0x{BLOB_XIP:08X}")
    lido = desvio(d, P_BURST)
    if lido is None or lido[0] != "bl" or lido[1] != BLOB_ENVIA_XIP:
        erros.append(f"0x{P_BURST:06X} nao e o bl do B6b para "
                     f"0x{BLOB_ENVIA_XIP:08X}")
    if bytes(d[P_CARREGA:P_CARREGA + 4]) != FALHA_BL:
        erros.append("os 4 bytes do carrega_capa nao sao movs r0,#0 + nop")
    lido = desvio(d, 0x1AA0FE)
    if lido is None or lido[0] != "b.w" or lido[1] != TITULO_EPILOGO:
        erros.append("o b.w do TITULO nao pula para 0xDAA1D0")
    if bytes(d[BLOB:BLOB + BLOB_MAX]) != F6.monta_blob("b"):
        erros.append("o blob do B6b nao e o exato")
    for off, velho in ESCALA:
        if bytes(d[off:off + 2]) != velho:
            erros.append(f"0x{off:06X} nao e {velho.hex()} do B6b")
    if degrau == "b":
        for off, nome in ((P_IN, "entrada"), (P_OUT, "saida")):
            if bytes(d[off:off + 4]) != ORR:
                erros.append(f"o ponteiro de {nome} em 0x{off:06X} nao e "
                             f"orr r1,r1,#1")
        if bytes(d[WRAP:WRAP + WRAP_BYTES]) != b"\x00" * WRAP_BYTES:
            erros.append("a area dos wrappers nao esta virgem")
        if bytes(d[VIEW6:VIEW6 + VIEW6_LEN]) != b"\x00" * VIEW6_LEN:
            erros.append("a area da guarda da view nao esta virgem")
        if bytes(d[P_VIEW6:P_VIEW6 + 4]) != VIEW6_ORIG:
            erros.append("0xDAAABC nao e cmp.w r3,#0x1c00 do B6b")
    erros.extend(confere_blob(cod))
    return erros


def bytes_do_patch(cod, degrau):
    patches = [(off, bytes([NOVA_ESCALA])) for off, _ in ESCALA]
    if degrau == "b":
        patches += [(P_IN, LDR_IN), (P_OUT, LDR_OUT),
                    (P_VIEW6, cod[0x0BC:0x0C0]),
                    (WRAP, cod[0x400:0x400 + WRAP_BYTES]),
                    (VIEW6, cod[0x460:0x482])]
    return patches


def confere_patch(d, cod, degrau):
    erros = []
    for off, velho in ESCALA:
        if d[off] != NOVA_ESCALA or d[off + 1] != velho[1]:
            erros.append(f"0x{off:06X} nao ficou cmp #{NOVA_ESCALA}")
    lido = desvio(d, P_TBB)
    if lido is None or lido[0] != "b.w" or lido[1] != BLOB_XIP:
        erros.append("o b.w do TITULO/dispatch mudou")
    lido = desvio(d, P_BURST)
    if lido is None or lido[0] != "bl" or lido[1] != BLOB_ENVIA_XIP:
        erros.append("o bl do envia_path mudou")
    if bytes(d[P_CARREGA:P_CARREGA + 4]) != FALHA_BL:
        erros.append("o carrega_capa cortado mudou")
    if degrau == "b":
        if bytes(d[P_IN:P_IN + 4]) != LDR_IN:
            erros.append("o ponteiro de entrada nao ficou no LDR literal")
        if bytes(d[P_OUT:P_OUT + 4]) != LDR_OUT:
            erros.append("o ponteiro de saida nao ficou no LDR literal")
        if bytes(d[WRAP:WRAP + WRAP_BYTES]) != cod[0x400:0x400 + WRAP_BYTES]:
            erros.append("os wrappers nao ficaram como o montado")
        if struct.unpack_from("<I", d, WRAP + 0x50)[0] != WRAP_IN:
            erros.append("o literal de entrada nao ficou em +0x450")
        if struct.unpack_from("<I", d, WRAP + 0x54)[0] != WRAP_OUT:
            erros.append("o literal de saida nao ficou em +0x454")
        if bytes(d[P_VIEW6:P_VIEW6 + 4]) != cod[0x0BC:0x0C0]:
            erros.append("o branch da guarda da view nao ficou em 0xDAAABC")
        if bytes(d[VIEW6:VIEW6 + VIEW6_LEN]) != cod[0x460:0x482]:
            erros.append("a guarda da view nao ficou em 0xDAAE60")
    return erros


def mesma_entrada(src, dst):
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
        description="RC7: os degraus B7a/B7b da ficha 015 (capa sem engasgo)")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--degrau", choices=("a", "b"), required=True)
    ap.add_argument("--em", default=None,
                    help=f"endereco do lote (tem de ser {G.LOTE:#x})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.em is not None:
        try:
            em = int(a.em, 0)
        except ValueError:
            print(f"RECUSADO: --em {a.em!r} nao e um endereco.", file=sys.stderr)
            return 2
        if em != G.LOTE:
            print(f"RECUSADO: --em {em:#x}; o lote desta ferramenta esta em "
                  f"{G.LOTE:#x}.", file=sys.stderr)
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
    nome = "B7a" if a.degrau == "a" else "B7b"
    print("=" * 72)
    print(f"OpenPod — RC7: o degrau {nome} da ficha 015\n"
          f"  origem : {a.src}\n  destino: {a.dst}")
    print("=" * 72)
    print(f"  {nome}: " + ("regra de escala 56 no carrega_capa"
                            if a.degrau == "a"
                            else "escala 56 + vPortYield + guarda da view"))

    erros = confere_premissas(d, cod, a.degrau)
    if erros:
        print(f"\n  RECUSADO — a entrada nao e a imagem que o {nome} mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print(f"  entrada conferida: B6b exato ({SHA_B6B[:16]}...); escala, "
          f"callbacks e area livre no lugar")

    patches = bytes_do_patch(cod, a.degrau)
    print("\n  PATCH")
    for off, novos in patches:
        print(f"    0x{off:06X}..0x{off + len(novos):06X}  {len(novos)} byte(s)")
    for off, novos in patches:
        d[off:off + len(novos)] = novos
    erros = confere_patch(d, cod, a.degrau)
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
