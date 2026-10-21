#!/usr/bin/env python3
"""
fab_fundo_preto.py — itens 2, 3 e 4 da ficha 001 (Reload 1.0 RC2): o
fundo preto.

PROPOSITO

    Tirar o branco de tres lugares, sem mexer em nada mais:

      item 2  o fundo da TELA DE ABERTURA, nas duas rotinas que a
              desenham: o `bl` da funcao de cor branca passa a chamar a
              funcao de cor preta que a propria fabrica traz ao lado;
      item 3  o fundo do DISPLAY, todo: um imediato de cor;
      item 4  o PAPEL DE PAREDE da tela Tocando Agora: as 256 cores da
              paleta viram preto.

    Nenhum dos tres aloca, nenhum cria objeto, nenhum mexe em header.

O QUE CADA ITEM TROCA

    0x12285A, 0x1228E4   `bl 0x00D21384`  ->  `bl 0x00D2138A`
                         o retorno vai para 0x00D4D092, o estilo bg da
                         tela. Trocar o ALVO — e nao a funcao — mantem a
                         lista de chamadas e a conferencia iguais.

                         0x00D21384  mov.w r0,#-1 ; nop ; bx lr   (branco)
                         0x00D2138A  mov.w r0,#0  ; nop ; bx lr   (preto)

    0x1567F6            `ff 23` -> `00 23`
                         `movs r3,#0xff` -> `movs r3,#0`, seguido de tres
                         `strb.w r3,[r4,#0x29/0x2a/0x2b]`: a cor de fundo
                         do display, em R, G e B.

    0x0C73C4..0x0C77C4  paleta do papel de parede: 256 entradas de 4
                         bytes. Vira B=G=R=0 e o alfa fica como estava.
                         O cabecalho (0x0C73B8) e os pixels
                         (0x0C77C4..0x0C87C4) NAO sao tocados — so a cor
                         muda, o desenho continua.

PREMISSAS, conferidas ANTES de escrever qualquer byte

    A ficha pede recusa (D3) e nao aceitacao. Se UMA premissa falhar, a
    ferramenta sai com codigo diferente de zero, sem criar o arquivo de
    saida e sem tocar na entrada:

      - a imagem tem 2 MiB;
      - os dois descritores INDEXED_8 sao os de fabrica, INTEIROS: os 32
        bits do cabecalho palavra por palavra (cf, always_zero, os bits
        reservados e a largura/altura embutidas), mais o data_size e o
        ponteiro XIP — o da logo da abertura (0x0CC7C4) e o do papel de
        parede (0x0C73B8). Conferir so o cf e a largura deixaria passar
        um sempre_zero ou um bit reservado aceso (achado 001-R1);
      - os dois `bl` da abertura (0x12285A e 0x1228E4) sao exatamente a
        codificacao de fabrica do salto para 0x00D21384;
      - 0x1567F6 ainda e `ff 23`;
      - as duas funcoes de cor da fabrica estao intactas: 0x00D21384 e
        0x00D2138A. Sem a preta nao ha o que chamar; sem a branca nao ha
        como saber que o salto era o de fabrica.

    Este item 2 e o unico jeito de trocar a cor da abertura: a funcao
    preta ja existe na imagem. Nada e alocado, nada e criado, nada e
    sobrescrito — por isso as premissas importam tanto.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`, achado 001-R1).
    Sem isso, um link com outro nome passava pela comparacao de caminho
    e a gravacao escrevia por cima da entrada.

USO

    python3 tools/fab_fundo_preto.py --in <entrada.bin> --out <saida.bin>
                                     [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib). Nao abre USB, nao grava no aparelho.

LIMITACOES

    - so serve na imagem que a ficha mediu: qualquer outra e recusada,
      mesmo que os endereços existam;
    - o item 2 troca o alvo dos DOIS `bl`. Nao da para escolher um so;
      as duas rotinas da abertura compartilham o estilo, e trocar uma
      so deixaria a tela com dois fundos;
    - o item 4 deixa as 256 cores pretas. O desenho do papel de parede
      continua o de fabrica — o que se ve e preto sobre preto, que e o
      pedido;
    - depois da RC2, rodar de novo sobre a saida e recusado (o `bl` ja
      nao e o de fabrica). E o comportamento correto: a ferramenta e
      feita para a receita, uma vez.
"""

