# Ficha 024 — análise: Cobrinha absoluta (Parte A) e a capa numa tarefa própria (Parte B)

Data: 2026-11-18. Base: `privado-completo` (Reload 3.1c). Branch:
`limtistech/tarefa-024`.

Resultado: **Parte A entregue**; **Parte B em `ESCALADA-024`**. A Parte B não
foi implementada porque o único caminho que fecha as nove regras exige uma
decisão de arquitetura (consumir uma fila da fábrica e marcar os pedaços da
capa), e a ficha manda escalar quando não há lugar seguro provado. As opções
estão no fim.

---

## Parte A — o que mudou

Arquivo: `sdk/apps/cobrinha/main.c`.

- `turn()` relativo virou `turn_abs(g, d)`, com as direções absolutas do
  campo: `0` direita, `1` baixo, `2` esquerda, `3` cima (`dx[]`/`dy[]`).
  A meia-volta direta `(dir + 2) & 3` é ignorada, como no celular.
- Mapa dos botões em `input_cb`:
  - `FW_KEY_PREV` `0x14` e `FW_KEY_PREV_LONG` `0x87` → `turn_abs(g, 2)`
    (esquerda);
  - `FW_KEY_NEXT` `0x13` e `FW_KEY_NEXT_LONG` `0x89` → `turn_abs(g, 0)`
    (direita);
  - `FW_KEY_M` `0xA0` → `turn_abs(g, 3)` (cima);
  - `FW_KEY_M_LONG` `0xA2` → `toggle_pause(g)`;
  - `FW_KEY_PLAY` `0x0A` → `play_key(g)`; na tela inicial começa, no fim de
    jogo recomeça e, em jogo, desce (`turn_abs(g, 1)`);
  - `FW_KEY_BACK` `0x81` 2× em 800 ms continua saindo.
- `play_action()` foi dividido em `play_key()` (Play/PRESSED) e
  `toggle_pause()` (M longo). O `LV_EVENT_PRESSED` do Play/Enter chama
  `play_key()`, não pausa: antes ele usava `press_handled` para o Play
  pausar; agora o mesmo evento só inicia/recomeça/desce.
- A caixa de mensagem passou a `MSG_H` 112 (era 66) e o texto para `y=22`;
  a ajuda tem seis linhas nos dois idiomas:
  - PT: `Play: baixo`, `M: cima`, `<<: esquerda`, `>>: direita`,
    `Segure M: pausa`, `VOL 2x: sair`;
  - EN: `Play: down`, `M: up`, `<<: left`, `>>: right`,
    `Hold M: pause`, `VOL 2x: exit`.
- A mensagem de pausa virou `Segure M: continuar` / `Hold M: resume`.

Build e testes:

- SDK jogos: 11.868 B em `0x00DAB000`, gancho `0x00DAD23C`, sha
  `58611dd86c3878a7…`, reproduzível (`--check-repro`).
- Receita `reload_3.2` = `reload_3.0` + `fab_sdk_jogos.py --variante jogos`
  (a mesma cadeia da 3.1c; só o fonte do SDK muda).
- `tests/test_reload_3_2.py` (6 testes) cobre reprodutibilidade, ausência de
  `.data`/`.bss`, bit Thumb, receita, mapa absoluto na fonte, ajuda bilíngue
  e o diff contra a 3.0 e a 3.1c publicada. Passa.
- `sh tools/ci.sh` verde.

---

## Parte B — provas no ORIGINAL

### Regra 1 — criar e terminar a tarefa

`fw_task_create` em `0xCF7AD4`:

- `push {r0-r8, lr}`; `r0` = entrada, `r1` = argumento, `r2` = nome,
  `r3` = prioridade; o quinto argumento (pilha) está em `[sp, #0x28]` depois
  do push. Aloca `0x18` B em `0xCF780C` e zera com `0xBAA`.
- TCB medido: `[0]` = entrada, `[4]` = argumento, `[8]` = id de thread,
  `[0xC]` = `exitSem`, `[0x14]` = `joinSem`. Cria os dois semáforos em
  `0xCF790E` e chama `os_thread_create` `0x8A30` com o wrapper
  `0xCF79D3`.
- O wrapper faz `entrada(arg)`, dá `exitSem` (`0xCF799E`), chama
  `0xA738(0)` e entra num laço `sleep(60000)` (`0xCF78E4`) que **nunca
  retorna**.
