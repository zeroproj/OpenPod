# Ficha 011 — Análise estática: o `get_path` na ViewTask, o refresh e o caminho sem o banco

Base: `firmware/ORIGINAL/GN438_original.bin` (`b7cd5eb9…`) + a RC7
(`3af97713…`). Só leitura; cada afirmação leva **CONFIRMADO / PROVÁVEL /
HIPÓTESE** com o endereço e a instrução. O que já estava na 009/010 vale
pela **Conferência da coordenação** (009 C1–C5, 010 D1–D5).

## 1a. De onde vem o comando de timer da MainTask

**CONFIRMADO — é o timer da própria MainTask, não a ViewTask.** O
descritor em `0xCF8030` cria a MainTask (`0xCF8078`, pilha `0x400` em
`sp+0x24`) com o timer `"MainTaskTimer"` (`0xCF8050`, literal `0xC49612`) e
a fila `"MainTaskQue"` (`0xCF8044`). O laço dela espera o comando em
`0xCF7EC0` (`bl 0xD7DADE`, timeout `-1`) e, no comando de timer, chama o
monitor:

```
00CF7FBE  bl 0xD46B14   ; comando de timer -> monitor -> refresh do watchdog
```

O timer é um **software timer** (`os_timer`, `0xD45CB8`/`0xD6AE38`), criado
na inicialização do app; ele roda no **timer task** do RTOS, não no laço do
LVGL nem na ViewTask. A origem **não depende** da ViewTask: se a MainTask
estiver viva, ela recebe o comando; se não recebe, é porque **parou** (ou o
timer task parou, o que a 009 não vê). O B2 (teste de tarefa morta
neutralizado) ainda reinicia, então o que para é a **MainTask**, não a
checagem da ViewTask (010 D5).

## 1b. Prioridades: a premissa da ficha está trocada

**CONFIRMADO — o campo da prioridade é `desc+0x20`, não `desc+0x54`.** O
registro da tarefa (`0xD6ACAC`) lê `[r4+0x24]` (pilha) e
`ldrb r3,[r4,#0x20]` (prioridade) e repassa os dois a `0xCF7AD4` →
`os_thread_create` (`0x8A30`):

```
00D6ACF4  ldr  r2, [r4, #0x24]   ; pilha
00D6ACF8  ldrb r3, [r4, #0x20]   ; PRIORIDADE
00D6ACFC  ldr  r0, [r4, #0xc]
00D6ACFE  ldrd r1, r2, [r4, #0x18]
00D6AD02  bl   0xCF7AD4
```

A MainTask grava `movs r3,#1` em `sp+0x20` (`0xCF8068`): prioridade **1**.
A ViewTask (`0xCF8384`) **não escreve** `sp+0x20` (o `memset` de `0xCF8394`
deixa 0): prioridade **0**. O `sp+0x54 = 3` (`0xCF83AC`) é o **id de fila**
(008 B8: a tabela `0x81D68C`, entrada de 0x58, id em `+0x54`), não a
prioridade.

As prioridades (`desc+0x20`) das criações de
`tools/stack_rc7.py --tarefas`:

| criação | tarefa | prioridade |
|---|---|---|
| `0xCF8078` | MainTask | **1** |
| `0xCF8174` | PreTask | 3 |
| `0xCF83B8` | ViewTask | **0** (não escreve; o `memset` deixa 0) |
| `0xD3FD30` | DbsTask | 1 |
| `0xD40104` | MgrTask | 3 |
| `0xD40266` | Master_CPU_Recv_Task | 4 |
| `0xD4039C` | MediaTask | 3 |
| `0xD40516` | (sem nome) | 4 |
| `0xD92350` | bt_host_task | 3 |

**PROVÁVEL — número maior = mais prioritário** (convenção do FreeRTOS;
`os_thread_create` na mask ROM). Logo a ViewTask (0) **não está acima** da
MainTask (1): **cai a hipótese de starvation por prioridade**. O que sobra é
a **trava do banco** (1c): a MainTask **bloqueia** no mutex, não perde CPU
para a view.

## 1c. Ciclo de travas: o que a RC7 acrescenta

**CONFIRMADO — o mutex do banco é `[0x81DC00]+0x5C`** (take `0x80DB48`,
give `0x80DB6E`), e o arquivo é `[0x81DC00]+0x60`. O `get_path`
(`0xCFEFC4`) entra em `0xD6D1B4` → `0xD6F138` → `0xD777CC`
(`f_open`/`f_read`/`f_close` de `0:\DBROOT\db_audio.db`), **segurando o
mutex durante o I/O do cartão**. O like getter (`0xCFF0A8` → `0xD6DB90`)
também toma o mesmo mutex.

**CONFIRMADO — quem chama o `get_path` na fábrica:** todos os 6 `bl`
diretos estão no **presenter/MainTask**:

