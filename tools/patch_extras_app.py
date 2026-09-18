#!/usr/bin/env python3
"""
patch_extras_app.py — os seis destinos do Extras, na camada APP

PROPOSITO
    Fazer o handler da pagina 0x53 (camada APP) entender SEIS indices em
    vez de tres, e mandar cada um para a tela certa.

    E a segunda metade do conserto. A primeira (Core 3.3) esta em
    `tools/patch_extras_router.py` e ja foi confirmada no aparelho.

POR QUE AQUI, E NAO NO CALLBACK DO LVGL
    A Core 3.2 chamou a navegacao de dentro do callback do LVGL e travou
    o aparelho: a navegacao roda noutra task. Este patch fica DENTRO do
    handler da APP, que ja e a task certa -- o mesmo lugar onde o
    firmware de fabrica abre as paginas.

O QUE O HANDLER DE FABRICA FAZ  (0x00D0CC7C, medido)

    ldrh r2, [r4, #0xc]     ; indice do item
    cmp  r2, #2
    bhi  #0x00D0CD6E        ; > 2 -> retorno limpo      <<< O LIMITE
    ...
    ldrh r5, [r4, #0xc]
    cmp  r5, #1 / beq / blo / cmp #2 / beq   ; despacho de TRES

    E cada caso abre a pagina assim (indice 0, o mais simples):

        movs r3, #0x1e          ; pagina destino (Alarme)
        movs r2, #0             ; sub
        ldrh r1, [r4, #0xa]     ; r1 vem DA MENSAGEM, nao e literal
        ldrh r0, [r4, #8]       ; r0 = pagina corrente, DA MENSAGEM
        pop.w {r4,r5,r6,r7,r8,lr}
        b.w  #0x00D0DAE0

    Confirmado no aparelho em 17/09: o item 1 do Extras abria o Alarme,
    que e exatamente a pagina 0x1E deste caso.

O QUE ESTE PATCH FAZ
    1. Troca 4 bytes em 0x00D0CC7E (`cmp r2,#2` + `bhi`) por um `b.w`.
    2. Instala em 0x00DA6200 um despacho de SEIS, com a MESMA convencao
       medida acima, incluindo a checagem de cartao e a mensagem de
       "sem cartao" de fabrica (0x00D0CCC2).

USO
    python3 tools/patch_extras_app.py \
        firmware/WORKING/GN438_core_3.3_carimbado.bin \
        firmware/WORKING/GN438_core_3.4_sem_versao.bin

LIMITACOES
    - Feito para uma imagem que ja tenha o roteador da 3.3.
    - Nao recalcula CRC (politica do projeto).
"""
import sys

BASE_XIP  = 0x00C00000
APP_ROUTER = 0x00DA6200          # mesma area livre, depois do roteador LVGL
HOOK       = 0x00D0CC7E          # cmp r2,#2 / bhi  -> 4 bytes
ABRE_PAG   = 0x00D0DAE0          # primitiva (chamada da task certa)
SEM_CARTAO = 0x00D0CCC2          # movs r0,#0x2f ; mostra "sem cartao"
RETORNO    = 0x00D0CD6E          # pop.w {r4,r5,r6,r7,r8,pc}
CHECA_CART = 0x00CFE714

