#!/usr/bin/env python3
"""
fab_icones_home.py — item 2 da ficha 004 (Reload 1.0 RC4): os nove icones
da home passam a ser os de `assets/IconesHome.png`.

PROPOSITO

    A folha de icones do menu principal e uma imagem INDEXED_8 de 128x160
    com 256 cores. Em fabrica ela tem os nove icones circulares antigos,
    cinza-azulados sobre fundo claro; o PNG aprovado em 2026-09-24 tem os
    icones no estilo "Apple-like moderno", sobre fundo PRETO.

    Trocar a arte e o que a ficha pede. Como a folha e indexada, a troca
    acontece em DUAS metades ao mesmo tempo: os pixels viram os indices
    das cores novas, e a paleta (256 entradas) passa a guardar essas
    cores. Nenhuma delas sozinha entrega o desenho.

O SLOT (docs/IMAGENS.md; verificado no ORIGINAL e na RC3.1)

    0x0CDD50   lv_img_dsc (12 bytes)
               0x1402000A  cf=10 (INDEXED_8BIT), w=128, h=160
               0x00005400  data_size = 21504 = 1024 (paleta) + 20480
               0x00CCDD5C  ponteiro XIP -> flash 0x000CDD5C (a paleta)
    0x0CDD5C   paleta: 256 entradas de 4 bytes, na ordem B, G, R, A
    0x0CE15C   pixels: 128 * 160 = 20480 indices, linha a linha
    0x0D315C   fim (exclusive)

    O CABECALHO NAO E TOCADO. A imagem nova tem as mesmas 128x160 e o
    mesmo cf, entao a forma do slot continua exata e o aparelho le a
    folha do mesmo jeito.

    A paleta e BGRA SEM PRE-INVERSAO: a entrada 1 de fabrica e `00 00 00
    ff`, isto e, o canal alfa e o ULTIMO byte e vale 255. Nao e RGB565,
    e a folha nao tem a troca de bytes que a CRIA_FAIXA tem.

    A home NAO navega pelo desenho: ela roteia por tecla e por indice
    (docs/PLANO_HOME.md 1.2), e a selecao acha o rotulo no array B pelo
    indice (1.3). Trocar os indices de paleta, entao, nao mexe na
    navegacao nem na selecao — e a regra "cor -> paleta" que o projeto ja
    usou antes (V002, docs/CHANGELOG.md: os nove icones mudaram de cor de
    uma vez so por causa da paleta).

A PALETA NOVA (256 entradas, todas com alfa 255)

    entradas 0..15   a cor EXATA da linha y do degradê da barra,
                     `topo + (base - topo) * y / 15` arredondado, com
                     topo = RGB(64,70,82) e base = RGB(14,16,19). Sao as
                     mesmas contas de `fab_barra_degrade.py`, agora com a
                     cor IDEAL em vez do indice mais proximo. E o que
                     mantem o degradê da barra da RC3 (dano D4): em vez de
                     escolher de 256 cores, a barra tem uma cor so;
    entradas 16..255 240 cores dos pixels das linhas 16..159 do PNG,
                     por corte mediano (median cut) com peso de populacao,
                     e o preto (0,0,0) EXATO entre elas. Sao 2974 cores
                     distintas no PNG, e 240 e o que a folha tem.

OS PIXELS (20480 bytes)

    linhas y=0..15    toda a linha recebe o indice y — a barra e uma
                     rampa de indices, um por linha, como a RC3;
    linhas y=16..159  cada pixel recebe o indice da cor mais proxima da
                     PALETA INTEIRA (as 256 entradas). Um pixel (0,0,0)
                     do PNG tem de cair numa entrada (0,0,0) exata: e o
                     fundo preto, e fundo preto e o que a tela faz.

    O criterio de aceitacao (C4) e conferido pela propria ferramenta
    depois de escrever: erro MEDIO por canal no maximo 2,0 e erro MAXIMO
    de 64 em um canal so. O maximo existe por causa do dano D1: o criterio
    da media sozinho deixa passar um glifo apagado (todo o microfone da
    Gravacao virando fundo) porque o resto da tela continua perfeito.

PREMISSAS, conferidas ANTES de escrever qualquer byte

    A ficha pede recusa (D3) e nao aceitacao. Se UMA premissa falhar, a
    ferramenta sai com codigo diferente de zero, sem criar o arquivo de
    saida e sem tocar na entrada:

      - a imagem tem 2 MiB;
      - o cabecalho e a paleta (0x0CDD50..0x0CE15C) sao os de fabrica,
        sha256 preso. Sao os 12 bytes do descritor e as 1024 bytes da
        paleta; o descritor tambem e conferido palavra por palavra, para
        a recusa dizer QUAL campo divergiu;
      - as 144 linhas dos icones (0x0D015C..0x0D315C) sao as de fabrica.
        As 16 linhas da barra NAO entram aqui: elas mudam nesta RC, e a
        ficha aceita tanto o ORIGINAL (todas indice 1, preto) quanto a
        RC3 (uma cor por linha). O que precisa valer nas duas e so que a
        linha seja UNIFORME — e o que diz que aquela faixa e a barra e
        nao parte de um icone;
      - `assets/IconesHome.png` tem o sha256 e o tamanho (128x160) fixados
        pela ficha. Sem isso a ferramenta estaria gravando um desenho que
        ninguem aprovou (dano D1).

    As regioes "tem de ser as de fabrica" sao presas por sha256 em vez de
    coladas no fonte: 1 KiB de paleta e 18 KiB de pixels no fonte seriam
    ruido, e o sha diz a mesma coisa sem chance de erro de digito.

CONFERENCIA DE SAIDA

    Apos escrever, a ferramenta RELE a paleta e os pixels do proprio binario
    — sem confiar na montagem — e confere: as 16 entradas da barra contra a
    conta do degradê, alfa 255 nas 256 entradas, as 16 linhas uniforme no
    indice y, o cabecalho intocado, o preto do PNG indo para o preto
    exato, e o erro medio e o maximo contra o PNG.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`, achado 001-R1).
    Sem isso, um link com outro nome passaria pela comparacao de caminho
    e a gravacao escreveria por cima da entrada.

    E so se escreve DENTRO de 0x0CDD5C..0x0D315C: a paleta e os pixels.
    Qualquer byte fora disso e recusa, sem gravar.

USO

    python3 tools/fab_icones_home.py --in <entrada.bin> --out <saida.bin>
                                     [--png assets/IconesHome.png]
                                     [--dry-run]

DEPENDENCIAS

    Python 3 + Pillow (para ler o PNG; `pip3 install Pillow`). Nao abre
    USB, nao grava no aparelho.

LIMITACOES

    - so serve na imagem que a ficha mediu: o ORIGINAL ou a RC3.1, com a
      folha de icones no estado que elas mediram. Qualquer outra e
      recusada, mesmo que os enderecos existam;
    - a arte vira 240 cores: o PNG tem 2974 cores distintas e a folha tem
      256 entradas, das quais 16 sao da barra. O corte mediano ponderado
      por populacao entrega erro medio de ~1,1 por canal e maximo de ~36
      neste PNG; os degradês suaves dentro dos icones ficam com um leve
      degrau, invisivel a 1 bpp. E o mesmo preco da folha ser INDEXED_8,
      e a ficha o aceita;
    - a paleta fica com 240 cores dos icones + as 16 da barra; se o PNG
      tiver menos de 240 cores distintas, as entradas que sobrarem sao
      repetidas em (0,0,0). Com o PNG aprovado isso nao acontece;
    - a ferramenta NAO faz a selecao do icone andar: a selecao da home e
      do aparelho (rotulo + cor de texto, array B). O que muda e so o
      desenho;
    - a navegacao e por indice, nao pelo desenho (PLANO_HOME 1.2), entao
      nenhum indice em particular e sacredo — mas se algum dia o aparelho
      passar a escolher cor por indice, a paleta nova invalida essa
      escolha. Hoje nao ha codigo assim (a troca V002 da paleta, no
      CHANGELOG, e a prova);
    - depois de aplicada, rodar de novo sobre a saida e recusado (a paleta
      ja nao e a de fabrica). E o comportamento correto: a ferramenta e
      feita para a receita, uma vez.
"""

