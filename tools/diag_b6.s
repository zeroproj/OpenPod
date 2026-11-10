@ B6a/B6b da ficha 014: o arquivo sai da ViewTask e vai para a PreTask.
@
@  B6a (degrau a): a view e a do B4, byte a byte. O envia_path (0xDAAC00)
@    abre o caminho com f_open(caminho,1), le 10 bytes, fecha e libera.
@    "ID3" -> mensagem tipo 5 com o caminho (a view do B4 mostra "No data");
@    qualquer falha -> tipo 5 vazio (cinza).
@
@  B6b (degrau b): a view do B4 + o tipo 6. O envia_path aloca um contexto
@    temporario de 0x2210 B, copia o caminho para +0x110, chama o
@    carrega_capa(0xDAA256) da RC7 e, no sucesso, envia 8 mensagens tipo 6
@    de 1024 B (pixels de tmp+0x210). A view so copia os pixels para
@    ext+0x210+offset e, no ultimo pedaco, faz img_set_src(img, ext).
@    Nenhuma funcao de arquivo e alcancavel a partir da view.
@
@ TODOS os destinos de bx/blx levam o bit Thumb (|1). O lr salvo por `bl`
@ chega com bit0=1; a tabela de chamadores e comparada com o bit0 limpo.
    .syntax unified
    .thumb
    .text

    .set DEGRAU_B, 0

@ ------------------------------------------------------------------ view
    .global label_dispatch
    .type label_dispatch, %function
    .thumb_func
label_dispatch:
.if DEGRAU_B
    cmp  r3, #6
    beq  tipo6
.endif
    cmp  r3, #5
    beq  tipo5
    adr  r0, tabela
    ldrb r0, [r0, r3]
    ldr  r0, [r5, r0]
    movw ip, #0x224f
    movt ip, #0x00d3
    bx   ip
tabela:
    .byte 0, 4, 8, 0x14, 0x18
    .balign 4