import argparse
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

XIP = 0x00C00000
TAMANHO = 0x200000                          # 2 MiB

# --- item 4: papel de parede da Tocando Agora
PAPEL_CAB = 0x0C73B8
PAPEL_DADOS = 0x0C73C4
PAPEL_PALETA_FIM = PAPEL_DADOS + 1024       # 0x0C77C4
PAPEL_FIM = PAPEL_PALETA_FIM + 128 * 160
PAPEL_CAB_FABRICA = 0x1402000A
PAPEL_TAM_FABRICA = 1024 + 128 * 160
PAPEL_PTR_FABRICA = PAPEL_DADOS + XIP

# --- o outro descritor, conferido so como premissa
LOGO_CAB = 0x0CC7C4
LOGO_CAB_FABRICA = 0x0462000A
LOGO_TAM_FABRICA = 1024 + 128 * 35
LOGO_PTR_FABRICA = 0x0CC7D0 + XIP

# --- item 2: o fundo da abertura
ABERTURA_BL = (0x12285A, 0x1228E4)
COR_BRANCA = 0x00D21384
COR_PRETA = 0x00D2138A
ESTILO_BG = 0x00D4D092                      # para onde o retorno vai
FUNCOES_FABRICA = {
    COR_BRANCA: bytes.fromhex("4ff0ff307047"),   # mov.w r0,#-1 ; nop ; bx lr
    COR_PRETA: bytes.fromhex("4ff000007047"),    # mov.w r0,#0  ; nop ; bx lr
}

# --- item 3: o fundo do display
FUNDO_DISPLAY = 0x1567F6
FUNDO_DISPLAY_FABRICA = b"\xff\x23"          # movs r3,#0xff
FUNDO_DISPLAY_NOVO = b"\x00\x23"              # movs r3,#0


# ---------------------------------------------------------------------------
# Thumb-2: `bl` de 32 bits (T1). A premissa e sobre o ALVO do salto, e o
# alvo so se le decodificando — comparar bytes crus nao diz para onde
# o aparelho vai.
# ---------------------------------------------------------------------------

def bl_alvo(b, a):
    """offset no arquivo -> endereco XIP de um `bl` de 32 bits, ou None."""
    h1, h2 = struct.unpack_from("<HH", b, a)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xD000) != 0xD000:
        return None
    S = (h1 >> 10) & 1
    J1, J2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    I1, I2 = 1 - (J1 ^ S), 1 - (J2 ^ S)
    off = (S << 24) | (I1 << 23) | (I2 << 22) | ((h1 & 0x3FF) << 12) \
        | ((h2 & 0x7FF) << 1)
    if S:
        off -= 1 << 25
    return XIP + a + 4 + off


def enc_bl(de, para):
    """endereco do `bl` -> enderevo alvo -> 4 bytes (T1, sinal de 25 bits)."""
    off = para - (de + 4)
    if not -(1 << 24) <= off < (1 << 24):
        raise ValueError(f"0x{de:08X} -> 0x{para:08X} fora do alcance do bl")
    S = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = 1 - (i1 ^ S), 1 - (i2 ^ S)
    h1 = 0xF000 | (S << 10) | ((off >> 12) & 0x3FF)
    h2 = 0xD000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF)
    return struct.pack("<HH", h1, h2)


# ---------------------------------------------------------------------------
# premissas
# ---------------------------------------------------------------------------

def confere_descritor(d, cab, nome, cab_fabrica, tam_fabrica, ptr_fabrica,
                      larg, alt):
    """O descritor e INTEIRO de fabrica: os 32 bits do cabecalho palavra por
    palavra — cf, always_zero, os bits reservados e a largura/altura
    embutidas — mais o data_size e o ponteiro XIP.

    Conferir campo por campo deixava passar um sempre_zero ou um bit
    reservado aceso: sao bits que o aparelho le, e a ficha diz que o
    descritor e premissa, nao o seu campo util (achado 001-R1, MEDIA).
    """
    cab_pal, tam, ptr = struct.unpack_from("<3I", d, cab)
    erros = []
    if cab_pal != cab_fabrica:
        erros.append(f"{nome} 0x{cab:06X}: cabecalho 0x{cab_pal:08X}, "
                     f"esperado 0x{cab_fabrica:08X} inteiro "
                     f"(cf, always_zero, reservados, {larg}x{alt})")
    if tam != tam_fabrica:
        erros.append(f"{nome} 0x{cab:06X}: data_size=0x{tam:X}, "
                     f"esperado 0x{tam_fabrica:X}")
    if ptr != ptr_fabrica:
        erros.append(f"{nome} 0x{cab:06X}: ponteiro=0x{ptr:08X}, esperado "
                     f"0x{ptr_fabrica:08X}")
    return erros


