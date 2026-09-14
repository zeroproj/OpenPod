#!/usr/bin/env python3
"""
patch_texto_branco_fixo.py — o texto que era BRANCO FIXO passa a ler a tabela.

O QUE O DIAGNOSTICO MOSTROU

    Com `cor_texto = AZUL` na tabela, os digitos do relogio sairam
    BRANCOS. Nao e cor herdada: e branco escrito no codigo.

    No tema claro `cor_tela` e branco — e **branco sobre branco some**.
    Era essa a "tela que as vezes fica branca" que o mantenedor relatou.
    Nao era falha de redesenho: e um elemento que desaparece.

O CENSO, ANTES DE CONSERTAR

    `set_style_text_color` tem 50 chamadas no firmware:

        constante/desconhecida ............ 24
        getter claro (ja le cor_texto) .... 10
        BRANCO FIXO (mov.w rX,#-1) ........  8   <- estes
        palette_main ......................  6
        getter de PRETO ...................  1
        getter da home (ja le cor_texto) ..  1

    Os oito de branco fixo, todos com **r1** como destino:

        0x00123686  0x001236B0  0x001236CA   view_set_icon_bat
        0x001238E8  0x00123912   (o icone de bateria da faixa)
        0x00128DD0  0x00128F14  0x00128FBA   page_bt_menu_scr_process

O CONSERTO

    `mov.w r1,#-1` ocupa 4 bytes. Um `bl` tambem. Entao cada ponto vira
    uma chamada a uma rotina de 8 bytes na area livre:

        ldr  r1, =0x00DA5400
        ldrh r1, [r1, #6]        <- cor_texto
        bx   lr

    Escreve so em **r1** e em **lr**. E `lr` ja esta comprometido nesses
    pontos: a instrucao seguinte a cada um e o proprio
    `bl set_style_text_color`. Se a funcao nao tivesse salvo `lr`, ela ja
    estaria quebrada antes de nos. Guarda conferida ponto a ponto.

O QUE ISTO **NAO** CONSERTA — dito antes

    Os **digitos do relogio nao estao entre os oito**. Eles vem de um dos
    24 pontos de origem nao identificada, e eu nao vou dizer que consertei
    o que nao medi. A tela de relogio continua com o defeito.

    Tambem ficam de fora os 6 pontos de `palette_main` e os 24
    desconhecidos.

SOBRE A BATERIA

    Cinco dos oito sao o icone de bateria da faixa. Hoje ele e branco
    sobre a faixa clara — quase invisivel. Passando a ler `cor_texto`,
    fica preto e legivel.

    **Nao e o alvo.** `marte/mockups/marte_completo.png` mostra a bateria
    COLORIDA, em verde, desenhada. Isso e o M4, com os bitmaps em
    `marte/adaptado/icones/battery_0*.png`. Preto e a forma legivel
    ate la, e esta registrado como interino.

USO
    python3 tools/patch_texto_branco_fixo.py --in <e.bin> --out <s.bin>
                                             [--em 0x1A6000] [--dry-run]
"""

import argparse, hashlib, struct, sys

XIP      = 0x00C00000
TAB      = 0x00DA5400
TC       = 0x00D4D10A      # set_style_text_color
PROIBIDO = 0x0000D000
EM_PADRAO = 0x001A6000

# (offset do mov.w, offset do set_style_text_color que ele alimenta)
PONTOS = [
    (0x00123686, 0x0012368C, "view_set_icon_bat"),
    (0x001236B0, 0x001236B6, "view_set_icon_bat"),
    (0x001236CA, 0x001236CE, "view_set_icon_bat"),
    (0x001238E8, 0x001238EE, "view_set_icon_bat"),
    (0x00123912, 0x00123918, "view_set_icon_bat"),
    (0x00128DD0, 0x00128DD6, "page_bt_menu_scr_process"),
    (0x00128F14, 0x00128F18, "page_bt_menu_scr_process"),
    (0x00128FBA, 0x00128FC0, "page_bt_menu_scr_process"),
]


