#!/usr/bin/env python3
"""
patch_sem_separador.py — tira o traco entre os itens das listas.

O ALVO

    `marte/mockups/marte_completo.png`, item M-a da tabela de
    `docs/MARTE_ALVO.md` §2. A lista do iPod nano e LIMPA: nao ha traco
    separando um item do outro. O firmware de fabrica desenha um, de
    1 px, em todas as telas de lista.

A CAUSA — medida, nao suposta

    Esta DENTRO de `CRIA_LINHA` (0x00D21764), a rotina compartilhada que
    39 telas usam para montar cada item. Desmontado do ORIGINAL:

        00D2179E  0121      movs  r1, #1     <- a LARGURA da borda
        00D217A0  2bf0a8fc  bl    0xD4D0F4      set_style_border_width (50)
        00D217A4  2046      mov   r0, r4
        00D217A6  0022      movs  r2, #0
        00D217A8  0121      movs  r1, #1
        00D217AA  2bf0a9fc  bl    0xD4D100      set_style_border_side  (51)

    A cor dessa borda vem de `palette_main(0x12)`, nao de tabela nenhuma.
    Por isso o caminho barato e zerar a LARGURA, nao caçar a cor.

O CONSERTO — 1 byte

    0x0012179E   01 -> 00    movs r1, #1  ->  movs r1, #0

    Zera a largura da borda da LINHA. O `border_side` em 0x001217A8 fica
    intocado: sem largura ele nao desenha nada, e mexer nos dois seria
    mudanca sem efeito adicional.

POR QUE ISTO E BARATO E VALE MUITO

    Um byte dentro de uma rotina compartilhada muda **39 telas ao mesmo
    tempo**. Contagem feita por padrao de bits dos `BL` (regra §3 do
    projeto), nao por disassembly linear:

        CRIA_LINHA  0x00D21764   39 chamadas

    E tambem a validacao pratica da tese da carcaca
    (`docs/CARCACA_PADRAO.md`): se um byte mudar as 39 telas de uma vez,
    a carcaca esta provada na tela, e nao so no papel.

⚠️ NAO CONFUNDIR COM O TRACO DA FAIXA

    O `faixa_separador` do `marte/paleta/nanoclone.json` (y=17) e a borda
    da FAIXA superior — e ela FICA, porque o alvo tem. Sao objetos
    diferentes: a borda da FAIXA e a borda da LINHA. Esta ferramenta so
    toca na segunda.

USO
    python3 tools/patch_sem_separador.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_sem_separador.py --in <entrada.bin> --dry-run
    python3 tools/patch_sem_separador.py --autoteste

DEPENDENCIAS
    Python 3. Nada mais.

LIMITACOES
    - so as telas que usam `CRIA_LINHA`. A HOME **nao** usa, entao ela
      nao muda com este patch — ver `docs/CARCACA_PADRAO.md` §2;
    - nao aloca nada, nao usa a area livre, nao tem parametro `--em`;
    - recusa se o byte de origem nao for o esperado: e sinal de que ja
      foi aplicado, ou de que a imagem nao e deste firmware.
"""

import argparse, hashlib, os, sys

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000

# (offset, byte esperado, byte novo, descricao)
PONTOS = [
    (0x0012179E, 0x01, 0x00,
     "largura da borda da LINHA -> 0  (CRIA_LINHA, 0x00D21764)"),
]

# guarda-corpo: o contexto que PRECISA estar intacto em volta do ponto.
# Se o firmware nao for este, isto nao bate e a ferramenta recusa antes
# de escrever qualquer coisa.
CONTEXTO = [
    (0x0012179A, bytes.fromhex("2046")),          # mov  r0, r4
    (0x0012179C, bytes.fromhex("0022")),          # movs r2, #0
    (0x001217A0, bytes.fromhex("2bf0a8fc")),      # bl   0xD4D0F4 border_width
    (0x001217A8, bytes.fromhex("0121")),          # movs r1, #1   (border_side)
    (0x001217AA, bytes.fromhex("2bf0a9fc")),      # bl   0xD4D100 border_side
]


def confere_contexto(d):
    for off, esperado in CONTEXTO:
        achado = bytes(d[off:off + len(esperado)])
        if achado != esperado:
            return False, (f"contexto em 0x{off:06X}: achei "
                           f"{achado.hex()}, esperava {esperado.hex()} — "
                           f"esta imagem nao e o firmware esperado")
    return True, "ok"


def aplica(d):
    """devolve (ok, mensagem). Altera d no lugar."""
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg
    for off, velho, novo, _ in PONTOS:
        if d[off] == novo:
            return False, f"0x{off:06X} ja esta {novo:02X}: patch ja aplicado"
        if d[off] != velho:
            return False, (f"0x{off:06X} tem {d[off]:02X}, esperado "
                           f"{velho:02X}")
    for off, velho, novo, _ in PONTOS:
        d[off] = novo
    return True, "ok"


def autoteste():
    """Aplica sobre o ORIGINAL e confere: 1 byte, no lugar certo, e o
    border_side preservado."""
    print("\n  AUTOTESTE — 1 byte sobre o ORIGINAL\n")
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

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    falhas = []

    if len(dif) != 1:
        falhas.append(f"esperava 1 byte alterado, foram {len(dif)}")
    elif dif[0] != 0x0012179E:
        falhas.append(f"byte alterado em 0x{dif[0]:06X}, esperava 0x0012179E")
    print(f"    bytes alterados        {len(dif)}  "
          + ("OK" if len(dif) == 1 else "FALHOU"))
    print(f"    offset                 0x{dif[0]:06X}  "
          + ("OK" if dif and dif[0] == 0x0012179E else "FALHOU"))

    if d[0x001217A8] != 0x01:
        falhas.append("o border_side em 0x001217A8 foi alterado — nao devia")
    print(f"    border_side intocado   0x{d[0x001217A8]:02X}  "
          + ("OK" if d[0x001217A8] == 0x01 else "FALHOU"))

    # teste negativo: aplicar de novo tem de RECUSAR
    ok2, msg2 = aplica(d)
    if ok2:
        falhas.append("aplicar duas vezes NAO foi recusado")
    print(f"    recusa 2a aplicacao    "
          + ("OK" if not ok2 else "FALHOU"))

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
        description="tira o traco entre os itens das listas (M-a)")
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

    print("\n  SEM SEPARADOR ENTRE OS ITENS  (Marte M-a)\n")
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    print("  ALTERACOES")
    for off, velho, novo, desc in PONTOS:
        print(f"    0x{off:06X}   1 B  {velho:02X} -> {novo:02X}  {desc}")
    print()
    print("  NAO TOCADO")
    print("    0x001217A8   border_side da LINHA  (sem largura, nao desenha)")
    print("    a borda da FAIXA superior — e outro objeto, e o alvo a tem")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido (R1).", file=sys.stderr)
        return 1
    print("  nada abaixo de 0x00D000   OK")
    print("  tabela de particoes NAO tocada   OK")
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}\n")
    print("  alcance: 39 telas de lista (CRIA_LINHA, 0x00D21764)")
    print("  a HOME nao usa CRIA_LINHA e NAO muda com este patch\n")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
