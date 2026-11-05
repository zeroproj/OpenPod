# Ficha 010 — Análise estática: o ring da view, a rajada do play e o bug do mutex

Ficha 010 (tipo Risco), base `privado-completo`. Só leitura do ORIGINAL
(`firmware/ORIGINAL/GN438_original.bin`, sha256 `b7cd5eb9…`) e das imagens
deste degrau. Ferramentas: capstone (desmontagem) + o scanner de `bl`/`b.w`
decodificado à mão + a varredura de literais `ldr rX,[pc,#imm]`.

Cada afirmação leva CONFIRMADO / PROVÁVEL / HIPÓTESE. **CONFIRMADO** traz o
endereço e as instruções desmontadas.

> **LEIA ANTES:** a coordenação conferiu esta análise. A capacidade do ring é **0x3C00 (15360 B)**, não 4096, e a causa
> principal mudou. Vale a seção **Conferência da coordenação**, no fim deste arquivo. O kit B1 fica de reserva.

---

## 0. O que o B1 conserta (o bug) — CONFIRMADO

O envio ao ring da view (`0x00CF83E4`), desmontado byte a byte:

```
00CF83E4  push {r0,r1,r2,r4,r5,r6,r7,lr}
00CF83E6  ldr  r6, [pc, #0x54]     ; 0x00CF843C -> 0x0081BBC0 (o descritor global)
00CF83E8  ldrd r5, r3, [r6, #8]   ; r5 = [0x81BBC8] (o ring), r3 = [0x81BBCC] (o mutex)
00CF83EC  mov  r7, r0              ; a mensagem
00CF83EE  mov  r4, r1              ; o tamanho
00CF83F0  cbnz r3, #0x00CF83F8    ; ja existe mutex? entao nao cria
00CF83F2  bl   0x00CF79F6         ; cria o mutex ("movs r0,#1 ; b.w 0x90C4")
00CF83F6  str  r0, [r6, #0xc]     ; [0x81BBCC] = o handle do mutex
00CF83F8  ldr  r0, [pc, #0x44]    ; 0x00CF8440 -> 0x0081BBCC (o mutex)
00CF83FA  bl   0x0080DB48         ; os_mutex_pend  (o take)
00CF83FE  mov  r0, r5
00CF8400  bl   0x00D6A9EA         ; o espaco livre no ring
00CF8404  adds r3, r4, #4
00CF8406  cmp  r0, r3
00CF8408  blo  #0x00CF8438        ; CHEIO -> caminho de erro
00CF840A  movs r2, #4 / movw r3,#0x55aa / strh [sp,#4] / strh [sp,#6]
00CF841E  bl   0x00D6AA72         ; copia o cabecalho (0x55AA + o tamanho)
00CF8422  mov r2,r4 / mov r1,r7 / mov r0,r5
00CF8428  bl   0x00D6AA72         ; copia a mensagem
00CF842C  ldr  r0, [pc, #0x10]    ; 0x00CF8440 -> 0x0081BBCC (o mutex)
00CF842E  bl   0x0080DB6E         ; os_mutex_give   <-- SO no caminho do SUCESSO
00CF8432  mov  r0, r4             ; devolve o tamanho
00CF8434  add  sp, #0xc
00CF8436  pop  {r4,r5,r6,r7,pc}
00CF8438  movs r4, #0             ; o caminho de erro: r4 = 0
00CF843A  b    #0x00CF8432        ; <-- PULA o give (0x00CF842C..0x00CF8431)
```

O `b` de `0x00CF843A` (`fa e7` = `b 0x00CF8432`, o alvo logo depois do give)
é o **bug da fábrica**: com o ring cheio, a função devolve 0 **sem soltar o
mutex** `0x81BBCC`. O B1 troca esses 2 bytes por `f7 e7` (`b 0x00CF842C`):
o caminho "cheio" passa pelo give e a mensagem é descartada (0).

**CONFIRMADO** — a única chamada do envio é `0x00D0D818` (tail call
`b.w 0x00CF83E4` em `0x00D0D82E`), e `0x00D0D818` tem **199 chamadores**
(varredura de `bl`/`b.w` no dump inteiro), todos na região do presenter
(`0x00D0…0x00D1…`).

---

## 1. Capacidade do ring: onde é criado e com que tamanho

### O que fecha

**CONFIRMADO — o ring é um ring de BYTES**, e o seu objeto é o `+8` do
descritor global `0x81BBC0` (`0x81BBC8`). A biblioteca do ring
(`0x00D6A974`, `0x00D6A98E`, `0x00D6A9EE`, `0x00D6AA2A`) mostra o layout:

```
00D6A974  ldr r3, [r0, #4]   ; o indice de escrita
          ldr r1, [r0]       ; a CAPACIDADE (o modulo)
          ldr r0, [r0, #8]   ; o indice de leitura
          ... (write+1) mod capacidade ...
00D6A98E  ldr r4, [r0]       ; a capacidade
          ldrd r6, r5, [r0,#4]
          cmp r6, r5         ; escrita == leitura -> CHEIO -> 0
          ... free = (cap + leitura - escrita) mod cap ...
00D6A9EE  ldr r3, [r6, #8]   ; o indice de leitura
          ldr r2, [r6, #0xc] ; o ponteiro do buffer de dados
```

**CONFIRMADO — o descritor da fila da view** é montado em `0x00CF8384` e
registrado em `0x00CF7E96` (dentro da inicialização do app, **antes** da
ViewTask ser criada em `0x00CF7EAA`):

```
00CF8384  push {r4,lr} / sub sp,#0x58 / memset(sp,0,0x58)
00CF8386  ldr r3, [pc,#0x48]  ; 0x0081BBC0 (o descritor global)
00CF8390  strb r1, [r3]       ; [0x81BBC0] = 0
00CF8392  str  r1, [r3, #4]   ; [0x81BBC4] = 0
00CF8398  ldr r3, [pc,#0x38]  ; 0x00CF8211  -> desc+0x10 (a funcao da task)
00CF839C  ldr r3, [pc,#0x38]  ; 0x00C499AB  -> desc+0x1C ("ViewTask")
00CF83A0  mov.w r3, #0x1000
00CF83A6  str  r3, [sp, #0x24]   ; desc+0x24 = 4096
00CF83AC  strb.w r3, [sp, #0x54] ; desc+0x54 = 3
00CF83B0  strb.w r4, [sp]        ; desc+0x00 = 1
00CF83B4  strb.w r4, [sp, #0x14] ; desc+0x14 = 1
00CF83B8  bl  0x00D6ACAC         ; registra a fila
```

**CONFIRMADO — o campo `desc+0x24` é um TAMANHO EM BYTES**, provado pelo
outro tipo de descritor (o de `desc+0 == 0`), em que ele é repassado para a
criação do ring:

```
0x00D6ACF4  ldr r2, [r4, #0x24]  ; o tamanho
0x00D6ACF6  str r2, [sp]
0x00D6AD02  bl  0x00CF7AD4       ; a criacao do ring
0x00CF7B06  ldr r2, [sp, #0x28]  ; o mesmo tamanho
0x00CF7B18  uxth r2, r2
0x00CF7B1E  bl  0x008A30         ; a ROM cria o buffer com esse tamanho
```

E os chamadores diretos de `0x00CF7AD4` passam o tamanho do mesmo jeito:
`0x00D1070C` (`mov.w r3,#0x400`) e `0x00D20F4A` (`mov.w r3,#0x200`). Os
outros dois descritores da fábrica usam o mesmo campo com `0x400`
(`0x00CF803E`) e `0x800` (`0x00CF8148`).

### O que NÃO fecha

**NÃO CONFIRMADO (a capacidade exata em bytes).** O descritor da **view**
(`desc+0 == 1`) é criado por outro caminho (`0x00D6AD30` → `0x00CF76EC`),
e `0x00CF76EC` **não lê** `desc+0x24`; o campo de capacidade do ring
(`[ring+0]`, o módulo das operações do ring) é escrito dentro da mask ROM
(fora do dump).

- **PROVÁVEL — 4096 bytes**: é o valor de `desc+0x24` no descritor da view,
  e é o valor que o mesmo campo assume (em bytes) nos outros dois
  descritores da fábrica e nos chamadores diretos de `0x00CF7AD4`.
- **HIPÓTESE — a capacidade real é menor que 4096**: só o aparelho (ou um
  log do driver) diz. *Nenhum outro número aparece no dump.*

### O que isso muda na hipótese do ring

O **gatilho** "ring cheio" precisa de **4096 bytes** de mensagens
acumuladas (no pior caso medido abaixo: 2308). Como a rajada do play, sozinha,
**não chega lá** (seção 2), o "ring cheio" exigiria mensagens acumuladas de
fora da rajada enquanto a ViewTask está ocupada com o TITULO da RC7 — ou uma
capacidade menor que 4096.

---

## 2. Quantas mensagens e bytes tem a rajada do play

