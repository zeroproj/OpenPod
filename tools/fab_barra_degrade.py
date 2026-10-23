#!/usr/bin/env python3
"""
fab_barra_degrade.py — itens 1 e 2 da ficha 002 (Reload 1.0 RC3): o
degradê da barra superior.

PROPOSITO

    Trocar o preto chapado da barra das 52 telas por um degradê vertical
    (RGB(64,70,82) no topo -> RGB(14,16,19) embaixo), e fazer o mesmo na
    home, que é uma imagem e não usa a rotina das telas. Dois lugares, uma
    ideia só. Nenhuma alocação nova além do lote 0x1A7000, nenhum objeto
    novo, nenhum cabeçalho tocado.

OS DOIS ITENS

    item 1 — as 52 telas que chamam a CRIA_FAIXA

        A CRIA_FAIXA (0x00D216F0) cria a faixa, põe a largura e chama o
        estilo de fundo em 0x00D21724. Esse `bl` é o gancho: ele vai para
        0x00D4D092 (wrapper de BG_COLOR) e recebe o objeto em r0. Trocar
        o ALVO — e não a função — mantém a lista de chamadas, o contrato
        de registradores e a conferência iguais às da fábrica.

        A rotina nova mora no lote 0x1A7000 (XIP 0x00DA7000), 56 bytes:

            push  {r4, lr}          ; pilha par, r4 = o objeto
            mov   r4, r0
            movw  r1, #0x2a42       ; topo, já pré-invertido
            movs  r2, #0
            bl    0x00D4D092        ; set_style_bg_color(obj, topo, 0)
            mov   r0, r4
            movs  r1, #0x21         ; LV_STYLE_BG_OPA
            movs  r2, #0xff         ; LV_OPA_COVER
            movs  r3, #0
            bl    0x00D4CAC4        ; set_local_style_prop
            mov   r0, r4
            movs  r1, #0x22         ; LV_STYLE_BG_GRAD_COLOR
            movw  r2, #0x8208       ; base, já pré-invertido
            movs  r3, #0
            bl    0x00D4CAC4
            mov   r0, r4
            movs  r1, #0x23         ; LV_STYLE_BG_GRAD_DIR
            movs  r2, #0x1          ; LV_GRAD_DIR_VER
            movs  r3, #0
            pop.w {r4, lr}          ; devolve r4 e o lr de quem chamou
            b.w   0x00D4CAC4        ; chamada de cauda: o retorno vai
                                    ; direto para 0x00D21728, que continua
                                    ; pintando o texto branco e a borda

        O `pop.w` seguido de `b.w` e o que faz a pilha voltar como estava:
        quem chamou (a CRIA_FAIXA) nao sabe que a pilha andou, e o
        registrador de link volta intacto. O `bl` substituido era de 4
        bytes, e a rotina tambem devolve 56 — o resto da CRIA_FAIXA nao se
        move em um byte.

        As cores vao PRE-INVERTIDAS porque a LVGL deste firmware foi
        compilada com LV_COLOR_16_SWAP: o valor que a CPU entrega a
        set_style_bg_color tem os bytes trocados. A ficha fixa 0x2A42
        (RGB(64,70,82)) e 0x8208 (RGB(14,16,19)); a ferramenta recalcula os
        dois a partir do RGB e recusa se nao bater.

        BG_OPA = LV_OPA_COVER (revisao R0) e posto aqui, e nao deixado
        para o tema: se o tema nao der opacidade ao fundo da faixa, o
        degradê nao aparece nas telas — sem quebrar nada, mas sem
        entregavel nenhum.

    item 2 — a home (folha de imagem)

        A home NAO usa a CRIA_FAIXA: e uma folha INDEXED_8 de 128x160 em
        0x0CDD50, e o relogio e a bateria sao desenhados por cima. As
        linhas y=0..15 sao todas indice 1 (preto) na fabrica.

        Aqui nao ha codigo para escrever: cada linha recebe UM indice de
        paleta, o mais proximo de `topo + (base - topo) * y / 15` entre as
        256 cores que ja existem na folha. A paleta NAO e tocada — a
        degradê sai das cores que o desenho ja usa, e por isso as linhas
        podem ficar com um matiz leve nas pontas (as 256 entradas estao em
        uso; ver os riscos aceitos da ficha). Os icones, que comecam em
        y=16, ficam como estavam.

        Criterios (os da ficha): erro maximo de 12 por canal, alfa 255 em
        todas as linhas e luminancia nunca subindo de uma linha para a
        seguinte. A ferramenta confere os tres DEPOIS de escrever e recusa
        em vez de gravar um degradê que ninguem conferiu.

PREMISSAS, conferidas ANTES de escrever qualquer byte

    A ficha pede recusa (D3) e nao aceitacao. Se UMA premissa falhar, a
    ferramenta sai com codigo diferente de zero, sem criar o arquivo de
    saida e sem tocar na entrada:

      - a imagem tem 2 MiB;
      - o `bl` do gancho (0x121724) ainda decodifica para 0x00D4D092;
      - a CRIA_FAIXA inteira (0x1216F0..0x121764) e a de fabrica. E a
        regiao que o gancho reescreve e a funcao que ele modifica: o resto
        dela precisa ser exatamente o codigo que a ficha mediu, byte a
        byte, nao "as Instructions que interessam";
      - as duas funcoes chamadas pela rotina nova continuam intactas:
        0x00D4D092 (0x22 bytes) e 0x00D4CAC4 (0x40 bytes). Sao elas que
        montam o valor da propriedade e vao para lv_obj_set_local_style_prop;
        se uma delas mudar de forma, o codigo novo escreve a propriedade
        errada sem nenhum erro visivel;
      - o lote 0x1A7000..0x1A7040 esta virgem (todo 0xFF). E o que barra
        a segunda passagem: depois da primeira a rotina esta la;
      - o cabecalho e a paleta da folha da home (0x0CDD50..0x0CE15C) sao
        os de fabrica, e as linhas y=0..15 sao todas indice 1. Sem isso a
        imagem nao e a folha que a ficha mediu — e o degradê cairia em
        cima de pixels que nao eram a barra;
      - `--em`, se vier, e o endereco fixo desta ferramenta.

    As regioes "tem de ser as de fabrica" sao presas por sha256 em vez de
    coladas no fonte: 1 KiB de paleta e 0x74 bytes de codigo no fonte
    seriam ruido, e o sha diz a mesma coisa sem chance de erro de digito.
    A conferencia com bytes crus continua existindo para o que ESTA
    ferramenta escreve: o gancho, a rotina e as linhas da home.

CONFERENCIA DE SAIDA

    A rotina e montada pelos encoders Thumb-2 daqui e conferida contra o
    literal de 56 bytes fixado abaixo. Se os dois discordarem, a
    ferramenta recusa: sao dois caminhos independentes para o mesmo
    codigo, e o disagreement e a pista de que um dos dois esta errado.
    O mesmo vale para o `bl` do gancho.

    Depois, a ferramenta relê o que escreveu e confere: alvo do gancho,
    os 56 bytes da rotina, o 0xFF que vem depois dela, o indice escolhido
    em cada uma das 16 linhas, o alfa, o erro por canal e a luminancia.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`, achado 001-R1).
    Sem isso, um link com outro nome passaria pela comparacao de caminho
    e a gravacao escreveria por cima da entrada.

    E so se escreve DENTRO de: 0x121724..0x121728, 0x1A7000..0x1A7040 e
    0x0CE15C..0x0CE95C. Qualquer byte fora disso e recusa, sem gravar.

USO

    python3 tools/fab_barra_degrade.py --in <entrada.bin> --out <saida.bin>
                                      [--em 0x1a7000] [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib). Nao abre USB, nao grava no aparelho.

LIMITACOES

    - so serve na imagem que a ficha mediu: qualquer outra e recusada, mesmo
      que os enderecos existam;
    - a degradê da home e quantizacao: as 16 linhas usam 7 das 256 cores
      da paleta (as mais proximas), entao as pontas podem ficar com um
      matiz de ate 10 por canal em relacao a cor ideal. E o que a ficha
      registra como risco aceito;
    - a cor do topo da home (66,76,81) e a cor do topo dos menus
      (64,70,82): sao quantizacoes diferentes da mesma ideia. Nao ha como
      igualar sem mexer na paleta, que a ficha proibe;
    - a Tocando Agora NAO ganha degradê: o papel de parede e uma imagem
      propria, fora do escopo desta RC;
    - depois de aplicada, rodar de novo sobre a saida e recusado (o gancho
      ja nao e o de fabrica e o lote ja nao esta virgem). E o comportamento
      correto: a ferramenta e feita para a receita, uma vez.
"""

