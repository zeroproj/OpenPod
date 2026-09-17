# EXTRAS — o plano, segunda tentativa

> Aberto em 2026-09-17, sobre a **Core 3.0.1**, depois do laudo
> `docs/INCIDENTE_3.1.2.md`.
>
> **Nada aqui foi implementado.** É plano, e desta vez é plano *medido*.

---

## 1. Por que as três tentativas falharam

| Tentativa | O que fez | Por que quebrou |
|---|---|---|
| 3.1 | reescreveu o handler de clique no lugar | apagou `0x00D2F01A`, a saída da função |
| 3.1.1 | trocou 6 bytes da tabela de remap | mandava Rádio e Gravação para os índices **3** e **9** da home, que são **casos de erro** |
| 3.1.2 | novo módulo + mini-handler | apagou 5 destinos de desvio de `page1_process` |

O erro comum: **as três mandaram mensagem para a camada APP e brigaram
com a guarda `msg->page == página corrente`.** Nenhuma precisava.

---

## 2. O estado real da 3.0.1  · CONFIRMADO

O handler de clique do Extras (`0x00D2EF60`) está **idêntico ao de
fábrica**. Ele é um `lv_event_cb`:

```asm
0x00D2EF76  bl   #0xD47034        ; lv_event_get_code
0x00D2EF7A  cmp  r0, #0xd
0x00D2EF7C  bne  #0xD2F01A        ; não é o evento -> sai
...                               ; switch por código de tecla
0x00D2EFDE  ...                   ; caso 0x0A = ENTER
0x00D2EFF2  bl   #0xD47648        ; objeto em foco -> r0
0x00D2EFF6  ldr  r3, [r4]         ; ┐
0x00D2EFF8  cmp  r0, r3           ; │ cadeia desenrolada
0x00D2EFFA  beq  #0xD2F01C        ; │ de comparação
0x00D2EFFC  ldr  r3, [r4, #4]     ; │ contra TRÊS
0x00D2EFFE  cmp  r0, r3           ; │ ponteiros de botão
0x00D2F000  beq  #0xD2F020        ; │
0x00D2F002  ldr  r3, [r4, #8]     ; │
0x00D2F004  cmp  r0, r3           ; │
0x00D2F006  bne  #0xD2F01A        ; ┘ nenhum casou -> SAI SEM FAZER NADA
0x00D2F008  movs r4, #2           ; índice do item
0x00D2F00A  movs r3, #4
0x00D2F00C  mov  r1, r3
0x00D2F00E  mov  r2, r4
0x00D2F010  movs r0, #0x53
0x00D2F012  bl   #0xD23510        ; monta e posta mensagem
0x00D2F016  ldr  r3, [pc, #0x78]  ; &0x00823D84
0x00D2F018  strb r4, [r3]         ; lembra o item selecionado
0x00D2F01A  pop  {r4, r5, r6, pc}
```

`r4 = [r3, #0x1E8]` é o vetor de ponteiros dos botões da página.

**A página de fábrica tem TRÊS itens. A 3.0.1 desenha SEIS.** Os itens
3, 4 e 5 não casam com nenhum dos três ponteiros, caem no
`bne #0xD2F01A` e a função retorna sem fazer nada.

> É por isso que nada abre. Não é corrupção de heap, não é a guarda de
> página, não é a tabela de remap. **É uma cadeia de comparação com três
> elos para uma lista de seis.**

---

## 3. A primitiva de abrir página  · CONFIRMADO

`page1_process` despacha os itens da home por uma `tbh` em `0x00D00FBA`,
com 12 entradas em `0x00D00FBE`:

| idx | corpo | o que faz |
|---|---|---|
| 0 | `0x00D00FD6` | checa cartão, mostra mensagem |
| 1 | `0x00D01066` | checa cartão + lista, conta itens |
| 2 | `0x00D010F6` | **a 3.0.1 reescreveu: abre a página 0x53 (Extras)** |
| 3 | `0x00D0113C` | mensagem `0xCA` — **não abre nada** |
| 4 | `0x00D01162` | checa cartão + lista |
| 5 | `0x00D011AE` | checa cartão, mensagem |
| 6 | `0x00D012D6` | abre página **`0x23`**, sub 6 |
| 7 | `0x00D0123A` | abre página **`0x28`**, sub 7 |
| 8 | `0x00D0128C` | checa cartão + lista |
| 9 | `0x00D012E2` | **caso de erro** — e também o default do `bhi.w` |
| 10 | `0x00D01202` | abre página **`0x37`** |
| 11 | `0x00D012DC` | abre página **`0x1E`**, sub 0xB |

O caminho de abrir página termina sempre no trampolim:

```asm
0x00D011F2  pop.w {r4, r5, r6, r7, r8, lr}
0x00D011F6  b.w   #0x00D0DAE0        <- a primitiva real
```

### A receita, confirmada em hardware

A 3.0.1 abre a tela Extras com exatamente isto, e **funciona no
aparelho**:

```asm
movs r0, #1        ; página de origem (1 = home)
movs r1, #2        ; comando = abrir
movs r2, #0        ; sub
movs r3, #0x53     ; página destino
b    #0x00D011F2
```

> Esta é a única primitiva de navegação do projeto **confirmada por
> observação na tela**. É sobre ela que o Extras deve ser construído.

---

## 4. O desenho proposto

### 4.1 O patch no código vivo: 4 bytes, e só

Substituir **apenas** `0x00D2EFF6`–`0x00D2EFF9` (as duas instruções
`ldr r3,[r4]` + `cmp r0,r3`) por um desvio largo:

```asm
0x00D2EFF6  b.w  #<roteador na área livre>
```

**O que isso preserva, e por que importa:**

- `0x00D2F01A` (o `pop`) — alvo de `bne` em `0x00D2EF7C` e `0x00D2F046`.
  **Intacto.** Foi o que a 3.1 destruiu.
- `0x00D2F01C` e `0x00D2F020` — alvos só de dentro da faixa
  contornada. Ficam inalcançáveis, sem prejuízo.
- Nada em `page1_process` é tocado. **Zero bytes na faixa
  `0x00D012E2`–`0x00D01301`.** Foi o que a 3.1.2 destruiu.

Os bytes `0x00D2EFFA`–`0x00D2F019` viram código morto. Não precisam ser
zerados — e **não devem**, para o diff ficar mínimo.

### 4.2 O roteador, na área livre

Primeiro setor virgem: **`0x001A6000`** (XIP `0x00DA6000`).

```asm
roteador:
    ; entrada: r0 = objeto em foco, r4 = vetor de botões
    movs r2, #0
.laco:
    ldr  r3, [r4, r2, lsl #2]
    cmp  r0, r3
    beq  .achou
    adds r2, #1
    cmp  r2, #6
    blo  .laco
    b.w  #0x00D2F01A          ; nenhum casou -> o pop original

.achou:
    ldr  r3, =TABELA
    ldrb r1, [r3, r2, lsl #1] ; página destino
    ldrb r2, [r3, ...]        ; sub
    ; grava o índice em 0x00823D84 (a seleção lembrada)
    movs r0, #0x53            ; origem = Extras, NÃO a home
    movs r1, #2
    b.w  #0x00D011F2
```

**Nenhuma mensagem, nenhuma fila, nenhuma guarda de página.** Chamada
direta à primitiva, com origem `0x53`. É o que as três tentativas
anteriores deviam ter feito.

Custo estimado: ~60 bytes de código + 12 bytes de tabela.

### 4.3 Orçamento de heap

`lv_mem_init` (`0x00D58100`) dá ao LVGL **40 KiB**, de `0x00876000` a
`0x00880000` (`andromeda/MEMORY.md`).

Este patch **não cria nenhum objeto LVGL** — a tela de 6 itens já existe
e já é desenhada pela 3.0.1. O roteador só troca ponteiro por índice.
**Consumo de heap adicional: zero.**

> É a diferença entre este plano e as três tentativas antigas, que
> esticavam a contagem de itens de uma página de fábrica.

---

## 5. Os seis destinos  · RESOLVIDO

A tabela mestra de páginas fica em `0x00D0DB1C`: uma `tbh` de **0x53
entradas**, indexada por `página − 1`, alcançada por
`0x00D0DAE0` (`cmp r3,#0x52; bhi -> erro; tbh [pc, r3, lsl #1]`).

Os nomes vieram de `docs/PAGINAS.md`, que **já tinha a tabela medida** —
o presenter e a view de cada página.

| Extras | página | view | observação |
|---|---|---|---|
| Gravação | **`0x18`** (24) | `page_record_menu_event_cb` | — |
| Rádio | **`0x1A`** (26) | `page_fm_play_create` | — |
| Livro digital | **`0x0C`** (12) | `page_ebook_list_event_cb` | precisa de cartão |
| Imagem | **`0x15`** (21) | `page_pict_list_event_cb` | precisa de cartão |
| Bluetooth | **`0x23`** (35) | `page_bt_menu_option_event_cb` | — |
| Pastas | **`0x22`** (34) | `page_folder_list_create` | precisa de cartão |

> Compare com o que a 3.1.1 usava: índices **3** e **9** da home para
> Rádio e Gravação. Os dois são casos de erro. O mapeamento nunca teve
> chance de funcionar.

### A verificação de cartão

Os itens da home que abrem lista de mídia chamam antes:

```asm
bl  #0x00CFE714     ; cartão/volume presente?
cmp r0, #0
beq <mensagem>
```

O roteador deve fazer o mesmo para Livro digital, Imagem e Pastas. É uma
chamada, e evita a regressão que a 3.1.2 assumiu (`"se não houver
gravações, a tela do gravador aparece vazia"`).

---

## 6. Checklist antes de empacotar

```
[x] ids das 6 páginas medidos, não inferidos
[ ] check_branch_targets.py --baseline 3.0.1  ->  APROVADO
[ ] setor 0x00D000 intacto        (não recalcular CRC na tabela)
[ ] bootloader 0x0-0xD000 intacto
[ ] PSMP intacta
[ ] validate_firmware.py: 21 OK + a falha de CRC da FIRM, a esperada
[ ] diff contra a 3.0.1 listado byte a byte no LEIA-ME
```

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| A cadeia de comparação tem 3 elos para 6 itens | CONFIRMADO |
| O handler do Extras na 3.0.1 é o de fábrica | CONFIRMADO |
| `0x00D011F2` → `0x00D0DAE0` é a primitiva de abrir página | CONFIRMADO |
| A receita `r0=origem, r1=2, r2=sub, r3=página` funciona | CONFIRMADO (a 3.0.1 abre o Extras assim, na tela) |
| Índices 3 e 9 da home são casos de erro | CONFIRMADO |
| O patch de 4 bytes não destrói alvo de desvio | PROVÁVEL (validar com a ferramenta) |
| Ids das 6 páginas destino | **CONFIRMADO** (`docs/PAGINAS.md` + tabela `0x00D0DB1C`) |
