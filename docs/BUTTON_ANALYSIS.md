# OpenPod — BUTTON_ANALYSIS

Análise do subsistema de entrada do GN-438.

> **Aviso de escopo.** Esta fase foi baseada em extração de strings e
> estruturas de dados. **Nenhum handler de tecla foi desmontado.** Portanto
> nada aqui descreve o comportamento real de um botão físico — apenas a
> arquitetura de software que os processa. As lacunas estão marcadas.

---

## 1. Nós de dispositivo de entrada — CONFIRMADO

Extraídos das strings do firmware:

| Nó | Ocorrências | Papel provável |
|---|---|---|
| `/dev/key_onoff` | 2 | tecla liga/desliga, tratada à parte |
| `/dev/key_io` | 2 | teclas em GPIO |
| `/dev/kadc_ch0` … `/dev/kadc_ch5` | 6 canais | **teclas por ADC** (escada resistiva) |
| `/dev/exti` | 2 | interrupção externa |
| `/dev/tp` | 6 | **touch panel** |

### Duas observações que precisam de verificação

**(a) `/dev/kadc_ch*`** — seis canais ADC de teclado. O padrão clássico
em players deste custo é uma **escada resistiva**: vários botões em um
único canal analógico, discriminados por faixa de tensão. Se for o caso,
"remapear um botão" é alterar limiares numéricos, não pinos — o que é
consideravelmente mais fácil. **NÃO CONFIRMADO.**

**(b) `/dev/tp`** — há um driver de touch panel no firmware. O GN-438
descrito no `CLAUDE.md` tem apenas botões físicos. Isto pode ser:
- código do SDK compartilhado com outro modelo que tem toque; ou
- o GN-438 realmente ter touch não documentado.

**NÃO RESOLVIDO.** Não assumir nenhuma das hipóteses.

---

## 2. Cadeia de eventos — PROVÁVEL

Reconstruída a partir dos nomes das funções de depuração:

```text
Hardware
   │  GPIO / ADC / EXTI
   ▼
/dev/key_onoff · /dev/key_io · /dev/kadc_chN
   │
   ▼
key manager  ──  identifica key_id
   │            ("-%s can not find key_id %x")
   ▼
watch_key_manager  ──  despacha conforme run_status
   │
   ├── watch_key_work_process
   ├── watch_key_back_light_off_process
   ├── watch_key_pv_sync_process
   ├── watch_key_sleep_wait_process
   ├── watch_key_sleep_process
   └── watch_key_wake_up_process
   │
   ▼
watch_key_sendMsgTo_task  (fila de mensagens)
   │
   ▼
_presenter_key_analysis  ──  camada de apresentação
   │
   ▼
pageNN_btn_process / pageNN_key_process  ──  tela ativa
   │
   ▼
LVGL  (lv_indev / lv_group)  ──  LV_KEY_*
```

Evidência para cada elo: todas as funções citadas aparecem como strings
literais no binário. A **ordem** entre elas é inferida pelos nomes e pelo
padrão do SDK — classificação **PROVÁVEL**, não confirmada.

---

## 3. Máquina de estados de energia — CONFIRMADO

O despacho de teclas depende de um `run_status`. Cinco estados foram
identificados por nome:

| Estado | Função |
|---|---|
| trabalho normal | `watch_key_work_process` |
| luz de fundo apagada | `watch_key_back_light_off_process` |
| sincronização PV | `watch_key_pv_sync_process` |
| aguardando dormir | `watch_key_sleep_wait_process` |
| dormindo | `watch_key_sleep_process` |
| acordando | `watch_key_wake_up_process` |

String de erro correspondente: `-watch_key_manager can not find run_status %d!`

> **Importante para o OpenPod:** o mesmo botão faz coisas diferentes
> conforme o estado de energia. Qualquer remapeamento tem de considerar os
> seis caminhos, não apenas o de trabalho normal.

---

## 4. Teclas nomeadas explicitamente — CONFIRMADO

Apenas **três** teclas têm tratamento nomeado no módulo `watch_key`:

| Tecla | Strings |
|---|---|
| **onoff / power** | `- onoff key`, `-onoff key press !`, `-onoff key short release status to backlight`, `-onoff key short release status to work`, `-onoff key long start`, `-onoff key long press`, `-onoff key long release`, `-%s power_key_event false %d!` |
| **volume_up** | `- volume_up key`, `-volume_up key press Vol+`, `-volume_up key short release Vol+`, `-volume_up key long en Vol+`, `-volume_up key long press Vol+` |
| **volume_down** | `- volume_down key`, `-volume_down key short release Vol-`, `-volume_down key long en Vol-`, `-volume_down key long press Vol-` |

### Gestos suportados — CONFIRMADO

Cada tecla distingue quatro eventos distintos:

```text
press            →  pressionar
short release    →  toque curto
long start / en  →  início do pressionar longo
long press       →  pressionar longo sustentado
long release     →  soltar após pressionar longo
```

Complementado por, na camada de UI:
`-short click`, `- repeat`, `-long pressed repeat`, `-repeat_state: %d`,
`-repeat_cnt clean`, `-%s long pressed repeat no ctrl_id: %d`.

Ou seja, **existe auto-repetição** com contador — o comportamento de
"segurar para avançar rápido" já está implementado. O OpenPod pode reusar.

---

## 5. Lacuna crítica: os demais botões

O `CLAUDE.md` descreve fisicamente:

```text
             M
             ↑
      |<<   ← ● →   >>|
             ↓
            VOL
             ▶Ⅱ
```

O módulo `watch_key` só nomeia **onoff, volume_up e volume_down**.
Os botões M, ◀◀, ▶▶, ▶Ⅱ e as direções **não aparecem com nome próprio**
em nenhuma string.

Três explicações possíveis, **nenhuma verificada**:

1. Chegam pelo mesmo `key_id` genérico e são discriminados numericamente
   (`-%s can not find key_id %x` sugere um mapa numérico de key_id).
2. São processados em outro módulo, não coberto por strings de debug.
3. São mapeados diretamente para códigos LVGL (`LV_KEY_*`) sem passar
   pelo `watch_key`.

Há suporte parcial à terceira hipótese: existem as strings
`-%s LV_KEY_LP_ENTER` e `-%s LV_KEY_LR_ENTER` em `0x000D5575` e
`0x000D558C` — ou seja, *long press* e *long release* do ENTER do LVGL
são tratados explicitamente.

**Status: NÃO RESOLVIDO.**

---

## 6. Mapa Button → Função

Não é possível produzi-lo honestamente nesta fase. A tabela abaixo
registra o que se sabe e o que falta:

| Botão físico | key_id | Evento | Ação | Status |
|---|---|---|---|---|
| Power | — | press / short / long | backlight, work, poweroff | parcial: efeitos conhecidos, key_id desconhecido |
| VOL+ | — | press / short / long / repeat | volume acima | parcial |
| VOL− | — | press / short / long / repeat | volume abaixo | parcial |
| M (menu) | ? | ? | ? | **DESCONHECIDO** |
| ◀◀ | ? | ? | ? | **DESCONHECIDO** |
| ▶▶ | ? | ? | ? | **DESCONHECIDO** |
| ▶Ⅱ | ? | ? | ? | **DESCONHECIDO** |
| ← / → / ↑ / ↓ | ? | ? | ? | **DESCONHECIDO** |

---

## 7. Próximos passos para fechar esta análise

1. Desmontar o handler que emite `-%s can not find key_id %x` e extrair a
   **tabela de key_id** — isso resolve a lacuna da seção 5 de uma vez.
2. Localizar a tabela de limiares do ADC (`kadc`) e determinar se há
   escada resistiva.
3. Determinar se `/dev/tp` é usado em runtime ou é código morto.
4. Mapear a conversão `key_id` → `LV_KEY_*` na camada `lv_indev`.
5. Só então propor o mapeamento de botões do OpenPod.