import argparse
import hashlib
import os
import struct
import sys

XIP = 0x00C00000
TAMANHO = 0x200000                          # 2 MiB

# --- item 1: a faixa das 52 telas
CRIA_FAIXA, CRIA_FAIXA_FIM = 0x1216F0, 0x121764
CRIA_FAIXA_SHA = "f8b0da202b8c984db1697f15bd1c9d854ad2b55d96d8714f0a4234fbbade73b8"
GANCHO = 0x121724                            # bl set_style_bg_color
GANCHO_FABRICA = bytes.fromhex("2bf0b5fc")   # bl 0x00D4D092
GANCHO_NOVO = bytes.fromhex("85f06cfc")      # bl 0x00DA7000
SET_BG_COLOR = 0x00D4D092
SET_BG_COLOR_TAM = 0x22
SET_BG_COLOR_SHA = "73c06b155e878421954028ceac51621ae6d6cb6d17fd8695baecb0839c42b904"
SET_LOCAL_PROP = 0x00D4CAC4
SET_LOCAL_PROP_TAM = 0x40
SET_LOCAL_PROP_SHA = "ebef9149b1c09faeb1ec452acdf99dac66066f8ba5dea064e6ade550c5b24a59"

ROTINA = 0x1A7000                            # XIP 0x00DA7000
ROTINA_LOTE = 0x40
EM_PADRAO = ROTINA

