// capa_album.s — Reload 1.0 RC7 (ficha 007): a capa do álbum na Tocando Agora.
//
// Rotinas novas na área livre (lote 0x001A8000..0x001AB000, XIP 0x00DA8000).
// Sem compilador C: o montador é o clang (tools/asm.py), que só faz o
// Thumb-2 — a saída é reprodutível (catraca).
//
// O QUE ESTÁ AQUI
//
//   CRIA    (0x00DAA01C)  cria o fundo, o contexto (ext) e a imagem da capa
//   TITULO  (0x00DAA020)  avisa a capa quando o título da faixa muda
//   APAGA   (0x00DAA024)  devolve o contexto quando a imagem da capa morre
//
// A TABELA DE ENTRADAS (no lote, em 0x00DAA010/14/18)
//
//   0x00DAA010  b.w CRIA     — o alvo do `bl` do papel de parede
//   0x00DAA014  b.w TITULO   — o alvo do `b.w` do set_text
//   0x00DAA018  b.w APAGA    — o cb do LV_EVENT_DELETE, registrado como
//                              0x00DAA019 (o bit do Thumb)
//
// CONTRATO (ficha 007)
//
//   - CRIA(r0 = tela, r5 = view): devolve o fundo (o 1º lv_img da tela).
//   - TITULO(r0 = rótulo, r1 = texto): chama lv_label_set_text PRIMEIRO e uma
//     vez só; depois, se a view existir, se o rótulo for o do título e se o
//     contexto existir, procura a capa do MP3 e troca a imagem.
//   - APAGA(r0 = evento): se o código for LV_EVENT_DELETE (0x21), devolve o
//     contexto.
//
// REGRAS QUE O CÓDIGO CUMPRE
//
//   - r4..r11 preservados, pilha balanceada e alinhada em 8 bytes;
//   - nenhuma função fora da lista da ficha é chamada (só as do contrato);
//   - o contexto é próprio (o global 0x81CDE8 do visualizador de fotos não
//     é tocado);
//   - a leitura do MP3 nunca passa do fim do quadro APIC;
//   - o tamanho de quadro é conferido contra o resto da tag ANTES de
//     avançar o ponteiro (nunca se soma 10 + tam em 32 bits).
//
// NOTA SOBRE AS CHAMADAS
//
//   O clang monta um objeto relocável e não há linkador neste ambiente:
//   um `bl 0x00CF7840` sairia com o deslocamento errado (o assembler
//   assumiria a base 0 da seção). Por isso toda chamada para fora é feita
//   com movw/movt + blx (o bit 1 do endereço é o do Thumb).
//
// NOTA SOBRE O PONTEIRO DO ARQUIVO
//
//   A leitura do MP3 é sequencial, e o ponteiro do arquivo e o contador do
//   código andam juntos: quando um quadro é pulado, o salto é feito com
//   f_lseek (o offset de 64 bits vai em r2:r3). Antes do jd_prepare o
//   arquivo volta para o começo da imagem: o leitor do TJpgDec lê do
//   início, e o contador do leitor anda junto com o arquivo.

.syntax unified
.thumb

// ---------------------------------------------------------------- endereços
.set CALLOC,   0x00CF7840
.set FREE,     0x00CF7884
.set GET_PATH, 0x00CFEFC4
.set F_OPEN,   0x00D777CC
.set F_READ,   0x00D76854
.set F_LSEEK,  0x00D76C0A
.set F_CLOSE,  0x00D77C9C
.set JD_PREP,  0x00D10B20
.set JD_DEC,   0x00D11090
.set IMG_CR,   0x00D5D850
.set IMG_SRC,  0x00D5D868
.set OBJ_AL,   0x00D4A3A2
.set ADD_CB,   0x00D47064
.set LBL_TXT,  0x00D5ED94
.set MEMSET,   0x00000BAA
.set PAGINAS,  0x0081CE2C
.set AUDIO,    0x0081BC84
.set DSC_GRAY, 0x00DA8000
.set APAGA_CB, 0x00DAA019          // a entrada da tabela do APAGA (bit Thumb)

// ---------------------------------------------------------------- o contexto
// Os campos pequenos ficam NA FRENTE: assim todo deslocamento cabe nos
// 12 bits do Thumb (o do meio, os pixels, é o único grande).
.set EXT_TAM,    0x2210            // dsc(12) + img(4) + 2 caminhos(512) + pixels(8192)
.set EXT_DSC,    0x0000
.set EXT_IMG,    0x000C
.set EXT_PATH,   0x0010            // o caminho guardado (256 bytes)
.set EXT_NOVO,   0x0110            // o caminho novo (o buffer do get_path)
.set EXT_PIX,    0x0210            // os 64x64 pixels (8192 bytes)
.set FIL_TAM,    0x025C            // o FIL do FatFs (A14)
.set JD_TAM,     0x0138            // o JDEC (0x118) + o contexto (0x20)
.set CTX,        0x0118            // o contexto logo depois do JDEC
.set POOL_TAM,   0x0E00
.set JPEG_SO,    0xD8

// ------------------------------------------------------------------ macros
// CHAMAR alvo: bl para um endereço absoluto (sem linkador, ver o cabeçalho).
.macro CHAMAR alvo
    movw ip, #((\alvo) + 1) & 0xFFFF
    movt ip, #((\alvo) + 1) >> 16
    blx ip
