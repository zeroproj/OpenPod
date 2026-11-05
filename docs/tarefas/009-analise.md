# Ficha 009 — RC7: a causa do REINÍCIO (análise estática do ORIGINAL)

> **LEIA ANTES:** a coordenação conferiu esta análise no binário e **derrubou duas conclusões marcadas como
> CONFIRMADO**: "o handler de fault está fora do dump" e "o B não é deadlock". Valem as correções da seção
> **Conferência da coordenação**, no fim deste arquivo. Onde houver conflito, ela prevalece.

- Tipo: **Risco**. Objeto: **só leitura** de `firmware/ORIGINAL/GN438_original.bin`
  (sha256 `b7cd5eb9…`, confere). Nada foi gravado no aparelho, nada foi
  empurrado, nenhum merge.
- Condução: sessão MiniMax M3 (API direta), sobre o despacho `DESPACHO-009.md`.
- Classificação de cada afirmação: **CONFIRMADO** (prova reproduzível: o
  endereço e as instruções desmontadas do ORIGINAL, ou a saída de um
  comando), **PROVÁVEL** (indícios fortes), **HIPÓTESE** (ainda não
  fechado). Onde não dá para saber, isso é dito.
- Endereços de execução XIP = offset no arquivo + `0x00C00000`. Os endereços
  de RAM (`0x008xxxxx`) e de mask ROM (`0x00xxxxxx` abaixo de `0x00C00000`)
  **não estão no dump** — quando aparecerem, é para dizer que não dá para
  saber o que eles fazem.

## Ferramentas desta sessão

| Comando | O que faz |
|---|---|
| `python3 tools/disasm.py firmware/ORIGINAL/GN438_original.bin --map xip --at 0x… --count N` | desmonta Thumb-2 e resolve os pools literais |
| `python3 tools/stack_rc7.py --cadeia 0x…` | quadro de pilha de cada função e o **pico** de uma cadeia de chamadas (medido, não estimado) |
| `python3 tools/stack_rc7.py --tarefas` | as criações de tarefa e o **tamanho declarado** de cada pilha |
| `python3 tools/stack_rc7.py --quem 0x…` | quem chama um endereço |
| `python3 tools/build.py --receita reload_1.0_rc7_diag_b0 --saida …` | a imagem B0 |
| `python3 tests/test_diag_trava.py` | 28 testes do degrau (inclui o B0) |

`tools/stack_rc7.py` é novo nesta ficha (340 linhas, o limite do projeto é
350). Ele **mede** o quadro de cada função (`push` + `sub sp,#imm`) e soma o
máximo ao longo da cadeia; as chamadas para fora do dump entram com quadro 0,
então o número que ele imprime é um **mínimo**.

## Achado avulso que muda o quadro (CONFIRMADO)

**A fábrica tem 1072 `udiv`/`sdiv`** — o que a ficha 007 usou como
premissa ("a fábrica não tem nenhuma ocorrência de udiv/sdiv") e a ficha 008
repetiu no H3 **é falsa**. Varredura de capstone do dump inteiro
(`0x00C00000..0x00DA0000`): **1072** ocorrências, a primeira em
`0x00C00BF6` (`udiv r1, r6, r7`). E há uma **no caminho do play**:
`0x00D087F2  udiv r3, r6, r2` (dentro do presenter que formata
`"%02d:%02d:%02d"`).

**Consequências:** (1) o **núcleo do SL6801 tem a divisão por hardware** — o
`div_soft` da ficha 007 (a reescala por software) foi **desnecessário**
(inofensivo: continua correto e mais lento); (2) o H3 da 008 se apoiava
numa premissa falsa — a conclusão dele ("o lote não usa divisão, logo não
há risco") continua válida, mas pelo motivo certo: **o núcleo tem
`udiv`**.

---

# Pergunta 1 — O que causa o REINÍCIO neste aparelho?

## 1.1 Onde estão os vetores (CONFIRMADO)

O dump tem **duas** tabelas de vetores, e é preciso saber qual é a que vale:

**a) a do bootloader** — o cabeçalho `HLKJ` (`0x00000000`, 0x60 B) tem
`loadToRam 0x0081FBC0`, `runFromRam 0x00820001`, `loadLength 0xC8EC`,
`loadCrc 0x759D`. O payload (file `0x00000060`..`0x0000C94C`) começa pela
tabela de vetores e vai para a RAM em `0x0081FBC0`; o CRC confere
(`crc16_ccitt_false(d[0x60:0x60+0xC8EC]) = 0x759D`).

**b) a do app (a que vale quando a música toca)** — a partição `FIRM`
(file `0x0000E000`) tem o seu cabeçalho: `loadToRam 0x00804C00`,
`runFromRam 0x00804C01`, `loadLength 0x1000` (4 KiB), `loadCrc 0x68E1`. O
CRC confere sobre `FIRM[0x30:0x1030]` = file `0x0000E030..0x0000F030`
(`crc16_ccitt_false(d[0xE030:0xF030]) = 0x68E1`). **A tabela de vetores do app
está em file `0x0000E030`** (RAM `0x00804C00`), e os primeiros 4 KiB da FIRM
são copiados para a RAM — o resto da FIRM (~1,6 MiB) roda em XIP.

A tabela do app, palavra a palavra (file `0xE030` + 4·i):

| i | vetor | valor | para onde |
|---|---|---|---|
| 0 | SP inicial | `0x0086AE98` | — |
| 1 | Reset | `0x00804C41` | RAM (fora do dump) |
| 2 | NMI | `0x00804C91` | RAM (fora do dump) |
| 3 | **HardFault** | `0x00804C91` | RAM (fora do dump) |
| 4 | MemManage | `0x00804C91` | RAM (fora do dump) |
| 5 | BusFault | `0x00804C91` | RAM (fora do dump) |
| 6 | UsageFault | `0x00804C91` | RAM (fora do dump) |
| 7..11 | reservados | `0x00CF5AC5` | XIP (o "default", ver 1.2) |
| 12 | SVCall | `0x0000B4F5` | **mask ROM** (fora do dump) |
| 13 | DebugMon | `0x00804C91` | RAM |
| 14 | reservado | `0x00CF5AC5` | XIP |
| 15 | PendSV | `0x0080CD05` | RAM (fora do dump) |
| 16 | SysTick | `0x0000B5A9` | **mask ROM** (fora do dump) |
| 17+ | IRQ 0..N | `0x00CF5AC5` (e dois `0x00804C91`) | XIP / RAM |

Desmontagem da primeira linha da tabela (file `0xE030`):
`98 ae 86 00 | 41 4c 80 00 | 91 4c 80 00 | 91 4c 80 00 | …` = SP `0x0086AE98`,
Reset `0x00804C41`, NMI/HardFault `0x00804C91`.