import argparse
import hashlib
import os
import struct
import sys
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XIP = 0x00C00000
TAMANHO = 0x200000                          # 2 MiB

# --- a folha
HOME_CAB, HOME_PAL, HOME_PX = 0x0CDD50, 0x0CDD5C, 0x0CE15C
HOME_LARG, HOME_ALT, HOME_BARRA = 128, 160, 16
HOME_FIM = HOME_PX + HOME_LARG * HOME_ALT  # 0x0D315C
HOME_PALETA = 256 * 4
HOME_CAB_PAL_SHA = ("0630d9d9b1e23a05a1294eb526b91176f09b832c12af6"
                    "8f8e9d89900c7f84eea")
HOME_ICONES_SHA = ("d8f1ec3bf97d591bba9f0266334ac2a063c6e35e4d7bba8"
                   "d4a656bb2252d4a32")
HOME_CAB_FABRICA = 0x1402000A
HOME_TAM_FABRICA = 21504                    # 1024 + 128*160
HOME_PTR_FABRICA = XIP + HOME_PAL

# --- o PNG aprovado
PNG_PADRAO = "assets/IconesHome.png"
SHA_PNG = "fbdd1dc714b1316b698cdf34bd1514595508f62250c5dc2da3fee910247d2b70"

# --- o degradê da barra: as MESMAS contas de fab_barra_degrade.py
COR_TOPO, COR_BASE = (64, 70, 82), (14, 16, 19)