def confere_premissas(d):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    erros = []
    if len(d) != TAMANHO:
        erros.append(f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)")
        return erros

    erros += confere_descritor(d, PAPEL_CAB, "papel de parede",
                               PAPEL_CAB_FABRICA, PAPEL_TAM_FABRICA,
                               PAPEL_PTR_FABRICA, 128, 160)
    erros += confere_descritor(d, LOGO_CAB, "logo da abertura",
                               LOGO_CAB_FABRICA, LOGO_TAM_FABRICA,
                               LOGO_PTR_FABRICA, 128, 35)

    for a in ABERTURA_BL:
        esperado = enc_bl(XIP + a, COR_BRANCA)
        got = bytes(d[a:a + 4])
        if got != esperado:
            alvo = bl_alvo(d, a)
            erros.append(f"0x{a:06X} = {got.hex()}, esperado {esperado.hex()} "
                         f"(o `bl` de fabrica aponta para "
                         f"{'nada' if alvo is None else f'0x{alvo:08X}'})")

    if bytes(d[FUNDO_DISPLAY:FUNDO_DISPLAY + 2]) != FUNDO_DISPLAY_FABRICA:
        erros.append(f"0x{FUNDO_DISPLAY:06X} = "
                     f"{bytes(d[FUNDO_DISPLAY:FUNDO_DISPLAY + 2]).hex()}, "
                     f"esperado ff23")

    for func, esperado in FUNCOES_FABRICA.items():
        o = func - XIP
        got = bytes(d[o:o + len(esperado)])
        if got != esperado:
            erros.append(f"0x{func:08X} = {got.hex()}, esperado "
                         f"{esperado.hex()}")

    return erros


# ---------------------------------------------------------------------------
# os tres itens
# ---------------------------------------------------------------------------

def fundo_abertura(d, antes):
    """item 2: o alvo dos dois `bl` vai da cor branca para a cor preta."""
    print("  ITEM 2 — fundo da tela de abertura")
    for a in ABERTURA_BL:
        velho = bytes(d[a:a + 4])
        d[a:a + 4] = enc_bl(XIP + a, COR_PRETA)
        print(f"    0x{a:06X}  bl 0x{antes[a]:08X}  ->  bl 0x{COR_PRETA:08X}"
              f"   [{velho.hex()} -> {bytes(d[a:a + 4]).hex()}]")
    print(f"    o retorno continua indo para o estilo bg 0x{ESTILO_BG:08X}")
    print(f"    0x{COR_PRETA:08X} = mov.w r0,#0 ; nop ; bx lr  (funcao de "
          f"fabrica, INTOCADA)")
    print()


def fundo_display(d):
    """item 3: o imediato da cor de fundo do display."""
    d[FUNDO_DISPLAY:FUNDO_DISPLAY + 2] = FUNDO_DISPLAY_NOVO
    print("  ITEM 3 — fundo do display")
    print(f"    0x{FUNDO_DISPLAY:06X}  ff 23 -> 00 23   "
          f"(movs r3,#0xff -> movs r3,#0)")
    print(f"    alimenta os tres strb.w r3,[r4,#0x29/0x2a/0x2b] "
          f"(R, G e B do fundo)")
    print()


