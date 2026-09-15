#!/usr/bin/env python3
"""
patch_nome_faixa.py — o nome "OpenPod" no lugar do icone de cartao SD.

O PEDIDO

    Do mantenedor, 2026-09-14, com a foto do iPod nano 2G ao lado:

        "no lugar do chip sd coloca o nome OpenPod"

    O nano mostra "iPod" na faixa superior. Aqui fica "OpenPod".

A ROTINA — pequena, dedicada, e com dois chamadores

    `0x00D226AC` cria UM rotulo e so serve para isso:

        00D226B2  bl   CRIA_ROTULO
        00D226BA  mvn  r2, #0x1d          x = -30
        00D226B6  movs r3, #2             y = 2
        00D226C0  bl   set_pos(align=3)
        00D226C6  ldr  r1, =0x00819D00    <- a FONTE do icone
        00D226CA  bl   set_style_text_font
        00D226CE  bl   getter CLARO       branco
        00D226D8  bl   set_style_text_color
        00D226DE  ldr  r1, =0x00C5D614    <- o glifo U+F0C7, o disquete
        00D226E0  bl   set_text

    Chamadores: 0x00D23898 e 0x00D23E9C. **As duas telas que a usam
    passam a mostrar "OpenPod".**

O CONSERTO — duas partes

    1. TIRAR A FONTE DE ICONE.
       `0x00D226C4..0x00D226CD` (10 bytes) viram NOP. Sem `set_font`, o
       rotulo usa a fonte de TEXTO padrao — a mesma dos itens da lista.
       Com a fonte de icone, "OpenPod" sairia como glifos sem sentido.

    2. TROCAR O TEXTO.
       O ponteiro no pool literal, em `0x001226F4`, deixa de apontar para
       o glifo e passa a apontar para a string nova, escrita na area
       livre.

⚠️ O QUE SE PERDE — e isto e decisao do mantenedor, nao minha

    O disquete provavelmente indica **cartao SD presente**. Trocando-o
    por um texto fixo, esse sinal some: nao havera mais indicacao visual
    de que o cartao esta ou nao inserido.

    Nao consegui confirmar se a rotina e chamada condicionalmente (o
    cartao presente) ou sempre. Se for condicional, "OpenPod" tambem
    aparecera so com cartao — o que seria pior que o icone.

    **Isto precisa ser olhado na tela, com e sem cartao.** Esta no
    LEIA-ME do kit.

USO
    python3 tools/patch_nome_faixa.py --in <entrada.bin> --out <saida.bin> --em 0x1A3040
    python3 tools/patch_nome_faixa.py --autoteste

DEPENDENCIAS
    Python 3. Nada mais.

LIMITACOES
    - o rotulo esta em x=-30, alinhado a direita. "OpenPod" tem ~45 px
      na fonte padrao; o relogio termina perto de x=40. Deve caber entre
      os dois, mas e a TELA que responde;
    - a faixa tem 16 px de altura e a fonte padrao tem 18 px de caixa
      (16 de tinta). Pode encostar em cima ou embaixo;
    - nao aloca fora do lote declarado em `--em`.
"""

import argparse, hashlib, os, sys

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000
BIAS     = 0x00C00000

NOME     = b"OpenPod\x00"
POOL     = 0x001226F4          # o ponteiro do texto, no pool literal
GLIFO    = 0x00C5D614          # U+F0C7, o disquete
FONTE_I  = 0x001226C4          # inicio do trecho que seta a fonte de icone
FONTE_N  = 10                  # 10 bytes -> 5 NOP
NOP      = b"\x00\xbf"

CONTEXTO = [
    (0x001226C4, bytes.fromhex("0022"),     "movs r2,#0 — inicio do set_font"),
    (0x001226C6, bytes.fromhex("0a49"),     "ldr r1,=0x00819D00 — a fonte de icone"),
    (0x001226CA, bytes.fromhex("2af030fd"), "bl set_style_text_font"),
    (0x001226DE, bytes.fromhex("0549"),     "ldr r1,[pc,#0x14] — o texto"),
    (0x001226E0, bytes.fromhex("3cf058fb"), "bl set_text"),
]


