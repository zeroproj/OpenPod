#!/usr/bin/env python3
"""
fab_home_moldura.py — a receita da Reload 1.0 RC6 (ficha 006): a home sem
os nomes, com a grade de icones centralizada e a moldura branca no icone
selecionado.

PROPOSITO

    Uma ferramenta so, aplicada sobre a RC5 (sha f9f2e059...). Ela faz tres
    coisas, e as tres cabem nos bytes que a ficha liberou:

      1. a GRADE: as tres faixas de icones da folha da home saem de baixo
         para o meio da tela, com espacamento igual;
      2. os NOMES: o texto dos nove rotulos da home vira a string vazia;
      3. a MOLDURA: o rotulo, que era o nome, passa a ser um retangulo de
         borda branca e cantos redondos em volta do icone selecionado — e
         essa moldura ANDA com a selecao, porque os oito pontos onde a
         fabrica mudava a cor do texto viraram "apaga a moldura" e "acende
         a moldura".

    A ideia e uma: o rotulo da home deixa de ser um TEXTO e passa a ser a
    MOLDURA do icone. Nao ha nome, e o desenho do icone e a selecao.

O QUE A FERRAMENTA NAO FAZ

    Nao mexe no tamanho dos icones, na navegacao, nas outras telas nem na
    tabela de textos (a da RC5 fica como esta). Nao usa nem copia
    patch_icones_home.py, patch_cor_selecao.py, patch_home_barra.py ou
    patch_menu_text.py: as tres ultimas nem existem mais na linha Reload, e
    a primeira e de uma RC anterior (ficha 004).

O COMO (medido no ORIGINAL, desmontado)

    A home e criada num laco de 9 itens em 0x00D2ECEE..0x00D2ED8E. Por item:

      - um `lv_img` SEM IMAGEM (0x00D5D850) na posicao (x,y) da tabela
        0x0004867C — o icone visivel vem da FOLHA de imagem, nao do objeto;
      - um rotulo (0x00D5E2E8) que recebe o TEXTO do id (0x00D2108C) e fica
        na posicao (x,y) da tabela 0x000486A0 (copiada para a pilha em
        0x00D2EC5E, e esta e a unica referencia ao literal).

    A selecao e a COR DO TEXTO do rotulo: a fabrica pinta de amarelo
    (0x00D57B48 com a paleta 0xC) o selecionado e volta a cor normal nos
    outros. Os oito `bl 0x00D4D10A` (a funcao que pinta a cor) sao:

        0x0012ED46  criacao — o rotulo nasce com a cor normal
        0x0012E9CA  navegacao — o item que PERDE a selecao
        0x0012EA26  navegacao — o item que PERDE a selecao
        0x0012EABA  navegacao — o item que PERDE a selecao
        0x0012EB12  navegacao — o item que PERDE a selecao
        0x0012EB4C  navegacao — o item que GANHA a selecao
        0x0012EDBC  criacao — o item inicial, que ja nasce selecionado

    E o `bl 0x00D2108C` da criacao (0x0012ED30) e o texto do rotulo.

    A ferramenta troca o ALVO dos oito `bl` (o `bl` e o gancho; a funcao e
    o contrato) e o alvo do nono. Em vez de pintar a cor do texto, as
    rotinas novas pintam a OPACIDADE DA BORDA do rotulo: apagada (0) quando
    o item nao esta selecionado, acesa (0xFF) quando esta. E o texto do
    rotulo passa a ser a string vazia, entao o rotulo fica com 35x35 de
    area e a borda e o que se ve.

AS ROTINAS NOVAS (lote 0x001A6400, 0x80 bytes)

    DESEL  0x00DA6400  borda apagada  (prop 0x31 = opacidade da borda, 0)
    SEL    0x00DA640A  borda acesa    (prop 0x31 = opacidade da borda, 0xFF)
    CRIA   0x00DA6414  prepares o rotulo: largura da borda 2 (prop 0x1032),
                       raio 8 (prop 0x60), cor branca (prop 0x30, 0xFFFF) e
                       devolve a string vazia (0x00DA6448)

    As tres chamam 0x00D4CAC4, a lv_obj_set_local_style_prop do firmware:
    (objeto, propriedade, valor, seletor) em r0..r3. Os ids das propriedades
    sao os dos wrappers de fabrica (0x00D4D0D6 = cor da borda, 0x00D4D0EA =
    opacidade, 0x00D4D0F8 = largura, 0x00D4D068 = raio).

    A CRIA usa o rotulo que ja esta em r6 (posto em 0x0012ED2C e nao
    mudado ate 0x0012ED38) e devolve o endereco da string vazia, que o
    chamador passa ao lv_label_set_text. O texto do nome some sem que a
    tabela de textos seja tocada (dano D6).

    A string vazia mora em 0x001A6448 (um byte 0x00) e o resto do lote fica
    em 0xFF, para que uma gravacao interrompida no meio do lote nao deixe
    codigo pela frente.

A GRADE (a folha da home)

    A folha e INDEXED_8, 128x160, com a paleta em 0x000CDD5C (256 entradas
    BGRA) e os pixels em 0x000CE15C. A paleta NAO e tocada: e so o indice
    dos pixels que muda.

    Na RC5 as faixas de icones (glifo de 31 px + sombra) estao em:

        faixa 1   linhas  16.. 49   (2 linhas de sombra acima nao ha: a 1a
                                      fileira e colada na barra)
        faixa 2   linhas  62.. 97   (2 linhas de sombra acima, 3 abaixo)
        faixa 3   linhas 110..145

    E a RC6 as move para 29..62, 70..105 e 114..149. As tres faixas sao
    COPIADAS como estao (so os indices dos pixels mudam de lugar); o resto
    das linhas 16..159 vira o indice preto da paleta. Os glifos passam a
    estar em y 29, 72 e 116, com vãos de 13, 12, 13 e 13 px entre a barra
    (y 16), as fileiras e o fim da tela.

    A paleta intocada e a folha movida sao as duas metades de uma imagem
    INDEXED_8: mexer so nos pixels e o que move o desenho sem trocar as
    cores.

OS ROTULOS VIRAM MOLDURAS

    A tabela de posicoes dos rotulos (0x000486A0) vira:

        (5,27) (46,27) (87,27)
        (5,70) (46,70) (87,70)
        (5,114) (46,114) (87,114)

    e o tamanho do rotulo (os dois `movs` de 0x0012ED5C e 0x0012ED5E) vira
    35x35 (era 40x15, o nome). 35 = 31 + 4: dois pixels de moldura de cada
    lado do glifo de 31 px. As posicoes sao as do glifo menos dois: o glifo
    da 1a fileira comeca em x 7 e o rotulo em x 5, e o glifo comeca em y 29
    e o rotulo em y 27.

PREMISSAS, conferidas ANTES de escrever qualquer byte

    A ficha pede recusa (D3) e nao aceitacao. Se UMA premissa falhar, a
    ferramenta sai com codigo diferente de zero, sem criar o arquivo de
    saida e sem tocar na entrada:

      - a imagem tem 2 MiB;
      - o sha256 da entrada e o da RC5 (f9f2e059...). A receita e a RC5
        mais esta ferramenta; qualquer outra imagem e recusada, mesmo que
        os enderecos existam;
      - cada um dos oito ganchos ainda decodifica para o alvo de fabrica
        (0x00D4D10A, e 0x00D2108C no nono);
      - os dois `movs` de tamanho sao os de fabrica (0x0F e 0x28);
      - a tabela de posicoes dos rotulos e a de fabrica;
      - a funcao de estilo 0x00D4CAC4 (0x40 bytes) e a de fabrica, presa
        por sha256: e ela que aplica a propriedade, e se mudar de forma a
        moldura sai errada sem nenhum erro visivel;
      - o lote 0x001A6400..0x001A6480 esta virgem (todo 0xFF);
      - a paleta da folha tem um preto exato (0,0,0,255), que e o fundo.

CONFERENCIA DE SAIDA

    A rotina e montada pelos encoders Thumb-2 daqui e conferida contra o
    literal de 72 bytes fixado abaixo. Se os dois discordarem, a ferramenta
    recusa: sao dois caminhos independentes para o mesmo codigo, e o
    disagreement e a pista de que um dos dois esta errado. O mesmo vale
    para cada `bl` de gancho.

    Depois, a ferramenta RELE o que escreveu e confere: o alvo dos oito
    ganchos, os 72 bytes da rotina, o 0x00 da string vazia e o 0xFF que vem
    depois dela, a tabela de posicoes, os dois bytes de tamanho, a folha
    (linha a linha, contra a conta da propria ferramenta), a paleta
    intocada, a funcao de estilo intacta e o resultado da busca por bytes
    escritos fora do permitido.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`, achado 001-R1). Sem
    isso, um link com outro nome passaria pela comparacao de caminho e a
    gravacao escreveria por cima da entrada.

    E so se escreve DENTRO de: 0x000486A0..0x000486C4 (a tabela), os oito
    ganchos (4 bytes cada), 0x0012ED5C..0x0012ED60 (o tamanho), o lote
    0x001A6400..0x001A6480 e 0x000CE95C..0x000D315C (as linhas 16..159 da
    folha). Qualquer byte fora disso e recusa, sem gravar.

USO

    python3 tools/fab_home_moldura.py --in <entrada.bin> --out <saida.bin>
                                       [--em 0x1a6400] [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib). Nao abre USB, nao grava no aparelho.

LIMITACOES

    - so serve na RC5 exata: qualquer outra imagem e recusada;
    - o nome dos icones da home some (e o que a ficha pede), mas o nome das
      OUTRAS telas continua: a tabela de textos da RC5 nao e tocada;
    - a moldura e branca e fixa (2 px, raio 8): nao ha cor por tema nem
      animacao;
    - a moldura depende do rotulo ter area: se o LVGL recusar o tamanho
      fixo de um rotulo com texto vazio, o resultado e um rotulo sem
      moldura — e o que o roteiro no aparelho tem de confirmar;
    - depois de aplicada, rodar de novo sobre a saida e recusado (o sha da
      entrada ja nao e o da RC5 e o lote ja nao esta virgem). E o
      comportamento correto: a ferramenta e feita para a receita, uma vez.
"""

