# OpenPod — O menu em lista: o que existe e o que falta

> Investigação de 2026-09-12, feita para responder: **é viável fazer o
> menu principal parecer com o do nano (lista vertical), mantendo fundo
> preto, letra branca e seletor azul?**
>
> **Resposta: viável, mas é um projeto, não um patch.** Parte do caminho
> já existe no firmware.

---

## 1. O firmware tem duas telas de "home"

| | `page_home_create` | `page_home_menu_create` |
|---|---|---|
| Endereço | `0x00D2EBB8` | `0x00D2F0A0` |
| Tamanho | 1.256 B | 1.136 B |
| Chamador | `0x00D23B8C` (**1 só**) | `0x00D23CF8` (**1 só**) |
| Referencia a folha de ícones | **SIM** → é a grade | **NÃO** |
| Helpers de lista (`0xD216F0`, `0xD21764`) | não usa | **usa os dois** |
| Funções próprias | `img_process` | **`btn_process`**, `label_process` |

`page_home_menu_create` **não desenha ícones em grade — monta botões com
rótulo em lista.** É uma tela completa, com `scr_process`,
`btn_process`, `label_process` e `event_reply` próprios.

---

## 2. ⚠️ Mas ela NÃO é o menu principal — são 3 itens

```asm
0x00D2F20C   ldr   r3, [pc, #0x114]      ; -> tabela em 0x00C486E8
0x00D2F20E   ldm.w r3, {r0, r1, r2}      ; le TRES valores
0x00D2F21C   movs  r6, #0
   ...laco...
0x00D2F2B8   ldr.w r0, [r3, r6, lsl #2]  ; ID[r6]
0x00D2F2BC   bl    #0xd2108c             ; get_string(ID)
0x00D2F2C4   bl    #0xd5ed94             ; set_text
0x00D2F2D4   adds  r6, #1
0x00D2F2DA   cmp   r6, #3                ; <<< limite
```

IDs `7`, `4`, `11`, resolvidos nas tabelas de idioma:

| ID | pt | en |
|---|---|---|
| 7 | Alarme | Alarm |
| 4 | Imagens | Pictures |
| 11 | Dicionário | Dictionary |

> **Um patch de 4 bytes redirecionando a home para esta função foi
> montado (V014) e DESCARTADO antes de gravar.** O aparelho abriria numa
> lista de 3 itens, sem acesso a Música, Vídeo, Gravação, Rádio, Livro,
> Bluetooth, Configurações e Arquivos.
>
> O patch estava tecnicamente correto; a **premissa** estava errada. Foi
> o mantenedor quem pediu a verificação — *"você não me falou os menus
> para bater com o principal"* — antes de gravar. Kit em
> `other/NAO_GRAVAR/`.

---

## 3. A boa notícia: a tela é dirigida por tabela

Ela não tem os itens embutidos. Lê de **duas** tabelas:

| Endereço | Conteúdo |
|---|---|
| `0x00C486E8` | IDs de texto — `[7, 4, 11, 0x65..0x6B, 0x0C, 0x0D]` |
| `0x00C5D622` | glifos de ícone — `EF 80 93`, `EF 84 B0`, `EF 81 8A`… |

Os bytes `EF 8x xx` são **UTF-8 da faixa U+F000**, a área dos ícones na
fonte (`FIRMWARE_MAP.md`). Cada linha da lista é **ícone + texto**, os
dois vindos de tabela.

**A tabela de IDs continua além dos três** — investigar se os itens do
menu principal já estão ali.

---

## 4. O que falta: o destino de cada item

O callback é registrado **igual para todos**:

```asm
ldr  r1, [pc, #0xcc]   ; = 0x00D2EF5C  (funcao de evento)
movs r2, #0xd          ; codigo do evento
movs r3, #0            ; user_data = 0   <<< para TODOS
bl   #0xd47064         ; add_event_cb
```

**O destino não está guardado no botão.** Ele chega pelo sistema de
mensagens: o manipulador pega o índice (`ldrh r2, [r0, #4]`), indexa o
vetor da tela, e salta ao despachante (`ldrh r0, [r4, #0xc]` →
`b.w #0xd23b10`).

Ou seja: **a associação índice → tela está na lógica de tratamento**, não
nos dados. Provavelmente um desvio fixo de três casos.

---

## 5. Estimativa

| Peça | Custo | Classe |
|---|---|---|
| Limite do laço `3` → `9` (`0x00D2F2DA`) | **1 byte** | camada 5 ✅ |
| Tabela de 9 IDs de texto | flash livre + 4 B no ponteiro | camada 5 ✅ |
| Tabela de 9 glifos de ícone | idem | camada 5 ✅ |
| **Mapear 9 índices para 9 telas** | **desconhecido** | provavelmente **camada 6** |

**A maior parte do caminho está pronta no firmware.** Falta a parte que
ninguém escreveu porque nunca precisou existir: um despacho de nove
destinos onde hoje há três.

---

## 6. Próximo passo — retomar por aqui

1. Ler `page_home_menu_btn_process` e medir o tamanho do desvio de
   destinos. **Isso fecha a estimativa.**
2. Verificar se os IDs `0x65..0x6B` da tabela `0x00C486E8` são os itens
   do menu principal.
3. Localizar os glifos de ícone equivalentes aos nove da grade.

