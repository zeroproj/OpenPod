#!/usr/bin/env python3
"""
fab_logo.py — item 1 da ficha 001 (Reload 1.0 RC2): a logo da abertura
passa a ser `assets/OpenLogo.png`.

PROPOSITO

    Trocar a imagem da tela de abertura pela logo do OpenPod, sem tocar
    no cabecalho da `lv_img_dsc`. O slot e o mesmo da fabrica: 128x35,
    INDEXED_8, paleta de 256 cores BGRA e 1 byte por pixel. Nada mais na
    flash muda.

O SLOT (docs/IMAGENS.md; verificado no ORIGINAL em 2026-10-21)

    0x0CC7C4   lv_img_dsc
               0x0462000A  cf=10 (INDEXED_8BIT), w=128, h=35
               0x00001580  data_size = 5504 = 1024 (paleta) + 4480 (pixels)
               0x00CCC7D0  ponteiro XIP -> flash 0x000CC7D0
    0x0CC7D0   paleta: 256 entradas de 4 bytes, na ordem B, G, R, A
    0x0CCBD0   pixels: 128 * 35 = 4480 indices
    0x0CDD50   fim (exclusive)

    O CABECALHO NAO E TOCADO. A imagem nova tem as mesmas 128x35, o
    mesmo cf e o mesmo data_size, entao a forma do slot continua exata.

    A imagem e lida pelas duas rotinas da abertura, pelos pools em
    0x12289C e 0x122924. O fundo preto da abertura e outro item (item 2
    da ficha, em tools/fab_fundo_preto.py) — aqui so a imagem.

PREMISSAS, conferidas ANTES de escrever qualquer byte

    A ficha pede recusa (D3) e nao aceitacao. Se UMA premissa falhar, a
    ferramenta sai com codigo diferente de zero sem criar o arquivo de
    saida e sem tocar na entrada:

      - a imagem tem 2 MiB;
      - o cabecalho da `lv_img_dsc` e o de fabrica, INTEIRO: os 32 bits
        palavra por palavra (cf, always_zero, os bits reservados e a
        largura/altura embutidas), o data_size, e o ponteiro XIP
        apontando para 0x000CC7D0. Conferir so o cf e a largura deixaria
        passar um sempre_zero ou um bit reservado aceso (achado 001-R1);
      - o cabecalho da imagem do papel de parede (0x0C73B8) tambem e o
        de fabrica, inteiro — a imagem tem de ser a que a ficha
        descreve, nao qualquer uma do tamanho certo;
      - os dois `bl` da abertura (0x12285A e 0x1228E4) ainda chamam a
        funcao de cor branca 0x00D21384;
      - 0x1567F6 ainda e `ff 23` (o `movs r3,#0xff` do fundo do display);
      - as duas funcoes de cor da propria fabrica continuam intactas:
        0x00D21384 = `mov.w r0,#-1` e 0x00D2138A = `mov.w r0,#0`;
      - `assets/OpenLogo.png` tem o sha256 e o tamanho fixados pela ficha.

    As tres ultimas conferem o resto da imagem, que esta ferramenta nao
    escreve. Se a imagem nao for a de fabrica la, entao nao e a imagem
    que a ficha mediu — e e exatamente o dano D3 que a recusa evita:
    escrever as contas certas no lugar errado.

CONFERENCIA DE SAIDA

    Apos escrever, a ferramenta le de volta o que escreveu, pelo
    cabecalho, e compara com o PNG: erro medio por canal no maximo 2.0,
    erro maximo 64 e alfa 255 em todos os pixels. Sao os limites dos
    criterios de aceite; se algum estourar, a ferramenta recusa em vez
    de gravar uma imagem que ninguem conferiu.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`, achado 001-R1).
    Sem isso, um link com outro nome passava pela comparacao de caminho
    e a gravacao escrevia por cima da entrada.

USO

    python3 tools/fab_logo.py --in <entrada.bin> --out <saida.bin>
                              [--png assets/OpenLogo.png] [--dry-run]

DEPENDENCIAS

    Python 3 + Pillow (quantizacao). Nao abre USB, nao grava no aparelho.

LIMITACOES

    - a imagem nova precisa ter exatamente 128x35: a ferramenta nao
      redimensiona nem recorta, porque o slot e fixo e a ficha fixa a
      imagem;
    - a logo precisa ser OPACA. Nao ha composicao de alfa: um pixel
      transparente viraria uma cor da paleta e apareceria como um retangulo
      de cor, nao como Absence. Recusa em vez de adivinhar;
    - a paleta e escrita com alfa 255 nas 256 entradas: as entradas nao
      usadas por nenhum pixel nao aparecem na tela;
    - a paleta e gerada por median cut do Pillow. Com o sha256 fixado
      pela ficha, o resultado e reproduzivel com a mesma versao do
      Pillow; a conferencia de erro acima e o que garante a imagem, nao o
      algoritmo.
"""