import argparse
import hashlib
import os
import struct
import sys

XIP = 0x00C00000
TAMANHO = 0x200000                          # 2 MiB

# --- a entrada: a RC5 exata (catraca, rodando no aparelho em 2026-10-23)
SHA_ENTRADA = ("f9f2e05990adb5d3882bbf093a6251673139004571af7698f351"
               "4b02f1e08f50")

# --- a folha da home (INDEXED_8, 128x160)
HOME_PAL, HOME_PX = 0x0CDD5C, 0x0CE15C
HOME_LARG, HOME_ALT, HOME_BARRA = 128, 160, 16
HOME_PALETA = 256 * 4
# (topo antigo, altura, topo novo) das tres faixas de icones
FAIXAS = ((16, 34, 29), (62, 36, 70), (110, 36, 114))

# --- os rotulos da home viram as molduras
ROTULO_POS = 0x0486A0                       # 9 x (int16 x, int16 y)
ROTULO_TAM = 36
POS_FABRICA = [(3, 48), (44, 48), (86, 48),
                (3, 96), (44, 96), (86, 96),
                (3, 144), (44, 145), (86, 145)]
POS_NOVAS = [(x, y) for y in (27, 70, 114) for x in (5, 46, 87)]
TAM_ALTURA, TAM_LARGURA = 0x12ED5C, 0x12ED5E   # os dois `movs` de tamanho
TAM_FABRICA = {TAM_ALTURA: bytes.fromhex("0f22"),     # 40 x 15
               TAM_LARGURA: bytes.fromhex("2821")}