tipo5:
    @ tipo 5 do B4: guardas e copia do caminho para ext+0x110
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
7:  ldrb r0, [r2]
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
.if DEGRAU_B
tipo6:
    @ tipo 6: copia 0x400 bytes de msg+0x14 para ext+0x210+offset
    movw r0, #0xce2c
    movt r0, #0x0081
    ldr  r0, [r0]
    cbz  r0, t6_out
    ldr.w r0, [r0, #0xac]
    cbz  r0, t6_out
    cmp  r0, r5
    bne  t6_out
    ldr  r0, [r5, #4]
    cbz  r0, t6_out
    ldr  r2, [r5, #0x30]
    cbz  r2, t6_out
    ldr  r1, [r2, #0xc]
    cbz  r1, t6_out
    cbz  r6, t6_out
    ldr  r3, [r4, #0x10]       @ offset do pedaco
    cmp  r3, #0x1c00
    bhi  t6_out
    movw r0, #0x3ff
    tst  r3, r0
    bne  t6_out
    add.w r2, r2, #0x210
    add  r2, r2, r3
    mov  ip, r6
    movw r1, #0x400
t6_copy:
    ldrb r0, [ip], #1
    strb r0, [r2], #1
    subs r1, #1
    bne  t6_copy
    cmp  r3, #0x1c00
    bne  t6_out
    ldr  r2, [r5, #0x30]
    ldr  r1, [r2, #0xc]
    mov  r0, r1
    mov  r1, r2
    movw ip, #0xd869
    movt ip, #0x00d5
    blx  ip                    @ img_set_src(img, ext) no ultimo pedaco
t6_out:
    movw ip, #0x22a1
    movt ip, #0x00d3
    bx   ip
.endif
    .size label_dispatch, . - label_dispatch

@ ------------------------------------------------------------------ envia_path
    .balign 0x200
    .global envia_path
    .type envia_path, %function
    .thumb_func
envia_path:
    push {r4-r8, lr}
    add  r7, sp, #24          @ o sp do chamador (a rajada)
    sub  sp, #16              @ 10 bytes do ID3 + 4 do contador
    mov  r6, r0               @ 1 = get_path ok
    @ guard: so os chamadores da ViewTask montam a mensagem
    ldr  r0, [r7, #0x14]      @ o lr salvo pela rajada
    bic  r0, r0, #1
    adr  r1, chamadores
    movs r2, #5
1:  ldr  r3, [r1], #4
    cmp  r0, r3
    beq  2f
    subs r2, #1
    bne  1b
    b    4f
2:  @ dentro da ViewTask: o trabalho de arquivo e aqui, na PreTask
.if DEGRAU_B
    cmp  r6, #1
    bne  b6b_vazio
    @ tmp = calloc(1, 0x2210)
    movs r0, #1
    movw r1, #0x2210
    movw ip, #0x7841
    movt ip, #0x00cf
    blx  ip
    cmp  r0, #0
    beq.w b6b_vazio
    mov  r8, r0
    @ copia o caminho (r4) para tmp+0x110
    add.w r2, r8, #0x110
    mov  r1, r4
    movs r3, #0
b6b_copia:
    ldrb r0, [r1, r3]
    strb r0, [r2, r3]
    cbz  r0, b6b_copiou
    adds r3, #1
    cmp  r3, #0xff
    bne  b6b_copia
    movs r0, #0
    strb r0, [r2, r3]
b6b_copiou:
    mov  r0, r8
    movw ip, #0xa257
    movt ip, #0x00da
    blx  ip                    @ carrega_capa(tmp)
    cmp  r0, #1
    bne  b6b_falha
    @ 8 pedacos de 1024 B
    movs r5, #0
b6b_pedaco:
    movw r0, #0x38f1
    movt r0, #0x0082
    movs r1, #0
    movw r2, #0x0414
    movw ip, #0x0bab
    blx  ip                    @ memset(msg, 0, 0x414)
    movw r0, #0x38f1
    movt r0, #0x0082
    movs r1, #4
    strb r1, [r0]
    movs r1, #3
    strb r1, [r0, #2]
    movs r1, #6
    strb r1, [r0, #4]          @ tipo 6
    movs r1, #3
    strb r1, [r0, #6]
    movs r1, #1
    strb r1, [r0, #0xc]
    str  r5, [r0, #0x10]       @ offset do pedaco
    add.w r1, r8, #0x210
    add  r1, r1, r5
    add.w r2, r0, #0x14
    movw r3, #0x400
b6b_copia_px:
    ldrb r0, [r1], #1
    strb r0, [r2], #1
    subs r3, #1
    bne  b6b_copia_px
    movw r0, #0x38f1
    movt r0, #0x0082
    movw r1, #0x0408
    strh r1, [r0, #0xa]        @ comprimento sem strlen
    movw ip, #0xd819
    movt ip, #0x00d0
    blx  ip                    @ 0xD0D818(msg)
    cmp  r0, #0
    bne  b6b_falha
    add.w r5, r5, #0x400
    cmp.w r5, #0x2000
    bne  b6b_pedaco
    mov  r0, r8
    movw ip, #0x7885
    movt ip, #0x00cf
    blx  ip                    @ free(tmp)
    b    4f
b6b_falha:
    mov  r0, r8
    movw ip, #0x7885
    movt ip, #0x00cf
    blx  ip                    @ free(tmp) em todos os caminhos
b6b_vazio:
    @ tipo 5 vazio (cinza)
    movw r0, #0x38f1
    movt r0, #0x0082
    movs r1, #0
    movw r2, #0x0414
    movw ip, #0x0bab
    blx  ip
    movw r0, #0x38f1
    movt r0, #0x0082
    movs r1, #4
    strb r1, [r0]
    movs r1, #3
    strb r1, [r0, #2]
    movs r1, #5
    strb r1, [r0, #4]
    movs r1, #3
    strb r1, [r0, #6]
    movs r1, #1
    strb r1, [r0, #0xc]
    movs r1, #9
    strh r1, [r0, #0xa]
    movw ip, #0xd819
    movt ip, #0x00d0
    blx  ip
    b    4f
.else
    cmp  r6, #1
    bne  b6a_vazio
    @ FIL = calloc(1, 0x25c)
    movs r0, #1
    movw r1, #0x25c
    movw ip, #0x7841
    movt ip, #0x00cf
    blx  ip
    cmp  r0, #0
    beq.w b6a_vazio
    mov  r8, r0
    @ f_open(FIL, caminho, 1)
    mov  r0, r8
    mov  r1, r4
    movs r2, #1
    movw ip, #0x77cd
    movt ip, #0x00d7
    blx  ip
    cmp  r0, #0
    bne  b6a_libera
    @ f_read(FIL, sp, 10, sp+0xC)
    mov  r0, r8
    mov  r1, sp
    movs r2, #10
    add  r3, sp, #0xC
    movw ip, #0x6855
    movt ip, #0x00d7
    blx  ip
    mov  r5, r0
    @ f_close(FIL) e free(FIL)
    mov  r0, r8
    movw ip, #0x7c9d
    movt ip, #0x00d7
    blx  ip
b6a_libera:
    mov  r0, r8
    movw ip, #0x7885
    movt ip, #0x00cf
    blx  ip
    cmp  r5, #0
    bne  b6a_vazio
    ldr  r0, [sp, #0xC]
    cmp  r0, #10
    bne  b6a_vazio
    ldrb r0, [sp]
    cmp  r0, #0x49
    bne  b6a_vazio
    ldrb r0, [sp, #1]
    cmp  r0, #0x44
    bne  b6a_vazio
    ldrb r0, [sp, #2]
    cmp  r0, #0x33
    bne  b6a_vazio
    @ tipo 5 com o caminho
    movw r0, #0x38f1
    movt r0, #0x0082
    movs r1, #0
    movw r2, #0x0414
    movw ip, #0x0bab
    blx  ip
    movw r0, #0x38f1
    movt r0, #0x0082
    movs r1, #4
    strb r1, [r0]
    movs r1, #3
    strb r1, [r0, #2]
    movs r1, #5
    strb r1, [r0, #4]
    movs r1, #3
    strb r1, [r0, #6]
    movs r1, #1
    strb r1, [r0, #0xc]
    add.w r0, r0, #0x14
    mov  r1, r4
    movw r2, #0x03ff
    movw ip, #0xfd55
    movt ip, #0x00d9
    blx  ip                    @ strncpy(msg+0x14, caminho, 0x3FF)
    movw r0, #0x38f1
    movt r0, #0x0082
    add.w r0, r0, #0x14
    movw ip, #0x0aa3
    blx  ip                    @ strlen(msg+0x14)
    movw r1, #0x38f1
    movt r1, #0x0082
    str  r0, [r1, #0x10]
    adds r0, #9
    strh r0, [r1, #0xa]
    mov  r0, r1
    movw ip, #0xd819
    movt ip, #0x00d0
    blx  ip
    b    4f
b6a_vazio:
    movw r0, #0x38f1
    movt r0, #0x0082
    movs r1, #0
    movw r2, #0x0414
    movw ip, #0x0bab
    blx  ip
    movw r0, #0x38f1
    movt r0, #0x0082
    movs r1, #4
    strb r1, [r0]
    movs r1, #3
    strb r1, [r0, #2]
    movs r1, #5
    strb r1, [r0, #4]
    movs r1, #3
    strb r1, [r0, #6]
    movs r1, #1
    strb r1, [r0, #0xc]
    movs r1, #9
    strh r1, [r0, #0xa]
    movw ip, #0xd819
    movt ip, #0x00d0
    blx  ip
.endif
4:  cmp  r6, #1
    bne  6f
    mov  r0, r4
    add.w r1, r7, #4          @ o slot do like getter (sp+4)
    movw ip, #0xdb91
    movt ip, #0x00d6
    blx  ip                    @ 0xD6DB90(buf, sp+4)
    add  sp, #16
    pop  {r4-r8, pc}
6:  add  sp, #16
    pop  {r4-r8, lr}
    movw ip, #0xf0df
    movt ip, #0x00cf
    bx   ip                    @ falha: free e volta
    .balign 4
chamadores:
    .word 0x00D088E0, 0x00D08970, 0x00D08BEE, 0x00D0902C, 0x00D0EED4
    .size envia_path, . - envia_path

    .org 0x600
