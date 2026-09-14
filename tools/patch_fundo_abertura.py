#!/usr/bin/env python3
"""
patch_fundo_abertura.py — o fundo da tela de abertura fica PRETO.

O DEFEITO

    A logo do OpenPod tem fundo preto; a tela de abertura tem fundo
    claro. O resultado e um retangulo escuro de 128x35 no meio de uma
    tela branca — exatamente o que o mantenedor relatou ao gravar a
    Core 1.0 em 2026-09-14.

    Com o logotipo GENAI de fabrica o problema nao aparecia: ele tem
    fundo claro, igual ao da tela.

A CAUSA

    As duas funcoes que desenham a logo, `0x00D22794` e `0x00D228A0`,
    consultam um getter de cor CLARA (`0x00D21384`). Existe ao lado um
    getter de PRETO (`0x00D2138A`).

O CONSERTO — 2 bytes

    0x0012285C   93 -> 96    redireciona o BL da 1a funcao
    0x001228E6   4E -> 51    redireciona o BL da 2a funcao

    Muda para ONDE a chamada aponta, nao o valor que ela devolve.

POR QUE NAO MEXER NO GETTER

    Ele e SOBRECARREGADO: devolve uma "cor clara" que umas telas usam
    como TEXTO e outras como FUNDO. Escurece-lo deixaria o texto de
    Configurar invisivel. Redirecionar as duas chamadas especificas
    resolve a abertura sem efeito colateral em nenhuma outra tela.

PROCEDENCIA

    E o patch da V008, de 12/09/2026, **confirmado na tela** naquela
    epoca: "logo do OpenPod sobre preto, sem faixa e sem moldura clara".
    A ferramenta se perdeu quando a construcao virou receita declarada —
    mesma historia do `patch_logo.py`. Aqui ela volta, com verificacao.

USO
    python3 tools/patch_fundo_abertura.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_fundo_abertura.py --autoteste

DEPENDENCIAS
    Python 3

LIMITACOES
    - so a tela de abertura. Nenhuma outra tela muda de cor;
    - recusa se os bytes de origem nao forem os esperados: e sinal de
      que ja foi aplicado, ou de que a imagem nao e deste firmware.
"""

import argparse, hashlib, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL   = "firmware/ORIGINAL/GN438_original.bin"
REFERENCIA = "firmware/WORKING/GN438_openpod_v008.bin"   # a que rodou
PROIBIDO   = 0x0000D000

# (offset, byte esperado, byte novo)
PONTOS = [
    (0x0012285C, 0x93, 0x96),   # bl da 1a funcao do logo (0x00D22794)
    (0x001228E6, 0x4E, 0x51),   # bl da 2a funcao do logo (0x00D228A0)
]


def aplica(d):
    """devolve (ok, mensagem). Altera d no lugar."""
    for off, velho, novo in PONTOS:
        if d[off] == novo:
            return False, f"0x{off:06X} ja esta {novo:02X}: patch ja aplicado"
        if d[off] != velho:
            return False, (f"0x{off:06X} tem {d[off]:02X}, esperado "
                           f"{velho:02X} — esta imagem nao e a esperada")
    for off, velho, novo in PONTOS:
        d[off] = novo
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — reproduzir os 2 bytes da V008, que rodou na tela\n")
    o = os.path.join(RAIZ, ORIGINAL)
    r = os.path.join(RAIZ, REFERENCIA)
    for p in (o, r):
        if not os.path.exists(p):
            print(f"  FALTA: {p}")
            return 1
    d = bytearray(open(o, "rb").read())
    ref = open(r, "rb").read()
    ok, msg = aplica(d)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1
    iguais = all(d[off] == ref[off] for off, _, _ in PONTOS)
    for off, velho, novo in PONTOS:
        print(f"    0x{off:06X}  {velho:02X} -> {d[off]:02X}   "
              f"V008 tem {ref[off]:02X}  {'OK' if d[off]==ref[off] else 'DIVERGE'}")
    print()
    print("  AUTOTESTE OK" if iguais else "  AUTOTESTE FALHOU")
    return 0 if iguais else 1


def main():
    ap = argparse.ArgumentParser(description="fundo da abertura em preto")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    a = ap.parse_args()

    if a.autoteste:
        return autoteste()
    if not a.src or not a.dst:
        ap.error("--in e --out sao obrigatorios (ou use --autoteste)")

    d = bytearray(open(a.src, "rb").read())
    if len(d) != 0x200000:
        print(f"ERRO: {a.src} tem {len(d)} B, esperado 2097152", file=sys.stderr)
        return 1
    orig = bytes(d)

    print("\n  FUNDO DA ABERTURA EM PRETO\n")
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    print("  ALTERACOES")
    for off, velho, novo in PONTOS:
        print(f"    0x{off:06X}   1 B  {velho:02X} -> {novo:02X}  "
              f"bl para o getter PRETO (0x00D2138A)")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido (R1).", file=sys.stderr)
        return 1
    print("  tabela de particoes NAO tocada   OK")
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}\n")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