Tudo análise estática, sem risco.

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| Existem duas telas de home, uma em grade e uma em lista | **CONFIRMADO** |
| A de lista mostra 3 itens: Alarme, Imagens, Dicionário | **CONFIRMADO** (tabela + tabelas de idioma) |
| A tela de lista é dirigida por tabela (texto e ícone) | **CONFIRMADO** |
| O limite do laço é 1 byte em `0x00D2F2DA` | **CONFIRMADO** |
| `user_data` é 0 para todos os itens | **CONFIRMADO** |
| O despacho de destino é fixo por caso | **PROVÁVEL** — não verificado |
| Estender para 9 itens é viável | **PROVÁVEL**, custo **NÃO DETERMINADO** |

---

## 8. ✅ Investigação continuada — as tabelas localizadas

### As duas tabelas de menu são ADJACENTES

```text
0x00C486C4   [1, 3, 5, 6, 2, 4, 9, 10, 8]   <- os 9 itens da GRADE
0x00C486E8   [7, 4, 11]                     <- os 3 da LISTA
```

`0x00C486C4 + 9x4 = 0x00C486E8`, exatamente. **A tabela do menu
principal já existe, completa, imediatamente antes da tabela da lista.**

### Os IDs, resolvidos (tabela do português: `0x00C53B84`)

| ID | Texto | Posição na grade |
|---|---|---|
| 1 | Música | 1 |
| 3 | vídeo | 2 |
| 5 | Gravação | 3 |
| 6 | Rádio | 4 |
| 2 | Livro digital | 5 |
| 4 | Imagem | 6 |
| 9 | Bluetooth | 7 |
| 10 | Configurar | 8 |
| 8 | Ver pastas | 9 |

> As tabelas de idioma ficam em `0x00C52744` (de), `0x00C52AA4` (en),
> `0x00C52E04` (fr), `0x00C534C4` (it), `0x00C53824` (nl),
> **`0x00C53B84` (pt)**, `0x00C53EE4` (es), `0x00C523E4` (zh).
> Cada idioma tem **duas** tabelas: a principal e uma secundária 0x50
> bytes adiante.

### Os ícones são FIXOS, não por item

```asm
0x00D2F280   ldr r1, [pc, #0xac]   ; = 0x00C5D622  (SEMPRE o mesmo)
0x00D2F284   bl  #0xd5ed94         ; set_text(label, icone)
```

O ponteiro é carregado **dentro do laço e não varia** — todas as linhas
recebem `U+F013` (engrenagem). É o que se vê em Configurações.

Glifos disponíveis em sequência a partir de `0x00C5D622`, cada um uma
string UTF-8 de um caractere (Font Awesome):

| Endereço | Codepoint | Ícone |
|---|---|---|
| `0x00C5D622` | U+F013 | engrenagem |
| `0x00C5D626` | U+F130 | microfone |
| `0x00C5D62A` | U+F04A | retroceder |
| `0x00C5D62E` | U+F04C | pausa |
| `0x00C5D632` | U+F04E | avançar |

---

## 9. Estimativa revista

| Peça | Custo | Classe |
|---|---|---|
| Apontar para a tabela de 9 (`0x00C486C4`) | **4 B** no pool | camada 5 ✅ |
| Limite do laço `3` → `9` (`0x00D2F2DA`) | **1 B** | camada 5 ✅ |
| Indexar a tabela direto, em vez da cópia na pilha | **~6 B** | camada 5 ✅ |
| Ícone por item (opcional) | tabela + índice | camada 5 |
| **Mapear 9 índices para 9 telas** | **NÃO DETERMINADO** | provável camada 6 |

**Sobre a cópia na pilha:** o código faz
`ldm r3,{r0,r1,r2}` → `stm [sp+0xc]` e depois indexa `sp+0xc`. Só cabem
**3 words** (`sub sp,#0x1c`). Para 9 itens, indexar a tabela
**diretamente** evita o problema — e os 10 bytes do `ldm`/`stm` ficam
livres para isso.

> **Os rótulos certos, em lista, custariam ~11 bytes.** O que falta é a
> navegação: fazer cada linha abrir a tela correspondente.

---

## 10. Próximo passo — daqui se retoma

**Única incógnita restante:** `page_home_menu_btn_process` e o despacho
de destino. Medir se é um desvio fixo de 3 casos (precisa virar 9) ou se
já é indexado por tabela (e aí talvez baste estendê-la).

Se for indexado: o menu em lista sai por **~15 bytes**, camada 5, sem
código novo. Se for desvio fixo: é camada 6, e aí vale avaliar se
compensa.

---

## 11. ✅ O despacho, encontrado — e a estrutura de memória

### O despacho é uma cadeia FIXA de três comparações

Em `0x00D2EF5C` (o callback registrado com `add_event_cb`):

```asm
0x00D2EFF2   bl   #0xd47648      ; qual objeto foi clicado
0x00D2EFF6   ldr  r3, [r4]       ; vetor[0]
0x00D2EFF8   cmp  r0, r3
0x00D2EFFA   beq  -> indice 0
0x00D2EFFC   ldr  r3, [r4, #4]   ; vetor[1]
0x00D2EFFE   cmp  r0, r3
0x00D2F000   beq  -> indice 1
0x00D2F002   ldr  r3, [r4, #8]   ; vetor[2]
0x00D2F004   cmp  r0, r3
0x00D2F006   bne  -> sai
0x00D2F008   movs r4, #2         ; indice 2
0x00D2F00A   movs r3, #4         ; <- convergencia
   ...
0x00D2F010   movs r0, #0x53      ; ID da mensagem
0x00D2F012   bl   #0xd23510      ; envia
```

**Resposta à pergunta da §10: é desvio fixo, não indexado. Camada 6.**

### Mas o laço substituto cabe no lugar — VERIFICADO

O espaço de `0x00D2EFF6` a `0x00D2F00A` são **exatamente 20 bytes**.
Um laço genérico montado e conferido por disassembly ocupa **20 bytes**:

```asm
0x00D2EFF6   movs  r6, #0                  ; 26 00
0x00D2EFF8   ldr.w r3, [r4, r6, lsl #2]    ; 54 F8 26 30
0x00D2EFFC   cmp   r0, r3                  ; 98 42
0x00D2EFFE   beq   #0xd2f008               ; 03 D0
0x00D2F000   adds  r6, #1                  ; 01 36
0x00D2F002   cmp   r6, #9                  ; 09 2E
0x00D2F004   bne   #0xd2eff8               ; F8 D1
0x00D2F006   b     #0xd2f01a               ; 08 E0
0x00D2F008   mov   r4, r6                  ; 34 46
```

Os três alvos de salto conferem: `beq`→`0xD2F008`, `bne`→`0xD2EFF8`,
`b`→`0xD2F01A` (o `pop` de saída). Cai no ponto de convergência.

**Sem realocação, sem flash livre, sem deslocar nada.**

---

## 12. ⚠️ A camada que quase passou despercebida — MEMÓRIA

A tela guarda os itens numa estrutura alocada:

```asm
0x00D2F0A4   movs  r0, #0x28        ; malloc(40 bytes)
0x00D2F2D6   str   r4, [r8, #4]!    ; vetor[0] - botoes
0x00D2F2DC   str.w sb, [r8, #0xc]   ; vetor[1] - rotulos
0x00D2F2E0   str.w sl, [r8, #0x18]  ; vetor[2] - icones
0x00D2F302   strb  r3, [r7, #0x26]  ; indice selecionado
```

**Três vetores de 3 palavras** nos offsets `0`, `0xC`, `0x18`, dentro de
40 bytes. Para 9 itens: `3 x 9 x 4 = 108 bytes`, e os offsets viram
`0x24` e `0x48` — **em todo lugar que lê a estrutura**.

> **Este é o primeiro patch do projeto que mexe em ALOCAÇÃO DE MEMÓRIA e
> aritmética de ponteiro.** Errar o tamanho do `malloc` ou um offset faz
> o firmware escrever **fora do bloco** e corromper a heap. O sintoma não
> seria uma tela feia — seria travamento aleatório, minutos depois, em
> outra parte do sistema. O defeito mais difícil de diagnosticar que
> existe.
>
> Todos os patches anteriores mexiam em **valores**. Se errassem, a tela
> ficava feia e a gente via na hora.

---

## 13. Plano completo — os 12 pontos

| # | Endereço | Hoje | Vira | Bytes |
|---|---|---|---|---|
| 1 | `0x00D2F324` (pool) | `0x00C486E8` | `0x00C486C4` | 4 |
| 2 | `0x00D2F2B6` | `add r3, sp, #0xc` | `ldr r3, [pc, #0x6c]` = `4B 1B` | 2 |
| 3 | `0x00D2F2DA` | `cmp r6, #3` | `cmp r6, #9` | 1 |
| 4 | `0x00D2F246` | `cmp r6, #2` | `cmp r6, #8` | 1 |
| 5 | `0x00D2F3E2` | `cmp r3, #2` | `cmp r3, #8` | 1 |
| 6 | `0x00D2F406` | `cmp r3, #2` | `cmp r3, #8` | 1 |
| 7 | `0x00D2EFF6` | cadeia de 3 | **laço de 9** (§11) | 20 |
| 8 | `0x00D2F0A4` | `movs r0, #0x28` | `movs r0, #0x70` | 1 |
| 9 | `0x00D2F2DC` | `str.w sb, [r8, #0xc]` | `#0x24` | 2 |
| 10 | `0x00D2F2E0` | `str.w sl, [r8, #0x18]` | `#0x48` | 2 |
| 11 | `0x00D2F40E` / `0x00D2F414` | `[r5,#0xc]` / `[r5,#0x18]` | `#0x24` / `#0x48` | 2 |
| 12 | `0x00D2F2FA` / `0x00D2F302` | `[r3,#0xc]` / `[r7,#0x26]` | conferir | ? |

**Ainda por verificar antes de montar:**

- `event_reply` (`0x00D2F478..`) — tem leitura em `[r3,#0xc]`, conferir
- o byte de índice selecionado em `[r7,#0x26]` — onde fica com 9 itens
- se a altura de linha permite 9 itens em 160 px (a lista de Configurações
  mostra 6 confortavelmente; 9 pode exigir rolagem, que o widget talvez
  já faça)
- **os ícones**: hoje é um ponteiro fixo (`U+F013`) carregado dentro do
  laço (§8). Com 9 itens, todos teriam engrenagem — funcional, mas feio.
  Dar ícone por item é trabalho adicional.

---

## 14. Recomendação — montar em sessão nova

**Não montar este patch no fim de uma sessão longa.** Não por ser
impossível: a análise está praticamente completa e nada indica que não
funcione. Mas:

- é o primeiro que pode causar dano **não-visual e não-imediato**
- corrupção de heap não aparece na verificação byte a byte pós-gravação,
  que é a nossa rede de segurança principal
- não há pressa: o aparelho está no V013, aprovado

**Ordem sugerida para a próxima sessão:**

1. Conferir os 4 pontos em aberto da §13
2. Montar o patch **inteiro de uma vez** — patches parciais deixariam a
   estrutura inconsistente, e aí sim há risco real
3. Validar por disassembly cada um dos 12 pontos antes de gerar o kit
4. Gravar com o kit do V013 já copiado para a máquina Linux, para
   reversão imediata

---

## 15. ⚠️ CORREÇÃO DE ENQUADRAMENTO — o plano da §13 não fecha a navegação