import argparse
import hashlib
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- o slot (offset no arquivo = endereco - XIP)
XIP = 0x00C00000
CAB = 0x0CC7C4                       # lv_img_dsc da logo da abertura
DADOS = 0x0CC7D0                     # paleta (1024 B) + pixels (4480 B)
PALETA_FIM = DADOS + 1024
FIM = PALETA_FIM + 128 * 35          # 0x0CDD50
LARG, ALT = 128, 35
CF_INDEXED_8 = 10
CAB_FABRICA = 0x0462000A
TAM_FABRICA = 1024 + LARG * ALT      # 5504
PTR_FABRICA = DADOS + XIP

# --- o outro descritor, conferido so como premissa
PAPEL_CAB = 0x0C73B8
PAPEL_CAB_FABRICA = 0x1402000A
PAPEL_TAM_FABRICA = 1024 + 128 * 160
PAPEL_PTR_FABRICA = 0x0C73C4 + XIP

# --- premissas de fabrica fora do slot (medidas na ficha)
ABERTURA_BL = (0x12285A, 0x1228E4)
FUNDO_DISPLAY = 0x1567F6
FUNDO_DISPLAY_FABRICA = b"\xff\x23"          # movs r3,#0xff
FUNCAO_BRANCA = 0x00D21384                    # mov.w r0,#-1 ; nop ; bx lr
FUNCAO_PRETA = 0x00D2138A                    # mov.w r0,#0  ; nop ; bx lr
FUNCOES_FABRICA = {
    FUNCAO_BRANCA: bytes.fromhex("4ff0ff307047"),
    FUNCAO_PRETA: bytes.fromhex("4ff000007047"),
}

TAMANHO = 0x200000                          # 2 MiB

PNG_PADRAO = "assets/OpenLogo.png"
SHA_PNG = "1e459938eddc15416d01fb9f29d7486400a2c9166ed159eac1ba0c58edf90d4d"

# limites da ficha (criterio de aceite C3)
ERRO_MEDIO_MAX = 2.0
ERRO_MAX_MAX = 64


# ---------------------------------------------------------------------------
# Thumb-2: decodifica o `bl` de 32 bits (T1). Precisa porque a premissa
# dos dois `bl` da abertura e sobre o ALVO do salto, e alvo se le no
# codigo — comparar bytes crus nao diz para onde o aparelho vai.
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


# ---------------------------------------------------------------------------
# PNG -> (1024 B de paleta BGRA, 4480 B de indices)
# ---------------------------------------------------------------------------

def quantiza(caminho):
    """Abre o PNG, confere o que a ficha fixou e devolve o par do slot."""
    try:
        from PIL import Image
    except ImportError:
        sys.exit("ERRO: Pillow nao esta instalado (pip3 install Pillow)")

    bruto = open(caminho, "rb").read()
    sha = hashlib.sha256(bruto).hexdigest()
    if sha != SHA_PNG:
        sys.exit(f"RECUSADO: {caminho} tem sha256 {sha}\n"
                 f"         a ficha fixa {SHA_PNG}")

    img = Image.open(caminho)
    if img.size != (LARG, ALT):
        sys.exit(f"RECUSADO: {caminho} tem {img.size[0]}x{img.size[1]} e o "
                 f"slot e {LARG}x{ALT}. A ferramenta nao redimensiona.")
    rgba = img.convert("RGBA")
    alfa = rgba.tobytes()[3::4]
    if min(alfa) != 255:
        sys.exit(f"RECUSADO: {caminho} tem alfa {min(alfa)}..{max(alfa)}. A "
                 f"logo precisa ser opaca — nao ha composicao de alfa aqui.")

    rgb = img.convert("RGB")
    try:                                    # Pillow >= 9.1
        q = rgb.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                         dither=Image.Dither.NONE)
    except (AttributeError, TypeError):     # Pillow antigo
        q = rgb.quantize(colors=256, method=Image.MEDIANCUT)

    pal = list(q.getpalette())[:768]
    pal += [0] * (768 - len(pal))
    blob = bytearray()
    for i in range(256):
        r, g, b = pal[i * 3:i * 3 + 3]
        blob += bytes((b, g, r, 255))       # BGRA
    px = q.tobytes()
    if len(px) != LARG * ALT:
        sys.exit(f"ERRO: a quantizacao devolveu {len(px)} indices, "
                 f"esperado {LARG * ALT}.")
    return bytes(blob), bytes(px), rgb


