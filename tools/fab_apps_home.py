#!/usr/bin/env python3
"""
fab_apps_home.py — ficha 021 (Reload 3.0): o indice 5 da home vira Apps.

PROPOSITO

    O item 5 da home (hoje Imagem) passa a abrir o menu Apps escondido. O
    menu e a pagina 0x53 de fabrica (`page_home_menu_create`); a 0x52 e o
    "Desligar sozinho" (`page_set_timershut_time_create`), como o
    `docs/PLANO_EXTRAS.md` §8.3 registra depois de a Core 3.0 abrir a tela
    errada. A ficha 021 escreve 0x52, mas a medicao e a 0x53; esta
    ferramenta usa a 0x53 e o `021-analise.md` registra a divergencia.

    O destino do indice 5 e o bloco de fabrica em 0xD011AE. Os primeiros
    10 bytes sao um `bl` de checagem de imagem; o bloco so chega ao numero
    da pagina em 0xD011EA. A receita comprovada no PLANO_EXTRAS e trocar
    esses 10 bytes por quatro `movs` e um `b` para a cauda comum:

        0xD011AE  53 23   movs r3, #0x53      a pagina do Apps
        0xD011B0  00 22   movs r2, #0
        0xD011B2  02 21   movs r1, #2
        0xD011B4  01 20   movs r0, #1
        0xD011B6  1C E0   b 0xD011F2          a cauda comum

    O resto do bloco antigo fica morto. O unico desvio de fora que entra
    nele e `0xD0129E beq 0xD011BE`, que cai DEPOIS dos 10 bytes trocados e
    continua intacto.

O TEXTO NOVO "Apps" (id 216)

    A tabela do idioma tem 216 ponteiros XIP e nao tem folga: o id 216
    leria a tabela seguinte. A copia da tabela para a area livre reservada
    (0x001A3600, 0x700 bytes) cabe 217 ponteiros: os 216 copiados do
    idioma e o novo apontando para a string "Apps", gravada no fim do
    lote. As duas tabelas (EN e PT) sao copiadas, porque o id 5 da tabela
    de rotulos da home e o mesmo nos dois idiomas.

    Quatro ponteiros passam a apontar para as tabelas novas: os dois
    literais que o `get_string` usa (0x1210E4 EN, 0x121104 PT) e as duas
    entradas do vetor de idiomas (0x48778 EN, 0x48798 PT). O ponteiro do
    id 5 na tabela de rotulos (0x486D8) vira 216.

PREMISSAS, conferidas ANTES de escrever

    - a imagem tem 2 MiB e e a 2.2.1 exata (sha256);
    - os dois literais e as duas entradas do vetor apontam para as tabelas
      de fabrica/2.2 (0xC52AA4 EN, 0xC53B84 PT);
    - as tabelas tem 216 ponteiros XIP, cada um para uma string com NUL;
    - a tabela de rotulos da home e [1,3,5,6,2,4,9,10,8] e o id 5 e 4;
    - o TBH de `page1_process` (0xD00FBE, entrada 5 = 0x00F8) leva a
      0xD011AE, e a cauda em 0xD011F2 e `pop.w` + `b.w 0xD0DAE0`;
    - os 10 bytes em 0x1011AE sao o bloco de fabrica;
    - o lote 0x001A3600..0x001A3D00 esta virgem (todo 0xFF).

USO

    python3 tools/fab_apps_home.py --in <2.2.1.bin> --out <3.0.bin>
    python3 tools/fab_apps_home.py --in ... --out ... --dry-run
"""
import argparse
import hashlib
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XIP = 0x00C00000
TAMANHO = 0x200000
SHA_2_2_1 = ("e477c1e78ac1c88db58d29b030f35d7f11c8d90f45ec695a9b63392e"
             "a9936402")

EM_PADRAO = 0x001A3600
EM_TAM = 0x0700
N_TEXTOS = 216
N_NOVO = 217
ID_NOVO = 216
TEXTO = b"Apps\0"

