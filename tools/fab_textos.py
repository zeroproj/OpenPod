#!/usr/bin/env python3
"""
fab_textos.py — ficha 005 (Reload 1.0 RC5): os textos em portugues revisados
e os nomes curtos da home.

PROPOSITO

    Os 180 textos em portugues que aparecem em qualquer tela do aparelho estao
    numa unica tabela: 216 ponteiros XIP em `0x053B84`, o idioma 8. A RC5 troca
    o texto de 180 desses 216 ids pelo conteudo revisado de
    `assets/textos_pt.tsv` — inclusive os oito rotulos da home, que passam a
    caber nos 40 px do rotulo sem corte nem rolagem.

    A troca e feita de dois jeitos ao mesmo tempo:

      - as strings novas saem gravadas num LOTE VIRGEM, 0x001A5000..0x001A6000
        (4 KiB de 0xFF no fim da area livre), em UTF-8, cada uma com o NUL;
      - a entrada da tabela de CADA id da lista passa a apontar para a string
        dele dentro do lote.

    NENHUMA string de fabrica e editada no lugar. Isso nao e preciosismo: em
    fabrica tres strings sao COMPARTILHADAS por dois ids cada, e em cada um
    desses pares o parceiro esta FORA da lista (0x00C54440 e dos ids 40 e 90,
    0x00C547E0 dos ids 78 e 155, 0x00C550B4 dos ids 9 e 29). Editar no lugar
    mudaria um id que a ficha manda deixar como esta — inclusive o id 40, que
    e o "Atualizar por SD" da RC1.

COMO O APARELHO CHEGA NO TEXTO (ficha 005, secao Evidencia)

    0x00D2108C(id)    devolve o texto: o idioma vem de 0x00D0E2B8 (0..8, `tbb`)
                     e o portugues e o 8;
    0x053B84          a tabela do portugues: 216 ponteiros XIP, 4 bytes cada;
    0x121104          o literal que diz qual e essa tabela (0x00C53B84).

    Conferido na desmontagem: id 1 "Música", id 3 "vídeo", id 8 "Ver pastas".
    O que falta para o texto aparecer em um `lv_label` e um NUL depois dos
    ultimos bytes — por isso o NUL vai junto no lote.

A FONTE (por que "tem glifo" e premissa, e nao detail)

    cmap: 7098 `u16` em `0x0A27E6` (caractere -> indice do glifo);
    avanco do glifo: `u32` em `0x086C44 + g * 16 + 4`.

    Um caractere sem glifo desenharia um quadrado ou sumiria o texto (dano D2).
    A ferramenta confere os dois campos da fonte contra o sha256 do ORIGINAL
    antes de medir largura alguma: medir largura com uma fonte adulterada daria
    um numero bonito e falso.

O LOTE

    0x001A5000..0x001A6000   4 KiB, virgens (todo 0xFF) na RC4

    2799 bytes das 180 strings novas ocupam 0x0AEF do lote; o resto fica em
    0xFF. As entradas da tabela que mudam sao as dos ids da lista, 4 bytes
    cada em `0x053B84 + 4 * id` — nada mais. Dano D6 (outro idioma afetado) e
    impossible por construcao: so a tabela 8 e reescrita.

PREMISSAS, conferidas ANTES de escrever qualquer byte

    Se UMA premissa falhar, a ferramenta sai com codigo diferente de zero, sem
    criar o arquivo de saida e sem tocar na entrada. Todas as premissas sao
    rodadas e todas as falhas sao mostradas juntas — quem recebe o "RECUSADO"
    precisa saber tudo que esta errado, nao so a primeira coisa.

    Na imagem:

      - 2 MiB;
      - sha256 da entrada = a RC4 exata, `74e8cb31...`. E o teste que decide:
        a revisao R0 da ficha mostrou que a RC1, a RC2 e a RC3 passariam em
        TODAS as outras premissas deste arquivo (elas nao repontaram tabela
        nenhuma), e uma delas passaria — a RC4 e que nao pode;
      - o literal 0x121104 aponta para 0x00C53B84;
      - a tabela, com os dois ponteiros da RC1 (ids 40 e 91) restoredos para
        fabrica, tem o sha256 da tabela de fabrica. Uma comparacao so do sha
        diria "a tabela mudou" sem dizer o que; por isso os dois ids da RC1
        sao conferidos a parte, nomeados;
      - os ids 40 e 91 apontam para os ponteiros da RC1 (0x00DA324C e
        0x00DA3260, dentro da area livre, diferentes dos de fabrica);
      - o lote 0x001A5000..0x001A6000 esta virgem;
      - o cmap e a tabela de avancos sao os de fabrica (sha256);
      - cada id da lista aponta para uma string terminada em NUL dentro da
        imagem, e aponta para fora do lote.

    Na lista de textos (`--textos`):

      - o arquivo tem o sha256 que a ficha fixou. Um `.tsv` mudado asimetrico
        (uma palavra a mais, um acento a menos) entraria no aparelho sem ninguem
        ver, e e o que o `--textos` existe para evitar;
      - todo id esta em 0..215, nenhum e 40 ou 91 (os da RC1) e nenhum
        repete;
      - todo caractere tem glifo;
      - os especificadores `%` sao os mesmos da string de fabrica. Divergir
        aqui e o dano D1: o `printf` do aparelho le os argumentos na ordem da
        fabrica e um `%d` virando `%s` le lixo (ou trava);
      - os oito rotulos da home estao na lista e medem no maximo 40 px;
      - cada linha nova mede no maximo 113 px OU nao e mais larga que a da
        fabrica. O 113 px e o limite do widget de duas linhas; os avisos longos
        de fabrica ja o estouram e o aparelho os quebra — o texto novo nunca
        pode ser o pior caso;
      - as 180 strings somam no maximo 4096 bytes (o tamanho do lote).

    `--em`, se vier, tem de ser o endereco que o MAPA do `build.py` declara.

CONFERENCIA DE SAIDA

    Apos escrever, a ferramenta RELE o binario — sem confiar na montagem — e
    confere: as entradas da tabela, cada ponteiro com a string certa e o NUL,
    o resto do lote em 0xFF, os 36 ids fora da lista com a entrada que tinham,
    as strings de fabrica intactas e nenhum byte alterado fora do permitido.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo caminho,
    symlink ou hardlink (`os.path.samefile`, achado 001-R1). Sem isso, um link
    com outro nome passaria pela comparacao de caminho e a gravacao escreveria
    por cima da entrada.

    E so se escreve DENTRO do lote e nos 4 bytes de entrada de cada id da
    lista. Qualquer byte fora disso e recusa, sem gravar.

    Rodar duas vezes e recusado — pela premissa do sha256, que e o mecanismo
    certo: a saida nao e a RC4.

O QUE ESTA FERRAMENTA NAO E

    Nao e a ferramenta antiga de texto, a que reescrevia a tabela de fabrica e
    as strings dela no lugar. Aquela nao serve aqui por dois motivos medidos:
    em fabrica tres strings sao compartilhadas por dois ids (o cabecalho diz
    quais), e a tabela de fabrica emenda direto na do espanhol, sem folga para
    crescer. Mover a tabela para a area livre resolve o segundo e desfaz o
    primeiro — e ainda mexe na entrada dos ids 40 e 91, que sao da RC1. Aqui a
    tabela fica onde esta: so as entradas dos ids da lista mudam de valor, e o
    resto da flash e byte a byte igual ao da RC4.

USO

    python3 tools/fab_textos.py --in <entrada.bin> --out <saida.bin>
                                [--textos assets/textos_pt.tsv]
                                [--em 0x1a5000] [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib). Nao abre USB, nao grava no aparelho.

LIMITACOES

    - so serve na imagem que a ficha mediu: a RC4 exata. Qualquer outra e
      recusada, mesmo que os enderecos existam;
    - a lista e conferida por sha256, entao uma correcao de traducao nova e
      uma mudanca de codigo (nova RC, novo sha). E o custo de trocar o
      conteudo por texto sem olhar para o aparelho;
    - a largura e medida com a fonte dos MENUS (`0x086C44`/`0x0A27E6`), que e
      a fonte que a ficha mediu. Rotulo que use outra fonte pode ter outra
      largura; a checagem cobre os 40 px da home e o widget de 113 px das
      telas, que e onde o dano D5 aparece;
    - nao confere se o texto novo combina com o CONTEXTO (uma frase curta no
      lugar de uma longa pode soar estranha). Isso e o roteiro no aparelho, nao
      a ferramenta: ela prova que o texto cabe, nao que ele le bem;
    - depois de aplicada, rodar de novo sobre a saida e recusado. E o
      comportamento correto: a ferramenta e feita para a receita, uma vez.
"""