def erro_por_canal(rgb, pal, px):
    """|R,G,B do PNG| contra |B,G,R do que foi escrito|, canal a canal."""
    ref = rgb.tobytes()
    got = bytearray()
    for i in px:
        b, g, r = pal[i * 4:i * 4 + 3]
        got += bytes((r, g, b))
    return [abs(x - y) for x, y in zip(ref, got)]


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
    descritor e premissa, nao o seu campoutil (achado 001-R1, MEDIA).
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
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = tudo ok)."""
    erros = []
    if len(d) != TAMANHO:
        erros.append(f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)")
        return erros

    erros += confere_descritor(d, CAB, "logo da abertura", CAB_FABRICA,
                               TAM_FABRICA, PTR_FABRICA, LARG, ALT)
    erros += confere_descritor(d, PAPEL_CAB, "papel de parede",
                               PAPEL_CAB_FABRICA, PAPEL_TAM_FABRICA,
                               PAPEL_PTR_FABRICA, 128, 160)

    for a in ABERTURA_BL:
        alvo = bl_alvo(d, a)
        if alvo != FUNCAO_BRANCA:
            erros.append(f"0x{a:06X} chama "
                         f"{'nada' if alvo is None else f'0x{alvo:08X}'}, "
                         f"esperado 0x{FUNCAO_BRANCA:08X}")

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


def confere_slot(d, cab, nome):
    """A imagem escrita bate com o PNG e o alfa e opaco?"""
    erros = []
    _, _, ptr = struct.unpack_from("<3I", d, cab)
    base = ptr - XIP
    pal = bytes(d[base:base + 1024])
    cab_pal, _, _ = struct.unpack_from("<3I", d, cab)
    w = (cab_pal >> 10) & 0x7FF
    h = (cab_pal >> 21) & 0x7FF
    px = bytes(d[base + 1024:base + 1024 + w * h])
    alfa = {pal[i * 4 + 3] for i in px}
    if alfa != {255}:
        erros.append(f"{nome}: alfa {sorted(alfa)} nos pixels, esperado 255")
    return pal, px, erros


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
        description="logo da abertura = assets/OpenLogo.png")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--png", default=os.path.join(RAIZ, PNG_PADRAO),
                    help=f"PNG da logo (padrao {PNG_PADRAO})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — RC2 item 1: logo da abertura")
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
    print(f"    - 2 MiB, os dois descritores INDEXED_8 de fabrica")
    print(f"    - os dois `bl` da abertura ainda chamam 0x{FUNCAO_BRANCA:08X}")
    print(f"    - 0x{FUNDO_DISPLAY:06X} = ff23 (fundo do display)")
    print(f"    - 0x{FUNCAO_BRANCA:08X} e 0x{FUNCAO_PRETA:08X} intactas")
    print(f"    - cabecalho da logo em 0x{CAB:06X} intacto\n")

    pal, px, rgb = quantiza(a.png)
    d[DADOS:FIM] = pal + px

    # --- o que foi escrito, conferido pelo cabecalho
    pal2, px2, erros = confere_slot(d, CAB, "logo")
    difs = erro_por_canal(rgb, pal2, px2)
    medio, maximo = sum(difs) / len(difs), max(difs)
    if medio > ERRO_MEDIO_MAX:
        erros.append(f"erro medio {medio:.2f} > {ERRO_MEDIO_MAX}")
    if maximo > ERRO_MAX_MAX:
        erros.append(f"erro maximo {maximo} > {ERRO_MAX_MAX}")
    if erros:
        print("  RECUSADO — a imagem escrita nao passa na conferencia:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    print(f"  LOGO  {LARG}x{ALT} INDEXED_8, {len(set(px2))} cores usadas")
    print(f"    paleta   0x{DADOS:06X}..0x{PALETA_FIM:06X}  (256 entradas BGRA)")
    print(f"    pixels   0x{PALETA_FIM:06X}..0x{FIM:06X}  ({len(px2)} indices)")
    print(f"    alfa     255 nas 256 entradas")
    print(f"    erro contra o PNG: medio {medio:.2f} (max {ERRO_MEDIO_MAX}), "
          f"maximo {maximo} (max {ERRO_MAX_MAX})   OK")
    print(f"    cabecalho 0x{CAB:06X}..0x{DADOS:06X} NAO tocado\n")

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    fora = [i for i in dif if not DADOS <= i < FIM]
    if fora:
        print(f"  RECUSADO: escreveu fora do slot em "
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