TAM_NOVO = {TAM_ALTURA: bytes.fromhex("2322"),        # 35 x 35
            TAM_LARGURA: bytes.fromhex("2321")}

# --- os nove ganchos: endereco -> (alvo de fabrica, alvo novo)
LOTE, LOTE_TAM = 0x1A6400, 0x80
DESEL, SEL, CRIA, VAZIO = 0xDA6400, 0xDA640A, 0xDA6414, 0xDA6448
TEXTO_ROTULO = 0xD2108C
COR_ROTULO = 0xD4D10A
GANCHOS = {
    0x12ED30: (TEXTO_ROTULO, CRIA),         # texto do rotulo -> "" (+ estilo)
    0x12ED46: (COR_ROTULO, DESEL),          # criacao: moldura apagada
    0x12E9CA: (COR_ROTULO, DESEL),          # navegacao: tira a selecao
    0x12EA26: (COR_ROTULO, DESEL),
    0x12EABA: (COR_ROTULO, DESEL),
    0x12EB12: (COR_ROTULO, DESEL),
    0x12EB4C: (COR_ROTULO, SEL),            # navegacao: da a selecao
    0x12EDBC: (COR_ROTULO, SEL),            # criacao: o item inicial
}

# --- o estilo
SET_PROP = 0x00D4CAC4                      # lv_obj_set_local_style_prop
SET_PROP_TAM = 0x40
SET_PROP_SHA = ("ebef9149b1c09faeb1ec452acdf99dac66066f8ba5dea064e6ade"
                "550c5b24a59")
