# ANDROMEDA — BOOT

## Análise do bootloader do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Local na flash | `0x00000060`–`0x0000C94C` | CONFIRMADO |
| Tamanho do payload | 51.436 bytes (0xC8EC) | CONFIRMADO |
| CRC16 do payload | 0x759D | CONFIRMADO |
| Carregado em RAM para | `0x0081FBC0` | CONFIRMADO |
| Stack pointer inicial | `0x0083BE90` | CONFIRMADO |
| Reset handler | `0x00820001` | CONFIRMADO |
| Inicialização de hardware | `0x00820418` (`startup_main_begin`) | CONFIRMADO |
| Carga da FIRM | `0x00820470` | CONFIRMADO |
| Rotina `sdupdate` | `0x00827850` | CONFIRMADO |
| Disparo do sdupdate | flag no PMU reg `0x23`, bits [2:0] == 6 | CONFIRMADO |

---

## 2. Fluxo de boot

```text
reset
  │
  ├─ Reset_Handler @ 0x00820001
  │     ├─ zera registradores
  │     ├─ configura stack pointer = 0x0083BE90
  │     ├─ zera .bss (0x0082C4AC .. 0x0083BA90)
  │     └─ bl main_bootloader @ 0x008204EC
  │
  ├─ main_bootloader @ 0x008204EC
  │     ├─ verifica flag de update por PC
  │     ├─ verifica flag de update por SD
  │     │
  │     ├─ SD flag == 6  →  caminho sdupdate
  │     │                      ├─ limpa flag
  │     │                      ├─ init de hardware
  │     │                      ├─ exibe "Finding file..."
  │     │                      ├─ monta tabela de I/O
  │     │                      └─ chama sdupdate @ 0x00827850
  │     │
  │     └─ SD flag != 6  →  boot normal
  │                           ├─ init de hardware @ 0x00820418
  │                           ├─ carrega FIRM @ 0x00820470
  │                           │     ├─ lê cabeçalho FIRM
  │                           │     ├─ copia 4 KiB para 0x00804C00
  │                           │     └─ blx 0x00804C01
  │                           └─ se falha → "update from pc"
```

---

## 3. Carga da FIRM (`0x00820470`)

Disassembly confirmado:

```asm
00820470  push {r0, r1, r2, r3, r4, r5, r6, lr}
00820472  bl  #0x82912c          ; localiza/encontra partição FIRM
00820478  bl  #0x829134          ; lê/processa cabeçalho FIRM
0082048C  bl  #0x820a64          ; flash_read(dst=0x00804C00, addr, len)
008204C0  bl  #0x820418          ; hardware init
008204C4  bl  #0x820da8          ; (cache/drain?)
008204C8  bl  #0x820288          ; (cache/invalidate?)
008204CC  addw lr, pc, #8
008204D0  blx r6                 ; r6 = runFromRam = 0x00804C01
008204D2  movs r0, #0
```

### Semântica

1. O bootloader lê o cabeçalho da FIRM (`0x30` bytes em `0x0000E000`).
2. Copia `loadLength` (= 0x1000 = 4 KiB) da flash para `loadToRam` (= `0x00804C00`).
3. Chama `0x820418` para inicialização final de hardware.
4. Salta para `runFromRam` (= `0x00804C01`, bit Thumb ligado).

### Implicação para SD Boot

O bootloader já sabe:
- Inicializar hardware.
- Copiar um bloco de dados da flash interna para RAM.
- Configurar stack (indiretamente, pois o vetor da FIRM contém SP).
- Saltar para código em RAM (`blx r6`).

O que ele **não faz** é ler do SD para RAM e saltar. O `sdupdate` lê do SD e grava na flash.

---

## 4. Rotina `sdupdate` (`0x00827850`)

A função `sdupdate` foi desmontada em detalhe em `docs/SDUPDATE_ANALYSIS.md`. Resumo:

```text
1. aloca fil (objeto FatFs) e buffer de 512 B
2. f_mount(0)
3. f_stat("0:\update.up")
4. f_open("0:\update.up", FA_READ)
5. f_read 0x200 bytes do cabeçalho
6. verifica "CONFI" (5 bytes) em +0x00
7. verifica "SL6801" em +0x16
8. lê codeOffsetInByte em +0x06
9. lê tamanho do arquivo
10. posiciona em partition_start + codeOffsetInByte
11. lê blocos de 0x80 bytes para validação de timestamp
12. apaga setores de 4 KiB a partir de partition_start
13. lê 512 B do arquivo → grava 2×256 B na flash
14. repete até o fim
15. compara CRC do arquivo × releitura da flash
16. exibe "Update finish!" e desliga
```

### Componentes reutilizáveis para SD Boot