> Enquanto os itens 1 e 2 não estiverem resolvidos, **não** alterar
> nada relacionado a entrada. O risco é ficar com um aparelho que liga
> mas não navega.

---

## ✅ Serigrafia → comportamento: resolvido POR OBSERVAÇÃO (2026-09-12, V014)

> A seção anterior recomendava desmontar a tabela de `key_id`, que está em
> RAM, para resolver a lacuna. **O V014 resolveu por outro caminho: o
> aparelho respondeu mais rápido que o disassembly.**
>
> Com o menu principal em lista vertical, cada ramo de tecla de
> `page_home_event_cb` passou a ter um efeito visualmente distinto
> (andar 1 linha × pular 3 linhas × entrar). Bastou apertar os botões.

### O que foi observado no aparelho

| Serigrafia | Efeito na home em lista | Ramo em `page_home_event_cb` |
|---|---|---|
| `\|<<` (voltar) | anda **1 linha** | `0x00D2E9DE` ou `0x00D2EACE` (±1) |
| `>>\|` (passar) | anda **1 linha** | o outro dos dois (±1) |
| `M` | pula **3 linhas** | `0x00D2EA3A` ou `0x00D2EB26` (±3) |
| `VOL` | pula **3 linhas** | o outro dos dois (±3) |
| `▶Ⅱ` (play/pause) | **entra** no item | `0x00D2EA52` → `key_id 0x0A` |

**CONFIRMADO** (observado na tela, com o firmware V014 em execução).

### O casamento exato com o `key_id`

Os ramos, levantados por disassembly, são:

```text
key_id 0x14 / 0x87  ->  indice - 1   (volta 0 -> 8)     0x00D2E9DE
key_id 0x13 / 0x8A  ->  indice + 1   (volta 8 -> 0)     0x00D2EACE
key_id 0xA0         ->  indice - 3   (0,1,2 -> +6)      0x00D2EA3A
key_id 0x81         ->  indice + 3                      0x00D2EB26
key_id 0x0A         ->  abre o item                     0x00D2EA52
```

`▶Ⅱ = 0x0A` é **CONFIRMADO**: é o único ramo que abre item.

Qual dos dois botões de ±1 é `0x13` e qual é `0x14` — e idem para `M` /
`VOL` contra `0xA0` / `0x81` — continua **NÃO DETERMINADO**. Falta uma
observação de uma linha: **qual deles desce a seleção**. Quem desce é o
`+1` (`0x13`/`0x8A`); quem sobe é o `−1` (`0x14`/`0x87`).

### Por que isto importa

A seção anterior dizia, com razão: *"enquanto a tabela de `key_id` não
estiver resolvida, não alterar nada relacionado a entrada"*. **Essa
ressalva continua valendo** — o que mudou é que agora sabemos o
**comportamento** de cada botão sem ter alterado nada de entrada. O V014
não remapeou nenhuma tecla; só tornou os ramos distinguíveis a olho.

> **Lição de método, a mesma da Sessão 26 (`COLOR_SOURCE.md` §10):** com
> um pipeline de gravação provado e reversível, o hardware responde mais
> rápido que a análise estática. Em vez de extrair uma tabela que vive em
> RAM, bastou um patch de layout que já íamos fazer de qualquer jeito.

### Consequência para o OpenPod

Na lista vertical, `|<<` e `>>|` viram **cima/baixo** naturalmente, e
`▶Ⅱ` vira **entrar** — que é o gesto do iPod. `M` e `VOL` pulando 3
linhas é herança da grade 3×3 e não tem significado numa lista.

**Recomendação: não mexer nisso agora.** Os dois ramos de ±3 fazem
aritmética que já volta dentro de 0..8 — não há risco de índice fora da
faixa. Converter para ±1 deixaria quatro botões fazendo a mesma coisa,
o que é pior, não melhor. A decisão útil é dar a `M` o papel de **voltar**
e a `VOL` o de **volume**, mas isso é mudança de entrada de verdade — e
aí a ressalva acima volta a valer com força total.