TAB_EN, TAB_PT = 0xC52AA4, 0xC53B84
VET_EN, VET_PT = 0x00048778, 0x00048798
LIT_EN, LIT_PT = 0x001210E4, 0x00121104
ROTULO = 0x000486D8
ROTULOS = (1, 3, 5, 6, 2, 4, 9, 10, 8)
ROTULO_FABRICA = 4

STUB = 0x001011AE
STUB_XIP = XIP + STUB
STUB_FABRICA = bytes.fromhex("fdf7b1fa0028c0d00020")
STUB_NOVO = bytes.fromhex("53230022022101201ce0")
TAIL = 0x00D011F2
TAIL_OFF = TAIL - XIP
TAIL_BYTES = bytes.fromhex("bde8f0410cf073bc")
TBH = 0x00D00FBE
TBH_IDX5 = 0x00F8
PAGINA = 0x53

PERMITIDO = [(STUB, STUB + len(STUB_NOVO)), (ROTULO, ROTULO + 4),
             (VET_EN, VET_EN + 4), (VET_PT, VET_PT + 4),
             (LIT_EN, LIT_EN + 4), (LIT_PT, LIT_PT + 4),
             (EM_PADRAO, EM_PADRAO + EM_TAM)]


def le32(d, off):
    return struct.unpack_from("<I", d, off)[0]


def grava32(d, off, v):
    struct.pack_into("<I", d, off, v)


def mesma_entrada(src, dst):
    """--out aponta para a propria entrada (caminho, symlink ou hardlink)?"""
    if os.path.abspath(src) == os.path.abspath(dst):
        return True
    if not os.path.lexists(dst):
        return False
    try:
        return os.path.samefile(src, dst)
    except OSError:
        return False


def confere_tabela(d, nome, base):
    """216 ponteiros XIP, cada um para uma string terminada em NUL."""
    erros = []
    off = base - XIP
    vals = struct.unpack_from("<216I", d, off)
    for i, p in enumerate(vals):
        if not (XIP <= p < XIP + TAMANHO):
            erros.append(f"{nome} id {i}: ponteiro 0x{p:08X} fora da imagem")
            continue
        q = p - XIP
        if d.find(b"\0", q) < 0:
            erros.append(f"{nome} id {i}: string 0x{p:08X} sem NUL")
    return erros


def confere_premissas(d, em):
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]
    erros = []
    got = hashlib.sha256(d).hexdigest()
    if got != SHA_2_2_1:
        erros.append(f"sha256 {got}; a entrada tem de ser a 2.2.1 "
                     f"{SHA_2_2_1}")
    for nome, off, esperado in (
            ("literal EN 0x1210E4", LIT_EN, TAB_EN),
            ("literal PT 0x121104", LIT_PT, TAB_PT),
            ("vetor EN 0x48778", VET_EN, TAB_EN),
            ("vetor PT 0x48798", VET_PT, TAB_PT)):
        v = le32(d, off)
        if v != esperado:
            erros.append(f"{nome} = 0x{v:08X}, esperado 0x{esperado:08X}")
    if tuple(struct.unpack_from("<9I", d, 0x486C4)) != ROTULOS:
        erros.append("a tabela de rotulos da home nao e a de fabrica")
    if le32(d, ROTULO) != ROTULO_FABRICA:
        erros.append(f"o id 5 do rotulo = {le32(d, ROTULO)}, esperado "
                     f"{ROTULO_FABRICA}")
    if d[STUB:STUB + 10] != STUB_FABRICA:
        erros.append(f"os 10 bytes em 0x{STUB:06X} nao sao o bloco de "
                     f"fabrica")
    if struct.unpack_from("<H", d, TBH - XIP + 10)[0] != TBH_IDX5:
        erros.append(f"a entrada 5 do TBH em 0x{TBH:08X} nao e 0x{TBH_IDX5:X}")
    if d[TAIL_OFF:TAIL_OFF + 8] != TAIL_BYTES:
        erros.append(f"a cauda em 0x{TAIL:08X} nao e pop.w + b.w 0xD0DAE0")
    erros += confere_tabela(d, "EN", TAB_EN)
    erros += confere_tabela(d, "PT", TAB_PT)
    if em != EM_PADRAO:
        erros.append(f"--em 0x{em:06X}; o MAPA reserva 0x{EM_PADRAO:06X}")
    if not (EM_PADRAO <= em and em + EM_TAM <= TAMANHO):
        erros.append("o lote nao cabe na imagem")
    elif set(d[em:em + EM_TAM]) != {0xFF}:
        erros.append(f"o lote 0x{em:06X}..0x{em + EM_TAM:06X} nao esta "
                     f"virgem (todo 0xFF)")
    return erros