**CONFIRMADO — a rajada do play são 9 mensagens**, em `page4_media_cb`
(`0x00D088B4`), na sequência `0x00D088D8..0x00D088F8` mais o `b.w` final
para `0x00D085DC`:

| # | quem monta | envia em | o que leva | `[msg+0xA]` | bytes no ring |
|---|---|---|---|---|---|
| 1 | `0x00D084F8` (o caminho do evento) | `0x00D0854A` | o caminho | `strlen+9` | `strlen+25` |
| — | `0x00CFF2A4` → `0x00CFF0A8` | — | **não envia** (é o getter: `malloc(0xFF)` + `get_path` + `0x00D6DB90`) | — | 0 |
| 2 | `0x00D086B0` (o tempo) | `0x00D08730` | string formatada (buffer de 0x14) | `strlen+9` | `strlen+25` (≤ 44) |
| 3 | `0x00D08744` (o outro tempo) | `0x00D087C4` | string formatada (buffer de 0x14) | `strlen+9` | `strlen+25` (≤ 44) |
| 4 | `0x00D08448` (o **TITULO**) | `0x00D084D8` | o caminho (do banco) | `strlen+9` | `strlen+25` (≤ 1048) |
| 5 | `0x00D083C4` (o índice) | `0x00D08432` | string formatada (buffer de 0x14) | `strlen+9` | `strlen+25` (≤ 44) |
| 6 | `0x00D08590` | `0x00D085CA` | valor fixo | 4 | 20 |
| 7 | `0x00D08668` | `0x00D086A0` | valor fixo | 4 | 20 |
| 8 | `0x00D08368` | `0x00D083A0` | valor fixo | 4 | 20 |
| 9 | `0x00D085DC` (o `b.w` final) | `0x00D08608` | valor fixo | 4 | 20 |

A conta do "bytes no ring" (CONFIRMADO, pelo mesmo caminho do código):

```
0x00D0D824  ldrh r1, [r4, #0xa]  ; o tamanho da mensagem
0x00D0D828  adds r1, #0xc        ; o que vai para o ring = tamanho + 12
0x00CF8404  adds r3, r4, #4      ; o ring precisa de (tamanho+12) + 4
0x00CF840A  ... o cabecalho de 4 bytes (0x55AA + o tamanho) ...
0x00CF841E  bl 0x00D6AA72        ; + o payload
```

Logo: **bytes no ring = `[msg+0xA] + 16`**.

- **CONFIRMADO — o total**: `2*strlen(caminho) + 3*strlen(string) + 205`.
- **CONFIRMADO — o pior caso**: os caminhos são copiados com
  `strncpy(..., 0x3FF)` (`0x00D084C0`, `0x00D0852E`, `0x00D0841E`) e as
  strings formatadas cabem em 0x14 bytes → **2308 bytes**.
- **PROVÁVEL — o caso típico**: com o caminho de uma faixa real
  (`0:\…\faixa.mp3`, ~30-60 bytes) e as strings curtas (5-11), o total fica
  **~300 bytes**.

**Consequência (a conta, não a medição):** mesmo no pior caso (2308), a
rajada **não enche** um ring de 4096 bytes. A rajada sozinha **não** é o
gatilho — o que corrigido na Conferência: a conclusão aqui estava invertida e usava a capacidade errada.

---

## 3. A quem mais o caminho "ring cheio" afeta

**CONFIRMADO — o mutex `0x81BBCC` é exclusivo do envio ao ring**: o literal
`0x0081BBCC` aparece **uma única vez** no dump inteiro (`0x00CF8440`) e é
usado em três lugares, todos no mesmo caminho: o take (`0x00CF83FA`), o give
(`0x00CF842E`) e o `ldr r6` do começo (`0x00CF83E6`). Não há nenhum outro
`take`/`give` desse mutex.

**CONFIRMADO — o alcance do estrago**: com o mutex preso, **todo** remetente
de mensagem para a view trava no take. São os **199 chamadores** de
`0x00D0D818` (o presenter de todas as telas), não só o presenter do play.
O que para a MainTask (que é quem alimenta o watchdog, `0x00CF7FBE` →
`0x00D46B14`) para o watchdog — e o que o watchdog faz no prazo é
PROVÁVEL (fora do dump, como na 009).

**CONFIRMADO — a LEITURA do ring não pega o mutex**: em `0x00CF8444..0x00CF84CE`
(read) e `0x00CF84D8..` (peek) não há nenhum `bl 0x0080DB48`. O sintoma
clássico é, portanto, "a tela continua viva, mas nada mais atualiza" — e
não um congelamento.