| chamada | função | contexto |
|---|---|---|
| `0xCFF0C0` | `0xCFF0A8` (like getter) | chamado por `0xCFF2A4` (rajada) e `0xD00C24` (delete) — MainTask |
| `0xCFF37C` | `0xCFF354` (`pstr_audio_love_change`) | chamado por `0xD08D98`/`0xD0A394` — presenter |
| `0xD0138E` | `0xD01368` (`page10 file path`) | `page10_mbox_process`/`page10_btn_process` — presenter |
| `0xD01624` | `page10_btn_process` | presenter |
| `0xD016C2` | `page10_mbox_process` | presenter |
| `0xD017D2` | `page10_mbox_process` | presenter |

A **RC7** acrescenta o **7º** chamador, `0xDAA144` (o TITULO), que roda na
**ViewTask**. É o **único** `get_path` da ViewTask; a fábrica nunca abriu o
banco pela view.

**PROVÁVEL — é essa a contenção:** a ViewTask pega o mutex no TITULO e
segura durante o I/O do cartão; a MainTask, no like getter da rajada
(`0xCFF0A8`, via `0xCFF2A4`), espera o mesmo mutex e **para**; sem refresh,
o watchdog vence (~15 s, 010 D5). O B2 não ajuda porque a ViewTask está
**viva** (segurando o mutex), só a MainTask está bloqueada.

## 1d. Outro caminho até o reset

**CONFIRMADO — há dois:** (1) o **fault handler** `0xCF5734` →
`0x80CF9E` (reinício da fábrica; 009 C1); (2) o **watchdog** alimentado por
`0xD46B14` (009 C2 / 010 D2). O B2 mostrou que a checagem "tarefa morta"
(`0xD46B30`) **não** é a causa (010 D5). O atraso de ~15 s aponta para o
watchdog (MainTask bloqueada no mutex), mas um **fault atrasado** no
`get_path`/driver de SD **não está descartado**. Fora do dump: o driver do
`/dev/wdog` e o código da mask ROM; não dá para separar os dois só pela
estática.

## 1e. Os ~15 s

**HIPÓTESE — o único número no dump é `0x14`:** `0xD46AAA` faz
`movs r3,#0x14` e passa a `/dev/wdog` (`0xD46AAC str r3,[r2,#-0x10]!` →
`0xD636F0`). A unidade (s ou ticks) e o período do comando de timer não
estão no dump (o descritor da MainTask tem `0x1e`/`0x78`/`0x3e8` em
`sp+0x30/34/40`, mas o papel de cada um não fecha). **Não dá para explicar
os ~15 s por estática**; a coincidência com `0x14` é só indício.

## 2. O caminho do arquivo sem o banco

**CONFIRMADO — não existe global com o caminho atual.** O `get_path` escreve
no buffer do chamador (o like getter aloca 0xFF em `0xCFF0A8`; o
`page10` usa o buffer de `0xD01368`); o caminho não fica num global lido
pela view. O `0xD08448` (mensagem do título) usa o getter de **nome**
(`0xCFEE60`), não o `get_path`.

**CONFIRMADO — a rajada já carrega o caminho na mensagem:** `page4_media_cb`
(`0xD088B4`) chama `0xD084F8` em `0xD088D8` (o caminho do evento) e o
`0xD0D818` envia a mensagem ao ring da view. O `0xD084F8` (branch `r0 != 0`,
`0xD08556`) copia o caminho (`r5`) para `msg+0x14` com o `0xD9FD54`
(strncpy); se `r0 == 0`, usa o placeholder `0xCE4473` (`"  "`). O título
(`0xD08448`, chamado logo depois em `0xD088E8`) faz o mesmo com o nome.

**CONFIRMADO — a ViewTask escolhe o rótulo pelo tipo da mensagem.**
`page_music_play_label_process` (`0xD3220C`, não `0xD32204`) lê o halfword
`msg+4` e o `tbb` de `0xD32242` escolhe o rótulo em `[[0x81CE2C]+0xAC]`
(`r5`): 0 → `[r5]`, 1 → `[r5+4]`, 2 → `[r5+8]`, 3 → `[r5+0x14]`,
4 → `[r5+0x18]`; em seguida `set_text(rótulo, msg+0x14)` em `0xD3225E`
(`b.w 0xD5ED94`). A mensagem do caminho (`0xD084F8`) grava **2** em `+4`
(o rótulo `[r5+8]`); a do título (`0xD08448`) grava **1** (o rótulo
`[r5+4]`).

**CONFIRMADO — o TITULO só roda para o título, e o `r5` dele é o texto do
título.** O TITULO (`0xDAA014`) só segue quando `r4 == [r6+4]`
(`0xDAA114`), isto é, quando o rótulo é o **1** (o título). Logo o `r5` que
o TITULO copia é o **texto do título**, não o caminho: era o erro do B3
anterior, que copiava o `r5` e caía sempre no cinza.

**CONFIRMADO — o rótulo 2 já tem o caminho quando o título chega.** O
`page4_media_cb` chama o caminho (`0xD088D8`) **antes** do título
(`0xD088E8`); a fila da ViewTask é FIFO (a mesma `0xD3220C` processa as
duas), então o `set_text` do rótulo 2 já rodou quando o TITULO lê o rótulo
2.