### A roda física, fotografada

```text
              M          ← cima
    |<<      ▶Ⅱ      >>|
              VOL        ← baixo
```

Com a foto, o comportamento observado deixa de ser arbitrário e passa a
ter explicação: **é a semântica da GRADE 3×3.**

| Botão | Posição física | Na grade 3×3 | Passo |
|---|---|---|---|
| `\|<<` / `>>\|` | esquerda / direita | anda 1 célula na linha | **±1** |
| `M` / `VOL` | cima / baixo | pula uma linha inteira | **±3** |
| `▶Ⅱ` | centro | abre | — |

**PROVÁVEL, com alta confiança:** `M` = `0xA0` (−3, linha acima) e
`VOL` = `0x81` (+3, linha abaixo); `|<<` = `0x14`/`0x87` (−1) e
`>>|` = `0x13`/`0x8A` (+1). A inferência vem da geometria da grade, não
de leitura da tabela de `key_id` — que continua em RAM.

### Consequência na lista vertical

O mapeamento ficou **invertido em relação à física**: os botões que são
literalmente cima e baixo (`M`, `VOL`) são os que pulam 3 linhas, e os
que são esquerda e direita andam 1.

### O patch que corrige — e por que ele NÃO depende de saber quem é quem

Converter os dois ramos de ±3 em ±1 **preserva a direção de cada botão** e
muda só o passo. Quem subia 3 passa a subir 1; quem descia 3 passa a
descer 1. Portanto **não é preciso determinar qual botão é `0xA0` e qual é
`0x81`** — a ambiguidade que resta não afeta o resultado.

```text
ramo -3  (0x00D2EA3A)
  0x0012EA3E   cmp   r2, #2    ->  cmp   r2, #0     02 -> 00
  0x0012EA42   subhi r2, #3    ->  subhi r2, #1     03 -> 01
  0x0012EA44   addls r2, #6    ->  addls r2, #8     06 -> 08

ramo +3  (0x00D2EB26)
  0x0012EB2A   adds r1, r2, #3 ->  adds r1, r2, #1  D1 -> 51
  0x0012EB70   subs r2, #6     ->  subs r2, #8      06 -> 08
```

**5 bytes, todos imediatos de 1 byte.** Nenhum alvo de salto se move,
nenhum tamanho de instrução muda.

**Verificação de alcance feita antes de propor:** `0x00D2EB70` (o ajuste
de volta do `+3`) é alcançado **por um único salto**, o `bhi` em
`0x00D2EB30` do próprio ramo. Não é compartilhado. E `0x00D2EA4E`
(`movs r2, #8`), que poderia parecer parte do ramo `−3`, na verdade
pertence ao ramo `−1` — só é alcançado de `0x00D2E9E4`. Com os novos
valores o índice fica sempre em 0..8, então o `bls` do `−3` é sempre
tomado e aquele caminho continua inalcançável a partir dali.

Depois disso, os quatro botões da roda navegam de 1 em 1: `M`/`VOL` como
cima/baixo e `|<<`/`>>|` como equivalentes. Redundante, mas é o
comportamento natural de um player com roda — e `▶Ⅱ` já entra.

### ✅ V015 confirmado no aparelho (2026-09-12)

Gravado e testado pelo mantenedor. Os quatro botões da roda andam de 1 em
1, as voltas nas pontas funcionam nos dois sentidos (Música ↔ Ver pastas)
e `▶Ⅱ` continua entrando.

| Previsto | Observado | Classe |
|---|---|---|
| `M` e `VOL` passam a andar 1 linha, mantendo a direção | ✅ | **CONFIRMADO** |
| `\|<<` e `>>\|` seguem andando 1 | ✅ | **CONFIRMADO** |
| volta 0 → 8 e 8 → 0 nos dois ramos | ✅ | **CONFIRMADO** |
| nenhuma mudança visual | ✅ | **CONFIRMADO** |

