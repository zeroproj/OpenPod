@ diag_b3.s — o codigo novo do degrau B3 da ficha 011.
@
@ copia_path: chamado no lugar do get_path no TITULO (0x00DAA144).
@ r0 = destino (ext+0x110, RAM), r1 = origem (o caminho da mensagem que o
@ 0xD084F8 manda em +0x14; o page_music_play_label_process passa em r1).
@ Copia a origem para o destino (ate 0xFF bytes), confere que parece um
@ caminho (0x30 0x3a 0x5c/0x2f = "0:\" ou "0:/") e devolve 1 (valido) ou
@ 0 (invalido). Nao chama o get_path, nao abre arquivo, nao aloca.
@
@ Nada aqui escreve na flash XIP: o destino e o ext+0x110 (RAM), como no
@ get_path da fabrica.

    .syntax unified
    .thumb
    .text

    .global copia_path
    .type copia_path, %function
copia_path:
    movs    r2, #0
1:  ldrb    r3, [r1, r2]
    strb    r3, [r0, r2]
    cmp     r3, #0
    beq     2f
    adds    r2, #1
    cmp     r2, #0xff
    blo     1b
    movs    r3, #0
    movs    r2, #0xff
    strb    r3, [r0, r2]
2:  ldrb    r3, [r1]
    cmp     r3, #0x30
    bne     3f
    ldrb    r3, [r1, #1]
    cmp     r3, #0x3a
    bne     3f
    ldrb    r3, [r1, #2]
    cmp     r3, #0x5c
    beq     4f
    cmp     r3, #0x2f
    bne     3f
4:  movs    r0, #1
    bx      lr
3:  movs    r0, #0
    bx      lr