> Sessão de 2026-09-12 (continuação). Os 4 pontos em aberto da §13 foram
> conferidos por disassembly, como pedido, **antes** de montar o patch.
> Três deles fecharam. O quarto abriu um quinto, que invalida a premissa
> do plano inteiro.

### 15.1 Os 4 pontos em aberto — respondidos

**(a) `event_reply` / leitura em `[r3,#0xc]` — RESOLVIDO.**

`page_home_menu_event_reply` (`0x00D2F4CC`) só despacha por `ctrl_grp`:

| ctrl_grp | função | endereço |
|---|---|---|
| 1 | `scr_process` | `0x00D2F33C` |
| 3 | `label_process` | `0x00D2F478` |
| 4 | `btn_process` | `0x00D2F3A0` |

Quem lê `[r5,#0xc]` e `[r5,#0x18]` é o **`btn_process`**, no ramo
`type == 3` (trocar texto), exatamente os pontos 11 do plano. O
`label_process` indexa `[r3,#0xc]` a partir de `page_p` — **também
precisa virar `#0x24`** (ponto que a §13 não listava):

```asm
0x00D2F482   add.w r3, r3, r2, lsl #2
0x00D2F486   ldr   r3, [r3, #0xc]      ; labels[ctrl_id]  -> #0x24
```

**(b) O byte de índice selecionado — RESOLVIDO.**

Confirmado por comparação com uma tela irmã de **10 itens**,
`page_set_menu` (página `0x28`, `btn_process` em `0x00D3A92C`), que é
estruturalmente idêntica:

| | `page_home_menu` (3 itens) | `page_set_menu` (10 itens) |
|---|---|---|
| `malloc` | `0x28` | `0x54` |
| botões | offset `0` | offset `0` |
| rótulos | offset `0x0C` | offset **`0x28`** |
| ícones | offset `0x18` | offset **`0x50`** |
| limite | `cmp r3, #2` | `cmp r3, #9` |

O esquema é `rótulos = N·4`, `ícones = 2·N·4`. Para **N = 9**: `0x24` e
`0x48`, e o byte de índice cabe em `0x6C` (`malloc(0x70)`).
**As contas da §13 estão certas** — e agora estão confirmadas contra uma
implementação real do próprio firmware, não deduzidas.

**(c) Altura de linha para 9 itens — CABE, com folga pequena.**
`page_set_menu` já monta 10 itens em 160 px. Não é limite.

**(d) Ícones fixos (`U+F013`) — continua valendo o que a §13 diz.**

### 15.2 O quinto ponto — a navegação NÃO está no plano

O `btn_process`, no ramo `type == 2`, navega assim:

```asm
0x00D2F3E0   ldrh r3, [r4, #4]      ; ctrl_id
0x00D2F3E2   cmp  r3, #2            ; limite
0x00D2F3E6   ldrh r0, [r4, #0xc]    ; parap->page  <<< A TELA DE DESTINO
0x00D2F3EC   b.w  #0xd23b10         ; view_page_create
```

**A tela de destino vem de DENTRO DA MENSAGEM, não do índice.** O
`ctrl_id` só é conferido contra o limite; quem escolhe o destino é quem
envia a mensagem.

E quem envia é **outra camada**. A cadeia real, levantada nesta sessão:

```text
tecla Enter
   ↓
page_home_menu_event_cb (0x00D2EF5C)   <- camada VIEW
   ↓  view_send(page=0x53, grp=4, id=índice, evento=4)   [0x00D23510]
   ↓  mensagem: +0=page +2=grp +4=ctrl_id +6=type(=1) +0xC=evento
   ↓  fila 3
   ├──> view_msg_analysis (0x00D23E50) -> page_..._btn_process
   │      type 1 não é tratado ali: só 2 (navegar), 3 (texto), 4 (valor)
   │
   └──> camada APP: pageNN_*_process  (região 0x00D0xxxx)
          vê a mensagem com prefixo de 8 bytes:
          +8=page +0xA=grp +0xC=ctrl_id +0xE=type +0x14=evento
          É AQUI que índice -> tela é decidido
```

### 15.3 Onde está, de fato, o mapa índice → tela

| Tela | Módulo APP | Endereço | O que faz |
|---|---|---|---|
| grade (página 1) | `page1_img_process` | `0x00D00F3C` | ramo fixo por item; carrega o id da página (`0x31`, `0x33`, `0x35`, `0x37`, `0x28`…) e chama o abridor comum |
| lista (página `0x53`) | `page83_btn_process` | `0x00D0CAFA` | **só trata `ctrl_id == 0`**; qualquer outro índice cai em `pop {r4,pc}` e não faz nada |

```asm
; page83_btn_process
0x00D0CB00   ldrh r3, [r4, #0xc]    ; ctrl_id
0x00D0CB02   cbnz r3, #0xd0cb20     ; != 0 -> RETORNA SEM FAZER NADA
```

> **Consequência:** aplicar os 12 pontos da §13 produziria uma lista
> bonita com os 9 rótulos certos em que **8 dos 9 itens não abririam
> nada**. O item 0 abriria o que `page83` já abre hoje.
>
> É o mesmo tipo de erro do **V014** — patch tecnicamente correto sobre
> premissa errada —, só que desta vez com `malloc` e aritmética de
> ponteiro no meio.

### 15.4 Classificação