**CONFIRMADO — o `lv_label_get_text` da fábrica é inline.** O
`lv_label_set_text` (`0xD5ED94`) grava o texto em `[rótulo+0x24]`
(`ldr r6,[r4,#0x24]` em `0xD5EDA0`; `str r0,[r4,#0x24]` em `0xD5EDC2`);
não há função separada nem a string `lv_label_get_text` no binário. O getter
é o próprio `ldr r0,[rótulo+0x24]`.

**O B3 (implementado):** no lugar do `get_path` da ViewTask, o TITULO lê o
texto do **rótulo 2** (o caminho) e o copia para a mesma RAM que o
`get_path` usava. Em `0xDAA144` os 10 bytes do par `movw/movt + blx
get_path` viram `ldr r0,[r6,#8]` (`B0 68`) + `ldr r0,[r0,#0x24]`
(`40 6A`) + `bl copia_path` (`0xDAAA00`) + 1 `nop`; o `copia_path` copia
`r0`→`r2` (`ext+0x110`) até 0xFF e devolve 1 só se o texto começa com `0:`
e tem `/` ou `\`, e 0 caso contrário. Em `0xDAA174` o cinza do **sucesso**
vira `movs r1,#0` + 3 `nop` (src nulo: **sem quadrado**); o `carrega_capa`
(`0x1AA188`) vira `movs r0,#0` + `nop`; o cinza da **falha** (`0xDAA1BE`)
fica, então caminho inválido/vazio continua cinza. O `0xD088D8`/`0xD084F8`
ficam de fábrica. Sem `f_open`, sem JPEG, sem heap; nenhum byte abaixo de
`0xE000`, setor `0xD000`/PSMP intocados.

**Formato:** nos ativos de teste o caminho é `0:/MUSICA/...` (barra
normal); o `get_path` da fábrica pode devolver `0:\` ou `0:/`. A cópia
aceita **os dois**.

## 3. A fábrica lê o cartão na ViewTask?

**CONFIRMADO — sim, e ela tira a view do monitor nesse trecho.** A
fábrica desregistra a ViewTask em `0xCFCA0E` e `0xCFCBC8`
(`"-view_task unregister failed!"`); o `0xCFCA0E` **antecede**
`"ebook_auto_play"`. O par `0xD46ACC`/`0xD46A20` é o
desregistro/registro do monitor. Ou seja: o e-book/foto lê o cartão no
contexto da view, mas a fábrica **desliga o monitor** durante o trabalho —
é a mitigação que o próximo passo (abrir o MP3 e decodificar o JPEG na
ViewTask) pode copiar.

## O que não dá para saber

- o **driver do `/dev/wdog`** e o **handler de fault ativo** (mask ROM): se
  o B3 ainda reiniciar, não separa fault de watchdog;
- o **tempo do `get_path`** no cartão real e a **unidade do `0x14`**;
- se o mutex do banco é recursivo e o **timeout do take** (`0x80DB48`);
- se o **page10** da fábrica também disputa o mutex com a MainTask (os dois
  são MainTask; a contenção só nasce com a view da RC7).

## Kits e shas do B3

Base: a RC7 exata `3af97713…`. Contra ela, o B3 altera **68 bytes**
(`0x1AA144` 10 B, `0x1AA174` 8 B, `0x1AA188` 4 B, `0x1AAA00..0x1AAA2E`
46 B); o `0xD088D8` fica de fábrica.

| | sha256 |
|---|---|
| imagem B3 (sem carimbo) | `3e9b8fa138c79f129bcfbd6cee1ed6f73634ce1e0be624ea89db3998340a5dd4` |
| imagem B3 carimbada (`RC7 diag B3`, `--em 0x1A4F00`) | `5e86077b88ad8cb45a5f7347a3e664508cdd27879e116427be9ac6c63d0dee3e` |
| `.up` (`OpenPod_OpenPodReload1.0RC7DiagB3.up`) | `e0d5594f2c4c496a7847caddc3491d0e29656608d8118a139cd33834c1a9c8f4` |

CRC do `.up`: **`0xD9DB`** (3 setores: `0x146000`, `0x1A4000`, `0x1AA000`;
65 bytes alterados contra a base B2 carimbada `72632cfc…`; bootloader e setor
`0xD000` como de fábrica; PSMP fora).

## Leitura do B3 no aparelho

| no aparelho | leitura |
|---|---|
| **Toca, sem o quadrado cinza** | o rótulo 2 tinha o caminho válido: a captura funcionou; a contenção do mutex no TITULO era a causa (o caminho da mensagem serve para a correção final) |
| **Toca, com o quadrado cinza** | o rótulo 2 não tinha o caminho (vazio ou fora do formato `0:`): o caminho não chegou à view; a contenção não era (só) o `get_path` |
| **Reinicia** | o `get_path` da view não era (ou não era só) a causa: sobra o `f_open`/JPEG, um fault ou o próprio caminho copiado |

A volta de segurança é a **RC6**.
