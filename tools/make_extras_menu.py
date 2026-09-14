#!/usr/bin/env python3
"""
make_extras_menu.py — Home com 4 itens + submenu "Extras" com 6.

ESTRUTURA DO PATCH

  PARTE A — a home (pagina 1) passa a mostrar 4 itens
      Musica · Imagem · Extras · Configurar

  PARTE B — a pagina 0x53 (page_home_menu), hoje uma lista morta de 3
      itens, passa a ser o Extras com 6:
      Video · Gravacao · Radio · Livro digital · Bluetooth · Ver pastas

  ROTEAMENTO — o Enter do Extras e enviado como se viesse da HOME
      (page=1, grp=2, ctrl_id=indice_na_home). Assim roda o bloco
      ORIGINAL de cada item em page1_process, com todas as verificacoes
      de cartao, volume e indice, e as mensagens de erro.

POR QUE NAO UMA TABELA DE DESTINOS

    So 4 dos 9 itens da home abrem por `movs r3,#destino`. Os outros
    cinco verificam cartao, volume e indice sujo, mostram mensagem e as
    vezes disparam uma VARREDURA ASSINCRONA antes de abrir. Uma tabela de
    destinos jogaria tudo isso fora: "Video" sem cartao abriria uma tela
    vazia em vez de dizer "Nao foram detectados ficheiros de video".

    Ver docs/MENU_HIERARQUIA.md secoes 13 e 14.

ESTRUTURA DE MEMORIA DA TELA DE 6 ITENS

    Esquema confirmado em page_set_menu (10 itens): rotulos = N*4,
    icones = 2*N*4.

        botoes 0x00   rotulos 0x18   icones 0x30   indice 0x48
        malloc 0x4C

    ⚠️ Este e o unico patch do projeto que mexe em ALOCACAO e aritmetica
    de ponteiro. Errar um offset corrompe a heap, e corrupcao de heap NAO
    aparece na verificacao byte a byte pos-gravacao. Por isso cada ponto
    tem guarda individual e a ferramenta recusa tudo se um so divergir.

CODIGO NOVO NA AREA LIVRE

    Um trecho curto de Thumb-2 substitui a convergencia do event_cb da
    lista: mapeia o indice do Extras para o indice da home e envia a
    mensagem. Leitura e execucao por XIP da area livre foram CONFIRMADAS
    nos V017 e V020.

USO
    python3 tools/make_extras_menu.py \
        --in  firmware/WORKING/GN438_openpod_v021.bin \
        --out firmware/WORKING/GN438_openpod_v022.bin [--dry-run]

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se QUALQUER um dos pontos nao estiver no valor esperado;
    - recusa se a area livre de destino nao estiver toda em 0xFF;
    - decodifica de volta os saltos que gera e compara os alvos.

ENDERECO EXPLICITO (--em)

    Por padrao esta ferramenta ALOCAVA sozinha na area livre, o que fazia
    o endereco depender de tudo que rodou antes. Com `--em 0x1A3600` quem
    chama declara onde. Ver `tools/build.py` para o motivo.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

XIP = 0x00C00000

# ---------------------------------------------------------------- layout
IMG_DESC = 0x000CDD50
PIX_OFF = 0x000CE15C
IMG_W, IMG_H = 128, 160
BG, FG = 1, 0
BANDAS = [(0, 4, 2), (5, 9, 3), (10, 15, 4)]
SEP_Y, SEP_IDX = 16, 5
LISTA_Y0 = 19
LABEL_X, CHEVRON_X, CHEVRON_DY = 6, 116, 3
CHEVRON = ["##....", ".##...", "..##..", "...##.", "....##",
           "...##.", "..##..", ".##...", "##...."]

TBL_ICON = 0x0004867C
TBL_LABEL = 0x000486A0
TBL_IDS = 0x000486C4

# home: 4 itens. ids na tabela do portugues realocada.
HOME_IDS = [1, 4, 216, 10]          # Musica, Imagem, Extras, Configurar
# linhas: as 4 primeiras do espacamento de 9 do V018
HOME_YS = [19, 35, 50, 66]

# Extras: 6 itens (id de texto, indice do MESMO item na home)
EXTRAS = [(3, 1), (5, 2), (6, 3), (2, 4), (9, 6), (8, 8)]
#          Video  Grav   Radio  Livro  BT     Pastas

# --------------------------------------------------- pontos de 1/2/4 bytes
# (offset, bytes esperados, bytes novos, descricao)
PONTOS = [
    # --- A: tabela de saltos de page1_process (12 halfwords em 0x100FBE)
    (0x00100FC0, "5400", "f800", "tbh idx1 -> bloco da Imagem"),
    (0x00100FC2, "9c00", "8f01", "tbh idx2 -> bloco do Extras"),
    (0x00100FC4, "bf00", "3e01", "tbh idx3 -> bloco do Configurar"),
    # --- A: o bloco morto do idx11 vira o bloco do Extras
    (0x001012DC, "1e23", "5323", "movs r3,#0x1e -> #0x53  (pagina destino)"),
    (0x001012DE, "0b22", "0222", "movs r2,#0xb  -> #2     (ctrl_id)"),
    # --- A: limite do laco de criacao da home
    (0x0012ED88, "242d", "102d", "cmp r5,#0x24 -> #0x10   (4 itens)"),
    # --- A: limites e voltas de indice no event_cb da home
    (0x0012EA66, "082a", "032a", "cmp r2,#8 -> #3   guarda do Enter"),
    (0x0012EA44, "0832", "0332", "addls r2,#8 -> #3 volta do ramo -1"),
    (0x0012EA4A, "082a", "032a", "cmp r2,#8 -> #3   apos -1"),
    (0x0012EA4E, "0822", "0322", "movs r2,#8 -> #3  volta de tecla -1"),
    (0x0012EAD6, "082a", "032a", "cmp r2,#8 -> #3   ramo +1"),
    (0x0012EB2E, "0829", "0329", "cmp r1,#8 -> #3   ramo +1 de tecla"),
    (0x0012EB70, "083a", "033a", "subs r2,#8 -> #3  volta do ramo +1"),
    # --- ROTEAMENTO: guarda de pagina de page1_process
    (0x00100F4E, "987a", "012a", "ldrb r0,[r3,#0xa] -> cmp r2,#1"),
    (0x00100F50, "8242", "00bf", "cmp r2,r0 -> nop"),
    # --- B: a tela de lista passa de 3 para 6 itens
    (0x0012F0A4, "2820", "4c20", "malloc 0x28 -> 0x4C"),
    (0x0012F0C2, "2822", "4c22", "memset 0x28 -> 0x4C"),
    (0x0012F246, "022e", "052e", "cmp r6,#2 -> #5"),
    (0x0012F2B6, "03ab", "1b4b", "add r3,sp,#0xc -> ldr r3,[pc,#0x6c]"),
    (0x0012F2DA, "032e", "062e", "cmp r6,#3 -> #6   contagem de itens"),
    (0x0012F2DC, "c8f80c90", "c8f81890", "vetor de rotulos 0x0C -> 0x18"),
    (0x0012F2E0, "c8f818a0", "c8f830a0", "vetor de icones  0x18 -> 0x30"),
    (0x0012F2FA, "d868", "9869", "ldr r0,[r3,#0xc] -> #0x18"),
    (0x0012F302, "87f82630", "87f84830", "indice em [r7,#0x26] -> #0x48"),
    (0x0012F3E2, "022b", "052b", "cmp r3,#2 -> #5   btn_process/nav"),
    (0x0012F406, "022b", "052b", "cmp r3,#2 -> #5   btn_process/texto"),
    (0x0012F40E, "e868", "a869", "ldr r0,[r5,#0xc] -> #0x18"),
    (0x0012F414, "ad69", "2d6b", "ldr r5,[r5,#0x18] -> #0x30"),
    (0x0012F486, "db68", "9b69", "ldr r3,[r3,#0xc] -> #0x18"),
    # --- B: cadeia de 3 comparacoes -> laco de 6
    (0x0012EFF6,
     "236898420fd063689842" + "0ed0a3689842" + "08d10224",
     "0026" + "54f82630" + "9842" + "03d0" + "0136" + "062e" + "f8d1"
     + "08e0" + "3446",
     "objeto clicado -> indice: cadeia de 3 vira laco de 6"),
]

POOL_IDS_EXTRAS = 0x0012F324        # pool da tabela de ids da lista
POOL_IDS_ESPERADO = 0x00C486E8
CONVERGENCIA = 0x0012F00A           # 4 B: b.w para a rotina na area livre

LIVRE_FIM = 0x001FC000


# ------------------------------------------------------------- utilitarios
def enc_bw(origem, destino, link=False):
    off = destino - (origem + 4)
    assert -(1 << 24) <= off < (1 << 24) and not off & 1, "fora de alcance"
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    imm10, imm11 = (off >> 12) & 0x3FF, (off >> 1) & 0x7FF
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    hw1 = 0xF000 | (s << 10) | imm10
    hw2 = (0xD000 if link else 0x9000) | (j1 << 13) | (j2 << 11) | imm11
    return struct.pack("<HH", hw1, hw2)


def dec_bw(origem, blob):
    hw1, hw2 = struct.unpack("<HH", blob)
    s, imm10 = (hw1 >> 10) & 1, hw1 & 0x3FF
    j1, j2, imm11 = (hw2 >> 13) & 1, (hw2 >> 11) & 1, hw2 & 0x7FF
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if s:
        off -= 1 << 25
    return origem + 4 + off, bool(hw2 & 0x4000)


def firm_entry(d):
    pt = struct.unpack_from("<I", d, 0x20)[0]
    n = struct.unpack_from("<I", d, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if d[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", d, b + 4)
            return b, off, ln
    raise RuntimeError("FIRM nao encontrada")


def proximo_livre(d, ini=0x001A3038, em=None):
    if em is not None:
        return em
    fim = ini
    for i in range(ini, ini + 0x4000):
        if d[i] != 0xFF:
            fim = i + 1
    return (fim + 3) & ~3


def desenha_folha(d, ys):
    for i in range(IMG_W * IMG_H):
        d[PIX_OFF + i] = BG
    for y0, y1, pi in BANDAS:
        for y in range(y0, y1 + 1):
            for x in range(IMG_W):
                d[PIX_OFF + y * IMG_W + x] = pi
    for x in range(IMG_W):
        d[PIX_OFF + SEP_Y * IMG_W + x] = SEP_IDX
    for y0 in ys:
        for dy, linha in enumerate(CHEVRON):
            for dx, c in enumerate(linha):
                if c == "#":
                    x, y = CHEVRON_X + dx, y0 + CHEVRON_DY + dy
                    if 0 <= x < IMG_W and 0 <= y < IMG_H:
                        d[PIX_OFF + y * IMG_W + x] = FG


def main():
    ap = argparse.ArgumentParser(description="Home com 4 itens + Extras")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", type=lambda x: int(x, 0), default=None,
                    help="endereco EXPLICITO da rotina/strings")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2
    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 74)
    print("OpenPod — home com 4 itens + submenu Extras  (V021 -> V022)")
    print("=" * 74)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    # ---------------------------------------------------------- conferencia
    erros = []
    for off, esp, novo, desc in PONTOS:
        e, n = bytes.fromhex(esp), bytes.fromhex(novo)
        if len(e) != len(n):
            erros.append(f"0x{off:06X}: esperado e novo tem tamanhos "
                         f"diferentes ({len(e)} vs {len(n)}) — {desc}")
        elif bytes(d[off:off + len(e)]) != e:
            erros.append(f"0x{off:06X}: {bytes(d[off:off+len(e)]).hex()} != "
                         f"{esp}  ({desc})")
    got = struct.unpack_from("<I", d, POOL_IDS_EXTRAS)[0]
    if got != POOL_IDS_ESPERADO:
        erros.append(f"0x{POOL_IDS_EXTRAS:06X}: pool 0x{got:08X} != "
                     f"0x{POOL_IDS_ESPERADO:08X}")
    hdr = struct.unpack_from("<I", d, IMG_DESC)[0]
    if (hdr & 0x1F, (hdr >> 10) & 0x7FF, (hdr >> 21) & 0x7FF) != (10, IMG_W, IMG_H):
        erros.append("descritor da folha inesperado")
    if erros:
        print(f"  ABORTADO — {len(erros)} ponto(s) fora do esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print(f"  estado de entrada conferido: {len(PONTOS)} pontos + pool + "
          "folha  OK")
    print()

    # ----------------------------------------------- area livre: dados/codigo
    cur = proximo_livre(d, em=a.em)
    # confere a virgindade ANTES de escrever qualquer coisa
    reserva = len(EXTRAS) * 4 + len(EXTRAS) + 4 + 64
    if any(b != 0xFF for b in d[cur:cur + reserva]):
        print(f"  ABORTADO: area livre 0x{cur:06X}..0x{cur+reserva:06X} "
              "nao esta virgem.", file=sys.stderr)
        return 1
    if cur + reserva > LIVRE_FIM:
        print("  ABORTADO: nao cabe na area livre.", file=sys.stderr)
        return 1
    tbl_ids = cur
    for i, (sid, _) in enumerate(EXTRAS):
        struct.pack_into("<I", d, tbl_ids + i * 4, sid)
    cur += len(EXTRAS) * 4

    mapa = cur
    for i, (_, hidx) in enumerate(EXTRAS):
        d[mapa + i] = hidx
    cur = (cur + len(EXTRAS) + 3) & ~3

    rotina = cur
    # ldr r2,[pc,#8] ; ldrb r2,[r2,r4] ; movs r3,#4 ; movs r1,#2 ;
    # movs r0,#1 ; bl view_send ; ldr r3,[pc,#8] ; strb r4,[r3] ;
    # pop {r4,r5,r6,pc}  ; .word MAPA ; .word 0x00823D84
    corpo = bytearray()
    corpo += bytes.fromhex("044a")          # ldr  r2,[pc,#16] -> MAPA
    corpo += bytes.fromhex("125d")          # ldrb r2,[r2,r4]
    corpo += bytes.fromhex("0423")          # movs r3,#4
    corpo += bytes.fromhex("0221")          # movs r1,#2
    corpo += bytes.fromhex("0120")          # movs r0,#1
    bl_off = rotina + len(corpo)
    corpo += enc_bw(bl_off + XIP, 0x00D23510, link=True)   # bl view_send
    corpo += bytes.fromhex("024b")          # ldr  r3,[pc,#8]
    corpo += bytes.fromhex("1c70")          # strb r4,[r3]
    corpo += bytes.fromhex("70bd")          # pop  {r4,r5,r6,pc}
    assert len(corpo) % 4 == 0, "corpo desalinhado"
    corpo += struct.pack("<I", mapa + XIP)          # .word MAPA
    corpo += struct.pack("<I", 0x00823D84)          # .word global do indice
    d[rotina:rotina + len(corpo)] = corpo
    cur = rotina + len(corpo)

    # confere os DOIS ldr literais decodificando o proprio encoding
    def alvo_ldr(pos):
        hw = struct.unpack_from("<H", corpo, pos)[0]
        assert (hw & 0xF800) == 0x4800, "nao e ldr literal"
        return (((rotina + pos + 4) & ~3) + (hw & 0xFF) * 4)
    esperados = ((0, rotina + len(corpo) - 8, mapa + XIP, "MAPA"),
                 (14, rotina + len(corpo) - 4, 0x00823D84, "indice global"))
    for pos, palavra, valor, nome in esperados:
        got = alvo_ldr(pos)
        lido = struct.unpack_from("<I", corpo, palavra - rotina)[0]
        if got != palavra or lido != valor:
            print(f"  ABORTADO: literal {nome}: ldr aponta 0x{got:06X}, "
                  f"palavra em 0x{palavra:06X} vale 0x{lido:08X}",
                  file=sys.stderr)
            return 1

    print("  AREA LIVRE")
    print(f"    0x{tbl_ids:06X}  tabela de ids do Extras  ({len(EXTRAS)} x 4 B)")
    print(f"    0x{mapa:06X}  mapa Extras -> home      "
          f"{[h for _, h in EXTRAS]}")
    print(f"    0x{rotina:06X}  rotina do Enter          ({len(corpo)} B)")
    print()

    # ------------------------------------------------------- pontos simples
    print("  PONTOS")
    for off, esp, novo, desc in PONTOS:
        n = bytes.fromhex(novo)
        d[off:off + len(n)] = n
        print(f"    0x{off:06X}  {esp:<20}-> {novo:<20}{desc}")
    struct.pack_into("<I", d, POOL_IDS_EXTRAS, tbl_ids + XIP)
    print(f"    0x{POOL_IDS_EXTRAS:06X}  {POOL_IDS_ESPERADO:08X}"
          f"            -> {tbl_ids + XIP:08X}            "
          "pool da tabela de ids do Extras")
    salto = enc_bw(CONVERGENCIA + XIP, rotina + XIP)
    alvo, link = dec_bw(CONVERGENCIA + XIP, salto)
    if alvo != rotina + XIP or link:
        print("  ABORTADO: o b.w da convergencia nao confere na volta.",
              file=sys.stderr)
        return 1
    d[CONVERGENCIA:CONVERGENCIA + 4] = salto
    print(f"    0x{CONVERGENCIA:06X}  convergencia          -> "
          f"b.w 0x{rotina + XIP:08X}  (conferido na volta)")
    print()

    # ------------------------------------------------------- home: 4 itens
    for i, sid in enumerate(HOME_IDS):
        struct.pack_into("<I", d, TBL_IDS + i * 4, sid)
    for i, y in enumerate(HOME_YS):
        struct.pack_into("<hh", d, TBL_LABEL + i * 4, LABEL_X, y)
        struct.pack_into("<hh", d, TBL_ICON + i * 4, CHEVRON_X, y)
    desenha_folha(d, HOME_YS)
    print("  HOME")
    print(f"    0x{TBL_IDS:06X}  ids {HOME_IDS}  "
          "(Musica, Imagem, Extras, Configurar)")
    print(f"    0x{TBL_LABEL:06X}  rotulos  y {HOME_YS}")
    print(f"    0x{TBL_ICON:06X}  chevrons y {HOME_YS}")
    print(f"    0x{PIX_OFF:06X}  folha com {len(HOME_YS)} chevrons")
    print()

    # ------------------------------------------------------------------ CRC
    base, foff, flen = firm_entry(d)
    old = struct.unpack_from("<H", d, base + 0x0C)[0]
    new = fw.crc16(bytes(d[foff:foff + flen]))
    if a.dry_run:
        print(f"  CRC da FIRM: 0x{old:04X} -> 0x{new:04X} (nao gravado)")
    else:
        # R1: NAO gravar o CRC da FIRM. Ele nao e verificado pelo
        # aparelho, e escrever aqui poe o setor 0x00D000 (tabela de
        # particoes) de volta na lista de setores — foi ele que matou
        # o primeiro aparelho. Achado pelo tools/build.py.
        pass   # NAO gravar o CRC (R1)
        print(f"  CRC da FIRM: 0x{old:04X} -> 0x{new:04X}")

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}")
    print("    " + "  ".join(f"0x{s:06X}" for s in secs))
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