PROP_BORDA_COR = 0x30                      # ids dos wrappers de fabrica
PROP_BORDA_OPA = 0x31
PROP_BORDA_LAR = 0x1032
PROP_RAIO = 0x60
LARG_BORDA, RAIO, BRANCO = 2, 8, 0xFFFF

EM_PADRAO = LOTE

# a rotina de 72 bytes, literal. Nao e a fonte da verdade — a fonte sao os
# encoders logo abaixo; e o outro caminho, para os dois discordarem juntos
# nunca passarem sem alarde.
ROTINA_LITERAL = bytes.fromhex(
    "3121" "0022" "0023" "a6f75dbb"                 # DESEL: borda apagada
    "3121" "ff22" "0023" "a6f758bb"                 # SEL:   borda acesa
    "10b5" "3046" "41f23201" "0222" "0023" "a6f750fb"   # CRIA: largura 2
    "3046" "6021" "0822" "0023" "a6f74afb"             #        raio 8
    "3046" "3021" "4ff6ff72" "0023" "a6f743fb"         #        branca
    "46f24840" "c0f2da00" "10bd"                      #        devolve ""
)

PERMITIDO = ([(ROTULO_POS, ROTULO_POS + ROTULO_TAM)]
             + [(a, a + 4) for a in sorted(GANCHOS)]
             + [(TAM_ALTURA, TAM_LARGURA + 2)]
             + [(LOTE, LOTE + LOTE_TAM)]
             + [(HOME_PX + HOME_LARG * HOME_BARRA,
                 HOME_PX + HOME_LARG * HOME_ALT)])


# ---------------------------------------------------------------------------
# Thumb-2. Os encoders vivem aqui porque o codigo e o objeto da RC: um
# literal opaco de 72 bytes nao deixa ninguem conferir nada.
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
    """endereco do salto -> endereco alvo -> 4 bytes (T1, sinal de 25 bits).

    hw1 = 11110 S imm10  |  hw2 = 11 J1 1 J2 imm11
    """
    off = para - (de + 4)
    if not -(1 << 24) <= off < (1 << 24):
        raise ValueError(f"0x{de:08X} -> 0x{para:08X} fora do alcance do bl")
    S = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = 1 - (i1 ^ S), 1 - (i2 ^ S)
    h1 = 0xF000 | (S << 10) | ((off >> 12) & 0x3FF)
    h2 = 0xD000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF)
    return struct.pack("<HH", h1, h2)


def enc_b(de, para):
    """`b.w` de 32 bits: o mesmo campo do `bl`, so mudam os dois bits que
    separam as duas instrucoes (10 J1 0 J2, em vez de 11 J1 1 J2).
    """
    off = para - (de + 4)
    if not -(1 << 24) <= off < (1 << 24):
        raise ValueError(f"0x{de:08X} -> 0x{para:08X} fora do alcance do b.w")
    S = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = 1 - (i1 ^ S), 1 - (i2 ^ S)
    h1 = 0xF000 | (S << 10) | ((off >> 12) & 0x3FF)
    h2 = 0x9000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF)
    return struct.pack("<HH", h1, h2)