- `fw_task_join` `0xCF7B90` dá `joinSem`, espera `exitSem` (`0xCF7996`),
  apaga os dois semáforos, chama `0x8BF4(id)` e `free(TCB)`. Ele **bloqueia**
  até a entrada retornar. `fw_task_delete` `0xCF7BDC` é parecido, mas sem
  esperar; auto-delete não é seguro.

Conclusão: uma tarefa por pedido só termina limpa se **outra** tarefa
chamar `join` e esperar; a PreTask não pode esperar, e a ViewTask não pode
esperar (regra 8). Sem joiner, cada pedido vaza TCB + dois semáforos +
pilha. A alternativa da ficha — **uma tarefa só, criada uma vez** — é a
única que não vaza.

### Regra 2 — prioridade abaixo da PreTask e da MediaTask

- PreTask: config em `0xCF812C`, prioridade `3` em `[sp, #0x20]`, pilha
  `0x800` em `[sp, #0x24]`, handler `0xCF8101`, fila `MgrTaskQue`.
- MediaTask: config em `0xD40354`, prioridade `3`, pilha `0x800`, handler
  `0xD4027D`, fila `MediaTaskQue`.
- Neste RTOS o número menor é mais prioritário (ViewTask 0, MainTask 1,
  PreTask 3). Uma tarefa de capa em prioridade **6** (a mesma do `video`,
  criado em `0xD127F8`) fica abaixo das duas. Prioridade 6 é aceita pela
  API; 4 e 5 não foram vistos, então 6 é a escolha com prova.

### Regra 3 — pilha

`carrega_capa` mediu **352 B** de pico na PreTask (ficha 014). A ficha pede
≥ 2 KiB; `0x800` = 2048 B é o valor de fábrica da PreTask e da MediaTask.
A medição do novo frame (wrapper + laço + hash + envio) no emulador ainda
não foi feita porque a tarefa não foi implementada. Se implementar, medir
com pilha pintada; 2 KiB é o piso, não uma estimativa.

### Regra 4 — buffer de mensagem próprio

O buffer global `0x8238F1` é da PreTask (cabeçalho de 0x14 B + 0x400 B de
payload) e é reutilizado a cada mensagem; duas tarefas montando ao mesmo
tempo corrompem. A tarefa da capa deve alocar **0x414 B** próprios e chamar:

- `0xD0D818(msg)`: lê o comprimento em `msg+0xA`, o tipo em `msg+4` e passa
  a mensagem para `0xCF83E4`;
- `0xD0D880(msg)` depois do último envio, como a fábrica.

O `calloc`/`free` da camada de SO (`0xCF780C`/`0xCF7884`) atende; o buffer
vive no contexto da tarefa e é liberado em todos os caminhos.

### Regra 5 — pedido copiado

O caminho tem de ir copiado para o contexto/fila da tarefa. O B6b já copia
para `tmp+0x110` antes de decodificar e libera `tmp`; um ponteiro para o
buffer da rajada fica pendurado. Se usar fila da fábrica, o item da fila
precisa de pelo menos `0x100` B para o caminho (o B6b usa 256 B), ou o
pedido leva um bloco de heap com dono definido.

### Regra 6 — troca rápida de faixa

O cabeçalho da mensagem tem um campo de 4 B em `msg+8` que o B6b zera e que
o caminho de envio **não lê**: `0xD0D818` só lê `+0xA` (comprimento); o
tratador tipo 6 lê `+0x10` (offset do pedaço) e `+0x14` (payload). O tipo 5
também só usa o payload `+0x14`.

Desenho que fecha a regra sem estado global:

1. O pedido leva um **resumo do caminho** (hash de 32 bits) em `msg+8`.
2. A tarefa decodifica; antes de cada um dos 8 pedaços, drena a fila sem
   bloquear. Se chegou pedido novo, abandona o antigo e decodifica o novo.
3. A view só aplica o tipo 6 se o hash de `msg+8` for igual ao hash do
   caminho atual em `ext+0x110`. Pedaço velho é descartado, mesmo que chegue
   depois da troca.
4. O 1500 px / 512 KiB → cinza continua no `carrega_capa`; nada de estado
   global para isso.

O ponto 3 exige patch no tratador tipo 6 da view (ou no blob B7b, se o
tratador estiver lá) e a prova de que ele ignora `msg+8`. É a parte que
ainda não foi implementada.

### Regra 7 — estado global