# --- quantizacao
N_CORES_ICONE = 256 - HOME_BARRA            # 240 entradas para os icones
PRETO = (0, 0, 0)

# limites da ficha (criterio de aceite C4)
ERRO_MEDIO_MAX = 2.0
ERRO_MAX = 64

PERMITIDO = [(HOME_PAL, HOME_FIM)]


# ---------------------------------------------------------------------------
# o degradê: uma cor por linha, sem quantizar
# ---------------------------------------------------------------------------

def alvo_linha(y):
    """A cor ideal da linha y da barra: topo + (base - topo) * y / (linhas-1).

    A MESMA conta do criterio de aceite (C4). Ela fica aqui como fonte, e a
    conferencia final compara as 16 entradas escritas contra ela — se as
    duas copias divergissem, a ferramenta recusaria em vez de gravar.
    """
    t = y / (HOME_BARRA - 1)
    return tuple(round(COR_TOPO[k] + (COR_BASE[k] - COR_TOPO[k]) * t)
                 for k in range(3))


def paleta_barra():
    """As 16 entradas da faixa, na cor exata de cada linha do degradê."""
    return [alvo_linha(y) for y in range(HOME_BARRA)]


# ---------------------------------------------------------------------------
# o PNG: leitura e corte mediano
# ---------------------------------------------------------------------------

def le_png(caminho):
    """Abre o PNG, confere o que a ficha fixou e devolve os bytes RGB.

    Devolve o buffer de `img.convert("RGB").tobytes()`: tres bytes por
    pixel, na ordem R, G, B, linha a linha, 128x160.
    """
    if not os.path.exists(caminho):
        raise ValueError(f"{caminho} nao existe")
    bruto = open(caminho, "rb").read()
    sha = hashlib.sha256(bruto).hexdigest()
    if sha != SHA_PNG:
        raise ValueError(f"{caminho} tem sha256 {sha}\n"
                         f"         a ficha fixa {SHA_PNG}")
    try:
        from PIL import Image
    except ImportError:
        sys.exit("ERRO: Pillow nao esta instalado (pip3 install Pillow)")
    img = Image.open(caminho)
    if img.size != (HOME_LARG, HOME_ALT):
        raise ValueError(f"{caminho} tem {img.size[0]}x{img.size[1]} e a "
                         f"folha e {HOME_LARG}x{HOME_ALT}. A ferramenta nao "
                         f"redimensiona.")
    dados = img.convert("RGB").tobytes()
    if len(dados) != HOME_LARG * HOME_ALT * 3:
        raise ValueError(f"o PNG devolveu {len(dados)} bytes, esperado "
                         f"{HOME_LARG * HOME_ALT * 3}")
    return dados