import argparse
import hashlib
import os
import re
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XIP = 0x00C00000
TAMANHO = 0x200000                          # 2 MiB

# --- a imagem que a ficha mediu
SHA_RC4 = "74e8cb315958b053f9e36e366a32f103ba995f7a18316c1c01e3de89e3f3b6d4"

# --- a tabela do portugues (idioma 8, 0x00D2108C)
TABELA_PT = 0x053B84                         # 216 ponteiros XIP de 4 bytes
N_TEXTOS = 216
TABELA_PT_FIM = TABELA_PT + 4 * N_TEXTOS     # 0x053EE4
LITERAL = 0x121104                           # o literal que aponta para ela
TABELA_XIP = 0x00C53B84
PT_SHA_FABRICA = "d61e7d3fde00fb1250e37ae0cebf6433c86e265dca36e59605c0dd289af038fc"
RC1_IDS = (40, 91)
PT_RC1 = (0x00DA324C, 0x00DA3260)            # "Atualizar por SD" (RC1)
PT_FABRICA_RC1 = (0x00C54440, 0x00C548A6)    # o que a RC1 substituiu

# --- o lote dos textos novos
LOTE, LOTE_TAM = 0x001A5000, 0x1000
EM_PADRAO = LOTE

# --- a fonte dos menus
CMAP, N_GLIFOS = 0x0A27E6, 7098
CMAP_SHA = "0aaa803a38fe762bf237a227a4ecf3858584bcd2a3222768e3ab9eca6a537234"
AVANCO, PASSO_GLIFO = 0x086C44, 16          # o `u32` do avanco e em +4
AVANCO_SHA = "637a51ae9a6e0c056e05805e6506b03f011f5d7767c4e816781821742de711b4"