**CONFIRMADO:** o `HardFault` (e NMI/MemManage/BusFault/UsageFault) do app
apontam para `0x00804C90`, que está **na RAM** — e a RAM **não está no dump**
(o que se vê em `0xE030` é só a *tabela*, não o código do handler).

## 1.2 Os handlers: reiniciam ou laçam? (CONFIRMADO)

**O handler "default" (os vetores reservados) LAÇA — não reinicia.**
`0x00CF5AC4`:

```
00CF5AC4  push {r3, lr}
00CF5AC6  bl   0xCF5AF0      ; pega um numero
00CF5ACA  mov  r4, r0
00CF5ACC  bl   0xCF5AE0      ; pega outro
00CF5AD0  mov  r1, r4
00CF5AD2  mov  r2, r0
00CF5AD4  ldr  r0, [pc, #4]   ; a string
00CF5AD6  bl   0x2B0         ; printf
00CF5ADA  b    0xCF5ADA      ; <<< LAÇO INFINITO
```

**O handler de fault do SDK (a cópia visível) desabilita interrupções e
chama uma rotina "fatal".** A assinatura aparece duas vezes no dump, com o
mesmo código: file `0x0000C4F0` (XIP `0x00C004F0`, a cópia do bootloader) e
file `0x0000E4C0` (XIP `0x00C0E4C0`, a cópia que está nos 4 KiB do app):

```
71 b6              cpsid i
1e f0 04 0f        tst.w lr, #4          ; veio de thread mode?
0c bf              ite eq
  <mrs> <mrs>                              ; dois registradores de status
20 e9 f0 0f        push.w {r4-r11, lr}
71 46              mov  r1, lr
03 f0 ef fa        bl   <a rotina fatal>
```

No build do **bootloader** esse `bl` resolve para a RAM `0x00823A72`
(file `0x00003F12`). No build do **app** o mesmo `bl` resolve para
`0x00D0EF64` — que está **dentro de uma tabela de saltos**, ou seja, **a
cópia que está no flash do app não é código executável**. Logo: **o handler
de HardFault que realmente roda está fora do dump** (mask ROM/RAM).

**Não dá para saber**, então, o que o HardFault ativo faz: se ele reinicia,
se ele laça, ou se ele escala para o Reset do sistema. A cópia do flash só
diz "desabilita interrupções e chama uma rotina fatal" — e o alvo da rotina
no build do app é lixo.

## 1.3 O app reinicia o chip por software? (CONFIRMADO: NÃO)

A rotina de reset do sistema **existe** no flash:

```
00C0E6A4  dsb sy
00C0E6A8  ldr  r1, [pc, #0x14]   ; = 0xE000ED00  (o SCB)
00C0E6AA  ldr  r3, [pc, #0x18]   ; = 0x05FA0004  (VECTKEY | SYSRESETREQ)
00C0E6AC  ldr  r2, [r1, #0xc]    ; AIRCR
00C0E6AE  and  r2, r2, #0x700    ; PRIGROUP
00C0E6B2  orrs r3, r2
00C0E6B4  str  r3, [r1, #0xc]    ; AIRCR = 0x05FA0004 | PRIGROUP
00C0E6B6  dsb sy
00C0E6BA  b    0xC0E6BA         ; espera o reset
```

`0x05FA0004` = `VECTKEY(0x5FA) << 16 | SYSRESETREQ(bit 2)` — é o
`NVIC_SystemReset()` do CMSIS. A cópia do bootloader está em `0x00C006D4`.

**E ninguém a chama.** Varredura de todos os `bl`/`b.w` do flash
(`0x00C00000..0x00DA0000`, 29 072 chamadas): **nenhuma** chama
`0x00C0E6A4` nem `0x00C006D4`. Varredura dos pools literais: **nenhum**
ponteiro para `0x00C0E6A4`/`0x00C0E6A5`.

**CONFIRMADO: o código visível do app nunca pede o reset do chip.** Se o
aparelho reiniciou, o pedido de reset veio de **fora do flash visível** — do
driver do watchdog ou da mask ROM (ver 1.4).

## 1.4 O watchdog (CONFIRMADO o que existe; não dá para saber o prazo)

- A **MainTask abre o watchdog de hardware** na inicialização:
  `0x00CF7EAA  bl 0x00D46A8C` → `0x00D46A8C` faz
  `ldr r0, [pc,#0x30] ; = 0x00CD9049` (a string **`"/dev/wdog"`**),
  `movs r1,#0`, e chama `0x00D636F0` (o `open`). O handle fica em
  `0x0081D148`.
- Um **monitor** (`0x00D46B16`) alimenta o watchdog: `bl 0x00D637AA`, que é
  um despachante (`ldr r0,[r0,#4]; ldr r4,[r0,#4]; bx ip` — o driver está
  **fora do dump**). O mesmo monitor imprime **`"-watch_watchdog_refresh"`**
  quando o modo de depuração (`0x00823EB0`) é `0x16`.
- Uma rotina **ao lado** (`0x00D46B6E`) confere o "batimento" de cada
  tarefa (a tabela `0x0081D68C`, entradas de `0x58`, o bit em `+0x50`) e
  imprime **`"-task %d (%s)is dead"`** / **`"-task %d is dead"`** quando uma
  tarefa não bate.
- **O refresh do watchdog não depende do teste das tarefas mortas**: o
  `bl` de refresh (`0x00D46B52`) está no caminho normal do monitor, e o
  `cbz` que precede o ramo das tarefas mortas **salta para ele** — ou
  seja, o watchdog é alimentado **incondicionalmente**.
- Nem `0x00D46B16` nem `0x00D46B6E` têm chamador visível (varredura de
  `bl`): são alcançados por uma tabela (timer/callback), que não está no
  dump.

**Não dá para saber:** o prazo do watchdog e o que o driver faz quando ele
expira (o driver está na mask ROM/RAM). Também não dá para saber se o
monitor, ao ver uma tarefa morta, faz alguma coisa além de imprimir — no
código visível, **ele só imprime e volta** (sem reset, sem `abort`).
**E, como o watchdog é alimentado incondicionalmente pelo monitor, uma
tarefa travada não o deixa expirar**: ela só aparece no log.

## 1.5 `0x9E3C` e o resto que está fora do dump

`0x00CF7884` (o `free` do app) é um trampolim para a mask ROM:

```
00CF7884  12 f7 da 92   b.w 0x9E3C     ; free  -> ROM
00CF7888  09 f7 4f 91   b.w 0xB2A      ; realloc -> ROM
00CF788C  09 f7 8d 91   b.w 0xBAA      ; memset -> ROM
00CF7890  12 f7 fa 92   b.w 0x9E88     ; malloc -> ROM
```