def monta(d, em):
    """(bytes da tabela PT, bytes da tabela EN, endereco da string)."""
    pt = bytes(d[TAB_PT - XIP:TAB_PT - XIP + 4 * N_TEXTOS])
    en = bytes(d[TAB_EN - XIP:TAB_EN - XIP + 4 * N_TEXTOS])
    txt = em + 4 * N_NOVO * 2
    return (pt + struct.pack("<I", XIP + txt),
            en + struct.pack("<I", XIP + txt), txt)


def confere_resultado(d, orig, em, tab_pt, tab_en, txt):
    erros = []
    pt_novo, en_novo = em, em + 4 * N_NOVO
    if bytes(d[pt_novo:pt_novo + len(tab_pt)]) != tab_pt:
        erros.append("a tabela PT nova nao foi gravada como montada")
    if bytes(d[en_novo:en_novo + len(tab_en)]) != tab_en:
        erros.append("a tabela EN nova nao foi gravada como montada")
    if d[txt:txt + len(TEXTO)] != TEXTO:
        erros.append("a string Apps nao foi gravada com NUL")
    for nome, off, alvo in (
            ("literal EN", LIT_EN, XIP + en_novo),
            ("literal PT", LIT_PT, XIP + pt_novo),
            ("vetor EN", VET_EN, XIP + en_novo),
            ("vetor PT", VET_PT, XIP + pt_novo)):
        v = le32(d, off)
        if v != alvo:
            erros.append(f"{nome} 0x{off:06X} = 0x{v:08X}, esperado "
                         f"0x{alvo:08X}")
    if le32(d, ROTULO) != ID_NOVO:
        erros.append(f"o id 5 do rotulo = {le32(d, ROTULO)}, esperado "
                     f"{ID_NOVO}")
    if d[STUB:STUB + len(STUB_NOVO)] != STUB_NOVO:
        erros.append("os 10 bytes do destino nao sao os da receita")
    h = struct.unpack_from("<H", d, STUB + 8)[0]
    if (h & 0xF800) != 0xE000:
        erros.append("o salto do stub nao e um b de 16 bits")
    else:
        imm = h & 0x7FF
        if imm & 0x400:
            imm -= 0x800
        alvo = STUB_XIP + 8 + 4 + imm * 2
        if alvo != TAIL:
            erros.append(f"o b do stub vai a 0x{alvo:08X}, esperado "
                         f"0x{TAIL:08X}")
    if d[TAIL_OFF:TAIL_OFF + 8] != TAIL_BYTES:
        erros.append("a cauda comum foi tocada")
    # a tabela PT nova tem de ser a copia exata dos 216 ids + o 217o
    if bytes(d[em:em + 4 * N_TEXTOS]) != bytes(
            orig[TAB_PT - XIP:TAB_PT - XIP + 4 * N_TEXTOS]):
        erros.append("os 216 ids da tabela PT nao sao a copia da entrada")
    if bytes(d[em + 4 * N_NOVO:em + 4 * N_NOVO + 4 * N_TEXTOS]) != bytes(
            orig[TAB_EN - XIP:TAB_EN - XIP + 4 * N_TEXTOS]):
        erros.append("os 216 ids da tabela EN nao sao a copia da entrada")
    return erros