def pixel(dados, x, y):
    """(x, y) do buffer RGB -> (r, g, b)."""
    o = (y * HOME_LARG + x) * 3
    return (dados[o], dados[o + 1], dados[o + 2])


def quantiza(dados):
    """As linhas 16..159 do PNG -> N_CORES_ICONE cores (corte mediano).

    Corte mediano com peso de POPULACAO: a cada passo a caixa com maior
    `alcance * pixels` e dividida no canal de maior alcance, pela metade da
    populacao. E o mesmo criterio do Pillow e do `fab_logo.py`, escrito
    aqui porque a ferramenta precisa de tres coisas que a biblioteca nao
    da: o numero exato de entradas (240, e nao 256), o preto (0,0,0)
    EXATO entre elas, e um resultado identico em qualquer Pillow.

    Devolve (cores, n_cores_distintas).
    """
    hist = Counter(pixel(dados, x, y)
                   for y in range(HOME_BARRA, HOME_ALT)
                   for x in range(HOME_LARG))
    cores = sorted(hist)
    pesos = [hist[c] for c in cores]

    caixas = [(cores, pesos)]
    while len(caixas) < N_CORES_ICONE:
        melhor = None
        for bi, (cs, ps) in enumerate(caixas):
            if len(cs) < 2:                 # nao da para dividir
                continue
            faixas = [max(c[i] for c in cs) - min(c[i] for c in cs)
                      for i in range(3)]
            canal = max(range(3), key=lambda i: faixas[i])
            ordem = sorted(range(len(cs)), key=lambda j: (cs[j][canal], cs[j]))
            escopo = (faixas[canal] + 1) * sum(ps)
            if melhor is None or escopo > melhor[0]:
                melhor = (escopo, bi, ordem)
        if melhor is None:                  # ja nao ha o que dividir
            break
        _, bi, ordem = melhor
        cs, ps = caixas.pop(bi)
        meio, acc, corte = sum(ps) / 2, 0, 0
        for pos, j in enumerate(ordem):
            acc += ps[j]
            if acc > meio:
                corte = pos + 1
                break
        corte = max(1, min(len(ordem) - 1, corte))
        esq, dir_ = ordem[:corte], ordem[corte:]
        caixas.append(([cs[j] for j in esq], [ps[j] for j in esq]))
        caixas.append(([cs[j] for j in dir_], [ps[j] for j in dir_]))

    pal = []
    for cs, ps in caixas:
        if PRETO in cs:
            # A caixa do preto vira (0,0,0) EXATO: o fundo da home e o
            # que a tela faz, e ele tem de ser uma entrada, nao um quase
            # preto que escurece o fundo em toda a tela.
            pal.append(PRETO)
            continue
        tot = sum(ps)
        pal.append(tuple(max(0, min(255, round(
            sum(c[i] * p for c, p in zip(cs, ps)) / tot))) for i in range(3)))
    while len(pal) < N_CORES_ICONE:         # so com PNG de poucas cores
        pal.append(PRETO)
    return pal, len(hist)


def monta_paleta(pal_icones):
    """As 256 entradas (r, g, b) da folha: 16 da barra + 240 dos icones."""
    return paleta_barra() + list(pal_icones)