O heap inteiro (malloc/realloc/free) está na **mask ROM**, fora do dump.
Logo: **não dá para saber se o `free(NULL)` da RC7 (achado H5 da ficha 008)
tolera `NULL`**, nem o que o `free` faz com um ponteiro já liberado. (No
degrau **B** e no **B0** isso não aparece: nenhum `calloc`/`free` é chamado.)

Fora do dump, e portanto **sem resposta possível**:
`0x00000000..0x00BFFFFF` (mask ROM: heap, drivers, `/dev/wdog`, SysTick em
`0xB5A8`, SVCall em `0xB4F4`, o `free` em `0x9E3C`), `0x00800000..` (RAM: o
código do SDK, os mutexes `0x80DB48`/`0x80DB6E`, o handler de fault ativo do
app em `0x00804C90`, o PendSV em `0x0080CD04`) e a parte do bootloader que
não está no dump (o `HLKJ` em `0x00000060` está, mas o resto da mask ROM
que o carrega, não).

## 1.6 Conclusão da pergunta 1

- **CONFIRMADO:** o flash visível **não** reinicia o chip (nenhuma chamada à
  rotina de reset). O "default" dos vetores **laça** (congela), não
  reinicia.
- **CONFIRMADO:** existe watchdog de hardware ("/dev/wdog"), aberto pela
  MainTask e alimentado por um monitor que também avisa qual tarefa parou.
- **PROVÁVEL:** o reinício do aparelho no B **não vem do app** (o app não
  pede reset); vem do **driver do watchdog na mask ROM** ou de um caminho de
  fault da própria ROM — que o dump não mostra. Como o monitor alimenta o
  watchdog mesmo com tarefas mortas, um **travamento** (deadlock) puro
  **não** reinicia: ele produziria **congelamento** (o sintoma que a ficha
  008 esperava), não reinício.
- **Logo: o B não trava — ele FAZ ALGUM QUE DÁ FAULT (ou um reset pedido
  de fora).** Um fault (HardFault/UsageFault) no app é tratado pelo handler
  em `0x00804C90`, **fora do dump**; se esse handler pedir o reset do
  sistema, o aparelho "reinicia" — e é exatamente o sintoma observado.
  Isso é **HIPÓTESE** (não dá para ver o handler), mas é a única hipótese
  que casa com "reiniciou" em vez de "congelou".

---

# Pergunta 2 — `get_path` com a origem real

## 2.1 O switch: seis casos, decodificados (CONFIRMADO — e a 008 errou o caso 0)

`0x00CFEFC4` (o `pstr_audio_get_path` da fábrica):

```
00CFEFC4  push {r4, r5, r6, lr}
00CFEFC6  mov  r6, r0            ; r6 = a ORIGEM
00CFEFC8  sub.w sp, sp, #0x238   ; quadro de 0x248
00CFEFCC  mov  r4, r1            ; r4 = o ÍNDICE
00CFEFCE  mov  r5, r2            ; r5 = o buffer de destino
00CFEFD0  cmp  r2, #0
00CFEFD2  beq  0xCFF092         ; buffer nulo -> falha
00CFEFD4  mov.w r2, #0x220
00CFEFD8  movs r1, #0
00CFEFDA  add  r0, sp, #0x18
00CFEFDC  bl   0xBAA             ; memset(sp+0x18, 0, 0x220)
00CFEFE0  movs r2, #0x10
00CFEFE2  movs r1, #0
00CFEFE4  add  r0, sp, #8
00CFEFE6  bl   0xBAA             ; memset(sp+8, 0, 0x10)
00CFEFEA  cmp  r6, #5
00CFEFEC  bhi  0xCFF02C         ; origem > 5 -> falha
00CFEFEE  tbb  [pc, r6]          ; o switch
```

**O `tbb` é em `0x00CFEFEE`** (4 bytes: `df e8 06 f0`) e a **tabela fica no
endereço seguinte, `0x00CFEFF2`** (bytes): `03 17 27 35 3c 42 01 22 06 a9
20 46 6e f0 …`. O alvo de cada caso é `0x00CFEFF2 + 2·byte`:

| origem | byte | alvo | o que o caso faz |
|---|---|---|---|
| **0** | `0x03` | `0x00CFEFF8` | `movs r2,#1; add r1,sp,#0x18; mov r0,r4; bl 0xD6D1B4` → o **banco** (`db_audio.db`), `strncpy(dest, buf, 0xFF)` e devolve 1 |
| **1** | `0x17` | `0x00CFF020` | `ldr r3,=0x0081BC84; ldr r0,[r3,#0x38]; bl 0xCFECBC` e, se válido, `bl 0xD6D414` (`db_artist.db`) |
| **2** | `0x27` | `0x00CFF040` | `ldr r0,[r3,#0x44]; bl 0xCFECCC` e, se válido, `bl 0xD6D3C4` |
| **3** | `0x35` | `0x00CFF05C` | `bl 0xD6DAE8` (com `r0 = 1`) |
| **4** | `0x3C` | `0x00CFF06A` | `bl 0xD6D7AC` |
| **5** | `0x42` | `0x00CFF076` | `ldr r0,=0x0081BCD0; bl 0xD6D978` |
| ≥6 | — | `0x00CFF02C` | falha (devolve 0) |

> **Correção importante:** a ficha 008 (achado B1) diz que o **caso 0** é o
> `0xD6D1B4` (o banco). O caso 0 é o `0xD6D1B4` **sim**, mas o B1 da 008 se
> refere ao **caso 2** na numeração que ela usou — com a base da tabela em
> `0x00CFEFF4` (a base alinhada em 4, como manda o ARMv7-M) os casos 0 e 1
> caem em endereços sem sentido (`0x00CFEFFC`, `0x00CF91D0`). **A base é
> `0x00CFEFF2`** (o endereço logo depois do `tbb`): com ela, **os seis
> casos caem em corpos de código coerentes**, e é essa leitura que está
> acima. (O `tbb` do Thumb-1 usa a base sem alinhar.)

## 2.2 A RC7 lê exatamente o que a fábrica lê (CONFIRMADO)

Os getters da fábrica são:

```
0x00CFF1A8  ldr r3, [pc, #4]   ; = 0x0081BC84
0x00CFF1AA  ldrb r0, [r3]      ; <<< a ORIGEM (1 byte)
0x00CFF1AC  bx  lr

0x00CFF0FC  ldr r3, [pc, #4]   ; = 0x0081BC84
0x00CFF0FE  ldr  r0, [r3, #0x20]   ; <<< o ÍNDICE (palavra)
0x00CFF100  bx  lr
```

