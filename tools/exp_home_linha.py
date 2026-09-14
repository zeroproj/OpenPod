#!/usr/bin/env python3
"""
exp_home_linha.py — EXPERIMENTO: a home passa a usar CRIA_LINHA.

NAO E UMA VERSAO. E a primeira tentativa de levar a home para o caminho
padrao, e ela pode simplesmente nao desenhar.

O QUE A HOME FAZ HOJE (docs/CONVERTER_HOME.md §2.1)

    Por item, duas coisas IRMAS, filhas do conteiner, posicionadas por
    coordenada absoluta:

        sb = lv_img_create(r7)        o quadro do icone (hoje vazio)
        r6 = lv_label_create(r7)      o rotulo

    Nao existe objeto de LINHA. E por isso que `cor_tela` nao alcanca a
    home, que a selecao precisa pintar o fundo do proprio rotulo, e que o
    espacamento vem de tabela de coordenadas.

O QUE ESTE EXPERIMENTO FAZ — tres edicoes, 10 bytes

    0x0012ECF0   bl lv_img_create   ->  bl CRIA_LINHA      4 B
    0x0012ED24   mov r0, r7         ->  mov r0, sb         2 B
    0x0012ED7E   bl posiciona       ->  nop ; nop          4 B

    A linha nasce pelo helper compartilhado — com fundo de `cor_tela`,
    altura de `altura_linha` e o estado de selecao das outras 36 telas. O
    rotulo passa a morar DENTRO dela, e nao precisa mais ser posicionado.

    A posicao da LINHA continua vindo da tabela de coordenadas, como
    antes. Nao dependemos de layout automatico — conferido: o
    CRIA_CONTEINER so limpa o flag de rolagem e zera os pads, nao
    configura flex.

O QUE PODE DAR ERRADO, E E PROVAVEL

    - as nove linhas podem empilhar em cima umas das outras, se a
      coordenada da imagem nao servir para a linha;
    - a linha pode nascer com largura zero e nada aparecer;
    - a selecao pode continuar sendo pintada no rotulo (os dois pontos de
      0x0012EB42 e 0x0012EDB2 NAO sao tocados aqui, de proposito: um
      experimento por vez).

    Qualquer um desses e visivel na hora, e o `.up` da 2.3 desfaz.

POR QUE ASSIM, E NAO DE UMA VEZ

    Este e o primeiro experimento do projeto que troca a CLASSE de um
    objeto em tela. Trocar tambem a selecao no mesmo passo tornaria
    impossivel saber qual das duas coisas quebrou.

USO
    python3 tools/exp_home_linha.py --in <e.bin> --out <s.bin> [--dry-run]
"""

import argparse, hashlib, struct, sys

XIP       = 0x00C00000
IMG       = 0x00D5D850      # lv_img_create
LINHA     = 0x00D21764      # CRIA_LINHA
POSICIONA = 0x00DA5760      # nossa rotina de posicao
PROIBIDO  = 0x0000D000

P_CRIA  = 0x0012ECF0        # bl lv_img_create
P_PAI   = 0x0012ED24        # mov r0, r7   (pai do rotulo)
P_POS   = 0x0012ED7E        # bl posiciona (o rotulo)


def enc_bl(o, d):
    off = d - (o + 4)
    off &= (1 << 25) - 1
    S = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    return struct.pack("<HH", 0xF000 | (S << 10) | ((off >> 12) & 0x3FF),
                       0xD000 | (((~i1 & 1) ^ S) << 13) | (((~i2 & 1) ^ S) << 11)
                       | ((off >> 1) & 0x7FF))


def dec_bl(o, b):
    w1, w2 = struct.unpack("<HH", b)
    if (w1 & 0xF800) != 0xF000 or (w2 & 0xD000) != 0xD000:
        return None
    S = (w1 >> 10) & 1
    j1, j2 = (w2 >> 13) & 1, (w2 >> 11) & 1
    off = (S << 24) | (((~(j1 ^ S)) & 1) << 23) | (((~(j2 ^ S)) & 1) << 22) \
        | ((w1 & 0x3FF) << 12) | ((w2 & 0x7FF) << 1)
    return o + 4 + (off - (1 << 25) if S else off)


def main():
    ap = argparse.ArgumentParser(description="EXPERIMENTO: home com CRIA_LINHA")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != 0x200000:
        print(f"ERRO: {a.src} tem {len(d)} B", file=sys.stderr)
        return 1
    orig = bytes(d)

    print("\n  EXPERIMENTO — a home passa a usar CRIA_LINHA\n")

    # guardas, todas antes de escrever
    if dec_bl(P_CRIA + XIP, bytes(d[P_CRIA:P_CRIA + 4])) != IMG:
        print(f"  ABORTADO: 0x{P_CRIA:06X} nao chama lv_img_create.",
              file=sys.stderr)
        return 1
    if struct.unpack_from("<H", d, P_PAI)[0] != 0x4638:      # mov r0, r7
        print(f"  ABORTADO: 0x{P_PAI:06X} nao e 'mov r0, r7' "
              f"(achei 0x{struct.unpack_from('<H', d, P_PAI)[0]:04X}).",
              file=sys.stderr)
        return 1
    if dec_bl(P_POS + XIP, bytes(d[P_POS:P_POS + 4])) != POSICIONA:
        print(f"  ABORTADO: 0x{P_POS:06X} nao chama a rotina de posicao.",
              file=sys.stderr)
        return 1
    print("    os tres pontos conferidos")
    print()

    d[P_CRIA:P_CRIA + 4] = enc_bl(P_CRIA + XIP, LINHA)
    d[P_PAI:P_PAI + 2] = struct.pack("<H", 0x4648)           # mov r0, sb(r9)
    d[P_POS:P_POS + 4] = struct.pack("<HH", 0xBF00, 0xBF00)  # nop ; nop

    print("  ALTERACOES")
    print(f"    0x{P_CRIA:06X}  bl lv_img_create -> bl CRIA_LINHA")
    print(f"    0x{P_PAI:06X}  mov r0,r7 -> mov r0,sb   "
          f"(o rotulo nasce DENTRO da linha)")
    print(f"    0x{P_POS:06X}  bl posiciona -> nop ; nop")
    print()

    v1 = dec_bl(P_CRIA + XIP, bytes(d[P_CRIA:P_CRIA + 4]))
    v2 = struct.unpack_from("<H", d, P_PAI)[0]
    print(f"  conferencia: 0x{P_CRIA:06X} -> 0x{v1:08X}  "
          f"{'OK' if v1 == LINHA else 'DIVERGE'}")
    print(f"               0x{P_PAI:06X} -> 0x{v2:04X}      "
          f"{'OK' if v2 == 0x4648 else 'DIVERGE'}")
    if v1 != LINHA or v2 != 0x4648:
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
