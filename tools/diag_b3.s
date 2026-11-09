@ B3: le o texto do rotulo 2 (o caminho da mensagem de 0xD084F8) e o
@ copia para ext+0x110. r0 = objeto do rotulo 2 ([view+8]), r2 = destino
@ (ext+0x110). Antes de qualquer deref: rotulo 0, texto 0 ou texto vazio
@ devolvem falha (0) sem ler mais nada. Copia ate 0xFF e devolve 1 se
@ comeca com "0:" e "/" ou "\".
    .syntax unified
    .thumb
    .text
    .global copia_path
    .type copia_path, %function
    .thumb_func
copia_path:
    cbz  r0, 4f
    ldr  r0, [r0, #0x24]
    cbz  r0, 4f
    ldrb r1, [r0]
    cbz  r1, 4f
    movs r3, #0
1:  ldrb r1, [r0, r3]
    strb r1, [r2, r3]
    cmp  r1, #0
    beq  3f
    adds r3, #1
    cmp  r3, #0xff
    bne  1b
3:  ldrb r1, [r0]
    cmp  r1, #0x30
    bne  4f
    ldrb r1, [r0, #1]
    cmp  r1, #0x3a
    bne  4f
    ldrb r1, [r0, #2]
    cmp  r1, #0x2f
    beq  5f
    cmp  r1, #0x5c
    beq  5f
4:  movs r0, #0
    bx   lr
5:  movs r0, #1
    bx   lr
    .size copia_path, . - copia_path
