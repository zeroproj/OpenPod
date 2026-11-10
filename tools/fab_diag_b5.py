#!/usr/bin/env python3
r"""
fab_diag_b5.py — os degraus B5a e B5b da ficha 013 (RC7: abrir a capa).

O B5a abre o MP3 e so olha o cabecalho: se comeca com "ID3", manda NULL
("No data"); qualquer falha fica no cinza. O B5b compara o caminho com
ext+0x10, desregistra a ViewTask do monitor, chama carrega_capa(ext),
registra de volta e, no sucesso, faz img_set_src(img, ext). O envia_path
continua o do B4 (a mensagem tipo 5 da rajada), agora em +0x500.

PATCH: 0x00132242 (4 B) bl B5a/B5b; 0x000FF0C4 (12 B) bl envia_path + 4 nop;
e o blob em 0x001AAA00 (B5a em +0x000, B5b em +0x200, envia em +0x500).

PREMISSAS (antes de escrever; senao recusa sem criar a saida): 2 MiB e
sha256 do B4 exato; os patches do B4; o blob do B4; a area livre ate
0x1AB000; o codigo novo montado e os alvos conferidos.

USO: python3 tools/fab_diag_b5.py --in <b4.bin> --out <b5.bin>
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
from asm import monta  # noqa: E402

TAMANHO = 0x200000
SHA_B4 = ("39bea4883008bb840f515dd617cce1b46fcdec9c7ae3b7a8aee70d"
          "3764e49252")

BLOB = 0x1AAA00
BLOB_XIP = A.XIP + BLOB                 # 0x00DAAA00
BLOB_A = 0x000
BLOB_B = 0x200
BLOB_ENVIA = 0x500
BLOB_ENVIA_XIP = A.XIP + BLOB + BLOB_ENVIA   # 0x00DAAF00
BLOB_MAX = 0x600

B4_BLOB_XIP = A.XIP + BLOB              # 0x00DAAA00
B4_ENVIA_XIP = A.XIP + BLOB + 0x200     # 0x00DAAC00
B4_LEN = 0x2D9

P_BURST = 0x0FF0C4
P_TYPE = 0x13223E
P_TBB = 0x132242
P_TITULO = 0x1AA0FE
P_CARREGA = 0x1AA188
TITULO_EPILOGO = 0x00DAA1D0
GET_PATH = 0x00CFEFC4

NOP = b"\x00\xBF"
CMP_R3_5 = b"\x05\x2B"
FALHA_BL = b"\x00\x20\x00\xBF"
PUSH = b"\x2D\xE9\xF0\x41"
FONTE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "diag_b5.s")

B5A_MARCAS = (
    ("4cf62c60", "a guarda [0x81CE2C]"),
    ("40f25c21", "o tamanho 0x25C do FIL"),
    ("47f6410cc0f2cf0ce047", "o calloc 0xCF7841"),
    ("47f2cd7cc0f2d70ce047", "o f_open 0xD777CD"),
    ("46f6550cc0f2d70ce047", "o f_read 0xD76855"),
    ("47f69d4cc0f2d70ce047", "o f_close 0xD77C9D"),
    ("47f6850cc0f2cf0ce047", "o free 0xCF7885"),
    ("4df6690cc0f2d50ce047", "o img_set_src 0xD5D869"),
    ("48f20001c0f2da01", "o cinza 0xDA8000"),
    ("4928", "o 'I' do ID3"),
    ("4428", "o 'D' do ID3"),
    ("3328", "o '3' do ID3"),
)
B5B_MARCAS = (
    ("4cf62c60", "a guarda [0x81CE2C]"),
    ("07f1100a", "o ext+0x10 do ultimo caminho"),
    ("4af6396cc0f2d60ce047", "o 0xD6AE39 (descritor da task)"),
    ("46f6cd2cc0f2d40ce047", "o 0xD46ACD (unregister)"),
    ("4af2572cc0f2da0ce047", "o carrega_capa 0xDAA257"),
    ("5030", "o descritor+0x50 do register"),
    ("46f6212cc0f2d40ce047", "o 0xD46A21 (register)"),
    ("4df6690cc0f2d50ce047", "o img_set_src 0xD5D869"),
    ("48f20001c0f2da01", "o cinza 0xDA8000"),
)
ENVIA_MARCAS = (
    ("786920f00100", "o ldr do lr + bic do bit0"),
    ("4df61903c0f2d003", "o 0xD0D819"),
    ("4df68103c0f2d003", "o 0xD0D881"),
    ("4df69133c0f2d603", "o like getter 0xD6DB91"),
    ("4ff65553c0f2d903", "o strncpy 0xD9FD55"),
    ("40f6a323", "o strlen 0xAA3"),
    ("40f6ab33", "o memset 0xBAB"),
    ("4ff2df0cc0f2cf0c", "a falha 0xCFF0DF"),
    ("42f24f2cc0f2d30c", "o comum 0xD3224F"),
    ("42f2a12cc0f2d30c", "o epilogo 0xD322A1"),
)


def monta_blob(degrau):
    """Monta tools/diag_b5.s com o degrau pedido (a ou b)."""
    with open(FONTE, "r") as f:
        fonte = f.read()
    if degrau == "b":
        fonte = fonte.replace(".set DEGRAU_B, 0", ".set DEGRAU_B, 1", 1)
    return monta(fonte)


def confere_blob(cod, degrau):
    """O codigo novo tem de caber, ser do degrau e ter as chamadas certas."""
    erros = []
    if len(cod) != BLOB_MAX:
        erros.append(f"o codigo novo tem {len(cod)} bytes, esperado {BLOB_MAX}")
        return erros
    ini = BLOB_A if degrau == "a" else BLOB_B
    if cod[ini:ini + 2] != CMP_R3_5:
        erros.append(f"o label_dispatch do B5{degrau} nao comeca com cmp r3,#5")
    if cod[BLOB_ENVIA:BLOB_ENVIA + 4] != PUSH:
        erros.append("o envia_path nao comeca em +0x500 com push {r4-r8,lr}")
    if degrau == "a":
        if any(cod[BLOB_B:BLOB_ENVIA]):
            erros.append("o B5a nao pode ter codigo na area do B5b")
        marcas = B5A_MARCAS
    else:
        if any(cod[:BLOB_B]):
            erros.append("o B5b nao pode ter codigo na area do B5a")
        marcas = B5B_MARCAS
    for hexa, nome in marcas:
        if bytes.fromhex(hexa) not in cod:
            erros.append(f"o codigo novo nao tem {nome}")
    for hexa, nome in ENVIA_MARCAS:
        if bytes.fromhex(hexa) not in cod:
            erros.append(f"o envia_path nao tem {nome}")
    for chamador in (0xD088E0, 0xD08970, 0xD08BEE, 0xD0902C, 0xD0EED4):
        if struct.pack("<I", chamador) not in cod:
            erros.append(f"sem o chamador 0x{chamador:08X} da ViewTask")
    off = cod.find(struct.pack("<I", 0xD088E0))
    if off < 0 or (BLOB_XIP + off) % 4:
        erros.append("a tabela chamadores nao esta 4-alinhada")
    return erros


def confere_premissas(d, cod, degrau):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]
    erros = []
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != SHA_B4:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{SHA_B4[:16]}... (o B4 exato)")
    if bytes(d[P_TYPE:P_TYPE + 2]) != CMP_R3_5:
        erros.append(f"0x{P_TYPE:06X} nao e cmp r3,#5 do B4")
    lido = A.desvio(d, P_TBB)
    if lido is None or lido[0] != "bl" or lido[1] != B4_BLOB_XIP:
        erros.append(f"0x{P_TBB:06X} nao e o bl do B4 para 0x{B4_BLOB_XIP:08X}")
    lido = A.desvio(d, P_BURST)
    if lido is None or lido[0] != "bl" or lido[1] != B4_ENVIA_XIP:
        erros.append(f"0x{P_BURST:06X} nao e o bl do B4 para "
                     f"0x{B4_ENVIA_XIP:08X}")
    if bytes(d[P_BURST + 4:P_BURST + 12]) != NOP * 4:
        erros.append("os 4 nop depois do bl do envia_path do B4 nao estao no lugar")
    lido = A.desvio(d, P_BURST - 4)
    if lido is None or lido[0] != "bl" or lido[1] != GET_PATH:
        erros.append(f"o bl do get_path (0x{P_BURST - 4:06X}) nao aponta "
                     f"para 0x{GET_PATH:08X}")
    lido = A.desvio(d, P_TITULO)
    if lido is None or lido[0] != "b.w" or lido[1] != TITULO_EPILOGO:
        erros.append(f"o b.w de 0x{P_TITULO:06X} nao pula para "
                     f"0x{TITULO_EPILOGO:08X}")
    if bytes(d[P_CARREGA:P_CARREGA + 4]) != FALHA_BL:
        erros.append("os 4 bytes do carrega_capa nao sao movs r0,#0 + nop")
    if bytes(d[BLOB:BLOB + 2]) != CMP_R3_5:
        erros.append(f"o blob do B4 em 0x{BLOB:06X} nao comeca com cmp r3,#5")
    if bytes(d[BLOB + BLOB_B:BLOB + BLOB_B + 4]) != PUSH:
        erros.append(f"o envia_path do B4 em +0x{BLOB_B:X} nao e push")
    if bytes(d[BLOB + B4_LEN:BLOB + BLOB_MAX]) != b"\xFF" * (BLOB_MAX - B4_LEN):
        erros.append(f"a area livre depois do B4 em 0x{BLOB + B4_LEN:06X} "
                     f"nao esta virgem (0xFF)")
    if BLOB + BLOB_MAX > A.LOTE + A.LOTE_TAM:
        erros.append("a area livre passa do lote")
    erros.extend(confere_blob(cod, degrau))
    return erros


def bytes_do_patch(cod, degrau):
    """As (deslocamento, bytes novos) do B5, na ordem em que sao aplicadas."""
    alvo = BLOB_XIP + (BLOB_A if degrau == "a" else BLOB_B)
    return [(P_TBB, A.enc(A.XIP + P_TBB, alvo, True)),
            (P_BURST, A.enc(A.XIP + P_BURST, BLOB_ENVIA_XIP, True) + NOP * 4),
            (BLOB, cod)]


def confere_patch(d, cod, degrau):
    """Rele o patch e confere: os bytes novos e a decodificacao deles."""
    erros = []
    alvo = BLOB_XIP + (BLOB_A if degrau == "a" else BLOB_B)
    lido = A.desvio(d, P_TBB)
    if lido is None or lido[0] != "bl" or lido[1] != alvo:
        erros.append(f"o bl de 0x{P_TBB:06X} nao ficou um bl para "
                     f"0x{alvo:08X}")
    lido = A.desvio(d, P_BURST)
    if lido is None or lido[0] != "bl" or lido[1] != BLOB_ENVIA_XIP:
        erros.append(f"o bl de 0x{P_BURST:06X} nao ficou um bl para "
                     f"0x{BLOB_ENVIA_XIP:08X}")
    if bytes(d[P_BURST + 4:P_BURST + 12]) != NOP * 4:
        erros.append("os 4 nop depois do bl do envia_path nao estao no lugar")
    if bytes(d[P_TYPE:P_TYPE + 2]) != CMP_R3_5:
        erros.append(f"os 2 bytes de 0x{P_TYPE:06X} nao sao cmp r3,#5")
    lido = A.desvio(d, P_TITULO)
    if lido is None or lido[0] != "b.w" or lido[1] != TITULO_EPILOGO:
        erros.append(f"o b.w de 0x{P_TITULO:06X} nao pula para "
                     f"0x{TITULO_EPILOGO:08X}")
    if bytes(d[P_CARREGA:P_CARREGA + 4]) != FALHA_BL:
        erros.append("os 4 bytes do carrega_capa nao sao movs r0,#0 + nop")
    if bytes(d[BLOB:BLOB + len(cod)]) != cod:
        erros.append("o codigo novo nao ficou como o montado")
    erros.extend(confere_blob(cod, degrau))
    return erros


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
        description="RC7: os degraus B5a/B5b da ficha 013 (abrir a capa)")
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
    cod = monta_blob(a.degrau)
    nome = "B5a" if a.degrau == "a" else "B5b"
    print("=" * 72)
    print(f"OpenPod — RC7: o degrau {nome} da ficha 013\n"
          f"  origem : {a.src}\n  destino: {a.dst}")
    print("=" * 72)
    print(f"  {nome}: " + ("abre o MP3 e so olha o ID3" if a.degrau == "a"
                            else "carrega a capa com o monitor desligado"))

    erros = confere_premissas(d, cod, a.degrau)
    if erros:
        print(f"\n  RECUSADO — a entrada nao e a imagem que o {nome} mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print(f"  entrada conferida: B4 exato ({SHA_B4[:16]}...); patches, "
          f"blob e area livre no lugar")

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
