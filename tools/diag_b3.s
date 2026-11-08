@ diag_b3.s — o codigo novo do degrau B3 da ficha 011.
@
@ guarda_path: chamado no lugar do bl 0xD084F8 da rajada do play
@ (0x00D088D8). Copia o caminho (r0) para o global 0x00DAAB00 e chama
@ o 0xD084F8 de verdade (a mensagem de caminho continua sendo enviada).
@
@ le_global: chamado no lugar do get_path no TITULO (0x00DAA144).
@ Copia o global para ext+0x110, confere que parece um caminho
@ (0x30 0x3a 0x5c = "0:\") e devolve 1 (valido) ou 0 (invalido).
@
@ O global fica em 0x00DAAB00 (arquivo 0x001AAB00), fora deste .text.

    .syntax unified
    .thumb
    .text

    .global guarda_path
    .type guarda_path, %function
guarda_path:
    push    {r4, lr}
    mov     r4, r0
    cbz     r4, 3f
    movw    r1, #0xab00
    movt    r1, #0xda
    movs    r2, #0
1:  ldrb    r3, [r4, r2]
    strb    r3, [r1, r2]
    cmp     r3, #0
    beq     2f
    adds    r2, #1
    cmp     r2, #0xff
    blo     1b
    movs    r3, #0
    movs    r2, #0xff
    strb    r3, [r1, r2]
2:  mov     r0, r4
3:  movw    ip, #0x84f9
    movt    ip, #0xd0
    blx     ip
    pop     {r4, pc}

    .org    0x40
    .global le_global
    .type le_global, %function
le_global:
    movw    r1, #0xab00
    movt    r1, #0xda
    add.w   r2, r7, #0x110
    movs    r3, #0
1:  ldrb    r0, [r1, r3]
    strb    r0, [r2, r3]
    cmp     r0, #0
    beq     2f
    adds    r3, #1
    cmp     r3, #0xff
    blo     1b
    movs    r0, #0
    movs    r3, #0xff
    strb    r0, [r2, r3]
2:  ldrb    r0, [r2]
    cmp     r0, #0x30
    bne     3f
    ldrb    r0, [r2, #1]
    cmp     r0, #0x3a
    bne     3f
    ldrb    r0, [r2, #2]
    cmp     r0, #0x5c
    beq     4f
    cmp     r0, #0x2f
    bne     3f
4:  movs    r0, #1
    bx      lr
3:  movs    r0, #0
    bx      lr