**Não é preciso um global novo** se o registro for a tabela de tarefas da
fábrica:

- Tabela em `0x0081D68C`, 15 entradas de `0x58` B; o id da fila fica em
  `[tarefa+0x54]`. `0xD6AE38` devolve a tarefa pelo id; a fila fica em
  `[tarefa+0x28]`.
- A PreTask recebe em `0xCF8101` com `0xD7DADE(&tarefa[0x28], &msg, -1)`;
  o envio equivalente é `0xD7DAFE(&tarefa[0x28], &msg, timeout)`.
- Os nove `0xD6ACAC` de fábrica usam os ids **1, 2, 3, 4, 5, 8, 9, 0xA,
  0xB**. Ficam livres **6, 7, 0xC, 0xD, 0xE** (0 é o “sem fila”). Todas as
  tarefas de fábrica nascem no boot; uma varredura da tabela no primeiro
  pedido prova o id livre em tempo de execução, e a criação é feita uma vez
  pela PreTask (serial).
- O handle da tarefa é a própria entrada da tabela; o número do pedido é o
  hash do caminho na mensagem; o estado da tarefa (último pedido, contexto
  de decode) fica no stack/heap dela. Nada de XIP como variável e nada de
  RAM “que parece livre”.

Isso é um lugar **seguro por construção**, mas consome um id de fila e
acrescenta uma tarefa à tabela da fábrica. É uma decisão de arquitetura,
não uma escolha do desenvolvedor; por isso a ficha vai para `ESCALADA-024`
em vez de implementar sem aprovação. A varredura de todos os escritores da
tabela e o teste do id em runtime ainda precisam entrar no pacote.

### Regra 8 — ViewTask e LVGL

A tarefa da capa não chama LVGL: só `carrega_capa` e `0xD0D818`. A ViewTask
continua só copiando bytes nos tipos 5/6 e chamando `img_set_src`; não abre
arquivo nem espera (o `0xD7DADE` dela já é a espera normal da fila de
mensagens). Se a tarefa for criada, `join`/`delete` ficam fora da view.

### Regra 9 — limites e falhas

O decode continua sendo `carrega_capa` `0xDAA256` com os limites da 2.2.1
(1000 px, 512 KiB → cinza; falha → cinza). O contexto de `0x2210` B é
liberado e o arquivo fechado em todos os caminhos, como no B6b. Não duplicar
a rotina de limite nem o `carrega_capa`.

---

## Opções para o decisor (ESCALADA-024)

1. **Aprovar a tabela da fábrica (recomendada).** Consumir um id livre
   (6/7/0xC/0xD/0xE), criar a tarefa uma vez pela PreTask via `0xD6ACAC`,
   enviar o pedido por `0xD7DAFE` e marcar os pedaços com o hash em `msg+8`.
   Falta: patch do tratador tipo 6, prova de que ele ignora `+8`, medição de
   pilha e teste no emulador. Não usa RAM nova nem XIP variável.
2. **Reservar 4 B de RAM com prova.** Um slot fixo para o handle/contador,
   escolhido com mapa de RAM/dump e travado por teste. Exige o arquiteto
   indicar o endereço; “parece livre” não vale.
3. **Fazer o decode em pedaços na própria PreTask.** Sem tarefa nova e sem
   global: `envia_path` faz um pedaço por chamada e guarda o estado no
   contexto do pedido. É a opção de menor risco de tarefa, mas exige fatiar
   `carrega_capa`/o envio e medir o pico; alto risco de regressão no áudio.
4. **Entregar só a Parte A.** É o que este pacote faz: a Cobrinha fica com
   os controles novos e a capa continua como na 3.1c (já aprovada no
   aparelho). Um kit 3.2 só com a Parte A pode ser gerado se o decisor
   quiser; a Parte B vira uma ficha própria.

## O que não foi feito

- Kit/release 3.2: não gerado (Parte B em escalada; o processo deixa kit e
  publicação para a coordenação).
- Parte B: nenhuma linha de firmware mudou no caminho da capa.
- Medição da pilha da tarefa nova no emulador: depende da implementação.
- `tests/test_reload_3_1c.py` continua afirmando as strings antigas da
  Cobrinha e falharia se rodado depois desta mudança; ele não está em
  `tools/ci.sh` nem em `tests/PROTEGIDOS.sha256`. Não foi alterado. O teste
  novo é `tests/test_reload_3_2.py`.
