#!/usr/bin/env python3
"""
patch_altura_linha.py — TODAS as telas de lista passam a ter a mesma
                        altura de linha: 16 px.

O PEDIDO

    Do mantenedor, 2026-09-14, depois da Core 2.1.1:

        "Menu Principal ta diferente em tamanho dos outros menus, da para
         ficar todos do tamanho do principal?"

    Ele esta certo, e a medida esta do lado dele:

        home           (160 - 19) / 9  =  15 px
        outras telas    160 / 7        =  22 px

O QUE ESTA FERRAMENTA FAZ

    Troca o DIVISOR de 7 para 10 nos 62 pontos que calculam altura de
    linha. `160 / 10 = 16 px`.

    **16 px nao e numero inventado**: e o `altura_linha` do
    `marte/paleta/nanoclone.json` — a medida da linha do iPod nano. A
    fonte de 18 px tem 16 px de tinta real.

    O `patch_home_lista.py` acompanha, com `TOPO = 16`:
    `(160 - 16) / 9 = 16`. As nove linhas ocupam y=16..160, exatamente.

    Resultado: home e as outras telas com a MESMA altura, e a do nano.

COMO OS 62 FORAM ACHADOS — e por que sao 62, nao "varios"

    Nao por leitura: por varredura.

      1. todos os chamadores de `set_height` (0x00D4A1EA): 108;
      2. destes, os que tem um `sdiv` nos 24 bytes anteriores;
      3. destes, os que tem um imediato 7 alimentando o divisor.

        62 pontos     54 com `movs rX,#7`      (16 bits)
                       8 com `mov.w rX,#7`     (32 bits)

    Nos 62 o imediato 7 e UM BYTE. Medido, nao suposto.

    Os outros 46 chamadores de `set_height` NAO usam divisao — sao
    alturas fixas, de telas que nao sao lista. Nao sao tocados.

POR QUE ISTO E A CARCACA FUNCIONANDO

    O mantenedor vem pedindo isto desde o inicio: "uma carcaca de design
    padrao que todos se baseiem nela". O firmware nao tem uma constante
    unica de altura — tem a MESMA CONTA repetida em 62 lugares. Trocar o
    divisor nos 62 e o mais proximo disso que o firmware de fabrica
    permite sem criar tabela nova.

USO
    python3 tools/patch_altura_linha.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_altura_linha.py --in <entrada.bin> --dry-run
    python3 tools/patch_altura_linha.py --autoteste

DEPENDENCIAS
    Python 3. Nada mais.

LIMITACOES
    - telas com MUITOS itens passam a mostrar mais linhas por tela. O
      Configurar, por exemplo, sai de ~6 visiveis para ~8. Isso e o
      efeito desejado, mas e mudanca de comportamento e esta declarada;
    - a altura do CONTEINER nao e tocada — so a da linha. Onde o
      conteiner era calculado com outro divisor, ele fica como estava;
    - nao aloca, nao usa a area livre.
"""

import argparse, hashlib, os, sys

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000
BIAS     = 0x00C00000

SET_HEIGHT = 0x00D4A1EA
DE, PARA   = 7, 10          # 160/7 = 22 px  ->  160/10 = 16 px
ESPERADOS  = 62             # medido no ORIGINAL


def _bl_alvos(d):
    out = {}
    for o in range(0, len(d) - 3, 2):
        w1 = d[o] | (d[o + 1] << 8)
        if (w1 & 0xF800) != 0xF000:
            continue
        w2 = d[o + 2] | (d[o + 3] << 8)
        if (w2 & 0xD000) != 0xD000:
            continue
        S = (w1 >> 10) & 1
        j1 = (w2 >> 13) & 1
        j2 = (w2 >> 11) & 1
        i1 = (~(j1 ^ S)) & 1
        i2 = (~(j2 ^ S)) & 1
        v = ((S << 24) | (i1 << 23) | (i2 << 22)
             | ((w1 & 0x3FF) << 12) | ((w2 & 0x7FF) << 1))
        if S:
            v -= (1 << 25)
        out.setdefault(BIAS + o + 4 + v, []).append(o)
    return out