| Função | Endereço | Papel |
|---|---|---|
| `f_mount` | `0x826AB8` | montar filesystem |
| `f_open` | `0x826464` | abrir arquivo |
| `f_read` | `0x8263E2` | ler bytes |
| `f_lseek` | `0x8263E2`? | posicionar (tabela de I/O) |
| tamanho do arquivo | `0x823A74` | retorna tamanho via FatFs |
| progresso | `0x823A7D` | callback de progresso |
| `flash_read` | `0x820A64` | ler da flash interna |
| `flash_write` | `0x821FFC` | gravar na flash interna |
| `erase_sector` | `0x8220E0` | apagar setor de 4 KiB |
| `crc_acc` | `0x821F84` | acumulador de CRC-16 |

### Tabela de operações de I/O (`0x00823CA0`)

O bootloader monta em pilha uma tabela de 8 ponteiros para abstrair as operações de arquivo:

| Slot | Endereço | Função |
|---|---|---|
| +0x00 | `0x00823B09` | abrir |
| +0x04 | `0x00823BFD` | fechar |
| +0x08 | `0x00823C11` | ler |
| +0x0C | `0x00823C29` | posicionar (lseek) |
| +0x10 | `0x00823A75` | tamanho |
| +0x14 | `0x00823C41` | ??? |
| +0x18 | `0x00823A7D` | progresso |
| +0x1C | `0x00823C45` | finalizar/erro |

Isso prova que o bootloader tem uma **camada de abstração de I/O sobre FatFs**.

---

## 5. Perguntas críticas do ANDROMEDA

### 5.1 O bootloader consegue inicializar o SD?

**SIM — CONFIRMADO.** A rotina `sdupdate` faz `f_mount(0)` e abre `0:\update.up` com sucesso.

### 5.2 O bootloader consegue abrir um arquivo no SD?

**SIM — CONFIRMADO.** `f_open("0:\update.up", FA_READ)` é chamado.

### 5.3 O bootloader consegue ler um arquivo do SD?

**SIM — CONFIRMADO.** `f_read` é chamado repetidamente em blocos de 512 B.

### 5.4 O bootloader consegue copiar conteúdo para RAM?

**INDIRETAMENTE SIM.** Ele copia da flash interna para RAM (`flash_read`). Não existe função equivalente que copie do SD para RAM, mas as primitivas (`f_read` + buffer de RAM) existem.

### 5.5 O bootloader consegue preparar a CPU e fazer jump para RAM?

**SIM — CONFIRMADO.** A carga da FIRM faz exatamente isso: copia 4 KiB para `0x00804C00` e salta para `0x00804C01` via `blx r6`.

### 5.6 Existe um caminho pronto para SD Boot?

**NÃO — CONFIRMADO.** O bootloader só tem dois caminhos:
1. Carregar da flash interna para RAM e executar (boot normal).
2. Carregar do SD para flash interna (`sdupdate`).

Não há um caminho "SD → RAM → execute".

---

## 6. Possibilidade de adicionar SD Boot

### 6.1 Onde um patch poderia entrar

A forma menos invasiva seria:

1. **Não modificar o bootloader existente** (alto risco).
2. Criar uma pequena rotina na **área livre da flash** (`0x001A3038` em diante) que:
   - Inicializa SD (reusa funções do bootloader? Não, pois a FIRM roda depois).
   - Ou: usa a própria FIRM modificada para carregar um binário do SD para RAM e saltar.

### 6.2 Problema: a FIRM precisa cooperar

Um SD loader real precisaria:
- Ou modificar o bootloader (risco alto).
- Ou ser implementado como um "aplicativo" dentro da FIRM que toma controle total do hardware.

A segunda opção é menos arriscada para a flash, mas exige:
- Desativar interrupções.
- Descartar o FreeRTOS.
- Recarregar vetores.
- Configurar stack.
- Saltar para o novo código.

Isso é **tecnicamente possível**, mas não é "SD Boot" no sentido estrito — é "aplicativo que se auto-substitui".

### 6.3 Risco de modificar o bootloader

O bootloader é a única rede de segurança conhecida. Se corrompido:
- O modo "update from pc" pode não funcionar.
- O aparelho pode virar tijolo.
- A gravação direta por USB (`write_flash`) já documentou bricks irrecuperáveis.

---

## 7. Conclusão da análise do bootloader

| Afirmação | Classe |
|---|---|
| Bootloader carrega FIRM da flash para RAM e executa | CONFIRMADO |
| Bootloader lê arquivos do SD via FatFs | CONFIRMADO |
| Bootloader grava na flash a partir do SD (sdupdate) | CONFIRMADO |
| Bootloader tem função "carregar SD → RAM → executar" | NÃO — CONFIRMADO |
| As primitivas para implementar SD Boot existem | CONFIRMADO |
| SD Boot via patch no bootloader é possível | HIPÓTESE |
| SD Boot via FIRM modificada é possível | HIPÓTESE |
| Modificar o bootloader é de alto risco | CONFIRMADO |