E a fábrica chama o `get_path` em `0x00CFF0A8` (o "caminho da faixa atual")
exatamente assim:

```
00CFF0B4  ldr  r5, [pc, #0x3c]   ; = 0x0081BC84
00CFF0B8  mov  r2, r0             ; o buffer
00CFF0BA  ldr  r1, [r5, #0x20]   ; o ÍNDICE
00CFF0BC  ldrb r0, [r5]           ; a ORIGEM
00CFF0C0  bl   0xCFEFC4           ; get_path(origem, índice, buf)
```

A rotina da RC7 (`tools/capa_album.s`, `corpo_titulo`) faz **o mesmo**, byte
a byte — no código montado:

```
00DAA134  movw r1, #0xbc84 ; movt r1, #0x81   ; 0x0081BC84
00DAA13C  ldrb r0, [r1]                        ; a origem
00DAA13E  ldr  r1, [r1, #0x20]                ; o índice
00DAA140  add.w r2, r7, #0x110                 ; o buffer
00DAA144  movw ip, #0xefc5 ; movt ip, #0xcf    ; 0x00CFEFC5 (get_path | Thumb)
00DAA14C  blx  ip                              ; <<< a chamada
```

**CONFIRMADO: a RC7 lê os MESMOS bytes que os getters da fábrica, no mesmo
endereço global.** Não há divergência de leitura. O que pode diferir é o
**valor** no instante em que a ViewTask roda o TITULO (o índice/origem podem
ter mudado entre a rajada do play e o processamento da mensagem) — e isso é
rara e verificável no aparelho.

## 2.3 De onde vem a origem (PROVÁVEL / não dá para saber o chamador)

A origem é um **id de playlist, 0..5**, e quem a escreve é
`0x00CFF25C`:

```
00CFF25C  push {r4, lr}
00CFF260  cmp  r0, #5
00CFF264  bls  0xCFF272         ; origem tem de ser 0..5
00CFF266  mov  r1, r0
00CFF26C  ldr  r0, [pc, #0x2c]  ; "-audio set playlist %d error!"
...
00CFF272  ldr  r4, [pc, #0x2c]  ; = 0x0081BC84
00CFF274  ldrb r3, [r4]         ; a origem antiga
00CFF276  strb r0, [r4]         ; <<< grava a origem
00CFF278  cmp  r3, r0
00CFF27A  itt  ne
00CFF27C  movne r3, #0
00CFF27E  strne r3, [r4, #0x20] ; se mudou, o índice vai a 0
```

**Nenhum `bl` do flash chama `0x00CFF25C`** (varredura de todos os `bl`:
nenhum) — o chamador está **fora do dump** (mask ROM/RAM). Também não há
ponteiro para ela nos pools. **Não dá para saber** qual valor a origem tem
em cada tela; **dá para saber** que ela é 0..5 e que o índice é zerado quando
a origem muda.

## 2.4 O que cada caso exige de estado (CONFIRMADO) e o que isso significa

Os seis casos **tomam o mesmo mutex** (`[0x0081DC00]+0x5C`, take `0x80DB48` /
give `0x80DB6E`, ambos fora do dump) e todos passam por
`f_open`/`f_read`/`f_close` do FatFs:

| caso | wrapper | inner | arquivo |
|---|---|---|---|
| 0 | `0xD6D1B4` | `0xD6F138` | `0:\DBROOT\db_audio.db` |
| 1 | `0xD6D414` | `0xD6EACC` | `0:\DBROOT\db_artist.db` (handle em `0x81BC84+0x38`) |
| 2 | `0xD6D3C4` | `0xD74180` | handle em `0x81BC84+0x44` |
| 3 | `0xD6DAE8` | `0xD7176C` | — |
| 4 | `0xD6D7AC` | `0xD735E8` | — |
| 5 | `0xD6D978` | `0xD706AC` | handle em `0x0081BCD0` |

Exigências de estado: o **mutex do banco** (`0x81DC00+0x5C`), o
**grant do FatFs** (reentrante, por operação) e o **handle** do caso (nos
casos 1, 2 e 5: o handle tem de ser válido — o getter `0xCFECBC`/`0xCFECCC`
devolve 1 só se o handle **não** for 1).

**O caso 0 é o único que abre `db_audio.db`** — e é o caso que a **fábrica
usa com sucesso** quando o aparelho toca. Como a RC7 chama o `get_path` com
**os mesmos valores** que a fábrica, o caso que roda é o mesmo que rodou
na fábrica.

**A diferença entre a fábrica e a RC7 não é o caso: é a TAREFA.** A
fábrica chama o `get_path` na **MainTask** (o presenter, `0x00D087D8`, que
manda a rajada do play); a RC7 chama o `get_path` na **ViewTask** (o
`page_music_play_label_process`, `0x00D32204`, que roda dentro do loop da
view, `0x00D24340` → `0x00D23E50`). É a **primeira vez** que o banco é
aberto pelo lado da ViewTask.

---

# Pergunta 3 — Pilha, sem premissa

## 3.1 A unidade de `0x1000`/`0x400` é PALAVRA (CONFIRMADO por contradição)

O `0x1000` e o `0x400` estão no campo `[struct+0x24]` que a fábrica passa
ao criar a tarefa (osFreeRTOS): `0x00CF83A0  mov.w r3, #0x1000` /
`0x00CF83A6  str r3, [sp, #0x24]`, e em `0x00D6ACF4` esse campo é repassado
ao `os_thread_create` (`0x00CF7AD4`), que o repassa **sem dividir nada**:

```
00CF7B06  ldr  r2, [sp, #0x28]   ; o tamanho da pilha
00CF7B08  ...
00CF7B18  uxth r2, r2            ; trunca para 16 bits
00CF7B1A  mov  r1, r5
00CF7B1C  ldr  r0, [pc, #0x40]   ; o pool
00CF7B1E  bl   0x8A30            ; xTaskCreate (mask ROM, fora do dump)
```

O `uxth` bate com o `configSTACK_DEPTH_TYPE` do FreeRTOS (uint16_t), que
conta a pilha **em palavras** — e a contradição abaixo fecha isso.

**O tamanho declarado de cada tarefa** (`python3 tools/stack_rc7.py --tarefas`):

| criação | tarefa | pilha declarada |
|---|---|---|
| `0x00CF8078` | **MainTask** | `0x400` |
| `0x00CF8174` | (PreTask) | `0x800` |
| `0x00CF83B8` | **viewTimer (a ViewTask)** | `0x1000` |
| `0x00D3FD30` | DbsTask | `0x1000` |
| `0x00D40104` | MgrTask | `0x400` |
| `0x00D40266` | Master_CPU_Recv_Task | `0x200` |
| `0x00D4039C` | MediaTask | `0x800` |
| `0x00D40516` | — | `0x200` |
| `0x00D92350` | bt_host_task | `0x800` |