def confere_contexto(d):
    for off, esperado, desc in CONTEXTO:
        achado = bytes(d[off:off + len(esperado)])
        if achado != esperado:
            return False, (f"0x{off:06X} ({desc}): achei {achado.hex()}, "
                           f"esperava {esperado.hex()}")
    return True, "ok"


def _aplica(d, em):
    if bytes(d[FONTE_I:FONTE_I + FONTE_N]) == NOP * (FONTE_N // 2):
        return False, "patch ja aplicado"
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg
    atual = int.from_bytes(d[POOL:POOL + 4], "little")
    if atual != GLIFO:
        return False, (f"o pool em 0x{POOL:06X} aponta para 0x{atual:08X}, "
                       f"esperava 0x{GLIFO:08X}")
    livre = d[em:em + len(NOME)]
    if any(b != 0xFF for b in livre):
        return False, (f"a area livre em 0x{em:06X} nao esta virgem: "
                       f"{bytes(livre).hex()}")
    d[em:em + len(NOME)] = NOME
    d[FONTE_I:FONTE_I + FONTE_N] = NOP * (FONTE_N // 2)
    d[POOL:POOL + 4] = (BIAS + em).to_bytes(4, "little")
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — 'OpenPod' no lugar do icone de SD\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    orig = open(o, "rb").read()
    d = bytearray(orig)
    em = 0x001A3040
    falhas = []

    ja = bytes(d[FONTE_I:FONTE_I + FONTE_N]) == NOP * (FONTE_N // 2)
    print(f"    imagem virgem          " + ("OK" if not ja else "FALHOU"))

    ok, msg = _aplica(d, em)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1

    texto = bytes(d[em:em + len(NOME)])
    print(f"    string escrita         {texto!r}  "
          + ("OK" if texto == NOME else "FALHOU"))
    if texto != NOME:
        falhas.append("a string nao foi escrita")

    novo = int.from_bytes(d[POOL:POOL + 4], "little")
    certo = novo == BIAS + em
    print(f"    ponteiro -> 0x{novo:08X}  " + ("OK" if certo else "FALHOU"))
    if not certo:
        falhas.append("o ponteiro do texto nao aponta para a string nova")

    sem_fonte = bytes(d[FONTE_I:FONTE_I + FONTE_N]) == NOP * (FONTE_N // 2)
    print("    set_font removido      " + ("OK" if sem_fonte else "FALHOU"))
    if not sem_fonte:
        falhas.append("o set_style_text_font nao virou NOP")

    intacto = bytes(d[0x001226E0:0x001226E4]) == bytes.fromhex("3cf058fb")
    print("    set_text intocado      " + ("OK" if intacto else "FALHOU"))
    if not intacto:
        falhas.append("o bl set_text foi alterado — nao devia")

    ok2, _ = _aplica(d, em)
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
        description="'OpenPod' no lugar do icone de cartao SD")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--em", type=lambda s: int(s, 0), default=0x001A3040,
                    help="endereco da string na area livre")
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

    print("\n  'OpenPod' NA FAIXA, no lugar do icone de SD\n")
    ok, msg = _aplica(d, a.em)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    print("  ALTERACOES")
    print(f"    0x{a.em:06X}   {len(NOME)} B  a string {NOME!r}")
    print(f"    0x{FONTE_I:06X}  {FONTE_N} B  o set_style_text_font vira NOP")
    print(f"               (sem ele o rotulo usa a fonte de TEXTO padrao)")
    print(f"    0x{POOL:06X}   4 B  o ponteiro do texto -> 0x{BIAS+a.em:08X}")
    print()
    print("  ALCANCE   a rotina 0x00D226AC tem 2 chamadores:")
    print("            0x00D23898 e 0x00D23E9C")
    print()
    print("  ⚠️  O disquete provavelmente indicava CARTAO SD PRESENTE.")
    print("      Esse sinal some. Olhar na tela COM e SEM cartao.")
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