def main():
    ap = argparse.ArgumentParser(description="ficha 021: indice 5 abre Apps")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", type=lambda s: int(s, 0), default=None,
                    help=f"lote da area livre (tem de ser {EM_PADRAO:#x})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    em = EM_PADRAO if a.em is None else a.em

    if not os.path.exists(a.src):
        print(f"RECUSADO: {a.src} nao existe.", file=sys.stderr)
        return 2
    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)
    print("=" * 72)
    print("OpenPod — Reload 3.0: o indice 5 da home abre o menu Apps")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n  lote   : "
          f"0x{em:06X}\n")

    erros = confere_premissas(d, em)
    if erros:
        print("  RECUSADO — a entrada nao e a 2.2.1 que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    tab_pt, tab_en, txt = monta(d, em)
    pt_novo, en_novo = em, em + 4 * N_NOVO
    d[pt_novo:pt_novo + len(tab_pt)] = tab_pt
    d[en_novo:en_novo + len(tab_en)] = tab_en
    d[txt:txt + len(TEXTO)] = TEXTO
    d[STUB:STUB + len(STUB_NOVO)] = STUB_NOVO
    grava32(d, ROTULO, ID_NOVO)
    grava32(d, VET_EN, XIP + en_novo)
    grava32(d, VET_PT, XIP + pt_novo)
    grava32(d, LIT_EN, XIP + en_novo)
    grava32(d, LIT_PT, XIP + pt_novo)

    print("  premissas conferidas:")
    print(f"    - sha256 = 2.2.1 exata")
    print(f"    - TBH 0x{TBH:08X} entrada 5 -> 0x{STUB_XIP:08X}")
    print(f"    - cauda 0x{TAIL:08X} = pop.w + b.w 0xD0DAE0")
    print(f"    - rotulos {ROTULOS}, id 5 = {ROTULO_FABRICA}")
    print(f"    - lote 0x{em:06X}..0x{em + EM_TAM:06X} virgem\n")
    print(f"  DESTINO 0x{STUB_XIP:08X}: {STUB_NOVO.hex(' ')}")
    print(f"    movs r3,#0x{PAGINA:02X} / r2,#0 / r1,#2 / r0,#1 / "
          f"b 0x{TAIL:08X}")
    print(f"  TEXTO   id {ID_NOVO} = {TEXTO!r}")
    print(f"    PT 0x{XIP + pt_novo:08X}  ({N_NOVO} ponteiros)")
    print(f"    EN 0x{XIP + en_novo:08X}  ({N_NOVO} ponteiros)")
    print(f"    string 0x{XIP + txt:08X}")
    print(f"    literais 0x{LIT_EN:06X}/0x{LIT_PT:06X} e vetores "
          f"0x{VET_EN:06X}/0x{VET_PT:06X} repontados")
    print(f"    rotulo 0x{ROTULO:06X}: {ROTULO_FABRICA} -> {ID_NOVO}\n")

    erros = confere_resultado(d, orig, em, tab_pt, tab_en, txt)
    if erros:
        print("  RECUSADO — a imagem montada nao passa na conferencia:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    fora = [i for i in dif if not any(x <= i < y for x, y in PERMITIDO)]
    if fora:
        print(f"  RECUSADO: escreveu fora do permitido em "
              f"0x{min(fora):06X}..0x{max(fora):06X}", file=sys.stderr)
        return 1
    if any(i < 0xE000 for i in dif) or any(0xD000 <= i < 0xE000 for i in dif):
        print("  RECUSADO: alterou abaixo de 0xE000 ou o setor 0xD000",
              file=sys.stderr)
        return 1
    if any(i >= 0x1FC000 for i in dif):
        print("  RECUSADO: alterou a PSMP", file=sys.stderr)
        return 1
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