> A aposta de método deu certo: a conversão foi desenhada para **preservar
> a direção de cada botão**, o que tornou desnecessário saber qual deles
> emite `0xA0` e qual emite `0x81`. A ambiguidade continua registrada como
> PROVÁVEL — e continua sem custo. **Quando dá para tornar uma incógnita
> irrelevante, isso vale mais do que resolvê-la.**

---

# 7. Os códigos de tecla que chegam na tela — CONFIRMADO

> Levantado em 2026-09-13. As seções anteriores paravam no `watch_key` e
> diziam *"nenhum handler de tecla foi desmontado"*. Isto desmonta a
> ponta final: o que a **tela ativa** recebe e o que ela faz.

## 7.1 Onde a tela recebe a tecla

Cada `page_*_create` registra um callback de evento da LVGL:

```asm
0x00D3A7F8   ldr  r1, =0x00D3A429     ; o callback
0x00D3A7F4   movs r2, #0xd            ; LV_EVENT_KEY = 13
0x00D3A7FC   bl   0xd47064            ; lv_obj_add_event_cb
```

**49 telas** registram callback de `LV_EVENT_KEY`. Os três que
interessam:

```text
pagina 0x01  home         cb 0x00D2E950   page_home_event_cb
pagina 0x53  Extras       cb 0x00D2EF5C   page_home_menu_event_cb
pagina 0x28  Configurar   cb 0x00D3A428   page_set_menu_event_cb
```

O callback lê a tecla com `0xD47038` e despacha por `cmp r2, #codigo`.
**Cada ramo carrega uma string de depuração com o próprio nome**
(`"-%s right"`, `"-%s enter"`, `"-%s back"`, `"-%s esc"`), o que torna a
leitura direta, sem adivinhação.

## 7.2 Os códigos são `LV_KEY_*` da LVGL v8 — CONFIRMADO

```text
0x0A  ENTER      0x12  DOWN       0x1B  ESC
0x09  NEXT       0x13  RIGHT
0x0B  PREV       0x14  LEFT
0x11  UP
```

Os códigos com bit alto (`0x81 0x87 0x8A 0x92 0x98 0x9B 0xA0`) são
variantes próprias do firmware. As strings `-%s LV_KEY_LP_ENTER` e
`-%s LV_KEY_LR_ENTER` (`0x000D5575`, `0x000D558C`) mostram que existem
variantes de *long press* e *long release*, mas **o mapeamento
bit-alto → gesto NÃO está determinado** e não deve ser suposto.

## 7.3 A divergência, medida

| tecla | home | Extras / Configurar |
|---|---|---|
| `0x13`, `0x8A` | move | `lv_group_focus_next` (`0xD474C4`) |
| `0x14` | move | `lv_group_focus_prev` (`0xD474DC`) |
| `0x11`, `0x12`, `0x87`, `0x98`, `0x9B` | **não tratadas** | movem |
| `0x09`, `0x0B` | movem | **não tratadas** |
| `0x0A` | entra | entra |
| **`0x81`** | **move** (`"-%s right"`) | **SAI DA TELA** (`"-%s back"`) |
| **`0xA0`** | **move** | **não tratada** — cai em `"no c: %d"` |
| `0x1B` ESC | sai | **`pop {r4,r5,r6,pc}` — não faz nada** |
| `0x92` | grava | não tratada |

O ramo `0x81` do Extras, desmontado:

```asm
00D2F05E   ldr  r3, =0x00823D84
00D2F062   strb r2, [r3]         ; zera o estado
00D2F066   movs r3, #0x14
00D2F068   movs r0, #0x53        ; pagina de origem
           -> transicao de pagina, volta para a home
```

### Censo nas 49 telas com callback de tecla

```text
0x81 -> navegacao     1 tela   (a home)
0x81 -> "back"       22 telas  (inclui 0x28 Configurar, 0x53 Extras,
                                0x22 Pastas, 0x04 Now Playing)
0x81 -> outro        22 telas  <- NAO CLASSIFICADO com confianca;
                                  o extrator pegou a string de erro.
                                  Reconferir antes de usar este numero.
```

