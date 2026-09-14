#!/usr/bin/env python3
"""
fix_barra_selecao_criacao.py — a home tinha DUAS selecoes ao mesmo tempo.

O QUE O MANTENEDOR VIU (2026-09-14, com a Core 2.0 no aparelho)

    Na foto da home: "Configurar" em CIANO e "Pastas" com a BARRA. Dois
    itens realcados de jeitos diferentes, ao mesmo tempo. Na foto
    anterior, "Musica" em ciano e a barra em "Gravacao".

A CAUSA — um caminho corrigido, outro esquecido. De novo.

    A home pinta a selecao em DOIS lugares, e a documentacao do
    `patch_cor_selecao.py` ja os nomeava:

        0x00D2EB42   navegacao   <- o `patch_barra_selecao` corrigiu
        0x00D2EDB2   criacao     <- ESQUECIDO

    O `patch_barra_selecao` troca `set_style_text_color` por
    `set_style_bg_color` em **0x0012EB4C**, o ponto da navegacao. O ponto
    gemeo da criacao, **0x0012EDBC**, continuou chamando
    `set_style_text_color`.

    Resultado: ao ENTRAR na tela, o item selecionado ganha cor de LETRA
    ciano. Ao navegar, a barra se move certo — mas a letra ciano do item
    pintado na criacao fica para tras, porque nada a limpa.

    Isso explica as duas fotos. Na segunda o mantenedor tinha voltado de
    Configurar: a home restaurou a selecao nele, pintou a letra na
    criacao, e ele desceu para Pastas.

    > **O padrao, agora na QUARTA vez** (V016, V027, V031, e a barra de
    > rolagem): quando um patch muda a aparencia de um objeto, enumerar
    > TODOS os pontos que criam ou repintam aquele objeto. Aqui os dois
    > pontos estavam escritos, com nome, na docstring de outra
    > ferramenta do proprio projeto.

O CONSERTO — 4 bytes

    0x0012EDBC   bl set_style_text_color -> bl set_style_bg_color

    O `bg_opa` daquele caminho JA esta ligado: o `patch_barra_selecao`
    desviou 0x0012ED58 para a rotina que liga opacidade, e ela fica no
    mesmo trecho de criacao, antes deste ponto. Por isso a barra aparece
    sem nada mais.

USO
    python3 tools/fix_barra_selecao_criacao.py --in <e.bin> --out <s.bin>
                                               [--dry-run]

DEPENDENCIAS
    Python 3

LIMITACOES
    - exige o `patch_barra_selecao` ja aplicado: recusa se 0x0012EB4C
      nao estiver apontando para bg_color, porque ai o defeito e outro;
    - nao mexe na cor. A cor sai da tabela do Saturno.
"""

import argparse, hashlib, struct, sys

XIP          = 0x00C00000
BG_COLOR     = 0x00D4D092
TEXT_COLOR   = 0x00D4D10A
PONTO_CRIA   = 0x0012EDBC     # o esquecido
PONTO_NAVEGA = 0x0012EB4C     # o que o patch_barra_selecao ja corrigiu
PROIBIDO     = 0x0000D000


def enc_bl(origem, destino):
    off = destino - (origem + 4)
    if not -(1 << 24) <= off < (1 << 24) or off & 1:
        raise ValueError("salto fora de alcance")
    off &= (1 << 25) - 1
    S = (off >> 24) & 1
    i1 = (off >> 23) & 1
    i2 = (off >> 22) & 1
    imm10 = (off >> 12) & 0x3FF
    imm11 = (off >> 1) & 0x7FF
    j1 = (~i1 & 1) ^ S
    j2 = (~i2 & 1) ^ S
    return struct.pack("<HH", 0xF000 | (S << 10) | imm10,
                       0xD000 | (j1 << 13) | (j2 << 11) | imm11)


def dec_bl(origem, b):
    w1, w2 = struct.unpack("<HH", b)
    if (w1 & 0xF800) != 0xF000 or (w2 & 0xD000) != 0xD000:
        return None
    S = (w1 >> 10) & 1
    imm10 = w1 & 0x3FF
    j1 = (w2 >> 13) & 1
    j2 = (w2 >> 11) & 1
    imm11 = w2 & 0x7FF
    i1 = (~(j1 ^ S)) & 1
    i2 = (~(j2 ^ S)) & 1
    off = (S << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if S:
        off -= 1 << 25
    return origem + 4 + off


def main():
    ap = argparse.ArgumentParser(description="a segunda selecao da home")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != 0x200000:
        print(f"ERRO: {a.src} tem {len(d)} B, esperado 2097152", file=sys.stderr)
        return 1
    orig = bytes(d)

    print("\n  A SEGUNDA SELECAO DA HOME\n")

    nav = dec_bl(PONTO_NAVEGA + XIP, bytes(d[PONTO_NAVEGA:PONTO_NAVEGA + 4]))
    cri = dec_bl(PONTO_CRIA + XIP, bytes(d[PONTO_CRIA:PONTO_CRIA + 4]))
    nome = {BG_COLOR: "set_style_bg_color", TEXT_COLOR: "set_style_text_color"}
    print(f"    navegacao  0x{PONTO_NAVEGA:06X} -> 0x{nav:08X}  "
          f"{nome.get(nav, '?')}")
    print(f"    criacao    0x{PONTO_CRIA:06X} -> 0x{cri:08X}  "
          f"{nome.get(cri, '?')}")
    print()

    if nav != BG_COLOR:
        print("  ABORTADO: a navegacao nao esta em bg_color. Esperava o "
              "patch_barra_selecao aplicado — o defeito aqui e outro.",
              file=sys.stderr)
        return 1
    if cri == BG_COLOR:
        print("  a criacao ja esta em bg_color — nada a fazer")
        return 0
    if cri != TEXT_COLOR:
        print(f"  ABORTADO: a criacao chama 0x{cri:08X}, que nao e nenhum "
              "dos dois esperados.", file=sys.stderr)
        return 1

    d[PONTO_CRIA:PONTO_CRIA + 4] = enc_bl(PONTO_CRIA + XIP, BG_COLOR)

    volta = dec_bl(PONTO_CRIA + XIP, bytes(d[PONTO_CRIA:PONTO_CRIA + 4]))
    print("  ALTERACOES")
    print(f"    0x{PONTO_CRIA:06X}   4 B  bl text_color -> bl bg_color")
    print(f"  conferencia: decodificado de volta -> 0x{volta:08X}  "
          f"{'OK' if volta == BG_COLOR else 'DIVERGE'}")
    if volta != BG_COLOR:
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
