#!/usr/bin/env python3
r"""
fab_diag_b3.py — o degrau B3 da ficha 011 (RC7: duas tarefas).

O B3 tira o get_path da ViewTask sem inventar RAM e sem escrever na flash
XIP. O caminho NAO esta no r5 do TITULO (esse e o texto do titulo): o
page_music_play_label_process (0x00D3220C) escolhe o rotulo pelo halfword
+4 da mensagem (tbb em 0x00D32242) e faz set_text(rotulo, msg+0x14) em
0x00D3225E. A mensagem do 0xD084F8 grava 2 em +4 (rotulo [view+8]); a de
titulo (0xD08448) grava 1 (rotulo [view+4]); o TITULO da RC7 so segue
quando r4 == [r6+4] (0x00DAA114). A fila e serial: o rotulo 2 ja tem o
caminho quando o titulo chega. O B3 le o texto do rotulo 2 com o
lv_label_get_text da fabrica (le [rotulo+0x24], como o lv_label_set_text
em 0xD5ED94) e copia para ext+0x110 (a RAM que o get_path usava; ext =
[[[0x81CE2C]+0xAC]+0x30]).

PATCH: 0x001AA144 (10 B) vira ldr r0,[r6,#8] + ldr r0,[r0,#0x24] +
bl copia_path + nop; 0x001AA174 (8 B) vira movs r1,#0 + 3 nop (o sucesso
sem o quadrado cinza; o cinza da falha em 0x001AA1BE fica); 0x001AA188
(4 B) vira movs r0,#0 + nop; e o copia_path em 0x001AAA00. A captura
0x001088D8 NAO e tocada.

PREMISSAS (conferidas ANTES de escrever; senao recusa sem criar a saida):
2 MiB e sha256 da RC7 exata (3af97713...); a tabela CRIA/TITULO/APAGA; a
captura de 0x001088D8; o TITULO da RC7 (o get_path e a estrutura
[0x81CE2C]/[r6+4]/[r6+8]/[r6+0x30]); o cinza do sucesso e o da falha, o
img_set_src e o lv_label_set_text (que grava [rotulo+0x24]); o
carrega_capa; a area livre virgem.

USO: python3 tools/fab_diag_b3.py --in <rc7.bin> --out <b3.bin>
[--em 0x1a8000] [--dry-run]. So serve na RC7 exata; a saida ja patcheada e
recusada; o lote NAO e remontado (a RC7 fica byte a byte, salvo os 3 pontos
e o blob).
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

# os tres pontos do patch (a captura 0x1088D8 fica da fabrica)
P_CAPTURA = 0x1088D8                    # `bl 0xD084F8` (fabrica; so confere)
P_TITULO = 0x1AA144                     # `movw/movt` + `blx get_path`
P_CAPA = 0x1AA174                       # o cinza do sucesso (`r1 = 0xDA8000`)
P_FALHA = 0x1AA1BE                      # o cinza da falha (nao e tocado)
P_IMG = 0x1AA17C                        # o `img_set_src` do sucesso
P_IMG_FALHA = 0x1AA1C6                  # o `img_set_src` da falha
P_CARREGA = 0x1AA188                    # `bl carrega_capa`
FALHA_BL = b"\x00\x20\x00\xBF"          # movs r0, #0 + nop
NOP = b"\x00\xBF"
LDR_R0_R6_8 = b"\xB0\x68"               # ldr r0, [r6, #8] (o rotulo 2)
LDR_R0_R0_24 = b"\x40\x6A"              # ldr r0, [r0, #0x24] (o texto)
MOVS_R1_0 = b"\x00\x21"                 # movs r1, #0 (src nulo)
RC7_TITULO = bytes.fromhex("4ef6c57cc0f2cf0ce047")   # get_path (0xDAA144)
RC7_CAPA = bytes.fromhex("48f20001c0f2da01")         # r1 = 0xDA8000
RC7_IMG = bytes.fromhex("4df6690cc0f2d50ce047")      # img_set_src
RC7_SET_TEXT = bytes.fromhex("4ef6955cc0f2d50ce047")  # label_set_text
ALVO_CAPTURA = 0x00D084F8               # o `0xD084F8` da fabrica
CARREGA_CAPA = 0x00DAA256               # o alvo do `bl` de 0x001AA188
SET_TEXT = 0x00D5ED94                   # o lv_label_set_text da fabrica
P_TEXTO_LDR = 0x15EDA0                  # ldr r6,[r4,#0x24] (o texto)
P_TEXTO_STR = 0x15EDC2                  # str r0,[r4,#0x24] (o texto)
FONTE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "diag_b3.s")

# a estrutura do TITULO da RC7 (arquivo, bytes, o que e)
ESTRUTURA = (
    (0x1AA0E6, "2de9f04f", "o prologo do TITULO"),
    (0x1AA0F4, RC7_SET_TEXT.hex(), "o lv_label_set_text do TITULO"),
    (0x1AA10C, "d0f8ac60", "o [r0+0xac] (o container)"),
    (0x1AA114, "7068a042", "a guarda r4 == [r6+4]"),
    (0x1AA11A, "376b", "o [r6+0x30] (a extensao)"),
    (0x1AA120, "07f58870", "o ext+0x110 do memset"),
    (0x1AA134, "4bf68441c0f28101", "o [0x81BC84]"),
    (0x1AA13C, "0878096a", "o [r1]/[r1+0x20]"),
    (0x1AA140, "07f58872", "o r2 = ext+0x110"),
    (P_CAPA, RC7_CAPA.hex(), "o cinza do sucesso"),
    (P_IMG, RC7_IMG.hex(), "o img_set_src do sucesso"),
    (P_FALHA, RC7_CAPA.hex(), "o cinza da falha"),
    (P_IMG_FALHA, RC7_IMG.hex(), "o img_set_src da falha"),
)


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
    for v in (0x2930, 0x293A, 0x292F, 0x295C):   # cmp r1, #'0'/':'/'/'/'\\'
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
    if lido is None or lido[0] != "bl" or lido[1] != ALVO_CAPTURA:
        erros.append(f"em 0x{P_CAPTURA:06X} nao ha um bl para o "
                     f"0x{ALVO_CAPTURA:08X} da fabrica — o codigo mudou")
    # 2. o TITULO da RC7: a estrutura e o par do get_path
    for off, hexa, nome in ESTRUTURA:
        b = bytes.fromhex(hexa)
        if bytes(d[off:off + len(b)]) != b:
            erros.append(f"0x{off:06X} nao e {nome} da RC7")
    # 3. o texto do rotulo: a prova do lv_label_get_text (o [r4+0x24])
    if bytes(d[P_TEXTO_LDR:P_TEXTO_LDR + 2]) != b"\x66\x6A":
        erros.append(f"o lv_label_set_text (0x{SET_TEXT:08X}) nao le "
                     f"[r4+0x24] — o texto do rotulo mudou de lugar")
    if bytes(d[P_TEXTO_STR:P_TEXTO_STR + 2]) != b"\x60\x62":
        erros.append(f"o lv_label_set_text (0x{SET_TEXT:08X}) nao grava "
                     f"[r4+0x24] — o texto do rotulo mudou de lugar")
    # 4. a capa: o carrega_capa (prologo unico) e o bl que o chama
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
    # 5. a area livre e o codigo novo
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
    titulo = (LDR_R0_R6_8 + LDR_R0_R0_24
              + A.enc(A.XIP + P_TITULO + 4, BLOB_XIP, True) + NOP)
    return [(P_TITULO, titulo),
            (P_CAPA, MOVS_R1_0 + NOP * 3),
            (P_CARREGA, FALHA_BL),
            (BLOB, cod)]


def confere_patch(d, cod):
    """Rele o patch e confere: os bytes novos e a decodificacao deles."""
    erros = []
    if bytes(d[P_TITULO:P_TITULO + 4]) != LDR_R0_R6_8 + LDR_R0_R0_24:
        erros.append(f"os 4 bytes de 0x{P_TITULO:06X} nao sao "
                     f"ldr r0,[r6,#8] + ldr r0,[r0,#0x24]")
    lido = A.desvio(d, P_TITULO + 4)
    if lido is None or lido[0] != "bl" or lido[1] != BLOB_XIP:
        erros.append(f"o bl de 0x{P_TITULO + 4:06X} nao ficou um bl para "
                     f"0x{BLOB_XIP:08X}")
    if bytes(d[P_TITULO + 8:P_TITULO + 10]) != NOP:
        erros.append("o nop depois do bl do copia_path nao esta no lugar")
    if bytes(d[P_CAPA:P_CAPA + 8]) != MOVS_R1_0 + NOP * 3:
        erros.append("os 8 bytes do cinza do sucesso nao sao movs r1,#0 + "
                     "3 nop")
    if bytes(d[P_CARREGA:P_CARREGA + 4]) != FALHA_BL:
        erros.append("os 4 bytes do carrega_capa nao sao movs r0,#0 + nop")
    if bytes(d[P_FALHA:P_FALHA + 8]) != RC7_CAPA:
        erros.append("o cinza da falha (0x001AA1BE) mudou — o caminho "
                     "invalido tem de continuar cinza")
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
    print(f"  B3: o caminho do rotulo 2, sem get_path na ViewTask")

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
    print(f"    - o TITULO da RC7 (0x{P_TITULO:06X}) e a estrutura estao "
          f"no lugar")
    print(f"    - o texto do rotulo ([r4+0x24]) e o carrega_capa estao no "
          f"lugar")
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