def localiza(d, valor):
    """Devolve os offsets do BYTE do divisor, para cada set_height que
    calcula altura = tela / <valor>."""
    t = _bl_alvos(d)
    achados = []
    for o in sorted(t.get(SET_HEIGHT, [])):
        sd = None
        for back in range(2, 26, 2):
            i = o - back
            if i < 2:
                break
            if (d[i + 1] == 0xFB and (d[i] & 0xF0) == 0x90
                    and (d[i + 2] & 0xF0) == 0xF0 and (d[i + 3] & 0xF0) == 0xF0):
                sd, Rm = i, d[i + 2] & 0xF
                break
        if sd is None:
            continue
        for b2 in range(2, 20, 2):
            k = sd - b2
            if k < 0:
                break
            hw = d[k] | (d[k + 1] << 8)
            # movs rX,#imm8  (16 bits)
            if (hw & 0xF800) == 0x2000 and ((hw >> 8) & 7) == Rm \
                    and (hw & 0xFF) == valor:
                achados.append((k, "movs", BIAS + o))
                break
            # mov.w rX,#imm   (32 bits)
            if d[k] == 0x4F and d[k + 1] == 0xF0 and (d[k + 3] & 0xF) == Rm \
                    and d[k + 2] == valor:
                achados.append((k + 2, "mov.w", BIAS + o))
                break
    return achados


def aplica(d):
    ja = localiza(d, PARA)
    if len(ja) >= ESPERADOS:
        return False, f"patch ja aplicado ({len(ja)} pontos com divisor {PARA})"
    pontos = localiza(d, DE)
    if len(pontos) != ESPERADOS:
        return False, (f"achei {len(pontos)} pontos com divisor {DE}, "
                       f"esperava {ESPERADOS} — esta imagem nao e a esperada, "
                       f"ou ha um caminho novo que esta ferramenta nao conhece")
    for k, _, _ in pontos:
        if d[k] != DE:
            return False, f"0x{k:06X} tem {d[k]}, esperava {DE}"
    for k, _, _ in pontos:
        d[k] = PARA
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — altura de linha igual em todas as telas\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    orig = open(o, "rb").read()
    d = bytearray(orig)
    falhas = []

    antes = localiza(d, DE)
    print(f"    pontos com divisor {DE}     {len(antes)}  "
          + ("OK" if len(antes) == ESPERADOS else "FALHOU"))
    if len(antes) != ESPERADOS:
        falhas.append(f"esperava {ESPERADOS} pontos, achei {len(antes)}")

    ok, msg = aplica(d)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    print(f"    bytes alterados        {len(dif)}  "
          + ("OK" if len(dif) == ESPERADOS else "FALHOU"))
    if len(dif) != ESPERADOS:
        falhas.append(f"alterou {len(dif)} bytes, esperava {ESPERADOS}")

    depois = localiza(d, PARA)
    print(f"    pontos com divisor {PARA}    {len(depois)}  "
          + ("OK" if len(depois) == ESPERADOS else "FALHOU"))
    if len(depois) != ESPERADOS:
        falhas.append("nem todos os pontos ficaram com o divisor novo")

    sobrou = localiza(d, DE)
    print(f"    nenhum ponto com {DE}      {len(sobrou)}  "
          + ("OK" if not sobrou else "FALHOU"))
    if sobrou:
        falhas.append(f"sobraram {len(sobrou)} pontos com divisor {DE}")

    # cada byte alterado tem de ser exatamente um imediato de divisor
    fora = [i for i in dif if i not in {k for k, _, _ in antes}]
    print("    so os imediatos          " + ("OK" if not fora else "FALHOU"))
    if fora:
        falhas.append(f"mexeu em bytes que nao sao divisor: {fora[:5]}")

    ok2, _ = aplica(d)
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
    ap = argparse.ArgumentParser(
        description="altura de linha igual em todas as telas: 16 px")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
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

    print("\n  ALTURA DE LINHA IGUAL EM TODAS AS TELAS\n")
    pontos = localiza(d, DE)
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    from collections import Counter
    c = Counter(t for _, t, _ in pontos)
    print(f"  {len(pontos)} PONTOS, divisor {DE} -> {PARA}")
    for k, v in c.items():
        print(f"    {v:3d} com {k}")
    print()
    print(f"    altura da linha:  160/{DE} = {160//DE} px  ->  "
          f"160/{PARA} = {160//PARA} px")
    print("    16 px e o `altura_linha` do marte/paleta/nanoclone.json")
    print()
    print("  NAO TOCADO")
    print("    os 46 set_height SEM divisao — alturas fixas, nao sao lista")
    print("    a altura do CONTEINER de cada tela")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}")
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