# indice na tela -> (pagina, checa cartao, PRECISA DE PREPARO, nome)
#
# >>> O ERRO DA Core 3.5 <<<
#   Ela trocou "abrir a pagina" por "saltar para o caso de fabrica da
#   home". Os casos da home leem campos DA MENSAGEM (`ldrh r2,[r4,#0xc]`
#   e companhia), e a mensagem do Extras tem os campos com outro
#   significado. Cada item foi parar num lugar diferente.
#   O mantenedor: "os menus estao todos bugados indo para outras coisas".
#
#   A 3.4 estava certa. Trocar o que funciona por uma teoria custou uma
#   gravacao.
#
# ESTA VERSAO: volta ao desenho da 3.4 (abrir a pagina direto) e
# REPLICA a preparacao do FM como sub-rotina, em vez de saltar para ela.
#
# POR QUE O RADIO PRECISA DISSO (Core 3.5)
#   A 3.4 abria a pagina e mais nada. O Radio abriu, mas nao sintonizava:
#   o caso da home faz CINCO coisas antes de abrir a pagina 0x1A --
#   mensagem, 0x00CFEC60, 0x00D45D50 e 0x00D00510 (a inicializacao do
#   tuner). Abrir a pagina sem isso da uma tela de radio morta.
#
#   Os casos abaixo foram medidos e tem frame COMPATIVEL com o nosso
#   (push.w {r4,r5,r6,r7,r8,lr}), e usam r4 = mensagem, igual a nos.
#   O de Imagem mora na PROPRIA funcao 0x00D0CC0C (indice 1 de fabrica).
#
#   Pastas continua abrindo direto: nao achei caso de fabrica com frame
#   compativel. O bloco da pagina 0x52 (0x00D0C888) desempilha QUATRO
#   registradores e nao serve.
# prep: sub-rotina de preparacao, ou None
# arg : (origem, r1) com que chamar a primitiva, ou None para usar os
#       campos da mensagem (o que a 3.4/3.6/3.7 faziam)
#
# >>> POR QUE `arg` EXISTE (Core 3.8) <<<
#   A 3.7 replicou a preparacao de Imagem e Livro digital e NAO
#   resolveu -- "do mesmo jeito". Comparando a chamada final:
#
#       fabrica (0x00D011EA):  r0=1     r1=2   r2=0  r3=0x15
#       3.7                 :  r0=0x53  r1=4   r2=0  r3=0x15
#
#   A pagina GUARDA a origem no proprio estado (0x00D03AD8:
#   `strh r0,[r5,#-8]`), entao r0 nao e decorativo.
#
#   HIPOTESE, nao medida: a pagina decide atualizar a lista a partir da
#   origem. E a segunda tentativa neste mesmo item -- se nao resolver,
#   parar e instrumentar em vez de tentar de novo.
#
#   arg == "T": sub-rotina TERMINAL, replica a cauda de fabrica.
#
# >>> A Core 3.9 E UM EXPERIMENTO CONTROLADO <<<
#   A mensagem "Lendo arquivos. Nao desligue nem remova o cartao" e o
#   id 0x9A. No caso de fabrica ela aparece assim:
#
#       bl   #0x00D3EC3C        ; quantos arquivos faltam varrer?
#       subs r5, r0, #0
#       ble  <segue e abre>
#         movs r0, #0x9a        ; "Lendo arquivos..."
#         bl   get_string / bl 0x00D0E2F0
#         b    <RETORNA, NAO abre a pagina>
#
#   A VARREDURA E ESSE RAMO. A 3.7 e a 3.8 copiaram so o outro -- o de
#   quando a lista ja esta pronta. E `0x00D3EC3C`, a contagem que decide
#   qual ramo tomar, nunca foi chamada.
#
#   Em vez de replicar de novo (duas tentativas ja falharam), o indice 2
#   SALTA para o caso de fabrica inteiro (`prep` = endereco, arg "F").
#   Isso e a tecnica que quebrou na Core 3.5 -- mas la ela foi aplicada
#   aos SEIS itens, e a quebra veio do despacho compartilhado 0x00D01036
#   ler r0/r1/r2 da mensagem. Aqui a pagina de destino e FIXA no codigo
#   (`movs r3,#0xc`), entao nao ha como ir para a tela errada.
#
#   O indice 3 (Imagem) ficou IGUAL AO DA 3.7 na 3.9, de proposito, para
#   servir de controle.
#
# >>> RESULTADO DA 3.9, no aparelho <<<
#   O salto para o caso de fabrica FUNCIONOU. Mantenedor: a varredura
#   passou a rodar ao entrar no Extras, e ao abrir o item os arquivos ja
#   estao la. O controle (Imagem) continuou sem varrer -- entao o
#   resultado e do mecanismo, nao de coincidencia.
#
#   Core 4.0: o mesmo tratamento para a Imagem (home idx 5, 0x00D011AE).
#
# >>> O BUG DA 4.0/4.1, medido <<<
#   Entrar na Imagem pelo Extras fazia TUDO parar de abrir depois.
#
#   A cauda dos dois casos de fabrica nao e igual:
#
#     Livro  0x00D011A2  movs r3,#0xc  / b 0x00D01036
#                        0x00D01036: ldrh r0,[r4,#8]   origem DA MENSAGEM
#     Imagem 0x00D011EA  movs r3,#0x15 / movs r2,#0 / movs r1,#2
#                        movs r0,#1                    origem FIXA = home
#
#   A pagina GUARDA a origem (0x00D03AD8 `strh r0,[r5,#-8]`). Com "vim
#   da home" gravado, a camada APP e a ViewTask discordam de onde o
#   aparelho esta, e a guarda `msg->page == pagina corrente` passa a
#   falhar sempre.
#
#   Core 4.2: a Imagem vira REPLICA do caso de fabrica, com os mesmos
#   ramos de erro (que sao alcancados por endereco absoluto, frame
#   compativel), mas terminando em 0x00D01036 -- o trampolim que le a
#   origem da mensagem, igual ao do Livro digital.
DESTINOS = [
    (0x18, 1, None,     None,   "Gravacao"),
    (0x1A, 0, "fm",     None,   "Radio"),
    (0x0C, 0, 0x00D01162, "F", "Livro digital"),   # caso de fabrica, home idx 4
    (0x15, 0, "imagem_fab", None, "Imagem"),       # replica com a origem CERTA
    (0x23, 0, None,     None,   "Bluetooth"),
    (0x22, 1, None,     None,   "Pastas"),
]

