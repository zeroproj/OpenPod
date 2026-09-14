#!/usr/bin/env python3
"""
fix_status_bar.py — Corrige os dois defeitos do V016 na faixa superior.

O QUE DEU ERRADO NO V016

    1. TITULO NO LABEL ERRADO. A faixa tem dois labels de icone parecidos,
       e eu patcheei o que NAO aparece:

         view_p[0x14]  criado em 0x00D226AC  glifo U+F0C7 (disquete)
                       condicao: cartao presente (0xCFE714 != 0)
                       -> E ESTE que aparece na tela

         view_p[0x18]  criado em 0x00D226F8  glifo U+E647
                       condicao: flag em RAM 0x008238EB != 0
                       -> nunca criado na home; a flag esta em 0

       O patch do V016 estava byte a byte correto -- e simplesmente nunca
       executava. O disassembly do V016 mostra o ponteiro resolvendo para
       "OpenPod" em 0x00DA3038, o que confirma que o defeito nao era o
       patch, era a ESCOLHA do alvo.

    2. BARRA CLARA DEMAIS. O degrade usou os cinzas que ja existiam na
       paleta da folha -- o mais escuro disponivel era (28,32,38). Na tela
       isso ficou proeminente. A folha usa hoje apenas 6 dos 256 indices
       de paleta, entao da para DEFINIR o tom exato em vez de garimpar.

O QUE ESTA FERRAMENTA FAZ

    A. Reverte os 5 pontos do V016 em 0x00D226F8 ao valor de fabrica.
       Importante: sem reverter, se aquela flag algum dia ficar != 0, o
       titulo apareceria no meio da tela por cima de outra coisa.

    B. Aplica o titulo em 0x00D226AC, o label que realmente aparece:
         0x001226BA  mvn r2,#0x1d (x_ofs=-30) -> movs r2,#4 ; nop
         0x001226BE  movs r1,#3 (TOP_RIGHT)   -> movs r1,#2 (TOP_MID)
         0x001226CA  bl set_style_text_font   -> 2x NOP (fonte padrao)
         0x001226F4  ponteiro do texto        -> 0x00DA3038 ("OpenPod")

    C. Define 4 entradas de paleta NOVAS e repinta a barra com elas.

    A string "OpenPod" ja esta em 0x001A3038 desde o V016; esta ferramenta
    so confere que continua la.

O QUE SE PERDE

    O icone de disquete (U+F0C7) da faixa. Ele indicava cartao presente.
    E o mesmo tipo de troca que o V016 pretendia fazer -- so que agora no
    objeto certo.

RESSALVA

    O label e criado apenas com cartao presente. Sem cartao, o titulo nao
    aparece. Nao existe label incondicional na faixa alem do relogio.

USO
    python3 tools/fix_status_bar.py \
        --in  firmware/WORKING/GN438_openpod_v016.bin \
        --out firmware/WORKING/GN438_openpod_v017.bin [--dry-run]

DEPENDENCIAS
    Python 3 + tools/fw_common.py
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

FLASH_XIP = 0x00C00000
STR_OFF = 0x001A3038
STR_ADDR = STR_OFF + FLASH_XIP

# --- A: reverter o label invisivel (0x00D226F8) ---------------------------
REVERTER = [
    (0x00122702, 0x02, 0x00, "y_ofs  -> 0x00 (original)"),
    (0x00122706, 0x04, 0x28, "x_ofs  -> 0x28 (original)"),
    (0x00122708, 0x02, 0x01, "align  -> 1 TOP_LEFT (original)"),
]
REV_BL = (0x00122714, bytes.fromhex("00bf00bf"), bytes.fromhex("2af00bfd"),
          "NOP NOP -> bl set_style_text_font (original)")
REV_POOL = (0x00122740, STR_ADDR, 0x00C5D608, "ponteiro do texto (original)")

# --- B: aplicar no label visivel (0x00D226AC) -----------------------------
NOVO_XOFS = (0x001226BA, bytes.fromhex("6ff01d02"), bytes.fromhex("042200bf"),
             "mvn r2,#0x1d (x=-30) -> movs r2,#4 ; nop")
NOVO_ALIGN = (0x001226BE, 0x03, 0x02, "align  3 TOP_RIGHT -> 2 TOP_MID")
NOVO_BL = (0x001226CA, bytes.fromhex("2af030fd"), bytes.fromhex("00bf00bf"),
           "bl set_style_text_font -> 2x NOP (fonte padrao)")
NOVO_POOL = (0x001226F4, 0x00C5D614, STR_ADDR, "ponteiro do texto -> OpenPod")

# --- C: paleta nova e barra ----------------------------------------------
PAL_OFF = 0x000CDD5C
PIX_OFF = 0x000CE15C
IMG_DESC = 0x000CDD50
IMG_W, IMG_H = 128, 160
BG_INDEX = 1
BARRA_ALTURA = 16

# indice -> (R, G, B). Precisam estar LIVRES nos pixels da folha.
PALETA_NOVA = {
    2: (20, 22, 26),     # topo da barra
    3: (14, 16, 19),     # meio
    4: (9, 10, 12),      # base
    5: (52, 56, 62),     # separador
}
BANDAS = [(0, 3, 2), (4, 8, 3), (9, 12, 4)]
SEPARADOR_Y, SEPARADOR_IDX = 13, 5

# indices que o V016 deixou na barra e que vamos substituir
V016_BARRA = {234, 33, 84, 181}


def firm_entry(data):
    pt = struct.unpack_from("<I", data, 0x20)[0]
    n = struct.unpack_from("<I", data, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if data[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", data, b + 4)
            return b, off, ln
    raise RuntimeError("particao FIRM nao encontrada")


def check(data):
    e = []

    hdr = struct.unpack_from("<I", data, IMG_DESC)[0]
    cf, w, h = hdr & 0x1F, (hdr >> 10) & 0x7FF, (hdr >> 21) & 0x7FF
    if (cf, w, h) != (10, IMG_W, IMG_H):
        e.append(f"descritor da folha inesperado: cf={cf} {w}x{h}")

    if data[STR_OFF:STR_OFF + 8] != b"OpenPod\0":
        e.append(f"a string em 0x{STR_OFF:06X} nao e 'OpenPod' — "
                 "a entrada nao parece ser o V016")

    for off, esp, _, d_ in REVERTER + [NOVO_ALIGN]:
        if data[off] != esp:
            e.append(f"0x{off:06X}: esperado 0x{esp:02X}, "
                     f"encontrado 0x{data[off]:02X} ({d_})")
    for off, esp, _, d_ in (REV_BL, NOVO_BL, NOVO_XOFS):
        if bytes(data[off:off + len(esp)]) != esp:
            e.append(f"0x{off:06X}: bytes inesperados ({d_})")
    for off, esp, _, d_ in (REV_POOL, NOVO_POOL):
        got = struct.unpack_from("<I", data, off)[0]
        if got != esp:
            e.append(f"0x{off:06X}: pool 0x{got:08X}, "
                     f"esperado 0x{esp:08X} ({d_})")

    # as entradas de paleta que vamos redefinir nao podem estar em uso
    usados = set(data[PIX_OFF:PIX_OFF + IMG_W * IMG_H])
    for i in PALETA_NOVA:
        if i in usados:
            e.append(f"indice de paleta {i} esta EM USO na folha — "
                     "nao pode ser redefinido")

    # fora da barra, a folha so pode ter fundo e chevrons
    fora = set()
    for y in range(BARRA_ALTURA, IMG_H):
        for x in range(IMG_W):
            fora.add(data[PIX_OFF + y * IMG_W + x])
    if fora & V016_BARRA:
        e.append("os tons da barra do V016 aparecem FORA da faixa superior; "
                 "repintar mudaria outra coisa")
    return e


def main():
    ap = argparse.ArgumentParser(
        description="Corrige a faixa superior: titulo no label certo, "
                    "barra mais discreta")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if os.path.abspath(args.src) == os.path.abspath(args.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    with open(args.src, "rb") as fh:          # somente leitura
        orig = fh.read()
    data = bytearray(orig)

    print("=" * 72)
    print("OpenPod — correcao da faixa superior (V016 -> V017)")
    print("=" * 72)
    print(f"  origem : {args.src}")
    print(f"  destino: {args.dst}")
    print()

    erros = check(data)
    if erros:
        print("  ABORTADO — o firmware de entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print("  estado de entrada conferido: V016 aplicado, string presente, "
          "indices de paleta 2-5 livres  OK")
    print()

    print("  A — REVERTE o label que nunca e criado (0x00D226F8)")
    for off, _, novo, d_ in REVERTER:
        data[off] = novo
        print(f"    0x{off:06X}  -> {novo:02X}   {d_}")
    off, _, novo, d_ = REV_BL
    data[off:off + 4] = novo
    print(f"    0x{off:06X}  -> {novo.hex()}   {d_}")
    off, _, novo, d_ = REV_POOL
    struct.pack_into("<I", data, off, novo)
    print(f"    0x{off:06X}  -> 0x{novo:08X}   {d_}")
    print()

    print("  B — APLICA o titulo no label que aparece (0x00D226AC)")
    off, _, novo, d_ = NOVO_XOFS
    data[off:off + 4] = novo
    print(f"    0x{off:06X}  -> {novo.hex()}   {d_}")
    off, _, novo, d_ = NOVO_ALIGN
    data[off] = novo
    print(f"    0x{off:06X}  -> {novo:02X}   {d_}")
    off, _, novo, d_ = NOVO_BL
    data[off:off + 4] = novo
    print(f"    0x{off:06X}  -> {novo.hex()}   {d_}")
    off, _, novo, d_ = NOVO_POOL
    struct.pack_into("<I", data, off, novo)
    print(f"    0x{off:06X}  -> 0x{novo:08X}   {d_}")
    print()

    print("  C — PALETA NOVA e barra repintada")
    for i, (r, g, b) in PALETA_NOVA.items():
        ant = (data[PAL_OFF + i * 4 + 2], data[PAL_OFF + i * 4 + 1],
               data[PAL_OFF + i * 4])
        data[PAL_OFF + i * 4 + 0] = b
        data[PAL_OFF + i * 4 + 1] = g
        data[PAL_OFF + i * 4 + 2] = r
        data[PAL_OFF + i * 4 + 3] = 0xFF
        print(f"    idx {i:>3}  {str(ant):<18} -> {(r, g, b)}")
    for y0, y1, pi in BANDAS:
        for y in range(y0, y1 + 1):
            for x in range(IMG_W):
                data[PIX_OFF + y * IMG_W + x] = pi
    for x in range(IMG_W):
        data[PIX_OFF + SEPARADOR_Y * IMG_W + x] = SEPARADOR_IDX
    for y in range(SEPARADOR_Y + 1, BARRA_ALTURA):
        for x in range(IMG_W):
            data[PIX_OFF + y * IMG_W + x] = BG_INDEX
    faixas = " ".join(f"y{a}-{b}:idx{i}" for a, b, i in BANDAS)
    print(f"    barra: [{faixas} · y{SEPARADOR_Y}:idx{SEPARADOR_IDX} · "
          f"y14-15:fundo]")
    print()

    base, foff, flen = firm_entry(data)
    old_crc = struct.unpack_from("<H", data, base + 0x0C)[0]
    new_crc = fw.crc16(bytes(data[foff:foff + flen]))
    if args.dry_run:
        print(f"  CRC da FIRM: 0x{old_crc:04X} -> 0x{new_crc:04X} (nao gravado)")
    else:
        # R1: o CRC da FIRM nao e verificado pelo aparelho, e gravar aqui
        # poria o setor 0x00D000 (tabela de particoes) de volta na lista
        # de setores a escrever. Foi esse setor que matou o primeiro
        # aparelho. Achado pelo tools/build.py ao reconstruir do zero.
        pass   # NAO gravar o CRC (R1)
        print(f"  CRC da FIRM: 0x{old_crc:04X} -> 0x{new_crc:04X}")

    d2 = [i for i in range(len(orig)) if orig[i] != data[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in d2})
    print(f"  bytes alterados: {len(d2)}   tamanho: inalterado ({len(data)})")
    print(f"  setores de 4 KiB a regravar: {len(secs)}")
    print("    " + "  ".join(f"0x{s:06X}" for s in secs))
    print()

    if args.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0

    with open(args.dst, "wb") as fh:
        fh.write(data)
    print(f"  gravado: {args.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