def papel_preto(d):
    """item 4: as 256 cores da paleta do papel de parede viram preto."""
    print("  ITEM 4 — papel de parede da Tocando Agora")
    antes = bytes(d[PAPEL_DADOS:PAPEL_PALETA_FIM])
    depois = bytearray(antes)
    for i in range(256):
        depois[i * 4:i * 4 + 3] = b"\x00\x00\x00"        # B = G = R = 0
        # o alfa (i * 4 + 3) fica como estava
    d[PAPEL_DADOS:PAPEL_PALETA_FIM] = bytes(depois)
    mudados = sum(1 for i in range(1024)
                  if i % 4 != 3 and antes[i] != depois[i])
    alfa_ok = all(antes[i * 4 + 3] == depois[i * 4 + 3] for i in range(256))
    print(f"    paleta    0x{PAPEL_DADOS:06X}..0x{PAPEL_PALETA_FIM:06X}  "
          f"{mudados} bytes de cor -> 0, alfa preservado: {alfa_ok}")
    for i in (0, 1, 2, 128, 255):
        print(f"      cor {i:3d}  {antes[i * 4:i * 4 + 4].hex()} -> "
              f"{depois[i * 4:i * 4 + 4].hex()}")
    print(f"    cabecalho 0x{PAPEL_CAB:06X} e pixels "
          f"0x{PAPEL_PALETA_FIM:06X}..0x{PAPEL_FIM:06X} NAO tocados")
    print()


PERMITIDO = [(PAPEL_DADOS, PAPEL_PALETA_FIM), (FUNDO_DISPLAY, FUNDO_DISPLAY + 2)] \
    + [(a, a + 4) for a in ABERTURA_BL]


def confere_resultado(d):
    """Rele o que foi escrito e confere no cabecalho / no codigo."""
    erros = []
    for a in ABERTURA_BL:
        alvo = bl_alvo(d, a)
        if alvo != COR_PRETA:
            erros.append(f"0x{a:06X} aponta para "
                         f"{'nada' if alvo is None else f'0x{alvo:08X}'}, "
                         f"esperado 0x{COR_PRETA:08X}")
    if bytes(d[FUNDO_DISPLAY:FUNDO_DISPLAY + 2]) != FUNDO_DISPLAY_NOVO:
        erros.append(f"0x{FUNDO_DISPLAY:06X} nao virou 0023")
    pal = bytes(d[PAPEL_DADOS:PAPEL_PALETA_FIM])
    for i in range(256):
        if pal[i * 4:i * 4 + 3] != b"\x00\x00\x00":
            erros.append(f"cor {i} da paleta nao ficou preta")
            break
    for func, esperado in FUNCOES_FABRICA.items():
        o = func - XIP
        if bytes(d[o:o + len(esperado)]) != esperado:
            erros.append(f"0x{func:08X} foi alterada")
    return erros


def mesma_entrada(src, dst):
    """--out aponta para a propria entrada?

    Comparar caminho resolve so o caso literal. Um symlink ou um hardlink
    com outro nome passa pela comparacao e a gravacao vai DENTRO da
    entrada — que e o que a regra do projeto proibe (achado 001-R1,
    BAIXA). `samefile` pergunta ao sistema de arquivos qual arquivo e,
    nao como ele se chama.
    """
    if os.path.abspath(src) == os.path.abspath(dst):
        return True
    if not os.path.lexists(dst):          # saida ainda nao existe: nada a ver
        return False
    try:
        return os.path.samefile(src, dst)
    except OSError:                       # link pendurado, sem permissao
        return False


def main():
    ap = argparse.ArgumentParser(
        description="fundo preto: abertura, display e papel de parede")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — RC2 itens 2, 3 e 4: fundo preto")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    # --- premissas, ANTES de qualquer escrita
    erros = confere_premissas(d)
    if erros:
        print("  RECUSADO — a entrada nao e a imagem de fabrica que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print(f"    - 2 MiB; os dois descritores INDEXED_8 de fabrica")
    print(f"    - os dois `bl` da abertura sao o salto de fabrica para "
          f"0x{COR_BRANCA:08X}")
    print(f"    - 0x{FUNDO_DISPLAY:06X} = ff23 (fundo do display)")
    print(f"    - 0x{COR_BRANCA:08X} (branca) e 0x{COR_PRETA:08X} (preta) "
          f"intactas")
    print()

    antes = {o: bl_alvo(d, o) for o in ABERTURA_BL}
    fundo_abertura(d, antes)
    fundo_display(d)
    papel_preto(d)

    erros = confere_resultado(d)
    if erros:
        print("  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  conferencia (saltos lidos de volta, paleta e funcoes): "
          "tudo OK\n")

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    fora = [i for i in dif if not any(a0 <= i < b0 for a0, b0 in PERMITIDO)]
    if fora:
        print(f"  RECUSADO: escreveu fora do permitido em "
              f"0x{min(fora):06X}..0x{max(fora):06X}", file=sys.stderr)
        return 1
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())