**A contradição que fecha a unidade:** a **MainTask** (a que tem `0x400`) é
a que executa o `get_path` na fábrica, e o pico medido desse caminho é
**≥ 3464 bytes** (3.4). Se `0x400` fossem **1024 bytes**, a fábrica
estouraria a pilha **a cada toque de música** — e a fábrica funciona.
Logo: **`0x400` são 4096 bytes (1024 palavras) e `0x1000` são 16 KiB
(4096 palavras).** CONFIRMADO.

## 3.2 A soma de 1216 B da ficha 008 está ERRADA (CONFIRMADO)

`python3 tools/stack_rc7.py --cadeia 0xCFF0A8` (o "caminho da faixa atual" da
fábrica, que chama o `get_path`):

```
pico de pilha: >= 3408 bytes (0xD50)      [MINIMO: fora do dump entra com 0]
    0x00CFF0A8  quadro 24     ; malloc(0xFF) + get_path
    0x00CFEFC4  quadro 584    ; push {r4,r5,r6,lr} + sub sp,#0x238
    0x00D6D414  quadro 24     ; o wrapper do banco (take/give do mutex)
    0x00D6EACC  quadro 64     ; o inner do caso 1
    0x00D6F390  quadro 640    ; sub.w sp,#0x264  <<< a 008 nao contou isto
    0x00D777CC  quadro 144    ; f_open
    0x00D76324  quadro 56
    0x00D74FD4  quadro 16
    0x00D74598  quadro 640    ; sub.w sp,#0x278  <<< e nem isto
    0x00D77C9C  quadro 24
    0x00D77AF0  quadro 120
    0x00D77CCE  quadro 176
    0x00D7774C  quadro 528    ; sub.w sp,#0x204  <<< nem isto
    0x00D77208  quadro 96
    ...
```

Por caso (a partir do wrapper):

| caso | pico a partir do wrapper | + quadro do `get_path` (584) |
|---|---|---|
| 0 (`0xD6D1B4`) | ≥ 2136 | **≥ 2720** |
| 1 (`0xD6D414`) | ≥ 2800 | **≥ 3384** |
| 2 (`0xD6D3C4`) | ≥ 2800 | **≥ 3384** |
| 3 (`0xD6DAE8`) | ≥ 2144 | **≥ 2728** |
| 4 (`0xD6D7AC`) | ≥ 2136 | **≥ 2720** |
| 5 (`0xD6D978`) | ≥ 2680 | **≥ 3264** |

**A soma da 008 (1216 B) esqueceu os quadros grandes do FatFs**
(`0xD6F390` = 640 B, `0xD74598` = 640 B, `0xD7774C` = 528 B). O valor
real é **≥ 2720 B** em qualquer caso — mais que o dobro.

**Consequência 1:** a frase da 008 "a MainTask (pilha 0x400) chama o mesmo
get_path e nunca transbordou" **não fecha em bytes** (1024 B < 2720 B): ela
só fecha em **palavras** (4096 B), que é a leitura correta.

**Consequência 2:** a **ViewTask tem 16 KiB**, e o caminho
`ViewTask → label_process → TITULO → get_path` usa
≈ 104 B (as camadas da view, 008-H2) + 392 B (o TITULO da RC7, medido pelo
arnês da 007) + **≥ 2720 B** (o `get_path` real) ≈ **3,2 KiB** — **cabe
com folga de ~13 KiB**. **A hipótese H2 (transbordo de pilha) está
REFUTADA**, ainda mais forte do que a 008 dizia.

## 3.3 Em qual tarefa roda o `page_music_play_label_process` (CONFIRMADO)

**Na ViewTask.** O loop da view (`0x00D24340`, no ramo que começa com a
string `"watch_view_rec_analysis"`) é:

```
00D24340  bl   0xCF8444     ; le o ring das mensagens da view
00D24344  mov  r4, r0
00D24346  cbz  r0, 0xD24380
00D24348  bl   0xD23E50     ; <<< o despacho (chama o *_process da pagina)
00D2434C  mov  r0, r4
00D2434E  bl   0xD5811C     ; lv_mem_free
00D24352  b    0xD24340
```

O `page_music_play_label_process` (`0x00D32204`) é chamado pelo despacho
(através da tabela de callbacks da página — por isso não aparece como `bl`),
e o gancho da RC7 (`0x00D3225E`) está **dentro dele**. Logo: **o TITULO da
RC7 roda na ViewTask, com a pilha de 16 KiB**, e não na MainTask.

---

# Pergunta 4 — A rotina real de `tools/capa_album.s`, sem o stub

Tudo conferido no **código montado** (a imagem `reload_1.0_rc7`, sha
`3af97713…`), não no fonte.

## 4.1 Alvo de chamada, argumentos e o `sp` (CONFIRMADO)

- O gancho em `0x00D3225E` (XIP) é um **`b.w`**, não uma chamada:
  `77 f0 d9 be  b.w #0xdaa014`. Ele substitui o `b.w 0xD5ED94`
  (o `lv_label_set_text` da fábrica) e está **logo depois** de
  `pop.w {r4, r5, r6, lr}` (o `label_process` já desempilhou o quadro
  antes de branchear) — ou seja, o TITULO roda **na mesma pilha e no mesmo
  nível** do `lv_label_set_text` original (chamada de cauda).
- A cadeia de desvios: `0xD3225E → 0xDAA014` (entrada TITULO da tabela do
  lote) `→ 0xDAA020` (trampolim) `→ 0xDAA0E6` (`corpo_titulo`).
- **Argumentos:** no gancho, `r0` = o rótulo e `r1` = o texto (os mesmos do
  `lv_label_set_text`); `corpo_titulo` faz `mov r4, r0` / `mov r5, r1`.
- **`sp` alinhado em 8 na chamada: SIM.** `corpo_titulo`:
  `push.w {r4-r11, lr}` (9 regs = 36 B) + `sub sp, #4` → **40 B**, e 40 é
  múltiplo de 8: o `sp` está alinhado em 8 em **todas** as chamadas internas.
  O mesmo vale para as outras rotinas do lote (`corpo_cria` 36+4, `corpo_apaga`
  36+4, `carrega_capa` 36+12, `procura_apic` 36+4+48, `saida` 36+4+40,
  `leitor` 24+8, `div_soft` 8, `comparou_caminho`/`copia_caminho` 16 — todos
  múltiplos de 8). E o `sp` de entrada é o do `label_process`, alinhado por
  contrato.

## 4.2 Registradores preservados (CONFIRMADO)

