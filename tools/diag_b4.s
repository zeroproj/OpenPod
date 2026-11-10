@ B4: o caminho chega da MainTask numa mensagem propria (classe 3, tipo 5)
@ e a view aplica na capa. Duas rotinas:
@
@  label_dispatch (0xDAAA00): chamada no lugar do tbb de 0xD32242.
@    r3 = tipo, r4 = msg, r5 = view, r6 = msg+0x14. Tipos 0..4 continuam
@    indo para o comum 0xD3224E (set_text do rotulo). O tipo 5 copia o
@    caminho (r6) para ext+0x110, valida ("0:" + "/" ou "\", nao vazio,
@    ate 0xFF) e faz img_set_src(img, NULL) no sucesso ou
@    img_set_src(img, 0xDA8000) no invalido/vazio. Antes de qualquer
@    deref, guarda [0x81CE2C], [..+0xAC] == view, [view+4] (titulo),
@    [view+0x30] (ext), [ext+0xC] (img) e r6 (texto); nulo descarta.
@
@  envia_path (0xDAAA00+0x200): chamada no lugar do get_path/like getter
@    da rajada (0xCFF0C4). r0 = retorno do get_path (1 = ok), r4 = buf,
@    r5 = [0x81BC84]. So envia a mensagem tipo 5 quando o lr salvo pela
@    rajada e um dos chamadores da ViewTask (0x8238F1 e o buffer global
@    dos construtores de rotulo); nos chamadores da MainTask/MediaTask
@    (0xD00C28, 0xCFF212) pula a mensagem e mantem o like getter. Monta a
@    mensagem (texto = caminho ou vazio), envia por 0xD0D818, chama o
@    0xD0D880 (a fabrica termina assim) e, no sucesso, o like getter
@    0xD6DB90 com r1 = sp do chamador + 4. No sucesso volta para 0xCFF0C8;
@    na falha do get_path pula para 0xCFF0DE (o free da rajada).
@
@ TODOS os destinos de bx/blx levam o bit Thumb (|1): no Cortex-M, bx/blx
@ com bit0=0 gera UsageFault INVSTATE. O emulador (Unicorn) nao aplica essa
@ checagem; o teste estatico 71 confere o bit.
    .syntax unified
    .thumb
    .text

    .global label_dispatch
    .type label_dispatch, %function
    .thumb_func
label_dispatch:
    cmp  r3, #5
    beq  5f
    adr  r0, tabela
    ldrb r0, [r0, r3]
    ldr  r0, [r5, r0]
    movw ip, #0x224f
    movt ip, #0x00d3
    bx   ip
tabela:
    .byte 0, 4, 8, 0x14, 0x18
    .balign 4
5:  @ tipo 5: guardas de nulo (pagina, view, titulo, ext, img, texto)
    movw r0, #0xce2c
    movt r0, #0x0081
    ldr  r0, [r0]
    cbz  r0, 9f
    ldr.w r0, [r0, #0xac]
    cbz  r0, 9f
    cmp  r0, r5
    bne  9f
    ldr  r0, [r5, #4]
    cbz  r0, 9f
    ldr  r2, [r5, #0x30]
    cbz  r2, 9f
    ldr  r1, [r2, #0xc]
    cbz  r1, 9f
    cbz  r6, 9f
    @ copia r6 -> ext+0x110 (r2 = ext+0x110)
    add.w r2, r2, #0x110
    movs r3, #0
6:  ldrb r0, [r6, r3]
    strb r0, [r2, r3]
    cbz  r0, 7f
    adds r3, #1
    cmp  r3, #0xff
    bne  6b
    movs r0, #0
    strb r0, [r2, r3]
7:  @ valida o copiado: "0:" + "/" ou "\"
    ldrb r0, [r2]
    cmp  r0, #0x30
    bne  8f
    ldrb r0, [r2, #1]
    cmp  r0, #0x3a
    bne  8f
    ldrb r0, [r2, #2]
    cmp  r0, #0x2f
    beq  4f
    cmp  r0, #0x5c
    bne  8f
4:  movs r0, #0
    b    3f
8:  movw r0, #0x8000
    movt r0, #0x00da
3:  mov  r2, r0
    mov  r0, r1
    mov  r1, r2
    movw ip, #0xd869
    movt ip, #0x00d5
    blx  ip
9:  movw ip, #0x22a1
    movt ip, #0x00d3
    bx   ip
    .size label_dispatch, . - label_dispatch

    .balign 0x200
    .global envia_path
    .type envia_path, %function
    .thumb_func
envia_path:
    push {r4-r8, lr}
    add  r7, sp, #24          @ o sp do chamador (a rajada)
    mov  r6, r0               @ 1 = get_path ok
    @ guard: so a ViewTask envia o tipo 5 (0x8238F1 e o buffer global dela)
    ldr  r0, [r7, #0x14]      @ o lr salvo pela rajada
    adr  r1, chamadores
    movs r2, #5
1:  ldr  r3, [r1], #4
    cmp  r0, r3
    beq  2f
    subs r2, #1
    bne  1b
    b    4f                   @ fora da ViewTask: nao toca 0x8238F1
2:  movw r8, #0x38f1
    movt r8, #0x0082          @ msg = 0x008238F1
    mov  r0, r8
    movs r1, #0
    movw r2, #0x0414
    movw r3, #0x0bab
    blx  r3                   @ memset(msg, 0, 0x414)
    movs r0, #4
    strb r0, [r8]
    movs r0, #3
    strb r0, [r8, #2]
    movs r0, #5
    strb r0, [r8, #4]
    movs r0, #3
    strb r0, [r8, #6]         @ msg[6] = 3 (a classe)
    movs r0, #1
    strb r0, [r8, #0xc]       @ msg[0xc] = 1 (como a mensagem do rotulo 2)
    cmp  r6, #1
    bne  3f
    mov  r1, r4               @ o caminho
    b    5f
3:  adr  r1, vazio
5:  add.w r0, r8, #0x14
    movw r2, #0x03ff
    movw r3, #0xfd55
    movt r3, #0x00d9
    blx  r3                   @ strncpy(msg+0x14, texto, 0x3FF)
    add.w r0, r8, #0x14
    movw r3, #0x0aa3
    blx  r3                   @ strlen(msg+0x14)
    str  r0, [r8, #0x10]
    adds r0, #9
    strh r0, [r8, #0xa]
    mov  r0, r8
    movw r3, #0xd819
    movt r3, #0x00d0
    blx  r3                   @ 0xD0D818(msg)
    mov  r0, r8
    movw r3, #0xd881
    movt r3, #0x00d0
    blx  r3                   @ 0xD0D880 (a fabrica termina assim)
4:  cmp  r6, #1
    bne  6f
    mov  r0, r4
    add.w r1, r7, #4          @ o slot do like getter (sp+4)
    movw r3, #0xdb91
    movt r3, #0x00d6
    blx  r3                   @ 0xD6DB90(buf, sp+4)
    pop  {r4-r8, pc}
6:  pop  {r4-r8, lr}
    movw ip, #0xf0df
    movt ip, #0x00cf
    bx   ip                   @ falha: free e volta
chamadores:
    .word 0x00D088E0, 0x00D08970, 0x00D08BEE, 0x00D0902C, 0x00D0EED4
vazio:
    .asciz ""
    .size envia_path, . - envia_path