# --- a lista de textos
TEXTOS_PADRAO = "assets/textos_pt.tsv"
SHA_TEXTOS = "c9cc64bda98520f0e690ef746a6efad156ef3f39804186c06a0673884c1ad2e2"

# --- os limites do aparelho
HOME_IDS = (1, 2, 3, 4, 5, 8, 9, 10)        # rotulos da home: 40 px
HOME_LARGURA = 40
LARGURA_LIMITE = 113                        # o widget de duas linhas
FORMATO = re.compile(r"%[-+ #0]*\d*(?:\.\d+)?[a-zA-Z%]")

# bytes que a ficha permite escrever: o lote e as 4 entradas da tabela de cada
# id da lista (montado em `permitido()`)
PERMITIDO_LOTE = (LOTE, LOTE + LOTE_TAM)


# ---------------------------------------------------------------------------
# leitura
# ---------------------------------------------------------------------------

def ponteiro(d, i):
    """O ponteiro XIP da entrada `i` da tabela do portugues."""
    return struct.unpack_from("<I", d, TABELA_PT + 4 * i)[0]


def string_no(d, p):
    """Os bytes da string XIP `p`, do ponteiro ate o NUL. None se nao ha NUL.

    None e o dano D3: o aparelho le a string pelo ponteiro e anda ate achar o
    NUL. Um ponteiro errado sem NUL adiante nao da nem para recusar — ele le a
    flash inteira e mostra lixo.
    """
    if not XIP <= p < XIP + len(d):
        return None
    ini = p - XIP
    fim = d.find(b"\0", ini)
    return None if fim < 0 else bytes(d[ini:fim])


