#!/usr/bin/env python3
"""
patch_selecao_marte.py — a barra de selecao ganha o AZUL DO MARTE.

O ALVO

    Item M-f de `docs/MARTE_ALVO.md` §2. O mockup
    `marte/mockups/marte_completo.png` tem a barra de selecao em AZUL;
    o firmware de fabrica usa o azul do Material Design da LVGL, que e
    mais claro e puxa para o ciano.

        de fabrica   RGB( 32,149,246)   paleta[5] da LVGL
        Marte        RGB( 41,101,222)   nanoclone.json, campo selecao_base

O CAMINHO — medido em 2026-09-14, e nao foi o obvio

    A selecao NAO e pintada pela `CRIA_LINHA`, nem pelo Configurar. Foi
    preciso eliminar varios candidatos ate achar:

        tabela de paletas  0x00CDF078   unico leitor: palette_main
        palette_main(7) CYAN            1 chamada, e e a pagina 0x18
        CRIA_LINHA  0x00D21764          nao seta cor de estado nenhum
        0xD51704 / 0xD516B4             geometria, nao cor
        page_set_menu                   1 unica chamada de cor propria

    Quem pinta e um HELPER COMPARTILHADO:

        0x00D219D4   10 chamadores, um deles (0x00D3AA94) dentro do
                     Configurar. Pinta bg_color no estado FOCUS_KEY com
                     palette_main(5) em 0x00D21B08 e 0x00D21B92.

O CONSERTO — 2 bytes, na TABELA

    Trocar as instrucoes exigiria espaco para carregar uma cor literal.
    Mas `palette_main` le uma TABELA, e a entrada 5 e um halfword:

        0x000DF082   24 BE  ->  2B 3B

        0xBE24 invertido = 0x24BE = RGB( 32,149,246)   de fabrica
        0x3B2B invertido = 0x2B3B = RGB( 41,101,222)   Marte

    Cores neste binario sao RGB565 **pre-invertidas** — ver
    `docs/COLOR_SOURCE.md` §9. Por isso os bytes gravados sao `2B 3B`.

ALCANCE — medido, nao suposto

    Os 12 pontos que usam paleta[5], e o que cada um pinta:

        9x  bg_color estado FOCUS_KEY   <- as barras de selecao
        1x  bg_color estado CHECKED
        1x  bg_color estado normal
        1x  consumidor nao identificado

    Ou seja: **as nove barras de selecao ganham o azul do Marte**, e tres
    outros elementos azuis passam a usar o MESMO azul. Isso e
    consistencia, nao regressao — nenhum deles fica de cor errada, todos
    ficam da cor certa.

    Nenhum outro indice da paleta e tocado.

USO
    python3 tools/patch_selecao_marte.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_selecao_marte.py --in <entrada.bin> --dry-run
    python3 tools/patch_selecao_marte.py --autoteste

DEPENDENCIAS
    Python 3. Nada mais.

LIMITACOES
    - a HOME nao usa o helper 0x00D219D4, entao a selecao dela NAO muda
      com este patch. Ver `docs/CARCACA_PADRAO.md` §2;
    - o alvo do Marte pede DEGRADE (selecao_topo -> selecao_base). Isto
      entrega a cor CHAPADA do `selecao_base`. O degrade e o item M-h,
      e e rotina nova;
    - nao aloca, nao usa a area livre, nao tem `--em`.
"""

import argparse, hashlib, os, sys

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000

PALETA   = 0x000DF078          # tabela de paletas da LVGL
INDICE   = 5                   # LV_PALETTE_BLUE
OFF      = PALETA + INDICE * 2 # 0x000DF082

DE   = bytes([0x24, 0xBE])     # 0xBE24 -> RGB(32,149,246)
PARA = bytes([0x2B, 0x3B])     # 0x3B2B -> RGB(41,101,222)  Marte