def indice_mais_proximo(pal, cor, cache):
    """O indice da cor mais proxima de `cor` na paleta de 256 entradas.

    Metrica: distancia de Chebyshev (o maximo por canal), desempate pelo
    menor indice, para o resultado ser estavel entre execucoes. O cache
    existe porque o PNG tem 2974 cores distintas em 18432 pixels.
    """
    i = cache.get(cor)
    if i is not None:
        return i
    melhor, custo = 0, None
    for j, (r, g, b) in enumerate(pal):
        c = (max(abs(r - cor[0]), abs(g - cor[1]), abs(b - cor[2])), j)
        if custo is None or c < custo:
            melhor, custo = j, c
    cache[cor] = melhor
    return melhor


# ---------------------------------------------------------------------------
# premissas
# ---------------------------------------------------------------------------

def confere_sha(d, ini, tam, esperado, nome):
    got = hashlib.sha256(bytes(d[ini:ini + tam])).hexdigest()
    if got == esperado:
        return []
    return [f"{nome} 0x{ini:06X}..0x{ini + tam:06X} (sha256 {got[:16]}..., "
            f"esperado {esperado[:16]}...) — a regiao nao e a de fabrica"]


def confere_cabecalho(d):
    """O descritor INTEIRO, palavra por palavra — cf, always_zero, os bits
    reservados e a largura/altura embutidas, mais o data_size e o ponteiro
    XIP. Conferir so o cf deixaria passar um bit reservado aceso (achado
    001-R1)."""
    erros = []
    cab_pal, tam, ptr = struct.unpack_from("<3I", d, HOME_CAB)
    if cab_pal != HOME_CAB_FABRICA:
        erros.append(f"cabecalho 0x{HOME_CAB:06X} = 0x{cab_pal:08X}, esperado "
                     f"0x{HOME_CAB_FABRICA:08X} inteiro (cf, always_zero, "
                     f"reservados, {HOME_LARG}x{HOME_ALT})")
    if tam != HOME_TAM_FABRICA:
        erros.append(f"cabecalho 0x{HOME_CAB:06X}: data_size=0x{tam:X}, "
                     f"esperado 0x{HOME_TAM_FABRICA:X}")
    if ptr != HOME_PTR_FABRICA:
        erros.append(f"cabecalho 0x{HOME_CAB:06X}: ponteiro=0x{ptr:08X}, "
                     f"esperado 0x{HOME_PTR_FABRICA:08X}")
    return erros


def confere_premissas(d):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]

    erros = confere_cabecalho(d)
    erros += confere_sha(d, HOME_CAB, HOME_PX - HOME_CAB, HOME_CAB_PAL_SHA,
                         "cabecalho+paleta da folha")
    erros += confere_sha(d, HOME_PX + HOME_LARG * HOME_BARRA,
                         HOME_FIM - HOME_PX - HOME_LARG * HOME_BARRA,
                         HOME_ICONES_SHA, "as 144 linhas dos icones")

    # a barra: cada linha tem de ser UNIFORME. Vale tanto para o ORIGINAL
    # (as 16 linhas em indice 1, preto) quanto para a RC3 (uma cor por
    # linha). Nao exigimos nem o indice nem a cor: o que precisa estar
    # provado e que aquela faixa e a barra, e nao parte de um icone.
    for y in range(HOME_BARRA):
        ini = HOME_PX + HOME_LARG * y
        linha = bytes(d[ini:ini + HOME_LARG])
        if len(set(linha)) != 1:
            fora = sorted(set(linha))
            erros.append(f"a linha y={y} da barra (0x{ini:06X}..) tem "
                         f"{len(fora)} indices diferentes ({fora[:4]}) — a "
                         f"barra tem de ser uma cor so por linha")
    return erros


# ---------------------------------------------------------------------------
# a escrita
# ---------------------------------------------------------------------------

def blob_paleta(pal):
    """(r, g, b) x 256 -> 1024 bytes BGRA, alfa 255 nas 256."""
    b = bytearray()
    for r, g, bl in pal:
        b += bytes((bl, g, r, 255))
    return bytes(b)


