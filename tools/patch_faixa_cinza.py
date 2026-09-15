#!/usr/bin/env python3
"""
patch_faixa_cinza.py — a FAIXA superior deixa de ser preta e vira CINZA,
                       em todas as 52 telas que a usam.

O PEDIDO

    Do mantenedor, depois da Core 2.3:

        "a faixa na home ainda continua preta era assim mesmo?"
        "um cinza ficaria bom, mas que cor pode ser colocada la para
         nao apagar o branco?"

    Era assim mesmo: a `CRIA_FAIXA` pinta PRETO, e o fundo da tela ja
    era preto. O M-c so acrescentou o traco de 1 px. A faixa nunca foi
    um elemento visivel por si.

A COR — derivada do Marte, nao escolhida por gosto

    No `marte/paleta/nanoclone.json` (tema CLARO), a faixa tem 56% da
    luminancia do conteudo, e puxa levemente para o AZUL:

        faixa base       RGB(189,198,205)     b > r
        conteudo         RGB(255,255,255)

    Invertendo a relacao para o tema escuro — que e o desvio ja
    registrado em `MARTE_ALVO.md` §0-bis — a faixa fica ~25% de luz
    ACIMA do preto, mantendo o mesmo tom azulado:

        RGB( 56, 60, 72)     RGB565 0x39E9     pre-invertido 0xE939

CONTRASTE — medido, que era a pergunta do mantenedor

    O limite de legibilidade e 4,5:1. Nenhum cinza razoavel apaga o
    branco; o que muda e quanto a BORDA da faixa ainda aparece.

        cor                  branco em cima    borda visivel
        preto (hoje)            21,0 : 1            —
        RGB( 56, 60, 72)        11,0 : 1          4,0 : 1   <- escolhida
        RGB( 49, 53, 66)        12,2 : 1          4,5 : 1
        RGB( 66, 70, 82)         9,4 : 1          3,5 : 1
        RGB( 90, 97,106)         6,3 : 1          2,3 : 1   <- borda SOME

    A borda da faixa e `palette(0x12)` = RGB(156,157,156). Com a faixa
    clara demais ela se dissolve no proprio fundo — por isso o ultimo
    candidato foi descartado.

    A barra de selecao (azul do Marte) tem 5,2:1 com branco. A faixa em
    11:1 fica claramente mais escura e nao compete com ela.

O CONSERTO — 4 bytes, dentro da carcaca

    `CRIA_FAIXA` (0x00D216F0) busca a cor num getter e a entrega ao
    `set_style_bg_color`:

        00D2171A  fff736fe   bl 0xD2138A        <- devolve 0, PRETO
        00D21724             bl set_style_bg_color

    A chamada tem 4 bytes. `MOVW` aceita qualquer imediato de 16 bits e
    tambem ocupa 4 bytes, entao entra no lugar sem mexer em mais nada:

        00D2171A  4ef63910   movw r0, #0xE939

    Como `CRIA_FAIXA` e compartilhada, **as 52 telas mudam juntas**. E
    o que a carcaca existe para fazer.

USO
    python3 tools/patch_faixa_cinza.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_faixa_cinza.py --cor 0xE939 --in ... --out ...
    python3 tools/patch_faixa_cinza.py --autoteste

DEPENDENCIAS
    Python 3. Nada mais.

LIMITACOES
    - muda a faixa de TODAS as 52 telas. Nao ha como deixar uma
      diferente — e proposital;
    - o getter preto 0x00D2138A continua existindo e sendo usado por
      outros pontos (o conteiner, a linha). So a faixa deixa de usa-lo;
    - trocar o tom depois e mudar UM numero: `--cor`.
"""

import argparse, hashlib, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import monta

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000

ALVO     = 0x0012171A                        # o `bl` do getter preto
DE       = bytes.fromhex("fff736fe")         # bl 0xD2138A
COR      = 0xE939                            # RGB(56,60,72) pre-invertido

CONTEXTO = [
    (0x00121716, bytes.fromhex("2bf0a5fc"), "bl set_style_radius, antes"),
    (0x00121724, bytes.fromhex("2bf0b5fc"), "bl set_style_bg_color, depois"),
    (0x00121736, bytes.fromhex("1220"),     "movs r0,#0x12 — a cor da borda"),
    (0x0012174C, bytes.fromhex("2bf0d2fc"), "bl set_style_border_width"),
]


def instrucao(cor):
    b = monta(f".syntax unified\n.thumb\nmovw r0, #0x{cor:04X}\n")
    if len(b) != 4:
        raise RuntimeError(f"movw saiu com {len(b)} bytes, esperava 4")
    return b