| Afirmação | Classe |
|---|---|
| `btn_process` tira a tela de destino de `vmsgp->page` (`+0xC`), não do índice | **CONFIRMADO** (disassembly) |
| Existe uma camada APP `pageNN_*_process` em `0x00D0xxxx` que recebe a mesma mensagem com prefixo de 8 bytes | **CONFIRMADO** (`page35_scr_process` em `0x00D07AA8` lê `type==1` e `evento` em `+0xC`) |
| `page83_btn_process` ignora todo `ctrl_id != 0` | **CONFIRMADO** (`cbnz r3` em `0x00D0CB02`) |
| `page1_img_process` contém o desvio fixo dos 9 destinos da grade | **CONFIRMADO** (ids `0x31`, `0x33`, `0x35`, `0x37`, `0x28` legíveis no desvio) |
| Estender `page83` para 9 destinos exige código novo na camada APP | **PROVÁVEL** — é camada 6, em módulo ainda não mapeado |

---

## 16. ✅ O caminho recomendado — virar a GRADE em lista, não a lista em menu

A pergunta original era *"dá para o menu principal parecer com o do
nano?"*. A resposta mudou de rota, e para melhor.

**A página 1 (grade) já tem tudo o que falta à página `0x53`:** os 9
itens, os 9 destinos e o despacho da camada APP funcionando e testado
todo dia pelo usuário. O que ela não tem é **aparência de lista** — e
aparência, neste firmware, é **dado**.

### 16.1 Como a grade é montada — `page_home_create` (`0x00D2EBB8`)

```text
0x00C4867C   9 pares int16 (x,y)  ->  posição dos ÍCONES
             x ∈ {0x09, 0x31, 0x59}   y ∈ {0x11, 0x41, 0x71}
0x00C486A0   9 pares int16 (x,y)  ->  posição dos RÓTULOS
             x ∈ {0x03, 0x2C, 0x56}   y ∈ {0x30, 0x60, 0x90}
0x00C486C4   9 ids de texto       ->  Música, vídeo, Gravação…
0x00CCDD50   folha 128×160 INDEXED_8  ->  os 9 ícones DESENHADOS
```

**Descoberta que decide o desenho:** os 9 objetos de imagem criados no
laço **não recebem fonte de imagem nenhuma** — `0xd5d868` (definir a
imagem) é chamada **uma única vez**, fora do laço, sobre a folha inteira
de 128×160. Os 9 objetos são áreas posicionadas; os ícones visíveis são
**pixels da folha**.

> Ou seja: mover os 9 pares de coordenadas **não move os ícones
> visíveis**. Quem desenha ícone é a folha — a mesma que o V001 já
> patcheou com sucesso.

### 16.2 O patch que isso implica

| Peça | Onde | Natureza | Risco |
|---|---|---|---|
| Redesenhar a folha `0x0CDD50` como 9 ícones em coluna | imagem INDEXED_8 | **dado** | o mesmo do V001/V002 |
| 9 pares de coordenadas dos rótulos | `0x00C486A0` | **dado** (36 B) | nenhum |
| 9 pares de coordenadas das áreas de ícone | `0x00C4867C` | **dado** (36 B) | nenhum |
| Largura do rótulo `0x28` → ~`0x60` | `0x00D2ED5E` | 1 byte | nenhum |
| Navegação de coluna (±3) → ±1 | ramo `0x00D2EA3A` | ~3 bytes | baixo |

**Nenhum `malloc`. Nenhum offset de estrutura. Nenhuma aritmética de
ponteiro. Nenhum risco de heap.** Volta à classe de patch em que um erro
aparece na tela na hora — que é a rede de segurança que este projeto tem
de fato.

### 16.3 Comparação honesta

| | §13 (lista → 9 itens) | §16 (grade → lista) |
|---|---|---|
| Rótulos certos | sim | sim (já são) |
| Ícone por item | trabalho extra | **já existe** (a folha) |
| Navegação funcionando | **não** — falta camada APP | **sim, já funciona** |
| Mexe em `malloc`/ponteiro | **sim** | não |
| Falha visível na hora | não (heap) | sim |
| Pontos de alteração | 12+ código | 2 tabelas + 1 imagem + 2 constantes |

**Recomendação: descartar o plano da §13 e seguir pela §16.**
A §13 fica registrada porque a análise de estrutura (offsets `0x24`/
`0x48`, limites, `malloc(0x70)`) está correta e confirmada — só não
resolve o problema que interessa.

### 16.4 O que ainda precisa ser medido antes de montar a §16

1. Confirmar que `0x00C4867C` e `0x00C486A0` são lidos **só** por
   `page_home_create` (senão mexer neles afeta outra tela).
2. Ver se a folha `0x0CDD50` é usada por outra tela além da home.
3. Decidir altura de linha: 9 linhas em 160 px → ~16 px por linha,
   com a fonte de 12 px. `page_set_menu` já faz 10 linhas, então cabe.
4. Mapear qual ramo de tecla é ±1 e qual é ±3 (há os dois hoje: o de
   `0x00D2E9DE` já é ±1 com volta em 8).

---

## 17. O alvo visual é o nano 2G — e isso reabre a §13 por outro caminho

> O mantenedor mostrou a referência: lista com **barra de seleção azul de
> largura total**, texto branco à esquerda, **chevron `>`** à direita,
> barra de título com "iPod" e bateria.

### 17.1 A §16 sozinha NÃO entrega essa imagem

Na página 1 (grade), a seleção é **só cor de texto**:

```asm
; page_home_event_cb, ao mudar de item
0x00D2EB3E   movs r0, #7
0x00D2EB42   bl   #0xd57b48        ; paleta(7) -> cor do item SELECIONADO
0x00D2EB4C   bl   #0xd4d10a        ; set_text_color(label, cor, 0)
; e para o item que perdeu a seleção:
0x00D2E9C0   bl   #0xd2e948        ; = 0xFFFF, branco
```