def texto_de_fabrica(d, i):
    """A string de fabrica do id `i` lida da propria imagem, ou None.

    A premissa do sha256 garante que a imagem de entrada E a RC4, e a RC1 a
    RC4 nao mexeram em nenhuma string de fabrica. Logo, a string que esta no
    ponteiro de fabrica da propria entrada e a de fabrica — e nao ha motivo
    para levar o ORIGINAL inteiro para dentro da ferramenta so por causa dela.
    """
    b = string_no(d, ponteiro(d, i))
    if b is None:
        return None
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return None


def cmap_de(d):
    """{caractere: indice do glifo}, do cmap da imagem."""
    return {c: g for g, c in
            enumerate(struct.unpack_from("<%dH" % N_GLIFOS, d, CMAP))}


def largura_px(d, cmap, t):
    """A largura de `t` em pixels, pela tabela de avancos. None sem glifo.

    O `\\n` nao conta: e quebra de linha, nao um glifo. O aparelho mede a
    largura do texto com a string inteira, e o caractere de quebra e o que
    separa as linhas do widget.
    """
    total = 0
    for c in t:
        if c == "\n":
            continue
        g = cmap.get(ord(c))
        if g is None:
            return None
        total += struct.unpack_from("<I", d, AVANCO + g * PASSO_GLIFO + 4)[0]
    return total


def maior_linha_px(d, cmap, t):
    """A maior LINHA de `t`: o que o widget tem de caber, nao a frase toda.

    O `%%` e um `%` para quem le, entao conta uma vez so.
    """
    return max(largura_px(d, cmap, x) or 0
               for x in t.replace("%%", "%").split("\n"))


# ---------------------------------------------------------------------------
# a lista de textos
# ---------------------------------------------------------------------------

def le_textos(caminho):
    """Le o `.tsv` e devolve {id: texto}, ja com `\\n` virado quebra de linha.

    Levanta ValueError com a mensagem da recusa: o sha, o id fora de faixa, o
    id da RC1 e o id repetido sao as quatro coisas que a ficha manda recusar,
    e cada uma delas tem de dizer ONDE esta o problema.
    """
    try:
        bruto = open(caminho, "rb").read()
    except OSError as e:
        raise ValueError(f"{caminho}: {e.strerror}")
    sha = hashlib.sha256(bruto).hexdigest()
    if sha != SHA_TEXTOS:
        raise ValueError(f"{caminho} tem sha256 {sha}\n         "
                         f"a ficha fixa {SHA_TEXTOS}")
    try:
        linhas = bruto.decode("utf-8").splitlines()
    except UnicodeDecodeError as e:
        raise ValueError(f"{caminho} nao e UTF-8: {e}")

    textos = {}
    for n, linha in enumerate(linhas, 1):
        if not linha.strip() or linha.startswith("#"):
            continue
        if "\t" not in linha:
            raise ValueError(f"linha {n} sem TAB (id<TAB>texto): {linha!r}")
        i_txt, texto = linha.split("\t", 1)
        try:
            i = int(i_txt)
        except ValueError:
            raise ValueError(f"linha {n}: {i_txt!r} nao e um id")
        if not 0 <= i < N_TEXTOS:
            raise ValueError(f"linha {n}: id {i} fora de 0..{N_TEXTOS - 1} "
                             f"(a tabela tem {N_TEXTOS} entradas)")
        if i in RC1_IDS:
            raise ValueError(f"linha {n}: id {i} e da RC1 ('Atualizar por "
                             f"SD'); a RC5 nao mexe nele")
        if i in textos:
            raise ValueError(f"linha {n}: id {i} repetido (ja na linha "
                             f"{textos[i][0]})")
        textos[i] = (n, texto.replace("\\n", "\n"))
    if not textos:
        raise ValueError(f"{caminho} nao tem nenhum id")
    return {i: t for i, (_, t) in textos.items()}


# ---------------------------------------------------------------------------
# premissas
# ---------------------------------------------------------------------------