**CONFIRMADO — a ViewTask é serial**: o laço dela é
`0x00D24340`/`0x00D24354`: `bl 0x00CF8444` (read) → `bl 0x00D23E50`
(dispatch) → `bl 0x00D5811C` (free) → repete; e dorme em `0x00D2436E`
(`b.w 0x811700`). Uma mensagem lenta (o TITULO da RC7) segura a **leitura**
do ring: enquanto ela roda, o presenter continua escrevendo e o ring
acumula.

**CONFIRMADO — o que o caminho "cheio" devolve**: `0` (`movs r4,#0` em
`0x00CF8438`), e o remetente não distingue "não coube" de "não havia view".

### O que NÃO dá para saber por estática

1. **O timeout do take** (`0x0080DB48`, na mask ROM): se ele devolve erro
   em vez de esperar, o estrago é menor (o remetente perde a mensagem e
   segue). Se ele espera sem limite, a task trava para sempre. **NÃO DÁ
   PARA SABER** — o código está fora do dump.
2. **O prazo e a ação do watchdog** (o driver de `/dev/wdog`): **NÃO DÁ PARA
   SABER** (mask ROM). O reinício é PROVÁVEL (009, seção C2).
3. **A capacidade exata do ring** (seção 1): **NÃO DÁ PARA SABER**; 4096 é
   PROVÁVEL.
4. **Quanto tempo a ViewTask leva por mensagem na RC7** (dezenas de ms no
   TITULO): só medindo no aparelho.
5. **Se o ring chegou a encher no aparelho**: só o aparelho diz.

---

## 4. O B1 (o degrau) e a leitura do resultado

**O B1** = a imagem Diag B (o nível B da 008, que REINICIA o aparelho)
mais **2 bytes** no código da fábrica: o `b` de `0x00CF843A`
(arquivo `0x00F843A`, `fa e7` = `b 0x00CF8432`) vira `f7 e7`
(= `b 0x00CF842C`). A região é de 2 bytes, mas **só o primeiro muda de
valor** (`0xFA` → `0xF7`): o diff efetivo contra o Diag B é de **1 byte**.

| | sha256 |
|---|---|
| Diag B (a entrada do B1) | `952c79fb3e6a4d2bdd2ae477060795ce8ea7e88c8523384bb62e468234844896` |
| imagem B1 (sem carimbo) | `fb0d91dd21bef55b447b01eb3b5560a21a1cb174ad2bc19f1a83e679b402fc8f` |
| imagem B1 carimbada (`RC7 diag B1`, `patch_versao --em 0x1A4F00`) | `ec6d55c69a5305d20ef14858abc775188ca05592bc4f3c822cb4a5bc54f63472` |
| `.up` (`OpenPod_OpenPodReload1.0RC7DiagB1.up`) | `69818727dcb33a3d8d65579e16e1beeecbfbb9f595bab176804493f417992311` |

**CRC do `.up`: `0x71C9`** (conferido: `crc16_ccitt_false` do payload = o
campo; payload = a imagem carimbada byte a byte; cobertura `0x1AB000`;
bootloader e setor `0xD000` intactos; PSMP fora).

### Leitura do resultado no aparelho

| no aparelho | leitura |
|---|---|
| **B1 TOCA (sem reiniciar)** | o **elo do ring está provado**: era o caminho "ring cheio" sem give que travava a MainTask e parava o watchdog. O próximo degrau é o **C + a correção** (a correção final: o caminho "cheio" solta o mutex e a correção do `get_path` na ViewTask) |
| **B1 REINICIA** | o ring **não é a causa, ou não é a única**: o reinício vem de outro caminho (o `get_path` na ViewTask, o `f_open`/`jd_prepare`, um fault). O próximo degrau volta a ser a bisseção do `get_path` (o C) |

O quadrado cinza com a nota é o **esperado** (o B1 mantém o TITULO do Diag B
intacto — só o bug do ring mudou). A **volta de segurança é sempre a RC6**.

---

## 5. O que NÃO foi feito (de propósito)

- **Nada foi gravado no aparelho**, nenhum USB aberto, nenhum `git push`,
  nenhum merge.
- `firmware/ORIGINAL/`, `tools/ci.sh` e os arquivos listados em
  `tests/PROTEGIDOS.sha256` **não foram tocados** (o `ci.sh` confere).
- Nenhum código das linhas **Core/Alphas** foi usado: só a fábrica e o
  código do **Reload (RC6/RC7)** deste repositório.