Os 9 itens da grade são **labels**, não botões. Não há objeto de fundo
por linha — logo **não há como fazer a barra azul sem criar objeto
novo**, que é código, não dado.

A §16 entrega: coluna vertical, 9 rótulos certos, ícones na folha,
navegação funcionando, item selecionado **colorido**.
Não entrega: barra de largura total, chevron.

> Isso é mais parecido com um iPod 1G/2G monocromático do que com o nano
> da foto. É uma melhora real e barata — mas não é a foto.

### 17.2 O widget da foto JÁ EXISTE no firmware

O helper de linha de lista `0x00D21764` cria exatamente o que a foto
mostra:

```asm
0x00D21766   bl #0xd5b890     ; cria BOTÃO
0x00D21778   bl #0xd4a1ba     ; largura = largura da tela  (0xd568a4)
0x00D2177C   bl #0xd2138A     ; cor de fundo = getter do tema (preto)
0x00D2178A   movs r0, #0x12
0x00D2178C   bl #0xd57b48     ; paleta(0x12) -> cor do estado realçado
0x00D21796   bl #0xd4d0c8
```

**Linha = botão de largura total com cor de fundo própria.** É a família
de widget usada pela lista de **Configurações** — que o mantenedor pode
conferir no aparelho em cinco segundos: é aquela tela que já tem a barra
de realce.

O chevron `>` sai de graça: os glifos Font Awesome estão em
`0x00C5D622` e seguintes, e cada linha da lista já tem **campo de ícone**
(offset `0x18` da estrutura). Hoje todos recebem `U+F013` fixo (§8).

### 17.3 ✅ Rota C — a que tira a camada 6 da conta

Descoberta desta sessão que muda a economia do problema:

> **O que decide o despacho é o `page id`, não qual função desenhou a
> tela.** Dá para manter a página **1** — com todo o despacho de 9
> destinos da camada APP intacto — e só trocar **quem desenha**.

| # | Onde | Hoje | Vira | Bytes |
|---|---|---|---|---|
| A | `0x00D23B8C` | `bl page_home_create` (`0xD2EBB8`) | `bl page_home_menu_create` (`0xD2F0A0`) | 4 |
| B | `0x00D2F010` | `movs r0, #0x53` | `movs r0, #1` | 2 |
| C | `0x00D2F00C` | `mov r1, r3` (=4) | `movs r1, #2` | 2 |

Com isso:

```text
página 1 continua sendo a página corrente
   ↓
desenhada pela função de LISTA (botões, realce, ícone por linha)
   ↓
Enter envia (page=1, grp=2, id=índice, evento=4)
   ↓
page1_img_process (camada APP) confere page==corrente ✅
   ↓
desvio fixo de 9 destinos — o que já funciona hoje
```

**A camada 6 sai da conta.** Não é preciso escrever despacho novo.

### 17.4 Mas o custo da §13 continua

A função de lista ainda monta **3** itens. Para 9, valem os 12+1 pontos
da §13 — incluindo `malloc(0x28)` → `malloc(0x70)` e os offsets `0x0C`/
`0x18` → `0x24`/`0x48`. **O risco de heap continua inteiro.**

Contas confirmadas contra `page_set_menu` (§15.1): `rótulos = N·4`,
`ícones = 2·N·4`.

### 17.5 Ressalva conhecida da Rota C

Mensagens endereçadas à página 1 chegam a `page_home_event_reply`, que
lê `page_p` em `[r3,#0xA0]` — slot da **grade**, que ficaria NULL. O
efeito é o log `-%s page_p NULL` e retorno: **atualizações dinâmicas de
texto da home parariam de funcionar**. A seleção não depende disso (é
feita direto no `event_cb`, que lê `[r3,#0x1E8]`, preenchido pela função
de lista). **Classe: PROVÁVEL** — precisa ser verificado antes de gravar
se alguma coisa atualiza a home em runtime.

### 17.6 Recomendação

| Rota | Entrega a foto? | Risco | Custo |
|---|---|---|---|
| §16 grade→lista | não (sem barra, sem chevron) | **baixo, erro visível na hora** | 2 tabelas + 1 imagem + 2 constantes |
| §17 Rota C + §13 | **sim** | **heap** — erro invisível na verificação pós-gravação | 3 pontos novos + 13 da §13 |

**Eu faria a §16 primeiro**, não porque a §17 seja errada, mas porque a
§16 é reversível, visível na hora, e responde uma pergunta que só o
aparelho responde: *9 linhas de 16 px com a fonte de 12 px ficam
legíveis?* Se ficarem, a §17 vira um passo bem definido em cima de uma
resposta já conhecida. Se não ficarem, a §17 teria sido trabalho de heap
para chegar num layout que não serve.

**Decisão é do mantenedor.** Se a prioridade for a foto e não a
prudência, a Rota C é o caminho certo — e aí vale o que a §14 já dizia:
montar **inteiro**, de uma vez, com o kit do V013 já na máquina Linux.

---

## 18. §16 — ETAPA 1: as 4 medições, feitas

Decisão do mantenedor: seguir pela **§16 (grade → lista)**, por etapas.
Esta seção fecha a §16.4. Tudo análise estática, nenhuma operação de
hardware.

### 18.1 Exclusividade das tabelas e da folha — **CONFIRMADO**

`tools/disasm.py --xref` sobre o firmware inteiro:

| Recurso | xrefs | Dono |
|---|---|---|
| `0x00C4867C` (coord. dos ícones) | **1** | `page_home_create` |
| `0x00C486A0` (coord. dos rótulos) | **1** | `page_home_create` |
| `0x00C486C4` (9 ids de texto) | **1** | `page_home_create` |
| `0x00CCDD50` (folha 128×160) | **1** | `page_home_create` |

