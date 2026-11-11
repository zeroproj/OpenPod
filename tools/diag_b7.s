@ B7a/B7b da ficha 015: a capa de 500x500 nao engasga a PreTask.
@
@  B7a (degrau a): o B6b exato + a regra de escala nova. O carrega_capa
@    (0xDAA256) compara as dimensoes com 0x38 (56) em vez de 0x40 (64):
@    500x500 decodifica em s=3 (62x62) e estica para 64x64.
@
@  B7b (degrau b): o B7a + pausa de scheduler. As chamadas de entrada
@    (0xDAA404) e saida (0xDAA476) do TJpgDec passam por dois wrappers no
@    lote (0xDAAE00 e 0xDAAE20). Cada wrapper chama o callback original,
@    salva o retorno e chama vPortYield (0xC43634) uma vez. N=1: nenhuma
@    leitura/decodificacao fica sem ponto de scheduler. Nao ha sleep.
@    A view tambem ganha a guarda do tipo 6: o tamanho em msg+0xA tem de
@    ser 0x408 antes de copiar; o cmp.w r3,#0x1c00 do B6b e desviado para
@    a guarda em 0xDAAE60 e volta para a copia em 0xDAAAC2.
@
@  O ponteiro de callback e trocado por LDR literal: o `orr r1,r1,#1`
@    original (4 B) vira `ldr.w r1,[pc,#...]` e o literal de 32 bits fica
@    em +0x450/+0x454. MOVW nao serve: ele zera a metade alta.
@
@  TODO destino indireto leva o bit Thumb (|1).
    .syntax unified
    .thumb
    .text

@ -------------------------------------------------- guarda da view (tipo 6)
@  O B6b testa o offset em [r4,#0x10] mas nao o tamanho em [r4,#0xA].
@  Este e o unico ponto da view que muda no B7b. O branch em +0xBC
@  substitui o cmp.w r3,#0x1c00; a guarda refaz o cmp e volta para +0xC2.
    .org 0x0bc
    .thumb_func
b7_view6_branch:
    b.w  b7_view6

@ ------------------------------------------------------------------ wrappers
    .org 0x400
    .thumb_func
b7_in:
    push {r4-r6, lr}
    mov  r4, r0
    movw ip, #0xa405          @ callback de entrada original 0xDAA404
    movt ip, #0x00da
    blx  ip
    b    b7_common

    .org 0x420
    .thumb_func
b7_out:
    push {r4-r6, lr}
    mov  r4, r0
    movw ip, #0xa477          @ callback de saida original 0xDAA476
    movt ip, #0x00da
    blx  ip
    b    b7_common

    .org 0x430
    .thumb_func
b7_common:
    mov  r5, r0
    movs r0, #1
    movw ip, #0x3635          @ vPortYield 0xC43634 (Thumb)
    movt ip, #0x00c4
    blx  ip
    mov  r0, r5
    pop  {r4-r6, pc}

@ ------------------------------------------------------------------ literais
    .org 0x450
    .word 0x00DAAE01          @ b7_in  | Thumb
    .word 0x00DAAE21          @ b7_out | Thumb

    .org 0x460
    .thumb_func
b7_view6:
    ldrh r0, [r4, #0xa]        @ tamanho da mensagem tipo 6
    cmp.w r0, #0x408           @ so a mensagem completa (0x408 B)
    bne  b7_view6_fail
    cmp.w r3, #0x1c00          @ o teste original do offset
    bhi  b7_view6_fail
    movw ip, #0xaac3           @ 0xDAAAC2 | Thumb: copia os 0x400 B
    movt ip, #0x00da
    bx   ip
b7_view6_fail:
    movw ip, #0xaafb           @ 0xDAAAFA | Thumb: epilogo da view
    movt ip, #0x00da
    bx   ip

    .org 0x600