def enc_bl(origem, destino):
    off = destino - (origem + 4)
    if not -(1 << 24) <= off < (1 << 24) or off & 1:
        raise ValueError("salto fora de alcance")
    off &= (1 << 25) - 1
    S = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    return struct.pack("<HH", 0xF000 | (S << 10) | ((off >> 12) & 0x3FF),
                       0xD000 | (((~i1 & 1) ^ S) << 13) | (((~i2 & 1) ^ S) << 11)
                       | ((off >> 1) & 0x7FF))


def dec_bl(origem, b):
    w1, w2 = struct.unpack("<HH", b)
    if (w1 & 0xF800) != 0xF000 or (w2 & 0xD000) != 0xD000:
        return None
    S = (w1 >> 10) & 1
    j1, j2 = (w2 >> 13) & 1, (w2 >> 11) & 1
    off = (S << 24) | (((~(j1 ^ S)) & 1) << 23) | (((~(j2 ^ S)) & 1) << 22) \
        | ((w1 & 0x3FF) << 12) | ((w2 & 0x7FF) << 1)
    return origem + 4 + (off - (1 << 25) if S else off)


def main():
    ap = argparse.ArgumentParser(description="texto branco fixo -> tabela")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", type=lambda x: int(x, 0), default=EM_PADRAO)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != 0x200000:
        print(f"ERRO: {a.src} tem {len(d)} B", file=sys.stderr)
        return 1
    orig = bytes(d)
    ROT = a.em

    print("\n  O TEXTO BRANCO FIXO PASSA A LER A TABELA\n")

    if all(x == 0xFF for x in d[TAB - XIP:TAB - XIP + 0x14]):
        print("  ABORTADO: tabela de tema virgem.", file=sys.stderr)
        return 1
    if any(x != 0xFF for x in d[ROT:ROT + 0x10]):
        print(f"  ABORTADO: 0x{ROT:06X} nao esta virgem.", file=sys.stderr)
        return 1

    # 1. confere os oito pontos ANTES de escrever qualquer coisa
    for mov, setter, onde in PONTOS:
        w1 = struct.unpack_from("<H", d, mov)[0]
        w2 = struct.unpack_from("<H", d, mov + 2)[0]
        if w1 != 0xF04F or (w2 & 0xF0FF) != 0x30FF or ((w2 >> 8) & 0xF) != 1:
            print(f"  ABORTADO: 0x{mov:06X} nao e 'mov.w r1,#-1'.",
                  file=sys.stderr)
            return 1
        if dec_bl(setter + XIP, bytes(d[setter:setter + 4])) != TC:
            print(f"  ABORTADO: 0x{setter:06X} nao chama "
                  f"set_style_text_color.", file=sys.stderr)
            return 1
    print(f"    os 8 pontos conferidos: 'mov.w r1,#-1' + set_style_text_color")
    print()

    # 2. a rotina: le cor_texto para r1 e volta
    rot = bytearray()
    rot += struct.pack("<H", 0x4900 | 1)            # ldr r1,[pc,#4]
    rot += struct.pack("<H", 0x8800 | (3 << 6) | (1 << 3) | 1)  # ldrh r1,[r1,#6]
    rot += struct.pack("<H", 0x4770)                # bx lr
    rot += struct.pack("<H", 0xBF00)                # nop (alinha o literal)
    rot += struct.pack("<I", TAB)                   # o literal
    d[ROT:ROT + len(rot)] = rot
    print(f"    rotina em 0x{ROT:06X}  {len(rot)} B   "
          f"ldr r1,=TAB ; ldrh r1,[r1,#6] ; bx lr")
    print()

    # 3. os oito desvios
    print("  ALTERACOES")
    for mov, setter, onde in PONTOS:
        d[mov:mov + 4] = enc_bl(mov + XIP, ROT + XIP)
        volta = dec_bl(mov + XIP, bytes(d[mov:mov + 4]))
        ok = volta == ROT + XIP
        print(f"    0x{mov:06X}  {onde:<26} mov.w r1,#-1 -> bl rotina  "
              f"{'OK' if ok else 'DIVERGE'}")
        if not ok:
            return 1
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido (R1).", file=sys.stderr)
        return 1
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}\n")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
