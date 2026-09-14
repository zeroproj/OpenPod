#!/usr/bin/env python3
"""
patch_fundo_lista.py — o fundo do CONTEINER e da LINHA passa a vir da tabela.

O QUE O APARELHO MOSTROU (2026-09-14, com a Core 2.1)

    Na home, tema claro perfeito: fundo branco, texto preto, barra azul.
    No Configurar, **os rotulos sumiram**: linhas escuras, texto preto.
    So aparecia o item selecionado, porque a barra azul o destaca.

A CAUSA — a sexta vez do mesmo padrao

    Os dois criadores compartilhados pintam fundo com PRETO FIXO:

        0x001216D0   CRIA_CONTEINER   bl 0xD2138A ; set_style_bg_color
        0x0012177C   CRIA_LINHA       bl 0xD2138A ; set_style_bg_color

        0x00D2138A   mov.w r0,#0 ; bx lr     <- preto, do codigo

    A tabela de tema TEM o campo para isso — `cor_tela`, em +0x00 — e ele
    estava praticamente morto: um unico leitor, o thunk do S12 na pagina
    0x18. Enquanto o tema era escuro, preto fixo e `cor_tela` preto davam
    no mesmo e ninguem notou. O Marte separou os dois.

O CONSERTO — 8 bytes, e sem rotina nova

    A rotina que le `cor_tela` JA EXISTE e tem a mesma assinatura do
    getter de preto:

        0x00D2138A   mov.w r0,#0            ; bx lr
        0x00DA5A20   ldr r0,=TAB ; ldrh r0,[r0] ; bx lr

    Substituicao direta. Dois `bl` redirecionados, 4 bytes cada.

    Efeito: `cor_tela` deixa de ser campo morto e passa a pintar o fundo
    de **36 telas de lista** mais o conteiner de todas.

O QUE NAO E TOCADO, E POR QUE

    O getter 0x00D2138A tem **12 chamadores**. Dois deles sao a tela de
    abertura — `0x0012285A` e `0x001228E4`, para onde o
    `patch_fundo_abertura` mandou as funcoes da logo de proposito. A logo
    tem fundo preto e precisa continuar preta.

    Por isso esta ferramenta troca **dois pontos nomeados**, e nao o
    getter. Trocar o getter apagaria a logo junto.

USO
    python3 tools/patch_fundo_lista.py --in <e.bin> --out <s.bin> [--dry-run]

LIMITACOES
    - exige a tabela do Saturno e a rotina de `cor_tela` presentes;
    - recusa se algum dos dois pontos nao estiver chamando o getter de
      preto — ai o firmware nao e o esperado.
"""

import argparse, hashlib, struct, sys

XIP       = 0x00C00000
PRETO     = 0x00D2138A      # mov.w r0,#0 ; bx lr
COR_TELA  = 0x00DA5A20      # ldr r0,=TAB ; ldrh r0,[r0] ; bx lr
TAB       = 0x001A5400
PROIBIDO  = 0x0000D000

PONTOS = [
    (0x001216D0, "CRIA_CONTEINER  o fundo do conteiner"),
    (0x0012177C, "CRIA_LINHA      o fundo de cada linha"),
]
# Nomeados para NAO serem tocados: a logo do boot precisa de preto.
LOGO = (0x0012285A, 0x001228E4)


def enc_bl(origem, destino):
    off = destino - (origem + 4)
    if not -(1 << 24) <= off < (1 << 24) or off & 1:
        raise ValueError("salto fora de alcance")
    off &= (1 << 25) - 1
    S = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    return struct.pack("<HH",
                       0xF000 | (S << 10) | ((off >> 12) & 0x3FF),
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
    if S:
        off -= 1 << 25
    return origem + 4 + off


def main():
    ap = argparse.ArgumentParser(description="fundo da lista pela tabela")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != 0x200000:
        print(f"ERRO: {a.src} tem {len(d)} B", file=sys.stderr)
        return 1
    orig = bytes(d)

    print("\n  O FUNDO DA LISTA VEM DA TABELA\n")

    if all(x == 0xFF for x in d[TAB:TAB + 0x14]):
        print("  ABORTADO: a tabela de tema esta virgem.", file=sys.stderr)
        return 1
    if bytes(d[COR_TELA - XIP:COR_TELA - XIP + 6]) != b"\x01\x48\x00\x88\x70\x47":
        print(f"  ABORTADO: 0x{COR_TELA:08X} nao e a rotina de cor_tela "
              "esperada.", file=sys.stderr)
        return 1
    print(f"    rotina de cor_tela em 0x{COR_TELA:08X}   conferida")
    print()

    for off, desc in PONTOS:
        atual = dec_bl(off + XIP, bytes(d[off:off + 4]))
        if atual == COR_TELA:
            print(f"    0x{off:06X}  {desc}   ja aponta para cor_tela")
            continue
        if atual != PRETO:
            print(f"  ABORTADO: 0x{off:06X} chama 0x{atual:08X}, esperava o "
                  f"getter de preto 0x{PRETO:08X}", file=sys.stderr)
            return 1
        d[off:off + 4] = enc_bl(off + XIP, COR_TELA)
        volta = dec_bl(off + XIP, bytes(d[off:off + 4]))
        ok = volta == COR_TELA
        print(f"    0x{off:06X}  {desc}")
        print(f"                 bl preto -> bl cor_tela   "
              f"{'OK' if ok else 'DIVERGE'}")
        if not ok:
            return 1
    print()

    for off in LOGO:
        alvo = dec_bl(off + XIP, bytes(d[off:off + 4]))
        print(f"    0x{off:06X}  a logo do boot  -> 0x{alvo:08X}  "
              f"{'INTOCADA (preto)' if alvo == PRETO else 'MUDOU — ERRO'}")
        if alvo != PRETO:
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