def mov_reg(rd, rm):
    """`mov rd, rm` de 16 bits (registadores baixos)."""
    return struct.pack("<H", 0x4600 | (rm << 3) | rd)


def movs_imm(rd, imm8):
    """`movs rd, #imm8` de 16 bits."""
    return struct.pack("<H", 0x2000 | (rd << 8) | imm8)


def movw(rd, imm16):
    """`movw rd, #imm16` de 32 bits (T3).

    O imediato nao esta no campo dele na ordem do papel: o campo de 4 bits
    da primeira meia-palavra e imm16[15:12], o bit `i` e imm16[11], e os 3
    bits da segunda sao imm16[10:8]. Conferido contra os `movw` do firmware
    (2591 amostras), byte a byte.
    """
    h1 = 0xF240 | (((imm16 >> 11) & 1) << 10) | ((imm16 >> 12) & 0xF)
    h2 = (((imm16 >> 8) & 0x7) << 12) | (rd << 8) | (imm16 & 0xFF)
    return struct.pack("<HH", h1, h2)


def movt(rd, imm16):
    """`movt rd, #imm16` de 32 bits (T1). Mesmos campos do `movw`.

    So o que muda em relacao ao `movw` e a base da primeira meia-palavra
    (0xF2C0 em vez de 0xF240). Conferido contra os `movt` do firmware.
    """
    h1 = 0xF2C0 | (((imm16 >> 11) & 1) << 10) | ((imm16 >> 12) & 0xF)
    h2 = (((imm16 >> 8) & 0x7) << 12) | (rd << 8) | (imm16 & 0xFF)
    return struct.pack("<HH", h1, h2)


def monta_rotina():
    """Os 72 bytes da ficha, montados na ordem em que estao na lista."""
    base = XIP + LOTE
    b = bytearray()
    # DESEL: a borda apagada
    b += movs_imm(1, PROP_BORDA_OPA)
    b += movs_imm(2, 0)
    b += movs_imm(3, 0)
    b += enc_b(base + len(b), SET_PROP)
    # SEL: a borda acesa
    b += movs_imm(1, PROP_BORDA_OPA)
    b += movs_imm(2, 0xFF)
    b += movs_imm(3, 0)
    b += enc_b(base + len(b), SET_PROP)
    # CRIA: o estilo da moldura, e devolve a string vazia
    b += struct.pack("<H", 0xB510)            # push {r4, lr}
    b += mov_reg(0, 6)                        # mov   r0, r6  (o rotulo)
    b += movw(1, PROP_BORDA_LAR)
    b += movs_imm(2, LARG_BORDA)
    b += movs_imm(3, 0)
    b += enc_bl(base + len(b), SET_PROP)
    b += mov_reg(0, 6)
    b += movs_imm(1, PROP_RAIO)
    b += movs_imm(2, RAIO)
    b += movs_imm(3, 0)
    b += enc_bl(base + len(b), SET_PROP)
    b += mov_reg(0, 6)
    b += movs_imm(1, PROP_BORDA_COR)
    b += movw(2, BRANCO)
    b += movs_imm(3, 0)
    b += enc_bl(base + len(b), SET_PROP)
    b += movw(0, VAZIO & 0xFFFF)
    b += movt(0, (VAZIO >> 16) & 0xFFFF)
    b += struct.pack("<H", 0xBD10)            # pop  {r4, pc}
    return bytes(b)


# ---------------------------------------------------------------------------
# a folha: a grade centralizada
# ---------------------------------------------------------------------------

def indice_preto(pal):
    """O indice da paleta que e o preto exato (0,0,0,255)."""
    achados = [i for i in range(256)
               if pal[i * 4:i * 4 + 3] == b"\0\0\0" and pal[i * 4 + 3] == 255]
    if not achados:
        raise ValueError("a paleta da folha nao tem um preto exato (0,0,0,255)")
    return achados[0]


