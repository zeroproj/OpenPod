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

**CONFIRMADO — a rajada já carrega o caminho:** `page4_media_cb`
(`0xD088B4`) chama `0xD084F8` em `0xD088D8` (o caminho do evento) e o
`0xD0D818` envia a mensagem ao ring da view. O **melhor ponto** para
capturar na MainTask é exatamente `0xD088D8`, **antes** da mensagem de
título: o caminho está em `[r4+0x14]` e a MainTask não precisa do banco.

**Formato:** nos ativos de teste o caminho é `0:/MUSICA/...` (barra
normal); o `get_path` da fábrica pode devolver `0:\` ou `0:/`. A captura
deve aceitar **os dois** (foi o que o B3 faz).

**O B3 (implementado):** em `0xD088D8` o `bl 0xD084F8` vira
`bl guarda_path` (`0xDAAA00`), que copia o caminho para `0xDAAB00` e chama
o `0xD084F8` de verdade; o TITULO (`0xDAA144`) troca o par
`movw/movt + blx get_path` por `bl le_global` (`0xDAAA40`) + 3 `nop`; o
`le_global` copia o global para `ext+0x110` e devolve 1 só se o caminho
começa com `0:/` ou `0:\`; o `carrega_capa` (`0x1AA188`) vira
`movs r0,#0` + `nop` e o cinza continua. Sem `f_open`, sem JPEG, sem heap.

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

| | sha256 |
|---|---|
| imagem B3 (sem carimbo) | `5f2fe23408fbdb001aa56275922c12b1a6740b6b808e4bca61fed19406941bf5` |
| imagem B3 carimbada (`RC7 diag B3`, `--em 0x1A4F00`) | `a11631282903b117efe8c58d21d3fdc9b223c0a276e22d6faf239e61b44bef8b` |
| `.up` (`OpenPod_OpenPodReload1.0RC7DiagB3.up`) | `2c8f091e2e36f3047d419c39ad3f917a429225777f16b6727d5ce8947e2fedee` |

CRC do `.up`: **`0xE7A9`** (4 setores: `0x108000`, `0x146000`, `0x1A4000`,
`0x1AA000`; 141 bytes alterados contra a base B2 `72632cfc…`; bootloader e
setor `0xD000` como de fábrica; PSMP fora).

## Leitura do B3 no aparelho

| no aparelho | leitura |
|---|---|
| **Toca, cinza** | a contenção do mutex no TITULO era a causa; o caminho capturado na MainTask serve para a correção final |
| **Reinicia** | o `get_path` da view não era (ou não era só) a causa: sobra o `f_open`/JPEG, um fault ou o próprio caminho capturado |

A volta de segurança é a **RC6**.