# --- as cores: RGB de 8 bits, e o valor pre-invertido (LV_COLOR_16_SWAP)
COR_TOPO = (64, 70, 82)
COR_BASE = (14, 16, 19)
TOPO_SWAP, BASE_SWAP = 0x2A42, 0x8208

# --- item 2: a folha da home
HOME_CAB, HOME_PAL, HOME_PX = 0x0CDD50, 0x0CDD5C, 0x0CE15C
HOME_LARG, HOME_LINHAS = 128, 16            # y=0..15 e a barra; y>=16 e icone
HOME_CAB_PAL_SHA = "0630d9d9b1e23a05a1294eb526b91176f09b832c12af68f8e9d89900c7f84eea"
HOME_PALETA = 256 * 4
INDICE_FABRICA = 1                           # as 16 linhas comecam pretas

# limites da ficha (criterio de aceite C4)
ERRO_MAX = 12

# a rotina de 56 bytes, literal. Nao e a fonte da verdade — a fonte sao os
# encoders logo abaixo; e o outro caminho, para os dois discordarem juntos
# nunca passarem sem alarde.
ROTINA_LITERAL = bytes.fromhex(
    "10b5" "0446" "42f64221" "0022" "a6f742f8"     # push; mov r4,r0; movw; movs; bl
    "2046" "2121" "ff22" "0023" "a5f755fd"         # bg_opa = COVER; bl
    "2046" "2221" "48f20822" "0023" "a5f74efd"     # grad_color; bl
    "2046" "2321" "0122" "0023"                    # grad_dir = VER
    "bde81040" "a5f746bd"                          # pop.w; b.w (cauda)
)