def folha_nova(px, pal):
    """A folha da RC6: as faixas movidas, o resto preto, a paleta intocada.

    Devolve (bytes da folha nova, indice do preto).
    """
    k = indice_preto(pal)
    velho = bytes(px)
    novo = bytearray(velho)
    for y in range(HOME_BARRA, HOME_ALT):
        novo[HOME_LARG * y:HOME_LARG * (y + 1)] = bytes([k]) * HOME_LARG
    for antigo, altura, novo_topo in FAIXAS:
        novo[HOME_LARG * novo_topo:HOME_LARG * (novo_topo + altura)] = \
            velho[HOME_LARG * antigo:HOME_LARG * (antigo + altura)]
    return bytes(novo), k


# ---------------------------------------------------------------------------
# premissas
# ---------------------------------------------------------------------------

def confere_sha(d, ini, tam, esperado, nome):
    got = hashlib.sha256(bytes(d[ini:ini + tam])).hexdigest()
    if got == esperado:
        return []
    return [f"{nome} 0x{ini:06X}..0x{ini + tam:06X} (sha256 {got[:16]}..., "
            f"esperado {esperado[:16]}...) — a regiao nao e a de fabrica"]


def confere_lote(d, ini, tam, nome):
    erros = []
    ocupado = [i for i in range(ini, ini + tam) if d[i] != 0xFF]
    if ocupado:
        erros.append(f"{nome} 0x{ini:06X}..0x{ini + tam:06X}: "
                     f"{len(ocupado)} byte(s) fora do 0xFF, o primeiro em "
                     f"0x{ocupado[0]:06X} — o lote tem de estar virgem")
    return erros


def confere_premissas(d):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]

    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != SHA_ENTRADA:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                    f"{SHA_ENTRADA[:16]}... — a receita e a RC5 mais esta "
                    f"ferramenta, e so a RC5 entra")

    for a in sorted(GANCHOS):
        alvo = bl_alvo(d, a)
        fab, _ = GANCHOS[a]
        if alvo != fab:
            erros.append(f"0x{a:06X} chama "
                         f"{'nada' if alvo is None else f'0x{alvo:08X}'}, "
                         f"esperado 0x{fab:08X} (o gancho de fabrica)")

    for a, fab in TAM_FABRICA.items():
        if bytes(d[a:a + 2]) != fab:
            erros.append(f"o tamanho em 0x{a:06X} e "
                         f"{bytes(d[a:a + 2]).hex()}, esperado {fab.hex()} "
                         f"(o `movs` de fabrica)")

    pos = [struct.unpack_from("<hh", d, ROTULO_POS + 4 * i) for i in range(9)]
    if pos != POS_FABRICA:
        erros.append(f"a tabela de posicoes dos rotulos (0x{ROTULO_POS:06X}) "
                     f"e {pos}, esperada {POS_FABRICA} (a de fabrica)")

    erros += confere_sha(d, SET_PROP - XIP, SET_PROP_TAM, SET_PROP_SHA,
                         "lv_obj_set_local_style_prop")
    erros += confere_lote(d, LOTE, LOTE_TAM, "lote das rotinas")

    pal = bytes(d[HOME_PAL:HOME_PX])
    if len(pal) != HOME_PALETA:
        erros.append(f"a paleta da folha tem {len(pal)} bytes, esperado "
                     f"{HOME_PALETA}")
    else:
        try:
            indice_preto(pal)
        except ValueError as e:
            erros.append(str(e))
    return erros


# ---------------------------------------------------------------------------
# a escrita
# ---------------------------------------------------------------------------

