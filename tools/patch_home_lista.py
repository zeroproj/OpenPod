#!/usr/bin/env python3
"""
patch_home_lista.py — a HOME deixa de ser grade 3x3 e vira LISTA,
                      pela carcaca do proprio firmware.

O ALVO

    Item M-b de `docs/MARTE_ALVO.md` §2, e o MARCO da linha: a home e a
    unica tela que nao usa a carcaca, e por isso a unica que nao obedece
    nada que ja funciona nas outras 39.

    Plano completo, escrito e aprovado ANTES desta ferramenta:
    `docs/PLANO_HOME.md`.

O QUE TORNA ISTO VIAVEL — tres medicoes, nesta ordem

    1. DESENHO E NAVEGACAO SAO DESACOPLADOS.
       A home roteia por TECLA e por INDICE, nunca por objeto clicado:

           00D2E96E  cmp r0, #0xd          LV_EVENT_KEY
           00D2EB2E  cmp r1, #8            indice 0..8, NOVE itens
           00D2EB32  strb r1,[0x00823D83]  o indice mora num global

       Trocar COMO os itens sao desenhados nao toca na navegacao.

    2. A SELECAO E ACHADA PELO INDICE, NO ARRAY B.

           00D2EB40  ldr r6,[r3,#0x24]     array B[indice] = O ROTULO
           00D2EB4C  bl set_style_text_color(r6, cor, 0)

       Esta ferramenta MANTEM o rotulo no array B. Logo todo o codigo de
       selecao e navegacao continua funcionando SEM SER TOCADO.

    3. A LINHA DA CARCACA FAZ LAYOUT SOZINHA — confirmado na Core 1.4.
       Os filhos se reorganizam; nao e preciso coordenada de filho.

ALOCACAO: ZERO BYTES — e isto elimina a unica classe de risco grave

    O molde do Configurar guarda TRES objetos por item (linha, texto,
    icone) e por isso precisaria de um terceiro array.

    A home do Marte NAO TEM ICONE — o M-e ja estabeleceu isso, e foi
    confirmado na tela. Ela precisa de DOIS, e JA TEM dois arrays:

        +0x00   hoje o quadro/icone   ->  passa a guardar A LINHA
        +0x24   o rotulo              ->  papel INALTERADO

    `malloc 0x54` FICA. Nenhuma aritmetica de ponteiro muda. Corrupcao
    de heap — que quebrou o `make_extras_menu` e que NAO aparece na
    verificacao byte a byte — esta fora do caminho.

A REGIAO REESCRITA

    0x00D2EC42 .. 0x00D2ED8F   334 bytes

    Comeca na carga da tabela de COORDENADAS (0x00C4867C e 0x00C486A0),
    que deixa de existir numa lista, e termina no `bne` do laco antigo.
    O codigo novo mora no lugar do velho: sem gancho, sem area livre,
    sem realocacao.

CONTRATO COM O CODIGO VIZINHO — o que entra e o que tem de sair

    entrada   r4 = a folha de imagem da grade
              r5 = a tela
              r8 = page_p (a estrutura de 0x54 bytes)

    saida     r4 PRESERVADO — 0x00D2EDC6 e 0x00D2EDD4 dependem dele
              [r8 + 0x00 + 4i] = a linha
              [r8 + 0x24 + 4i] = o rotulo

    r5, r6, r7, sb, sl, fp podem ser destruidos: o codigo seguinte
    recarrega r5 em 0x00D2ED90.

UM DESVIO DELIBERADO DO PLANO, e o motivo

    O `PLANO_HOME.md` §6 risco 3 dizia para NAO esconder a folha de
    imagem preventivamente — so se a tela mostrasse a grade por baixo.

    Esta ferramenta ESCONDE. Motivo: a folha **e** a grade, nao um
    "talvez". Deixa-la visivel produziria a lista desenhada por cima dos
    nove icones de fabrica, o que nao e um teste valido de nada.

    E um desvio declarado, nao silencioso.
    `0xD49204(r4, 1)` = add_flag(LV_OBJ_FLAG_HIDDEN).

USO
    python3 tools/patch_home_lista.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_home_lista.py --in <entrada.bin> --dry-run
    python3 tools/patch_home_lista.py --autoteste
    python3 tools/patch_home_lista.py --mostra     (so monta e desmonta)

DEPENDENCIAS
    Python 3 e `clang` com back-end ARM (via tools/asm.py).

LIMITACOES
    - a SELECAO continua sendo COR DE TEXTO, nao barra. E a Etapa 1 do
      plano, de proposito: prova a conversao sem mexer em mais nada.
      A barra e a Etapa 2, versao separada;
    - nao mexe na faixa superior, no degrade nem na bateria;
    - nao aloca, nao usa a area livre.
"""