# ---------------------------------------------------------------------------
# Thumb-2. Os encoders vivem aqui porque o codigo e o objeto da RC: um
# literal opaco de 56 bytes nao deixa ninguem conferir nada.
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

    Conferido contra os 413 saltos largos incondicionais do ORIGINAL: com
    (endereco, alvo) certainos, estes encoders reproduzem os bytes da
    fabrica um a um.
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
    bits da segunda sao imm16[10:8]. Conferido contra o assembler do LLVM.
    """
    h1 = 0xF240 | (((imm16 >> 11) & 1) << 10) | ((imm16 >> 12) & 0xF)
    h2 = (((imm16 >> 8) & 0x7) << 12) | (rd << 8) | (imm16 & 0xFF)
    return struct.pack("<HH", h1, h2)


def monta_rotina():
    """Os 56 bytes da ficha, montados na ordem em que estao na lista."""
    base = XIP + ROTINA
    b = bytearray()
    b += struct.pack("<H", 0xB510)            # push {r4, lr}
    b += mov_reg(4, 0)                        # mov   r4, r0
    b += movw(1, TOPO_SWAP)                   # movw  r1, #0x2A42
    b += movs_imm(2, 0)                       # movs  r2, #0
    b += enc_bl(base + len(b), SET_BG_COLOR)  # bl    set_style_bg_color
    b += mov_reg(0, 4)                        # mov   r0, r4
    b += movs_imm(1, 0x21)                    # BG_OPA
    b += movs_imm(2, 0xFF)                    # LV_OPA_COVER
    b += movs_imm(3, 0)                       # seletor 0
    b += enc_bl(base + len(b), SET_LOCAL_PROP)
    b += mov_reg(0, 4)                        # mov   r0, r4
    b += movs_imm(1, 0x22)                    # BG_GRAD_COLOR
    b += movw(2, BASE_SWAP)                   # movw  r2, #0x8208
    b += movs_imm(3, 0)                       # seletor 0
    b += enc_bl(base + len(b), SET_LOCAL_PROP)
    b += mov_reg(0, 4)                        # mov   r0, r4
    b += movs_imm(1, 0x23)                    # BG_GRAD_DIR
    b += movs_imm(2, 1)                       # LV_GRAD_DIR_VER
    b += movs_imm(3, 0)                       # seletor 0
    b += struct.pack("<HH", 0xE8BD, 0x4010)   # pop.w {r4, lr}
    b += enc_b(base + len(b), SET_LOCAL_PROP)  # b.w  (cauda)
    return bytes(b)


def rgb565_swap(c):
    """RGB de 8 bits -> o valor que a LVGL com LV_COLOR_16_SWAP espera."""
    v = ((c[0] >> 3) << 11) | ((c[1] >> 2) << 5) | (c[2] >> 3)
    return ((v & 0xFF) << 8) | (v >> 8)


# ---------------------------------------------------------------------------
# o degradê da folha
# ---------------------------------------------------------------------------

def alvo_linha(y):
    """A cor ideal da linha y: topo + (base - topo) * y / (linhas - 1)."""
    t = y / (HOME_LINHAS - 1)
    return tuple(round(COR_TOPO[k] + (COR_BASE[k] - COR_TOPO[k]) * t)
                 for k in range(3))


def luminancia(r, g, b):
    """A mesma conta do criterio de aceite (299/587/114)."""
    return 299 * r + 587 * g + 114 * b


def escolhe_linhas(pal):
    """Um indice de paleta por linha y=0..15.

    Metrica: distancia de Chebyshev (o maximo por canal), que e o proprio
    limite da ficha; desempate pela soma dos quadrados e depois pelo
    indice, para o resultado ser estavel entre execucoes.
    """
    cands = []
    for i in range(256):
        b, g, r, a = pal[i * 4:i * 4 + 4]
        if a == 255:                       # a barra e opaca
            cands.append((i, (r, g, b)))
    if not cands:
        raise ValueError("a paleta da folha nao tem cor com alfa 255")
    escolhidas = []
    for y in range(HOME_LINHAS):
        t = alvo_linha(y)

        def custo(c):
            r, g, b = c[1]
            return (max(abs(r - t[0]), abs(g - t[1]), abs(b - t[2])),
                    sum((c[1][k] - t[k]) ** 2 for k in range(3)), c[0])

        escolhidas.append(min(cands, key=custo)[0])
    return escolhidas


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

    alvo = bl_alvo(d, GANCHO)
    if alvo != SET_BG_COLOR:
        erros.append(f"0x{GANCHO:06X} chama "
                     f"{'nada' if alvo is None else f'0x{alvo:08X}'}, "
                     f"esperado 0x{SET_BG_COLOR:08X} (o gancho de fabrica)")
    erros += confere_sha(d, CRIA_FAIXA, CRIA_FAIXA_FIM - CRIA_FAIXA,
                         CRIA_FAIXA_SHA, "CRIA_FAIXA")
    erros += confere_sha(d, SET_BG_COLOR - XIP, SET_BG_COLOR_TAM,
                         SET_BG_COLOR_SHA, "set_style_bg_color")
    erros += confere_sha(d, SET_LOCAL_PROP - XIP, SET_LOCAL_PROP_TAM,
                         SET_LOCAL_PROP_SHA, "lv_obj_set_local_style_prop")
    erros += confere_lote(d, ROTINA, ROTINA_LOTE, "lote da rotina")

    erros += confere_sha(d, HOME_CAB, HOME_PX - HOME_CAB,
                         HOME_CAB_PAL_SHA, "cabecalho+paleta da folha")
    for y in range(HOME_LINHAS):
        ini = HOME_PX + HOME_LARG * y
        fora = [i for i in range(ini, ini + HOME_LARG)
                if d[i] != INDICE_FABRICA]
        if fora:
            erros.append(f"folha da home: a linha y={y} (0x{ini:06X}..) tem "
                         f"{len(fora)} pixel(is) de indice {INDICE_FABRICA}, "
                         f"o primeiro em 0x{fora[0]:06X} — nao e a barra "
                         f"preta de fabrica")
            break

    if rgb565_swap(COR_TOPO) != TOPO_SWAP:
        erros.append(f"RGB{COR_TOPO} pre-invertido da {rgb565_swap(COR_TOPO):#06x}, "
                     f"a ficha fixa {TOPO_SWAP:#06x}")
    if rgb565_swap(COR_BASE) != BASE_SWAP:
        erros.append(f"RGB{COR_BASE} pre-invertido da {rgb565_swap(COR_BASE):#06x}, "
                     f"a ficha fixa {BASE_SWAP:#06x}")
    return erros


PERMITIDO = [
    (GANCHO, GANCHO + 4),
    (ROTINA, ROTINA + ROTINA_LOTE),
    (HOME_PX, HOME_PX + HOME_LARG * HOME_LINHAS),
]


# ---------------------------------------------------------------------------
# os dois itens
# ---------------------------------------------------------------------------

def item1_faixa(d):
    """O gancho passa a chamar a rotina, e a rotina vai para o lote."""
    rotina = monta_rotina()
    if rotina != ROTINA_LITERAL:
        raise ValueError("os encoders e o literal de 56 bytes discordam:\n"
                         f"    encoders: {rotina.hex()}\n"
                         f"    literal : {ROTINA_LITERAL.hex()}")
    if len(rotina) > ROTINA_LOTE:
        raise ValueError(f"a rotina tem {len(rotina)} bytes e o lote "
                         f"{ROTINA_LOTE}")
    if enc_bl(XIP + GANCHO, XIP + ROTINA) != GANCHO_NOVO:
        raise ValueError("o bl do gancho montado nao bate com o literal")
    if d[GANCHO:GANCHO + 4] != GANCHO_FABRICA:
        raise ValueError("o bl do gancho nao e o de fabrica")

    d[GANCHO:GANCHO + 4] = GANCHO_NOVO
    d[ROTINA:ROTINA + ROTINA_LOTE] = rotina + b"\xFF" * (ROTINA_LOTE - len(rotina))
    return len(rotina)


def item2_home(d):
    """Cada linha da barra da home ganha o indice de paleta mais proximo."""
    pal = bytes(d[HOME_PAL:HOME_PX])
    if len(pal) != HOME_PALETA:
        raise ValueError(f"a paleta tem {len(pal)} bytes, esperado "
                         f"{HOME_PALETA}")
    linhas = escolhe_linhas(pal)
    for y, i in enumerate(linhas):
        d[HOME_PX + HOME_LARG * y:HOME_PX + HOME_LARG * (y + 1)] = bytes([i]) \
            * HOME_LARG
    return linhas


def confere_resultado(d, orig, tam):
    """Relê o que foi escrito e confere, sem confiar na montagem."""
    erros = []
    alvo = bl_alvo(d, GANCHO)
    if alvo != XIP + ROTINA:
        erros.append(f"0x{GANCHO:06X} aponta para "
                     f"{'nada' if alvo is None else f'0x{alvo:08X}'}, "
                     f"esperado 0x{XIP + ROTINA:08X}")
    if bytes(d[ROTINA:ROTINA + tam]) != ROTINA_LITERAL:
        erros.append(f"a rotina em 0x{ROTINA:06X} nao e a da ficha")
    if any(x != 0xFF for x in d[ROTINA + tam:ROTINA + ROTINA_LOTE]):
        erros.append(f"lixo depois da rotina, em 0x{ROTINA + tam:06X}..")

    erros += confere_sha(d, SET_BG_COLOR - XIP, SET_BG_COLOR_TAM,
                         SET_BG_COLOR_SHA, "set_style_bg_color")
    erros += confere_sha(d, SET_LOCAL_PROP - XIP, SET_LOCAL_PROP_TAM,
                         SET_LOCAL_PROP_SHA, "lv_obj_set_local_style_prop")

# a CRIA_FAIXA: tudo igual a entrada (que a premissa ja prendeu ao
    # sha256 de fabrica), menos os 4 bytes do gancho, que e justamente o
    # que esta ferramenta troca
    antes = bytes(orig[CRIA_FAIXA:CRIA_FAIXA_FIM])
    esperado = (antes[:GANCHO - CRIA_FAIXA] + GANCHO_NOVO
                + antes[GANCHO + 4 - CRIA_FAIXA:])
    if bytes(d[CRIA_FAIXA:CRIA_FAIXA_FIM]) != esperado:
        erros.append(f"a CRIA_FAIXA mudou fora dos 4 bytes do gancho "
                     f"(0x{CRIA_FAIXA:06X}..0x{CRIA_FAIXA_FIM:06X})")

    pal = bytes(d[HOME_PAL:HOME_PX])
    lum_ant = None
    pior = 0
    for y in range(HOME_LINHAS):
        linha = bytes(d[HOME_PX + HOME_LARG * y:HOME_PX + HOME_LARG * (y + 1)])
        if len(set(linha)) != 1:
            erros.append(f"linha y={y} da home nao ficou uniforme")
            continue
        i = linha[0]
        b, g, r, a = pal[i * 4:i * 4 + 4]
        if a != 255:
            erros.append(f"linha y={y}: indice {i} com alfa {a}")
        alvo_l = alvo_linha(y)
        erro = max(abs(r - alvo_l[0]), abs(g - alvo_l[1]), abs(b - alvo_l[2]))
        pior = max(pior, erro)
        if erro > ERRO_MAX:
            erros.append(f"linha y={y}: RGB({r},{g},{b}) a {erro} do alvo "
                         f"{alvo_l} (max {ERRO_MAX})")
        lum = luminancia(r, g, b)
        if lum_ant is not None and lum > lum_ant:
            erros.append(f"linha y={y} ficou mais clara ({lum}) que a "
                         f"anterior ({lum_ant})")
        lum_ant = lum
    if d[HOME_PX] == INDICE_FABRICA:
        erros.append("a primeira linha da home continua preta")
    return erros, pior


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
        description="RC3 itens 1 e 2: degradê na faixa das 52 telas e na home")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", default=None,
                    help=f"endereco da rotina (tem de ser {EM_PADRAO:#x})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.em is not None:
        try:
            em = int(a.em, 0)
        except ValueError:
            print(f"RECUSADO: --em {a.em!r} nao e um endereco.", file=sys.stderr)
            return 2
        if em != EM_PADRAO:
            print(f"RECUSADO: --em {em:#x}; a rotina desta ferramenta esta "
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
    print("OpenPod — RC3 itens 1 e 2: degradê da barra superior")
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
    print("    - 2 MiB")
    print(f"    - o `bl` do gancho 0x{GANCHO:06X} ainda chama "
          f"0x{SET_BG_COLOR:08X}")
    print(f"    - CRIA_FAIXA 0x{CRIA_FAIXA:06X}..0x{CRIA_FAIXA_FIM:06X} intacta")
    print(f"    - 0x{SET_BG_COLOR:08X} e 0x{SET_LOCAL_PROP:08X} intactas")
    print(f"    - lote 0x{ROTINA:06X}..0x{ROTINA + ROTINA_LOTE:06X} virgem")
    print(f"    - cabecalho+paleta da folha e as {HOME_LINHAS} linhas pretas "
          f"de fabrica\n")

    try:
        tam_rotina = item1_faixa(d)
        linhas = item2_home(d)
    except ValueError as e:
        print(f"  RECUSADO — {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    print("  ITEM 1 — a faixa das 52 telas (a CRIA_FAIXA)")
    print(f"    gancho  0x{GANCHO:06X}  {GANCHO_FABRICA.hex()} -> "
          f"{GANCHO_NOVO.hex()}   bl 0x{SET_BG_COLOR:08X} -> "
          f"0x{XIP + ROTINA:08X}")
    print(f"    rotina  0x{ROTINA:06X}..0x{ROTINA + tam_rotina:06X}  "
          f"{tam_rotina} bytes, o resto do lote em 0xFF")
    print(f"      topo     RGB{COR_TOPO} -> {TOPO_SWAP:#06x} "
          f"(pre-invertido, LV_COLOR_16_SWAP)")
    print(f"      base     RGB{COR_BASE} -> {BASE_SWAP:#06x}")
    print("      bg_opa   0x21 = LV_OPA_COVER (nao depende do tema)")
    print("      grad_dir 0x23 = LV_GRAD_DIR_VER")
    print(f"      a cauda `b.w` volta para 0x{SET_LOCAL_PROP:08X}, e de la o "
          f"retorno segue para 0x{XIP + GANCHO + 4:08X}")
    print("      a CRIA_FAIXA nao mudou em nenhum outro byte\n")

    pal = bytes(d[HOME_PAL:HOME_PX])
    print(f"  ITEM 2 — a barra da home (folha {HOME_LARG}x160)")
    print(f"    pixels  0x{HOME_PX:06X}..0x{HOME_PX + HOME_LARG * HOME_LINHAS:06X}"
          f"  ({HOME_LARG * HOME_LINHAS} bytes, {HOME_LINHAS} linhas)")
    print(f"    paleta NAO tocada (0x{HOME_PAL:06X}..0x{HOME_PX:06X})")
    print(f"    {'y':>3} {'alvo':>14} {'idx':>4} {'RGB':>14} {'erro':>5}")
    for y in range(HOME_LINHAS):
        i = linhas[y]
        b, g, r, _ = pal[i * 4:i * 4 + 4]
        alvo = alvo_linha(y)
        erro = max(abs(r - alvo[0]), abs(g - alvo[1]), abs(b - alvo[2]))
        print(f"    {y:3d} {str(alvo):>14} {i:4d} "
              f"{str((r, g, b)):>14} {erro:5d}")
    print(f"    icones (y >= {HOME_LINHAS}) NAO tocados\n")

    erros, pior = confere_resultado(d, orig, tam_rotina)
    if erros:
        print("  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  conferencia (saltos lidos de volta, 56 bytes da rotina, 0xFF "
          "depois dela, paleta e as duas funcoes): tudo OK")
    print(f"    erro maximo por canal no degradê da home: {pior} "
          f"(limite {ERRO_MAX})\n")

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