def confere_sha(d, ini, tam, esperado, nome):
    """sha256 de uma regiao, com o endereco e o tamanho na mensagem.

    Colar os bytes no fonte seria ruido — 4 KiB de cmap e 113 KiB de tabela de
    avancos — e o sha diz a mesma coisa sem chance de erro de digito.
    """
    if ini + tam > len(d):
        return [f"{nome} 0x{ini:06X}..0x{ini + tam:06X} esta fora da imagem "
                f"(ela tem {len(d)} bytes)"]
    got = hashlib.sha256(bytes(d[ini:ini + tam])).hexdigest()
    if got == esperado:
        return []
    return [f"{nome} 0x{ini:06X}..0x{ini + tam:06X} (sha256 {got[:16]}..., "
            f"esperado {esperado[:16]}...) — a regiao nao e a de fabrica"]


def confere_lote(d, ini, tam, nome):
    """O lote tem de estar virgem: todo 0xFF."""
    ocupado = [i for i in range(ini, ini + tam) if d[i] != 0xFF]
    if ocupado:
        return [f"{nome} 0x{ini:06X}..0x{ini + tam:06X}: {len(ocupado)} "
                f"byte(s) fora do 0xFF, o primeiro em 0x{ocupado[0]:06X} — o "
                f"lote tem de estar virgem"]
    return []


def confere_premissas(d, textos):
    """TODAS as premissas da ficha NA IMAGEM. Devolve a lista de erros.

    Todas sao rodadas e todas as falhas voltam juntas: quem receber o
    "RECUSADO" precisa saber tudo que esta errado. O sha256 vem primeiro
    porque e o teste que decide — a revisao R0 da ficha mostrou que a RC1, a
    RC2 e a RC3 passam em todas as outras.
    """
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]

    erros = []
    got = hashlib.sha256(bytes(d)).hexdigest()
    if got != SHA_RC4:
        erros.append(
            f"o sha256 da entrada e {got}\n"
            f"      a ficha fixa a RC4 exata, {SHA_RC4}\n"
            f"      esta ferramenta roda uma vez, sobre a RC4 — nem duas "
            f"vezes, nem sobre a RC3, nem sobre o ORIGINAL")

    # o literal que diz qual e a tabela
    lit = struct.unpack_from("<I", d, LITERAL)[0]
    if lit != TABELA_XIP:
        erros.append(f"o literal 0x{LITERAL:06X} = 0x{lit:08X}, esperado "
                     f"0x{TABELA_XIP:08X} (a tabela do portugues)")

    # a tabela, com os dois ids da RC1 restoredos para fabrica
    tab = bytearray(d[TABELA_PT:TABELA_PT_FIM])
    if len(tab) == TABELA_PT_FIM - TABELA_PT:
        for k, i in enumerate(RC1_IDS):
            tab[4 * i:4 * i + 4] = struct.pack("<I", PT_FABRICA_RC1[k])
        got = hashlib.sha256(bytes(tab)).hexdigest()
        if got != PT_SHA_FABRICA:
            erros.append(
                f"a tabela 0x{TABELA_PT:06X}..0x{TABELA_PT_FIM:06X}, com os "
                f"ids 40 e 91 de volta para fabrica, tem sha256 {got}\n"
                f"      esperado {PT_SHA_FABRICA}: algum id aponta para um "
                f"lugar que nao e a string de fabrica dele")
    else:
        erros.append(f"a tabela 0x{TABELA_PT:06X}..0x{TABELA_PT_FIM:06X} "
                     f"esta truncada na imagem")

    # os dois ids da RC1, nomeados: e o dano D4 desfazer o "Atualizar por SD"
    for k, i in enumerate(RC1_IDS):
        p = ponteiro(d, i)
        if p != PT_RC1[k]:
            erros.append(f"o id {i} aponta para 0x{p:08X}, esperado "
                         f"0x{PT_RC1[k]:08X} (o ponteiro da RC1; o de fabrica "
                         f"e 0x{PT_FABRICA_RC1[k]:08X} e nao serve)")

    erros += confere_lote(d, LOTE, LOTE_TAM, "o lote dos textos")
    erros += confere_sha(d, CMAP, N_GLIFOS * 2, CMAP_SHA,
                         "o cmap da fonte dos menus")
    erros += confere_sha(d, AVANCO, CMAP - AVANCO, AVANCO_SHA,
                         "a tabela de avancos da fonte dos menus")

    # cada id da lista: a string de destino existe e acaba em NUL na imagem
    for i in sorted(textos):
        p = ponteiro(d, i)
        if string_no(d, p) is None:
            erros.append(f"id {i}: o ponteiro 0x{p:08X} nao leva a uma "
                         f"string terminada em NUL dentro da imagem")
        elif LOTE <= p - XIP < LOTE + LOTE_TAM:
            erros.append(f"id {i} ja aponta para dentro do lote "
                         f"0x{LOTE:06X} — a imagem ja foi tratada")
    return erros


