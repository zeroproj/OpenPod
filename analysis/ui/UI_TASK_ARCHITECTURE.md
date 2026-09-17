# Arquitetura da UI — ViewTask / MgrTask / navegação

> Análise aprofundada do firmware GN-438 (yp3_2.0.43).
> Descoberta: a navegação de telas é feita pela **ViewTask** (task id 3),
> não pela MgrTask. A MgrTask (id 9) cuida de USB/PMU/timers.

---

## 1. Visão geral das tasks identificadas

| Task | ID | Nome da fila | Função principal | Responsabilidade |
|---|---|---|---|---|
| **MainTask** | 1 | MainTaskQue | `0x00CF7DF1` | Inicialização, watchdog, estado global |
| **TransmitTask** | 2 | TransmitTaskQue | `0x00D40451` | Comunicação entre CPU/coprocessadores |
| **ViewTask** | 3 | *(usa fila da task 3)* | `0x00CF8210` | **Navegação de telas, eventos LVGL, UI** |
| **MgrTask** | 9 | MgrTaskQue | `0x00D3FF8C` | USB, PMU, timers, estados de energia |
| **MediaTask** | 8 | MediaTaskQue | `0x00D4027D` | Áudio/vídeo/rádio |
| **Master_CPU_Recv_Task** | 5 | — | `0x00D40171` | Recepção de comandos externos |
| **PreTask** | 11 | MgrTaskQue | `0x00CF8101` | Pré-inicialização, volume, configs |

A tabela de tasks está em RAM em `0x0081D68C`, com entradas de `0x58` bytes
(15 entradas). A função `0x00D6AE38` recebe um id e retorna o ponteiro
para a entrada correspondente.

---

## 2. ViewTask — a task de UI

### 2.1 Criação

Localizada em `0x00CF8210`:

```text
watch_view_task init:
  task_id = 3
  get_task_by_id(3) -> ViewTask entry
  malloc view ring buffer -> 0x0081BBC0 + 0x8
  init pages (0x00D4053C)
  while (1):
      msg = queue_receive(ViewTask.queue, buf, -1)
      parse_msg(buf)
      view_process()
      register_manager()
```

### 2.2 Loop principal (`0x00CF8274`)

```text
00CF8274  queue_receive(ViewTask.queue, sp+0x14, -1)  ; 0x80D81E
00CF827E  r6 = result
00CF8282  if (r6 != 0):
          parse_message(ViewTask.queue, sp+0x14)      ; 0x80DA06
00CF828A  view_process()                              ; 0xCFE708
00CF828E  if (ret != 0):
          sleep/wfi
00CF82A4  register_manager(ViewTask.entry)            ; 0xD46BBC
00CF82A8  loop
```

### 2.3 Mapeamento da mensagem recebida

O buffer de mensagem tem pelo menos:

| Offset | Campo | Tamanho | Observação |
|---|---|---|---|
| `+0x00` | `src` | byte | origem da mensagem |
| `+0x01` | `dir` | byte | direção |
| `+0x02` | `cmd` | byte | comando principal |
| `+0x03` | `sub_cmd` | byte | sub-comando |
| `+0x04` | `len` | halfword | tamanho do payload |
| `+0x08` | `payload` | variável | dados adicionais |

Formato observado no debug string:

```text
-src = 0x%02x, dir = 0x%02x, len = %d
cmd = 0x%02x, sub_cmd = 0x%02x, payload : 
```

---

## 3. Envio de mensagens para a ViewTask

### 3.1 Função de post (`0x00D234AC`)

Recebe um ponteiro para mensagem, empacota com header interno
(`0x06060B03` + length) e chama a função de post da fila
(`0x0080D91C`).

### 3.2 Função de conveniência (`0x00D23510`)

Monta uma mensagem de 0x1C bytes na stack a partir de 4 argumentos:

```text
r0 -> offset +0x00 (halfword)
r1 -> offset +0x02 (halfword)
r2 -> offset +0x04 (halfword)
r3 -> offset +0x0C (halfword)
```

Campos fixos:

```text
+0x06 = 1
+0x0A = 2
```

Exemplo no callback do menu home (`0x00D2F540`):

```text
item clicado -> envia(7, 4, i, 4)
```

Onde `i` é o índice do item (0..5). A mensagem resultante tem:

```text
src = 7, dir = 4, cmd = i, sub_cmd = 4
```

> **Nota:** a documentação anterior (`docs/GUI_ANALYSIS.md` §25.3) listava
> a ordem como `msg(7, 4, 4, i)`. O disassembly mostra que o índice `i`
> vai para o campo `cmd` (offset +0x02) e o valor `4` vai para
> `sub_cmd` (offset +0x03). A convenção exata ainda está sendo
> confirmada por mais callbacks.

---

## 4. MgrTask — não é a task de UI

A `MgrTask` (id 9) cuida de eventos de hardware:

- USB in/out (estados do `/dev/usbd`)
- PMU / VBUS
- Card reader
- Timers de sistema

Seu dispatcher (`0x00D460F4`) usa `tbh` para escolher o handler com
base no estado atual (`0x0081D110`). Não é responsável pela navegação
entre páginas de menu.

---

## 5. Implicações para o OpenPod

1. **Para mudar a navegação de telas**, devemos estudar a `ViewTask`
   (`0x00CFE708`) e a tabela de páginas, não a `MgrTask`.

2. **Para adicionar uma página nova**, precisamos:
   - Criar o construtor `page_nova_create`.
   - Registrá-lo na tabela de páginas consultada pela `ViewTask`.
   - Garantir que o callback do menu envie a mensagem correta.

3. **Mudanças visuais simples** (ícones, cores, textos) continuam sendo
   os patches de menor risco.

---

## 6. Endereços chave

| Símbolo | Endereço |
|---|---|
| `get_task_by_id` | `0x00D6AE38` |
| Tabela de tasks | `0x0081D68C` |
| ViewTask entry -> queue handle | `entry + 0x08` |
| ViewTask main | `0x00CF8210` |
| ViewTask process | `0x00CFE708` |
| ViewTask queue receive | `0x0080D81E` |
| ViewTask parse msg | `0x0080DA06` |
| Post message | `0x00D234AC` |
| Build/send message | `0x00D23510` |
| `page_home_menu_event_cb` | `0x00D2F540` |
| MgrTask main | `0x00D3FF8C` |
| MgrTask dispatcher (USB/PMU) | `0x00D460F4` |

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| Existe uma task dedicada à UI (ViewTask, id 3) | **CONFIRMADO** |
| Mensagens de navegação vão para a ViewTask | **CONFIRMADO** |
| MgrTask lida com USB/PMU/timers, não UI | **CONFIRMADO** |
| Layout exato dos campos da mensagem de navegação | **PROVÁVEL** |
| Tabela de registro de páginas na ViewTask | **HIPÓTESE** |

---

*Última atualização: 2026-09-16*