**Nenhuma outra tela usa nada disso.** Mexer nas quatro coisas não pode
afetar outra parte do sistema. Medições 1 e 2 fechadas.

### 18.2 Mapa de teclas da home — **CONFIRMADO**

| `key_id` | Ramo | Efeito no índice |
|---|---|---|
| `0x14`, `0x87` | `0x00D2E9DE` | **−1**, volta 0 → 8 |
| `0x13`, `0x8a` | `0x00D2EACE` | **+1**, volta 8 → 0 |
| `0xa0` | `0x00D2EA3A` | −3 (0,1,2 → +6) |
| `0x81` | `0x00D2EB26` | +3 |
| `0x0a` | `0x00D2EA52` | abre o item |
| `0x1b`, `0x92` | — | só log, sem efeito |

> **Conclusão que economiza um patch: ±1 já existe nativamente.** Numa
> lista vertical, o par `0x13`/`0x14` vira cima/baixo sem alteração
> nenhuma. Os ramos de ±3 pulariam 3 linhas — estranho, não quebrado.
> **Não se mexe em tecla nesta etapa.** Decide-se depois de ver no
> aparelho qual botão físico é qual (a lacuna nº 2 do `relatorio.md`
> continua aberta: a tabela serigrafia → `key_id` está em RAM).

### 18.3 Dois pontos novos, descobertos ao medir a altura

O rótulo de cada item é montado assim:

```asm
0x00D2ED52   movs r2, #0
0x00D2ED54   movs r1, #2        ; text_align = 2
0x00D2ED58   bl   #0xd4d13a     ; set_style_text_align(label, 2, 0)
0x00D2ED5C   movs r2, #0xf      ; altura = 15
0x00D2ED5E   movs r1, #0x28     ; largura = 40
0x00D2ED62   bl   #0xd4a21a     ; set_size(label, w, h)
```

- **Largura 40 px** serve para texto centrado sob um ícone de 31 px na
  grade; numa lista, "Bluetooth" e "Livro digital" não cabem.
  `0x00D2ED5E`: `0x28` → `0x64` (100 px). **1 byte.**
- **`text_align = 2`** é centralizado. O nano é alinhado à esquerda.
  `0x00D2ED54`: `0x02` → `0x00`. **1 byte.**

> Identificação de `0xd4d13a` como `lv_obj_set_style_text_align` e de
> `0xd5ef04` como `lv_label_set_long_mode`: **PROVÁVEL**, não confirmado.
> Sustentação: os valores batem com as constantes da LVGL v8
> (`LV_TEXT_ALIGN_CENTER = 2`; e o `long_mode` do item selecionado é
> `3 = SCROLL_CIRCULAR`, o que explica o texto longo rolando só na linha
> selecionada). **A falha, se eu errei, é puramente visual e imediata** —
> está dentro da rede de segurança do projeto.

### 18.4 Altura de linha — decidida

Geometria atual da grade, que revela o espaço reservado:

```text
ícones   y ∈ {17, 65, 113}   x ∈ {9, 49, 89}    (31 px de altura)
rótulos  y ∈ {48, 96, 144}   x ∈ {3, 44, 86}    (15 px de altura)
```

Os 17 px de topo estão livres — é a faixa de status. Preservar.

**Layout proposto para a lista:**

```text
y = 0..15     faixa de status (intocada)
linha i:      y = 16 + 16·i        i = 0..8
              ícone   16×16 em x = 4
              rótulo  100×15 em x = 24
última linha: y = 144..159  -> fecha exatamente em 160
```

| Tabela | Novo conteúdo (9 pares int16 x,y) |
|---|---|
| `0x00C4867C` ícones | `(4, 16+16i)` |
| `0x00C486A0` rótulos | `(24, 16+16i)` |
| folha `0x0CDD50` | 9 ícones de 16×16 desenhados em `(4, 16+16i)` |

### 18.5 Escopo fechado da etapa 2

| # | Onde | Natureza | Bytes |
|---|---|---|---|
| 1 | `0x00C4867C` | dado | 36 |
| 2 | `0x00C486A0` | dado | 36 |
| 3 | `0x00D2ED5E` largura 40 → 100 | constante | 1 |
| 4 | `0x00D2ED54` align centro → esquerda | constante | 1 |
| 5 | folha `0x0CDD50` redesenhada | imagem | pixels |

Nenhum `malloc`. Nenhum offset de estrutura. Nenhuma aritmética de
ponteiro. Nenhuma tecla. **Toda falha possível aparece na tela na hora.**

---

## 19. §16 — ETAPA 2: o V014 montado, validado e empacotado

### 19.1 Ferramentas novas

| Ferramenta | Função |
|---|---|
| `tools/make_list_home.py` | grade 3×3 → lista vertical; confere o estado de entrada, reescreve as 2 tabelas, os 2 bytes de constante e a folha, e recalcula o CRC da FIRM |
| `tools/preview_home.py` | renderiza a tela **fora do aparelho**, usando a fonte do próprio firmware, e mede se algum rótulo estoura a largura |

`make_list_home.py` **recusa** rodar se a entrada não for exatamente a
grade original (tabelas, descritor da folha e os dois bytes `0x28`/`0x02`).
Isso garante que a base é o V013 e não um patch já aplicado.

### 19.2 O que o V014 mudou