`corpo_titulo` faz `push.w {r4-r11, lr}` no começo e `pop {r4-r11, pc}` no
fim: **`r4..r11` e o `lr` são preservados**, e o retorno é para quem chamou
o `label_process` (mesma semântica de cauda do `b.w` original).
`r0..r3` são de raspar (o AAPCS os trata como destruíveis, e o
`label_process` não os usa depois do branch — ele já desempilhou o quadro).

## 4.3 Tamanho do buffer e o `strncpy` da fábrica (CONFIRMADO)

O `get_path` da fábrica termina com
`strncpy(destino, sp+0x18, 0xFF)` (`0x00CFF084`), ou seja: **no máximo 255
bytes e sem terminador se o caminho for maior**. A RC7 protege isso:
antes da chamada ela faz `memset(ext+0x110, 0, 0x100)` (256 B) — logo o
byte 255 fica 0 e o buffer **é sempre uma string C válida de ≤ 255
caracteres**. Os dois laços da RC7 (`comparou_caminho`, `copia_caminho`)
leem/escrevem no máximo o índice `0xFF` dos buffers de 256 B
(`ext+0x10` = o caminho guardado, `ext+0x110` = o novo): **dentro dos
limites**. CONFIRMADO.

## 4.4 O ponteiro: mensagem antes da view/ext e depois de apagada (CONFIRMADO)

O TITULO **re-lê** a view e o contexto antes de usar:

```
00DAA0FE  movw r0, #0xce2c ; movt r0, #0x81   ; 0x0081CE2C
00DAA106  ldr  r0, [r0]                ; a struct das paginas
00DAA108  cmp  r0, #0
00DAA10A  beq  0xDAA1D0                ; sem struct -> so o set_text
00DAA10C  ldr.w r6, [r0, #0xac]        ; a view da pagina 4
00DAA110  cmp  r6, #0
00DAA112  beq  0xDAA1D0                ; sem view -> so o set_text
00DAA114  ldr  r0, [r6, #4]            ; o rotulo do titulo da view
00DAA116  cmp  r0, r4                  ; e o rotulo que recebeu a mensagem?
00DAA118  bne  0xDAA1D0
00DAA11A  ldr  r7, [r6, #0x30]         ; o contexto (ext)
00DAA11C  cmp  r7, #0
00DAA11E  beq  0xDAA1D0                ; sem contexto -> so o set_text
```

- **Mensagem antes de a view existir:** `[[0x81CE2C] == 0]` ou
  `[view] == 0` → o TITULO sai depois do `set_text`. **Seguro.**
- **Mensagem antes de o contexto existir** (`calloc` falhou): `[view+0x30] == 0`
  → sai depois do `set_text`. **Seguro.**
- **Depois de apagada:** o `APAGA` (o cb do `LV_EVENT_DELETE` da imagem da
  capa) **libera o contexto e zera `[view+0x30]`** — e a `view` da página 4
  também é destruída (`view_clean_all_objs`, `lv_mem_free` em `0x00D23A7C`).
  Aí há **um risco real**: o TITULO lê `[[0x81CE2C]+0xAC]`, que pode
  apontar para uma `view` já liberada; se `[liberada+4]` por acaso casar com
  o rótulo recebido, o TITULO continua com `[liberada+0x30]`.
  **Emaltecer o risco: PROVÁVEL, não CONFIRMADO** — depende do que o
  gerenciador de memória faz com o bloco liberado (se o `memset` do
  `APAGA` já zerou `[view+0x30]`, o TITULO para; se o bloco foi reutilizado,
  o ponteiro é lixo). Note que a comparação `r0 == r4` **não protege**:
  a fábrica tirou o rótulo da **mesma** `view` (`ldr r0, [r5, #4]`, com
  `r5 = [[0x81CE2C]+0xAC]`), então a comparação é sempre verdadeira.
- **O `ext` nunca é liberado duas vezes:** o `APAGA` libera o contexto
  (e o `TITULO` não libera nada). O `ext` é criado na `CRIA` (uma vez por
  view) e liberado no `DELETE` da imagem.

---

# VEREDITO

**A causa do reinício NÃO fecha por estática.** O que fecha:

1. **CONFIRMADO** — o flash visível **não pede o reset do chip** (a rotina
   `NVIC_SystemReset` existe em `0x00C0E6A4` e **ninguém a chama**), e o
   handler "default" dos vetores **laça** (congela), não reinicia.
2. **CONFIRMADO** — existe watchdog de hardware, alimentado por um monitor
   que **também** avisa qual tarefa parou; como o monitor o alimenta mesmo
   com tarefas mortas, um travamento puro produziria **congelamento**, e o
   aparelho **reiniciou**. Logo o B **não é um deadlock**.
3. **CONFIRMADO** — a pilha não é a causa: a unidade de `0x1000`/`0x400` é
   **palavra** (16 KiB / 4 KiB) e o caminho do `get_path` da RC7 usa
   ≈ 3,2 KiB numa pilha de 16 KiB.
4. **CONFIRMADO** — a RC7 lê **exatamente** os mesmos bytes de origem e
   índice que a fábrica, e o `get_path` da RC7 roda **o mesmo caso** que o da
   fábrica (o mesmo `db`, o mesmo mutex, o mesmo FatFs). A **única**
   diferença é a **tarefa**: a fábrica abre o banco na MainTask; a RC7 abre
   na **ViewTask**.
5. **O elo que falta** está fora do dump: o **handler de HardFault ativo**
   (RAM `0x00804C90`), o **driver do `/dev/wdog`** (mask ROM) e o código da
   **mask ROM** em geral. Sem eles não dá para dizer se o B produz um
   **fault** (que a ROM transformaria em reset) ou um reset pedido de fora.

**Por isso a imagem B0 é necessária:** ela é a única forma de separar, no
aparelho, "a rotina do TITULO" de "a chamada do `get_path`".

---

# A imagem B0 (o degrau que separa a rotina do `get_path`)

**O que é:** a RC7 exata (`3af97713…`) com **2 bytes** trocados — o `blx`
da chamada ao `get_path` (o par `movw/movt` em `0x00DAA144` +
`0x00DAA14C`) vira `movs r0, #0`. O `get_path` **não é chamado** e a
rotina **inteira** do TITULO roda: `set_text`, leitura da view/ext,
`memset` do buffer, a comparação do caminho, o caminho guardado vazio e o
**quadrado cinza** (o caminho "sem_caminho" que já existe no código,
`0x00DAA1A4`).