def monta_pixels(pal, dados):
    """(128 x 160) de indices: a barra e uma rampa, os icones sao o mais
    proximo. Devolve (bytes, quantas cores distintas do PNG entraram)."""
    cache = {}
    px = bytearray(HOME_LARG * HOME_ALT)
    for y in range(HOME_BARRA):
        px[y * HOME_LARG:(y + 1) * HOME_LARG] = bytes([y]) * HOME_LARG
    for y in range(HOME_BARRA, HOME_ALT):
        for x in range(HOME_LARG):
            px[y * HOME_LARG + x] = indice_mais_proximo(
                pal, pixel(dados, x, y), cache)
    return bytes(px), len(cache)


def escreve(d, pal, dados):
    """A paleta e os pixels, e devolve (bytes de pixel escritas, cores do
    PNG distintas que entraram no mapa)."""
    d[HOME_PAL:HOME_PX] = blob_paleta(pal)
    px, usadas = monta_pixels(pal, dados)
    d[HOME_PX:HOME_FIM] = px
    return len(px), usadas


def confere_resultado(d, orig, dados):
    """Rele a paleta e os pixels do BINARIO (nao da montagem) e confere.

    Devolve (erros, erro medio por canal, erro maximo por canal).
    """
    erros = []
    if bytes(d[HOME_CAB:HOME_PAL]) != bytes(orig[HOME_CAB:HOME_PAL]):
        erros.append(f"o cabecalho em 0x{HOME_CAB:06X} foi tocado — ele e "
                     f"premissa, nao campo a preencher")
    if len(d[HOME_PAL:HOME_PX]) != HOME_PALETA:
        erros.append(f"a paleta tem {len(d[HOME_PAL:HOME_PX])} bytes, "
                     f"esperado {HOME_PALETA}")

    blob = bytes(d[HOME_PAL:HOME_PX])
    pal = [(blob[i * 4 + 2], blob[i * 4 + 1], blob[i * 4], blob[i * 4 + 3])
           for i in range(256)]

    # as 16 entradas da barra: a cor EXATA do degradê
    for y in range(HOME_BARRA):
        alvo = alvo_linha(y)
        if pal[y][:3] != alvo:
            erros.append(f"entrada {y} = RGB{pal[y][:3]}, esperado RGB{alvo} "
                         f"(a cor exata da linha {y})")
    alfa = {p[3] for p in pal}
    if alfa != {255}:
        erros.append(f"alfa {sorted(alfa)} na paleta, esperado 255 nas 256")

    px = bytes(d[HOME_PX:HOME_FIM])
    if len(px) != HOME_LARG * HOME_ALT:
        erros.append(f"os pixels tem {len(px)} bytes, esperado "
                     f"{HOME_LARG * HOME_ALT}")
        return erros, 0.0, 0

    # a barra: linha y toda indice y
    for y in range(HOME_BARRA):
        linha = px[y * HOME_LARG:(y + 1) * HOME_LARG]
        if set(linha) != {y}:
            erros.append(f"linha y={y} da barra = indices "
                         f"{sorted(set(linha))}, esperado so o {y}")

    # os icones: cada pixel tem de bater com o PNG, e o preto tem de cair
    # no preto exato
    soma, n, pior, pior_em, errados = 0, 0, 0, None, 0
    for y in range(HOME_BARRA, HOME_ALT):
        for x in range(HOME_LARG):
            i = px[y * HOME_LARG + x]
            c = pal[i][:3]
            ref = pixel(dados, x, y)
            if ref == PRETO and c != PRETO:
                errados += 1
            e = [abs(c[k] - ref[k]) for k in range(3)]
            if max(e) > pior:
                pior, pior_em = max(e), (x, y, c, ref)
            soma += sum(e)
            n += 3
    medio = soma / n if n else 0.0
    if errados:
        erros.append(f"{errados} pixel(s) (0,0,0) do PNG caem em uma "
                     f"entrada que nao e (0,0,0) — o fundo da home nao e "
                     f"preto")
    if medio > ERRO_MEDIO_MAX:
        erros.append(f"erro medio {medio:.2f} por canal > {ERRO_MEDIO_MAX}")
    if pior > ERRO_MAX:
        x, y, c, ref = pior_em
        erros.append(f"erro maximo {pior} em ({x},{y}): RGB{c} contra "
                     f"RGB{ref} no PNG (max {ERRO_MAX}) — um glifo apagado "
                     f"passaria so pela media")
    return erros, medio, pior