def rgb(pre):
    v = ((pre & 0xFF) << 8) | (pre >> 8)          # desfaz a pre-inversao
    return (((v >> 11) & 0x1F) * 255 // 31,
            ((v >> 5) & 0x3F) * 255 // 63,
            (v & 0x1F) * 255 // 31)


def confere_contexto(d):
    for off, esperado, desc in CONTEXTO:
        achado = bytes(d[off:off + len(esperado)])
        if achado != esperado:
            return False, (f"0x{off:06X} ({desc}): achei {achado.hex()}, "
                           f"esperava {esperado.hex()}")
    return True, "ok"


def aplica(d, cor):
    novo = instrucao(cor)
    achado = bytes(d[ALVO:ALVO + 4])
    if achado[:2] == novo[:2] or (achado[0] & 0xF0) == 0xF0 and achado[1] == 0xF6:
        pass
    if achado == novo:
        return False, "patch ja aplicado com esta cor"
    if achado != DE:
        return False, (f"0x{ALVO:06X} tem {achado.hex()}, esperava {DE.hex()} "
                       f"— ou ja foi aplicado com outra cor")
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg
    d[ALVO:ALVO + 4] = novo
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — a faixa vira cinza\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    orig = open(o, "rb").read()
    d = bytearray(orig)
    falhas = []

    ok, msg = aplica(d, COR)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    print(f"    bytes alterados        {len(dif)}  "
          + ("OK" if len(dif) == 4 else "FALHOU"))
    if len(dif) != 4:
        falhas.append(f"alterou {len(dif)} bytes, esperava 4")

    dentro = all(ALVO <= i < ALVO + 4 for i in dif)
    print("    so no lugar do `bl`    " + ("OK" if dentro else "FALHOU"))
    if not dentro:
        falhas.append("escreveu fora dos 4 bytes do `bl`")

    esperado = instrucao(COR)
    certo = bytes(d[ALVO:ALVO + 4]) == esperado
    print(f"    movw r0,#0x{COR:04X}       " + ("OK" if certo else "FALHOU"))
    if not certo:
        falhas.append("a instrucao montada nao bate")

    # o set_bg_color logo depois NAO pode ter sido tocado
    seguinte = bytes(d[0x00121724:0x00121728]) == bytes.fromhex("2bf0b5fc")
    print("    set_bg_color intocado  " + ("OK" if seguinte else "FALHOU"))
    if not seguinte:
        falhas.append("o bl set_style_bg_color foi alterado")

    # a BORDA tem de continuar visivel sobre a cor nova
    def lum(c):
        def f(v):
            v /= 255
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
    def ct(a, b):
        la, lb = lum(a), lum(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
    c = rgb(COR)
    b_branco = ct((255, 255, 255), c)
    b_borda = ct((156, 157, 156), c)
    print(f"    branco em cima         {b_branco:.1f}:1  "
          + ("OK" if b_branco >= 4.5 else "FALHOU"))
    if b_branco < 4.5:
        falhas.append(f"branco sobre a faixa da {b_branco:.1f}:1, minimo 4.5")
    print(f"    borda ainda visivel    {b_borda:.1f}:1  "
          + ("OK" if b_borda >= 3.0 else "FALHOU"))
    if b_borda < 3.0:
        falhas.append(f"a borda da faixa some no fundo ({b_borda:.1f}:1)")

    ok2, _ = aplica(d, COR)
    print("    recusa 2a aplicacao    " + ("OK" if not ok2 else "FALHOU"))
    if ok2:
        falhas.append("aplicar duas vezes NAO foi recusado")

    print()
    if falhas:
        for f in falhas:
            print(f"  FALHA: {f}")
        print("\n  AUTOTESTE FALHOU")
        return 1
    print("  AUTOTESTE OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description="a faixa superior vira cinza")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--cor", type=lambda s: int(s, 0), default=COR,
                    help="cor RGB565 PRE-INVERTIDA (padrao 0xE939)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    a = ap.parse_args()

    if a.autoteste:
        return autoteste()
    if not a.src:
        ap.error("--in e obrigatorio (ou use --autoteste)")
    if not a.dst and not a.dry_run:
        ap.error("--out e obrigatorio, ou use --dry-run")

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAMANHO:
        print(f"ERRO: {a.src} tem {len(d)} B, esperado {TAMANHO}",
              file=sys.stderr)
        return 1
    orig = bytes(d)

    print("\n  A FAIXA SUPERIOR VIRA CINZA\n")
    ok, msg = aplica(d, a.cor)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    print("  ALTERACAO")
    print(f"    0x{ALVO:06X}   4 B  {DE.hex()} -> {bytes(d[ALVO:ALVO+4]).hex()}")
    print(f"      bl getter PRETO  ->  movw r0, #0x{a.cor:04X}")
    print(f"      = RGB{rgb(a.cor)}, derivado do Marte")
    print()
    print("  ALCANCE   CRIA_FAIXA e compartilhada: 52 telas mudam juntas")
    print()
    print("  NAO TOCADO")
    print("    o getter preto 0x00D2138A — o conteiner e a linha seguem usando")
    print("    a borda da faixa, palette(0x12)")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido (R1).", file=sys.stderr)
        return 1
    print("  nada abaixo de 0x00D000   OK")
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}\n")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