CHECA_LISTA = 0x00D45CAC         # a verificacao que faltava
EBOOK_SCAN  = 0x00D00430         # atualiza a lista de livros
IMG_E8EC    = 0x00D0E8EC
IMG_E39C    = 0x00D0E39C
IMG_EDCC    = 0x00D3EDCC
IMG_SCAN    = 0x00D0D058         # atualiza a lista de imagens

# rotinas da preparacao do FM, medidas em 0x00D0113C
FM_STR     = 0x00D2108C          # get_string
FM_MBOX    = 0x00D0E2F0          # mostra a mensagem
FM_CFEC60  = 0x00CFEC60
FM_D45D50  = 0x00D45D50
FM_INIT    = 0x00D00510          # a inicializacao do tuner
FM_LIT_R1  = 0x00D0083D          # literais do bl 0x00D45D50
FM_LIT_R0  = 0x00C4C943


def bl(origem, destino):
    off = destino - (origem + 4)
    assert -(1 << 24) <= off < (1 << 24) and off % 2 == 0, "BL fora de alcance"
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    w1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    w2 = 0xD000 | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF)
    return w1.to_bytes(2, "little") + w2.to_bytes(2, "little")


def bw(origem, destino):
    b = bytearray(bl(origem, destino))
    b[3] &= ~0x40
    return bytes(b)


class Bloco:
    """Montador simples: acumula bytes e sabe o endereco de cada rotulo.

    Existe porque a Core 3.5/3.6 foram montadas com offsets contados a
    mao, e um `bhs` acabou caindo no meio de outra instrucao. Com isto,
    acrescentar uma rotina nao obriga a recontar nada.
    """
    def __init__(self, base):
        self.base, self.b, self.rot = base, bytearray(), {}
    def rotulo(self, nome):
        self.rot[nome] = self.base + len(self.b)
    @property
    def pos(self):
        return self.base + len(self.b)
    def h(self, v):
        self.b.extend(v.to_bytes(2, "little"))
    def w(self, v):
        self.b.extend(v.to_bytes(4, "little"))
    def bl(self, destino):
        self.b.extend(bl(self.pos, destino))
    def bw(self, destino):
        self.b.extend(bw(self.pos, destino))
    def alinha(self, n=4):
        while len(self.b) % n:
            self.h(0xBF00) if len(self.b) % 2 == 0 else self.b.append(0)