- Nada foi escrito abaixo de `0x00E000`, no setor `0x00D000` ou na PSMP.
- A **correção final** não foi implementada (ela depende do resultado do
  B1), e `tools/capa_album.s` não foi tocado.

---

# Conferência da coordenação (leitura direta do ORIGINAL)

Imagem B1 refeita pela receita: `fb0d91dd…`, 1 byte de diferença contra o Diag B (`0xF843A`: `fa` → `f7`). Payload do `.up`
igual, salvo os 15 bytes de carimbo e etapa. CI OK. A mudança em `tools/gera_versao.py` não alterava o resultado e foi revertida.

## D1. A capacidade do ring é 15360 B (CONFIRMADO; a análise dizia "4096, PROVÁVEL" e "escrita na ROM")

Na entrada da ViewTask, o ring é criado no próprio firmware:

```
00CF8246  movs r0,#0x14 ; bl 0xD58188   ; aloca o objeto do ring
00CF824E  str  r0,[r4,#8]               ; [0x81BBC8] = o ring
00CF82B4  mov.w r0,#0x3C00
00CF82B8  str  r0,[r5]                  ; [ring+0] = 0x3C00, a capacidade
00CF82BA  bl   0xD58188                 ; aloca o buffer
00CF82C0  str  r0,[r5,#0xC]             ; [ring+0xC] = o buffer
```

`desc+0x24 = 0x1000` é a pilha da tarefa, não o ring. Com 15360 B, a rajada do play (cerca de 300 B, pior caso 2308)
**não enche o ring em segundos**. O bug do ring é real, mas **deixa de ser o gatilho principal**.

## D2. Tarefa monitorada parada corta o watchdog (CONFIRMADO; corrige a 009, seção 1.4)

O refresh **não é incondicional**. A cada comando de timer, o monitor confere as tarefas registradas:

```
00D46B18  ldrd r4,r1,[r2]            ; r4 = registradas, r1 = bateram desde a última vez
00D46B2A  lsr.w r6,r1,r3 ; lsls r6,#0x1f
00D46B30  bpl 0xD46B68               ; registrada e NÃO bateu -> "-task %d is dead" e RETORNA
...
00D46B52  bl  0xD637AA               ; o refresh: nesse caminho, não executa
```

- **A ViewTask é monitorada:** `0xD46BEC` registra a tarefa (string `"-watch monitor register view error !"`).
- **Ela bate uma vez por volta do laço:** `0xCF82A4 bl 0xD46BBC`. Enquanto trata uma mensagem, não bate.
- **A fábrica tira a ViewTask do monitor em dois pontos:** `0xCFCA0E` e `0xCFCBC8`
  (string `"-view_task unregister failed!"`). O motivo não está no código; o `0xCFCA0E` antecede `"ebook_auto_play"`.
- **A MainTask não é registrada:** ela é quem roda o monitor (`0xD46BEC` só registra a 3 e a 9, que a string nomeia
  como view e manager). Por isso a fábrica pode chamar o `get_path` nela sem esse risco.

## D3. Nova causa principal (PROVÁVEL que seja o watchdog; HIPÓTESE o mecanismo exato)

O `get_path` na ViewTask a segura sem bater. Por tempo demais, ou para sempre, o monitor deixa de alimentar o
watchdog e o aparelho reinicia. Não usa o ring. Encaixa em A toca, B0 toca e B reinicia.

Falta saber: o período do comando de timer e o prazo do watchdog (fora do dump; `0xD46AAA` passa `0x14` ao abrir
`/dev/wdog`, e o significado é HIPÓTESE), e se o `get_path` é só lento ou não retorna nunca.

## D4. Próximo degrau: B2, no lugar do B1

**B2 = Diag B + 2 bytes:** arquivo `0x146B30`: `1a d5` (`bpl`) vira `00 bf` (`nop`). O monitor passa a tratar toda tarefa
como viva e o watchdog é sempre alimentado. Uma gravação separa as três possibilidades:

| B2 no aparelho | Leitura | Caminho |
|---|---|---|
| **Toca** | O `get_path` só é lento | Tirar a ViewTask do monitor durante o trabalho, como a fábrica faz, ou obter o caminho na MainTask |
| **Congela, sem reiniciar** | O `get_path` não retorna na ViewTask | Obter o caminho na MainTask |
| **Reinicia** | Fault de verdade (C1 da 009), não watchdog | Procurar a falha no caminho do `get_path` |

Sem watchdog, um congelamento só sai pelo botão de reset. Por isso o B2 é só diagnóstico: esse patch nunca entra na versão final.
O kit B1 fica de reserva.