## 7.4 ⚠️ A pergunta que trava o conserto

`patch_home_keys.py` registrou que `0x81` e `0xA0` são **M e VOL**, em
ordem desconhecida — e conseguiu contornar a ambiguidade porque
**preservava a direção** de cada tecla. **Aqui não dá para contornar:**
o conserto muda conforme a resposta.

| se `0x81` for… | então |
|---|---|
| **o M** | `"back"` está **certo** — M = Menu = voltar, como no nano. O defeito é só o `0xA0` (VOL) não fazer nada. Conserto pequeno: mapear `0xA0` para `focus_next`/`prev`. |
| **o VOL** | o VOL sai da tela, o que é o defeito. Mas remapear **prende o usuário**: com o ESC morto, `0x81` pode ser a única saída daquelas 22 telas. Exige arranjar a saída **antes**. |

> **Não deduzir.** É exatamente o padrão que custou V016, V027, V031 e a
> barra de rolagem: corrigir uma dimensão e não reexaminar a outra.
>
> **O teste, no aparelho, leva cinco segundos:** abrir o **Extras**,
> apertar **M**, apertar **VOL**. Qual dos dois volta para a home? O
> outro faz alguma coisa?

## 7.5 Classificação

| Afirmação | Classe |
|---|---|
| 49 telas registram callback de `LV_EVENT_KEY` | **CONFIRMADO** (varredura de `0xD47064` com `r2=13`) |
| Os códigos baixos são `LV_KEY_*` da LVGL v8 | **CONFIRMADO** (batem um a um com o enum) |
| `0x81` = `"back"` no Extras e no Configurar | **CONFIRMADO** (disassembly + string de depuração) |
| `0x81` = navegação na home | **CONFIRMADO** |
| `0xA0` não é tratada no Extras/Configurar | **CONFIRMADO** |
| ESC não faz nada no Extras | **CONFIRMADO** (`0xD2F01A` é `pop`) |
| 22 telas tratam `0x81` como "back" | **PROVÁVEL** — varredura automática, amostra conferida à mão só no Extras e no Configurar |
| Os outros 22 casos | **NÃO DETERMINADO** |
| Qual botão físico emite `0x81` | **NÃO DETERMINADO** — e é o que trava tudo |

---

# 8. A lacuna fechada, e o conserto — V056 / OpenPod 1.7

## 8.1 A resposta, do aparelho

Relato do mantenedor em 2026-09-13, com o Extras na tela:

> *"M nao faz nada!! e o VOL VOLTA. Os botoes voltar e proxima navega no
> menu e o play/pause entra na opcao"*

```text
0x81 = VOL          0xA0 = M
```

**A ambiguidade da §5 e da §7.4 está fechada.** Custou uma pergunta e
cinco segundos, depois de a análise estática ter levado o problema até a
porta dela.

> Vale registrar o método: a análise estática determinou **tudo** —
> quais telas, quais códigos, quais ramos, o que cada ramo faz — e
> isolou **uma** pergunta binária que ela não podia responder. Não foi
> preciso desmontar a cadeia de entrada inteira.

## 8.2 O ponto único

Toda tecla de toda tela passa por um lugar só — o `lv_group_send_data`
da LVGL, o **único** ponto do firmware que envia `LV_EVENT_KEY`:

```asm
00D47652   push {r0, r1, r2, lr}    ; r0 = grupo, r1 = A TECLA
00D47654   str  r1, [sp, #4]        ; o slot que sera enviado
00D47656   bl   0xd47648            ; objeto focado
00D4765C   add  r2, sp, #4          ; &tecla
00D4765E   movs r1, #0xd            ; LV_EVENT_KEY
00D47660   bl   0xd46ff0            ; lv_event_send(obj, KEY, &tecla)
```

Seis bytes em `0x00D47654` viram `bl <rotina>` + `nop`. A rotina traduz a
tecla **antes** de qualquer callback vê-la, e decide **por página**.

**Isso transformou 21 patches em 1.**

### O detalhe que faz funcionar sem mexer na pilha