def confere_textos(d, textos):
    """TODAS as premissas da ficha NA LISTA. Devolve a lista de erros."""
    erros = []
    cmap = cmap_de(d)

    # dano D2: todo caractere tem glifo
    sem_glifo = set()
    for i, t in sorted(textos.items()):
        sem = [c for c in t if c != "\n" and ord(c) not in cmap]
        if sem:
            erros.append(f"id {i} {t!r}: sem glifo na fonte dos menus para "
                         f"{sem!r} — sairia quadrado ou cortado (dano D2)")
            sem_glifo.add(i)

    # dano D1: os especificadores `%` tem de ser os de fabrica. Um `%d` virando
    # `%s` faz o `printf` do aparelho ler o argumento na ordem errada.
    for i, t in sorted(textos.items()):
        if i in sem_glifo:
            continue
        fab = texto_de_fabrica(d, i)
        if fab is None:
            continue                     # ja recusado acima (dano D3)
        novo, velho = FORMATO.findall(t), FORMATO.findall(fab)
        if novo != velho:
            erros.append(f"id {i}: especificadores {novo} contra {velho} da "
                         f"fabrica — o `printf` do aparelho leria os "
                         f"argumentos na ordem errada (dano D1)")

    # dano D5: a home cabe nos 40 px do rotulo, sem corte e sem rolagem
    for i in HOME_IDS:
        if i not in textos:
            erros.append(f"id {i} (rotulo da home) nao esta na lista — a "
                         f"home ficaria com o texto de fabrica, que rola")
            continue
        larg = largura_px(d, cmap, textos[i])
        if larg is not None and larg > HOME_LARGURA:
            erros.append(f"id {i} {textos[i]!r} mede {larg} px e o rotulo da "
                         f"home tem {HOME_LARGURA} — o nome nao cabe inteiro")

    # dano D5, fora da home: cada linha cabe no widget de 113 px, ou nao e mais
    # larga que a da fabrica
    for i, t in sorted(textos.items()):
        if i in sem_glifo:
            continue
        fab = texto_de_fabrica(d, i)
        if fab is None:
            continue
        novo = maior_linha_px(d, cmap, t)
        velho = maior_linha_px(d, cmap, fab)
        if novo > max(LARGURA_LIMITE, velho):
            erros.append(f"id {i}: a maior linha mede {novo} px, e o limite e "
                         f"{max(LARGURA_LIMITE, velho)} px (113 do widget, ou "
                         f"a largura da propria fabrica) — o texto nao cabe "
                         f"(dano D5)")
    return erros


# ---------------------------------------------------------------------------
# a escrita
# ---------------------------------------------------------------------------

def monta_lote(textos):
    """(blob, {id: offset}) — as strings novas em UTF-8, cada uma com NUL.

    Em ordem de id, sem preenchimento: o lote tem 4 KiB para 2,8 KB de texto,
    entao nao ha por que desperdicicar byte com alinhamento. O que importa e
    que cada string comece onde a anterior acabou e termine em NUL — e que o
    aparelho vai ler por aquele ponteiro ate o NUL.
    """
    partes, offsets, pos = [], {}, 0
    for i in sorted(textos):
        bloco = textos[i].encode("utf-8") + b"\0"
        offsets[i] = pos
        partes.append(bloco)
        pos += len(bloco)
    blob = b"".join(partes)
    if len(blob) > LOTE_TAM:
        raise ValueError(
            f"as {len(textos)} strings somam {len(blob)} bytes e o lote "
            f"0x{LOTE:06X}..0x{LOTE + LOTE_TAM:06X} tem {LOTE_TAM}")
    return blob, offsets


