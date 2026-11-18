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

O TEXTO "Aplicativos" (id 159)

    O firmware de fabrica ja traz o texto no id 159 em todos os idiomas:
    PT "Aplicativos", EN/FR/DE/IT/ES "APP", NL "Toepassing", ZH "应用" e
    o hebraico correspondente. Nao ha tabela nova, string nova nem
    ponteiro de tabela a repontar; so o id do rotulo 5 da home muda de 4
    para 159.

PREMISSAS, conferidas ANTES de escrever

    - a imagem tem 2 MiB e e a 2.2.1 exata (sha256);
    - a tabela de rotulos da home e [1,3,5,6,2,4,9,10,8] e o id 5 e 4;
    - o TBH de `page1_process` (0xD00FBE, entrada 5 = 0x00F8) leva a
      0xD011AE, e a cauda em 0xD011F2 e `pop.w` + `b.w 0xD0DAE0`;
    - os 10 bytes em 0x1011AE sao o bloco de fabrica;
    - os 10 ponteiros do vetor de idiomas apontam para texto com NUL;
    - as 9 tabelas de idioma tem id 159 com ponteiro XIP e string com NUL.

USO

    python3 tools/fab_apps_home.py --in <2.2.1.bin> --out <3.0.bin>
    python3 tools/fab_apps_home.py --in ... --out ... --dry-run
"""
import argparse
import hashlib
import os
import struct
import sys

XIP = 0x00C00000
TAMANHO = 0x200000
SHA_2_2_1 = ("e477c1e78ac1c88db58d29b030f35d7f11c8d90f45ec695a9b63392e"
             "a9936402")

ID_NOVO = 159
ROTULO = 0x000486D8
ROTULOS = (1, 3, 5, 6, 2, 4, 9, 10, 8)
ROTULO_FABRICA = 4

# vetor de idiomas: 0x48774 aponta para o nome PT; 0x48778..0x48798
# apontam para as 9 tabelas de texto (EN, ZH, FR, DE, IT, ES, HE, NL, PT).
VETOR = tuple(range(0x00048774, 0x00048774 + 10 * 4, 4))
TABELAS = (
    ("EN", 0xC52AA4),
    ("ZH", 0xC523E4),
    ("FR", 0xC52E04),
    ("DE", 0xC52744),
    ("IT", 0xC534C4),
    ("ES", 0xC53EE4),
    ("HE", 0xC53164),
    ("NL", 0xC53824),
    ("PT", 0xC53B84),
)
N_TEXTO = 216

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

PERMITIDO = [(STUB, STUB + len(STUB_NOVO)), (ROTULO, ROTULO + 4)]


def le32(d, off):
    return struct.unpack_from("<I", d, off)[0]


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


def confere_texto(d, nome, p):
    if not (XIP <= p < XIP + TAMANHO):
        return f"{nome}: ponteiro 0x{p:08X} fora da imagem"
    if d.find(b"\0", p - XIP) < 0:
        return f"{nome}: string 0x{p:08X} sem NUL"
    return None


def confere_tabela(d, nome, base):
    """216 ponteiros XIP, cada um para uma string terminada em NUL."""
    erros = []
    off = base - XIP
    if not (0 <= off <= TAMANHO - 4 * N_TEXTO):
        return [f"{nome}: tabela 0x{base:08X} fora da imagem"]
    vals = struct.unpack_from(f"<{N_TEXTO}I", d, off)
    for i, p in enumerate(vals):
        erro = confere_texto(d, f"{nome} id {i}", p)
        if erro:
            erros.append(erro)
    erro = confere_texto(d, f"{nome} id {ID_NOVO}", vals[ID_NOVO])
    if erro:
        erros.append(erro)
    return erros


def confere_premissas(d):
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]
    erros = []
    got = hashlib.sha256(d).hexdigest()
    if got != SHA_2_2_1:
        erros.append(f"sha256 {got}; a entrada tem de ser a 2.2.1 "
                     f"{SHA_2_2_1}")
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
    for off in VETOR:
        erro = confere_texto(d, f"vetor 0x{off:06X}", le32(d, off))
        if erro:
            erros.append(erro)
    for nome, base in TABELAS:
        erros += confere_tabela(d, nome, base)
    return erros


def confere_resultado(d, orig):
    erros = []
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
    for nome, base in TABELAS:
        erro = confere_texto(d, f"{nome} id {ID_NOVO}",
                             le32(d, base - XIP + 4 * ID_NOVO))
        if erro:
            erros.append(erro)
    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    fora = [i for i in dif if not any(x <= i < y for x, y in PERMITIDO)]
    if fora:
        erros.append(f"escreveu fora do permitido em "
                     f"0x{min(fora):06X}..0x{max(fora):06X}")
    return erros


def main():
    ap = argparse.ArgumentParser(description="ficha 021: indice 5 abre Apps")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

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
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    erros = confere_premissas(d)
    if erros:
        print("  RECUSADO — a entrada nao e a 2.2.1 que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    d[STUB:STUB + len(STUB_NOVO)] = STUB_NOVO
    struct.pack_into("<I", d, ROTULO, ID_NOVO)

    print("  premissas conferidas:")
    print(f"    - sha256 = 2.2.1 exata")
    print(f"    - TBH 0x{TBH:08X} entrada 5 -> 0x{STUB_XIP:08X}")
    print(f"    - cauda 0x{TAIL:08X} = pop.w + b.w 0xD0DAE0")
    print(f"    - rotulos {ROTULOS}, id 5 = {ROTULO_FABRICA}")
    print(f"    - 10 ponteiros do vetor de idiomas com texto valido")
    print(f"    - id {ID_NOVO} valido nas {len(TABELAS)} tabelas\n")
    print(f"  DESTINO 0x{STUB_XIP:08X}: {STUB_NOVO.hex(' ')}")
    print(f"    movs r3,#0x{PAGINA:02X} / r2,#0 / r1,#2 / r0,#1 / "
          f"b 0x{TAIL:08X}")
    print(f"  ROTULO  0x{ROTULO:06X}: {ROTULO_FABRICA} -> {ID_NOVO}\n")

    erros = confere_resultado(d, orig)
    if erros:
        print("  RECUSADO — a imagem montada nao passa na conferencia:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
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
