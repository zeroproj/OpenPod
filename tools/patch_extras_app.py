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
DESTINOS = [
    (0x18, 1, 0, "Gravacao"),
    (0x1A, 0, 1, "Radio"),          # 1 = roda a preparacao do FM antes
    (0x0C, 1, 0, "Livro digital"),
    (0x15, 1, 0, "Imagem"),
    (0x23, 0, 0, "Bluetooth"),
    (0x22, 1, 0, "Pastas"),
]

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


def montar():
    c = bytearray()
    def h(v): c.extend(v.to_bytes(2, "little"))
    A = APP_ROUTER

    h(0x89A2)                          # 0x00  ldrh r2, [r4, #0xc]
    h(0x2A06)                          # 0x02  cmp  r2, #6
    h(0xD219)                          # 0x04  bhs  FIM (0x3a)
    h(0x4615)                          # 0x06  mov  r5, r2
    h(0x4B0D)                          # 0x08  ldr  r3, [pc,#0x34] -> &TAB_CHK
    h(0x5C9B)                          # 0x0A  ldrb r3, [r3, r2]
    h(0x2B00)                          # 0x0C  cmp  r3, #0
    h(0xD003)                          # 0x0E  beq  PREP (0x18)
    c += bl(A + 0x10, CHECA_CART)      # 0x10  bl   checa cartao
    h(0x2800)                          # 0x14  cmp  r0, #0
    h(0xD00E)                          # 0x16  beq  SEMCARTAO (0x36)
    # PREP (0x18)
    h(0x4B0A)                          # 0x18  ldr  r3, [pc,#0x28] -> &TAB_PREP
    c += bytes.fromhex("53f82530")     # 0x1A  ldr.w r3, [r3, r5, lsl #2]
    h(0x2B00)                          # 0x1E  cmp  r3, #0
    h(0xD000)                          # 0x20  beq  ABRE (0x24)
    h(0x4798)                          # 0x22  blx  r3     (r4/r5 sobrevivem)
    # ABRE (0x24) — igual a 3.4, que funcionou
    h(0x4B08)                          # 0x24  ldr  r3, [pc,#0x20] -> &TAB_PAG
    h(0x5D5B)                          # 0x26  ldrb r3, [r3, r5]
    h(0x2200)                          # 0x28  movs r2, #0
    h(0x8961)                          # 0x2A  ldrh r1, [r4, #0xa]
    h(0x8920)                          # 0x2C  ldrh r0, [r4, #8]
    c += bytes.fromhex("bde8f041")     # 0x2E  pop.w {r4,r5,r6,r7,r8,lr}
    c += bw(A + 0x32, ABRE_PAG)        # 0x32
    c += bw(A + 0x36, SEM_CARTAO)      # 0x36  SEMCARTAO
    c += bw(A + 0x3A, RETORNO)         # 0x3A  FIM
    h(0xBF00)                          # 0x3E  nop
    assert len(c) == 0x40, hex(len(c))
    c += (A + 0x58).to_bytes(4, "little")   # 0x40 -> &TAB_CHK
    c += (A + 0x60).to_bytes(4, "little")   # 0x44 -> &TAB_PREP
    c += (A + 0x78).to_bytes(4, "little")   # 0x48 -> &TAB_PAG
    c += b"\x00" * 0x0C                     # 0x4C  reservado
    c += bytes(chk for _, chk, _, _ in DESTINOS)   # 0x58  6 B
    c += b"\x00\x00"                         # 0x5E  pad
    for _, _, prep, _ in DESTINOS:          # 0x60  6 words
        c += ((A + 0x80) | 1).to_bytes(4, "little") if prep else b"\x00" * 4
    c += bytes(pg for pg, _, _, _ in DESTINOS)     # 0x78  6 B
    c += b"\x00\x00"                         # 0x7E  pad
    assert len(c) == 0x80, hex(len(c))

    # --- PREPARACAO DO FM (0x80) — replica de 0x00D0113C ---
    h(0xB500)                          # 0x80  push {lr}
    h(0x20CA)                          # 0x82  movs r0, #0xca
    c += bl(A + 0x84, FM_STR)          # 0x84  bl   get_string
    h(0x4601)                          # 0x88  mov  r1, r0
    h(0x2001)                          # 0x8A  movs r0, #1
    c += bl(A + 0x8C, FM_MBOX)         # 0x8C  bl   mostra mensagem
    h(0x2001)                          # 0x90  movs r0, #1
    c += bl(A + 0x92, FM_CFEC60)       # 0x92  bl   0x00CFEC60
    h(0x2214)                          # 0x96  movs r2, #0x14
    h(0x4903)                          # 0x98  ldr  r1, [pc,#0xc]  -> FM_LIT_R1
    h(0x4804)                          # 0x9A  ldr  r0, [pc,#0x10] -> FM_LIT_R0
    c += bl(A + 0x9C, FM_D45D50)       # 0x9C  bl   0x00D45D50
    c += bl(A + 0xA0, FM_INIT)         # 0xA0  bl   0x00D00510  <- o tuner
    h(0xBD00)                          # 0xA4  pop  {pc}
    h(0xBF00)                          # 0xA6  nop
    assert len(c) == 0xA8, hex(len(c))
    c += FM_LIT_R1.to_bytes(4, "little")    # 0xA8
    c += FM_LIT_R0.to_bytes(4, "little")    # 0xAC
    assert len(c) == 0xB0, hex(len(c))
    return bytes(c)


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
    for i, (pg, chk, prep, nome) in enumerate(DESTINOS):
        print(f"  {i}  {nome:<14} -> pagina {pg:#04x}"
              f"{'   + preparacao do FM' if prep else ''}"
              f"{'   (checa cartao)' if chk else ''}")
    print(f"\nescrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