```text
0x04867C   36 B  coordenadas dos chevrons   -> (116, 16+16i)
0x0486A0   36 B  coordenadas dos rótulos    -> (6,   16+16i)
0x12ED5E    1 B  largura do rótulo   0x28 (40)     -> 0x64 (100)
0x12ED54    1 B  text_align          0x02 (centro) -> 0x00 (esquerda)
0x0CE15C  pixels folha 128×160 redesenhada: fundo preto + 9 chevrons 6×9
0x00D00C    2 B  CRC-16 da FIRM      0x8A58 -> 0xF5AB
```

**6 999 bytes alterados · tamanho inalterado · paleta inalterada.**

### 19.3 Medição que só a fonte do firmware podia dar

Risco real: `long_mode = 0` faz o rótulo **quebrar linha** se o texto não
couber, e uma linha quebrada invadiria a linha de baixo. Medido com a
tabela de glifos (`0x086C44`) e o cmap (`0x0A27E6`):

| Item | px | Item | px | Item | px |
|---|---|---|---|---|---|
| Música | 39 | Rádio | 33 | Bluetooth | 52 |
| vídeo | 29 | Livro digital | **62** | Configurar | 58 |
| Gravação | 52 | Imagem | 46 | Ver pastas | 59 |

**Maior: 62 px, em 100 disponíveis. Nenhum estouro, nenhuma quebra.**

> De quebra isso confirma que a largura de 40 px da grade era apertada
> demais: 6 dos 9 rótulos não cabiam nela. O texto longo só não aparecia
> cortado porque o item selecionado usa `long_mode = 3` (rolagem).

### 19.4 Validação estática

```text
tools/validate_firmware.py GN438_openpod_v014.bin
  22 verificações OK, 0 falhas
  headerCrc 0x34DB · bootloader 0x759D · FIRM 0xF5AB · TONE 0x9177
```

Prévia renderizada em `analysis/preview/home_v014.png`.

### 19.5 Kit e um defeito corrigido no caminho

`OpenPod_Install_v014/` — **8 setores, 32 KiB**:

```text
0x00D000  0x048000  0x0CE000  0x0CF000
0x0D0000  0x0D1000  0x0D2000  0x12E000
```

Bootloader não endereçado. `sh -n` OK. **1** `write_flash` executável.

> ⚠️ **Ao gerar o kit apareceu um defeito latente desde o V002:** as
> instruções de socorro mandavam gravar setores **de fábrica** para
> desfazer o patch — o que deixaria a FIRM misturada, com CRC gravado
> `0x49A6` contra calculado `0xACBB`. Corrigido: a reversão agora usa os
> setores da **base**. Detalhe e verificação em `docs/ROLLBACK_POLICY.md`.

Ida e volta conferida sobre as imagens:

```text
V013 + setores do kit      == V014   OK
V014 + setores de reversão == V013   OK   (byte-idêntico)
```

### 19.6 O que o V014 NÃO faz

- **sem barra de seleção**: o item selecionado muda de **cor de texto**
  (paleta 7). Barra de largura total exige objeto novo — é a Rota C da
  §17, com o custo de heap que ela traz;
- **sem ícone à esquerda**: fiel à referência do nano 2G, que também não
  tem;
- **teclas intocadas**: `0x13`/`0x14` já eram ±1 e viram cima/baixo
  naturalmente; `0xa0`/`0x81` continuam ±3 e vão **pular 3 linhas**.
  Decisão adiada de propósito, para ser tomada com o botão físico na mão.

### 19.7 O que observar no aparelho

1. as 9 linhas aparecem, na ordem Música → Ver pastas;
2. cada linha abre a tela certa (é o mesmo despacho de sempre — se falhar
   aqui, a premissa da §16 estava errada);
3. qual botão anda de 1 em 1 e qual pula de 3 em 3;
4. legibilidade de 16 px por linha;
5. o chevron colide com algum texto longo? (medido: não, mas medição não
   é tela).

---

## 20. ✅ ETAPA 3 — V014 NO APARELHO: a renderização confere

Gravado e fotografado pelo mantenedor em 2026-09-12.

**O que a tela confirmou** — cada item é algo que a análise estática
**não** podia decidir sozinha:

| Previsto | Observado | Classe |
|---|---|---|
| 9 linhas, ordem Música → Ver pastas | ✅ exatamente | **CONFIRMADO** |
| faixa de status é objeto separado, não está na folha | ✅ relógio 23:38 e bateria intactos | **CONFIRMADO** |
| 16 px por linha é legível com a fonte de 12 px | ✅ | **CONFIRMADO** |
| "Livro digital" (62 px) não encosta no chevron em x=116 | ✅ | **CONFIRMADO** |
| `text_align` 0 alinha à esquerda (`0xd4d13a`) | ✅ todos à esquerda | **CONFIRMADO** — era PROVÁVEL |
| largura 100 px evita quebra de linha | ✅ nenhuma linha dupla | **CONFIRMADO** |
| seleção continua sendo só cor de texto | ✅ "Música" em azul, sem barra | **CONFIRMADO** |
| a folha de 128×160 é o que desenha os "ícones" | ✅ os 9 chevrons apareceram | **CONFIRMADO** |

> **A premissa central da §16 está provada:** os objetos de imagem do laço
> não têm fonte própria; o que se vê vem dos pixels da folha. Foi por isso
> que trocar layout custou 2 tabelas, 2 bytes e uma imagem — e nenhum
> `malloc`.

A identificação de `0xd4d13a` como `lv_obj_set_style_text_align` sobe de
**PROVÁVEL** para **CONFIRMADO**: o valor 0 produziu alinhamento à
esquerda na tela.

**Ainda por confirmar nesta etapa:** se cada linha abre a tela certa, e
qual botão físico anda ±1 e qual pula ±3.