def escreve(d):
    """A folha, a tabela, o tamanho, os ganchos e o lote. Devolve um relatorio."""
    rel = {}

    # 1. a grade: as faixas movidas, o resto preto
    pal = bytes(d[HOME_PAL:HOME_PX])
    px, k = folha_nova(d[HOME_PX:HOME_PX + HOME_LARG * HOME_ALT], pal)
    d[HOME_PX:HOME_PX + HOME_LARG * HOME_ALT] = px
    rel["preto"] = k

    # 2. as posicoes dos rotulos (a moldura)
    blob = bytearray()
    for x, y in POS_NOVAS:
        blob += struct.pack("<hh", x, y)
    d[ROTULO_POS:ROTULO_POS + ROTULO_TAM] = bytes(blob)

    # 3. o tamanho do rotulo: 35 x 35
    for a, novo in TAM_NOVO.items():
        d[a:a + 2] = novo

    # 4. os nove ganchos
    for a, (_, novo) in sorted(GANCHOS.items()):
        d[a:a + 4] = enc_bl(XIP + a, novo)

    # 5. as rotinas
    rotina = monta_rotina()
    if rotina != ROTINA_LITERAL:
        raise ValueError("os encoders e o literal de 72 bytes discordam:\n"
                         f"    encoders: {rotina.hex()}\n"
                         f"    literal : {ROTINA_LITERAL.hex()}")
    if len(rotina) > LOTE_TAM:
        raise ValueError(f"a rotina tem {len(rotina)} bytes e o lote "
                         f"{LOTE_TAM}")
    if VAZIO != XIP + LOTE + len(rotina):
        raise ValueError(f"a string vazia esta em 0x{XIP + LOTE + len(rotina):08X}"
                         f" e a ficha fixa 0x{VAZIO:08X}")
    d[LOTE:LOTE + LOTE_TAM] = rotina + b"\xFF" * (LOTE_TAM - len(rotina))
    # o byte da string vazia: um 0x00 logo depois da rotina
    d[LOTE + len(rotina)] = 0x00
    rel["rotina"] = rotina
    return rel