def escreve(d, textos, blob, offsets):
    """O lote e as entradas da tabela dos ids da lista. NADA mais."""
    d[LOTE:LOTE + LOTE_TAM] = blob + b"\xFF" * (LOTE_TAM - len(blob))
    for i, off in offsets.items():
        d[TABELA_PT + 4 * i:TABELA_PT + 4 * i + 4] = struct.pack(
            "<I", XIP + LOTE + off)


def permitido(ids):
    """As regioes que a ficha permite escrever: o lote e as entradas da lista."""
    return [PERMITIDO_LOTE] + [(TABELA_PT + 4 * i, TABELA_PT + 4 * i + 4)
                               for i in sorted(ids)]


def confere_resultado(d, orig, textos, blob, offsets):
    """Rele o binario e confere, sem confiar na montagem."""
    erros = []

    # o lote: o blob escrito, e 0xFF ate o fim
    if bytes(d[LOTE:LOTE + len(blob)]) != blob:
        erros.append(f"o lote 0x{LOTE:06X}..0x{LOTE + len(blob):06X} nao e "
                     f"o blob montado")
    sobra = [i for i, x in enumerate(d[LOTE + len(blob):LOTE + LOTE_TAM])
             if x != 0xFF]
    if sobra:
        erros.append(f"lixo depois da ultima string, em "
                     f"0x{LOTE + len(blob) + sobra[0]:06X}")

    # cada id da lista: o ponteiro novo e a string que ele promete
    for i in sorted(textos):
        p = ponteiro(d, i)
        if p != XIP + LOTE + offsets[i]:
            erros.append(f"id {i}: a entrada aponta para 0x{p:08X}, esperado "
                         f"0x{XIP + LOTE + offsets[i]:08X}")
            continue
        if string_no(d, p) != textos[i].encode("utf-8"):
            erros.append(f"id {i}: a string no lote nao e {textos[i]!r}")
        if d[p - XIP + len(textos[i].encode("utf-8"))] != 0:
            erros.append(f"id {i}: a string do lote nao termina em NUL")

    # os ids de fora da lista, os dois da RC1 entre eles: entrada intacta
    for i in range(N_TEXTOS):
        if i in textos:
            continue
        if ponteiro(d, i) != ponteiro(orig, i):
            erros.append(f"id {i} (fora da lista) mudou de ponteiro")
            break
    for k, i in enumerate(RC1_IDS):
        if ponteiro(d, i) != PT_RC1[k]:
            erros.append(f"id {i} (da RC1) mudou de ponteiro")
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


def nome(caminho):
    """O caminho como se fosse da raiz do projeto, quando for."""
    if caminho.startswith(RAIZ + os.sep):
        return os.path.relpath(caminho, RAIZ)
    return caminho