**Receita:** `reload_1.0_rc7_diag_b0` = `reload_1.0_rc7` +
`fab_diag_trava.py --nivel b0 --em 0x1a8000`.
**Nível novo** em `tools/diag_trava_asm.py` (o scanner acha o par
`movw/movt` que carrega `0x00CFEFC5` **com o bit do Thumb** e o `blx` logo
depois; recusa se aparecer ≠ 1 vez) e em `tools/fab_diag_trava.py` (as
mesmas premissas e a mesma conferência de saída dos outros degraus: lê de
volta os 2 bytes, decodifica, e o diff final tem de ser **exatamente** os
2 bytes do patch).

| | sha256 |
|---|---|
| imagem (sem carimbo) | `63afb46ab8a9d9f8e0bedddf501c2adc2a4880f85d91d2ad982f73b23fec6cdb` |
| imagem carimbada (`RC7 diag B0`, `patch_versao --em 0x1A4F00`) | `61872fc2c87b77eae612f77487cacc5a4f5f54ab6030e7790f240381baa43d62` |
| `.up` (`OpenPod_OpenPodReload1.0RC7DiagB0.up`) | `70f5dc1476ddd984fdb25774371c2dfd53896d2e4a0063a68b4a3066f465ac6a` |

**CRC do `.up`: `0xA27E`** (conferido: `crc16_ccitt_false` do payload = o
campo; payload = a imagem carimbada byte a byte; cobertura `0x1AB000`;
bootloader e setor `0xD000` intactos; PSMP fora).

**Diff contra a RC7:** exatamente **2 bytes**, em `0x1AA14C` (`e0 47` →
`00 20`). Nada mais, em lugar nenhum.

**Kits:**
- `firmware/RELEASE/OpenPod Reload 1.0 RC7 Diag B0/` (interno)
- `release/OpenPod-Reload-1.0-RC7-Diag-B0/` (público, com o `.up`,
  `cabo/setores/`, `install.sh` e o **`TESTAR.txt`** curto)

**Leitura do resultado:**

| no aparelho | leitura |
|---|---|
| **B0 toca e NÃO reinicia** | a **rotina** do TITULO é inocente → a causa é a **chamada do `get_path` da ViewTask** (o banco/FatFs pelo lado da view) |
| **B0 reinicia** | a causa está na **própria rotina** (o ponteiro do contexto, o `lv_img_set_src`, o quadro/uso de `sp`) → e o `get_path` nem chega a ser chamado |

**Testes:** `tests/test_diag_trava.py` — **28 testes, verdes** (os 26 da
ficha 008 + `test_14c_get_path_ja_patcheado` (o B0 já patcheado é
recusado) + `test_24_b0_rotina_ativa_sem_get_path` (no arnés de emulação: a
sequência é **exatamente** `label_set_text` + `img_set_src` do quadrado
cinza, **zero** `get_path`, zero `calloc`/`free`/`f_open`)). `sh tools/ci.sh`
verde (`CI OK`).

---

# Proposta de correção (curta) — **NÃO implementada**

**A ideia:** o caminho tem de ser obtido **onde a fábrica o obtém** — na
MainTask/presenter — e **viajado junto com a mensagem do título**, em vez de
a ViewTask abrir o banco. O caminho da faixa atual **já existe** na
fábrica: o presenter `0x00D08448` monta a mensagem do título; o caminho pode
ser pego com o mesmo `get_path` (`0x00CFF0A8`, que já devolve o caminho
num buffer de 255 B) e anexado à mensagem. A ViewTask passa a receber o
caminho pronto e nunca toca no banco nem no FatFs.

**O que muda:** (1) o presenter anexa o caminho à mensagem do título; (2) o
`TITULO` da RC7 usa o caminho que veio na mensagem em vez de chamar o
`get_path`; (3) o `carrega_capa` continua na ViewTask (ele **precisa** do
arquivo do usuário) — então a ViewTask ainda abre arquivo, mas **não o
banco**: o `get_path` (que abre `db_audio.db`/`db_artist.db` e usa o mutex
do banco) deixa de rodar na view.

**Riscos:**
- a mensagem do título grows (o caminho tem até 255 B): o ring da view tem
  um limite — **é preciso medir** (a ficha 008 mediu `0x414` B como o
  maior payload de título; somar 255 B pode estourar o ring, que é
  justamente o bug B5);
- o caminho anexado pode **envelhecer**: se o índice mudar entre o
  presenter e a view, o caminho é da faixa errada (mitigável: o presenter
  anexa o índice junto, e a view compara);
- mexer no **formato da mensagem** é mexer no contrato entre presenter e
  view — o maior risco desta linha;
- `f_open`/JPEG na ViewTask **nunca rodaram no aparelho** (o degrau B e o
  C provaram que o `get_path` sozinho já reinicia; o `f_open` do MP3 nunca
  foi testado no aparelho). Continua sem prova.

**Alternativa mais barata (se o B0 mostrar que é a chamada do `get_path`):**
fazer o `get_path` rodar **na MainTask** e guardar o resultado num global
(uma struct com o caminho), como a própria fábrica já faz em
`0x00CFF0A8`; a ViewTask só lê o global. É menos invasivo (não muda o
formato da mensagem), mas tem uma janela (o caminho global pode ser do
índice errado se duas faixas trocarem rápido) — a mesma ressalva do item 2.

**O que o aparelho ainda precisa provar (nada disso fecha por estática):**
1. se o **B0** toca sem reiniciar (separa a rotina do `get_path`);
2. se o **C** (que abre o MP3 de verdade) reinicia — o `f_open` do MP3 na
   ViewTask nunca rodou no aparelho;
3. o **prazo e a ação do watchdog** (só o aparelho, ou um log do driver);
4. se um **fault** (e não um travamento) é mesmo o que produz o reinício —
   o handler ativo (`0x00804C90`) não está no dump;
5. se o `free(NULL)` (achado H5 da 008) tolera `NULL` — o heap está na
   mask ROM.

---

# O que NÃO foi feito (de propósito)

- **Nada foi gravado no aparelho**, nenhum USB aberto, nenhum `git push`,
  nenhum merge.
- `firmware/ORIGINAL/`, `tools/ci.sh` e os arquivos listados em
  `tests/PROTEGIDOS.sha256` **não foram tocados** (o `ci.sh` confere).
- Nenhum código das linhas **Core/Alphas** foi usado: só a fábrica e o
  código do **Reload (RC6/RC7)** deste repositório.
- Nada foi escrito abaixo de `0x00E000`, no setor `0x00D000` ou na PSMP.
- A **correção não foi implementada**: ela depende da resposta do decisor
  (e do resultado do B0 no aparelho).

---

# Conferência da coordenação (leitura direta do ORIGINAL)

Refaz por desmontagem as afirmações de que a conclusão depende. Mapa usado: os 4 KiB carregados em RAM têm
**RAM `0x804C00` = arquivo `0xE430`** (a tabela de vetores em `0xE030` ocupa 0x400 B antes deles), não
`0xE030`. Com esse mapa, Reset (`0x804C40`, arquivo `0xE470`) e o handler (`0x804C90`, arquivo `0xE4C0`)
desmontam em código coerente. O engano do mapa causou os erros C1 e C2.