`bl` não altera `sp`, e a rotina **não chama ninguém** — então `lr`
sobrevive sozinho e não precisa ser empilhado. Ela empilha só
`{r0, r2, r3}` (o `r0` é o grupo, usado como rascunho na busca), desempilha,
escreve `[sp, #4]` — que a essa altura é de novo o slot do chamador — e
faz **tail call** para `0xd47648`, que é folha (`bx lr`). O retorno cai
no `nop` e a função original continua como se nada tivesse acontecido.

## 8.3 O que a rotina faz

```text
se a pagina corrente esta na tabela:
    0x81 (VOL)  ->  0x12   LV_KEY_DOWN
    0xA0 (M)    ->  0x81   o codigo que a tela trata como "back"
```

**Nenhum comportamento novo foi criado.** As telas já tratam `0x12` como
"próximo" e `0x81` como "voltar"; o patch só escolhe qual botão aciona
qual. A home não está na tabela e não muda em nada.

## 8.4 As 21 páginas não foram escolhidas a dedo

Uma página só entra se as **três** condições valerem, cada uma verificada
**simulando a cadeia de comparações** do callback daquela tela:

```text
1. 0x12 chega num ramo que chama lv_group_focus_next (0xD474C4)
2. 0x81 chega num ramo rotulado "-%s back"
3. 0xA0 hoje cai no ramo de erro ("-%s no c: %d") — nao esta em uso
```

```text
0x02 0x09 0x0B 0x0E 0x10 0x17 0x18 0x1E 0x20 0x23 0x28
0x29 0x2A 0x2E 0x30 0x3C 0x4B 0x4C 0x4D 0x50 0x53
```

`tools/patch_navegacao.py` **refaz essa verificação na imagem de entrada
a cada execução** e recusa se uma só página deixar de qualificar.

**28 páginas ficaram de fora**, e o motivo importa: elas não tratam
`0x12` como "próximo". Remapear o VOL nelas o deixaria **morto** — pior
que hoje. Fora, notavelmente: `0x04` (Now Playing), `0x1A` (FM) e os
seletores de hora.

> Foi exatamente aqui que o hábito de *"enumerar todos os pontos"* pagou:
> a versão ingênua do patch aplicaria o remap em tudo que tratasse `0x81`
> como "back" — **22 telas** — e teria quebrado o botão de voltar do Now
> Playing.

## 8.5 Dois erros do próprio detector, e o que ensinam

O primeiro censo aprovou **5** páginas; o correto era 21. Duas falhas
minhas, ambas no analisador, nenhuma no firmware:

1. **Parar no `pop`.** O ramo termina em `pop.w {...,lr}` seguido de
   `b.w <alvo>` — *tail call*. Quem para no `pop` perde justamente o
   alvo.
2. **Andar de 2 em 2 bytes.** `pop.w` tem 4. O passo fixo caía no meio da
   instrução e o `b.w` seguinte nunca era visto.

> **Lição:** uma ferramenta de análise errada não dá erro — dá uma
> resposta plausível e menor. O que salvou foi ter um **caso conhecido**
> (o Extras, já lido à mão) para validar o simulador antes de confiar
> nele. Todo analisador novo precisa de um caso assim.

## 8.6 O que este patch NÃO conserta

- **O ESC (`0x1B`) continua morto** nas subtelas (`pop` puro). Não foi
  tocado.
- O mapeamento **bit alto → gesto** (press / long press / long release)
  continua **NÃO DETERMINADO**. Este patch trata `0x81` e `0xA0` como os
  códigos que o aparelho comprovadamente emite para VOL e M — nada além
  disso.
- As 28 páginas fora da tabela continuam com VOL = voltar e M morto.

---

# 9. ⚠️ V057 / OpenPod 1.8 — a navegação foi REVERTIDA, e o porquê importa

Depois de usar a 1.7 no aparelho, o mantenedor concluiu:

> *"o padrão seria melhor o M não fazer nada, o VOL voltar, e os botões
> frente e trás andar nos menus e o play/pause entrar (…) confere se esse
> é o padrão do produto"*