def main():
    ap = argparse.ArgumentParser(
        description="RC5: os textos em portugues revisados e os nomes "
                    "curtos da home")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--textos", default=os.path.join(RAIZ, TEXTOS_PADRAO),
                    help=f"lista id<TAB>texto (padrao {TEXTOS_PADRAO})")
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
            print(f"RECUSADO: --em {em:#x}; o lote desta ferramenta esta em "
                  f"{EM_PADRAO:#x}, e o MAPA do build.py declara esse.",
                  file=sys.stderr)
            return 2

    if not os.path.exists(a.src):
        print(f"RECUSADO: {a.src} nao existe.", file=sys.stderr)
        return 2
    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    print("=" * 72)
    print("OpenPod — RC5: os textos em portugues revisados + os nomes da home")
    print("=" * 72)
    print(f"  origem : {nome(a.src)}\n  destino: {nome(a.dst)}\n"
          f"  textos : {nome(a.textos)}\n")

    try:
        textos = le_textos(a.textos)
    except ValueError as e:
        print(f"  RECUSADO — a lista de textos: {e}")
        print(f"\n  nada foi escrito em {nome(a.dst)}")
        return 1

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    # --- premissas, ANTES de qualquer escrita
    #
    # As da imagem primeiro e as da lista depois: medir largura com uma fonte
    # adulterada daria um numero bonito e falso, entao quando a imagem nao e a
    # da ficha as medidas nem sao tentadas.
    erros = confere_premissas(d, textos)
    motivo = "a imagem de entrada nao e a que a ficha mediu"
    if not erros:
        erros = confere_textos(d, textos)
        motivo = ("a lista de textos nao passa nas medidas do aparelho "
                  "(fonte, formato, largura)")
    if erros:
        print(f"  RECUSADO — {motivo}:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {nome(a.dst)}")
        return 1

    try:
        blob, offsets = monta_lote(textos)
    except ValueError as e:
        print(f"  RECUSADO — {e}")
        print(f"\n  nada foi escrito em {nome(a.dst)}")
        return 1

    print(f"  lista conferida ({len(textos)} ids, {nome(a.textos)}):")
    print(f"    - sha256 {SHA_TEXTOS[:16]}..., o que a ficha fixa")
    print(f"    - todo id em 0..{N_TEXTOS - 1}, nenhum 40/91 (da RC1), "
          f"nenhum repetido")
    print(f"    - todo caractere tem glifo; os `%` iguais aos de fabrica")
    print(f"    - os {len(HOME_IDS)} rotulos da home cabem em "
          f"{HOME_LARGURA} px; cada linha nova cabe em {LARGURA_LIMITE} px ou "
          f"nao e mais larga que a de fabrica\n")
    print("  entrada conferida:")
    print(f"    - 2 MiB, sha256 {SHA_RC4[:16]}... (a RC4 exata)")
    print(f"    - o literal 0x{LITERAL:06X} aponta para a tabela "
          f"0x{TABELA_XIP:08X}")
    print(f"    - a tabela 0x{TABELA_PT:06X}..0x{TABELA_PT_FIM:06X} e a de "
          f"fabrica (os ids 40 e 91 a parte)")
    print(f"    - os ids 40 e 91 apontam para os ponteiros da RC1 "
          f"(0x{PT_RC1[0]:08X}, 0x{PT_RC1[1]:08X})")
    print(f"    - o lote 0x{LOTE:06X}..0x{LOTE + LOTE_TAM:06X} esta virgem")
    print(f"    - o cmap e a tabela de avancos sao os de fabrica\n")

    escreve(d, textos, blob, offsets)
    print(f"  LOTE  0x{LOTE:06X}..0x{LOTE + LOTE_TAM:06X}  "
          f"({len(blob)} bytes escritos, "
          f"{LOTE_TAM - len(blob)} bytes em 0xFF)")
    print(f"    as {len(textos)} strings novas, em UTF-8 e com NUL, em ordem "
          f"de id")
    for i in sorted(textos)[:3] + sorted(textos)[-1:]:
        print(f"      0x{LOTE + offsets[i]:06X}  id {i:3d}  "
              f"0x{XIP + LOTE + offsets[i]:08X}  "
              f"{textos[i]!r}")
    print(f"      ... (as outras {len(textos) - 4} no relatorio da imagem)")

    print(f"\n  TABELA  0x{TABELA_PT:06X}  {len(textos)} entradas de 4 bytes "
          f"(so as ids da lista)")
    print(f"    0x{TABELA_XIP:08X} + 4 * id  ->  0x{XIP + LOTE:08X} + offset do "
          f"lote")
    print(f"    os outros {N_TEXTOS - len(textos)} ids intactos, os dois da "
          f"RC1 entre eles\n")

    erros = confere_resultado(d, orig, textos, blob, offsets)
    if erros:
        print("  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {nome(a.dst)}")
        return 1
    print("  conferencia (ponteiro e string de cada id, o NUL de cada uma, o "
          "0xFF depois da ultima,")
    print(f"    os {N_TEXTOS - len(textos)} ids de fora da lista com a entrada "
          f"que tinham, a RC1 no lugar): tudo OK\n")

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    ok = permitido(textos)
    fora = [i for i in dif if not any(a0 <= i < b0 for a0, b0 in ok)]
    if fora:
        print(f"  RECUSADO: escreveu fora do permitido em "
              f"0x{min(fora):06X}..0x{max(fora):06X}", file=sys.stderr)
        return 1
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)} em {len(secs)} setor(es): "
          + "  ".join(f"0x{s:06X}" for s in secs))

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {nome(a.dst)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())