## C1. Fault reinicia o aparelho (CONFIRMADO; a análise dizia "não dá para saber")

O handler ativo **está no dump**. `0x804C90`: `cpsid f; tst lr,#4; mrs r0,msp/psp; stmdb r0!,{r4-r11};
mov r1,lr; bl 0xCF5734`. O `bl` só "caía numa tabela" (1.2) porque foi calculado com endereço de XIP.

`0xCF5734` imprime o estado ("thread:%s", "exception:%d happen", "hard fault happen, HFSR", etc.) e termina em:

```
00CF5908  movs r1,#0 ; mov r0,r1
00CF590C  bl 0xCF6634        ; acerta o registrador 0x4D do PMU
00CF5910  bl 0x80CF9E        ; REINICIA
00CF5914  b  0xCF5914
```

`0x80CF9E` é a rotina de reinício da própria fábrica: em `0xCF9D4E` a string `"-update set pc and restart ...."`
vem logo antes de `b.w 0x80CF9E`. O app reinicia por ela, e não pelo `NVIC_SystemReset`, o que torna a seção 1.3 irrelevante.

## C2. O watchdog é alimentado pela MainTask (CONFIRMADO; a análise dizia o contrário)

A entrada do monitor é `0xD46B14` (`ldr r2,=0x81D120`), um `ldr` antes do `0xD46B16` que a análise varreu.
Ela **tem chamador**, no laço principal da mesma função que abre `/dev/wdog` (`0xCF7EAA`) e foi criada como
MainTask em `0xCF8078`:

```
00CF7EC0  bl 0xD7DADE        ; espera o próximo comando (timeout -1)
...
00CF7FBE  bl 0xD46B14        ; comando de timer -> monitor -> refresh do watchdog
```

Logo: **se a MainTask parar, o watchdog deixa de ser alimentado.** Prazo e ação na expiração seguem fora do
dump (reinício é o PROVÁVEL). **Cai a conclusão "travamento puro congela, logo o B não é deadlock"** (1.4, 1.6 e
itens 2 e 5 do veredito). "Reiniciou" não separa fault de travamento: **os dois caminhos reiniciam**.

## C3. A causa principal volta a ser o ring da view (HIPÓTESE principal, gatilho não provado)

Cada elo, com a classificação própria:

1. **CONFIRMADO, desmontado de novo:** `0xCF83E4` pega o mutex `0x81BBCC` (`0xCF83FA`). Com o ring cheio, `blo 0xCF8438`
   (`0xCF8408`) → `movs r4,#0` → `0xCF8432` retorna **sem o give** de `0xCF842E`.
2. **PROVÁVEL:** o presenter da MainTask manda a rajada do play por esse caminho (008, B4).
3. **HIPÓTESE:** o `get_path` na ViewTask deixa a view lenta o bastante para o ring encher. Falta medir: capacidade
   do ring, tamanho da rajada, tempo do `get_path`.
4. **HIPÓTESE:** a MainTask fica presa no take seguinte. Falta saber se o mutex é recursivo e qual o timeout do take
   (`0x80DB48`, RAM fora dos 4 KiB).
5. **Por C2:** MainTask presa → watchdog sem alimento → reinício.

Isso explica o que o decisor viu na RC7 ("às vezes abre o player, mas não toca"): a tela vive e a tarefa que
toca está parada. Não é prova. **Fault dentro do `get_path` chamado pela ViewTask segue possível** (C1).

## C4. Outras correções

- **"A única diferença é a tarefa" (veredito, item 4): rebaixado a PROVÁVEL.** Os valores de origem e índice
  no instante da chamada não foram observados, e o tempo que a view fica ocupada também muda.
- **Pilha em palavras (3.1): rebaixado a PROVÁVEL.** `xTaskCreate` está na ROM, e o argumento depende de a
  MainTask rodar esse caminho. O resultado é coerente com o FreeRTOS, mas não é leitura direta.
- **"O B e o C provaram que o get_path sozinho já reinicia" (proposta, riscos): falso.** O C não foi gravado, e o B
  liga a rotina junto com o `get_path`; separar os dois é a razão do B0.
- **`udiv` na fábrica: CONFIRMADO** (`0xD087F2`, `b6fb f2f3`; 1064 na FIRM pela varredura da coordenação).
  A premissa da 007 estava errada. `tests/test_rc7_trava.py` continua válido, mas o motivo escrito no cabeçalho não.
- **A base do `tbb` (2.1) está certa** (`0xCFEFEE + 4`); o motivo está mal escrito: é a regra PC+4 do Thumb-2.

## C5. O que muda na proposta de correção

- **Pôr o trabalho lento na MainTask é perigoso:** ela alimenta o watchdog (C2). O `get_path` rápido a fábrica já
  faz lá; a decodificação de JPEG não pode ir para lá sem medir o tempo.
- **Entra a correção do bug do ring** (soltar o mutex quando estiver cheio). A decidir: descartar a mensagem ou
  esperar e tentar de novo. Descartar pode perder uma atualização de tela; esperar segura a MainTask.
- **Próximo degrau depois do B0, se ele tocar:** B + bug do ring corrigido. Se tocar, o elo fica provado.

## Conferência da imagem B0 (refeita de forma independente)

Reconstruída pela receita: RC7 `3af97713…`, B0 `63afb46a…`. Diferença entre as duas: **só `0x1AA14C..D`**
(`e0 47` → `00 20`). Payload do `.up` igual à imagem, salvo os 15 bytes de carimbo e etapa. Abaixo de `0xE000` e setor
`0xD000` iguais ao ORIGINAL. `sh tools/ci.sh`: CI OK. **O B0 segue válido**: nenhum dos erros acima o afeta.
No `TESTAR.txt`, a volta de segurança apontava para a RC7, que é a que reinicia; corrigida para a RC6.

# Resultado no aparelho (decisor, 2026-11-05)

**B0: toca, com o quadrado cinza, sem reiniciar.** CONFIRMADO no aparelho: a rotina do TITULO no caminho de falha
(set_text, leitura da view/ext, memset, `set_src` do cinza) não causa o reinício. B reinicia e B0 não, e os dois só
diferem em: (1) a chamada ao `get_path` na ViewTask; (2) o ramo de sucesso depois dela (comparar e guardar o caminho),
que o B0 não executa. Fica entre esses dois, e (2) é o menos provável por ser um laço limitado sem chamada externa.
Próximo degrau: ficha 010 (B1 = B + bug do ring corrigido).