def confere_resultado(d, orig, rotina):
    """Relê o que foi escrito e confere, sem confiar na montagem."""
    erros = []
    for a, (_, novo) in sorted(GANCHOS.items()):
        alvo = bl_alvo(d, a)
        if alvo != novo:
            erros.append(f"0x{a:06X} aponta para "
                         f"{'nada' if alvo is None else f'0x{alvo:08X}'}, "
                         f"esperado 0x{novo:08X}")
    if bytes(d[LOTE:LOTE + len(rotina)]) != ROTINA_LITERAL:
        erros.append(f"a rotina em 0x{LOTE:06X} nao e a da ficha")
    if any(x != 0xFF for x in d[LOTE + len(rotina) + 1:LOTE + LOTE_TAM]):
        erros.append(f"lixo depois da string vazia, em "
                     f"0x{LOTE + len(rotina) + 1:06X}..")
    pos = [struct.unpack_from("<hh", d, ROTULO_POS + 4 * i) for i in range(9)]
    if pos != POS_NOVAS:
        erros.append(f"a tabela de posicoes dos rotulos ficou {pos}, "
                     f"esperado {POS_NOVAS}")
    for a, novo in TAM_NOVO.items():
        if bytes(d[a:a + 2]) != novo:
            erros.append(f"o tamanho em 0x{a:06X} nao ficou {novo.hex()}")
    if bytes(d[HOME_PAL:HOME_PX]) != bytes(orig[HOME_PAL:HOME_PX]):
        erros.append("a paleta da folha mudou — ela nao pode ser tocada")
    erros += confere_sha(d, SET_PROP - XIP, SET_PROP_TAM, SET_PROP_SHA,
                         "lv_obj_set_local_style_prop")

    # a folha: a conta da propria ferramenta, lida do binario
    pal = bytes(orig[HOME_PAL:HOME_PX])
    esperado, k = folha_nova(orig[HOME_PX:HOME_PX + HOME_LARG * HOME_ALT], pal)
    if bytes(d[HOME_PX:HOME_PX + HOME_LARG * HOME_ALT]) != esperado:
        erros.append("a folha nao ficou como a conta das faixas diz")
    # as linhas que NAO estao em nenhuma faixa tem de ficar no indice preto
    nas_faixas = set()
    for _, altura, topo in FAIXAS:
        nas_faixas |= set(range(topo, topo + altura))
    for y in range(HOME_BARRA, HOME_ALT):
        if y in nas_faixas:
            continue
        ini = HOME_PX + HOME_LARG * y
        linha = bytes(d[ini:ini + HOME_LARG])
        if set(linha) != {k}:
            erros.append(f"a linha y={y} da folha nao ficou no indice "
                         f"preto {k}")
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
        description="RC6: a home sem nomes, com a grade centralizada e a "
                    "moldura branca no icone selecionado")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", default=None,
                    help=f"endereco do lote (tem de ser {EM_PADRAO:#x})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.em is not None:
        try:
            em = int(a.em, 0)
        except ValueError:
            print(f"RECUSADO: --em {a.em!r} nao e um endereco.", file=sys.stderr)
            return 2
        if em != EM_PADRAO:
            print(f"RECUSADO: --em {em:#x}; o lote desta ferramenta esta "
                  f"em {EM_PADRAO:#x}, e o MAPA do build.py declara esse.",
                  file=sys.stderr)
            return 2

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
    print("OpenPod — RC6: a home sem nomes, grade centralizada e moldura")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    # --- premissas, ANTES de qualquer escrita
    erros = confere_premissas(d)
    if erros:
        print("  RECUSADO — a entrada nao e a RC5 que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print("    - 2 MiB")
    print(f"    - sha256 {SHA_ENTRADA[:16]}... (a RC5)")
    print(f"    - os {len(GANCHOS)} ganchos ainda chamam o alvo de fabrica")
    print("    - os dois `movs` de tamanho sao os de fabrica (40 x 15)")
    print("    - a tabela de posicoes dos rotulos e a de fabrica")
    print(f"    - 0x{SET_PROP:08X} (0x40 bytes) intacta")
    print(f"    - lote 0x{LOTE:06X}..0x{LOTE + LOTE_TAM:06X} virgem")
    print("    - a paleta da folha tem o preto exato\n")

    try:
        rel = escreve(d)
    except ValueError as e:
        print(f"  RECUSADO — {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    rotina = rel["rotina"]

    print("  GRADE — a folha 128x160 (so os indices dos pixels mudam)")
    print(f"    pixels  0x{HOME_PX:06X}..0x{HOME_PX + HOME_LARG * HOME_ALT:06X}"
          f"  (linhas {HOME_BARRA}..{HOME_ALT - 1})")
    print(f"    paleta  0x{HOME_PAL:06X}..0x{HOME_PX:06X}  NAO tocada")
    print(f"    fundo das linhas soltas: indice {rel['preto']} (preto exato)")
    print("      faixa 1   linhas  16.. 49  ->  29.. 62   glifo em y 29")
    print("      faixa 2   linhas  62.. 97  ->  70..105   glifo em y 72")
    print("      faixa 3   linhas 110..145  -> 114..149   glifo em y 116")
    print("      vaos: 13 (barra), 12, 13, 13 (fim da tela)\n")

    print("  ROTULOS — viram molduras")
    print(f"    posicoes 0x{ROTULO_POS:06X}..0x{ROTULO_POS + ROTULO_TAM:06X}:")
    for i, (x, y) in enumerate(POS_NOVAS):
        print(f"      {i}  ({x:3d},{y:3d})")
    print(f"    tamanho  0x{TAM_ALTURA:06X} e 0x{TAM_LARGURA:06X}: "
          f"40 x 15 -> 35 x 35 (2 px de cada lado do glifo de 31)\n")

    print(f"  ROTINAS — lote 0x{LOTE:06X}..0x{LOTE + LOTE_TAM:06X}")
    print(f"    DESEL 0x{DESEL:08X}  borda apagada (opacidade 0)")
    print(f"    SEL   0x{SEL:08X}  borda acesa   (opacidade 0xFF)")
    print(f"    CRIA  0x{CRIA:08X}  largura {LARG_BORDA}, raio {RAIO}, branca; "
          f"devolve a string vazia 0x{VAZIO:08X}")
    print(f"    {len(rotina)} bytes, o resto do lote em 0xFF\n")

    print("  GANCHOS")
    for end, (fab, novo) in sorted(GANCHOS.items()):
        print(f"    0x{end:06X}  bl 0x{fab:08X} -> 0x{novo:08X}")

    erros = confere_resultado(d, orig, rotina)
    if erros:
        print("\n  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("\n  conferencia (alvos dos ganchos lidos de volta, 72 bytes da "
          "rotina,")
    print("    o 0x00 da string vazia e o 0xFF depois dela, a tabela, o "
          "tamanho,")
    print("    a folha linha a linha, a paleta e a funcao de estilo): tudo OK")

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