# ---------------------------------------------------------------------------
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
        description="RC4 item 2: os nove icones da home viram os do PNG")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--png", default=os.path.join(RAIZ, PNG_PADRAO),
                    help=f"PNG dos icones (padrao {PNG_PADRAO})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.src):
        print(f"RECUSADO: {a.src} nao existe.", file=sys.stderr)
        return 2
    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — RC4 item 2: os nove icones novos da home")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n  png    : {a.png}\n")

    # --- premissas, ANTES de qualquer escrita
    erros = confere_premissas(d)
    if erros:
        print("  RECUSADO — a entrada nao e a folha que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    try:
        dados = le_png(a.png)
    except ValueError as e:
        print(f"  RECUSADO — {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    print("  entrada conferida:")
    print("    - 2 MiB")
    print(f"    - cabecalho 0x{HOME_CAB:06X} (cf={HOME_CAB_FABRICA & 0xFFFF}, "
          f"data_size 0x{HOME_TAM_FABRICA:X}, ponteiro "
          f"0x{HOME_PTR_FABRICA:08X}) e paleta de fabrica")
    print(f"    - as {HOME_ALT - HOME_BARRA} linhas dos icones sao as de "
          f"fabrica")
    print(f"    - as {HOME_BARRA} linhas da barra sao uniformes (aceita "
          f"ORIGINAL e RC3)")
    print(f"    - o PNG tem o sha256 e o tamanho {HOME_LARG}x{HOME_ALT} "
          f"que a ficha fixou\n")

    pal_icones, distintas = quantiza(dados)
    pal = monta_paleta(pal_icones)
    if PRETO not in pal_icones:
        print("  RECUSADO — o PNG nao tem preto (0,0,0) exato; o fundo da "
              "home nao seria preto.")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    wrote, usadas = escreve(d, pal, dados)
    print(f"  PALETA  0x{HOME_PAL:06X}..0x{HOME_PX:06X}  (256 entradas BGRA, "
          f"alfa 255 nas 256)")
    print(f"    entradas  0..{HOME_BARRA - 1}   a cor EXATA de cada linha do "
          f"degradê, sem quantizar")
    for y in (0, 1, 7, 15):
        print(f"      linha {y:2d}  RGB{alvo_linha(y)}")
    print(f"    entradas {HOME_BARRA}..255  {len(pal_icones)} cores das "
          f"{distintas} do PNG (corte mediano, peso de populacao)")
    print(f"    preto (0,0,0) exato na entrada "
          f"{HOME_BARRA + pal_icones.index(PRETO)}")
    print(f"    cabecalho 0x{HOME_CAB:06X}..0x{HOME_PAL:06X} NAO tocado")
    print(f"\n  PIXELS  0x{HOME_PX:06X}..0x{HOME_FIM:06X}  ({wrote} bytes)")
    print(f"    linhas 0..{HOME_BARRA - 1}   toda a linha e o indice y "
          f"(a rampa da barra)")
    print(f"    linhas {HOME_BARRA}..{HOME_ALT - 1}   o indice da cor mais "
          f"proxima ({usadas} cores distintas do PNG)\n")

    erros, medio, pior = confere_resultado(d, orig, dados)
    if erros:
        print("  RECUSADO — a folha escrita nao passa na conferencia:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  conferencia (as 16 cores da barra, alfa 255, as 16 linhas "
          "uniformes,")
    print("    cabecalho intocado, preto do PNG indo para o preto "
          "exato): tudo OK")
    print(f"    erro contra o PNG: medio {medio:.2f} por canal (max "
          f"{ERRO_MEDIO_MAX}), maximo {pior} (max {ERRO_MAX})   OK\n")

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