def montar():
    A = APP_ROUTER
    k = Bloco(A)

    k.h(0x89A2)                       # ldrh r2, [r4, #0xc]
    k.h(0x2A06)                       # cmp  r2, #6
    k.h(0xD219)                       # bhs  FIM
    k.h(0x4615)                       # mov  r5, r2
    k.h(0x4B0D)                       # ldr  r3, [pc,#0x34] -> &TAB_CHK
    k.h(0x5C9B)                       # ldrb r3, [r3, r2]
    k.h(0x2B00)                       # cmp  r3, #0
    k.h(0xD003)                       # beq  PREP
    k.bl(CHECA_CART)                  # bl   checa cartao
    k.h(0x2800)                       # cmp  r0, #0
    k.h(0xD00E)                       # beq  SEMCARTAO
    k.h(0x4B0A)                       # PREP: ldr r3,[pc,#0x28] -> &TAB_PREP
    k.b.extend(bytes.fromhex("53f82530"))   # ldr.w r3, [r3, r5, lsl #2]
    k.h(0x2B00)                       # cmp  r3, #0
    k.h(0xD000)                       # beq  ABRE
    k.h(0x4798)                       # blx  r3
    k.h(0x4B08)                       # ABRE: ldr r3,[pc,#0x20] -> &TAB_PAG
    k.h(0x5D5B)                       # ldrb r3, [r3, r5]
    k.h(0x2200)                       # movs r2, #0
    k.h(0x8961)                       # ldrh r1, [r4, #0xa]
    k.h(0x8920)                       # ldrh r0, [r4, #8]
    k.b.extend(bytes.fromhex("bde8f041"))   # pop.w {r4,r5,r6,r7,r8,lr}
    k.bw(ABRE_PAG)
    k.bw(SEM_CARTAO)                  # SEMCARTAO
    k.bw(RETORNO)                     # FIM
    k.h(0xBF00)
    assert k.pos == A + 0x40, hex(k.pos)
    k.w(A + 0x58); k.w(A + 0x60); k.w(A + 0x78)   # &TAB_CHK, &TAB_PREP, &TAB_PAG
    k.b.extend(b"\x00" * 0x0C)
    assert k.pos == A + 0x58
    k.b.extend(bytes(chk for _, chk, _, _, _ in DESTINOS)); k.b.extend(b"\x00\x00")
    assert k.pos == A + 0x60
    tab_prep_em = len(k.b)
    k.b.extend(b"\x00" * 24)           # TAB_PREP, preenchida no fim
    assert k.pos == A + 0x78
    k.b.extend(bytes(pg for pg, _, _, _, _ in DESTINOS)); k.b.extend(b"\x00\x00")

    # ---- sub-rotinas de preparacao, replicadas dos casos de fabrica ----
    k.rotulo("imagem_fab")            # replica de 0x00D011AE, cauda corrigida
    k.bl(CHECA_CART)                  # bl   cartao?
    k.h(0x2800)                       # cmp  r0, #0
    k.h(0xD101)                       # bne  +2 (segue)
    k.bw(0x00D01138)                  #      b.w  "sem cartao" (msg 0x2F)
    k.h(0x2000); k.bl(CHECA_LISTA)    # movs r0,#0 ; bl checa lista
    k.h(0x2800)                       # cmp  r0, #0
    k.h(0xD102)                       # bne  +4 (segue)
    k.h(0x20D7)                       # movs r0, #0xd7
    k.bw(0x00D01044)                  #      b.w  mostra mensagem
    k.h(0x2000); k.bl(IMG_E8EC)       # movs r0,#0 ; bl 0x00D0E8EC
    k.bl(IMG_E39C)                    # bl   0x00D0E39C
    k.h(0x2000); k.bl(IMG_EDCC)       # movs r0,#0 ; bl 0x00D3EDCC
    k.bl(IMG_SCAN)                    # bl   0x00D0D058  (a varredura)
    k.h(0x2800)                       # cmp  r0, #0
    k.h(0xDC02)                       # bgt  +4 (tem imagem: abre)
    k.h(0x2033)                       # movs r0, #0x33   "sem imagens"
    k.bw(0x00D01044)                  #      b.w  mostra mensagem
    k.h(0x2315)                       # movs r3, #0x15
    k.bw(0x00D01036)                  # b.w  trampolim: origem vem da MENSAGEM

    k.rotulo("fm")                    # de 0x00D0113C
    k.h(0xB500); k.h(0x20CA); k.bl(FM_STR)
    k.h(0x4601); k.h(0x2001); k.bl(FM_MBOX)
    k.h(0x2001); k.bl(FM_CFEC60)
    k.h(0x2214)
    # os dois `ldr rX,[pc,#imm]` sao emitidos com imm provisorio e
    # corrigidos depois que o pool existir -- contar offset a mao foi o
    # que errou na 3.6.
    p_r1, a_r1 = len(k.b), k.pos; k.h(0x4900)
    p_r0, a_r0 = len(k.b), k.pos; k.h(0x4800)
    k.bl(FM_D45D50); k.bl(FM_INIT); k.h(0xBD00); k.alinha()
    lit = k.pos
    k.w(FM_LIT_R1); k.w(FM_LIT_R0)
    for pos, addr, base_op, alvo in ((p_r1, a_r1, 0x4900, lit),
                                     (p_r0, a_r0, 0x4800, lit + 4)):
        imm = alvo - (((addr + 4) & ~3))
        assert 0 <= imm <= 0x3FC and imm % 4 == 0, hex(imm)
        k.b[pos:pos + 2] = (base_op | (imm // 4)).to_bytes(2, "little")

    def abre_como_a_fabrica(pagina):
        """A cauda dos casos da home: r0=1 (origem home), r1=2, r2=0."""
        k.h(0x2300 | pagina)          # movs r3, #<pagina>
        k.h(0x2200)                   # movs r2, #0
        k.h(0x2102)                   # movs r1, #2
        k.h(0x2001)                   # movs r0, #1
        k.b.extend(bytes.fromhex("bde8f041"))   # pop.w {r4,r5,r6,r7,r8,lr}
        k.bw(ABRE_PAG)                # b.w  0x00D0DAE0



    # preenche TAB_PREP agora que os rotulos existem
    for i, (_, _, prep, _, _) in enumerate(DESTINOS):
        if isinstance(prep, int):      # salto direto para caso de fabrica
            v = prep | 1
        else:
            v = (k.rot[prep] | 1) if prep else 0
        k.b[tab_prep_em + 4 * i: tab_prep_em + 4 * i + 4] = v.to_bytes(4, "little")
    return bytes(k.b)


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: patch_extras_app.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")
    # exige o roteador da 3.3 ja instalado
    if img[0x001A6000:0x001A6004] != bytes.fromhex("002254f8"):
        sys.exit("erro: o roteador LVGL da Core 3.3 nao esta na imagem")

    off = APP_ROUTER - BASE_XIP
    cod = montar()
    if any(b != 0xFF for b in img[off:off + len(cod)]):
        sys.exit(f"erro: {APP_ROUTER:#x} nao esta apagado")
    img[off:off + len(cod)] = cod
    oh = HOOK - BASE_XIP
    img[oh:oh + 4] = bw(HOOK, APP_ROUTER)
    open(sys.argv[2], "wb").write(img)

    print(f"despacho APP  {APP_ROUTER:#010x}  {len(cod)} bytes")
    print(f"gancho        {HOOK:#010x}  4 bytes (cmp r2,#2 / bhi)")
    print(f"  despacho de 3 -> 6 indices\n")
    for i, (pg, chk, prep, arg, nome) in enumerate(DESTINOS):
        a = ("  SALTA para o caso de fabrica" if arg == "F"
             else "  abre ela mesma" if arg == "T" else "  args da mensagem")
        print(f"  {i}  {nome:<14} -> pagina {pg:#04x}{a}"
              f"{('  + prep ' + prep) if isinstance(prep, str) else ''}"
              f"{'  (checa cartao)' if chk else ''}")
    print(f"\nescrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