import argparse, hashlib, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import monta

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000

BIAS     = 0x00C00000
INI      = 0x0012EC42          # offset de arquivo, inicio da regiao
FIM      = 0x0012ED90          # exclusivo
ESPACO   = FIM - INI           # 334 bytes

# ---------------------------------------------------------------------------
# ALINHAMENTO — um erro que quase foi para o aparelho
#
#     0x00D2EC42 NAO e multiplo de 4. O `ldr rX,[pc,#imm]` do ARM le a
#     partir do PC ALINHADO PARA BAIXO em 4, e o clang alinha o pool
#     literal dentro da secao supondo que ela comeca em 0.
#
#     Resultado medido: o pool caiu em 0x00D2ECEE — desalinhado. Os dois
#     ponteiros (a tabela de ids e o tratador de evento) seriam lidos do
#     lugar errado, e a home carregaria LIXO. Nao da erro de montagem,
#     nao da erro de validacao: so quebra no aparelho.
#
#     Conserto: o codigo montado comeca em 0x00D2EC44, que e multiplo de
#     4, e os dois bytes de 0x00D2EC42 viram NOP.
# ---------------------------------------------------------------------------
NOP      = b"\x00\xbf"
DESLOC   = 2                   # os 2 bytes de NOP antes do codigo
CODIGO_INI = INI + DESLOC      # 0x0012EC44
BASE     = BIAS + CODIGO_INI   # 0x00D2EC44 — MULTIPLO DE 4
assert BASE % 4 == 0, "a base do codigo montado tem de ser multipla de 4"

# --- os simbolos do firmware que o codigo novo chama ---------------------
SIMB = {
    "ADD_FLAG":       0x00D49204,   # lv_obj_add_flag(obj, flag)
    "CRIA_CONTEINER": 0x00D21690,   # a carcaca
    "CRIA_LINHA":     0x00D21764,   # a carcaca — 39 telas usam
    "CRIA_ROTULO":    0x00D5E2E8,
    "ADD_EVENT_CB":   0x00D47064,
    "DISP":           0x00D56898,   # prepara/obtem o display
    "ALTURA":         0x00D568CC,   # altura da tela
    "LARGURA":        0x00D568A4,   # largura da tela
    "SET_HEIGHT":     0x00D4A1EA,
    "SET_WIDTH":      0x00D4A1BA,
    "SET_POS":        0x00D4A3A2,
    "SET_LONG_MODE":  0x00D5EF04,
    "GET_STRING":     0x00D2108C,
    "SET_TEXT":       0x00D5ED94,
}
IDS      = 0x00C486C4          # tabela de ids de texto da home, 9 entradas
HANDLER  = 0x00D2E951          # page_home_event_cb | 1 (thumb)
N_ITENS  = 9
TOPO     = 19          # `inicio_lista` do Marte: onde a lista comeca, abaixo da barra de status


# ---------------------------------------------------------------------------
# COMO OS `bl` SAO RESOLVIDOS — e por que nao da para deixar com o clang
#
#     Tentei definir cada simbolo como (alvo - BASE), contando que o
#     `bl` PC-relativo se resolvesse sozinho. NAO se resolve: o clang
#     trata simbolo ABSOLUTO como o proprio deslocamento e NAO subtrai o
#     PC do ponto de chamada. Resultado medido: `bl 0xD4920C` onde se
#     queria `0xD49204` — oito bytes adiante, e cada chamada com um erro
#     diferente, porque o erro e o offset da instrucao.
#
#     Solucao: cada simbolo vira uma ETIQUETA unica e reconhecivel. O
#     clang monta, e depois esta ferramenta varre o resultado, identifica
#     cada `bl` pela etiqueta que ele carrega e REENCODA com o alvo certo,
#     ja sabendo o offset real da instrucao.
#
#     O `--autoteste` desmonta o resultado e confere alvo por alvo. Foi
#     assim que o erro acima apareceu, e e assim que ele nao volta.
# ---------------------------------------------------------------------------
ETIQUETA = 0x00200000          # base das etiquetas: longe de qualquer alvo