# guarda-corpo: a tabela inteira tem de ser a Material padrao da LVGL.
# Confere as entradas VIZINHAS, que este patch nao toca.
#
# Os valores sao halfwords little-endian: o bruto 0x963A grava-se `3A 96`.
VIZINHOS = [
    (4, bytes([0x3A, 0x96])),   # INDIGO      bruto 0x963A
    (6, bytes([0x05, 0x5E])),   # LIGHT_BLUE  bruto 0x5E05
    (7, bytes([0x05, 0xFA])),   # CYAN        bruto 0xFA05
]


def rgb(v):
    return (((v >> 11) & 0x1F) * 255 // 31,
            ((v >> 5) & 0x3F) * 255 // 63,
            (v & 0x1F) * 255 // 31)


def confere_contexto(d):
    for i, esperado in VIZINHOS:
        o = PALETA + i * 2
        achado = bytes(d[o:o + 2])
        if achado != esperado:
            return False, (f"paleta[{i}] em 0x{o:06X}: achei {achado.hex()}, "
                           f"esperava {esperado.hex()} — a tabela nao e a "
                           f"Material padrao da LVGL")
    return True, "ok"


def aplica(d):
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg
    achado = bytes(d[OFF:OFF + 2])
    if achado == PARA:
        return False, f"0x{OFF:06X} ja esta {PARA.hex()}: patch ja aplicado"
    if achado != DE:
        return False, (f"0x{OFF:06X} tem {achado.hex()}, esperado {DE.hex()}")
    d[OFF:OFF + 2] = PARA
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — 2 bytes na tabela de paletas\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    orig = open(o, "rb").read()
    d = bytearray(orig)

    ok, msg = aplica(d)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1

    falhas = []
    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    print(f"    bytes alterados        {len(dif)}  "
          + ("OK" if len(dif) == 2 else "FALHOU"))
    if len(dif) != 2:
        falhas.append(f"esperava 2 bytes, foram {len(dif)}")
    if dif and (dif[0] != OFF or dif[-1] != OFF + 1):
        falhas.append("os bytes alterados nao sao a entrada 5")
    print(f"    offset                 0x{dif[0]:06X}  "
          + ("OK" if dif and dif[0] == OFF else "FALHOU"))

    v = d[OFF] | (d[OFF + 1] << 8)
    inv = ((v & 0xFF) << 8) | (v >> 8)
    cor = rgb(inv)
    print(f"    cor resultante         RGB{cor}  "
          + ("OK" if cor == (41, 101, 222) else "FALHOU"))
    if cor != (41, 101, 222):
        falhas.append(f"cor {cor}, esperava (41, 101, 222)")

    for i, esperado in VIZINHOS:
        oo = PALETA + i * 2
        igual = bytes(d[oo:oo + 2]) == esperado
        print(f"    paleta[{i}] intocada     "
              + ("OK" if igual else "FALHOU"))
        if not igual:
            falhas.append(f"paleta[{i}] foi alterada")

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
        description="a barra de selecao ganha o azul do Marte (M-f)")
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

    print("\n  SELECAO NO AZUL DO MARTE  (M-f)\n")
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    vd = int.from_bytes(DE, "little"); vp = int.from_bytes(PARA, "little")
    print("  ALTERACAO")
    print(f"    0x{OFF:06X}   2 B  {DE.hex()} -> {PARA.hex()}   paleta[5] BLUE")
    print(f"      de   RGB{rgb(((vd & 0xFF) << 8) | (vd >> 8))}  (Material da LVGL)")
    print(f"      para RGB{rgb(((vp & 0xFF) << 8) | (vp >> 8))}  (Marte, selecao_base)")
    print()
    print("  ALCANCE  — os 12 pontos que usam paleta[5]")
    print("    9x  bg_color estado FOCUS_KEY   <- as barras de selecao")
    print("    3x  outros elementos azuis, que passam a usar o MESMO azul")
    print()
    print("  NAO MUDA")
    print("    a HOME — ela nao usa o helper 0x00D219D4")
    print("    nenhum outro indice da paleta")
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
