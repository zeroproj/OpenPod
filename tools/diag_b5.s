@ B5: o tipo 5 da ViewTask abre o MP3 e/ou desenha a capa. Dois degraus:
@
@  B5a (0xDAAA00): so ABRE o arquivo, le 10 bytes e fecha. Se o cabecalho
@    comeca com "ID3", faz img_set_src(img, NULL); senao, cinza. Nao mexe no
@    monitor: se o f_open travar, o watchdog reinicia o aparelho.
@
@  B5b (0xDAAC00): compara o caminho com ext+0x10; igual nao faz nada. Se
@    mudou, copia para ext+0x10, pinta cinza, DESREGISTRA a ViewTask do
@    monitor, chama carrega_capa(ext), REGISTRA de volta e, no sucesso, faz
@    img_set_src(img, ext). Qualquer falha fica no cinza.
@
@  envia_path (0xDAAF00): a mesma rotina do B4 (rajada -> mensagem tipo 5).
@
@ TODOS os destinos de bx/blx levam o bit Thumb (|1). O teste estatico 71
@ confere o bit; o emulador nao aplica a checagem do Cortex-M.
    .syntax unified
    .thumb
    .text

@ ------------------------------------------------------------------ macros
.macro CHAMAR alvo
    movw ip, #((\alvo) + 1) & 0xFFFF
    movt ip, #((\alvo) + 1) >> 16
    blx ip
.endm

.macro CARREGAR reg, valor
    movw \reg, #(\valor) & 0xFFFF
    movt \reg, #(\valor) >> 16
.endm

.set DEGRAU_B, 0

@ ------------------------------------------------------------------ B5a
.if DEGRAU_B
    @ B5a ausente neste degrau: preenche ate +0x200
    .org 0x200
.else
    .global label_dispatch_b5a
    .type label_dispatch_b5a, %function
    .thumb_func
label_dispatch_b5a:
    cmp  r3, #5
    beq  5f
    adr  r0, tabela_a
    ldrb r0, [r0, r3]
    ldr  r0, [r5, r0]
    movw ip, #0x224f
    movt ip, #0x00d3
    bx   ip
tabela_a:
    .byte 0, 4, 8, 0x14, 0x18
    .balign 4