**Conferi no `GN438_original.bin`, e ele está certo.** Nas 49 telas que
tratam tecla no firmware de fábrica:

| papel | M (`0xA0`) | VOL (`0x81`) |
|---|---|---|
| sem função | **41** | 7 |
| "voltar" | 0 | **41** |
| outra coisa | 7 | 1 |

```text
M   -> usado so em 7 telas: a home (navega), 3x esc, 2x desce,
       1 mensagem de depuracao
VOL -> "voltar" em 41 telas; navega so na home
```

**`VOL = voltar` e `M = sem função` são o padrão do produto**, com
41 de 49 telas cada. Não é tela esquecida nem acidente: é o desenho.

## 9.1 O erro de raciocínio que produziu a 1.7

Eu tratei *"o M não faz nada"* como **defeito a corrigir**, e ele era
**especificação**. O argumento que usei — *"M tem nome de Menu, e no iPod
o Menu volta"* — é **analogia com outro aparelho**, não evidência deste.

A verificação que faltou era barata e do mesmo tipo que o projeto já faz
o tempo todo: **contar, no firmware de fábrica, o que cada tecla faz em
todas as telas.** Se eu tivesse feito esse censo antes de propor, teria
visto 41×41 e não teria proposto.

> **Regra derivada:** antes de chamar um comportamento de defeito,
> **medir a frequência dele no firmware de fábrica**. Comportamento que
> se repete em 41 de 49 telas é decisão de produto. Um que aparece em 1
> tela é que é candidato a defeito.
>
> É primo da lição da §8.4 (*"enumerar todos os pontos"*), mas apontada
> para outro lado: lá, enumerar evitou **quebrar** telas; aqui, enumerar
> teria evitado **consertar o que não estava quebrado**.

## 9.2 O que a 1.7 deixou de bom

O trabalho não foi perdido — o **mapa** continua valendo, e ele é que
custou caro:

- `0x81` = VOL e `0xA0` = M: **CONFIRMADO**, a lacuna da §5 segue fechada;
- `0x00D47654` é um **ponto único** por onde passa toda tecla de toda
  tela — vale para qualquer mudança futura de mapeamento;
- o simulador de despacho (`tools/patch_navegacao.py`) responde
  *"o que a tecla X faz na tela Y?"* para qualquer X e Y.

A ferramenta fica no repositório, **desaplicada**. Quem quiser reaplicar
tem 6 bytes e uma tabela.

## 9.3 A reversão é limpa — e isso foi provado, não suposto

```text
0x00147654   6 B  bl 0x00DA50C0 ; nop  ->  str r1,[sp,#4] ; bl 0xd47648
0x001A50C0  832 B  rotina + tabela     ->  0xFF
```

A imagem revertida bate **byte a byte** com a V055, que nunca teve o
patch. O patch era autocontido.

### Ordem de gravação (R2), invertida em relação ao normal

```text
0x147000   o gancho     <- PRIMEIRO: desativa
0x10A000   o carimbo
0x1A5000   a rotina     <- por ultimo: so entao pode ser apagada
```

**Ao remover, a desativação vem primeiro.** Apagar a rotina antes de tirar
o gancho deixaria um estado intermediário em que a primeira tecla
pressionada saltaria para uma região de `0xFF`. É a mesma regra R2 de
sempre, lida ao contrário.

## 9.4 O que continua em aberto

A queixa original do `ROADMAP_1.1.md` §2 — *"a navegação é diferente
entre a home e as outras"* — **continua verdadeira**, e agora sabemos que
é assim de fábrica:

```text
home       M e VOL navegam        (heranca da grade 3x3, onde pulavam 3)
subtelas   M morto, VOL volta
```

O mesmo botão (VOL) navega numa tela e volta na outra. Alinhar isso
exigiria mexer na **home**, não nas subtelas — e aí tiraria dela dois
botões que hoje funcionam. **Decisão do mantenedor, não minha.**
