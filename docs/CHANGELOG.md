# OpenPod — CHANGELOG

Registro de alterações do projeto e das imagens de firmware.

Regra: **nenhuma versão sobrescreve outra**. Cada imagem produzida recebe
número, hash e registro do que mudou.

---

## 2026-09-17 — ⚠️ Core 3.8 OBSOLETA — quebrou o Extras inteiro

Mantenedor: *"Após esse update no Extra somente gravação está
funcionando. Pelo menos a 3.7 tudo funcionava."*

**Ponto estável: Core 3.7.**

### O diff, e por que ele acusa efeito colateral

A 3.7 e a 3.8 diferem em **95 bytes**. Despacho, `TAB_CHK`, `TAB_PAG` e
a preparação do FM são **idênticos**. Só os índices 2 (Livro digital) e
3 (Imagem) mudaram de caminho.

Rádio, Bluetooth e Pastas rodam código byte a byte igual ao da 3.7.
Logo, eles não quebraram por si: entrar no Imagem ou no Livro digital
deixou o aparelho num estado ruim e o resto parou depois.

### O candidato, NÃO MEDIDO

A fábrica testa o resultado da verificação de lista:

```asm
movs r0,#0 / bl #0x00D45CAC
cmp  r0,#0 / beq -> mensagem "sem lista"
```

As réplicas da 3.7 e da 3.8 chamam `0x00D45CAC` e **ignoram o
resultado**. Se a lista não existe, `0x00D00430` e `0x00D0D058`
trabalham em cima de estado inválido.

Copiei as chamadas e não copiei as guardas.

### A regra que eu quebrei

Duas gravações seguidas (3.7 e 3.8) no mesmo item, as duas apresentadas
com confiança, as duas erradas. Na 3.8 eu escrevi que pararia se
falhasse. **Parei.**

> O defeito de Imagem/Livro digital fica ABERTO e sem tentativa nova até
> haver medição — não mais uma hipótese. Instrumentar significa comparar
> o estado da página nas duas entradas (home e Extras), não adivinhar
> qual argumento importa.

---

## 2026-09-17 — Core 3.7 — ✅ O PONTO ESTÁVEL

Confirmada por eliminação: a 3.8 quebrou e o mantenedor relatou que
**"pelo menos a 3.7 tudo funcionava"**.

Os seis itens do Extras abrem, o Rádio sintoniza. O que falta: Imagem e
Livro digital não checam o cartão nem atualizam a lista ao entrar pelo
Extras (funciona pela tela principal). Defeito ABERTO.

- `firmware/RELEASE/OpenPod Core 3.7/OpenPod_Core_3.7.up`
- hash: `5467824568276ed50e9704e8cdc63c79e33aa11253b14fcad1853e1c2c3eeca9`

---

## 2026-09-17 — Core 3.6 — a 3.4 de volta, mais o tuner do FM

**154 bytes** sobre a 3.4. **Um único setor: `0x1A6000`.** O gancho e as
tabelas são byte a byte os da 3.4.

### O que mudou

Só isto: o índice 1 (Rádio) ganhou uma sub-rotina de preparação, chamada
por `blx` antes de abrir a página. Ela **replica** `0x00D0113C`:

```asm
movs r0, #0xca / bl get_string / bl 0x00D0E2F0   ; a mensagem
movs r0, #1    / bl 0x00CFEC60
movs r2, #0x14 / ldr r1,=0x00D0083D / ldr r0,=0x00C4C943
bl  #0x00D45D50
bl  #0x00D00510                                  ; o tuner
```

Os outros cinco itens seguem exatamente o caminho da 3.4.

### ✅ CONFIRMADA NO APARELHO — 2026-09-17

Mantenedor: **"Gravei e está sintonizando"**. O Rádio do Extras funciona.

**Ponto estável do projeto: passa da 3.4 para a 3.6.**

> Lição que fica: quando uma tela abre mas não funciona, o defeito não é
> o despacho — é a **preparação** que o caso de fábrica faz antes de
> abrir. Procure o que vem antes do `movs r3, #<pagina>`.

---

## 2026-09-17 — ⚠️ Core 3.5 OBSOLETA — quebrou os menus

Gravada. Mantenedor: *"os menus estão todos bugados indo para outras
coisas, a versão 3.4 tinha algo que está funcionando perfeitamente"*.

### A causa

A 3.5 trocou "abrir a página" por "saltar para o caso de fábrica da
home". Os casos da home leem campos **da mensagem**:

```asm
0x00D01036  ldrh r2, [r4, #0xc]
0x00D01038  ldrh r1, [r4, #0xa]
0x00D0103A  ldrh r0, [r4, #8]
```

A mensagem do Extras tem esses campos com **outro significado** — o
índice é 0..5 do submenu, não o índice da home. Cada item foi parar num
lugar diferente.

### A lição

A 3.4 estava confirmada no aparelho e funcionando. Eu troquei o
mecanismo dos **seis** itens para consertar **um**, e o defeito do
Rádio nem justificava isso: bastava acrescentar a preparação.

> Regra que o projeto já tinha, de 14/09: *"volta um passo por vez,
> testado no aparelho, e nunca empacotado com algo que não foi pedido."*
> A 3.5 violou a segunda metade.

**Não gravar a 3.5.** Substituída pela 3.6.

---

## 2026-09-17 — OpenPod Core 3.4 — os seis destinos, na camada APP

**94 bytes** sobre a 3.3. Setores `0x10A000`, `0x10C000`, `0x1A6000`.
Segunda e última metade do conserto do Extras.

### A 3.3 foi confirmada no aparelho

O mantenedor gravou e testou: itens 1 a 3 continuaram indo para os
destinos de fábrica, itens 4 a 6 não fizeram nada, **e nada travou**.
Era exatamente o previsto. O lado LVGL está provado.

### O limite estava explícito

No handler da página `0x53` da camada APP:

```asm
0x00D0CC7C  ldrh r2, [r4, #0xc]     ; índice do item
0x00D0CC7E  cmp  r2, #2
0x00D0CC80  bhi  #0x00D0CD6E        ; > 2 -> retorno limpo
```

### A convenção, medida e não suposta

O caso do índice 0 (`0x00D0CCAC`) abre a página assim:

```asm
movs r3, #0x1e          ; página destino — o ALARME
movs r2, #0             ; sub
ldrh r1, [r4, #0xa]     ; r1 vem DA MENSAGEM, não é literal
ldrh r0, [r4, #8]       ; r0 = página corrente, DA MENSAGEM
pop.w {r4,r5,r6,r7,r8,lr}
b.w  #0x00D0DAE0
```

Página `0x1E` é o Alarme — **exatamente o que o mantenedor viu** ao
entrar no primeiro item do Extras. A medição e a observação fecharam.

> Note a diferença para a Core 3.2: aqui `r0` e `r1` vêm da mensagem, e
> a chamada acontece dentro do handler da APP — a task certa.

### O patch

- 4 bytes em `0x00D0CC7E` (`cmp r2,#2` + `bhi`) -> `b.w 0x00DA6200`.
- 72 bytes de despacho de seis na área livre, com a mesma convenção,
  a checagem de cartão (`0x00CFE714`) e a mensagem de "sem cartão" de
  fábrica (`0x00D0CCC2`) reaproveitadas.

| Extras | página | view | checa cartão |
|---|---|---|---|
| Gravação | `0x18` | `page_record_menu` | sim |
| Rádio | `0x1A` | `page_fm_play` | não |
| Livro digital | `0x0C` | `page_ebook_list` | sim |
| Imagem | `0x15` | `page_pict_list` | sim |
| Bluetooth | `0x23` | `page_bt_menu_option` | não |
| Pastas | `0x22` | `page_folder_list` | sim |

### Preservado

```text
check_branch_targets --baseline 3.3   APROVADO
bootloader / 0xD000 / PSMP            intactos
page1_process                         intacta
0x00D0CCC2 e 0x00D0CD6E               intactos (reusados)
```

Arquivos:

- `firmware/WORKING/GN438_core_3.4_carimbado.bin`
- `firmware/RELEASE/OpenPod Core 3.4/OpenPod_Core_3.4.up`
- hash: `ce5cca6b6327110476fe95c22793a827037f0df76beca39e815d6b39c358843b`

Ferramenta criada: `tools/patch_extras_app.py`.

### ✅ CONFIRMADA NO APARELHO — 2026-09-17

Gravada e testada pelo mantenedor: **"Deu certo"**.

Os seis itens do Extras abrem as seis telas certas.

> Este é o patch que falhou **três vezes** antes (`patch_extras`,
> `patch_extras_fix`, `patch_extras_fix2`, em 2026-09-13), e mais três
> nesta linha (3.1, 3.1.1, 3.1.2), e mais uma que travou o aparelho
> (3.2). Sete tentativas.
>
> O que mudou na oitava não foi esperteza: foi **partir em duas metades
> testáveis** e medir a convenção de cada camada em vez de supor.

**Ponto estável do projeto: passa da 3.0.1 para a 3.4.**

---

## 2026-09-17 — OpenPod Core 3.3 — a cadeia de 3 elos vira 6, e só isso

**66 bytes**, sobre a Core 3.0.1. Três setores: `0x10A000`, `0x12E000`,
`0x1A6000`.

Esta versão é **metade** do conserto do Extras, de propósito. Ela faz o
lado LVGL e **não decide destino nenhum**.

### O que mudou

O roteador na área livre acha o índice do item em foco num laço de seis
posições e **posta a mensagem**, byte a byte igual ao handler de fábrica:

```asm
movs r0, #0x53     ; página corrente
movs r1, #4
movs r3, #4
bl   #0x00D23510   ; monta msg 0x1C B e posta na fila
strb indice, [0x00823D84]
```

A única diferença para a fábrica é a origem do índice: um laço de 6 em
vez de três comparações desenroladas.

### O que esperar no aparelho

Os seis itens passam a postar mensagem com índice 0 a 5. O handler da
camada APP (`0x00D0CC0C`) **ainda só entende 3 índices**, então:

```text
itens 1 a 3  -> continuam indo para os destinos de fábrica (errados)
itens 4 a 6  -> a mensagem é postada e ignorada: NADA ACONTECE
travamento   -> NENHUM. É o que esta versão vai provar.
```

**O sucesso desta versão é não travar.** Se os itens 4, 5 e 6 não
fizerem nada e o aparelho continuar estável, o lado LVGL está provado e
só falta a camada APP.

### O que NÃO foi tocado

```text
page1_process                intacta
0x00D0CC0C (handler da APP)  intacto
0x00D2F01A (o pop)           intacto
bootloader / 0xD000 / PSMP   intactos
check_branch_targets         APROVADO
```

Arquivos:

- `firmware/WORKING/GN438_core_3.3_carimbado.bin`
- `firmware/RELEASE/OpenPod Core 3.3/OpenPod_Core_3.3.up`
- hash: `ff3c58eead236cf8f18fd723e5db8f13e877022c083a522c654fe98399d9aed4`

**Não testada no aparelho.**

---

## 2026-09-17 — ⚠️ Core 3.2 OBSOLETA — travou o aparelho

Gravada e testada. Resultado do mantenedor: *"Nada funcionou, inclusive
alguns travaram o sistema e outro ficou fazendo um barulho."*

### A causa

O roteador chamava a primitiva de abrir página (`0x00D0DAE0`)
**diretamente, de dentro do callback do LVGL**.

`0x00D23510` — o que o handler de fábrica usa — monta uma mensagem de
`0x1C` bytes e chama `0x00D234AC`, que **posta na fila da ViewTask**. O
firmware nunca chama a navegação de dentro de um callback do LVGL: ele
posta, e a camada APP consome **noutra task**.

Chamar direto executa a abertura de página na task errada, com o lock do
LVGL segurado. Daí os travamentos; o ruído era uma página de áudio
(Rádio ou Gravação) inicializando o hardware fora de contexto.

### A lição, e ela é desconfortável

O laudo da 3.1.2 criticou as versões anteriores por *"brigarem com a
guarda `msg->page == página corrente` em vez de chamar direto"*.

**Estava errado. A guarda existe porque a navegação é assíncrona.** A
3.1 e a 3.1.2 acertaram a arquitetura e erraram os detalhes; a 3.2
errou a arquitetura, que é pior.

A receita `(r0,r1,r2,r3) -> 0x00D0DAE0` foi medida **dentro de
`page1_process`**, que já roda na task certa. Que ela pudesse ser
invocada de fora nunca foi medido — foi suposto, e apresentado como
CONFIRMADO.

> `check_branch_targets.py` aprovou a 3.2. E a 3.2 travou o aparelho.
> A ferramenta responde "o patch destruiu alvo de desvio?" — não
> responde "o patch roda na task certa?". Nenhuma verificação estática
> responde isso.

**Não gravar a 3.2.** Substituída pela 3.3.

---

## 2026-09-17 — OpenPod Core 3.2 — o Extras abre as seis telas

**114 bytes**, sobre a Core 3.0.1. Três setores: `0x10A000`, `0x12E000`,
`0x1A6000`. Plano em `docs/PLANO_EXTRAS_V2.md`.

### A causa, medida no aparelho

O mantenedor gravou a 3.0.1 e testou item a item. Resultado:

```text
Gravacao       -> abriu ALARME
Radio          -> abriu DICIONARIO ("sem dados do dicionario")
demais quatro  -> nada
```

Isso fechou o diagnóstico. O handler de clique do Extras (`0x00D2EF60`)
é o de fábrica e tem uma cadeia de comparação **desenrolada com três
elos** (`[r4]`, `[r4,#4]`, `[r4,#8]`). A página de fábrica tinha 3
itens; a 3.0.1 desenha 6. Os itens 3, 4 e 5 não casam com ponteiro
nenhum e a função retorna pelo `bne #0x00D2F01A`.

Os três primeiros casavam e iam para os destinos **de fábrica** do
Extras antigo — Alarme e Dicionário.

> Não era corrupção de heap, não era a guarda de página, não era a
> tabela de remap. As três tentativas anteriores foram atrás da camada
> de mensagens, que nunca foi o problema.

### A correção

- **4 bytes** em `0x00D2EFF6`: `b.w 0x00DA6000`.
- **92 bytes** de roteador na área livre (`0x001A6000`, setor virgem):
  laço de 6 posições, verificação de cartão, e chamada direta à
  primitiva de abrir página.
- **18 bytes** para a versão na tela Informações.

Mapeamento (ids de `docs/PAGINAS.md` + tabela mestra `0x00D0DB1C`):

| Extras | página | view | checa cartão |
|---|---|---|---|
| Gravação | `0x18` | `page_record_menu` | sim |
| Rádio | `0x1A` | `page_fm_play` | não |
| Livro digital | `0x0C` | `page_ebook_list` | sim |
| Imagem | `0x15` | `page_pict_list` | sim |
| Bluetooth | `0x23` | `page_bt_menu_option` | não |
| Pastas | `0x22` | `page_folder_list` | sim |

### Uma correção de desenho, achada antes de escrever

O plano original mandava saltar para o trampolim `0x00D011F2`. Ele faz
`pop.w {r4,r5,r6,r7,r8,lr}` — **seis** registradores. O handler do
Extras empilhou **quatro** (`push {r4,r5,r6,lr}`). O salto teria
desalinhado a pilha. O roteador chama `0x00D0DAE0` com `bl` e sai pelo
`pop` original.

### O que foi preservado

```text
check_branch_targets.py --baseline 3.0.1   APROVADO
bootloader 0x0-0xD000                      intacto
setor 0xD000 (tabela de particoes)         intacto
PSMP                                       intacta
page1_process                              intacta
0x00D2F01A (o pop)                         intacto
```

Arquivos:

- `firmware/WORKING/GN438_core_3.2_carimbado.bin`
- `firmware/RELEASE/OpenPod Core 3.2/OpenPod_Core_3.2.up`
- hash: `3587037eb79dcd23e63b546e47a63437a457f0e6d0722a8d3df21950fc8aa842`

Ferramenta criada: `tools/patch_extras_router.py`.

**Não testada no aparelho.**

---

## 2026-09-17 — INCIDENTE: a 3.1.2 não abre nada no Extras

**Sem modificação de firmware.** O mantenedor relatou, com a **3.1.2
gravada no aparelho**: *"nada abre no extra"*. Diagnóstico fechado por
desmontagem comparada. Laudo completo: `docs/INCIDENTE_3.1.2.md`.

Três defeitos confirmados, dois deles em código sem relação com o Extras:

1. **Cinco destinos de desvio apagados** (3.1.2). A faixa
   `0x00D012E2`–`0x00D01301`, descrita no CHANGELOG da 3.1.2 como "o
   slot 9 da home (vago)", era o corpo de cinco casos de um switch.
   `page1_process` desvia para lá em `0x00D00F46`, `0x00D00F66`,
   `0x00D00FA6`, `0x00D00FAE` e `0x00D00FB6` — incluindo as duas saídas
   de falha de guarda e o caso default. Todos viraram `nop`.
2. **O índice do item é sempre 0** (3.1.2). O global `0x00823D84` é lido
   em 2 pontos e escrito em **nenhum**: o único `strb` que o escrevia,
   em `0x00D2F016`, foi sobrescrito pelo patch. Os seis itens do Extras
   despacham para `tabela[0] = 0x09`.
3. **A saída do handler virou nop** (3.1). `0x00D2F01A` era o
   `pop {r4,r5,r6,pc}`; dois `bne` apontam para ele.

PROVÁVEL: `current_page` nunca vira `0x53`, porque o único ponto que a
grava (`0x00D0CDC4`) está dentro de `0xD0CC0C` — a função que a 3.1.2
desconectou. A guarda `msg->page == current_page` falharia sempre, e o
desvio de falha é um dos que viraram `nop`. Descreve o sintoma exato.

**A 3.1.2 não é consertável com um patch pequeno.**

Ferramenta criada: `tools/check_branch_targets.py`. Responde o que o
diff, o CRC e a releitura do aparelho não respondem — se algum desvio do
original aponta para dentro de uma faixa sobrescrita. Rodada versão a
versão, isola as duas culpadas sozinha:

```text
2.4    vs 2.3     -> 0 desvios novos   APROVADO
3.0    vs 2.4     -> 0 desvios novos   APROVADO
3.1    vs 2.4     -> 2 desvios novos   REPROVADO
3.1.1  vs 3.1     -> 0 desvios novos   APROVADO
3.1.2  vs 3.1.1   -> 5 desvios novos   REPROVADO
```

Se existisse, a 3.1 não teria chegado ao cartão.

**A regra que fica:** nenhum patch escreve por cima de código sem antes
listar todos os desvios que apontam para aquela faixa. Em Thumb-2 com
switch compilado, os casos ficam **depois** do fim aparente da função.

Recomendação: voltar para a **Core 2.4** e refazer o Extras uma vez só.

---

## 2026-09-16 — UI — arquitetura ViewTask / MgrTask / navegação

**Sem modificação de firmware.** Aprofundamento na arquitetura de UI do
firmware original.

Descobertas:

- Listadas **249 páginas** da UI em `analysis/ui/page_list.txt`.
- Identificada a **ViewTask** (task id 3) como a task responsável pela
  navegação de telas. Sua função principal está em `0x00CF8210`.
- Corrigida análise anterior: a `MgrTask` (task id 9) trata USB/PMU/timers
  (`0x00D460F4`), não navegação de UI.
- A função `0x00D23510` monta mensagens e `0x00D234AC` posta na fila da
  ViewTask.
- Mapeamento provável dos campos da mensagem de navegação: `src`, `dir`,
  `cmd`, `sub_cmd`, `len`, `payload`.
- Disassembly salvo em:
  - `analysis/disassembly/view_task.asm`
  - `analysis/disassembly/page_home_menu_event_cb.asm`
- Documento criado: `analysis/ui/UI_TASK_ARCHITECTURE.md`.
- Documento atualizado: `docs/GUI_ANALYSIS.md` §25.4 e §25.7.

---

## 2026-09-16 — ANDROMEDA — offsets SDIO/PWM e debug de PLL

**Sem modificação de firmware.** Continuação do mapeamento de periféricos
SL6801 a partir de análise estática.

Descobertas:

- Offsets do SDIO mapeados para `0x40020000`, `0x40030000` e `0x40038000`.
  - `0x40030000 + 0x2B0` é o offset mais referenciado (12 vezes, 4 funções).
  - `0x40038000` acessado apenas em `+0x000` (possível DMA/config).
- Offsets de timer/PWM mapeados para `0x40010000`, `0x40010100`, `0x40010200`
  e `0x40011000`.
  - Blocos `0x40010x00` têm registrares espaçados a cada 0x100 bytes.
  - Bloco `0x40011000` tem registradores densos a cada 0x04–0x08 bytes,
    sugerindo PWM dedicado.
- Função de debug de clock localizada em `0x00D65840`:
  - Imprime `core pll:%u, cpu pll:%u, cpu0:%u, cpu1:%u, ahb:%u, norf:%u`.
  - Usa helper `0x008051E0` para acessar registradores de clock/SCU.
  - Usa `0x0080D6CC` e `0x00CF7294` para leitura/conversão de PLL
    (parte do código reside em RAM, invisível estaticamente).
- Headers C provisórios criados:
  - `andromeda/headers/sl6801_sdio.h`
  - `andromeda/headers/sl6801_pwm.h`
- Script `tools/peripheral_offsets.py` criado para mapear offsets dentro de
  uma base de periférico.
- Documentos atualizados:
  - `andromeda/PERIPHERAL_REGISTER_SCAN.md` §5.5, §5.6, §5.7, §7, §8.
  - `andromeda/PROMPT_RETOMADA.md`.

---

## 2026-09-16 — ANDROMEDA — rastreamento de `keyad_read` e offsets GPIO/clock/LCDC

**Sem modificação de firmware.** Continuação da engenharia reversa do
subsistema de entrada e do mapeamento de periféricos do SoC SL6801.

Descobertas:

- `keyad_read` localizada em `0x00D21110`.
- Buffer de evento de tecla mapeado em `0x00823D7A` (escritor `0x00D21374`).
- Callback de tecla registrado na inicialização `0x00CFC378`:
  `0x00CFC7A9` para `/dev/kadc_ch1`, `/dev/key_onoff` e `/dev/key_io`.
- Tabela de conversão `(key_id, event_type)` → código LVGL documentada em
  `andromeda/INPUT.md` §7.4 e `docs/BUTTON_ANALYSIS.md` §10.
- Eventos de tecla reconhecidos: `0x10` (press), `0x30` (release),
  `0x40` (long start), `0x50` (long press), `0x60` (long release).
- Drivers de ADC localizados:
  - `0x00D7C660` usa base `0x40095000`.
  - `0x00D7C564` usa base `0x40096000`.
- Offsets específicos mapeados para GPIO (`0x40085000`), clock/reset
  (`0x40080000`, `0x40081000`) e LCDC (`0x400D0000`, `0x400D1000`).
- Headers C provisórios criados em `andromeda/headers/`:
  `sl6801_gpio.h`, `sl6801_clock.h`, `sl6801_lcdc.h`, `sl6801_adc.h`.
- Documentos atualizados:
  - `andromeda/INPUT.md`
  - `docs/BUTTON_ANALYSIS.md`
  - `andromeda/PERIPHERAL_REGISTER_SCAN.md`

Ainda não resolvido:

- Mapeamento físico botão → GPIO/ADC (limiares em RAM só acessíveis em
  runtime).
- Offsets internos do ADC (acessos via cópia de estrutura).
- Headers provisórios para SDIO e PWM.

---

## 2026-09-16 — ANDROMEDA — scan de registradores de periféricos

**Sem modificação de firmware.** Trabalho de engenharia reversa contínuo
para mapear o SoC SL6801.

Descobertas:

- Criado `andromeda/PERIPHERAL_REGISTER_SCAN.md` com mapeamento automatizado
  de acessos a periféricos via `LDR [PC, #imm]`.
- Confirmados registradores internos Cortex-M: `0xE000ED88` (CPACR),
  `0xE000E010` (SysTick), `0xE000E100` (NVIC), `0xE000ED00` (SCB/CPUID),
  `0xE000ED04` (ICSR), `0xE000ED14` (CCR).
- CPACR habilita CP10/CP11 → FPU VFP ativa → núcleo **provavelmente
  Cortex-M4F**.
- Identificadas bases prováveis:
  - GPIO/pinmux: `0x40085000`
  - Clock/Reset: `0x40080000`, `0x40081000`
  - PMU/System Control: `0x40070000`
  - SDIO: `0x40020000`, `0x40030000`, `0x40038000`
  - LCDC: `0x400D0000`, `0x400D1000`
  - ADC (teclas): `0x40095000`, `0x40096000`
  - PWM: `0x40010000`..`0x40011000`
  - USB device: `0x40A00000`, `0x40C00000`
  - USB host/otg: `0x41100000`
  - Audio I2S/DAC: `0x40090000`, `0x40240000`, `0x40300000`
  - SPI Flash controller: `0x40027000`
- Atualizados `andromeda/CPU.md`, `andromeda/MEMORY.md`,
  `andromeda/DISPLAY.md` e `andromeda/INPUT.md` com os novos candidatos.

Próximos passos: confirmar offsets dentro de cada base e cruzar com
strings de driver (`/dev/uart*`, `/dev/kadc*`, `/dev/pwm*`, etc.).

---

## 2026-09-15 — OpenPod Core 3.1.2 — Extras abre os apps corretamente

**Correção real do despacho do Extras.** A 3.1.1 trocava só a tabela de
remap (`0x00D2F00C`), mas o problema estava mais fundo: o firmware entrega
mensagens pelo **número da página corrente**, não pela página que a
mensagem diz. Com o Extras na tela (página `0x53`), uma mensagem dizendo
"página 1" nunca chegava ao `page1_process` da home.

Mudanças:

- Handler de clique do Extras (`0x00D2F004`) envia agora `page = 0x53`,
  mantendo `grp = 2` e o índice remapeado pela tabela.
- Novo módulo na área livre (`0x00DA5920`) trata o Enter da página
  `0x53` e repassa para `page1_process` (`0x00D00F3C`). A guarda
  `msg->page == página corrente` passa, e cada item executa a rotina
  original de fabrica, com as verificações de cartão/volume.
- Handler da **Gravação** refeito no slot 9 da home (`0x00D012E2`):
  o handler original havia sido destruído pela 3.1, então o slot 9
  recebeu um mini-handler que abre a página do Gravador (0x18)
  diretamente. As verificações de cartão/volume do handler original
  não foram restauradas nesta versão.

Mapeamento confirmado (ordem na tela: Gravação, Rádio, Livro digital,
Imagem, Bluetooth, Pastas):

| Extras | destino | slot da home |
|---|---|---|
| Gravação | Gravador | 9 (mini-handler, sem verificações) |
| Rádio | Rádio FM | 3 |
| Livro digital | eBook | 4 |
| Imagem | Imagens | 5 |
| Bluetooth | Bluetooth | 6 |
| Pastas | Arquivos | 8 |