5:  @ r4 = msg, r5 = view, r6 = msg+0x14
    push {r4-r10, lr}
    sub  sp, #16
    movw r0, #0xce2c
    movt r0, #0x0081
    ldr  r0, [r0]
    cmp  r0, #0
    beq  b5a_fim
    ldr.w r0, [r0, #0xac]
    cmp  r0, #0
    beq  b5a_fim
    cmp  r0, r5
    bne  b5a_fim
    ldr  r0, [r5, #4]
    cmp  r0, #0
    beq  b5a_fim
    ldr  r7, [r5, #0x30]
    cmp  r7, #0
    beq  b5a_fim
    ldr  r8, [r7, #0xc]
    cmp  r8, #0
    beq  b5a_fim
    cmp  r6, #0
    beq  b5a_fim
    @ copia r6 -> ext+0x110 (r9)
    add.w r9, r7, #0x110
    movs r3, #0
b5a_copia:
    ldrb r0, [r6, r3]
    strb r0, [r9, r3]
    cbz  r0, b5a_val
    adds r3, #1
    cmp  r3, #0xff
    bne  b5a_copia
    movs r0, #0
    strb r0, [r9, r3]
b5a_val:
    ldrb r0, [r9]
    cmp  r0, #0x30
    bne  b5a_cinza
    ldrb r0, [r9, #1]
    cmp  r0, #0x3a
    bne  b5a_cinza
    ldrb r0, [r9, #2]
    cmp  r0, #0x2f
    beq  b5a_abre
    cmp  r0, #0x5c
    bne  b5a_cinza
b5a_abre:
    movs r0, #1
    movw r1, #0x25c
    CHAMAR 0x00CF7840              @ calloc(1, 0x25C)
    mov  r10, r0
    cmp  r10, #0
    beq  b5a_cinza
    mov  r0, r10
    mov  r1, r9
    movs r2, #1
    CHAMAR 0x00D777CC              @ f_open(fil, caminho, FA_READ)
    cmp  r0, #0
    bne  b5a_libera
    mov  r0, r10
    add  r1, sp, #0
    movs r2, #10
    add  r3, sp, #12
    CHAMAR 0x00D76854              @ f_read(fil, buf, 10, &br)
    cmp  r0, #0
    bne  b5a_fecha
    ldr  r0, [sp, #12]
    cmp  r0, #10
    bne  b5a_fecha
    ldrb r0, [sp, #0]
    cmp  r0, #0x49
    bne  b5a_fecha_cinza
    ldrb r0, [sp, #1]
    cmp  r0, #0x44
    bne  b5a_fecha_cinza
    ldrb r0, [sp, #2]
    cmp  r0, #0x33
    bne  b5a_fecha_cinza
    @ "ID3": fecha, libera e manda NULL (No data)
    mov  r0, r10
    CHAMAR 0x00D77C9C              @ f_close(fil)
    mov  r0, r10
    CHAMAR 0x00CF7884              @ free(fil)
    mov  r0, r8
    movs r1, #0
    CHAMAR 0x00D5D868              @ img_set_src(img, NULL)
    b    b5a_fim
b5a_fecha_cinza:
    mov  r0, r10
    CHAMAR 0x00D77C9C              @ f_close(fil)
b5a_libera_cinza:
    mov  r0, r10
    CHAMAR 0x00CF7884              @ free(fil)
    b    b5a_cinza
b5a_fecha:
    mov  r0, r10
    CHAMAR 0x00D77C9C              @ f_close(fil)
b5a_libera:
    mov  r0, r10
    CHAMAR 0x00CF7884              @ free(fil)
b5a_cinza:
    mov  r0, r8
    CARREGAR r1, 0x00DA8000        @ o descritor do quadrado cinza
    CHAMAR 0x00D5D868              @ img_set_src(img, 0xDA8000)
b5a_fim:
    add  sp, #16
    pop  {r4-r10, lr}
    movw ip, #0x22a1
    movt ip, #0x00d3
    bx   ip
    .size label_dispatch_b5a, . - label_dispatch_b5a
    .org 0x200
.endif

@ ------------------------------------------------------------------ B5b
.if DEGRAU_B
    .global label_dispatch_b5b
    .type label_dispatch_b5b, %function
    .thumb_func
label_dispatch_b5b:
    cmp  r3, #5
    beq  5f
    adr  r0, tabela_b
    ldrb r0, [r0, r3]
    ldr  r0, [r5, r0]
    movw ip, #0x224f
    movt ip, #0x00d3
    bx   ip
tabela_b:
    .byte 0, 4, 8, 0x14, 0x18
    .balign 4
5:  @ r4 = msg, r5 = view, r6 = msg+0x14
    push {r4-r10, lr}
    sub  sp, #16
    movw r0, #0xce2c
    movt r0, #0x0081
    ldr  r0, [r0]
    cmp  r0, #0
    beq  b5b_fim
    ldr.w r0, [r0, #0xac]
    cmp  r0, #0
    beq  b5b_fim
    cmp  r0, r5
    bne  b5b_fim
    ldr  r0, [r5, #4]
    cmp  r0, #0
    beq  b5b_fim
    ldr  r7, [r5, #0x30]
    cmp  r7, #0
    beq  b5b_fim
    ldr  r8, [r7, #0xc]
    cmp  r8, #0
    beq  b5b_fim
    cmp  r6, #0
    beq  b5b_fim
    @ copia r6 -> ext+0x110 (r9)
    add.w r9, r7, #0x110
    movs r3, #0
b5b_copia:
    ldrb r0, [r6, r3]
    strb r0, [r9, r3]
    cbz  r0, b5b_val
    adds r3, #1
    cmp  r3, #0xff
    bne  b5b_copia
    movs r0, #0
    strb r0, [r9, r3]
b5b_val:
    ldrb r0, [r9]
    cmp  r0, #0x30
    bne  b5b_cinza
    ldrb r0, [r9, #1]
    cmp  r0, #0x3a
    bne  b5b_cinza
    ldrb r0, [r9, #2]
    cmp  r0, #0x2f
    beq  b5b_compara
    cmp  r0, #0x5c
    bne  b5b_cinza
b5b_compara:
    @ mesmo caminho de ext+0x10? entao nao faz nada
    add.w r10, r7, #0x10
    movs r3, #0
b5b_cmp:
    ldrb r0, [r9, r3]
    ldrb r1, [r10, r3]
    cmp  r0, r1
    bne  b5b_dif
    cmp  r0, #0
    beq  b5b_fim
    adds r3, #1
    cmp  r3, #0xff
    bne  b5b_cmp
b5b_dif:
    @ copia r9 -> ext+0x10
    movs r3, #0
b5b_copia_old:
    ldrb r0, [r9, r3]
    strb r0, [r10, r3]
    cbz  r0, b5b_copiou
    adds r3, #1
    cmp  r3, #0xff
    bne  b5b_copia_old
    movs r0, #0
    strb r0, [r10, r3]
b5b_copiou:
    mov  r0, r8
    CARREGAR r1, 0x00DA8000
    CHAMAR 0x00D5D868              @ cinza antes de decodificar
    @ desregistra a ViewTask do monitor (task 3)
    movs r0, #3
    CHAMAR 0x00D6AE38              @ descritor da task 3
    cbz  r0, b5b_sem_mon
    mov  r10, r0
    mov  r0, r10
    CHAMAR 0x00D46ACC              @ unregister(descritor)
    str  r0, [sp, #0]
    b    b5b_mon_pronto
b5b_sem_mon:
    movs r0, #0
    str  r0, [sp, #0]
b5b_mon_pronto:
    mov  r0, r7
    CHAMAR 0x00DAA256              @ carrega_capa(ext)
    mov  r9, r0
    @ registra de volta se o unregister deu certo
    ldr  r0, [sp, #0]
    cbz  r0, b5b_sem_reg
    movs r0, #3
    CHAMAR 0x00D6AE38
    cbz  r0, b5b_sem_reg
    adds r0, #0x50
    CHAMAR 0x00D46A20              @ register(&task->monitor)
b5b_sem_reg:
    cmp  r9, #1
    bne  b5b_fim
    mov  r0, r8
    mov  r1, r7
    CHAMAR 0x00D5D868              @ img_set_src(img, ext)
    b    b5b_fim
b5b_cinza:
    mov  r0, r8
    CARREGAR r1, 0x00DA8000
    CHAMAR 0x00D5D868              @ img_set_src(img, 0xDA8000)
b5b_fim:
    add  sp, #16
    pop  {r4-r10, lr}
    movw ip, #0x22a1
    movt ip, #0x00d3
    bx   ip
    .size label_dispatch_b5b, . - label_dispatch_b5b
.else
    @ B5b ausente neste degrau: preenche ate +0x500
    .org 0x500
.endif

@ ------------------------------------------------------------------ envia_path
    .org 0x500
    .global envia_path
    .type envia_path, %function
    .thumb_func
envia_path:
    push {r4-r8, lr}
    add  r7, sp, #24          @ o sp do chamador (a rajada)
    mov  r6, r0               @ 1 = get_path ok
    @ guard: so a ViewTask envia o tipo 5 (0x8238F1 e o buffer global dela)
    ldr  r0, [r7, #0x14]      @ o lr salvo pela rajada
    bic  r0, r0, #1
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
    .balign 4
chamadores:
    .word 0x00D088E0, 0x00D08970, 0x00D08BEE, 0x00D0902C, 0x00D0EED4
vazio:
    .asciz ""
    .size envia_path, . - envia_path

    .org 0x600