.endm

// CARREGAR reg, valor: põe um endereço absoluto num registrador.
.macro CARREGAR reg, valor
    movw \reg, #(\valor) & 0xFFFF
    movt \reg, #(\valor) >> 16
.endm

// MAIS reg, base, valor: reg = base + valor (para valores grandes).
.macro MAIS reg, base, valor
    movw \reg, #(\valor)
    add \reg, \base, \reg
.endm

// PULAR fil, pos: f_lseek(fil, pos) — o offset de 64 bits vai em r2:r3.
.macro PULAR fil, pos
    mov r0, \fil
    mov r1, \pos
    mov r2, \pos
    movs r3, #0
    CHAMAR F_LSEEK
.endm

// ===================================================================
// A TABELA DE ENTRADAS (0x00DAA010/14/18) aponta para três trampolins
// de 4 bytes, em endereços FIXOS: assim o montador não precisa dizer
// onde cada rotina ficou.
// ===================================================================
    .align 2
CRIA:
    b.w corpo_cria
    .align 2
TITULO:
    b.w corpo_titulo
    .align 2
APAGA:
    b.w corpo_apaga
    .align 2

// ===================================================================
// CRIA — a capa começa aqui.
// ===================================================================
corpo_cria:
    push {r4-r11, lr}
    sub sp, #4
    mov r4, r0                  // r4 = a tela
                                // r5 = a view (vem do chamador)

    mov r0, r4
    CHAMAR IMG_CR               // o fundo (o 1º objeto: a capa fica acima)
    mov r6, r0

    movs r0, #1
    movw r1, #EXT_TAM
    CHAMAR CALLOC               // o contexto
    mov r7, r0

    cmp r7, #0
    beq sem_dsc                 // sem memória: o quadrado cinza fica
    movw r0, #0x0004            // o dsc: TRUE_COLOR 64x64
    movt r0, #0x0801
    str r0, [r7, #EXT_DSC]
    movw r0, #8192
    str r0, [r7, #EXT_DSC + 4]
    MAIS r0, r7, EXT_PIX
    str r0, [r7, #EXT_DSC + 8]

sem_dsc:
    mov r0, r4
    CHAMAR IMG_CR               // a imagem da capa
    mov r8, r0
    cmp r8, #0
    beq sem_objeto

    mov r0, r8
    CARREGAR r1, DSC_GRAY
    CHAMAR IMG_SRC

    mov r0, r8
    movs r1, #2
    movs r2, #0
    movs r3, #42
    CHAMAR OBJ_AL

    cmp r7, #0
    beq sem_ext                 // sem contexto: não há evento nem troca
    str r8, [r7, #EXT_IMG]      // o contexto guarda a imagem
    str r7, [r5, #0x30]         // a view guarda o contexto

    mov r0, r8
    CARREGAR r1, APAGA_CB
    movs r2, #0x21              // LV_EVENT_DELETE
    mov r3, r7
    CHAMAR ADD_CB
    b fim_cria

sem_ext:
    movs r0, #0
    str r0, [r5, #0x30]         // a view fica sem contexto

sem_objeto:
    mov r0, r7
    CHAMAR FREE                 // o contexto sem imagem não serve
    movs r0, #0
    str r0, [r5, #0x30]

fim_cria:
    mov r0, r6                  // devolve o fundo
    add sp, #4
    pop {r4-r11, pc}

// ===================================================================
// TITULO — o título da faixa mudou.
// ===================================================================
corpo_titulo:
    push {r4-r11, lr}
    sub sp, #4
    mov r4, r0                  // r4 = o rótulo
    mov r5, r1                  // r5 = o texto

    mov r0, r4
    mov r1, r5
    CHAMAR LBL_TXT              // PRIMEIRO, e uma vez só

    CARREGAR r0, PAGINAS
    ldr r0, [r0]                // a struct das páginas
    cmp r0, #0
    beq fim_titulo
    ldr r6, [r0, #0xAC]         // a view da página 4
    cmp r6, #0
    beq fim_titulo
    ldr r0, [r6, #4]            // o rótulo do título
    cmp r0, r4
    bne fim_titulo
    ldr r7, [r6, #0x30]         // o contexto
    cmp r7, #0
    beq fim_titulo

    // o caminho novo: limpa, pergunta e compara
    add r0, r7, #EXT_NOVO
    movs r1, #0
    movw r2, #256
    CHAMAR MEMSET

    CARREGAR r1, AUDIO
    ldrb r0, [r1]               // r0 = a origem
    ldr r1, [r1, #0x20]         // r1 = o índice da faixa
    add r2, r7, #EXT_NOVO       // r2 = o buffer do caminho
    CHAMAR GET_PATH             // get_path(origem, índice, buf)
    cmp r0, #0
    beq sem_caminho

    add r0, r7, #EXT_NOVO
    add r1, r7, #EXT_PATH
    bl comparou_caminho         // r0 = 1 se for a mesma faixa
    cmp r0, #0
    bne fim_titulo              // a mesma faixa: não faz nada

    add r0, r7, #EXT_NOVO
    add r1, r7, #EXT_PATH
    bl copia_caminho

    ldr r8, [r7, #EXT_IMG]
    mov r0, r8
    CARREGAR r1, DSC_GRAY
    CHAMAR IMG_SRC              // o quadrado cinza enquanto não há capa

    mov r0, r7
    bl carrega_capa             // r0 = 1 se deu certo
    cmp r0, #0
    beq fim_titulo

    ldr r8, [r7, #EXT_IMG]
    mov r0, r8
    mov r1, r7                  // o dsc do contexto
    CHAMAR IMG_SRC
    b fim_titulo

sem_caminho:
    add r0, r7, #EXT_PATH       // sem caminho: o guardado fica vazio
    movs r1, #0
    movw r2, #256
    CHAMAR MEMSET
    ldr r8, [r7, #EXT_IMG]
    mov r0, r8
    CARREGAR r1, DSC_GRAY
    CHAMAR IMG_SRC              // e o quadrado cinza

fim_titulo:
    add sp, #4
    pop {r4-r11, pc}

// comparou_caminho(r0 = a, r1 = b) -> r0 = 1 se forem iguais
comparou_caminho:
    push {r4, r5, r6, lr}
    mov r2, #0
cmp_loop:
    ldrb r3, [r0, r2]
    ldrb r4, [r1, r2]
    cmp r3, r4
    bne cmp_dif
    cmp r3, #0
    beq cmp_igual
    add r2, r2, #1
    cmp r2, #0xFF
    blo cmp_loop
cmp_igual:
    movs r0, #1
    pop {r4, r5, r6, pc}
cmp_dif:
    movs r0, #0
    pop {r4, r5, r6, pc}

// copia_caminho(r0 = de, r1 = para): copia até o 0 (no máximo 256 bytes)
copia_caminho:
    push {r4, r5, r6, lr}
    mov r4, r0
    mov r5, r1
    movs r6, #0
copia_loop:
    ldrb r2, [r4, r6]
    strb r2, [r5, r6]
    cmp r2, #0
    beq copia_fim
    add r6, r6, #1
    cmp r6, #0xFF
    blo copia_loop
copia_fim:
    pop {r4, r5, r6, pc}

// ===================================================================
// APAGA — a imagem da capa foi apagada.
// ===================================================================
corpo_apaga:
    push {r4-r11, lr}
    sub sp, #4
    ldrb r1, [r0, #8]           // o código do evento
    cmp r1, #0x21
    bne fim_apaga
    ldr r2, [r0, #0xC]          // o contexto (o user_data)
    cmp r2, #0
    beq fim_apaga
    CARREGAR r0, PAGINAS
    ldr r0, [r0]
    cmp r0, #0
    beq apaga_sem_view
    ldr r0, [r0, #0xAC]
    cmp r0, #0
    beq apaga_sem_view
    ldr r1, [r0, #0x30]         // o contexto da view
    cmp r1, r2
    bne fim_apaga
    movs r1, #0
    str r1, [r0, #0x30]         // a view não tem mais contexto
apaga_sem_view:
    mov r0, r2
    CHAMAR FREE
fim_apaga:
    add sp, #4
    pop {r4-r11, pc}

// ===================================================================
// carrega_capa(r0 = contexto) -> r0 = 1 se a capa entrou no contexto.
//
//   Abre o MP3, acha o 1º APIC, confere que o JPEG é baseline, decodifica
//   com o TJpgDec da fábrica (leitor próprio, limitado ao quadro) e escreve
//   os 64x64 pixels no contexto. Qualquer falha: quadrado cinza.
// ===================================================================
carrega_capa:
    push {r4-r11, lr}
    sub sp, #12
    mov r4, r0                  // r4 = o contexto
    movs r5, #0                 // r5 = o FIL
    movs r8, #0                 // r8 = o JDEC
    movs r9, #0                 // r9 = o pool
    movs r10, #0                // r10 = o arquivo está aberto?

    movs r0, #1
    movw r1, #FIL_TAM
    CHAMAR CALLOC
    mov r5, r0
    cmp r5, #0
    beq capa_falha

    mov r0, r5
    add r1, r4, #EXT_NOVO
    movs r2, #1                 // só leitura
    CHAMAR F_OPEN
    cmp r0, #0
    bne capa_falha
    movs r10, #1

    mov r0, r5
    bl procura_apic             // r0 = 1, r1 = o início, r2 = o fim
    cmp r0, #0
    beq capa_falha
    mov r6, r1                  // r6 = o início da imagem
    mov r7, r2                  // r7 = o fim da imagem

    movs r0, #1
    movw r1, #JD_TAM
    CHAMAR CALLOC
    mov r8, r0
    cmp r8, #0
    beq capa_falha

    movs r0, #1
    movw r1, #POOL_TAM
    CHAMAR CALLOC
    mov r9, r0
    cmp r9, #0
    beq capa_falha

    add r0, r8, #CTX            // o contexto do leitor
    str r5, [r0, #0]            // o FIL
    str r6, [r0, #4]            // a posição
    str r7, [r0, #8]            // o fim (nunca lê depois)
    MAIS r1, r4, EXT_PIX
    str r1, [r0, #0xC]          // a saída dos pixels

    PULAR r5, r6                // o leitor começa na imagem

    movs r0, #0
    str r0, [sp]                // o 5º argumento do jd_prepare: o device
    mov r0, r8
    adr r1, leitor
    orr r1, #1
    mov r2, r9
    movw r3, #POOL_TAM
    CHAMAR JD_PREP
    cmp r0, #0
    bne capa_falha

    ldrh r0, [r8, #0x1C]        // a largura
    ldrh r1, [r8, #0x1E]        // a altura
    cmp r0, #64
    blo capa_falha
    cmp r1, #64
    blo capa_falha

    // a escala: o maior de 0..3 com (w>>s) >= 64 e (h>>s) >= 64
    movs r11, #0                // s
    movs r2, #0
    str r2, [sp, #4]            // a melhor escala
escala_loop:
    cmp r11, #4
    bhs escala_pronto
    lsr r2, r0, r11
    cmp r2, #64
    blo escala_proximo
    lsr r2, r1, r11
    cmp r2, #64
    blo escala_proximo
    str r11, [sp, #4]           // a melhor = s
escala_proximo:
    add r11, r11, #1
    b escala_loop
escala_pronto:
    ldr r11, [sp, #4]           // r11 = a escala
    lsr r0, r0, r11             // r0 = W
    lsr r1, r1, r11             // r1 = H
    add r2, r8, #CTX
    strh r0, [r2, #0x10]        // o contexto do leitor
    strh r1, [r2, #0x12]

    mov r0, r8
    adr r1, saida
    orr r1, #1
    mov r2, r11
    CHAMAR JD_DEC
    cmp r0, #0
    bne capa_falha

    // deu certo: fecha e liberta tudo
    mov r0, r5
    CHAMAR F_CLOSE
    movs r10, #0
    mov r0, r5
    CHAMAR FREE
    mov r0, r8
    CHAMAR FREE
    mov r0, r9
    CHAMAR FREE
    movs r0, #1
    add sp, #12
    pop {r4-r11, pc}

capa_falha:
    cmp r10, #0
    beq capa_limpa
    mov r0, r5
    CHAMAR F_CLOSE
capa_limpa:
    mov r0, r5
    CHAMAR FREE
    mov r0, r8
    CHAMAR FREE
    mov r0, r9
    CHAMAR FREE
    movs r0, #0
    add sp, #12
    pop {r4-r11, pc}

// ===================================================================
// leitor(r0 = jd, r1 = buf, r2 = n) -> r0 = os bytes lidos
//
//   O leitor do TJpgDec da fábrica: lê n bytes no arquivo, ou pula n bytes
//   quando buf == 0. Nunca passa do fim da imagem (o limite está no
//   contexto), que é o que impede a leitura fora do quadro.
// ===================================================================
leitor:
    push {r4-r8, lr}
    mov r4, r0                  // r4 = o jd
    mov r5, r1                  // r5 = o buf
    mov r6, r2                  // r6 = n
    add r7, r4, #CTX            // r7 = o contexto
    ldr r0, [r7, #8]            // o fim
    ldr r1, [r7, #4]            // a posição
    sub r0, r0, r1              // o que resta
    cmp r0, #0
    blo leitor_nada
    cmp r0, r6
    blo leitor_limita
    b leitor_tem
leitor_limita:
    mov r6, r0                  // n = o que resta
leitor_tem:
    cmp r6, #0
    beq leitor_nada
    cmp r5, #0
    beq leitor_pula
    sub sp, #8                  // o contador do f_read
    ldr r0, [r7, #0]            // o FIL
    mov r1, r5
    mov r2, r6
    mov r3, sp
    CHAMAR F_READ
    ldr r0, [sp]
    add sp, #8
    ldr r1, [r7, #4]
    add r1, r1, r0
    str r1, [r7, #4]
    pop {r4-r8, pc}
leitor_pula:
    ldr r0, [r7, #0]            // o FIL
    ldr r1, [r7, #4]
    add r1, r1, r6
    mov r2, r1
    movs r3, #0
    CHAMAR F_LSEEK
    ldr r1, [r7, #4]
    add r1, r1, r6
    str r1, [r7, #4]
    mov r0, r6
    pop {r4-r8, pc}
leitor_nada:
    movs r0, #0
    pop {r4-r8, pc}

// ===================================================================
// saida(r0 = jd, r1 = o bitmap, r2 = o rect) -> r0 = 1
//
//   O TJpgDec da fábrica entrega a imagem reduzida em pedaços (um retângulo
//   por vez, RGB565 little-endian). A tela quer 64x64: o pixel (ox, oy) da
//   tela vem do pixel (ox*W/64, oy*H/64) da imagem reduzida — e com os
//   bytes trocados (LV_COLOR_16_SWAP).
//
//   Para não caber a imagem inteira na memória, cada pedaço é lido uma vez
//   só: as faixas de ox e oy que caem no retângulo são calculadas com
//   divisão (POR SOFTWARE, ver div_soft) e os pixels são copiados direto
//   para o contexto.
// ===================================================================
saida:
    push {r4-r11, lr}
    sub sp, #4
    sub sp, #40
    mov r4, r0                  // r4 = o jd
    mov r5, r1                  // r5 = o bitmap
    mov r6, r2                  // r6 = o rect
    add r7, r4, #CTX            // r7 = o contexto
    ldrh r8, [r6, #0]           // left
    ldrh r9, [r6, #2]           // right
    ldrh r10, [r6, #4]          // top
    ldrh r11, [r6, #6]          // bottom
    ldrh r0, [r7, #0x10]        // W
    str r0, [sp, #8]
    ldrh r0, [r7, #0x12]        // H
    str r0, [sp, #12]

    // ox_lo = (left*64 + W - 1) / W
    ldr r2, [sp, #8]            // W
    mov r1, r8
    lsls r1, r1, #6
    add r1, r1, r2
    subs r1, r1, #1
    mov r0, r1
    mov r1, r2
    bl div_soft
    str r0, [sp, #16]
    // ox_hi = ((right+1)*64 + W - 1) / W - 1
    ldr r2, [sp, #8]            // W
    add r1, r9, #1
    lsls r1, r1, #6
    add r1, r1, r2
    subs r1, r1, #1
    mov r0, r1
    mov r1, r2
    bl div_soft
    subs r0, r0, #1
    str r0, [sp, #20]
    // oy_lo = (top*64 + H - 1) / H
    ldr r2, [sp, #12]           // H
    mov r1, r10
    lsls r1, r1, #6
    add r1, r1, r2
    subs r1, r1, #1
    mov r0, r1
    mov r1, r2
    bl div_soft
    str r0, [sp, #24]
    // oy_hi = ((bottom+1)*64 + H - 1) / H - 1
    ldr r2, [sp, #12]           // H
    add r1, r11, #1
    lsls r1, r1, #6
    add r1, r1, r2
    subs r1, r1, #1
    mov r0, r1
    mov r1, r2
    bl div_soft
    subs r0, r0, #1
    str r0, [sp, #28]
    // a largura da linha do pedaço
    sub r1, r9, r8
    add r1, r1, #1
    str r1, [sp, #32]
    // a saída
    ldr r1, [r7, #0xC]
    str r1, [sp, #36]

saida_linha:
    ldr r0, [sp, #24]           // oy
    ldr r1, [sp, #28]
    cmp r0, r1
    bhi saida_fim
    // sy = (oy*H) >> 6
    ldr r1, [sp, #12]
    mul r2, r0, r1
    lsr r2, r2, #6
    // a linha de origem: (sy - top) * a largura
    sub r3, r2, r10
    ldr r1, [sp, #32]
    mul r3, r3, r1
    lsls r3, r3, #1
    add r4, r5, r3              // r4 = o começo da linha
    // o destino: out + oy*128 + ox_lo*2
    ldr r1, [sp, #36]
    lsls r2, r0, #7
    add r2, r1, r2              // r2 = o destino
    ldr r0, [sp, #16]           // ox
    lsls r1, r0, #1
    add r2, r2, r1              // e o começo da faixa de ox
saida_pixel:
    ldr r1, [sp, #20]
    cmp r0, r1
    bhi saida_pixel_fim
    // sx = (ox*W) >> 6
    ldr r1, [sp, #8]
    mul r6, r0, r1
    lsr r6, r6, #6
    sub r6, r6, r8              // o deslocamento dentro da linha
    lsls r6, r6, #1
    add r6, r4, r6              // o endereço de origem
    ldrb r7, [r6, #1]           // a cor com os bytes trocados
    strb r7, [r2, #0]
    ldrb r7, [r6, #0]
    strb r7, [r2, #1]
    add r2, r2, #2
    add r0, r0, #1
    b saida_pixel
saida_pixel_fim:
    ldr r0, [sp, #24]
    add r0, r0, #1
    str r0, [sp, #24]
    b saida_linha
saida_fim:
    movs r0, #1
    add sp, #40
    add sp, #4
    pop {r4-r11, pc}

// ===================================================================
// div_soft(r0 = o dividendo, r1 = o divisor) -> r0 = o quociente
//
//   DIVISÃO POR SOFTWARE, de propósito.
//
//   A divisão por hardware (udiv/sdiv) é OPCIONAL no ARMv7-M, e o
//   firmware de fábrica visível (0xC00000..0xDA0000, 1,75 MiB) NÃO TEM
//   NENHUMA ocorrência de udiv/sdiv: nada evidencia que o núcleo do
//   SL6801 implemente a instrução. O emulador (QEMU/unicorn) executa
//   udiv em qualquer ARMv7, então o verde dos testes não provaria nada
//   no aparelho — e um UsageFault no meio da reescala derrubaria a
//   Tocando Agora ao tocar qualquer MP3 com capa.
//
//   Aqui a divisão é o laço clássico: o dividendo é girado um bit por
//   vez (do mais alto para o mais baixo); o resto dobra e recebe o bit;
//   se o resto alcançar o divisor, ele subtrai e o quociente ganha o
//   bit. São 32 passos, com o dividendo < 2^23 e o divisor >= 64: sem
//   estouro de 32 bits (o resto é sempre < divisor antes de dobrar).
//
//   Preserva r4..r11 (o chamador, `saida`, guarda o jd, o bitmap e o
//   rect neles); r0 e r2 são destruídos, r1 e r3 saem do jeito que
//   entraram (o divisor e o resto).
// ===================================================================
div_soft:
    push {r4, lr}
    mov r2, #0                // o quociente
    mov r3, #0                // o resto
    movs r4, #32              // os 32 bits do dividendo
div_soft_loop:
    lsls r2, r2, #1           // o quociente dobra
    lsls r0, r0, #1           // o bit mais alto vai para o carry
    adcs r3, r3               // o resto = resto + resto + o bit (2*resto + bit)
    cmp r3, r1
    blo div_soft_sem
    sub r3, r3, r1            // o resto -= o divisor
    orr r2, r2, #1            // e o quociente ganha o bit
div_soft_sem:
    subs r4, r4, #1
    bne div_soft_loop
    mov r0, r2                // o quociente
    pop {r4, pc}

// ===================================================================
// procura_apic(r0 = fil) -> r0 = 1 (r1 = o início da imagem, r2 = o fim)
//
//   Lê a tag ID3v2 (v3 ou v4), procura o 1º quadro APIC, monta o corpo
//   (codificação, MIME, tipo, descrição) e devolve o alcance da imagem.
//
//   O tamanho de cada quadro é conferido contra o resto da tag ANTES de
//   avançar o ponteiro: é o que impede o laço infinito com um tamanho
//   hostil (0xFFFFFFF6) e a leitura fora do quadro.
//
//   O ponteiro do arquivo (r5) e o contador andam juntos: o cabeçalho e o
//   corpo são lidos em sequência, e um quadro que não é APIC é pulado com
//   f_lseek.
// ===================================================================
procura_apic:
    push {r4-r11, lr}
    sub sp, #4
    sub sp, #48
    mov r4, r0                  // r4 = o FIL
    movs r5, #0                 // r5 = a posição no arquivo

    // ---- o cabeçalho da tag (10 bytes)
    mov r0, r4
    add r1, sp, #8
    movs r2, #10
    bl le_n
    cmp r0, #10
    bne apic_falha

    ldrb r0, [sp, #8]
    cmp r0, #0x49               // 'I'
    bne apic_falha
    ldrb r0, [sp, #9]
    cmp r0, #0x44               // 'D'
    bne apic_falha
    ldrb r0, [sp, #10]
    cmp r0, #0x33               // '3'
    bne apic_falha
    ldrb r7, [sp, #11]          // a versão
    cmp r7, #3
    beq apic_versao
    cmp r7, #4
    bne apic_falha
apic_versao:
    ldrb r0, [sp, #13]          // as flags da tag
    tst r0, #0x80               // unsync
    bne apic_falha

    // ---- o tamanho da tag (synchsafe)
    ldrb r0, [sp, #14]
    cmp r0, #0x80
    bhs apic_falha
    ldrb r0, [sp, #15]
    cmp r0, #0x80
    bhs apic_falha
    ldrb r0, [sp, #16]
    cmp r0, #0x80
    bhs apic_falha
    ldrb r0, [sp, #17]
    cmp r0, #0x80
    bhs apic_falha
    ldrb r0, [sp, #14]
    ldrb r1, [sp, #15]
    ldrb r2, [sp, #16]
    ldrb r3, [sp, #17]
    lsls r0, r0, #21
    orr r0, r0, r1, lsl #14
    orr r0, r0, r2, lsl #7
    orr r0, r0, r3
    add r6, r0, #10             // r6 = o fim da tag
    movs r5, #10                // a posição depois do cabeçalho

    // ---- o cabeçalho estendido?
    ldrb r0, [sp, #13]
    tst r0, #0x40
    beq apic_quadros

    mov r0, r4
    add r1, sp, #44
    movs r2, #4
    bl le_n
    cmp r0, #4
    bne apic_falha
    cmp r7, #4
    beq apic_ext_v4
    ldrb r0, [sp, #44]          // v2.3: BE32, sem os 4 bytes do tamanho
    ldrb r1, [sp, #45]
    ldrb r2, [sp, #46]
    ldrb r3, [sp, #47]
    lsls r0, r0, #24
    orr r0, r0, r1, lsl #16
    orr r0, r0, r2, lsl #8
    orr r0, r0, r3
    add r0, r0, #4
    add r5, r5, r0
    b apic_ext_pronto
apic_ext_v4:
    ldrb r0, [sp, #44]          // v2.4: synchsafe, e já inclui os 4 bytes
    cmp r0, #0x80
    bhs apic_falha
    ldrb r0, [sp, #45]
    cmp r0, #0x80
    bhs apic_falha
    ldrb r0, [sp, #46]
    cmp r0, #0x80
    bhs apic_falha
    ldrb r0, [sp, #47]
    cmp r0, #0x80
    bhs apic_falha
    ldrb r0, [sp, #44]
    ldrb r1, [sp, #45]
    ldrb r2, [sp, #46]
    ldrb r3, [sp, #47]
    lsls r0, r0, #21
    orr r0, r0, r1, lsl #14
    orr r0, r0, r2, lsl #7
    orr r0, r0, r3
    add r5, r5, r0
apic_ext_pronto:
    cmp r5, r6
    bhs apic_falha             // o cabeçalho estendido não cabe na tag
    PULAR r4, r5

// ---- os quadros
apic_quadros:
    cmp r5, r6
    bhs apic_fim                // a tag acabou
    sub r11, r6, r5             // o resto da tag
    cmp r11, #10
    blo apic_fim                // não cabe um cabeçalho de quadro

    mov r0, r4
    add r1, sp, #24
    movs r2, #10
    bl le_n
    cmp r0, #10
    bne apic_falha
    add r5, r5, #10             // a posição depois do cabeçalho do quadro

    ldrb r0, [sp, #24]
    cmp r0, #0
    beq apic_fim                // o ID começa com 0: é padding

    // ---- o tamanho do quadro
    cmp r7, #4
    beq apic_tam_v4
    ldrb r0, [sp, #28]          // v2.3: BE32 normal
    ldrb r1, [sp, #29]
    ldrb r2, [sp, #30]
    ldrb r3, [sp, #31]
    lsls r0, r0, #24
    orr r0, r0, r1, lsl #16
    orr r0, r0, r2, lsl #8
    orr r0, r0, r3
    b apic_tam_pronto
apic_tam_v4:
    ldrb r1, [sp, #28]          // v2.4: synchsafe (synchsafe inválido = cinza)
    cmp r1, #0x80
    bhs apic_falha
    ldrb r1, [sp, #29]
    cmp r1, #0x80
    bhs apic_falha
    ldrb r1, [sp, #30]
    cmp r1, #0x80
    bhs apic_falha
    ldrb r1, [sp, #31]
    cmp r1, #0x80
    bhs apic_falha
    ldrb r0, [sp, #28]
    ldrb r1, [sp, #29]
    ldrb r2, [sp, #30]
    ldrb r3, [sp, #31]
    lsls r0, r0, #21
    orr r0, r0, r1, lsl #14
    orr r0, r0, r2, lsl #7
    orr r0, r0, r3
apic_tam_pronto:
    mov r8, r0                  // r8 = o tamanho do quadro

    // ---- o quadro cabe na tag? (o resto MENOS o cabeçalho já lido)
    sub r11, r6, r5
    cmp r8, r11
    bhi apic_falha              // o quadro passa do fim da tag

    // ---- é APIC? (os QUATRO bytes do id: 'A','P','I','C')
    ldrb r0, [sp, #24]
    cmp r0, #0x41               // 'A'
    bne apic_proximo
    ldrb r0, [sp, #25]
    cmp r0, #0x50               // 'P'
    bne apic_proximo
    ldrb r0, [sp, #26]
    cmp r0, #0x49               // 'I'
    bne apic_proximo
    ldrb r0, [sp, #27]
    cmp r0, #0x43               // 'C'
    bne apic_proximo
    b apic_corpo

apic_proximo:
    add r5, r5, r8              // pula o corpo do quadro (sem estouro: o
    PULAR r4, r5                // quadro cabe na tag, checado acima)
    b apic_quadros

// ---- o corpo do APIC
apic_corpo:
    ldrb r9, [sp, #33]          // as flags do quadro
    cmp r7, #4
    bne apic_flags_v3
    and r9, r9, #0x4F           // v2.4: grupo/compressão/cifra/unsync/DLI
    b apic_flags_pronto
apic_flags_v3:
    and r9, r9, #0xE0           // v2.3: comprimido/cifrado/grupo
apic_flags_pronto:
    cmp r9, #0
    bne apic_falha

    add r11, r5, r8             // r11 = o fim do quadro
    cmp r5, r11
    bhs apic_falha

    mov r0, r4
    add r1, sp, #40
    movs r2, #1
    bl le_n
    cmp r0, #1
    bne apic_falha
    add r5, r5, #1
    ldrb r0, [sp, #40]          // a codificação
    cmp r0, #3
    bhi apic_falha
    mov r9, r0

apic_mime:
    cmp r5, r11
    bhs apic_falha
    mov r0, r4
    add r1, sp, #40
    movs r2, #1
    bl le_n
    cmp r0, #1
    bne apic_falha
    add r5, r5, #1
    ldrb r0, [sp, #40]
    cmp r0, #0
    bne apic_mime

    cmp r5, r11                // o tipo da imagem
    bhs apic_falha
    mov r0, r4
    add r1, sp, #40
    movs r2, #1
    bl le_n
    cmp r0, #1
    bne apic_falha
    add r5, r5, #1

    cmp r9, #1                 // a descrição: UTF-16 (1 ou 2) ou Latin-1/UTF-8
    beq apic_desc16
    cmp r9, #2
    beq apic_desc16
apic_desc0:
    cmp r5, r11
    bhs apic_falha
    mov r0, r4
    add r1, sp, #40
    movs r2, #1
    bl le_n
    cmp r0, #1
    bne apic_falha
    add r5, r5, #1
    ldrb r0, [sp, #40]
    cmp r0, #0
    beq apic_imagem
    b apic_desc0
apic_desc16:
    sub r0, r11, r5
    cmp r0, #2
    blo apic_falha
    mov r0, r4
    add r1, sp, #44
    movs r2, #2
    bl le_n
    cmp r0, #2
    bne apic_falha
    add r5, r5, #2
    ldrb r0, [sp, #44]
    ldrb r1, [sp, #45]
    orr r0, r0, r1, lsl #8
    cmp r0, #0
    bne apic_desc16

// ---- a imagem: tem de começar com FF D8
apic_imagem:
    sub r0, r11, r5
    cmp r0, #2
    blo apic_falha
    mov r0, r4
    add r1, sp, #44
    movs r2, #2
    bl le_n
    cmp r0, #2
    bne apic_falha
    add r5, r5, #2
    ldrb r0, [sp, #44]
    cmp r0, #0xFF
    bne apic_falha
    ldrb r0, [sp, #45]
    cmp r0, #JPEG_SO
    bne apic_falha
    sub r10, r5, #2             // r10 = o início da imagem (o FFD8)

    // ---- só baseline: procura o SOF (a posição é a DEPOIS do FFD8: o
    // leitor do arquivo e o contador do código andam juntos)
    mov r0, r4
    mov r1, r5
    mov r2, r11
    bl varre_marcadores
    cmp r0, #0
    beq apic_falha
    mov r1, r10                 // r1 = o início da imagem
    mov r2, r11                 // r2 = o fim da imagem
    movs r0, #1
    add sp, #48
    add sp, #4
    pop {r4-r11, pc}

apic_fim:
    movs r0, #0                  // sem APIC
    add sp, #48
    add sp, #4
    pop {r4-r11, pc}

apic_falha:
    movs r0, #0
    add sp, #48
    add sp, #4
    pop {r4-r11, pc}

// ===================================================================
// varre_marcadores(r0 = fil, r1 = a posição, r2 = o fim) -> r0 = 1
//
//   Percorre os marcadores do JPEG até o SOF: o C0 (baseline) serve, o
//   C1..CF (menos C4, C8 e CC) e o D9/DA antes do SOF são recusados.
//
//   A posição (r5) é a posição do arquivo: o que é lido avança o arquivo, e
//   o salto de um segmento é feito com f_lseek para a mesma posição.
// ===================================================================
varre_marcadores:
    push {r4-r11, lr}
    sub sp, #4
    sub sp, #8
    mov r4, r0                  // r4 = o FIL
    mov r5, r1                  // r5 = a posição
    mov r6, r2                  // r6 = o fim

varre_loop:
    cmp r5, r6
    bhs varre_falha
    mov r0, r4
    add r1, sp, #8
    movs r2, #1
    bl le_n
    cmp r0, #1
    bne varre_falha
    add r5, r5, #1
    ldrb r0, [sp, #8]
    cmp r0, #0xFF               // o byte de preenchimento
    bne varre_falha

varre_marcador:
    cmp r5, r6
    bhs varre_falha
    mov r0, r4
    add r1, sp, #8
    movs r2, #1
    bl le_n
    cmp r0, #1
    bne varre_falha
    add r5, r5, #1
    ldrb r0, [sp, #8]
    cmp r0, #0xFF
    beq varre_loop              // outro byte de preenchimento

    cmp r0, #0xC0               // SOF0: baseline
    beq varre_baseline
    cmp r0, #0xD9               // EOI antes do SOF
    beq varre_falha
    cmp r0, #0xDA               // SOS antes do SOF
    beq varre_falha
    cmp r0, #0xC1               // C1..CF: só C4, C8 e CC passam
    blo varre_sem_tamanho
    cmp r0, #0xD0
    bhs varre_acima_d0
    cmp r0, #0xC4
    beq varre_com_tamanho
    cmp r0, #0xC8
    beq varre_com_tamanho
    cmp r0, #0xCC
    beq varre_com_tamanho
    b varre_falha
varre_acima_d0:
    cmp r0, #0xD8               // SOI (e os RSTn) não têm tamanho
    beq varre_sem_tamanho
    cmp r0, #0xD0
    blo varre_sem_tamanho
    b varre_com_tamanho

varre_sem_tamanho:
    b varre_loop

varre_com_tamanho:
    sub r0, r6, r5
    cmp r0, #2
    blo varre_falha
    mov r0, r4
    add r1, sp, #8
    movs r2, #2
    bl le_n
    cmp r0, #2
    bne varre_falha
    add r5, r5, #2
    ldrb r0, [sp, #8]
    ldrb r1, [sp, #9]
    lsls r0, r0, #8
    orr r0, r0, r1
    cmp r0, #2
    blo varre_falha
    sub r0, r0, #2              // o que sobra do segmento
    add r5, r5, r0
    cmp r5, r6
    bhs varre_falha
    PULAR r4, r5
    b varre_loop

varre_baseline:
    movs r0, #1
    add sp, #8
    add sp, #4
    pop {r4-r11, pc}

varre_falha:
    movs r0, #0
    add sp, #8
    add sp, #4
    pop {r4-r11, pc}

// ===================================================================
// le_n(r0 = fil, r1 = o buf, r2 = n) -> r0 = os bytes lidos
// ===================================================================
le_n:
    push {r4, r5, r6, lr}
    sub sp, #8
    mov r4, r0
    mov r5, r1
    mov r6, r2
    mov r0, r4
    mov r1, r5
    mov r2, r6
    mov r3, sp
    CHAMAR F_READ
    ldr r0, [sp]
    add sp, #8
    pop {r4, r5, r6, pc}