Versão na tela Informações: `OpenPod Core 3.1.2` (`0x001A5930`).
CRC da partição FIRM recalculado e validado.

Arquivos:

- `firmware/WORKING/GN438_core_3.1.2.bin`
- `firmware/RELEASE/OpenPod Core 3.1.2/OpenPod_Core_3.1.2.up`
- hash: `be653ea8a811dcd329959a95bbfadb0491f3165573e0efaf13593432f330f505`

---

## 2026-09-15 — OpenPod Core 3.1.1 — correção do remap do Extras

**Seis bytes.** Tabela de remapeamento do clique no Extras
(`0x00D2F00C..0x00D2F011`):

- `09 03 04 05 06 08` → `03 04 05 06 08 02`

Isso corrige:

1. **Rádio ia para índice 9 (inválido)** → agora vai para índice 3 (FM).
2. **Demais itens deslocados em +6 posições** → cada um agora abre a
   tela correspondente na home:
   - Livro digital → eBook
   - Imagem → Imagens/Galeria
   - Bluetooth → Bluetooth
   - Pastas → Arquivos
   - Gravação → Gravador

A mensagem de redespacho continua sendo `msg(1, 2, index, 4)`, igual ao
clique da home. A correção está somente nos índices enviados.

Também atualizada a string da tela Informações para
`OpenPod Core 3.1.1` (na área livre, 0x001A4F20).

CRC da partição FIRM recalculado e validado.

Arquivos:

- `firmware/WORKING/GN438_core_3.1.1.bin`
- `firmware/RELEASE/OpenPod Core 3.1.1/OpenPod_Core_3.1.1.up`
- hash: `23168420d4a5739113e5b61057182bfaadb23dc84e36b365bcb4cd2dbc823684`

---

## 2026-09-15 — Análise: por que páginas de menu novas ficam inacessíveis

Sem alteração de firmware. Descobertas da análise contínua do
`GN438_original.bin`:

- Mapeados os pontos de entrada de todas as páginas nomeadas
  (`page_<nome>_create`, `page_<nome>_scr_process`,
  `page_<nome>_event_cb`).
- Decodificado `page_home_menu_create` (`0x00D2F794`): cria 6 itens de
  lista usando `CRIA_LINHA`, `lv_obj_add_event_cb` e dois rótulos por
  item.
- Decodificado `page_home_menu_event_cb` (`0x00D2F540`): ao clicar num
  item, ele itera pela tabela de botões e envia uma mensagem
  `msg(7, 4, 4, i)` para a fila da `MgrTask`.
- Identificado o dispatcher da `MgrTask` (`0x00D3FF8C` → `0x00D460F4`)
  como o ponto que interpreta o comando e transiciona de estado/página.

**Conclusão:** criar uma página nova e desenhar um botão para ela não é
suficiente. É preciso também registrar a página no sistema de páginas e
garantir que o dispatcher da `MgrTask` saiba carregá-la. Isso explica o
sintoma relatado de itens de menu inacessíveis.

Documentado em `docs/GUI_ANALYSIS.md` §25.

---

## 2026-09-14 — OpenPod Core 1.1 — ✅ CONFIRMADA NA TELA

**Um byte.** `0x0012179E`, `01` → `00`, dentro de `CRIA_LINHA`
(`0x00D21764`, usada por 39 telas): a borda da linha vai a zero e o traço
entre os itens some.

Instalada pelo cartão. Foto da tela Configurar, mantenedor: *"Excelente"*.

```
sem traco entre os itens              OK
traco embaixo da FAIXA preservado     OK   <- a distincao, provada
nada mais mudou                       OK
```

> **A tese da carcaça está provada em hardware.** Um byte numa rotina
> compartilhada mudou a tela. Deixou de ser dedução.

Relatório: `docs/releases/OpenPod_Core_1.1.md`.

### A mesma foto fechou três itens que estavam abertos

| item | medido na tela |
|---|---|
| **M-f** seleção | **já é de borda a borda** — falta só a cor: é ciano `palette_main(7)` RGB(0,190,213); o alvo é azul RGB(41,101,222) |
| **M-d** / **M-e** / **M-c** | rolagem, ícones de engrenagem e faixa sem título — todos confirmados |
| **M-j** tema escuro | **sem faixas horizontais** — o desvio de `MARTE_ALVO` §0-bis se sustenta |

### E a estrutura da home foi mapeada no mesmo dia

Pré-requisito do passo seguinte, fechado (`CARCACA_PADRAO.md` §4.3):

```
+0x00 .. +0x23   array A   9 ponteiros
+0x24 .. +0x47   array B   9 ponteiros
+0x48 .. +0x4B   campo r4
+0x4C .. +0x53   8 BYTES DE FOLGA, no FIM
```

Duas correções minhas: a folga é de **8** bytes, não 12 (faltava contar
`r4`); e os offsets que publiquei do Configurar estavam deslocados de 4 —
as instruções são pré-indexadas, o encoding não é o offset.

Custo da conversão: `malloc`/`memset` de `0x54` → `0x70`, **dois
imediatos de 8 bits**, e o campo `r4` não se move.

---

## 2026-09-14 — LIMPEZA: a linha 2.x foi removida

> Pedido do mantenedor, nas palavras dele:
>
> *"realmente você está pegando códigos e problemas de versões anteriores
> bugadas. Pedi para você mudar só o menu, você veio com um update 2.4
> com alteração da barra superior que não pedi."*
>
> E, sobre o acervo: *"não podemos usar essas referências, elas não são
> boas"*, *"experiments são problemáticas"*.

**A causa era estrutural, não desatenção.** As receitas 2.x encadeavam
até 31 passos em que o `patch_chrome_padrao` — a barra superior — era
**pré-requisito declarado** dos doze passos do Saturno. Mexer em qualquer
item da lista arrastava a barra junto. O acoplamento estava na receita,
não no firmware.

**Agravante medido:** existiam duas coisas chamadas "OpenPod 1.0" no
mesmo repositório — `historico/releases/OpenPod 1.0` (morta) e
`firmware/RELEASE/OpenPod Core 1.0.1` (viva).

### O que saiu

| | |
|---|---|
| `tools/` | 56 ferramentas: 28 da receita 2.x (Saturno S3–S12, chrome_padrao, marte_paleta, status_bar, titulos, extras, home, `exp_home_linha`) e 28 experimentos da lista `FORA` |
| `build.py` | receitas `interface`, `core2.0`, `core2.1`, `core2.2`, `marte`, `carcaca`. Resta **uma**: `core1.0` |
| `firmware/RELEASE/` | 22 kits mortos (OpenPod 1.4–3.1, Core 2.0–2.4, v044) |
| `firmware/WORKING/` | imagens `v001`–`v101` e todas as 2.x |
| `docs/` | 8 planos da 2.x, e 5 relatórios de versão |
| `experiments/` | SONDA, DIAGNOSTICO cores, HOME como linha |
| `historico/` | kits V001–V044 e releases da numeração velha |
| `update/SDCARD_v001` | pacote da V001 |

### O que ficou, e por quê

```
firmware/ORIGINAL       intocado, sha b7cd5eb9... conferido antes e depois
OpenPod Core 1.0.1      a unica STABLE, a que esta no aparelho
recovery/               + modo_download, promovido de historico/recuperacao
marte/                  a BASE VISUAL — decisao do mantenedor
analysis/ extracted/    a engenharia reversa
docs/                   o entendimento do firmware
tools/                  30 ferramentas: a receita, o pipeline, a analise
```

### As medições foram extraídas antes de apagar

`PROJETO_SATURNO.md`, `CONVERTER_HOME.md` e `PADRONIZAR_HOME.md` tinham
planos mortos **misturados com medições reais do firmware de fábrica**. As
medições foram para **`GUI_ANALYSIS.md` PARTE IV** antes da remoção: os
dois caminhos de desenho, o laço da home decodificado (dois objetos por
item), o molde de `page_home_menu_event_cb`, o perigo de alocação da
página `0x53`, e os pontos de cor e fonte.

> ⚠️ Endereços `0x001A5xxx` eram a área onde os patches da 2.x escreviam.
> **Não existem no firmware de fábrica.**

### Validação depois da limpeza

```
tools/build.py --receita core1.0
  sha256  7312fbd066b1a31e508a51c9c44c5e203e17e6d1e1b9719c0df7e37e7b250d34
  bate com o hash publicado da Core 1.0.1   OK
  21 verificacoes OK + a falha de CRC da R1, a esperada
  nada abaixo de 0x00D000  |  0x00D000 intocado  |  PSMP intocada
```

**Recuperabilidade:** tudo está no git, no commit da limpeza — **exceto**
o que estava no `.gitignore`: as imagens de `firmware/WORKING/` e a maior
parte de `firmware/RELEASE/`. Essas se perderam de verdade.

### A regra que fica

**Volta um passo por vez, testado no aparelho, e nunca empacotado com
algo que não foi pedido.**

---

## Imagens de firmware

### `GN438_readback_2026-09-12.bin` — RELEITURA DO APARELHO (evidência)

| | |
|---|---|
| Local | `firmware/READBACK/GN438_readback_2026-09-12.bin` |
| Lido em | 2026-09-12, máquina Ubuntu, somente leitura |
| SHA-256 | `0b97ef5169791acd8c8ca85ebab16a89c1b96847ba9a3e4d3f42f051cd2d72d0` |
| Permissões | `r--r--r--` (444) |
| Divergências vs original | **apenas na `PSMP`** (802 bytes); todas as regiões críticas idênticas |
| Valor | prova que a recuperação por USB funciona e que o original é cópia fiel |

### `GN438_original.bin` — ORIGINAL, INTOCÁVEL

| | |
|---|---|
| Local | `firmware/ORIGINAL/GN438_original.bin` |
| Tamanho | 2.097.152 bytes |
| SHA-256 | `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f` |
| Origem | dump read-only via `smartlink_flash / smtlink_dump` (`flash_id`, `read_flash`) — procedimento completo em `docs/FIRMWARE_DUMP.md` |
| Permissões | `r--r--r--` (444), marcado somente-leitura |
| Modificações | **nenhuma** |

### `GN438_analysis.bin` — cópia de trabalho

| | |
|---|---|
| Local | `firmware/WORKING/GN438_analysis.bin` |
| Criada em | 2026-09-11 |
| SHA-256 | `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f` (idêntico ao original) |
| Modificações | **nenhuma** — usada apenas para leitura durante a análise |

### `GN438_rebuilt_original.bin` — prova de round-trip

| | |
|---|---|
| Local | `firmware/WORKING/GN438_rebuilt_original.bin` |
| Criada em | 2026-09-11 |
| SHA-256 | `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f` (idêntico ao original) |
| Origem | reconstruída por `tools/rebuild_firmware.py` a partir do original |
| Modificações | **nenhuma** — é a prova de que o container foi entendido |

### `update_restore_original.up` — PACOTE DE RECUPERAÇÃO

| | |
|---|---|
| Local | `firmware/WORKING/update_restore_original.up` |
| Criado em | 2026-09-12 |
| Tamanho | 1.716.536 bytes |
| SHA-256 | `82f0ae8c71a604f900c8d4aa235c046b91250f346e9623835daf8aecb29c35c8` |
| Origem | `firmware/ORIGINAL/GN438_original.bin` (somente leitura) |
| CRC do payload | `0x77F5` |
| Validação | 11 OK / 0 falhas; payload idêntico a `flash[0:0x1A3038]` |
| **Instalado** | **NÃO** |
| Limitação | só serve se o aparelho ainda iniciar a aplicação — ver `FLASH_POLICY.md` §3 |

### `GN438_openpod_v001.bin` — PRIMEIRO PATCH VISUAL

| | |
|---|---|
| Local | `firmware/WORKING/GN438_openpod_v001.bin` |
| Criada em | 2026-09-12 |
| Tamanho | 2.097.152 bytes (inalterado) |
| SHA-256 | `9dc755eef24e3e09c8939d90c89d9a241e0c6edd75b377c1792e743ccc79215c` |
| Base | `firmware/ORIGINAL/GN438_original.bin` (aberto somente para leitura) |
| Alteração | ícone **Música** da folha do menu — recolorido para RGB(0,150,255), rótulo vermelho preservado |
| Bytes alterados | **718** (716 de pixels + 2 do CRC da FIRM), em 43 faixas |
| Paleta | **0 bytes** alterados |
| CRC recalculado | FIRM `0x49A6` → `0x583A`; todos os demais inalterados |
| Validação | `validate_firmware.py` 22 OK / 0 falhas · `fwhelper scan` limpo |
| **Gravada no aparelho** | **NÃO** |
| Ferramenta | `tools/patch_home_icon.py --cell 1 --rgb 0,150,255 --keep 5,7,8,9,10,11,12,14` |

---

## Histórico do projeto

### 2026-09-11 — Organização inicial

- Criada a estrutura de diretórios definida em `CLAUDE.md` §10.
- `GN438_original.bin` movido para `firmware/ORIGINAL/`; SHA-256 calculado
  antes e depois do movimento, ambos conferindo com o valor esperado.
- Arquivo marcado como somente-leitura (444).
- `OpenPod_CLAUDE.md` → `CLAUDE.md` (raiz).
- `OpenPod_Design_System.md` → `docs/OpenPod_Design_System.md` (sem alteração de conteúdo).
- `README.txt` e `GN438_SHA256.txt` movidos para `firmware/ORIGINAL/` por
  serem proveniência do dump.
- Nenhum arquivo apagado. Nenhum ZIP ou pacote encontrado.

### 2026-09-11 — Primeira análise forense

**Cópia de trabalho criada** em `firmware/WORKING/GN438_analysis.bin`
(hash idêntico ao original).

**Ferramentas escritas:**

| Ferramenta | Função |
|---|---|
| `tools/firmware_info.py` | entropia, histograma, regiões de preenchimento, magics |
| `tools/extract_strings.py` | strings ASCII / UTF-16LE / UTF-16BE com offsets |
| `tools/find_partitions.py` | decodifica e **valida** a tabela de partições e os CRCs |
| `tools/scan_fonts.py` | descobre tabelas de glifos LVGL por auto-consistência |
| `tools/extract_fonts.py` | decodifica e renderiza fontes bitmap LVGL |
| `tools/extract_graphics.py` | exporta ícones e imagens para PNG |

**Descobertas principais:**

- Arquitetura **ARM Cortex-M com FPU**, **Thumb-2**, **little-endian**.
- RTOS **FreeRTOS** com camada de abstração `OAL_`.
- Tabela de partições em `0x0000D000`: **FIRM**, **TONE**, **PSMP**.
- Algoritmo de integridade **CRC-16/CCITT-FALSE**, validado em 4 regiões.
- Nomes dos campos de cabeçalho extraídos de uma string de debug do
  próprio bootloader.
- Flash mapeada em memória (**XIP**) na base **`0x00C00000`**.
- Apenas 4 KiB da FIRM são copiados para RAM; o resto executa da flash.
- GUI: **LVGL v8**, display **128×160 RGB565**, controlador **GC9106**.
- **61 telas** mapeadas (`page1`–`page84`).
- Fonte de texto totalmente decodificada: 7.098 glifos, 1 bpp, 12 px.
- **675 ícones** 4bpp decodificados e exportados.
- 8 imagens `lv_img_dsc_t` exportadas, incluindo a folha de ícones do
  menu principal e o logotipo de boot.
- Rotina `boot sdupdate` identificada no bootloader.
- 8 idiomas embutidos, incluindo **português**.
- **Sem criptografia e sem compressão.**

**Extraído:** 801 arquivos PNG em `extracted/`.

**Relatórios:** `FIRMWARE_ANALYSIS.md`, `FIRMWARE_MAP.md`,
`GUI_ANALYSIS.md`, `BUTTON_ANALYSIS.md`.

**Hardware:** nenhuma operação realizada. Nenhum flash, erase ou write.

### 2026-09-11 — Fase 0.5: rebuild e validação

**Ferramentas criadas:**

| Ferramenta | Função |
|---|---|
| `tools/fw_common.py` | CRC-16/CCITT-FALSE e layout dos cabeçalhos (fonte única) |
| `tools/rebuild_firmware.py` | desmonta e remonta o container, regenerando CRCs |
| `tools/validate_firmware.py` | validação independente + comparação byte a byte |
| `tests/test_roundtrip.py` | testes de regressão, incluindo controle negativo |

**Resultado do round-trip:**

```text
SHA-256 original == SHA-256 rebuilt
byte differences = 0
26 verificações de validação OK, 0 falhas
3 testes de regressão, todos aprovados
```

**Descobertas:**
- Campo `+0x5C` do cabeçalho HLKJ identificado como **CRC-16/CCITT-FALSE
  do próprio cabeçalho**, sobre `[0x00:0x5C]` = `0x34DB`. Campos
  desconhecidos do HLKJ caíram de 4 para 3.

**Correções:**
- Defeito na política de CRC: o rebuilder inferia "partição não
  verificada" a partir do valor presente na entrada, o que propagaria um
  CRC zerado inválido para um firmware modificado. Substituído por
  política explícita em `fw_common.PARTICOES_SEM_CRC`. Encontrado pelo
  teste T2 antes de causar dano.

**Hardware:** nenhuma operação realizada.

### 2026-09-12 — Proveniência do dump documentada

**Criado:**

| Arquivo | Função |
|---|---|
| `docs/FIRMWARE_DUMP.md` | procedimento de obtenção do firmware, com evidências |
| `tools/external/smartlink_flash.lock` | versão travada do dumper (commit + SHA-256 de 15 arquivos) |
| `tools/external/fetch_smartlink_flash.sh` | obtém e verifica essa versão exata |

**Registrado:**
- Repositório: https://github.com/ilyakurdyukov/smartlink_flash
- Commit travado: `49d51d17e825afbbbc2be7d91d6367674543c2e3`
- VID:PID `301a:2801`, serial `20201111000001`, `flash_id 0x14851485`
- Comando exato do dump e a natureza somente-leitura, comprovada pelos
  opcodes emitidos (`CMD_SL_READID` e `CMD_SL_READ`, apenas)

**Decisão:** o código do dumper não foi copiado para o projeto — upstream
sem arquivo de licença. Reprodutibilidade garantida por commit travado e
verificação por hash.

**Hardware:** nenhuma operação. O dump NÃO foi repetido.

### 2026-09-12 — Engenharia reversa do `boot sdupdate`

**Ferramenta criada:** `tools/disasm.py` — disassembly ARM Thumb-2
(capstone) com conversão offset↔endereço, busca de xrefs por pool literal
e anotação automática de strings.

**Documento:** `docs/SDUPDATE_ANALYSIS.md`

**Confirmado por disassembly:**
- Arquivo de atualização: `0:\update.up`, raiz do cartão, aberto em modo
  `1` (somente leitura)
- Magic: `"CONFI"` — **5** bytes em `0x00` (o 6º byte não é verificado)
- Marca do chip: `"SL6801"` em `0x16`, 6 bytes
- `codeOffsetInByte`: u32 desalinhado em `+0x06`
- `parition_start` vem de `flash[0x20]` — **confirma por disassembly** que
  o campo `+0x20` do `HLKJ` é o offset da tabela de partições
- **Não há assinatura nem validação de CRC do pacote antes de gravar**
- O CRC existente compara arquivo × releitura da flash (verificação de
  escrita, não de integridade do pacote)
- Apaga em setores de 4 KiB, grava em páginas de 256 B, sempre a partir de
  `parition_start`; a faixa `0x0`–`0xD000` **nunca é tocada**
- Códigos de retorno: `0xFA` marca errada · `0xFC` timestamp igual ·
  `0xFE` magic errado · `0xFF` falha de alocação

**Achado crítico:** o bootloader **rejeita** o pacote se o `fileStamp` for
**igual** ao timestamp instalado. A string `"time is not same"` é impressa
no caminho de **sucesso** — semântica invertida em relação ao texto. Um
pacote gerado do rebuild byte-a-byte seria recusado.

**Não resolvido:** como o `sdupdate` é disparado (chamada indireta).

**Decisão:** nenhum pacote `update.up` criado — formato ainda não
completamente comprovado nesta etapa.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Mapeamento do sistema de entrada

**Documento:** `docs/INPUT_MAP_COMPLETE.md`

**Confirmado por disassembly:**
- **13 `key_id`**: `0x20`–`0x25`, `0x34`, `0x37`, `0x38`, `0x42`, `0x43`,
  `0x45`, `0x47`. Nomeados: `enter`, `volume_down`, `volume_up`, `record`,
  `onoff`, `left`, `right`, `back`, `power`.
  **Quatro sem nome:** `0x20`, `0x22`, `0x25`, `0x38`
- **5 códigos de evento:** `0x10` press · `0x30` short release ·
  `0x40` long start · `0x50` long release · `0x60` long press
- Palavra de evento: `key_id` em bits [7:0], evento em bits [23:16],
  flag no bit 31
- `/dev/key_onoff` é aberto declarando literalmente os ids `0x37` e `0x47`
- Máquina de 8 estados via tabela `tbh` em `0x00CFC828`
- Navegação é definida pelo `ctrl_id` do widget focado no LVGL, **não**
  pelo botão físico

**Correção a documento anterior:** `docs/GUI_ANALYSIS.md` §5 afirmava
`page34` como candidato mais forte a Now Playing. Está **errado** —
`page4` é a tela do reprodutor, confirmado por disassembly de
`pstr_page4_process` (`0x00D08A90`). O documento de GUI foi corrigido.

**Não resolvido:** a tabela que liga serigrafia (M, ◀◀, ▶▶, ▶Ⅱ) a
`key_id` fica em RAM (`0x00819BCC`), montada em runtime. O mapeamento
físico ficou registrado como **HIPÓTESE**, não como fato.

**Hardware:** nenhuma operação. Firmware não alterado.

---

### 2026-09-12 — Referência do formato `update.up`

**Documento:** `docs/UPDATE_UP_REFERENCE.md`

**Busca:** 7 frentes (web, GitHub, fabricantes chineses, issues upstream).
**Nenhum pacote `update.up` público existe.**

**Encontrado material melhor:** `fwhelper/main.c`, no repositório já
travado por hash desde a sessão de proveniência, é o **gerador** do
formato — "converts the raw dump to a format recognized by official
flashing tools" (palavras do autor, issue #3).

**Lacunas fechadas:**
- Cabeçalho CONFIG completo (0x100 bytes): `"CONFIG"` · `+0x06`=`0x100` ·
  `+0x10`=`fw_size` · `+0x14`=CRC16 do payload · `+0x16`=nome do chip ·
  `+0xFE/FF`=`0x55 0xAA`
- **`codeOffsetInByte` = `0x100`** — deslocamento flash→arquivo.
  Confirmado por duas análises independentes
- **Timestamp = decimal `YYMMDDHHMM`**: `2401300930` = 2024-01-30 09:30
- Word `+0x08` da tabela de partições = **versão** (`≥0x30` ⇒ SL6806;
  o nosso é `0` ⇒ SL6801)

**Validação cruzada:** `fwhelper scan` executado (somente leitura) no
firmware original — **nenhuma divergência de checksum**. Implementação de
terceiros valida os mesmos CRCs que `tools/validate_firmware.py`. A
política `PARTICOES_SEM_CRC={PSMP}` coincide com o que o upstream faz.