def _bl(origem, alvo):
    """Codifica `bl alvo` numa instrucao que mora em `origem` (endereco
    de execucao). Devolve 4 bytes."""
    off = alvo - (origem + 4)
    if not (-(1 << 24) <= off < (1 << 24)) or off & 1:
        raise RuntimeError(f"bl fora de alcance: 0x{origem:08X} -> 0x{alvo:08X}")
    v = off & 0x1FFFFFF
    S = (v >> 24) & 1
    i1 = (v >> 23) & 1
    i2 = (v >> 22) & 1
    imm10 = (v >> 12) & 0x3FF
    imm11 = (v >> 1) & 0x7FF
    j1 = (~i1 ^ S) & 1
    j2 = (~i2 ^ S) & 1
    w1 = 0xF000 | (S << 10) | imm10
    w2 = 0xD000 | (j1 << 13) | (j2 << 11) | imm11
    return bytes([w1 & 0xFF, w1 >> 8, w2 & 0xFF, w2 >> 8])


def _imm_bl(b, i):
    """Decodifica o deslocamento de um `bl` em b[i:i+4], ou None."""
    w1 = b[i] | (b[i + 1] << 8)
    if (w1 & 0xF800) != 0xF000:
        return None
    w2 = b[i + 2] | (b[i + 3] << 8)
    if (w2 & 0xD000) != 0xD000:
        return None
    S = (w1 >> 10) & 1
    imm10 = w1 & 0x3FF
    j1 = (w2 >> 13) & 1
    j2 = (w2 >> 11) & 1
    imm11 = w2 & 0x7FF
    i1 = (~(j1 ^ S)) & 1
    i2 = (~(j2 ^ S)) & 1
    v = (S << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if S:
        v -= (1 << 25)
    return v


def _resolve_bls(b):
    """Troca cada `bl <etiqueta>` pelo `bl <alvo real>`."""
    nomes = list(SIMB)
    por_etiqueta = {ETIQUETA + 4 * n: nomes[n] for n in range(len(nomes))}
    b = bytearray(b)
    achados = []
    i = 0
    while i < len(b) - 3:
        v = _imm_bl(b, i)
        if v is not None and v in por_etiqueta:
            nome = por_etiqueta[v]
            b[i:i + 4] = _bl(BASE + i, SIMB[nome])
            achados.append((i, nome))
            i += 4
            continue
        i += 2
    faltando = set(SIMB) - {n for _, n in achados}
    if faltando:
        raise RuntimeError(f"etiquetas nao encontradas: {sorted(faltando)}")
    return bytes(b), achados


def fonte():
    """O codigo novo. Cada simbolo e uma ETIQUETA unica — o alvo real e
    escrito depois, por `_resolve_bls`. Ver o comentario acima."""
    nomes = list(SIMB)
    defs = "\n".join(f"{k} = {ETIQUETA + 4 * n}" for n, k in enumerate(nomes))
    return f""".syntax unified
.thumb
{defs}

    @ --- esconde a folha de imagem da grade de fabrica -----------------
    @ r4 e a folha. Ela E a grade 3x3; deixa-la visivel desenharia os
    @ nove icones por tras da lista.
    movs  r1, #1                  @ LV_OBJ_FLAG_HIDDEN
    mov   r0, r4
    bl    ADD_FLAG

    @ --- o conteiner, pela carcaca -------------------------------------
    mov   r0, r5                  @ r5 = a tela
    bl    CRIA_CONTEINER
    mov   r7, r0

    @ O CONTEINER FICA DO TAMANHO DA TELA INTEIRA, a partir de y=0.
    @
    @ Na 2.0.1 eu o encolhi para comecar em y=19, para nao sobrepor a
    @ barra de status. Isso criou defeito PIOR: a faixa y=0..18 ficou
    @ descoberta, mostrando o fundo do DISPLAY — que e BRANCO
    @ (lv_disp_drv_register grava 0xFF; ver ARQUITETURA.md §12). E o
    @ relogio e a bateria sao desenhados em BRANCO, entao sumiram:
    @ branco sobre branco. Visto na tela.
    @
    @ O certo e o conteiner cobrir tudo de preto, e quem comeca em
    @ TOPO ser a LINHA. Assim o fundo fica preto, a barra de status
    @ volta a aparecer por cima dele, e nada e sobreposto.

    @ --- preparo do laco ------------------------------------------------
    ldr   r6, =0x{IDS:08X}        @ tabela de ids da home
    sub.w sl, r8, #4              @ base dos arrays, pre-indexada
    movs  r5, #0                  @ indice

laco:
    @ --- a LINHA -------------------------------------------------------
    mov   r0, r7
    bl    CRIA_LINHA
    mov   sb, r0

    @ altura da linha = (tela_h - TOPO) / 9
    @
    @ NAO e a formula do Configurar. Ele usa tela_h/7 porque tem 10 itens
    @ e mostra ~7, rolando o resto. A home tem NOVE itens que precisam
    @ CABER, e sem barra de rolagem (M-d).
    @     160/7 = 22 ; 22 * 9 = 198  >  160   <- transbordava. Visto na tela.
    @     (160-19)/9 = 15 ; 15 * 9 = 135      <- cabe, com folga
    bl    DISP
    bl    ALTURA
    subs  r0, r0, #{TOPO}
    movs  r1, #{N_ITENS}
    sdiv  r1, r0, r1
    sxth  r1, r1
    mov   r0, sb
    bl    SET_HEIGHT

    @ y = TOPO + altura_da_linha * indice
    @
    @ E a LINHA que desce, nao o conteiner. TOPO = 19 e o `inicio_lista`
    @ do Marte (marte/paleta/nanoclone.json) — deixa passar a barra de
    @ status, que continua desenhada por cima do fundo preto.
    bl    DISP
    bl    ALTURA
    subs  r0, r0, #{TOPO}
    movs  r3, #{N_ITENS}
    sdiv  r3, r0, r3
    mul   r3, r3, r5
    adds  r3, #{TOPO}
    sxth  r3, r3
    movs  r2, #0
    movs  r1, #2
    mov   r0, sb
    bl    SET_POS

    @ clicavel, e o mesmo tratador de evento de sempre
    movs  r1, #2
    mov   r0, sb
    bl    ADD_FLAG
    movs  r3, #0
    movs  r2, #0xd
    ldr   r1, =0x{HANDLER:08X}
    mov   r0, sb
    bl    ADD_EVENT_CB

    @ --- o ROTULO, filho da linha ---------------------------------------
    mov   r0, sb
    bl    CRIA_ROTULO
    mov   fp, r0

    bl    DISP
    bl    LARGURA
    subs  r1, r0, #0xf
    sxth  r1, r1
    mov   r0, fp
    bl    SET_WIDTH

    movs  r1, #4
    mov   r0, fp
    bl    SET_LONG_MODE

    ldr   r0, [r6]
    adds  r6, #4
    bl    GET_STRING
    mov   r1, r0
    mov   r0, fp
    bl    SET_TEXT

    @ --- guarda os ponteiros nos arrays QUE JA EXISTEM -------------------
    str   sb, [sl, #4]!           @ array A (+0x00) — agora a LINHA
    str.w fp, [sl, #0x24]         @ array B (+0x24) — o ROTULO, papel intacto

    adds  r5, #1
    cmp   r5, #{N_ITENS}
    bne   laco

    @ --- DESVIA POR CIMA DO POOL LITERAL --------------------------------
    @ Sem isto a execucao cai no pool e interpreta os ponteiros como
    @ instrucoes. Foi visto na desmontagem antes de gravar:
    @     00D2ECF0  c486  strh r4,[r0,#0x36]   <- isto e DADO
    b     depois
    .p2align 2
    .ltorg
depois:
    @ daqui em diante e NOP ate 0x00D2ED90, onde o codigo original segue
"""


def codigo(detalhe=False):
    b = monta(fonte())
    if len(b) % 2:
        b += b"\x00"
    b, achados = _resolve_bls(b)
    cabe = ESPACO - DESLOC
    if len(b) > cabe:
        raise RuntimeError(f"o codigo novo tem {len(b)} B e so cabem {cabe}")
    # NOP de alinhamento na frente; o resto da regiao vira NOP tambem,
    # para cair limpo em 0x00D2ED90
    b = NOP * (DESLOC // 2) + b + NOP * ((cabe - len(b)) // 2)
    return (b, achados) if detalhe else b


# guarda-corpo: o que tem de estar intacto ANTES e DEPOIS da regiao.
CONTEXTO = [
    (0x0012EC3E, bytes.fromhex("1ef028fa"), "bl bg_color, logo antes"),
    (0x0012EC42, bytes.fromhex("6a4b"),     "ldr r3,=0x00C4867C (inicio)"),
    (0x0012ED8E, bytes.fromhex("aed1"),     "bne do laco antigo (fim)"),
    (0x0012ED90, bytes.fromhex("1b4d"),     "ldr r5,=0x0081CE2C, logo depois"),
    (0x0012EDD4, bytes.fromhex("c8f84840"), "str.w r4,[r8,#0x48] — r4 vive"),
]


def confere_contexto(d):
    for off, esperado, desc in CONTEXTO:
        achado = bytes(d[off:off + len(esperado)])
        if achado != esperado:
            return False, (f"0x{off:06X} ({desc}): achei {achado.hex()}, "
                           f"esperava {esperado.hex()}")
    return True, "ok"


def aplica(d):
    novo = codigo()
    if bytes(d[INI:FIM]) == novo:
        return False, "patch ja aplicado"
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg
    d[INI:FIM] = novo
    return True, "ok"


def mostra():
    b, achados = codigo(detalhe=True)
    util = len(b.rstrip(b"\x00\xbf"))
    print(f"\n  CODIGO NOVO DA HOME\n")
    print(f"    montado : {util} bytes uteis")
    print(f"    regiao  : {ESPACO} bytes  (0x{BASE:08X} .. 0x{BASE+ESPACO-1:08X})")
    print(f"    folga   : {ESPACO - util} bytes, preenchidos com NOP")
    print(f"    cabe    : {'SIM' if util <= ESPACO else 'NAO'}\n")
    print(f"  OS {len(achados)} `bl`, RECONFERIDOS pela desmontagem do resultado\n")
    mau = 0
    for off, nome in achados:
        alvo = BASE + off + 4 + _imm_bl(b, DESLOC + off)
        ok = alvo == SIMB[nome]
        mau += not ok
        print(f"    0x{BASE+off:08X}  bl 0x{alvo:08X}  {nome:15} "
              + ("OK" if ok else f"ERRADO, esperado 0x{SIMB[nome]:08X}"))
    print()
    print("  TODOS OS ALVOS CONFEREM" if not mau else f"  {mau} ALVO(S) ERRADO(S)")
    print()
    for rotulo, pos in confere_pool(b):
        print(f"    {rotulo}")
        mau += 0 if pos else 1
    return 1 if mau else 0


def confere_pool(b):
    """Confere os dois `ldr rX,[pc,#imm]` do codigo: o endereco lido tem
    de ser MULTIPLO DE 4 e o valor tem de ser o esperado.

    E esta a conferencia que pegou o erro de alinhamento."""
    fora = []
    esperados = {IDS: "tabela de ids da home", HANDLER: "tratador de evento"}
    achados = {}
    for i in range(0, len(b) - 1, 2):
        hw = b[i] | (b[i + 1] << 8)
        if (hw & 0xF800) != 0x4800:          # ldr rX,[pc,#imm8]
            continue
        pc = (BIAS + INI + i + 4) & ~3
        end = pc + (hw & 0xFF) * 4
        k = end - (BIAS + INI)
        if not (0 <= k <= len(b) - 4):
            fora.append((f"ldr em 0x{BIAS+INI+i:08X} le FORA da regiao", False))
            continue
        val = int.from_bytes(b[k:k + 4], "little")
        alinhado = end % 4 == 0
        nome = esperados.get(val, f"valor 0x{val:08X} NAO esperado")
        ok = alinhado and val in esperados
        achados[val] = True
        fora.append((f"ldr em 0x{BIAS+INI+i:08X} -> 0x{end:08X} "
                     f"{'alinhado' if alinhado else 'DESALINHADO'}  "
                     f"= 0x{val:08X}  {nome}  " + ("OK" if ok else "FALHOU"), ok))
    for v, n in esperados.items():
        if v not in achados:
            fora.append((f"literal {n} (0x{v:08X}) NAO foi carregado", False))
    return fora


def autoteste():
    print("\n  AUTOTESTE — a home vira lista\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    orig = open(o, "rb").read()
    d = bytearray(orig)

    b, achados = codigo(detalhe=True)
    util = len(b.rstrip(b"\x00\xbf"))
    falhas = []
    print(f"    codigo montado         {util} B em {ESPACO} B  "
          + ("OK" if util <= ESPACO else "FALHOU"))
    if util > ESPACO:
        falhas.append("o codigo nao cabe")

    print(f"    base multipla de 4     0x{BASE:08X}  "
          + ("OK" if BASE % 4 == 0 else "FALHOU"))
    if BASE % 4:
        falhas.append("a base do codigo nao e multipla de 4")

    maus = [(o, n) for o, n in achados
            if BASE + o + 4 + _imm_bl(b, DESLOC + o) != SIMB[n]]
    print(f"    os {len(achados)} `bl`             "
          + ("OK" if not maus else f"FALHOU: {maus}"))
    if maus:
        falhas.append(f"bl errado: {maus}")

    ruim = [t for t, ok in confere_pool(b) if not ok]
    print("    pool literal alinhado  " + ("OK" if not ruim else "FALHOU"))
    for t in ruim:
        falhas.append(t)

    # O POOL NAO PODE SER EXECUTADO. Sem um desvio incondicional logo
    # antes dele, a execucao cai nos ponteiros e os interpreta como
    # instrucoes. Isto foi visto na desmontagem antes de gravar:
    #     00D2ECF0  c486  strh r4,[r0,#0x36]   <- dado virando codigo
    ini_pool = min((k for k in range(0, len(b) - 3, 2)
                    if int.from_bytes(b[k:k + 4], "little") in (IDS, HANDLER)),
                   default=None)
    salta = False
    if ini_pool is not None and ini_pool >= 2:
        # aceita `b.n` (0xE0xx) ou `b.w` nos 2/4 bytes anteriores,
        # eventualmente com um NOP de alinhamento no meio
        for recuo in (2, 4):
            k = ini_pool - recuo
            if k < 0:
                continue
            hw = b[k] | (b[k + 1] << 8)
            if (hw & 0xF800) == 0xE000 or (hw & 0xF800) == 0xF000:
                salta = True
            if b[k:k + 2] == NOP:
                continue
    print("    pool NAO executavel    " + ("OK" if salta else "FALHOU"))
    if not salta:
        falhas.append("nao ha desvio incondicional antes do pool literal — "
                      "a execucao cairia nos ponteiros")

    ok, msg = aplica(d)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    dentro = all(INI <= i < FIM for i in dif)
    print(f"    tudo dentro da regiao  {len(dif)} B  "
          + ("OK" if dentro else "FALHOU"))
    if not dentro:
        falhas.append("escreveu fora da regiao declarada")

    # o codigo vizinho tem de continuar identico
    for off, esperado, desc in CONTEXTO:
        if INI <= off < FIM:
            continue
        igual = bytes(d[off:off + len(esperado)]) == esperado
        print(f"    {desc[:34]:34} " + ("OK" if igual else "FALHOU"))
        if not igual:
            falhas.append(f"{desc} foi alterado")

    ok2, _ = aplica(d)
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
    ap = argparse.ArgumentParser(description="a home vira lista (M-b)")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    ap.add_argument("--mostra", action="store_true")
    a = ap.parse_args()

    if a.mostra:
        return mostra()
    if a.autoteste:
        return autoteste()
    if not a.src:
        ap.error("--in e obrigatorio (ou use --autoteste / --mostra)")
    if not a.dst and not a.dry_run:
        ap.error("--out e obrigatorio, ou use --dry-run")

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAMANHO:
        print(f"ERRO: {a.src} tem {len(d)} B, esperado {TAMANHO}",
              file=sys.stderr)
        return 1
    orig = bytes(d)

    print("\n  A HOME VIRA LISTA  (Marte M-b, Etapa 1)\n")
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    b = codigo()
    util = len(b.rstrip(b"\x00\xbf"))
    print(f"  REGIAO REESCRITA  0x{INI:06X} .. 0x{FIM-1:06X}   {ESPACO} B")
    print(f"    codigo novo {util} B   +  {ESPACO - util} B de NOP")
    print()
    print("  ALOCACAO   malloc 0x54 INTOCADO — zero bytes")
    print("    +0x00  array A  passa a guardar A LINHA")
    print("    +0x24  array B  continua guardando o ROTULO")
    print()
    print("  NAO TOCADO")
    print("    r4, a folha de imagem — 0x00D2EDD4 depende dela")
    print("    todo o codigo de selecao e navegacao")
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