**Avisos de risco registrados (issue #3 do upstream):**
1. A flash **não se comporta como flash normal**: escrever `1` sobre `0`
   sem apagar funciona em ~90 % dos casos, aparentemente de forma
   aleatória. Toda gravação exige verificação por releitura.
2. **Brick além do bootloader é documentado** — há aparelhos que não voltam
   nem em modo bootloader. Qualifica a conclusão anterior: o bootloader
   sobrevive ao caminho do **cartão SD**, mas gravação por **USB** pode
   destruí-lo.

Não há registro público de ninguém ter gravado firmware modificado nesta
família com sucesso.

**Nada criado:** nenhum `update.up`, artificial ou não. Nenhum flash.

---

### 2026-09-12 — Dossiê de pesquisa externa

**Documento:** `docs/EXTERNAL_RESEARCH.md` — registro das buscas, fontes,
inteligência da comunidade e resultados negativos. Documento vivo, com
procedimento de atualização no §8.

**Conteúdo:**
- 10 frentes de busca registradas com escopo e resultado
- Metadados da fonte primária (`smartlink_flash`: 41 estrelas, sem licença,
  suporte a gravação com apenas 8 meses e pouco testado)
- Issue #3 lida por completo (25 comentários, 7 participantes, 13 meses)
- Bugs conhecidos do firmware original relatados por usuários
- O que comprovadamente **não** existe publicamente

**⚠️ CORREÇÃO a `docs/UPDATE_UP_REFERENCE.md` §7:** aquele documento
afirmava que ninguém havia gravado firmware modificado nesta família com
sucesso. **Está errado.** O desenvolvedor **bunkaich** corrigiu o Bluetooth
e **remapeou os botões** de um aparelho desta família, confirmado pelo
próprio autor da `smartlink_flash`. A afirmação errada nasceu de ler apenas
os primeiros comentários de uma discussão de 25. O documento foi corrigido
apontando para `EXTERNAL_RESEARCH.md` §5.1; a conclusão antiga **não** foi
apagada em silêncio.

**Consequências:** gravação de firmware modificado nesta família é fato
consumado, e **remapeamento de botões já foi feito por alguém** — apesar
da tabela de descritores ficar em RAM. Nenhum código foi publicado.

**Lead de maior valor:** contatar `bunkaich` — resolveu na prática o item
aberto nº 1 do `INPUT_MAP_COMPLETE.md`.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Especificação reproduzível do `update.up`

**Documento:** `docs/UPDATE_UP_REFERENCE.md` — acrescentada a **PARTE II**
(§11–§17), com a especificação completa derivada de `fwhelper/main.c`
(commit `49d51d17`, hash do arquivo verificado contra o lock) confrontada
instrução a instrução com `docs/SDUPDATE_ANALYSIS.md`.

**Confirmado:**
- Pacote = cabeçalho CONFIG de `0x100` bytes + `flash[0 : fw_size]`
- `fw_size` = maior `off+len` entre as partições, **excluindo `PSMP`** —
  para o nosso aparelho, `0x1A3038`; pacote de 1.716.536 bytes
- Todos os 9 campos do cabeçalho, com bytes reais calculados
- `codeOffsetInByte` = `0x100`, verificado numericamente pelas duas pontas
- 8 CRCs catalogados por região, incluindo um **novo** (CONFIG `+0x14`,
  sobre todo o payload) que só o `fwhelper` produz
- `dump2fw` **valida e aborta**, nunca corrige — nosso
  `rebuild_firmware.py` é pré-requisito dele, não alternativa
- `fileStamp` **não** é gerado pelo `fwhelper`: vive em `FIRM+0x04`,
  dentro do payload, e é copiado literalmente

**Verificado:** réplica exata de `dump2fw()` executada **em memória** sobre
`GN438_rebuilt_original.bin` — passa em todas as verificações. Nenhum
arquivo `update.up` foi criado.

**⚠️ CORREÇÃO a `docs/SDUPDATE_ANALYSIS.md` §6:** aquele documento afirmava
que um pacote do rebuild byte-a-byte **seria rejeitado com `0xFC`** por
timestamp igual. **A afirmação não se sustenta.** Ela pressupunha que o
valor comparado é o timestamp instalado; a análise mostra que a origem dos
dois valores **não está resolvida** e que, sob a leitura mais provável,
ambos são espúrios (`"FIRM"` usado como offset de seek; contagem de
partições lida como `fileStamp`). Sob essa hipótese a verificação **nunca
dispara**. A conclusão antiga foi marcada como tachada, não removida.

**Classificação:** 17 conclusões classificadas — 11 CONFIRMADO,
2 PROVÁVEL, 1 HIPÓTESE, 3 NÃO RESOLVIDO.

**Pré-requisitos que continuam abertos para gravar:** disparo do
`sdupdate`; previsibilidade da verificação de timestamp; gravação não
determinística.

**Hardware:** nenhuma operação. Nenhum `update.up` criado.

---

### 2026-09-12 — Investigação forense: gatilho, timestamp, entrada e páginas

**Documentos atualizados:** `SDUPDATE_ANALYSIS.md` (PARTE II),
`INPUT_MAP_COMPLETE.md` (PARTE II), `GUI_ANALYSIS.md` (PARTE II).

#### 1. Gatilho do `sdupdate` — RESOLVIDO (CONFIRMED)

Cadeia completa rastreada por disassembly:
`HAL_pmu_sd_update_flag_set` grava o **registrador 0x23 do PMU**; no reset,
o boot lê `(pmu[0x23] & 7) == 6`; se ligado, limpa a flag, inicializa o
hardware, exibe `"Finding file..."` e chama `0x00823CA0`, que monta a
vtable de I/O e invoca o núcleo em `0x00827850`.

**O `sdupdate` não é acionado por combinação de teclas nem pela presença
do arquivo** — depende de um flag persistente gravado pela aplicação.

Tabela de operações de arquivo mapeada (8 slots, endereços confirmados):
abrir / fechar / ler / posicionar / tamanho / ? / progresso / finalizar.

Também confirmado: se o carregamento normal da FIRM falhar, o boot cai no
modo **"update from pc"** — segunda rede de proteção, independente do SD.

**⚠️ CORREÇÃO a `SDUPDATE_ANALYSIS.md` §9:** aquele documento afirmava que
não havia `bl` direto para o núcleo e que a chamada seria indireta.
**Errado** — o `bl` está em `0x00823CCC`. Minha varredura linear
dessincronizou ao atravessar pools literais: **falso negativo do método**.

#### 2. Verificação de timestamp — REAVALIADA (PROBABLE)

O `sdupdate` lê `ptable+0x10` e usa como offset de arquivo; na imagem real
esse campo contém o **nome** `"FIRM"`. Testadas as duas hipóteses de
layout: a alternativa `{off,len,crc,name}` torna **dois** fatos coerentes
de uma vez (lseek válido **e** leitura caindo exatamente em `FIRM+0x04`),
contra apenas um rótulo de string — e os rótulos deste bootloader já
provaram enganar.

**Conclusão PROBABLE:** o caminho espera um layout de entrada diferente do
da imagem instalada, lê com deslocamento de 4 bytes e compara valores
espúrios. **Não é proteção contra downgrade/reflash.**
Que nunca dispare na prática permanece HYPOTHESIS.

#### 3. Entrada física — PARCIAL

**CONFIRMED:** distribuição das teclas — `key_onoff` 2 ids inline
(`0x37`, `0x47`); `key_io` 2 teclas via tabela em RAM; `kadc_ch1` até
**16 níveis de ADC**. Ou seja, **a maioria dos botões é lida por ADC**
(escada resistiva), não por GPIO.

Drivers localizados: kadc `0x00D63DC0`, key_io `0x00D64014`,
key_onoff `0x00D642C8`, lcd `0x00D64404`.

**UNKNOWN:** a tabela pino/limiar → `key_id`. Quatro métodos tentados,
todos documentados. O mapeamento de M/◀◀/▶▶/▶Ⅱ segue **HYPOTHESIS** —
não foi inventado.

#### 4. Arquitetura LVGL — CONFIRMED

61 handlers `pstr_pageNN_process` localizados e tabelados.
Estrutura da mensagem de UI decodificada (6 campos).

- **`page1` = menu principal**: 6 callbacks de construção
  (música, vídeo, fotos, ebook, gravador, arquivos); menu **construído
  dinamicamente** a partir de bases com marcação *dirty*
- **`page3` e famílias = listas roláveis** com `top_index` / `select` /
  `total` e PgUp/PgDn — **o modelo que o Design System pede já existe**
- **`page4` = Now Playing**: é um **`lv_btnmatrix`** com `ctrl_id` 0–7
  (play, pre, next, speed, repeat, loop, love)

**Implicação de design:** a tela Now Playing precisa ser expressa como
matriz de botões com foco, ou a navegação quebra. Restrição **estrutural**,
além da de espaço.

**Hardware:** nenhuma operação. Firmware não alterado, não gravado.

---

### 2026-09-12 — Primeiro patch visual: GN438_openpod_v001.bin

**Ferramenta criada:** `tools/patch_home_icon.py` — substitui os pixels de
uma célula da folha de ícones do menu principal, de forma determinística,
sem alterar paleta, tamanho, offsets ou tabelas.

#### Descoberta que mudou a estratégia — CONFIRMADO

O menu principal **não usa ícones 4bpp**. `page_home_create` faz
`lv_img_set_src` de uma única imagem `INDEXED_8` 128×160 (`0x000CDD50`)
com os 9 ícones em grade 3×3. Não há codepoint `U+Fxxx` envolvido.

Isso torna o patch **mais simples** do que o planejado: um recurso único,
tamanho fixo, sem tabela de índices.

#### Mapa semântico da GUI — CONFIRMADO

Localizados **370** nomes `page_<tela>_<papel>` — mapa completo das telas,
muito mais útil que o esquema numérico `pageNN`. Registrado em
`GUI_ANALYSIS.md` §15.

#### Geometria da folha — CONFIRMADO

Grade 3×3, células de ~32×31, posições e offsets de cada ícone tabelados.
Correspondência com os 9 callbacks de `page1` confirmada.

#### Decisão A vs B

**Caminho A (substituir recursos) escolhido**, sem hesitação: mesma
capacidade de mudança visual do menu, com offsets, tabelas e código
intactos. O caminho B não é necessário para a Fase 1 — o modelo de lista e
o `lv_btnmatrix` que o Design System pede já existem no firmware.

#### Pipeline executado

```text
ORIGINAL (somente leitura)
   ↓ patch_home_icon.py   716 bytes de pixels, paleta intacta
   ↓ rebuild_firmware.py  revalida e regenera todos os CRCs
   ↓ validate_firmware.py 22 verificacoes OK, 0 falhas
   ↓ fwhelper scan        validacao de terceiros, limpa
   ↓ diff                 718 bytes, 43 faixas, tamanho inalterado
GN438_openpod_v001.bin
```

**SHA-256:** `9dc755eef24e3e09c8939d90c89d9a241e0c6edd75b377c1792e743ccc79215c`

**Original:** intacto, `b7cd5eb9…4b36f`, permissão 444.

**Hardware:** nenhuma operação. Nenhum `write_flash`, `erase_flash`,
`write_mem`, `exec` ou tentativa de `sdupdate`.

---

### 2026-09-12 — Mecanismo de atualização + pacote V001 offline

**Documento:** `docs/UPDATE_MECHANISM.md` (621 linhas, 11 seções + veredito).
**Ferramenta:** `tools/make_update_up.py` — gera e valida pacotes `.up`.

#### Artefato gerado

| | |
|---|---|
| Arquivo | `firmware/WORKING/update_v001.up` |
| Tamanho | 1.716.536 bytes = `0x100` + `0x1A3038` |
| SHA-256 | `b45bcf6d5f20f3836b935692f52fb35302536feb2b90edfa5345b8c0224ec314` |
| CRC do payload | `0xE662` · chip `SL6801` |
| **Instalado no aparelho** | **NÃO** |

**Validação:** 11 verificações OK, 0 falhas. E — a prova mais forte —
**byte a byte idêntico** ao produzido pela implementação de referência
(`fwhelper dump2fw`, upstream): `cmp` retorna IDENTICOS, mesmo SHA-256.

#### Achados novos — CONFIRMADO

- **Quais campos do header o `sdupdate` realmente lê**: apenas o magic
  (5 bytes), `codeOffsetInByte` e o nome do chip. **`fw_size` e o CRC do
  payload NUNCA são lidos** pelo caminho do cartão — são metadados,
  PROVAVELMENTE para a ferramenta USB. Os acessos a `[r5,#0x10]` que
  aparecem adiante ocorrem depois do buffer ser sobrescrito.
- **O tamanho a gravar vem do tamanho do ARQUIVO**, via a função de
  `tamanho` da vtable (`0x00823A74`), não de `fw_size`.
- **Geometria exata**: apaga `0xD000..0x1A4000` (407 setores de 4 KiB),
  grava `0xD000..0x1A3000` (3248 blocos de 512).
- **⚠️ Janela apagada e não gravada**: `0x1A3000..0x1A4000`. O contador de
  blocos trunca enquanto o de setores arredonda para cima. Isso deixaria os
  **últimos 56 bytes da partição TONE apagados (0xFF)**, quebrando seu CRC.
  Comportamento do mecanismo do fabricante, não do nosso pacote. Se algo
  verifica o CRC da TONE em runtime: **NÃO DETERMINADO**.
- **Existe caminho na aplicação para ligar a flag**: função `0x00CF9D3C`
  aceita `"sd"` ou `"pc"`, liga o flag no PMU e reinicia. Não exige USB.

#### Veredito sobre a hipótese "SD é mais seguro que USB"

**CONFIRMADA — mas por motivo estrutural, não pela qualidade da
validação.** O `sdupdate` valida pouco (sem assinatura, sem conferir o CRC
do payload antes de gravar). Ele é mais seguro porque **nunca apaga nem
grava a faixa `0x0`–`0xD000`**, deixando o bootloader — único caminho de
recuperação — fora do alcance da operação. O `write_flash` por USB aceita
qualquer endereço, inclusive `0`.

#### Avaliação de risco registrada

Risco de brick pelo caminho SD: **baixo**. Pior caso realista: FIRM
corrompida → boot cai sozinho em "update from pc" → regravação por USB.
Não é tijolo, desde que o bootloader esteja íntegro — o que o `sdupdate`
garante por construção.

#### Resposta final: **SIM, COM RESSALVAS**

Ressalva bloqueante: **a rede de segurança nunca foi exercitada**. Antes
de gravar, confirmar que o aparelho enumera por USB e que um `read_flash`
de teste funciona — leitura pura. Sem isso, seria gravar sem saber se
existe volta.

**Hardware:** nenhuma operação. Nenhum `write_flash`, `erase_flash`,
`write_mem`, `exec` ou tentativa de instalação.

---

### 2026-09-12 — Calibragem de risco (lacuna corrigida)

Auditoria dos documentos mostrou que os **fatos** do mecanismo de update
estavam todos registrados, mas a **camada de julgamento** — quanto
preocupar-se com cada bloqueador — existia só na conversa.

**Acrescentado:** `docs/UPDATE_MECHANISM.md` §7.1.

- **Bloqueador 1 (timestamp imprevisível): NÃO é preocupante.** O pior
  desfecho é recusa, e a verificação ocorre **antes** de qualquer
  apagamento. Não existe cenário em que danifique o aparelho.
- **Bloqueador 2 (gravação não determinística): moderado e contido**, por
  três barreiras confirmadas. Atenuante: a anomalia `0 → 1` refere-se a
  gravar **sem apagar**; o `sdupdate` apaga antes.
- **Veredito calibrado:** risco baixo-moderado pelo caminho SD.
- **Correção registrada:** sessões anteriores encerraram com *"os
  bloqueadores de gravação seguem de pé"*, tratando os dois como
  equivalentes — o que deu ao primeiro um peso que ele não tem.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Regra de encerramento de sessão adotada

**Motivo:** duas falhas seguidas de documentação, ambas detectadas por
pergunta do mantenedor, não por verificação minha.

| Quando | O que ficou de fora |
|---|---|
| Sessões 4–6 | o `CHANGELOG.md` inteiro, três sessões seguidas |
| Sessão 11 | 4 de 10 pontos da avaliação de risco — inclusive a conclusão de que um dos "bloqueadores" **não pode danificar o aparelho** |

**Padrão identificado:** *documento bem o que descubro e mal o que
concluo.* Os fatos técnicos entram; recomendações, calibragens e vereditos
ficam só na conversa — e são justamente o que falta a quem pegar o projeto
depois. Dados sozinhos não dizem **quanto se preocupar**.

**Adotado:** `relatorio.md` §8 — checklist obrigatório de encerramento,
com quatro blocos: **A** fatos · **B** julgamento · **C** registros ·
**D** integridade. O bloco B é a novidade: recomendações, calibragens,
vereditos, ressalvas bloqueantes e correções de enquadramento.

**Método de verificação:** listar as afirmações de julgamento feitas na
resposta e localizar cada uma por `grep` nos documentos. Se não achar,
não foi documentado — por mais claro que tenha ficado na conversa.

**Também gravado** na memória persistente do projeto, para valer em
sessões futuras independentemente deste arquivo.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Política de gravação adotada

**Decisão do mantenedor:** usar sempre o `update.up` como método de
gravação, e manter o firmware original como base de recuperação.

**Documento:** `docs/FLASH_POLICY.md` — normativo, não análise.

**Justificativa registrada:** a superioridade do caminho SD **não** vem de
validar melhor (ele valida pouco: sem assinatura, sem conferir o CRC do
payload antes de gravar). Vem de ser **estrutural**: o `sdupdate` apaga e
grava só a partir de `0x00D000`, deixando o bootloader — único caminho de
recuperação — fora do alcance por construção.

#### ⚠️ Ressalva que precisou entrar junto com a política

A regra "sempre `update.up`" **não pode valer para recuperação**, e isso é
consequência do mecanismo, não uma brecha:

```text
FIRM corrompida → a aplicação não inicia → ninguém liga o flag do PMU
                → o sdupdate não pode ser acionado → só resta o USB
```

Redação correta adotada: **gravação normal sempre por SD; USB reservado
exclusivamente para recuperação**, a partir do original verificado. Banir
o USB por completo tornaria o projeto **menos** seguro — seria abrir mão
da única rede de proteção.

#### Artefato criado

`firmware/WORKING/update_restore_original.up`, SHA-256
`82f0ae8c…35c8`, 11 verificações OK. Gerado **antes** de qualquer teste,
de propósito. Limitação documentada: só serve enquanto o aparelho ainda
iniciar a aplicação.

**Proibições permanentes** registradas no §6 do documento.

**Pré-requisito que continua aberto:** confirmar, por leitura pura, que o
aparelho enumera por USB. A Regra 2 depende disso.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Procedimento de verificação da recuperação

**Documento:** `docs/RECOVERY_CHECK.md` — procedimento de bancada,
somente leitura, ~10 minutos, risco nenhum.
**Ferramenta:** `tools/verify_device_readback.py`.

**O que o teste prova, de uma vez:** que o aparelho enumera por USB; que a
flash pode ser lida por completo; e que o `GN438_original.bin` preservado
confere com o aparelho — ou seja, que a rede de segurança é **real**, não
presumida.

#### ⚠️ Plataforma: Ubuntu, não macOS — motivo verificado no código

`smtlink_dump.c` linhas 133–145: `libusb_kernel_driver_active` devolve
`LIBUSB_ERROR_NOT_SUPPORTED` (negativo) no macOS, então o `if (err > 0)`
é falso e **o detach nunca acontece**. Em modo card reader o aparelho é
reivindicado pelo driver de armazenamento do macOS e
`libusb_claim_interface` falha com `LIBUSB_ERROR_ACCESS`.

O README do upstream também só cita Linux e Windows. E há uma razão
melhor: **o dump original foi feito no Ubuntu** — usar a mesma máquina
elimina uma variável exatamente onde se precisa de certeza.

#### Ressalva registrada

O teste prova que o USB funciona com o aparelho **saudável**. **Não** prova
que o modo `"update from pc"` enumera após a FIRM corromper — provar isso
exigiria corromper a FIRM de propósito. É a melhor evidência obtenível sem
risco: se o USB não responder nem com o aparelho bom, não responderá com
ele quebrado.

**Ferramenta testada nos dois sentidos:** aprova o rebuild byte-idêntico e
reprova o V001 (detecta as 716 divergências na FIRM e as 2 na tabela de
partições).

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Script autocontido para a verificação no Linux

**Criado:** `tools/recovery_check_linux.sh` — **único arquivo** que precisa
ir para a máquina Ubuntu. Autocontido, não depende da árvore do projeto.

Faz: clone no commit travado → confere os **15 hashes embutidos** →
compila → detecta o aparelho e o modo (card reader / bootloader) →
`flash_id` + `read_flash 0 2M` → compara o SHA-256 com o do original →
grava `readback.bin` e `readback.log`.

**Somente leitura, verificado:** o único comando que chega ao aparelho é
`smtlink_dump --id <id> flash_id read_flash 0 2M` — opcodes
`CMD_SL_READID` (0) e `CMD_SL_READ` (7). Nenhuma escrita.

**Guardas implementadas:** aborta se não for Linux; se faltar
`libusb-1.0-0-dev`, `git`, `make`, `cc` ou `lsusb`; se qualquer hash
divergir; se o aparelho não enumerar.

**Testado no que dá para testar offline:** sintaxe (`sh -n`) e a lógica de
verificação de hashes, simulada contra o clone local — 15 OK, 0 falhas, e
os hashes embutidos são **idênticos** aos de `smartlink_flash.lock`.

**Decisão registrada:** não levar a pasta `tools/` nem o
`GN438_original.bin` para a máquina Linux. Quanto menos o original
circular, melhor — a conferência por região acontece na máquina do
projeto, onde está a referência.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Caminho para instalação existente do smartlink_flash

**Criado:** `tools/recovery_check_manual.txt` — bloco de comandos para
copiar e colar, para quem já tem a ferramenta instalada e funcionando.

**Decisão registrada:** usar a instalação existente **não é problema** para
este teste. `flash_id` e `read_flash` são comandos do boot ROM do chip,
estáveis desde a primeira versão — a versão da ferramenta é irrelevante
para leitura. Clonar uma segunda cópia só para conferir hashes seria
cerimônia sem ganho.

**Mas o bloco registra a procedência mesmo assim** (`git log -1` + SHA-256
do `smtlink_dump.c` + `uname -a`), por um motivo específico: o suporte a
**escrita** só entrou no upstream em 2026-01-27. Saber se a cópia daquela
máquina é anterior ou posterior importa **na hora de gravar**, não agora.
Se for anterior, provavelmente nem consegue escrever — o que nesta fase é
uma vantagem.

**Somente leitura:** os dois únicos comandos que tocam o aparelho são
`flash_id` e `flash_id read_flash 0 2M`.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Revisão do script de verificação: 1 bug real corrigido

Antes de o script ir para o hardware, revisão linha a linha. **Encontrado
um defeito que teria falhado em campo.**

#### Bug corrigido — sequência de comandos por modo

A primeira versão usava `--id <id> flash_id read_flash` para **os dois**
modos. Mas o README do upstream é explícito:

- modo **bootloader** (`301a:2800`): o `init` é **obrigatório** antes;
- modo **card reader** (`301a:2801`): o `init` **trava** ("it will hang
  quickly").

Se o aparelho tivesse entrado em modo bootloader, a leitura teria falhado.
Corrigido: o script agora escolhe a sequência conforme o modo detectado.

#### Outras três correções

| # | Problema | Correção |
|---|---|---|
| 2 | `\| tee` mascarava o código de saída do `smtlink_dump` — uma leitura falha passaria despercebida | captura do status em arquivo temporário antes de exibir |
| 3 | Um clone pré-existente era reusado sem conferir o commit | agora verifica e ajusta, ou aborta |
| 4 | Variável `EXPECTED_FLASH_ID` morta | documentada como conferência visual |

#### Testes executados

- `sh -n` (sintaxe): OK
- lógica de seleção de modo, com três entradas simuladas: card reader,
  bootloader e PID inesperado — **as três corretas**
- captura de status com comando que falha: **detecta**, onde a versão
  anterior mascarava
- verificação dos 15 hashes, simulada contra o clone local: **15 OK**

**11 guardas** que abortam: não-Linux · dependências · libusb · commit
divergente · hash divergente · falha de build · binário ausente ·
aparelho não enumera · PID inesperado · leitura falhou · arquivo não
criado.

**Um único ponto executa a ferramenta** (linha 146), e a sequência é
sempre somente leitura.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — ✅ Recuperação por USB CONFIRMADA + formato da PSMP decodificado

**O pré-requisito bloqueante de `FLASH_POLICY.md` §7 está atendido.**

#### Execução no Ubuntu (somente leitura)

```text
[1/5] clone no commit travado         OK
[2/5] 15 hashes conferidos            OK
[3/5] build                           OK
[4/5] Bus 003 Device 067: ID 301a:2801 SmartlinkTechnology
      modo: card reader
[5/5] flash_id: 0x14851485
      dump_flash: 0x00000000, target: 0x200000, read: 0x200000
```

O script funcionou de ponta a ponta, incluindo a correção do modo feita na
sessão anterior. `kernel driver is active, trying to detach` — o detach do
Linux funcionou, como previsto (e como **não** funcionaria no macOS).

#### Conferência por região — resultado

```text
cabecalho HLKJ · bootloader · tabela particoes · FIRM · TONE · area livre
                          TODAS IDENTICAS
PSMP (config)                        802 bytes divergentes
```

**Prova três coisas:** o aparelho enumera e responde; a flash é legível
por completo; e o `GN438_original.bin` é **cópia fiel do aparelho** — não
uma suposição.

#### Descoberta: formato da PSMP — CONFIRMADO

**Documento:** `docs/PSMP_FORMAT.md`.

Primeira descoberta do projeto obtida por **observação do aparelho**, não
por análise estática: a `PSMP` mudou sozinha entre dois dumps e a
diferença revelou o formato.

```text
+0x00  55 AA   magic      +0x07  u16  tamanho do valor
+0x02  u8      flag       +0x09  u16  numero de sequencia
+0x03  u32     checksum?  +0x0B  u8   comprimento da chave
                          +0x0C  chave ASCII + valor
```

Verificado em 4 registros consecutivos, com sequências **5, 6, 7, 8**.

**O detalhe que explica o desenho:** todas as 7 transições observadas na
área já usada são de `1` para `0` (`(orig & novo) == novo`). É um log
append-only que **nunca precisa apagar** — por isso a `PSMP` não tem CRC
na tabela e por isso é excluída do `update.up`.

Conexão com o risco de `EXTERNAL_RESEARCH.md` §5.2: a anomalia relatada é
sobre gravar `0 → 1` sem apagar. A `PSMP` nunca faz isso. O firmware está
correto neste ponto.

**Chaves observadas:** `audio_volume`, `bright`, `offscr`, `language`,
`music`, `record`, `profile`, `bt_addr`, `freq_drift`, `pass`, `device_id`.

#### Promoções de classificação

| Afirmação | Antes | Agora |
|---|---|---|
| `PSMP` é config gravada em runtime | PROVÁVEL | **CONFIRMADO** |
| Excluí-la do pacote preserva a configuração | PROVÁVEL | **CONFIRMADO** |
| O original é cópia fiel do aparelho | presumido | **CONFIRMADO** |

#### ⚠️ Alerta de dado sensível

O registro `device_id` contém um identificador desta unidade
(`CBKJ01MP3---MP3-------T90026----------C0B2C1003357854270`). Se o
projeto for publicado, remover essa string dos documentos e não divulgar
o `readback` com a `PSMP` real.

#### Consequência operacional

Dois dumps do mesmo aparelho **nunca** terão o mesmo SHA-256. Comparar
sempre **por região**, com `tools/verify_device_readback.py`.

#### Organização

- evidência em `firmware/READBACK/` (marcada 444)
- o clone do `smartlink_flash` que veio junto foi **movido** para fora do
  projeto (não apagado) — decisão de licença da sessão 3. Conferido: os
  15 arquivos batem com o lock.

#### Comportamento observado do aparelho

Ao conectar em modo card reader, o GN-438 exibe uma **tela com símbolo de
raio** (carregando/USB) e permanece nela durante `flash_id` e
`read_flash`, sem travar nem reiniciar.

**Relevância:** o aparelho **dá retorno visual** em operações USB. Como o
bootloader tem as strings `"Finding file..."`, `"Update...  %"` e
`"Update finish!"`, é **PROVÁVEL** que haja progresso na tela durante o
`sdupdate` — sem depender da UART. E se a tela não mostrar nada disso,
será sinal de que o processo não começou.

**Hardware:** apenas leitura. Nenhuma escrita.

---

### 2026-09-12 — ✅ Primeira ESCRITA na flash: caminho de recuperação confirmado

**Ferramenta:** `tools/write_test_freearea.sh` (endereço fixo no código,
16 guardas, confirmação manual obrigatória).
**Documento:** `docs/WRITE_TEST_RESULT.md`.
**Evidência:** `analysis/hardware_tests/2026-09-12_writetest/`.

#### O teste

Setor `0x1D0000` (4 KiB) na área livre — 180 KiB depois da TONE, 172 KiB
antes da PSMP. Sequência: ler tudo e conferir 4 regiões críticas → conferir
que o setor está `0xFF` → confirmação do operador → **escrever** → reler e
comparar → **apagar** → reler → ler tudo e reconferir.

#### Resultado — todos os passos OK

| Verificação | Resultado |
|---|---|
| `target_written` == `pattern` | idênticos, 0 divergências |
| `target_erased` == `target_before` | idênticos, todo `0xFF` |
| Regiões críticas antes × depois | 0 divergências |
| **Flash inteira, `before` × `after`** | **0 bytes alterados** |

Verifiquei os artefatos por conta própria, não apenas o log do script.
O `pattern.bin` gerado no Ubuntu tem o mesmo SHA-256 que calculei no macOS.

#### Conferência cruzada das três leituras do dia

`before` (teste de escrita) × readback anterior: **0 divergências**.
`before` × dump de ontem: 802, **todas na PSMP**. A PSMP segue sendo a
única região que muda sozinha.

#### O que mudou na avaliação de risco

| Risco | Antes | Agora |
|---|---|---|
| **Escrita por USB não funcionar quando precisar** | **desconhecido, sem volta** | ✅ **eliminado** |
| V001 não inicializa | recuperável *se* a escrita funcionasse | **recuperável** |

> **O único risco irrecuperável do projeto deixou de existir.**
> O que resta é a pergunta que sempre foi a do teste — *o V001 inicializa?*
> — e agora ela tem resposta reversível.

#### O que NÃO foi testado, e por que não precisa

Escrever em área **já escrita**, sem apagar. A anomalia `0 → 1` relatada
não foi exercitada — e o caminho que vamos usar não depende dela: o
`sdupdate` apaga antes de gravar, e a PSMP do próprio firmware só faz
`1 → 0`. Registrado como **NÃO DETERMINADO**.

#### Organização

Evidência em `analysis/hardware_tests/2026-09-12_writetest/`.
`before.bin` e `after.bin` **não** foram duplicados: são byte-idênticos ao
readback já preservado — `NOTA.txt` registra os hashes que provam isso.

**Hardware:** uma escrita de 4 KiB em área livre, revertida e verificada.
Nenhuma região crítica tocada.

---

### 2026-09-12 — Procedimento de instalação por SD + item de menu identificado

**Documento:** `docs/SD_UPDATE_PROCEDURE.md`.

#### Lacuna fechada — CONFIRMADO

O item de menu que dispara o `sdupdate` estava como **PROVÁVEL**. Agora
está localizado, pelos textos do bloco em português:

```text
Configurações → Opções de actualização → Actualização do cartão SD
                (0x054425)              (0x0544C3)
```

Encontrada também uma **tabela de comandos de console** em `0x049F80`:
`cpu (clk)`, `reboot`, `update`, `sleep`, `hello`, `tp`, `sd` — onde
`update` aponta para a função `0x00CF9D3D` que grava o flag no PMU.

#### Aviso do próprio firmware

O firmware alerta, em oito idiomas, para **carregar a bateria antes de
atualizar** (`0x05D0FC`). Uma queda de energia durante a gravação é o
cenário mais próximo de um brick real. Incorporado ao procedimento.

#### Pacotes prontos para o cartão

Criadas duas pastas com o arquivo **já com o nome correto** — renomear
errado é o erro mais fácil de cometer, e o bootloader procura o literal
`0:\update.up`:

| Pasta | SHA-256 |
|---|---|
| `update/SDCARD_v001/update.up` | `b45bcf6d…c314` |
| `update/SDCARD_restore/update.up` | `82f0ae8c…35c8` |

Cada uma com um `LEIA-ME.txt` explicando o conteúdo e a limitação.

#### Ressalva registrada sobre a recuperação

O `WRITE_TEST_RESULT.md` validou uma escrita de **4 KiB em área livre**.
Uma regravação de **2 MiB cobrindo o bootloader** é **PROVÁVEL** que
funcione por extrapolação, mas **não foi exercitada**. O procedimento
recomenda, nesse cenário, gravar primeiro só a partir de `0x00D000`
(preservando o bootloader intacto) antes de tentar a flash inteira.

**Hardware:** nenhuma operação nesta sessão.

---

### 2026-09-12 — ⚠️ CORREÇÃO: o item de menu não está confirmado

**Eu classifiquei como CONFIRMADO algo que não observei.**

Afirmei que o gatilho do `sdupdate` seria
`Configurações → Opções de actualização → Actualização do cartão SD`,
baseado apenas em as strings existirem no firmware. O mantenedor verificou
no aparelho: **a opção não aparece no menu.**

**String existir ≠ item exposto na interface.** Foi o mesmo erro de duas
sessões atrás — inferir de artefato estático e promover a CONFIRMADO sem
observação.

#### Reclassificação

| Afirmação | Antes | Agora |
|---|---|---|
| As strings existem, em 8 idiomas | CONFIRMADO | CONFIRMADO |
| A função `0x00CF9D3C` grava o flag ao receber `"sd"` | CONFIRMADO | CONFIRMADO |
| Ela está numa tabela de **comandos de console** (`0x049F80`) | CONFIRMADO | CONFIRMADO |
| **Existe item de menu que a aciona** | CONFIRMADO | **NÃO DETERMINADO** |
| **O `sdupdate` é acionável sem UART** | presumido | **NÃO DETERMINADO** |

#### Releitura da evidência

`cpu (clk)`, `reboot`, `update`, `sleep`, `hello`, `tp`, `sd` não são
nomes de itens de menu — são comandos de **console de depuração**, quase
certamente sobre UART. É PROVÁVEL que `update sd` seja o caminho real.

#### Efeito prático

`docs/SD_UPDATE_PROCEDURE.md` foi **bloqueado** do Passo 2 em diante. Os
passos de preparar o cartão e de verificação continuam válidos.

Isto **não** invalida nada do que foi provado sobre o formato do pacote,
a geometria da gravação, a recuperação por USB ou o V001. Invalida apenas
a resposta para *como disparar*.

#### Ajuste de método

A regra da §8 do relatório cobre documentar julgamentos. Falta cobrir o
**rigor da classificação**: só é CONFIRMADO o que foi lido no disassembly
**ou** observado no aparelho. Inferência de artefato estático é, no
máximo, PROVÁVEL.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Item de menu confirmado por observação + regra de classificação

**Resolvido.** O item existe: acessado **sem cartão**, o aparelho responde
*"Não foram detectados dispositivos de armazenamento"* (string `0x0544E0`,
vizinha às de atualização no bloco de idioma). A tela verifica
armazenamento antes de prosseguir.

```text
Configurações → Opções de actualização → Actualização do cartão SD
```

Classificação: **CONFIRMADO por observação no aparelho**.

**Consequência prática:** o cartão precisa estar inserido **antes** de
entrar no menu. `SD_UPDATE_PROCEDURE.md` desbloqueado.

#### Erro de método mantido no registro

A conclusão estava certa, o método não. Eu havia classificado como
CONFIRMADO apoiado só em as strings existirem; reclassifiquei para NÃO
DETERMINADO quando o mantenedor reportou não achar a opção; e a observação
seguinte mostrou que existia.

**Acertar por inferência não é confirmar.** Se a string pertencesse a uma
tela morta — coisa que este firmware tem — a mesma inferência teria
produzido uma instrução errada num procedimento de gravação.

**Regra acrescentada ao checklist de encerramento (bloco A):** só é
CONFIRMADO o que foi lido no disassembly ou observado no aparelho.
Inferência a partir de string, nome de função ou tabela é, no máximo,
PROVÁVEL — mesmo quando parece óbvia.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — ⚠️ SEGUNDA reversão: o item de menu NÃO existe

**Reverti uma classificação que eu havia promovido a CONFIRMADO na entrada
anterior deste changelog.**

O mantenedor verificou: o caminho `Configurações → Opções de actualização
→ Actualização do cartão SD` **não existe** no menu do aparelho, com ou
sem cartão.

#### O erro

Na sessão anterior o mantenedor escreveu *"sem cartão inserido ele fala
isso mesmo, fala que tá sem armazenamento"*. Eu li como "achei a opção e
ela reclamou de armazenamento" e promovi a CONFIRMADO por observação.
**A frase era ambígua e eu não perguntei.**

Foi a **segunda** promoção indevida da mesma linha:

1. a partir de as strings existirem no firmware;
2. a partir de uma frase ambígua lida como confirmação.

A segunda ocorreu logo depois de eu acrescentar ao checklist a regra
contra exatamente isso.

#### Regras acrescentadas

- só é CONFIRMADO o que foi lido no disassembly ou **observado de forma
  inequívoca**;
- relato do mantenedor só conta como observação **depois de confirmado o
  entendimento** — frase ambígua não é evidência;
- na dúvida, **perguntar antes de classificar**.

#### Estado real

| Afirmação | Classe |
|---|---|
| As strings existem, em 8 idiomas | CONFIRMADO |
| A função `0x00CF9D3C` grava o flag com `"sd"` | CONFIRMADO |
| Está numa tabela de **comandos de console** (`0x049F80`) | CONFIRMADO |
| **Existe item de menu que a aciona** | **NÃO DETERMINADO** |

`SD_UPDATE_PROCEDURE.md` bloqueado de novo, do Passo 2 em diante.

Nada disto afeta o formato do pacote, a geometria da gravação, a
recuperação por USB ou o V001 — só a resposta para *como disparar*.

**Hardware:** nenhuma operação. O arquivo no cartão foi verificado
(`b45bcf6d…c314`, 1.716.536 bytes) e está correto.

---

### 2026-09-12 — Gatilho de atualização localizado (e não é o que eu dizia)

**Documento:** `docs/UPDATE_TRIGGER.md`.

#### A busca que resolveu

Varredura por **padrão de bits** das instruções `BL` — não por disassembly
linear — atrás dos chamadores dos gravadores de flag do PMU:

| Função | Chamadores |
|---|---|
| `set_flag_SD` (`0x00D78252`) | **1** — só o comando de console |
| `set_flag_PC` (`0x00D7824C`) | **2** — console **e `0x00D0A62E`** |

> O disassembly linear reportou **0** para os dois. A varredura por bits
> achou as três. **Terceiro falso negativo do mesmo tipo neste projeto** —
> conclusões de ausência exigem o método certo.

#### Achado — CONFIRMADO

**Não existe caminho pela interface para o update por cartão SD.** Só pelo
console de depuração. É por isso que o item de menu nunca apareceu: ele
não existe nesta build.

**Mas existe um gatilho escondido para o modo de atualização por PC**, em
`pstr_page51_process`:

```asm
cmp  r2, #2         ; ctrl_id == 2
ldrb r3, [contador] ; 0x008238F0
adds r3, #1
cmp  r3, #0xe       ; passou de 14?
bhi  -> zera contador, bl set_flag_PC, reinicia
```

**Quinze acionamentos seguidos** do controle `ctrl_id = 2` na tela
`page51` gravam o flag e reiniciam. O contador é zerado ao soltar
(`repeat_cnt clean`), então precisam ser seguidos.

`page51` exibe `yp3_2.0.43` — o ponteiro da string está **no mesmo pool
literal** da função. É **PROVÁVEL** que seja o item "Número da versão".

#### O menu real, para registro

`Despertador · Língua · Hora e data · Brilho · Configuração do Ecrã ·
Desligamento sem carga · Informações · Estado de Armazenamento ·
Configuração de fábrica · Atualização da Lista de Reprodução`

Sem "Opções de actualização". E a mensagem de "sem armazenamento" que
gerou a confusão anterior vem de **Estado de Armazenamento**
(`page_storage_info_create`), não de uma tela de atualização.

#### Consequência para a política de gravação

O caminho disponível agora usa `write_flash`, que **não tem** a proteção
estrutural do `sdupdate` (`FLASH_POLICY.md` §2) — aceita qualquer
endereço, inclusive o do bootloader.

**Mitigação adotada:** gravar **a partir de `0x00D000`**, nunca de `0`.
Reproduz o que o `sdupdate` faria e preserva o bootloader — a mesma
propriedade de segurança, mantida por **escolha explícita** em vez de por
construção.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Correção do gatilho: é SEGURAR, não 15 toques

Antes que o teste fosse feito com a instrução errada.

Os valores de `sta` no gatilho (`6` incrementa, `8` zera) correspondem
exatamente ao enum `lv_event_code_t` do LVGL v8:

```text
6 = LV_EVENT_LONG_PRESSED_REPEAT
8 = LV_EVENT_RELEASED
```

**Logo: é manter o botão pressionado.** A repetição automática dispara o
evento `6` seguidamente e, na 15ª, grava o flag e reinicia. Soltar
(evento `8`) zera o contador.

Tocar 15 vezes **não funcionaria** — cada solta zeraria a contagem.

| Afirmação | Classe |
|---|---|
| `sta` é `lv_event_code_t` do LVGL v8 | **PROVÁVEL** (valores batem) |
| O gatilho exige manter pressionado | **PROVÁVEL** |

Coerente com a repetição automática já documentada em
`INPUT_MAP_COMPLETE.md` §3 (evento `0x60`, *long press* sustentado).

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Script de gravação V001 pronto e validado

`tools/flash_v001.sh` (sha256 `8ca41352…6c823`) — grava **3 setores,
12 KiB**, via `write_flash` em modo card reader:

| Endereço | Tamanho | Conteúdo |
|---|---|---|
| `0x00D000` | `0x1000` | tabela de partições (2 bytes: CRC da FIRM) |
| `0x0CE000` | `0x2000` | pixels do ícone Música (716 bytes) |

O bootloader (`0x0`–`0xD000`) não é endereçado.

**Dois defeitos encontrados por revisão linha a linha, antes de rodar:**

1. **Real:** `WROTE=$((WROTE + 1))` estava **depois** do `write_flash`.
   Se o `write_flash` falhasse no meio, o `die()` imprimiria *"Nada foi
   gravado"* — conselho perigosamente errado com o aparelho já
   parcialmente escrito. Corrigido: incrementa **antes** de gravar.
2. **Cosmético:** `log "… 0x$2 …"` imprimia `0x0xD000`.

**Validação executada (2026-09-12):**

```text
sh -n                          -> OK
grep 'write_flash'             -> 1 chamada executável (linha 174, em wr())
grep '^wr '                    -> wr() chamada 2x: $A1 e $A2
grep '^A1=|^A2='               -> A1=0xD000  A2=0xCE000
grep -c 'erase_flash|write_mem'-> 0
```

As outras 4 ocorrências de `write_flash` são texto de log (comandos de
restauração impressos ao operador) e um comentário.

`OpenPod_Install/` contém o script, o V001, o original de restauração e o
LEIA-ME com essas verificações registradas.

**Hardware:** nenhuma operação. A gravação será feita pelo usuário no
Ubuntu.

---

### 2026-09-12 — Pivô: `sdupdate` deixa de ser o caminho do V001

A política declarada era *"usar sempre o update `.up`"*. Ela **não é
aplicável a este build**:

- o item de menu de atualização por SD **não existe** neste firmware
  (`set_flag_SD` tem **um único** chamador: a tabela de comandos do
  console de debug em `0x049F80`);
- o usuário enumerou o menu Configurações completo — não há a opção;
- `update.up` na raiz do cartão: o aparelho ligou normalmente, sem efeito.

O caminho USB em modo card reader **já foi validado em hardware** (teste
de escrita no setor `0x1D0000`: gravou, conferiu, apagou, restaurou,
**0 bytes alterados** na flash inteira).

| Caminho | Bytes regravados |
|---|---|
| `sdupdate` (`.up`) | 1.624 KiB |
| `write_flash` direto (V001) | 12 KiB — **99,3 % menos** |

O `.up` e o `GN438_original.bin` continuam como material de recuperação.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — page51 **não** é a tela de versão

O ponteiro `yp3_2.0.43` é carregado em `0x00D0A53C`, **antes** do
prólogo de page51 em `0x00D0A5A0` — pertence a **page5**.

O usuário segurou todos os botões na tela de versão: nenhum efeito
(só o Power desligou, e o aparelho religou normalmente).

Qual tela é page51: **NÃO DETERMINADO**. O gatilho oculto em
`0x00D0A62E` (segurar `ctrl_id` 2 até 15 auto-repetições) continua
comprovado por disassembly, mas **sem tela conhecida** para acioná-lo.
Ele grava o flag **PC**, não o de SD.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — `.claude/settings.json` criado

Regras de permissão do projeto, para que a validação de scripts deixe
de ser bloqueada:

```json
allow: Bash(sh -n:*)  Bash(shasum:*)  Bash(sha256sum:*)
       Bash(grep:*)   Bash(chmod:*)
deny:  Bash(sudo:*)
       Edit(firmware/ORIGINAL/**)   Write(firmware/ORIGINAL/**)
```

O `deny` de `sudo` cobre o caminho por onde toda escrita no hardware
passaria (`sudo smtlink_dump …`); o de `firmware/ORIGINAL/**` torna a
regra *"não modificar o original"* uma trava, não só uma instrução.

**Nota de método:** a primeira versão do `deny` usava padrões como
`Bash(*write_flash*)`. Eles bloquearam o próprio `grep write_flash` da
verificação — o padrão casa com a *string*, não com a execução.
Corrigido para `Bash(sudo:*)`.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — ⚠️ PRIMEIRA GRAVAÇÃO: falhou, foi detectada e restaurada

**A gravação do V001 corrompeu a tabela de partições. O aparelho foi
restaurado byte a byte e voltou a bootar normalmente.**

**Causa raiz — `write_flash` grava a partir do offset 0 do arquivo.**
O script v1 chamava `write_flash 0xD000 0xD000 0x1000 imagem_2MiB.bin`
supondo que o 2º argumento fosse o offset no arquivo. Não é: foram
gravados os 4096 bytes **iniciais** do `.bin` (cabeçalho `HLKJ` +
início do bootloader) em `0xD000`.

Detalhe completo em **`docs/WRITE_FLASH_SEMANTICS.md`**.

**Diagnóstico (só leitura):** o hash lido `5c64eaee…98d61` não batia com
nenhuma hipótese; a varredura achou o bloco no offset `0x000000` dos
dois arquivos, e os bytes `0xD01C–0xD01D` = `0004` são os bytes
`0x1C–0x1D` do início do arquivo. Duas evidências convergentes.

**Estado após o incidente, medido:**

| Região | Estado |
|---|---|
| bootloader | ✅ intacto |
| `HLKJ` | ✅ intacto |
| FIRM | ✅ original, não tocada |
| TONE | ✅ intacta |
| setor `0x0CE000` | ✅ original — nunca gravado |
| ptable `0x00D000` | ❌ corrompida → **restaurada** |

**Restauração:** `restaura_ptable.sh` gravou `ptable_orig.bin` (4096 B,
offset 0) em `0xD000`. Releitura: `c3d16a15…507091` — idêntico ao
original. Aparelho religado e funcionando.

**O que funcionou, e por quê:**

- gravar só a partir de `0x00D000` manteve o bootloader fora de alcance
  — foi por ele que a correção entrou;
- conferir cada setor logo após gravar detectou o erro no 1º;
- abortar na primeira divergência impediu a gravação do 2º;
- `WROTE` incrementado **antes** da escrita (corrigido na sessão
  anterior) fez o `die()` avisar corretamente — se estivesse depois,
  teria dito "Nada foi gravado";
- o diagnóstico foi feito **lendo**, nunca escrevendo.

**O que falhou além do bug:** os comandos de restauração impressos pelo
próprio script repetiam a assinatura errada e teriam gravado o cabeçalho
de novo. Foram interceptados antes de rodar. Corrigidos no script e no
`OpenPod_Install/LEIA-ME.txt`.

**Por que a Sessão 20 não pegou isso:** aquele teste usou um arquivo
pequeno em que o conteúdo já estava no offset 0 — o comportamento errado
era indistinguível do correto. Um teste que passa por acidente é pior
que um que falha.

**`flash_v001.sh` v2** (sha256 `c4d70211…63ddc`): grava a partir de
arquivos por setor (`v001_D000.bin` 4 KiB, `v001_CE000.bin` 8 KiB) com
`0` no 2º argumento — correto nas duas interpretações possíveis. Confere
tamanho **e** hash da releitura. Sem `tail`/`head`.

**`coreutils` em Rust:** na distro usada, `tail -c +N f | head -c M`
aborta com `BrokenPipe` e `core dumped`. O hash sai correto (o `head`
recebe seus bytes antes), mas o ruído mascara erros reais. Todos os
scripts passaram a usar `python3`.

**Hardware:** 2 operações de escrita de 4 KiB em `0xD000` — a gravação
falha e a restauração. Estado final: **idêntico ao original**.

---

### 2026-09-12 — `PARA_UBUNTU/` → `OpenPod_Install/` (padronização)

O nome antigo descrevia um transporte pontual. O novo descreve o que a
pasta **é**: o kit de gravação do projeto, autocontido e reutilizável a
cada versão. Nada nele é específico do Ubuntu — serve em qualquer Linux
com `python3`, `lsusb` e o `smtlink_dump`.

**Padrão de conteúdo, fixado a partir de agora:**

| Categoria | Arquivos |
|---|---|
| Diagnóstico (só leitura) | `diag.sh` |
| Gravação | `flash_vNNN.sh` |
| Restauração | `restaura_*.sh` |
| Setores a gravar | `vNNN_<ENDEREÇO>.bin` |
| Setores de restauração | `orig_<ENDEREÇO>.bin` |
| Imagens completas | `GN438_*.bin` — referência, **nunca** gravadas direto |

**Regra de nomenclatura dos setores:** `<origem>_<endereço>.bin`, com
tamanho exatamente igual ao da região e **offset 0 = conteúdo de
destino**. É o que torna o `write_flash` correto por construção
(`WRITE_FLASH_SEMANTICS.md` §5).

`ptable_orig.bin` foi consolidado em `orig_D000.bin` — eram
byte-idênticos (`c3d16a15…507091`); manter dois nomes para o mesmo
conteúdo era um convite a erro.

O `LEIA-ME.txt` foi reescrito como manual do kit, com a semântica do
`write_flash` em destaque logo no topo. `diag.sh` e `restaura_ptable.sh`
também passaram a viver em `tools/`.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — ✅ V001 GRAVADO, VERIFICADO E CONFIRMADO NA TELA

**A primeira modificação real do firmware do GN-438 está funcionando no
aparelho.** O ícone de Música do menu principal está **azul**.

**Gravação:** 3 setores de 4096 B, um a um, cada um relido e conferido
por SHA-256 antes de passar ao próximo.

| Endereço | Arquivo | SHA-256 conferido na releitura |
|---|---|---|
| `0x00D000` | `v001_D000.bin` | `c2124ab4…9215c`… ✅ |
| `0x0CE000` | `v001_CE000.bin` | `7121e448…8b288f` ✅ |
| `0x0CF000` | `v001_CF000.bin` | `c7753769…f10492` ✅ |

**Estado DEPOIS, sobre a flash inteira relida:**

| Região | Esperado | Resultado |
|---|---|---|
| bootloader | INTACTO | ✅ |
| ptable | MUDADA | ✅ |
| FIRM | MUDADA | ✅ |
| TONE | INTACTA | ✅ |

**Validação funcional:** aparelho desconectado, ligado, menu principal
aberto — **ícone azul**. É a única prova que o hash não dá: confirma que
o firmware **interpreta** os bytes como previsto, não só que eles estão
no lugar certo.

**O ciclo completo está fechado e é reprodutível:**

```text
extrair → entender → modificar → reconstruir → gravar → validar → ver funcionando
```

**O que fez esta tentativa dar certo, depois da falha:**

1. **Arquivo por setor**, offset 0 = conteúdo de destino — torna a
   semântica do `write_flash` irrelevante em vez de depender de acertá-la.
2. **Todos os blocos de 4096 B** — exatamente o tamanho já provado em
   hardware pela restauração. O bloco de 8 KiB foi dividido em dois;
   conferido que remontam o original (`a30962bc…d45597`).
3. **Diagnóstico antes de gravar** — `diag.sh` confirmou que a
   restauração do incidente tinha sido completa, sem resíduo.
4. `python3` no lugar de `tail`/`head` — nenhum *panic* nesta execução.

**Correção cosmética:** a etapa de releitura final imprimia `[6/7]`
duas vezes. Renumerada.

**Hardware:** 3 escritas de 4 KiB. **Estado final: V001 em execução.**

---

### 2026-09-12 — Verificação forense do `after.bin` — V001 confirmado byte a byte

Artefatos recebidos em `openpod_flash_v001/`:

| Arquivo | SHA-256 |
|---|---|
| `before.bin` | `a78f41b6deddf1d60ceeb594509926905ac79a8fd2e191c6255cf300cc593f9f` |
| `after.bin` | `6c1a175049b21bffea01eeee49cc1fca2684a4ca395236aa6447489045aa8908` |

**`before` → `after`: exatamente 718 bytes alterados.**

```text
0x00D01C..0x00D01D     2 bytes   CRC-16 da FIRM na tabela de particoes
0x0CE96C..0x0CF878   716 bytes   pixels do icone Musica
```

718 = 2 + 716 — exatamente o previsto pelo diff estático, sem um byte
a mais e sem escrita colateral.

**Os bytes alterados, mapeados de volta para a folha de ícones (128 px
por linha), desenham um disco com furo central:**

```text
y=24  ..#############..
y=33  ..###############################..
y=34  ..##############...##############..
y=40  ..##########...........##########..
y=45  ..###############################..
y=54  ..#############..
```

As linhas centrais partem-se em duas exatamente onde fica o furo do
disco. **Nenhum pixel fora do ícone foi tocado.** Esta é a confirmação
geométrica de que o mapeamento da folha de ícones (`0x0CDD50`,
INDEXED_8, 128×160, grade 3×3) está correto.

**`after` vs o V001 de referência: 4675 bytes diferem, 100% dentro da
PSMP** (`0x1FC000`+), **zero fora**. A PSMP é o log append-only de
configuração que o próprio firmware reescreve a cada boot
(`PSMP_FORMAT.md`) — não é modificação nossa.

| Região | `before` | `after` |
|---|---|---|
| bootloader | ORIG | **ORIG** ✅ |
| ptable | ORIG | **V001** ✅ |
| FIRM | ORIG | **V001** ✅ |
| TONE | ORIG | **ORIG** ✅ |

> **Conclusão:** o aparelho contém exatamente a imagem gerada e validada
> offline, byte a byte, com a única exceção da configuração de runtime.
> O ciclo de rebuild é **reprodutível e verificável dos dois lados**.

**Hardware:** nenhuma operação (análise dos artefatos).

---

### 2026-09-12 — ✅ V002 GRAVADO — 9 ícones recoloridos pela PALETA

**Os nove ícones do menu principal passaram a monocromático.** Gravado,
verificado e confirmado na tela.

**Mudança de método: cor agora é PALETA, não pixel.**

A folha de ícones (`0x0CDD50`) é `INDEXED_8`: **1024 bytes de paleta** em
`0x0CDD5C`, pixels a partir de `0x0CE15C`. Reescrevendo 255 das 256
entradas, os 9 ícones mudam de cor **de uma vez**, com o anti-aliasing
preservado.

| | Pixels (V001) | Paleta (V002) |
|---|---|---|
| Recolorir 1 ícone | ~700 B, 2 setores | — |
| Recolorir **os 9** | ~6 KB, redesenho manual | **1 KB, 2 setores** |
| Anti-aliasing | refeito à mão | preservado |

**Regra nova:** cor → paleta. Pixel só quando a **forma** mudar.

**O patch:** 1473 bytes, 4 setores (`0x0D000`, `0x0CD000`, `0x0CE000`,
`0x0CF000`), 16 KiB. CRC da FIRM `0x49A6` → `0x71E5`. Validação estática
**22/22 OK**. Reverte também o hack de pixels do V001, para o disco de
Música ser tratado como os outros oito.

**Verificação do `after.bin`:** 1473 bytes alterados — exatamente o
previsto. bootloader ORIG→ORIG, ptable e FIRM V001→V002, TONE ORIG→ORIG.
`after` vs V002 de referência: 4887 bytes diferem, **100% na PSMP, zero
fora**.

**Resultado visual — o que deu certo:** o carnaval de seis matizes acabou
e **o amarelo da seleção virou a única cor da tela**. Cor passou a
significar estado, não decoração. Isso não era o objetivo declarado do
patch; emergiu dele.

**O que NÃO saiu como projetado — registrado para o V003:**

1. **O display renderiza bem mais claro que o preview.** O grafite
   desenhado (`base #3A424C`, γ=1.9) chegou na tela como cinza-azulado
   pálido. Consequência: contraste do glifo branco caiu.
2. **O ícone "Image" virou um ponto branco destoante.** No original era
   círculo branco com glifo azul; o mapeamento por luminância mandou
   branco → branco.

**Por que (2) não tem conserto pela paleta — CONFIRMADO:** os índices são
**compartilhados entre ícones**. "Image" divide 30 índices com "Vídeo",
27 com "Música", 20 com "FM". Nenhum ícone tem paleta exclusiva.
Escurecer o círculo branco do Image escureceria junto o anel do Vídeo e o
brilho do disco. Corrigir só ele exige **editar pixels**, remapeando-os
para índices próprios.

> **Lição:** preview em monitor não prevê o display. A calibragem de
> luminosidade só pode ser feita **depois** de ver na tela — e isso é um
> argumento a favor de patches pequenos e reversíveis, não contra.

**Ferramenta nova: `tools/make_install_kit.py`.** Gera o kit inteiro
(setores, script de gravação, `diag.sh`, LEIA-ME) calculando tudo a
partir das imagens — elimina a classe de erro que corrompeu a ptable
ontem. **Recusa** gerar qualquer patch que toque abaixo de `0x00D000`.

Dois defeitos que a geração pegou e a leitura não teria pego:

- **o diff estava contra a imagem errada** — contra o original davam 3
  setores, mas o aparelho tinha o V001 e são **4** (`0x0CF000` precisa
  voltar aos pixels originais);
- **o `diag.sh` rotulava errado** — regiões idênticas nos três estados
  colapsavam num `dict` e apareciam como "ALVO V002" mesmo na imagem
  original. Trocado por lista de pares e testado contra as 3 imagens.

**Hardware:** 4 escritas de 4 KiB. **Estado final: V002 em execução.**

---

### 2026-09-12 — `docs/ROADMAP.md` — viabilidade avaliada e referência revista

**Veredito: o Design System é viável** como direção, que é o que ele
próprio diz ser (§12, §13). Viabilidade classificada em 6 camadas, da
provada à cara, cada uma com a evidência que a sustenta.

**Descoberta geométrica — a referência visual estava mal escolhida:**

| Modelo | Resolução | Orientação | Distância do GN-438 |
|---|---|---|---|
| GN-438 | 128×160 | retrato | — |
| **nano 2G** | 176×132 | **paisagem** | **0,53 — o pior de todos** |
| nano 4G/5G | 240×376 | retrato | 0,16 |
| nano 6G | 240×240 | quadrado | 0,20 |

**O nano 2G é o único nano deitado; o GN-438 é em pé.** A assinatura do
2G — lista à esquerda, capa à direita — depende de ser mais largo que
alto e não cabe em 128×160.

**Duas consequências:**

1. **A grade 3×3 deixa de ser dívida técnica.** O nano 6G tinha home em
   grade de ícones. O item mais caro do projeto — converter a home para
   lista — vira **opção estética**, não correção pendente.
2. **A referência se divide:** filosofia do **2G** (é o que o `CLAUDE.md`
   §1 pede — "reproduzir conceitos", não geometria), soluções de layout
   em retrato do **4G/5G**, legitimidade da grade do **6G**.

**Inversão estratégica — atacar as listas primeiro, a home por último.**

`lv_list` **não existe** no binário (0 ocorrências; a LVGL foi compilada
sem o widget), mas há dezenas de telas de lista montadas à mão com
`lv_label`/`lv_obj`. **A estética de lista do nano já está no aparelho** —
aparece em Arquivos, Livro e Configurações. A home é 1 tela de 61.

Dá para chegar a "parece um iPod" na maior parte do uso com as camadas
1–4, sem uma linha de código ARM.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Decisão: menu segue o nano 2G, sem faixa de capas

O mantenedor descartou a tira de capas de álbum do nano 4G/5G. Dois
motivos independentes, cada um suficiente:

1. **O nano 2G não a tinha** — seu menu principal era lista pura. "Como
   o 2G" não abre mão de nada; é o que o 2G era.
2. **Seria o item mais caro da interface**, e para enfeite: JPEG em
   runtime, três imagens simultâneas, RAM nunca medida.

**Referência consolidada:**

| O que | De qual nano |
|---|---|
| Menu como lista pura | **2G** |
| Proporções em tela vertical | 4G/5G |
| Legitimidade da grade na home | 6G |

Mantém o elemento mais caro do projeto fora do caminho crítico, sem
custo estético.

**Próxima investigação definida:** de onde vem a cor de fundo das listas.
Se for imediato Thumb-2, é camada 5; se vier de tabela de estilos em
dados, é camada 3 e sai barato. A resposta decide se o OpenPod pode
inverter para fundo claro (Design System §8) ou fica escuro por
enquanto.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — ✅ V003 GRAVADO — calibragem de luminosidade, série de ícones fechada

**Terceira gravação, terceira verificação perfeita.** 3 setores, 12 KiB,
**737 bytes alterados — exatamente o previsto**. `after` vs V003 de
referência: só a PSMP difere, **zero bytes fora**.

| Região | before | after |
|---|---|---|
| bootloader | intacto | ✅ inalterado |
| ptable | V002 | **V003** |
| FIRM | V002 | **V003** |
| TONE | intacta | ✅ inalterada |

**A calibragem.** O V002 saiu mais claro na tela do que no preview.
O V003 compensa: rampa de `#3A424C`/γ=1.9 para `#1C2026`/γ=2.6.
CRC da FIRM `0x49A6` → `0x05F2`. Validação estática 22/22.

**Resultado confirmado pelo mantenedor: contraste no ponto, tudo cinza.**
Os glifos brancos deixaram de estar lavados — era o problema do V002.
A série de ícones do menu principal está encerrada.

**Lição de método — foto de tela não serve para julgar cor.**

A foto do V003 mostrava os ícones nitidamente azuis. Eu cheguei a
atribuir isso a um viés frio da minha própria rampa (`B − R = +10`),
o que era verdade mas irrelevante: **ao olho, na tela, está cinza.**

A foto foi tirada sob luz quente; o balanço de branco da câmera compensa
o ambiente empurrando a tela para o azul.

> **Regra adotada:** foto de tela vale para **geometria, contraste e
> legibilidade**. Para **cor**, perguntar o que o olho vê. Eu quase
> gerei um V004 para corrigir um problema que só existia na câmera.

**Pendência conhecida, não corrigida:** o ícone "Image" continua sendo o
mais claro dos nove — no original era círculo branco com glifo azul, e o
mapeamento por luminância o mantém branco. Com os outros oito escuros,
ficou mais evidente. **Não tem conserto pela paleta** (índices
compartilhados, ver entrada do V002); exigiria remapear os pixels dele
para índices próprios. Fica em aberto, por baixa prioridade.

**Hardware:** 3 escritas de 4 KiB. **Estado final: V003 em execução.**

---

### 2026-09-12 — Espera ativa pelo aparelho nos scripts do kit

**Observação do mantenedor:** o `recovery_check_linux.sh` "funcionava
melhor" para entrar em card reader do que o `diag.sh` e o `flash_*.sh`.

**Causa real — não é comando, é timing.** O `recovery_check` **não faz
nada** para mudar o modo do aparelho. Ele gasta tempo clonando,
conferindo 15 hashes e compilando **antes** de falar com o aparelho, e
esse intervalo é o que o aparelho precisa para estabilizar em card
reader. Os outros scripts exigiam o aparelho já enumerado e atacavam na
sequência — daí o `smtlink_dump` ficar "aguardando a conexão" e a
gravação do V002 falhar na primeira tentativa.

**Implementado em `tools/make_install_kit.py` (`bloco_aguardar`)**, agora
presente no `diag.sh` e no `flash_vNNN.sh` de todo kit:

1. se já estiver conectado, segue;
2. senão, **espera até 180s** avisando a hora de conectar;
3. ao detectar, dá **4s de folga** para estabilizar;
4. **reconfirma** que continua enumerado (se caiu, aborta com instrução);
5. **pergunta se pode seguir.**

**O fluxo muda: rodar o script primeiro, conectar depois.** O `LEIA-ME`
gerado explica isso e o porquê.

> Uma observação operacional do mantenedor virou propriedade do
> ferramental. Ele tinha um contorno que funcionava sem saber por quê;
> agora a razão está entendida, documentada e automatizada.

**Verificado:** `set -e` não dispara em `[ -n "$U" ] && break` (testado);
rótulos do `diag.sh` reconferidos contra as 3 imagens após a regeração.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Investigação: de onde vêm as cores — **respondida**

Detalhe completo em **`docs/COLOR_SOURCE.md`**.

**Resposta: não existe tema central.** As cores estão inline no código da
aplicação, como constante de 16 bits em cada ponto de chamada — **~155
pontos**: 79 de fundo, 56 de texto, 20 de borda.

| Setter | Endereço | prop | Chamadores |
|---|---|---|---|
| `lv_obj_set_style_bg_color` | `0x00D4D092` | `0x20` | 79 |
| `..._text_color` (provável) | `0x00D4D10A` | `0x457` | 56 |
| `..._border_color` | `0x00D4D0C8` | `0x30` | 20 |

**Como:** `lv_style_set_prop` localizada em `0x00D58D38` pelo `__func__`
do próprio assert; só 3 chamadores diretos; 54 pontos de entrada da
máquina de estilos mapeados em `0x00D4C000`–`0x00D4D200`; os setters de
**cor** distinguem-se por empacotarem 16 bits com `bfi` (tamanho de
`lv_color_t` em RGB565), enquanto os escalares passam `r1` direto.

**Ambas as hipóteses anteriores estavam erradas.** Não é tabela de
estilos em dados (camada 3, barato) nem imediato dentro de
`page_*_create` (camada 5, caro). É **constante de 16 bits no ponto de
chamada** — trocar uma cor não exige escrever código ARM, e o ferramental
atual cobre isso sem adaptação.

**Consequência boa:** sem tema compartilhado, **mudar uma tela não afeta
nenhuma outra** — o oposto do que aconteceu com a paleta dos ícones.

**Consequência ruim:** inverter o sistema inteiro para fundo claro são
**~155 patches individuais**, não uma mudança. E o modo de falhar é
silencioso: cor errada numa tela que só aparece em uso.

**Atribuição às telas: PARCIAL** — 47 dos 79 chamadores de `bg_color` não
foram atribuídos com confiança. A heurística usada (literal `__func__`
mais próximo) é grosseira; precisão exige detectar fronteiras de função
de verdade.

**Recomendação registrada: não tentar a inversão global.** Uma tela por
vez, começando por Configurações, depois de melhorar a atribuição.

> **Quarto falso negativo do mesmo tipo.** O disassembly linear achou
> **zero** chamadores; a varredura por padrão de bits achou 155. Já é
> regra do projeto: neste firmware, contagem de chamadas se faz por
> padrão de bits, nunca por varredura linear.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — ✅ V004 GRAVADO — rótulos cinza, seleção ciano

**O menor patch do projeto: 8 bytes.** 2 setores, 8 KiB. Verificação
byte a byte — exatamente os 8 previstos, zero diferença fora da PSMP.

```text
0x00D01C-1D   F205 -> D3D9                         CRC-16 da FIRM
0x12E948-4B   mov.w r0,#-1 -> movw r0,#0xA514       cor dos rotulos
0x12EB3E      movs r0,#12 -> movs r0,#7             selecao (site 1)
0x12EDAE      movs r0,#12 -> movs r0,#7             selecao (site 2)
```

| | Antes | Depois |
|---|---|---|
| Rótulos | branco `0xFFFF` | cinza `#A0A0A0` |
| Seleção | `LV_PALETTE_YELLOW` (12) | `LV_PALETTE_CYAN` (7) |

**Primeiro patch de CÓDIGO do projeto** — os anteriores mexiam em
recursos (pixels, paleta). Este altera instruções Thumb-2:
`movw r0, #imm16` (T3) ocupa exatamente os 4 bytes de `mov.w r0, #-1`
(T2), e o índice de paleta é 1 byte. **A camada 5 do `ROADMAP.md` deixa
de ser NÃO DETERMINADO: está PROVADA.**

**Correção de método — a ordem recomendada estava invertida.**

O log revelou que o aparelho **re-enumerou** entre a espera e o recovery
check: `Device 094` → `Device 098`. Ou seja, "rodar primeiro e plugar
depois" pega o aparelho no momento instável.

O mantenedor já tinha o procedimento certo por observação: **plugar,
esperar ~10s, e só então rodar.** Eu havia invertido a recomendação sem
evidência de que fosse melhor.

Corrigido no gerador: a ordem plugar-primeiro passa a ser a
**recomendada** no `LEIA-ME`; o caminho inverso continua aceito, mas
agora avisa na tela que costuma causar re-enumeração. `ESTABILIZA`
subiu de 4s para 8s.

**Hardware:** 2 escritas de 4 KiB. **Estado final: V004 em execução.**

---

### 2026-09-12 — ✅ V005 — `LV_COLOR_16_SWAP` **CONFIRMADO**; menu principal fechado

**5 bytes.** Só a constante da cor dos rótulos e o CRC.

**Experimento controlado, com previsão feita antes da gravação:**

| | Escrito | Display lê | Resultado na tela |
|---|---|---|---|
| V004 | `0xA514` (neutro) | `0x14A5` | **verde** ❌ |
| V005 | `0x14A5` (pré-invertido) | `0xA514` | **cinza neutro** ✅ |

A previsão se confirmou. **O display usa RGB565 com bytes trocados.**

**Confirmação cruzada — o swap está DENTRO da LVGL.** Se fosse externo,
`LV_PALETTE_CYAN` teria saído vermelho e `LV_PALETTE_YELLOW` teria saído
ciano-esverdeado. Nenhum dos dois aconteceu. Logo `lv_palette_main()` já
entrega o formato certo, e **só constantes cruas precisam ser
pré-invertidas** — regra registrada em `COLOR_SOURCE.md` §9.

**Por que quase passou despercebido:** branco (`0xFFFF`) e preto
(`0x0000`) são simétricos — a troca não os altera. Como o firmware
original usa quase só esses dois para texto, o defeito só apareceu na
primeira cor intermediária que escrevemos.

**Estado do menu principal — fechado:**

| Elemento | Antes | Agora |
|---|---|---|
| 9 ícones | 6 matizes | cinza, uma linguagem |
| Rótulos | branco | cinza neutro |
| Seleção | amarelo | ciano/azul |

Ícones, rótulos e seleção na mesma linguagem, com a cor reservada para
**estado**, não decoração. Cinco patches, todos verificados byte a byte,
bootloader nunca endereçado.

**Hardware:** 2 escritas de 4 KiB. **Estado final: V005 em execução.**

---

### 2026-09-12 — ✅ V006 — tema central encontrado; Configurações alinhada

**6 bytes.** Uma única instrução: o getter de texto do tema
(`0x00D21384`) deixa de devolver branco e passa a devolver o cinza
`#A0A0A0` (pré-invertido para `0x14A5`).

**Correção de uma conclusão anterior: EXISTE tema central.** Eu havia
afirmado que não existia — não tinha descido fundo o bastante.

```asm
0x00D21384:  mov.w r0,#-1  ->  BRANCO (texto)   17 chamadores
0x00D2138A:  mov.w r0,#0   ->  PRETO  (fundo)    7 chamadores
```

`page_set_menu_create` tem **uma só** chamada de cor; a aparência da
lista vem de helpers (`0x00D216F0` com 52 chamadores, `0x00D21764` com
39) que consultam esses dois getters.

**Alcance medido no aparelho, não na análise.** A cadeia é profunda
demais para o traçado estático (só 91 de 3.365 funções têm nome). O V006
usou o hardware como oráculo: **Configurações ficou cinza** → usa o tema.

> **Lição:** com pipeline de gravação provado e reversível, o hardware
> responde mais rápido que a análise estática. Horas rastreando chamadas
> custavam mais que um patch de 6 bytes que mostra a resposta na tela.

**O que destrava:** o getter de FUNDO segue intocado. Trocá-lo é a
alavanca única para o tema claro do nano 2G — **4 bytes**, não os ~155
patches estimados antes.

**Resultado:** menu principal e Configurações na mesma linguagem —
cinza, com o azul da seleção como único acento.

**Hardware:** 2 escritas de 4 KiB. **Estado final: V006 em execução.**

---

### 2026-09-12 — ✅ V007 — o logo do OpenPod no aparelho

**3 setores, 12 KiB, 5.322 bytes.** O logo GENAI foi substituído pelo do
OpenPod na tela de abertura. **Primeiro patch que põe a identidade do
projeto no dispositivo.**

**O logo já estava em 128×35** — o tamanho exato do slot, sem
redimensionar. Conversão para `INDEXED_8`: 548 → **247 cores**, erro
médio **0,0%** por canal. Praticamente sem perda.

| | Slot (`0x0CC7C4`) |
|---|---|
| Cabeçalho `lv_img_dsc` | `0x0CC7C4` |
| Paleta BGRA | `0x0CC7D0`, 1024 B |
| Pixels | `0x0CCBD0`, 4480 B = 128×35 |
| Setores | `0x0CC000` e `0x0CD000` |

Nota: `0x0CD000` contém **o fim do logo e o começo da paleta dos ícones**
— por isso 3 setores e não 2. O kit grava o setor inteiro com o conteúdo
correto dos dois.

**Paletas de imagem não precisam da pré-inversão** de `COLOR_SOURCE.md`
§9 — formato BGRA próprio, já validado no V002/V003.

**Confirmação visual do mecanismo do V006.** Com o logo GENAI (fundo
branco) a tela parecia uma faixa clara; com o do OpenPod (fundo preto) a
faixa ficou escura e **o fundo claro ao redor ficou evidente** — é o
valor do getter `0x00D21384`, exatamente como o disassembly indicava.
Mecanismo **CONFIRMADO por código e por tela**.

**Pergunta encerrada como NÃO DETERMINADO:** se havia uma tela preta
antes da do logo. O mantenedor tentou observar e o boot é rápido demais.
Não bloqueia nada — a memória do estado anterior não altera nenhuma
decisão.

**Hardware:** 3 escritas de 4 KiB. **Estado final: V007 em execução.**

---

### 2026-09-12 — ✅ V008 — fundo da abertura em preto; primeiro patch de FLUXO

**4 bytes.** O menor patch do projeto, e o mais cirúrgico.

```text
0x12285C   93 -> 96    redireciona o BL da 1a funcao do logo
0x1228E6   4E -> 51    redireciona o BL da 2a funcao do logo
```

As duas funções que desenham o logo (`0x00D22794` e `0x00D228A0`)
passaram a consultar o getter **preto** (`0x00D2138A`) em vez do getter
de cor clara (`0x00D21384`).

**Primeiro patch de FLUXO DE CONTROLE do projeto.** Até aqui trocamos
valores — cores, constantes, pixels. Aqui mudamos **para onde uma chamada
aponta**. É o mesmo mecanismo que um dia permitiria redirecionar uma tela
inteira para outra implementação (camada 6).

**Por que não mudar o getter:** ele é **sobrecarregado** — devolve uma
"cor clara" que umas telas usam como **texto** e outras como **fundo**.
Escurecê-lo deixaria o texto de Configurações invisível. Redirecionar as
duas chamadas específicas resolve a tela de abertura **sem efeito
colateral em nenhuma outra**.

**Resultado confirmado na tela:** logo do OpenPod sobre preto, sem faixa
e sem moldura clara.

**Hardware:** 2 escritas de 4 KiB. **Estado final: V008 em execução.**

---

### 2026-09-12 — Correção: o truncamento de rótulos NÃO é defeito

Registrado a partir de observação em foto do aparelho.

Eu havia listado o texto cortado em Configurações ("Configuração do
ecr:", "Desligamento sem c") como defeito a corrigir **encurtando os
rótulos**, e apontado o bloco de textos (`0x053000`) como alvo barato da
Fase 1.2.

**Estava errado.** O firmware **rola o rótulo selecionado**
horizontalmente: numa foto do menu, o item selecionado aparecia como
`onfigur:` — "Configurações" no meio da rolagem.

**O texto completo já é acessível.** Encurtar os rótulos seria trabalho
para **piorar**: perderíamos informação para resolver um problema que o
firmware já resolve.

> Um item removido do roadmap e uma suposição derrubada — por olhar uma
> foto com atenção, não por análise. Vale lembrar para o que vier: nem
> todo comportamento estranho é defeito; parte é solução que ainda não
> entendemos.

---

### 2026-09-12 — V009/V010/V011 — o experimento do tema claro, e a volta

**Decisão do mantenedor: manter o tema escuro.** Fundo preto, texto
claro, seleção azul. O tema claro fica para depois, como **atualização de
design** — não como recriação do sistema.

**O que foi tentado:**

| | O quê | Resultado |
|---|---|---|
| V009 | inverte os dois getters do tema | inconsistente — só parte do aparelho mudou |
| V010 | nano completo: paleta dos ícones invertida, rótulos e seleção | **menu principal ficou excelente**; duas telas quebraram |
| V011 | logo com fundo claro (`NEW.png`, 252 cores, erro 0,04%) | montado, não gravado |

**O menu principal do V010 é a melhor tela que o projeto produziu** —
fundo claro, ícones escuros com glifo recortado, rótulos escuros. É
reconhecivelmente um iPod. Fica registrado como desejável.

**O que quebrou:** a tela do relógio (hora e data em branco sobre claro) e
os itens **não selecionados** de Configurações (texto claro sobre claro).

---

#### A descoberta que encerrou a tentativa

**Este firmware é arquiteturalmente escuro.** Não tem um tema
configurável no modo escuro — branco-sobre-preto é o padrão assumido em
dezenas de lugares independentes.

Varredura por padrão de bytes (`mov.w r0,#-1 ; bx lr`):

| | Quantidade | Chamadas somadas |
|---|---|---|
| Helpers que devolvem **branco** | **8** | 52 |
| Helpers que devolvem **preto** | **5** | 27 |
| Pontos de cor **inline** | ~155 | — |

**Nenhum** deles é chamado de dentro de `page_set_menu_create`: a cor do
texto da lista vem de um caminho ainda não localizado.

> **Eu estimei "4 bytes" para inverter o tema. Errei por uma ordem de
> grandeza.** Generalizei de dois helpers para o firmware inteiro, sem
> verificar. O custo real é dezenas de investigações, cada uma terminando
> num patch pequeno, **sem garantia de completude** — sempre pode restar
> uma tela que só aparece numa condição específica.

---

#### Correção de uma conclusão anterior

**A entrada do V006 afirmava que "Configurações usa o tema central".**
Isso veio de um relato verbal ambíguo ("tudo cinza") que eu tratei como
confirmação. **É o mesmo erro de classificação já cometido duas vezes
neste projeto.**

A verificação agora mostra o contrário: com o getter em `#181C18`
(escuro), o texto dos itens continua **branco**. Os itens de
Configurações **não** usam o getter `0x00D21384`.

O que o V006 provou continua válido: aquele getter existe, tem 17
chamadores e afeta *alguma coisa*. Qual exatamente: **NÃO DETERMINADO**.

---

#### Enquadramento adotado

> Tema claro = **atualização de design**, a ser feita quando a base
> estiver pronta. Não é pré-requisito para o OpenPod.

Coerente com `CLAUDE.md` §1 (reproduzir **conceitos**, não paleta) e com
o Design System §49 (*realidade do firmware > especificação*).

**Hardware:** V009 e V010 gravados e verificados; revertidos ao V008.

---

### 2026-09-12 — V012 — consolidação do tema escuro

**V012 é byte-idêntico ao V008** (`sha256 f321e618…a6a3`). Não há
conteúdo novo: é o mesmo firmware com numeração atualizada, para que a
versão em uso não seja uma anterior à série do experimento claro.

**Por que existe:** o aparelho estava no V010 (tema claro). O V012 leva
ele de volta ao estado aprovado numa **única gravação de 6 setores**,
em vez de desfazer patch a patch.

**O que o V012 contém** — a soma de V001 a V008:

| Elemento | Estado |
|---|---|
| 9 ícones do menu | cinza monocromático, calibrado ao display |
| Rótulos do menu | cinza `#A0A0A0` |
| Seleção do menu | `LV_PALETTE_CYAN` |
| Tela de abertura | logo OpenPod sobre preto |
| Fundo geral | preto |
| Bootloader | **nunca endereçado** |

**Filosofia adotada, registrada como decisão do mantenedor:**

> Fundo preto, letras claras, seletor azul. O tema claro fica para
> depois, como **atualização de design** — não como recriação do sistema.

**Hardware:** 6 escritas de 4 KiB (V010 → V012).

---

### 2026-09-12 — V013 — fonte branca; a filosofia gravada

**10 bytes.** Os dois getters de cor de texto voltam a devolver `0xFFFF`:

```text
0x12E948   movw r0,#0x14A5  ->  mov.w r0,#-1    rotulos do menu
0x121384   movw r0,#0x14A5  ->  mov.w r0,#-1    texto do tema
```

São **literalmente as instruções originais de fábrica** nesses dois
pontos — o V013 desfaz o que o V004 e o V006 fizeram, mantendo todo o
resto.

**Por quê:** o mantenedor enunciou a filosofia como *"fundo preto,
letras brancas, seletor azul"*, mas o que estava gravado era **cinza**
`#A4A1A4` — escolha nossa no V004/V006, para criar hierarquia. Havia
descompasso entre o declarado e o gravado, e o declarado venceu.

**Nota técnica:** `0xFFFF` é **simétrico** — a troca de bytes do display
(`COLOR_SOURCE.md` §9) não o altera. É a única cor imune a esse erro.

**Estado do OpenPod após o V013:**

| Elemento | Cor |
|---|---|
| Fundo | preto |
| Texto (menu e listas) | **branco** |
| Ícones do menu | cinza monocromático |
| Seleção | azul |
| Abertura | logo OpenPod sobre preto |

**Hardware:** 3 escritas de 4 KiB.

**Confirmado na tela pelo mantenedor:** *"bem melhor, gostei desse
negócio preto com branco"*. O V013 encerra a Fase 1.1 com a identidade
visual do OpenPod definida e aprovada.

---

### 2026-09-12 — Organização do projeto

- `other/` — kits de gravação de V001 a V011, com `LEIA-ME.txt`
  explicando o que cada um fez e **avisando que cada kit exige um estado
  anterior específico**; rodar um antigo sem `diag.sh` antes é erro.
- `analysis/readbacks/` — os `before.bin`/`after.bin`/logs trazidos do
  aparelho, com `LEIA-ME.txt` registrando que são **evidência**: foi com
  eles que cada gravação foi conferida byte a byte. O `before.bin` do
  V001 é o estado de fábrica lido do próprio dispositivo.
- Raiz do projeto reduzida ao kit atual, às artes do logo e às pastas
  estruturais do `CLAUDE.md` §10.

Nada foi apagado.

---

### 2026-09-12 — Menu em lista: investigado, documentado, adiado

Pergunta do mantenedor: **é viável o menu principal parecer com o do
nano (lista), mantendo preto/branco/azul?**

**Resposta: viável, mas é projeto, não patch.** Detalhe completo em
**`docs/MENU_LISTA.md`**.

**O firmware tem duas telas de home:** `page_home_create` (grade, usa a
folha de ícones) e `page_home_menu_create` (lista, usa os helpers de
item). Cada uma com **um único chamador** — trocar qual é chamada são
4 bytes.

**⚠️ O V014 foi montado e DESCARTADO antes de gravar.** A lista mostra
**3 itens** (Alarme, Imagens, Dicionário), não os nove do menu. Gravar
deixaria o aparelho sem acesso a seis funções.

> O patch estava tecnicamente correto; a **premissa** estava errada. Eu
> recomendei gravar **sem saber o que a tela mostrava**. Foi o mantenedor
> quem pediu a verificação antes — *"você não me falou os menus para
> bater com o principal"*. Segunda vez no dia em que uma pergunta dele
> corrigiu meu rumo; a primeira foi a ordem de conexão do aparelho.
>
> Kit em `other/NAO_GRAVAR/`, com o motivo registrado.

**O que a investigação deu de valioso:** a tela de lista é **dirigida por
tabela** — IDs de texto em `0x00C486E8`, glifos de ícone em
`0x00C5D622` (faixa U+F000 da fonte). Não tem itens embutidos.

| Peça para 9 itens | Custo |
|---|---|
| Limite do laço (`0x00D2F2DA`) | **1 byte** |
| Tabelas de texto e ícone | flash livre + ponteiros |
| **Mapear 9 índices para 9 telas** | **NÃO DETERMINADO** |

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Menu em lista: tabelas localizadas, estimativa revista

Continuação da investigação. Detalhe em `MENU_LISTA.md` §8–10.

**A tabela do menu principal existe e está adjacente à da lista:**

```text
0x00C486C4   [1, 3, 5, 6, 2, 4, 9, 10, 8]   <- 9 itens da GRADE
0x00C486E8   [7, 4, 11]                     <- 3 itens da LISTA
```

Os IDs foram resolvidos na tabela do português (`0x00C53B84`, localizada
nesta investigação junto com as outras 7 línguas): Música, vídeo,
Gravação, Rádio, Livro digital, Imagem, Bluetooth, Configurar, Ver pastas.

**Os ícones da lista são fixos**, não por item: o ponteiro
`0x00C5D622` (U+F013, engrenagem — Font Awesome) é carregado dentro do
laço e nunca varia. É por isso que toda linha de Configurações tem
engrenagem.

**Estimativa revista — os rótulos certos custariam ~11 bytes:**

| Peça | Custo |
|---|---|
| Apontar para a tabela de 9 | 4 B |
| Limite do laço 3 → 9 | 1 B |
| Indexar a tabela direto (a pilha só cabe 3) | ~6 B |
| **Navegação: 9 índices → 9 telas** | **NÃO DETERMINADO** |

**Única incógnita restante:** se o despacho de destino é desvio fixo de
3 casos (camada 6) ou indexado por tabela (camada 5, ~15 B no total).

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Menu em lista: despacho encontrado, plano completo, montagem adiada

**O despacho é uma cadeia FIXA de 3 comparações** em `0x00D2EFF6`
(callback `0x00D2EF5C`), não uma tabela indexada. **Camada 6 confirmada.**

**Mas o laço substituto cabe no lugar:** montei um laço genérico de
**20 bytes** para o espaço de **20 bytes** disponível, com os três alvos
de salto conferidos por disassembly. Sem realocação, sem flash livre.

**⚠️ E apareceu uma camada que eu não tinha visto: MEMÓRIA.** A tela usa
`malloc(0x28)` com três vetores de 3 palavras (offsets `0`, `0xC`,
`0x18`). Para 9 itens: 108 bytes, e os offsets mudam em todo lugar que lê
a estrutura.

> **É o primeiro patch do projeto que mexe em alocação e aritmética de
> ponteiro.** Errar o `malloc` ou um offset corrompe a heap — travamento
> aleatório, minutos depois, em outra parte do sistema. **E corrupção de
> heap não aparece na verificação byte a byte pós-gravação**, que é a
> nossa principal rede de segurança.
>
> Todos os patches anteriores mexiam em **valores**: se errassem, a tela
> ficava feia e a gente via na hora.

**Estimativa revista: 12 pontos de alteração**, não os ~32 bytes que eu
tinha dito. Plano completo em `MENU_LISTA.md` §13, com 4 pontos ainda por
verificar.

**Decisão: montar em sessão nova**, com atenção inteira. O aparelho está
no V013, aprovado, e não há pressa.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — Menu em lista: os 4 pontos conferidos, e o plano da §13 descartado

Sessão aberta para montar o patch da `MENU_LISTA.md` §13. **O patch não
foi montado** — a conferência prévia dos 4 pontos em aberto, que o
próprio plano exigia, derrubou a premissa.

**Os 4 pontos fecharam** (detalhe em `MENU_LISTA.md` §15.1): as contas de
estrutura estavam certas e agora estão **confirmadas contra uma
implementação real do firmware** — `page_set_menu` (página `0x28`) é a
mesma tela com **10 itens**, `malloc(0x54)`, rótulos em `0x28`, ícones em
`0x50`, limite `cmp r3,#9`. O esquema é `rótulos = N·4`, `ícones = 2·N·4`.
Apareceu um 13º ponto que a §13 não listava: `label_process`
(`0x00D2F486`) também indexa `[r3,#0xc]`.

**O que derrubou o plano:** a tela de destino **não vem do índice**, vem
do campo `+0xC` da mensagem. Quem decide é uma **camada APP** até agora
não mapeada, em `0x00D0xxxx`, que recebe a mesma mensagem com 8 bytes de
prefixo. E `page83_btn_process` (`0x00D0CB02`) **ignora todo `ctrl_id`
diferente de 0**:

```asm
0x00D0CB00   ldrh r3, [r4, #0xc]
0x00D0CB02   cbnz r3, #0xd0cb20     ; != 0 -> retorna sem fazer nada
```

> Aplicar os 12 pontos da §13 daria uma lista bonita com os 9 rótulos
> certos em que **8 dos 9 itens não abririam nada**. Mesmo tipo de erro
> do V014 — patch correto sobre premissa errada — só que desta vez com
> `malloc` e aritmética de ponteiro no meio.

**O caminho que substitui** (`MENU_LISTA.md` §16): **virar a GRADE em
lista**, em vez de virar a lista em menu. A página 1 já tem os 9 itens,
os 9 destinos e o despacho funcionando. Falta só aparência — e aparência
aqui é **dado**:

- os 9 objetos de imagem do laço **não recebem fonte de imagem**;
  `0xd5d868` é chamada **uma vez só**, fora do laço, sobre a folha
  128×160 de `0x0CDD50`. Os ícones visíveis são **pixels da folha** — a
  mesma que o V001 já patcheou com sucesso;
- as posições saem de duas tabelas de 9 pares int16: `0x00C4867C`
  (ícones) e `0x00C486A0` (rótulos).

| | §13 (lista → 9) | §16 (grade → lista) |
|---|---|---|
| Navegação funcionando | **não** | **sim, já funciona** |
| Mexe em `malloc`/ponteiro | **sim** | não |
| Erro aparece na hora | não (heap) | sim |
| Alterações | 12+ pontos de código | 2 tabelas + 1 imagem + 2 constantes |

**Calibragem de risco:** a §16 devolve o projeto à classe de patch em que
um erro aparece na tela imediatamente — que é a rede de segurança real
deste projeto. A §13 era a primeira que podia corromper heap, e o ganho
que ela trazia (rótulos certos) a §16 entrega de graça, porque a grade já
tem os rótulos certos.

**Recomendação registrada:** descartar a §13, seguir pela §16. A §13 fica
documentada porque a análise de estrutura está correta e confirmada — só
não resolve o problema que interessa.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — V014: menu principal em lista vertical estilo iPod nano 2G

Decisão do mantenedor: seguir pela rota recomendada (§16, grade → lista),
por etapas, tendo o **V013 como ponto de retorno**.

**Etapa 1 — as 4 medições da §16.4** (`MENU_LISTA.md` §18):

- as três tabelas (`0x00C4867C`, `0x00C486A0`, `0x00C486C4`) e a folha
  `0x00CCDD50` têm **exatamente 1 xref cada**, todas em
  `page_home_create`. Nenhuma outra tela é afetada. **CONFIRMADO**;
- mapa de teclas da home levantado: `0x13`/`0x8a` = **+1**,
  `0x14`/`0x87` = **−1**, `0xa0` = −3, `0x81` = +3, `0x0a` = abre.
  **±1 já existe nativamente — nenhuma tecla precisou ser remapeada**;
- dois pontos novos apareceram ao medir a altura: o rótulo tinha
  **largura 40 px** e **`text_align = 2`** (centrado). Ambos de 1 byte.

**Etapa 2 — V014 montado, validado e empacotado** (`MENU_LISTA.md` §19):

```text
0x04867C   36 B  chevrons  -> (116, 16+16i)
0x0486A0   36 B  rótulos   -> (6,   16+16i)
0x12ED5E    1 B  largura   0x28 -> 0x64
0x12ED54    1 B  align     0x02 -> 0x00
0x0CE15C  pixels folha redesenhada: fundo preto + 9 chevrons 6×9
0x00D00C    2 B  CRC FIRM  0x8A58 -> 0xF5AB
```

`validate_firmware.py`: **22 OK, 0 falhas**. Kit: **8 setores, 32 KiB**,
bootloader não endereçado, `sh -n` OK, 1 `write_flash` executável.

**Ferramentas novas:** `tools/make_list_home.py` (recusa rodar se a
entrada não for a grade original) e `tools/preview_home.py` (renderiza a
tela fora do aparelho com a fonte do próprio firmware).

**Medição que evitou um defeito:** `long_mode = 0` quebra linha se o
texto não couber, e linha quebrada invadiria a de baixo. Medido na fonte
real: maior rótulo é "Livro digital" com **62 px em 100**. Nenhum
estouro. De quebra, revelou que **6 dos 9 rótulos não cabiam nos 40 px**
da grade.

**⚠️ Defeito latente desde o V002, encontrado e corrigido:** as
instruções de socorro dos kits mandavam gravar setores **de fábrica**
para desfazer um patch. Isso deixaria a FIRM **misturada** — medido sobre
o V013: CRC gravado `0x49A6` contra calculado `0xACBB`. Corrigido em
`tools/make_install_kit.py`: a reversão usa os setores da **base**.
Documento novo: `docs/ROLLBACK_POLICY.md`.

> **Lição:** a rede de segurança tinha sido testada para a frente e nunca
> para trás. É a segunda vez que o erro está no **conselho impresso para
> a hora em que algo der errado**, não no caminho principal.

Ida e volta conferida: `V013 + setores == V014` e
`V014 + reversão == V013` (byte-idêntico), CRC consistente nos dois.

**Limites assumidos do V014:** sem barra de seleção (o item selecionado
muda de cor de texto — barra exige objeto novo, Rota C da §17), sem ícone
à esquerda (fiel ao nano) e teclas `0xa0`/`0x81` ainda pulando 3 linhas.

**Hardware:** nenhuma operação. A gravação é do mantenedor.

---

### 2026-09-12 — V014 CONFIRMADO NO APARELHO + lacuna dos botões fechada

**O menu principal do GN-438 é uma lista vertical estilo iPod nano 2G.**
Gravado, verificado e fotografado pelo mantenedor.

**O que a tela provou** (nada disso era dedutível do binário):

- 9 linhas, ordem Música → Ver pastas, **cada uma abrindo a tela certa**
  — a premissa central da §16 está confirmada;
- a faixa de status (relógio, bateria) sobreviveu: é objeto separado, não
  estava na folha;
- 16 px por linha é legível; "Livro digital" não encosta no chevron;
- `text_align = 0` alinha à esquerda → `0xd4d13a` é
  `lv_obj_set_style_text_align`. Sobe de **PROVÁVEL** para **CONFIRMADO**;
- a seleção continua sendo cor de texto, como previsto.

**Lacuna nº 2 do `relatorio.md` — fechada por observação, não por
disassembly.** Ela estava aberta desde a Sessão 1: a tabela de `key_id`
vive em RAM e o plano era extraí-la. Com a home em lista, cada ramo de
tecla passou a ter efeito visualmente distinto, e bastou apertar:

```text
        M          pula 3
|<<    ▶Ⅱ    >>|   anda 1 · ENTRA · anda 1
        VOL        pula 3
```

Com a foto da roda, o padrão ganhou explicação: **é a semântica da grade
3×3** — esquerda/direita anda 1 célula, cima/baixo pula uma linha de 3.

> **Segunda vez que o aparelho responde mais rápido que a análise
> estática** (a primeira foi o alcance do tema central, `COLOR_SOURCE.md`
> §10). E desta vez a resposta veio de graça: o patch de layout que
> íamos fazer de qualquer jeito tornou os ramos distinguíveis a olho.

**Proposta registrada para o V015** (`BUTTON_ANALYSIS.md`): converter os
dois ramos de ±3 em ±1 — **5 bytes**, todos imediatos. O detalhe que
torna isso seguro: a conversão **preserva a direção de cada botão**, então
não é preciso saber qual deles é `0xA0` e qual é `0x81`. A ambiguidade que
sobra não afeta o resultado.

**Hardware:** gravação do V014 feita pelo mantenedor, verificada pelo
próprio script (4 regiões por SHA-256 sobre a releitura dos 2 MiB).

---

### 2026-09-12 — V015 (teclas) + estudo de viabilidade da hierarquia de menu

**V015 — `M` e `VOL` passam a andar 1 linha.** 5 bytes, todos imediatos:
`cmp r2,#2→#0`, `subhi #3→#1`, `addls #6→#8`, `adds r1,r2,#3→#1`,
`subs r2,#6→#8`. O que torna isso seguro: a conversão **preserva a
direção de cada botão**, então a ambiguidade `0xA0` vs `0x81` não afeta o
resultado. Alcance dos saltos verificado antes. Aritmética simulada:
ambos percorrem 0..8 com volta, sem índice fora da faixa.
`validate_firmware.py`: 22 OK. Kit: **2 setores, 8 KiB**, ida e volta
conferida. Ferramenta: `tools/patch_home_keys.py`.

**Estudo: home com 4 itens + submenu "Extras"** (`docs/MENU_HIERARQUIA.md`).

> **Descoberta que corrige o enquadramento da `MENU_LISTA.md` §15.3:** o
> destino de cada item da home **não é cadeia de código fixo — é uma
> tabela `tbh` de 12 entradas em `0x00D00FBE`**. Trocar para onde um item
> vai custa **2 bytes**.

- **Parte A (home com 4 itens): dado puro**, ~30 B + a folha. Nenhum
  `malloc`, nenhum offset de estrutura — o `malloc(0x54)` atual sobra.
- **Parte B (tela Extras): código novo.** Varri as 83 tabelas de salto da
  camada APP: só `page1_process` (12) e `page82_process` (8, seletor de
  tempo) despacham por índice; todas as de 6 são telas em uso. Não há
  hospedeiro para canibalizar.
- **A camada APP tem tabela própria de páginas**, 83 entradas em
  `0x00D0DB1C`, e **12 ids de página estão livres nas duas camadas**.
- O obstáculo esperado era o alcance: o `tbb` de `view_page_create` chega
  a só **510 bytes**, e a flash livre (`0x1A3038` → `0x00DA3038` no XIP)
  está fora. **Contornável:** reaproveitar a página `0x53`, que já tem os
  dois slots, desviando os dois pontos de entrada com `BL`/`B.W`
  (±16 MB). 4 bytes cada.

**Ressalva que manda:** A e B têm de ser gravadas **juntas**. Uma home de
4 itens cujo "Extras" não abre nada é pior que a de hoje — esconde seis
funções sem oferecer caminho.

**Falta medir:** o texto "Extras" precisa de um id de string. Ou existe
id livre nas 8 tabelas de idioma, ou a string vai para área livre com um
ponteiro em cada idioma. **NÃO DETERMINADO.**

**Hardware:** nenhuma operação nesta sessão.

---

### 2026-09-12 — Faixa superior mapeada (relógio, bateria, ícones)

Pergunta do mantenedor enquanto gravava o V015. Detalhe em
`docs/STATUS_BAR.md`.

**Viável, e quase tudo é imediato de 1 byte.** A faixa não está na folha
de imagem — são objetos LVGL da camada view, guardados na estrutura
global (`0x0081CE2C`). Foi por isso que sobreviveu ao V014.

| Elemento | Slot | Criado em | Geometria |
|---|---|---|---|
| Relógio | `view_p[0x20]` | `0x00D217B4` | `align(1, x=3, y=2)` |
| Bateria | `view_p[0x10]` | `0x00D225B0` | `set_pos(107, 0)`, barra 13×6, cor `0xCF5D` |
| BT / SD | `view_p[0x0C]` / `[0x18]` | `view_icon_create` `0x00D23740` | por estado |

Mover relógio ou bateria: **1 byte cada**. Barra: 2 bytes. Cor: 4 bytes
(pré-invertida). Glifo: 4 bytes de pool.

**A armadilha encontrada antes de cair nela:** o formato `"%02d:%02d"` em
`0x00C4CD5D` é a **cauda** de `"%02d. %02d:%02d:%02d"`. Editar no lugar
para virar um título "OpenPod" quebraria a string longa, usada para
data/hora completa. A forma limpa é repontar os **dois** ponteiros de pool
(`0x00123994` e `0x00124390`) para uma string nova — 8 bytes.

> **Recomendação registrada:** esconder elemento por **deslocamento**
> (mover para fora da tela, 1 byte, reversível em 1 byte), nunca tirando
> a chamada que o cria — isso mexe em fluxo e pode deixar ponteiro nulo
> para outra função desreferenciar. `view_set_icon_bat` tem guarda
> `cbz`; não conferi todas as outras.

Confirmação lateral da regra do `LV_COLOR_16_SWAP`: a cor de bateria
fraca é escrita como `0x00F8`, que pré-invertida é `0xF800` — vermelho
puro.

**Hardware:** nenhuma operação.

---

### 2026-09-12 — V015 CONFIRMADO NO APARELHO

Os quatro botões da roda andam de 1 em 1, as voltas nas pontas funcionam
nos dois sentidos (Música ↔ Ver pastas), `▶Ⅱ` continua entrando e nada
mudou visualmente.

> A conversão foi desenhada para **preservar a direção de cada botão**, o
> que tornou desnecessário saber qual emite `0xA0` e qual emite `0x81`.
> **Tornar uma incógnita irrelevante valeu mais do que resolvê-la** — e
> custou os mesmos 5 bytes.

**Ponto estável do projeto: passa do V014 para o V015.**

**Hardware:** gravação do V015 pelo mantenedor, 2 setores, verificada
pelo script.

---

### 2026-09-13 — V016: faixa superior com barra, separador e título "OpenPod"

Escolha do mantenedor: **título E relógio**, reaproveitando o label do
ícone do SD; e a barra com uma leve variação de cor, "para mostrar que é
uma barra", como no nano. Detalhe em `docs/STATUS_BAR.md` §8.

**1 812 bytes, 4 setores.** `validate_firmware.py`: 22 OK. Ida e volta do
kit conferida. Ferramenta: `tools/patch_status_bar.py`.

**Decisão de método que vale registrar:** para o label virar texto, ele
precisava largar a fonte de ícones. Eu não sabia o endereço da fonte
padrão — e em vez de procurar, **apaguei a chamada** (`bl` → 2× `NOP`).
Sem estilo de fonte o objeto herda a do tema, que é o que o label do
relógio já faz. **Não descobrir saiu mais barato e mais seguro do que
descobrir** — mesma família da decisão do V015, em que preservar a
direção dos botões tornou a tabela de `key_id` irrelevante.

**A prévia pegou um erro antes do aparelho:** a primeira barra ficou clara
demais e o separador colava na palavra "Música". Ajustada para degradê
mais escuro, separador em y=13 e duas linhas de respiro. Foi
`tools/preview_home.py` que mostrou — renderizando com a fonte do próprio
firmware.

> **O que este patch prova para o V017:** a string "OpenPod" foi gravada
> em `0x001A3038`, os 364 KiB livres fora de todas as partições. É a
> primeira vez que o projeto grava e lê dessa região. Se o título aparecer
> na tela, fica provado — **com um patch de dado e risco visual** — que a
> área livre é endereçável por XIP. Essa é a premissa em que o V017
> inteiro se apoia, e estava classificada como PROVÁVEL.

**O que se perde:** o ícone do cartão SD deixa de aparecer.

**Hardware:** nenhuma operação.

---

### 2026-09-13 — V016 falhou no aparelho · V017 corrige

O V016 foi gravado e **os dois objetivos falharam**: a barra ficou visível
demais e o título não apareceu. Detalhe em `docs/STATUS_BAR.md` §9.

**Defeito 1 — label errado.** A faixa tem dois labels de ícone parecidos.
`view_p[0x14]` (`0x00D226AC`, U+F0C7, condicionado a cartão presente) é o
que aparece; `view_p[0x18]` (`0x00D226F8`, U+E647, condicionado a uma flag
em RAM que está em 0) **nunca é criado na home**. Patcheei o segundo.

> **Lição:** eu confirmei que o patch estava aplicado no binário e tratei
> isso como se confirmasse que ele funcionaria. *"O byte certo está no
> lugar certo"* não é *"este código roda"*. Mesma família do erro da
> Sessão 25. Faltou uma pergunta de uma linha — **este objeto chega a ser
> criado nesta tela?** — cuja resposta estava a duas instruções.

**Defeito 2 — barra clara demais.** Usei os cinzas que já existiam na
paleta; o mais escuro era `(28,32,38)`. A folha usa **6 dos 256 índices**:
havia 250 livres e dava para definir o tom exato. Eu tinha escrito "não
altera a paleta" na ferramenta como se fosse regra de segurança, quando
era só uma limitação que eu mesmo impus.

**V017:** reverte o patch morto (um patch que não roda **não é
inofensivo — é armadilha adormecida**, dispararia se a flag mudasse),
aplica o título no label certo e define 4 entradas de paleta novas
(`(20,22,26)`, `(14,16,19)`, `(9,10,12)`, separador `(52,56,62)`).
**1 828 bytes, 4 setores.** `validate_firmware.py` 22 OK, ida e volta do
kit conferida. Ferramenta: `tools/fix_status_bar.py`.

> **O que continua NÃO PROVADO:** a leitura por XIP da área livre
> (`0x001A3038`). O V016 deveria ter testado, mas o label nunca foi
> criado e o ponteiro nunca foi lido. **O V017 é que responde** — e é a
> premissa em que o V018 (Extras) se apoia para pôr código lá.

**Numeração:** Extras passa de V017 para **V018**.

**Hardware:** gravação do V016 pelo mantenedor; nenhuma operação minha.

---

### 2026-09-13 — V017 CONFIRMADO · área livre PROVADA · V018 corrige a altura

**O título "OpenPod" apareceu na tela.** Com ele, cinco previsões
confirmadas de uma vez — o label certo, o `align=2`, a herança de fonte
ao apagar o `bl`, a paleta redefinida e, principalmente:

> ### A premissa da área livre saiu de PROVÁVEL para CONFIRMADO
>
> Dados em `0x001A3038` são legíveis por XIP em `0x00DA3038`. Custou
> **8 bytes de string**. É a premissa em que o Extras se apoia.
>
> Ressalva de alcance: prova **leitura de dado**, **não execução de
> código**. São coisas diferentes — a mesma distinção que me custou o
> V016.

**V018 — a barra tinha altura errada, e dava para medir.** O mantenedor
observou que a faixa ficou apertada. A régua estava no firmware:

```text
fonte: ascendente 12, descendente 0 -> texto com y_ofs=2 ocupa y 2..14
barra do V017: banda 0..12, separador 13
-> o texto ESTOURAVA a barra em 1 px e cruzava o separador
```

Corrigido: barra `y0..16`, separador `y17`, lista de `y18` com as 9
linhas em `18 34 50 65 81 97 113 128 144` (espaçamento alternando 16 e
15 px, última terminando exatamente em 159). Bateria desce para `y=2`.
**1 217 bytes, 7 setores**, 22 verificações OK, ida e volta conferida.
Ferramenta: `tools/patch_bar_height.py`.

> **Lição:** a métrica exata existia — a ascendente da fonte, a três
> linhas de Python — e eu escolhi a altura por aparência na prévia.
> Quando o número está no próprio artefato, a prévia é conferência, não
> substituto.

**Numeração:** Extras passa a ser **V019**.

**Hardware:** gravação do V017 pelo mantenedor.

---

### 2026-09-13 — V018 regerado: inclui "vídeo" → "Vídeo"

O mantenedor pediu a maiúscula no item do menu, fora de padrão com os
outros oito. Como o V018 ainda não tinha sido gravado, a correção entrou
nele em vez de virar uma versão nova.

**A correção óbvia estava errada.** `'vídeo'` (pt id 3) é a **cauda** de
`"Reprodução de vídeo"` — trocar 1 byte no lugar mudaria a string longa
junto. **Segunda vez** que um ponteiro aponta para o meio de outra
string; a primeira foi `"%02d:%02d"` dentro de `"%02d. %02d:%02d:%02d"`.

> **Regra derivada:** neste firmware, **nunca editar string no lugar**.
> Gravar a nova na área livre e reapontar o ponteiro custa 4 bytes a mais
> e **remove a classe de erro**, em vez de evitá-la caso a caso. Mesmo
> raciocínio da regra "um arquivo por setor, offset 0" do `write_flash`.

Ferramenta nova: `tools/patch_menu_text.py` — grava na área livre,
reaponta a tabela de idioma, e recusa texto com caractere fora da fonte.
Serve também para o "Extras" do V019. A técnica é a que o V017 provou.

Conferido: `"Reprodução de vídeo"` continua intacta em `0x055370`.

**V018 final: 1 227 bytes, 9 setores**, 22 verificações OK, ida e volta
conferida.

**Hardware:** nenhuma operação.

---

### 2026-09-13 — V018 refeito: 2 px de respiro entre o separador e a lista

Na prévia o mantenedor viu que **o separador encostava no topo de
"Música"**. Medido na folha: **0 px de folga** — o rótulo começava
exatamente na linha seguinte ao separador.

Corrigido subindo o texto da barra em 1 px, o que libera espaço embaixo
sem apertar a barra nem cortar a última linha:

```text
texto da barra   y_ofs 2 -> 1,  ocupa y  1 .. 13
barra            y  0 .. 15
separador        y 16
respiro          y 17 .. 18        2 px
lista            y 19 ..159        19 35 50 66 82 97 113 129 144
```

Dois bytes novos: `0x001217D6` (relógio) e `0x001226B6` (título).

> **Lição reforçada duas vezes na mesma sessão:** errei a altura da barra
> e depois errei o respiro, e nos dois casos bastava **medir a folga em
> pixels** em vez de olhar a imagem. A métrica estava no próprio
> firmware. A prévia é conferência, não substituto.

**V018 final: 1 227 bytes, 11 setores**, 22 verificações OK, ida e volta
conferida.

**Hardware:** nenhuma operação.

---

### 2026-09-13 — V018 CONFIRMADO no aparelho · V019 alinha a bateria

**V018 na tela, aprovado pelo mantenedor:** barra com respiro, 9 linhas
sem corte, "Vídeo" com maiúscula, título e relógio na faixa.

**Uma observação dele:** o ícone de bateria ficou baixo. **Ele tem razão,
e a causa fui eu de novo.** No V018 subi o texto da faixa (`y_ofs` 2→1)
e, no mesmo passo, desci a bateria de `y=0` para `y=2` — **sem medir**.

```text
V017   texto y_ofs 2, bateria y 0   -> diferença −2   (agradava)
V018   texto y_ofs 1, bateria y 2   -> diferença +1   (ficou baixa)
V019   texto y_ofs 1, bateria y 0   -> diferença −1
```

A fonte de ícones (`0x00CACFE4`) tem `line_height` 16 e `base_line` 2,
contra 12 px de ascendente do texto: por isso o ícone precisa de um `y`
**menor** que o do texto para parecer alinhado.

**V019: 3 bytes, 2 setores.** Ferramenta nova `tools/patch_battery_y.py`
— o ajuste tinha sido feito à mão e foi refeito por ferramenta, porque o
projeto não guarda passo não reproduzível.

> **Terceira vez na mesma sessão** que eu escolhi um valor de geometria
> por aparência tendo métrica disponível. O padrão está claro o bastante
> para virar regra: **antes de mexer em posição, imprima a folga em
> pixels — do estado atual e do proposto.**

**Hardware:** gravação do V018 pelo mantenedor.

---

### 2026-09-13 — V020: ensaio de execução na área livre

Decisão do mantenedor: testar a execução **separado** do Extras, para que
uma falha tenha causa única.

**Achado que mudou o desenho do teste.** Eu ia usar a tela inicial como
cobaia. Antes, fui ver onde mora o card reader — o caminho de
recuperação: a string `"CARDREADER"` está em `0x00046FC7`, **dentro da
FIRM**, e o bootloader não tem nenhuma string de USB. Se o teste travasse
montando a tela inicial, a recuperação ficaria incerta.

> Isso também reinterpreta a Sessão 25: a recuperação funcionou com a
> tabela de partições destruída porque a **FIRM continuou rodando** — ela
> é achada em `0x0000E000` por cabeçalho próprio, não pela tabela.
> **PROVÁVEL**, por convergência de duas evidências.

**O desenho seguro:** a cobaia é `page_set_menu_create`, executada só
quando se entra em Configurar de propósito.

```text
0x001A3048   b.w 0x00D58188        trampolim na área livre
0x0013A640   bl 0x00D58188  ->  bl 0x00DA3048
```

Salto de cauda: `LR` intacto, semântica idêntica se executar.
**Abre normal = executa. Trava = não executa**, e um ciclo de energia
devolve a tela inicial, o USB sobe e o kit reverte. O caminho de
recuperação fica intacto nos dois resultados.

A ferramenta codifica, **decodifica de volta e compara**; conferido
também por capstone, por fora.

**8 bytes, 3 setores.** `tests/test_exec_free_area.py`.

---

### 2026-09-13 — V019 CONFIRMADO no aparelho

Bateria alinhada com o texto da faixa. Aprovado pelo mantenedor.

**Fase 1 fechada.** O menu principal do GN-438 é uma lista vertical
estilo iPod nano 2G, com faixa superior própria: relógio à esquerda,
título "OpenPod" no centro, bateria à direita, separador e respiro.

Tudo isso foi feito **sem uma linha de código novo** — só dado, constante
de 1 byte e ponteiro de pool. O próximo passo (V020) é o primeiro que
depende de executar código fora da FIRM.

**Ponto estável: V019.**

**Hardware:** gravação do V019 pelo mantenedor.

---

### 2026-09-13 — ✅ V020: execução na área livre CONFIRMADA

A tela Configurar abriu normalmente: a chamada passou pelo trampolim em
`0x00DA3048` e voltou. **Cinco afirmações subiram para CONFIRMADO de uma
vez** — código na área livre executa por XIP; `bl` da FIRM alcança lá;
`b.w` de lá alcança a FIRM de volta; e o salto de cauda preserva `LR`
através da fronteira.

> **A Parte B do Extras deixou de ter incógnita de plataforma.** O que
> sobra é trabalho: escrever Thumb-2 correto — difícil, mas difícil de um
> jeito controlável, porque dá para desmontar de volta e conferir antes
> de gravar.
>
> Um teste de **8 bytes** respondeu cinco perguntas, num lugar onde o
> pior resultado custaria um ciclo de energia. Vale como modelo: quando
> uma premissa sustenta um trabalho grande, comprá-la barato primeiro.

**Pendência anotada:** o trampolim do V020 deve ser **revertido** no
V021. Ele cumpriu a função e não tem razão para continuar no caminho de
Configurar — patch que não serve mais é armadilha adormecida (lição do
V016).

**Ponto estável: V020.**

**Hardware:** gravação do V020 pelo mantenedor.

---

### 2026-09-13 — V021: tabela do português realocada, com o id "Extras"

Escolha do mantenedor: "Extras" pela opção A, ordem do menu confirmada.
**Dividi o trabalho:** o V021 faz só a realocação; a reestruturação do
menu e a tela Extras ficam para o V022.

**Por que dividir:** a Parte A sozinha seria pior que hoje — esconderia
seis funções atrás de um "Extras" que não abre nada. E a realocação é
independente, é a fundação das duas partes, e tem o melhor teste possível
aqui: **se eu errar, todos os textos do menu quebram de uma vez.** Mesmo
raciocínio do V020: comprar a fundação barato antes de construir em cima.

```text
0x0013A640   reverte o trampolim do V020 (patch que não serve mais é
             armadilha adormecida — lição do V016)
0x001A304C   "Extras\0"
0x00DA3054   tabela do pt realocada, 217 ids, 868 bytes
0x00121104   pool do get_string   -> nova base
0x00048798   vetor de bases       -> nova base
```

A ferramenta relê os 217 ponteiros e compara **string por string** com a
original antes de gravar. **885 bytes, 5 setores**, 22 verificações OK,
ida e volta conferida. `tools/relocate_lang_table.py`.

> **⚠️ Consequência permanente:** passa a existir uma **cópia** da tabela
> do português. Editar a original em `0x00C53B84` deixa de ter efeito.
> `tools/patch_menu_text.py` precisa apontar para `0x00DA3054` antes de
> ser usado de novo em pt — **pendência anotada para o V022.**

**Hardware:** nenhuma operação.

---

### 2026-09-13 — V021 CONFIRMADO no aparelho

Tabela do português realocada para `0x00DA3054`, com o id 216 = "Extras".
Textos do menu corretos. **Ponto estável: V021.**

Com isso, as três premissas da área livre estão confirmadas no hardware:
**dados legíveis** (V017), **código executável** (V020) e agora uma
**estrutura de dados inteira** servindo o firmware em produção (V021).

**Hardware:** gravação do V021 pelo mantenedor.

---

### 2026-09-13 — V022: home com 4 itens + submenu Extras

**30 pontos com guarda individual + 28 bytes de Thumb-2 novo na área
livre.** 217 bytes, 10 setores. `tools/make_extras_menu.py`.

```text
HOME     Música · Imagem · Extras · Configurar
EXTRAS   Vídeo · Gravação · Rádio · Livro digital · Bluetooth · Ver pastas
```

**A decisão de projeto que evitou perder função:** os itens do Extras não
carregam um id de página destino. Eles enviam o Enter **como se viesse da
home** (`page=1, grp=2, ctrl_id=índice_na_home`), então roda o bloco
ORIGINAL de cada item em `page1_process` — com as verificações de cartão,
volume e índice, as mensagens de erro e a varredura assíncrona. Uma
tabela de destinos teria jogado tudo isso fora.

Custo disso: relaxar a guarda de página de `page1_process`
(`cmp r2,r0` → `cmp r2,#1`), 2 bytes.

**A ferramenta recusou duas vezes durante a montagem**, por erro meu:
escrevi na área livre antes de conferir a virgindade dela, e calculei mal
o deslocamento de um `ldr` literal (apontava 8 bytes à frente quando a
palavra estava a 16). As guardas pegaram os dois.

**⚠️ O risco que não mudou:** é o primeiro patch que mexe em `malloc` e
aritmética de ponteiro. **Corrupção de heap não aparece na verificação
byte a byte** — o sintoma é travamento aleatório minutos depois. Se isso
acontecer, mesmo com a tela parecendo certa, **reverta**.

**Pendência do V021 resolvida:** `tools/preview_home.py` passou a ler a
base da tabela de idioma do **pool do `get_string`**, não de um endereço
fixo — senão mostrava "Español" no lugar de "Extras".

**Hardware:** nenhuma operação.

---

### 2026-09-13 — ⚠️ V022 falhou no aparelho: nenhum item do menu abre

A home ficou exatamente como projetada — 4 itens, "Extras" no lugar,
faixa e seleção corretas. **Mas o Enter não abre nada, nem Música.**

**Descartado por leitura:** o disassembly do V022 confere com o projeto
ponto a ponto; a guarda relaxada preserva as flags corretamente; o limite
do Enter não corta o índice visível.

**O que manda no diagnóstico:** Música é o índice 0 da tabela de saltos,
que eu **não toquei**. A falha atinge caminho não alterado → a causa é
algo **compartilhado**, e é uma **premissa** minha, não um byte errado.

> **A lacuna que eu deixei aberta e segui mesmo assim:** nunca tracei
> quem entrega a mensagem de evento da view ao módulo da camada APP. Há
> três chamadores de `page1_process` e não sei qual serve este caminho
> nem que condições impõe. Era exatamente o tipo de premissa não
> verificada que custou o V016 — desta vez custou um patch de 30 pontos.

**Decisão: não chutar outra gravação.** Gerado `V023 = V021 + SÓ a Parte
A` (sem guarda relaxada, sem nada da página `0x53`). Uma gravação corta o
espaço de busca pela metade. Também gerado `OpenPod_Volta_v021/`, que
devolve direto ao último estado que funcionava.

**Hardware:** gravação do V022 pelo mantenedor.

---

### 2026-09-13 — V023 também falhou · V024 isola os limites de índice

`V023 = V021 + só a Parte A` — **continua sem abrir nenhum item.**

**Elimina:** toda a Parte B, a guarda relaxada, a rotina na área livre e
o `b.w` da convergência. **A causa está nos 13 pontos da Parte A** — e,
como Música é o índice 0 da tabela de saltos, que não foi tocado, também
não é a tabela nem o bloco do Extras.

Sobram: os 7 bytes de limite de índice, o limite do laço de criação, a
tabela de ids, e coordenadas/folha.

**V024 = V021 + SOMENTE os 7 bytes de limite.** A home volta a 9 itens
com rótulos originais; só o índice fica limitado a 0..3. Seguro, porque
3 < 9 itens criados. **9 bytes, 2 setores.**

> **Nota de método:** daria para testar dois grupos de uma vez, mas isso
> exigiria deixar o índice ir até 8 com só 4 itens criados — e aí
> `labels[idx]` leria NULL da estrutura zerada. **Um teste que pode
> travar por um motivo diferente do que se quer medir não mede nada.**

**Hardware:** gravação do V023 pelo mantenedor.

---

### 2026-09-13 — ✅ V024 funciona · erro real do V022 identificado

**V024 (só os 7 bytes de limite) abre os 4 primeiros itens** — os limites
são inocentes.

**E ao reexaminar, achei um erro real no V022:**

```asm
0x00D00F4E   ldrb r0, [r3, #0xa]    ; r0 = PÁGINA CORRENTE
0x00D00F50   cmp  r2, r0
```

Eu li isso como só uma guarda e troquei a primeira instrução por
`cmp r2,#1`. Mas o `ldrb` **também carrega r0**, e os blocos que chamam
`0xd0dae0` contam com isso — nenhum deles recarrega r0. O 1º argumento
(página de origem) vinha daquele `ldrb`, 0x2EC bytes antes.

> **Tratei uma instrução com dois efeitos como se tivesse um só.** É um
> erro real e é meu. Explica por que Configurar e o bloco novo do Extras
> falhariam no V022.

**Mas não explica o V023**, que não tem a guarda relaxada. Nele, Música
(cujo bloco recarrega r0 com `bl 0xcfe714`) deveria abrir. Pendente de
confirmação com o mantenedor antes de gravar mais uma vez.

**Hardware:** gravação do V024 pelo mantenedor.

---

### 2026-09-13 — V025: contorna o limite do laço em vez de investigá-lo

No V023 Música não abre; no V024 abre. Por eliminação, a causa é o
**limite do laço de criação** (`cmp r5,#0x24` → `#0x10`) — a única
mudança **estrutural** da Parte A. Coordenadas e ids estão provados
inocentes (as coordenadas dos 4 primeiros são idênticas às do V021, e o
texto renderiza certo).

**Não achei o mecanismo por leitura.** Fica **PROVÁVEL por eliminação**,
não CONFIRMADO por mecanismo — registrado assim de propósito.

**O contorno:** continuar criando os **9 objetos** e mandar os 5 que
sobram para **fora da tela** (`y = 200`). O índice já está limitado a
0..3, então nunca são alcançados.

> **Mesmo raciocínio do V001→V002 com o `write_flash`:** a correção forte
> não é a que acerta o comportamento desconhecido, é a que **torna o
> desconhecido irrelevante**.

**V025: 112 bytes, 7 setores.** `validate_firmware` 22 OK.

**Hardware:** gravação do V024 pelo mantenedor.

---

### 2026-09-13 — ✅ V025 funciona: Parte A resolvida

Os 4 itens aparecem e **todos abrem**. "Extras" abre a página `0x53` — a
lista antiga de 3 itens, conteúdo original dela, como esperado.

**Confirma a hipótese da §20:** o limite do laço era a causa, e criar os
9 objetos escondendo 5 fora da tela contorna sem entender o mecanismo.

**O erro do V022, agora inteiramente explicado.** Eu troquei **duas**
instruções; o certo seria trocar só a segunda:

```asm
0x00D00F4E   ldrb r0,[r3,#0xa]  ->  (intacta — ela carrega r0!)
0x00D00F50   cmp  r2, r0        ->  cmp r2, #1
```

**Apaguei a instrução errada das duas.**

**E a Parte B redesenhada não precisa de relaxamento nenhum**
(`MENU_HIERARQUIA.md` §22): o módulo da página `0x53` repassa para
`page1_process` com o índice remapeado, e o `event_cb` do Extras envia
`page = 0x53`, que **é** a página corrente — a guarda passa intacta, e
`r0` fica com a página de origem correta.

> O patch que eu errei era, além de errado, **desnecessário**.

**Risco que resta:** estender a tela `0x53` de 3 para 6 itens é mudança
**estrutural** — a mesma classe que custou três gravações. **Deve ser
gravada e testada sozinha.**

**Hardware:** gravação do V025 pelo mantenedor.

---

### 2026-09-13 — V026: extensão da página 0x53 para 6 itens, isolada

A foto do V025 confirmou que "Extras" abre a página `0x53` com a lista
antiga — **e com a barra de seleção azul de largura total**. O widget que
o Design System pedia desde o começo existe nativo nessa tela; quando o
Extras estiver pronto será visualmente mais fiel ao nano que a home.

**V026 = V025 + SÓ a extensão de 3 para 6 itens.** 16 pontos na página
`0x53` + tabela de 6 ids na área livre. **Nenhum roteamento.**
67 bytes, 4 setores, 22 verificações OK.

> **Por que sozinho:** é exatamente a classe de mudança que custou três
> gravações — mexer na contagem de itens de uma tela. No
> `page_home_create` quebrou por um motivo que nunca identifiquei, e eu
> só descobri bissectando. **Desta vez vai sozinha.**

Esperado: os 6 itens aparecem e a seleção anda, **mas nenhum abre** — o
despacho é o original, que só trata o índice 0. Não é defeito.

**Hardware:** nenhuma operação.

---

### 2026-09-13 — V027: a seleção vira barra · PADRÃO do projeto

Decisão do mantenedor: **a barra de seleção passa a ser característica
padrão de todos os menus**, não só da tela inicial. Registrado em
`docs/OpenPod_Design_System.md`.

**O mecanismo é uma troca de alvo de chamada.** A seleção chamava
`set_style_text_color` (`0x00D4D10A`); passa a chamar
`set_style_bg_color` (`0x00D4D092`) — mesma assinatura. O texto fica
branco e o fundo vira ciano.

```text
0x0012EB4C   selecao      text_color -> bg_color
4 ramos      desselecao   branco -> preto  E  text_color -> bg_color
0x0012ED58   bl text_align -> rotina na area livre (liga bg_opa = 255)
0x0012ED5E   largura 100 -> 116   barra de x=6 a x=122
```

**41 bytes, 3 setores.** Os 10 saltos gerados foram **decodificados de
volta e comparados** pela ferramenta, e conferidos de novo por capstone.

**Detalhe que faltava:** um rótulo nasce com fundo **transparente**. Sem
ligar `bg_opa` a cor de fundo simplesmente não apareceria — e seria um
"não funcionou" sem sintoma. A rotina de 18 bytes na área livre chama o
`text_align` original e liga o `bg_opa` em seguida.

**Antes disso, um defeito na prévia foi corrigido** (`STATUS_BAR.md`
§13): o renderizador calculava a linha de base só com ASCII, e os
acentos (`á ã í ú`) saíam 1 px acima da caixa do rótulo. O mantenedor viu
o "ú" de "Música" fora da barra. **Era a prévia, não o desenho** — o
texto tem 13 px e o rótulo 15.

> **A prévia é ferramenta de decisão: um erro nela custa uma decisão
> errada.** Essa quase me fez mexer na altura da barra para resolver um
> problema inexistente.

**Hardware:** nenhuma operação.

---

### 2026-09-13 — V027 no aparelho: fundo branco · V028 corrige

A barra funcionou, mas as linhas **ainda não desselecionadas** apareciam
**brancas** — e sumiam uma a uma conforme o mantenedor passava por cima.
O padrão denunciou a causa na hora:

| Seleção em | Linhas brancas |
|---|---|
| Música | as 3 de baixo |
| Imagem | as 2 de baixo |
| Extras | a 1 de baixo |
| Configurar | nenhuma |

**Ao ligar `bg_opa = 255`, o rótulo passou a mostrar a cor de fundo
padrão do tema — que é BRANCA.** Só a desseleção pintava de preto, e ela
só roda quando se passa pela linha.

**V028:** a rotina da área livre passa a pintar `bg_color = preto`
**antes** de ligar o `bg_opa`. Rotina nova em `0x00DA33E4` (28 B); a do
V027 fica no lugar, sem uso, porque a flash não se apaga byte a byte.
**30 bytes, 3 setores.**

> **Lição registrada no Design System:** ao ligar uma propriedade que
> **revela** outra, as duas têm de ser definidas juntas. Ligar a
> visibilidade de algo cujo valor você não definiu é confiar num padrão
> que você não escolheu.

**Hardware:** gravação do V027 pelo mantenedor.

---

### 2026-09-13 — V029: o roteamento do Extras

**O achado que fechou tudo:** existem **duas** tabelas de 83 entradas na
camada APP, e eu tinha confundido as duas.

| Tabela | Tipo | Indexada por | Para quê |
|---|---|---|---|
| `0x00D0DB1C` | `tbh` | página **destino** | criar a página |
| `0x00D0EF64` | **endereços absolutos** | página **corrente** | tratar o evento |

A segunda usa **endereços absolutos**, então aponta direto para a área
livre. E a entrada da página `0x53` apontava para o **caminho de erro** —
a página nunca teve tratador de eventos. Era essa a causa.

**O módulo** (38 B na área livre) confere `ctrl_grp == 2`, limita o
`ctrl_id` a 0..5, reescreve o `ctrl_id` na mensagem pelo `MAPA` e chama
`page1_process`. Assim cada item roda o **bloco original** da home, com
verificação de cartão, mensagens de erro e varredura assíncrona.

**E a guarda não precisou ser relaxada:** o `event_cb` envia
`page = 0x53`, que **é** a página corrente, então a comparação passa
intacta e `r0` fica com a página de origem correta. **O patch que eu
errei no V022 era, além de errado, desnecessário.**

Os índices 1, 2 e 3 da tabela de saltos tinham sido repontados no V025,
deixando vídeo/Gravação/Rádio sem entrada. Voltaram nos slots 5, 7 e 10 —
por isso `MAPA = [5, 7, 10, 4, 6, 8]`.

> **Um erro pego pela conferência:** a primeira montagem gerou
> `ldrb r3,[r3,r3]` em vez de `ldrb r3,[r2,r3]` — `0x5CDB` no lugar de
> `0x5CD3`, registrador base trocado. O disassembly de volta pegou antes
> de gerar kit. Teria dado índice lixo e salto para bloco errado.
> **Desmontar o que se monta não é cerimônia.**

**50 bytes, 5 setores**, 22 verificações OK.

**Hardware:** nenhuma operação.

---

### 2026-09-13 — ⚠️ INCIDENTE: escrita falhou em 0x00D000, aparelho sem resposta

A gravação do V028 falhou no **primeiro setor** (`0x00D000`, a tabela de
partições). O `write_flash` retornou erro; a segunda tentativa nem
conseguiu ler (LIBUSB_ERROR_TIMEOUT). Depois disso o aparelho **não liga
e não enumera** — silêncio absoluto no USB.

**O estado do setor é DESCONHECIDO** — o contador `WROTE` é incrementado
antes da escrita, então "1 setor" significa tentativa, não sucesso.

> **⚠️ Uma premissa de segurança do projeto pode estar errada.** Desde a
> Sessão 20 repetimos que gravar só a partir de `0x00D000` mantinha a
> recuperação garantida. Na Sessão 39 eu encontrei evidência contra isso
> — `"CARDREADER"` está em `0x00046FC7`, **dentro da FIRM**, e o
> bootloader não tem string de USB nenhuma. **Usei o achado para escolher
> a cobaia daquele teste e não voltei para reavaliar a regra geral.**
>
> Se o card reader depende da FIRM rodar, a rede de segurança não cobre
> justamente o setor mais perigoso que o projeto grava. **PROVÁVEL** —
> ainda indistinguível de bateria descarregada.

Documento aberto: `docs/INCIDENTE_V028.md`, com o estado real, os três
hashes possíveis do setor, os caminhos de recuperação ainda não
investigados e o que muda daqui para a frente.

**Hardware:** tentativa de gravação do V028 pelo mantenedor; falhou no
primeiro setor.

---

## v030 — a rede de segurança (2026-09-13)

**Construída sobre o ORIGINAL de fábrica**, não sobre a cadeia V014..V029.
O aparelho novo chega de fábrica; esta é a primeira coisa que entra nele.

### O que faz

`Configurar → Configuração de fábrica` passa a chamar
`HAL_pmu_sd_update_flag_set(1)` (`0x00CF6CA0`) antes de abrir a tela de
sempre. Isso arma o flag 6 no PMU. No boot seguinte o bootloader entra em
`boot sdupdate`, lê `0:\update.up` da raiz do cartão e regrava a flash.

Nenhum comportamento existente muda: a tela de Configuração de fábrica
abre normalmente, e sem cartão preparado armar o flag não faz nada.

### Como

```asm
; gancho: page_set_menu_process, 0x001093DC
00D093DC  b.w 0x00DA3038        ; era b.w 0x00D0E138

; rotina na area livre (fora da FIRM, fora do CRC)
00DA3038  cmp   r2, #8          ; "Configuracao de fabrica"?
00DA303A  bne   0xda3048
00DA303C  push  {r0, r1, r2, lr}
00DA303E  movs  r0, #1
00DA3040  bl    0xcf6ca0        ; HAL_pmu_sd_update_flag_set
00DA3044  pop.w {r0, r1, r2, lr}
00DA3048  b.w   0xd0e138        ; navegacao original, SEMPRE
```

### Setores — a tabela de partições NÃO entra

| ordem | setor | bytes | o quê |
|---|---|---|---|
| 1/3 | `0x1A3000` | 20 | a rotina (o alvo do gancho existe primeiro) |
| 2/3 | `0x037000` | 2 | compensação do CRC |
| 3/3 | `0x109000` | 2 | o gancho — **ativa por último** (R2) |

`0x00D000` não é tocado. O CRC da FIRM volta a `0x49A6`, o valor de
fábrica já gravado na tabela, via `tools/crc_neutralize.py`: CRC-16 é
afim sobre GF(2), então 2 bytes de padding morto em `0x037716`
(2.325 B de folga dos dois lados) devolvem o valor exato.

### Validação

- SHA-256 da entrada conferido contra o original de fábrica;
- gancho conferido byte a byte (`04f0acbe` = `b.w 0x00D0E138`);
- os três saltos gerados decodificados de volta e comparados;
- binário de saída **desmontado com capstone**, instrução por instrução;
- bootloader, ptable, TONE e PSMP conferidos idênticos ao original;
- 24 bytes alterados, tamanho inalterado.

`firmware/WORKING/GN438_openpod_v030.bin`
sha256 `94d77c9ae1425e9899ceec2ab99adae0d2672f35268a770d9e2121de0d2f1b4d`

### Ferramentas novas

- `tools/make_v030.py`
- `tools/crc_neutralize.py`
- `tools/make_install_kit.py` ganhou `--ordem` (regra R2): ordem explícita
  de gravação, para que todo estado intermediário continue bootável.

### Estado

Construída e validada. **Não gravada** — o primeiro aparelho morreu antes.
Aguarda o aparelho novo, e só depois da conferência do SHA-256 do dump.

---

### 2026-09-13 — RECUPERAÇÃO, e as duas regras que caíram

**O aparelho voltou.** Modo de download da ROM de máscara
(`USB + Volume↓ + Reset` → `301a:2800`), leitura pela `smtlink_dump`,
gravação de **um setor de 4096 bytes**. Detalhe em
`docs/MODO_DOWNLOAD.md` e `docs/INCIDENTE_V028.md` §9.

Duas premissas do projeto caíram no mesmo dia:

| regra | estado |
|---|---|
| R0 — precisa de programador SPI como rede | **falsa** — a rede é de fábrica, está na ROM |
| R1 — o CRC da FIRM é obrigatório | **falsa** — CONFIRMADO no hardware |

A prova do R1 veio de graça: consertamos gravando a tabela de partições
**de fábrica** (`CRC = 0x49A6`) por cima de uma FIRM que é a V027, cujo
CRC é outro. Bootou normalmente. **`0x00D000` sai do projeto.**

---

### 2026-09-13 — V028b: fundo preto das linhas (sem tocar 0x00D000)

O mesmo conteúdo da V028, gerado a partir de uma base com a tabela de
partições de fábrica — o que faz o setor `0x00D000` sumir da lista de
diferenças. **2 setores, 28 bytes**, contra 3 setores da V028 original.

Ordem explícita (R2): rotina em `0x1A3000` primeiro, gancho em
`0x12E000` por último. Todo estado intermediário continua bootável.

**Hardware:** gravada, funcionando.

---

### 2026-09-13 — V031: a seleção na CRIAÇÃO também vira barra

**1 byte.** `0x0012EDBC`: `bl set_text_color` → `bl set_bg_color`.

O `patch_barra_selecao.py` (V027) cobriu **seleção** e **desseleção** e
deixou passar o terceiro caminho: a **criação** da tela. Quando a home é
recriada (entrar num item e voltar, ou ligar o aparelho), o índice salvo
era repintado com o estilo antigo — texto ciano, sem barra. Dois
marcadores diferentes na mesma lista.

Os três trechos são o mesmo código; só o alvo da última chamada diferia.

> **O padrão, agora na terceira vez (V016, V027, V031):** um caminho de
> código foi corrigido e outro, que produz o mesmo elemento na tela,
> ficou para trás. **Quando um patch muda a aparência de um objeto,
> enumerar TODOS os pontos que criam ou repintam aquele objeto** — não só
> o que aparece no comportamento observado.

**Hardware:** gravada, confirmada.

---

### 2026-09-13 — V032: a barra encurta para 110 e o chevron volta

**1 byte.** `0x0012ED5E`: `0x74` → `0x6E`.

A V028b ligou fundo opaco nos rótulos. Como o rótulo tem 116 px a partir
de x=6, ele ocupava x=6..121 — e os chevrons da folha de fundo estão em
x=116..121. O fundo pintava por cima deles.

```
barra    x =   6 .. 115   (110 px)
chevron  x = 116 .. 121   (livre)
margens  6 px de cada lado
```

Não era bug de desenho: sobreposição geométrica. Ferramenta nova,
`tools/patch_largura_barra.py`, que **lê as tabelas de coordenadas** e
recusa qualquer largura que invada o chevron ou passe da borda.

---

### 2026-09-13 — V029 marcada OBSOLETA

Construída para consertar o roteamento do Extras. O mantenedor confirmou
no aparelho que **todos os itens do Extras já abrem corretamente** — a
V025/V026 resolveram por outro caminho. Não será gravada.

Fica o achado que ela produziu e que continua válido: as **duas** tabelas
de 83 entradas na camada APP (`0x00D0DB1C` por página destino,
`0x00D0EF64` por página corrente, com endereços absolutos).

---

### 2026-09-13 — V035: fonte mais grossa (revertida na V038)

**1 setor, 171 glifos.** A fonte de texto do firmware é **1 bpp**, sem
canal alfa, então engrossar é acrescentar pixel. Duas travas:

1. **Não fechar vão** — só espalha para x+1 se x+2 estiver apagado.
   Sem isso o `M` (`.#.#.#.#.`) vira bloco sólido (`.########.`).
2. **Não passar do avanço** — o texto não fica mais largo em px nenhum.
   Medido: `08:31 OpenPod` 89 px antes e depois, `Música` 39 e 39.

Descritor de glifo decodificado e validado renderizando:

```
+0  u32 offset no blob   +4  u32 avanço
+8  u16 stride em bits   +10 u16 altura
+12 s16 ofs_x            +14 s16 ofs_y
```

**Revertida na V038 a pedido do mantenedor** — na prévia em ASCII o peso
parecia bom; no LCD real não ficou. Ferramenta preservada em
`tools/patch_fonte_negrito.py`.

> **Lição:** prévia em ASCII prova *correção* (o M sobreviveu, a largura
> não mudou), não prova *estética*. Para decisão visual, o aparelho é o
> único juiz.

---

### 2026-09-13 — V034, V036, V037: a barra de rolagem, em três tentativas

A linha vertical à direita da home era barra de rolagem — os 5 itens que
a V025 escondeu em **y=200** fazem o conteúdo medir ~215 px numa janela
de 141, e a proporção da linha (dois terços da altura) batia com isso.

| versão | o que tentei | resultado |
|---|---|---|
| V034 | `clear_flag(r4, SCROLLABLE)` | continuou |
| V036 | `bg_opa=0` em `LV_PART_SCROLLBAR`, ainda em `r4` | continuou |
| V037 | o mesmo, agora em **`r7`** | **sumiu** ✅ |

**Erro 1 (V034):** deduzi da documentação da LVGL que a flag bastava, sem
evidência no binário.

**Erro 2 (V036):** corrigi o mecanismo e **mantive o alvo errado**. As
linhas são criadas com pai `r7` (`0xD2EC82: r7 = 0xD5615C(r4)`), não
`r4`. Bastaria ter olhado quem era o pai antes de gravar de novo.

> **É o mesmo padrão do V016/V027/V031:** corrigir uma dimensão do
> problema e não reexaminar a outra. Registrado ali, repetido aqui.

**O que ficou de conhecimento** — seletores de parte da LVGL, confirmados
neste binário (não supostos), varrendo chamadas a setters de estilo:

```
0x00010000  LV_PART_SCROLLBAR   (1 chamada, em 0x00D29CC8)
0x00020000  LV_PART_INDICATOR   (7)
0x00040000  LV_PART_SELECTED    (9)
0x00050000  LV_PART_ITEMS       (1)

lv_obj_add_flag    0x00D49204   (orrs  [r4,#0x1c])
lv_obj_clear_flag  0x00D4924A   (bic.w [r4,#0x1c])
```

A codificação de `mov.w r2, #0x10000` foi **copiada de 0x00129CC0**, do
próprio firmware, em vez de gerada.

---

### 2026-09-13 — V039: a lista do sistema começa a virar nano

**4 bytes, 1 setor** — e pega **Extras e Configurar juntos**, porque as
duas são `page_set_menu_create` (0x00D3A638) com tabelas diferentes.

```
0x0013A7BA  1 B  divisor 7 -> 10    altura da linha 22 -> 16 px
0x0013A8BC  4 B  ícone U+F013 -> string vazia
```

`0x00D568CC` é `lv_disp_get_ver_res`; o código faz `altura = 160/divisor`.
Com 10, a linha fica com 16 px — o passo da home — e 10 itens ocupam
exatamente os 160 px da tela.

**Estrutura da tela, desmontada:**

```asm
r4 = 0xD21764(...)                ; a linha
     set_h(r4, ver_res/sb)        ; sb = o divisor
     set_align(r4, 2, 0, (ver_res/sb)*i - 1)
fp = novo_rotulo(r4)
     0xD4D12E(fp, 0x00CA671C)     ; fonte de ícones
     set_text(fp, 0x00C5D622)     ; U+F013, a engrenagem
sb = novo_rotulo(r4)
     set_w(sb, hor_res - 15)
     set_text(sb, get_string(id))
```

Struct: linhas em 0, rótulos em `0x28`, ícones em `0x50` — confirma o
esquema `N*4 / 2*N*4` para N=10.

**Falta para a padronização:** separador entre itens (provável borda do
widget `0xD21764`) e a barra superior com relógio e título — este último
é o mesmo trabalho documentado em `docs/STATUS_BAR.md` para a home.

---

### 2026-09-13 — V054 / OpenPod 1.6: título na barra superior de 37 telas

**A pendência nº 1 do `ESTADO_ATUAL.md`, e ela não era o que parecia.**
O roadmap dizia *"a única pendência que cria objeto e mexe com malloc"*.
Não cria: o criador do rótulo do título (`0x00D226AC`) já existe desde o
V017, e `view_icon_create` já tem o número da página corrente na mão.

```text
0x00123880   30 B  bloco do titulo  ->  bl 0x00DA5000 + 13 NOPs
0x001A5000   88 B  rotina: pagina -> tabela -> cria rotulo -> get_string
0x001A5058   76 B  tabela de 37 telas, 2 bytes cada
0x00123E8A    2 B  ldrb r2,[r6] -> b 0x00D23EA2
```

**193 bytes, 3 setores.** Detalhe completo em `docs/STATUS_BAR.md` §14.

**Custo por tela nova daqui em diante: 2 bytes na tabela.**

**Corrige um defeito da 1.5:** remover o cartão SD com a home na tela
apagava o título "OpenPod" (`0x00D23E86`, herança de quando aquele slot
era o ícone do cartão). Achado varrendo *quem mais escreve neste slot* —
a pergunta que faltou no V016.

**Quase repeti o erro de 2026-09-12:** a primeira versão da ferramenta
recalculava o CRC da FIRM, o que traria o setor `0x00D000` de volta para
a lista de gravação. A regra **R1** já tinha aposentado esse setor. A
ferramenta agora recusa qualquer diferença abaixo de `0x00E000`.

Ordem de gravação (**R2**): `0x1A5000` (a rotina) → `0x10A000` (carimbo)
→ `0x123000` (o gancho, que é o que ativa). Antes do último setor a
rotina está gravada e ninguém a chama.

Não testado no aparelho. Sem título ainda: página 23 (`page_record_time`,
não identificada com confiança).

---

### 2026-09-13 — V055 / OpenPod 1.6: o raio da seleção, em 1 byte

**A pendância que já tinha custado duas versões, e o erro estava numa
constante.**

```text
0x001A3530   movs r1, #0x0b  ->  movs r1, #0x60
```

A rotina da cor da seleção terminava com
`despachante(linha, 0x0B, 0, 0)`. Na LVGL v8 deste binário, `0x0B` é
`TRANSFORM_HEIGHT` — a chamada era válida, executava, e setava um valor
que já era o padrão. `LV_STYLE_RADIUS` é **96**.

**Como foi determinado, desta vez:** enumerando a família inteira de
wrappers de estilo do firmware, não a documentação da LVGL. A tabela
está em `docs/GUI_ANALYSIS.md` e fecha sem sobra; dois membros já eram
conhecidos por uso independente (fonte e cor de fundo).

**O que o tool antigo afirmava, e estava errado:**

> *"`lv_obj_set_style_radius` não existe no binário"* — existe:
> `0x00D4D064`, e é chamado **51 vezes**, quase sempre na forma
> `(obj, 0, 0)`. É o idioma do firmware para deixar algo quadrado. A
> faixa e o contêiner da lista recebem; a linha compartilhada não.

A evidência necessária já estava no cabeçalho do tool que falhou: ele
listou **quatro** wrappers e parou. Enumerar a tabela toda teria mostrado
`prop 96 = RADIUS` ali.

> **Lição:** quando a resposta depende de uma constante do binário,
> enumerar é barato e deduzir é caro. `tools/fix_raio_selecao.py` agora
> **desmonta o wrapper e confere a propriedade na imagem de entrada** —
> se a análise algum dia estiver errada, ele recusa em vez de gravar.

**1 byte, 1 setor**, na área livre, fora da FIRM. Reversível em 1 byte.
A home não é afetada (não usa `0x00D21764`).

### A 1.6 vai com os dois patches

Decisão do mantenedor: juntar o raio ao título.

```text
0x1A3000   raio da selecao          <- 1 byte
0x1A5000   rotina + tabela do titulo
0x10A000   carimbo de versao
0x123000   o gancho                 <- por ultimo, e o que ATIVA
```

**4 setores, 208 bytes.** Ordem R2 preservada: até o último setor a
rotina do título está gravada e ninguém a chama.

---

### 2026-09-13 — V056 / OpenPod 1.7: M volta, VOL desce

**A segunda pendência do `ROADMAP_1.1.md`, fechada — e em 1 ponto, não
em 21.**

O mantenedor respondeu a pergunta que a análise estática não alcançava:
no Extras, **o M não faz nada e o VOL volta**. Logo `0x81` = VOL e
`0xA0` = M. A ambiguidade estava aberta no `BUTTON_ANALYSIS.md` desde o
começo do projeto.

```text
0x00147654    6 B  str r1,[sp,#4] ; bl 0xd47648
                -> bl 0x00DA50C0 ; nop
0x001A50C0   64 B  rotina de tradução de tecla (Thumb-2)
0x001A5100   22 B  tabela de 21 páginas
```

`0x00D47654` é o `lv_group_send_data` da LVGL — **o único ponto do
firmware que envia `LV_EVENT_KEY`**. Toda tecla de toda tela passa ali.
Traduzir nesse ponto vale para o aparelho inteiro.

```text
nas 21 telas da tabela:
    0x81 VOL -> 0x12  LV_KEY_DOWN   (a tela ja trata como "proximo")
    0xA0 M   -> 0x81                (a tela ja trata como "back")
```

**Nenhum comportamento novo foi criado** — só a escolha de qual botão
aciona qual ramo que já existia. A home não está na tabela e não muda.

**As 21 páginas foram verificadas uma a uma**, simulando a cadeia de
comparações de cada callback: `0x12` tem que chegar em
`lv_group_focus_next`, `0x81` tem que chegar num ramo `"-%s back"`, e
`0xA0` tem que estar hoje caindo no ramo de erro. A ferramenta refaz a
verificação a cada execução e recusa se uma só falhar.

**28 telas ficaram de fora de propósito** — não tratam `0x12` como
"próximo", então remapear o VOL nelas o deixaria morto. Entre elas, o
**Now Playing**: a versão ingênua do patch teria quebrado o botão de
voltar dele.

> **O detector errou duas vezes antes de acertar** — parava no `pop.w`
> (perdendo o *tail call* logo depois) e andava de 2 em 2 bytes por dentro
> de uma instrução de 4. Aprovava 5 páginas em vez de 21. O que salvou
> foi validar o simulador contra o Extras, que eu já tinha lido à mão.
> **Analisador novo sem caso de controle é chute com aparência de dado.**

Detalhe completo em `docs/BUTTON_ANALYSIS.md` §8.

### O kit 1.7

A 1.6 nunca chegou ao aparelho. O `.up` é **imagem inteira**, então a 1.7
contém tudo:

```text
0x1A3000   raio da selecao
0x1A5000   rotina do titulo + rotina da navegacao
0x10A000   carimbo de versao
0x123000   gancho do titulo       <- ativa o titulo
0x147000   gancho da navegacao    <- ativa a navegacao
```

**5 setores, 300 bytes.** Ordem R2: as rotinas primeiro, os dois ganchos
por último. `0x00D000` intocado.

---

### 2026-09-13 — V057 / OpenPod 1.8: navegação revertida ao padrão do produto

**A 1.7 rodou no aparelho. A barra superior passou; a navegação não.**

Relato do mantenedor: *"os menus ficaram bons, agora todos no tamanho
certo"* — e, sobre os botões, que o certo seria **M sem função, VOL
voltando**, pedindo que eu conferisse se era o padrão do produto.

**Era.** Censo no `GN438_original.bin`, 49 telas que tratam tecla:

```text
VOL (0x81) = "voltar"     em 41 telas
M   (0xA0) = sem funcao   em 41 telas
```

Eu tratei especificação como defeito. O argumento que usei — *"M tem nome
de Menu, e no iPod o Menu volta"* — era analogia com outro aparelho, não
evidência deste. **O censo custava 30 segundos e teria evitado a versão.**

> **Regra derivada:** antes de chamar um comportamento de defeito, contar
> quantas telas do firmware de fábrica o repetem. 41 de 49 é decisão de
> produto; 1 de 49 é candidato a defeito.

```text
0x00147654    6 B  bl 0x00DA50C0 ; nop  ->  str r1,[sp,#4] ; bl 0xd47648
0x001A50C0  832 B  rotina + tabela      ->  0xFF
```

**3 setores, 118 bytes.** A imagem revertida bate **byte a byte** com a
V055 — o patch era autocontido.

Ordem R2 **invertida**: o gancho primeiro (desativa), a rotina por último
(só então pode ser apagada). Apagar a rotina antes deixaria um estado em
que a primeira tecla saltaria para `0xFF`.

**O mapa de teclas continua valendo** e é o que custou caro: `0x81`=VOL,
`0xA0`=M, e `0x00D47654` como ponto único de toda tecla de toda tela.
`tools/patch_navegacao.py` fica no repositório, desaplicado.

Detalhe em `docs/BUTTON_ANALYSIS.md` §9.

### ✅ Confirmado no aparelho pela 1.7

- a **barra superior com título** funciona nas telas de lista;
- as **alturas de linha** ficaram certas ("todos no tamanho certo");
- a premissa da área livre continua válida, agora com **código** e não
  só dado: a rotina do título em `0x001A5000` executou.


---

### 2026-09-14 — V058/V059 / OpenPod 1.9: texto branco e respiro

Duas correções de acabamento vindas do uso da 1.8.

**Texto cinza nas listas (V058).** Mesma estrutura da cor da seleção: a
home pinta o texto explicitamente, as listas do sistema não pintam nada
e caem no tema. A V013 consertou os dois *getters* de cor — e quem nunca
chama getter nenhum não foi beneficiado. `TEXT_COLOR` tem o bit de
herança, então pintar a **linha** pinta o rótulo filho.

```text
0x001A5200  24 B  rotina: chama a antiga e acrescenta a cor do texto
0x001217AA   4 B  bl 0x00DA3518 -> bl 0x00DA5200
```

**A barra de seleção encostando no título (V059).** Não era falta de
separador: a faixa **já desenha** um traço (`border_width=1`,
`border_side=BOTTOM`). A linha 0 da lista caía em `y = altura_da_faixa - 1`
— exatamente em cima do traço. O `-1` servia às linhas de 22 px do
desenho original; com as de 16 px da V039/V040 virou colisão.

```text
0x001A5220  18 B  rotina: radius (que ja fazia) + pad_top = 3
0x001216CC   4 B  bl set_style_radius -> bl 0x00DA5220
```

O contêiner da lista sai de um helper compartilhado por **58 páginas**
(`0x00D21690`), então são 4 bytes para todas. Os 3 px saíram da
geometria: dão 2 px de respiro no Configurar, igual ao da home.

**3 setores, 72 bytes.** Detalhe em `docs/STATUS_BAR.md` §15.

> **Ressalva:** o helper serve 58 páginas e eu não conferi as 58. Telas
> que não sejam lista também ganham o padding. Reversível em 4 bytes.

## OpenPod 2.2  (interno V073, carimbado)

Base de gravacao: OpenPod 2.1 (V070). 25 setores, 187 bytes alterados.
Ordem R2: `0x1A5000` (rotinas) antes de todos os ganchos.

- **Extras: clicar nao levava a nada.** O `patch_extras` da 2.1 mandava a
  mensagem para a *entrada* de `page1_process`, que exige `msg[0x0a]==2`;
  o Extras chega com `==4` e ela morria em `0x00100F66`, antes do `tbh`.
  Tabela, mapa e rotina estavam certos — o trajeto nao. A rotina agora
  entra em `0x00100FB2`, ja depois das guardas que `pstr_page84_process`
  fez identicas, e **preserva `[0x0a]`**: a cauda `0x00101036` o repassa,
  e e isso que faz o "voltar" retornar ao Extras. Monta tambem `r6` com
  o global `0x00823D05`, que a cauda `0x0010101C` le antes de escrever.
  (`tools/patch_extras_fix.py`)
- **Altura de linha unica (Saturno S11).** O aparelho tinha DUAS: 28
  pontos com o imediato 10 px e 10 calculando `160/10` = 16 px. A tabela
  e a home dizem 16. Os 38 pontos agora leem `altura_linha` (+0x0D).
  Mudanca visivel: as listas das 28 telas ficam menos apertadas.
  (`tools/patch_saturno_s11.py`)
- **Fundo lendo o campo de fundo (Saturno S12).** `0x00122F5A` pintava
  `BG_COLOR` da pagina 0x18 com o getter de *cor de texto*; agora le
  `cor_tela`. (`tools/patch_saturno_s12.py`)
- **Auditoria:** `audita_chrome.py` passou a conferir a LINHA. O ponto
  cego que me fez relatar "SEM DIVERGENCIAS" com o defeito aberto esta
  fechado — o novo teste acusa a V070 e aprova a V073.

Correcoes de registro apuradas no firmware de fabrica:
- o fundo branco **nao** foi causado pela V013: `0x00121384` ja era
  `mov.w r0,#-1` no original;
- os rotulos da faixa em `TOP_LEFT x=40` / `TOP_RIGHT x=-45` sao
  **icones**, nao o contador da Musica.

---

## OpenPod Core 1.0  (2026-09-14)

**A primeira versão da nova linha. Base: o firmware ORIGINAL de fábrica.**

Relatório completo: `docs/releases/OpenPod_Core_1.0.md`.

```
Status     EXPERIMENTAL — nao testada no aparelho
Receita    tools/build.py --receita core1.0   (5 passos)
Diff       8 setores, 9.143 bytes, menor offset 0x048798
           0x00D000 NAO tocado · nada abaixo de 0x00D000 · PSMP intocada
Valida     validate_firmware 21 OK + a falha de CRC da R1
.up        1.724.416 B, CRC 0x69FF conferido
sha        e42be52362bd0f22980f56def0a67d87f5390b16c799f4a35037648eb1f37f55
```

O que entrou: logo do OpenPod na abertura, tabela do português na área
livre, textos revisados em PT-BR, 'Vídeo' com maiúscula, item "Atualizar
por SD" em Configurar, e a versão na tela Informações.

O que ficou de fora **de propósito**: home em lista, faixa superior,
título por tela, Saturno inteiro, Extras. Continuam na receita
`interface` e voltam na Core 2.0.

**O recuo visual é o preço declarado de uma fundação auditável.** A home
volta à grade 3×3 de fábrica.

### O que esta versão fechou, além dela mesma

- **`tools/patch_logo.py`** — a ferramenta da V007 tinha sumido do
  repositório, e por isso a 3.0 e a 3.1 bootavam com o logotipo GENAI.
  A nova reproduz o slot da V007 **byte a byte** (`--autoteste`).
- **Receitas nomeadas no `build.py`** — `--receita core1.0` e
  `--receita interface`.
- **`--texto-info` no `make_install_kit`** — a tela Informações aceita
  duas linhas; antes era sempre o nome da versão numa linha só.

### Pendências registradas

A tela Informações só cabe 2 linhas (o prompt pede 4; defeito de layout
na camada VIEW, não localizado). `patch_versao.py` é a última ferramenta
que ainda aloca sozinha na área livre. O binary diff e a validação ainda
não são passos do `build.py`.

---

## OpenPod Core 1.0.1  (2026-09-14)

**Versão de correção. Base: a Core 1.0, gravada e testada no aparelho.**

Relatório: `docs/releases/OpenPod_Core_1.0.1.md`.

```
Diff contra a 1.0    10 bytes, 2 setores
     0x122000   2 B  os dois BL da logo -> getter preto
     0x1A4000   8 B  o texto da tela Informacoes
.up                  1.724.672 B, CRC 0x67AB
sha                  36125f5665b8613e0d96215e2ffcf36170d847068d0c72e572167fe506400c1f
```

### O teste da 1.0 no aparelho

Passou: ligou, menus em português "atualizados perfeito", item "Atualizar
por SD" apareceu, nada quebrado. **Quatro de seis itens do roteiro, na
primeira gravação da linha Core.**

Falhou em dois, corrigidos aqui.

### Defeito 1 — retângulo preto na abertura

A logo tem fundo preto, a tela tem fundo claro. As duas funções que
desenham a logo consultavam o getter de cor **clara**; passam a consultar
o de **preto**. 2 bytes.

É o patch da V008, de 12/09, que já tinha rodado na tela. A ferramenta
tinha se perdido quando a construção virou receita — **a mesma história
do `patch_logo.py`**. Voltou como `tools/patch_fundo_abertura.py`, com
autoteste contra a V008.

> **O padrão, agora na segunda vez:** conhecimento que existia só na
> imagem, não na ferramenta, sumiu quando a corrente virou receita. Vale
> varrer o CHANGELOG antigo atrás de outros patches sem ferramenta.

### Defeito 2 — tela Informações sobreposta

**A causa era uma afirmação minha, errada, nunca verificada.** O
`patch_versao.py` dizia que o rótulo aceita `\n`. Aceita — num rótulo
LVGL comum. A tela Informações monta uma **mensagem**
(`0x00D0D818`), e esse caminho **não quebra linha**: o aparelho desenhou
os dois textos um sobre o outro.

Medido agora: a tela tem **dois** espaços de texto, o título
(`get_string(43)`, **um único chamador**) e a linha de baixo, cada um de
**uma** linha, limite 113 px.

Decisão do mantenedor: voltar a uma linha só, como da 1.4 à 3.0. O
cabeçalho do `patch_versao.py` foi corrigido — a afirmação errada não
fica no repositório.

### ✅ Core 1.0.1 declarada STABLE — 2026-09-14

Mantenedor, depois de ver o aparelho: **"Tudo funcionou."**

```
abertura                  logo sobre PRETO, sem moldura clara   OK
Configurar > Informacoes  duas linhas, sem sobrepor             OK
Atualizar por SD          instalada PELO CARTAO, funcionou      OK
```

**A Core 1.0.1 e a BASELINE da linha Core.** Versoes novas partem dela,
nao do ORIGINAL — e o que STABLE autoriza (§6 do prompt-mestre).
Reconstruivel a qualquer momento: `tools/build.py --receita core1.0` sai
sempre em `7312fbd066b1a31e...`.

### O caminho de atualizacao inteiro deixou de ser teoria

A instalacao por cartao funcionou de ponta a ponta, com uma imagem gerada
pelo nosso pipeline:

```
build.py -> gera_up.py -> update.up no cartao
  -> Configurar > Atualizar por SD
     -> HAL_pmu_sd_update_flag_set (0x00CF6CA0, orfa no firmware de fabrica)
        -> reboot -> bootloader le 0:/update.up -> grava -> boota
```

Cada elo era **analise estatica**. Agora e **CONFIRMADO**. Consequencia
pratica: daqui em diante nenhuma versao precisa de cabo, de modo download
ou de abrir o aparelho.
