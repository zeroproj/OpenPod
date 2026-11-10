# Ficha 012 — revisão (degrau B4)

REPROVADO

Revisor Claude independente (sem cota do Codex — exceção §5, registrada).
Método: leitura da ficha, da 012-análise, de `tools/diag_b4.s`,
`tools/fab_diag_b4.py`, da receita em `tools/build.py` e do TESTAR;
desmontagem própria do ORIGINAL (`b7cd5eb9…`) e da RC7 reproduzida
(`3af97713…`) com `tools/disasm.py`; imagem construída com
`python3 tools/build.py --receita reload_1.0_rc7_diag_b4 --saida tmp_b4.bin`
(sha `d43bebe9…`, apagada depois), diff byte a byte contra a RC7, .up
conferido head a head; `python3 tests/test_diag_trava.py` (61 testes, verde).
Nenhum código, imagem ou kit alterado; só este documento entra no commit.

## O achado que reprova

**[MÉDIA] CONFIRMADO — a guarda do `envia_path` compara o lr salvo (que no
aparelho chega ímpar, com o bit0 de Thumb) com cinco endereços pares; a
guarda nunca bate e a mensagem tipo 5 nunca é enviada. O degrau fica sem
efeito no aparelho (sem fault/reinício, mas a capa nunca é aplicada).**

- O que executa: no blob montado, `0x00DAAC08 7869 ldr r0,[r7,#0x14]`
  (o lr salvo pela rajada), depois `adr r1,chamadores` e o loop
  `0x00DAAC14 9842 cmp r0,r3`. A tabela está em `0x00DAACC2` e foi
  montada com os valores de `tools/diag_b4.s:172`:
  `0x00D088E0, 0x00D08970, 0x00D08BEE, 0x00D0902C, 0x00D0EED4` —
  **todos pares** (li os 5 words do blob).
- Como o lr chega: os cinco chamadores da ViewTask entram na rajada por
  `bl` imediato — `0xD088DC bl 0xCFF2A4`, `0xD0896C bl 0xCFF2A4`,
  `0xD08BEA bl 0xCFF2A4`, `0xD09028 bl 0xCFF2A4`, `0xD0EED0 bl 0xCFF2A4`
  (confirmei os cinco no ORIGINAL; e por varredura de `desvio` no flash
  inteiro, 0xCFF2A4 é o único intermediário: só `0xCFF20E`/MediaTask e
  `0xD00C24`/MainTask chamam 0xCFF0A8 direto). Um `bl` do Thumb-2 salva
  o lr com **bit0=1**. Como `0xCFF2A4 = fff700bf b.w 0xCFF0A8` (rabo, sem
  push, preserva o lr), o valor chega intacto ao
  `0xCFF0A8 37b5 push {r0,r1,r2,r4,r5,lr}`, que guarda o lr em
  `[sp+0x14]` — a matemática de `0x00DAAC04 add r7,sp,#0x18` +
  `[r7,#0x14]` está certa; o que quebra é comparar com entradas pares.
- Consequência: em `[r7+0x14]` chega `0xD088E1 / 0xD08971 / 0xD08BEF /
  0xD0902D / 0xD0EED5` (todos ímpares) e `cmp r0,r3` nunca é igual a
  uma entrada da tabela → às cinco chamadas o `envia_path` cai em
  `4f` (like getter, `0xDAAC9C b 4f` → `blx 0xD6DB91`) → o tipo 5 nunca
  sai → o `img_set_src` nunca é aplicado → com o TITULO reduzido a
  `set_text` (`0x1AA0FE b.w 0xDAA1D0`), a capa fica como estiver
  (faixa anterior ou cinza estático) para sempre. O roteiro do TESTAR
  nunca verá "TOCA sem o quadrado cinza". Quebra de função → reprova.
- Incoerência interna: a própria ficha/RC7-acerto tratou bit0 nos dez
  destinos indiretos (varredura de capstone no blob montado:
  `0x00DAAA12 bx ip 0xD3224F`, `0x00DAAA86 blx ip 0xD5D869`, `0x00DAAA90
  bx ip 0xD322A1`, `0x00DAAC32 blx r3 0x00000BAB`, `0x00DAAC6E blx r3
  0xD9FD55`, `0x00DAAC78 blx r3 0x00000AA3`, `0x00DAAC8E blx r3
  0xD0D819`, `0x00DAAC9A blx r3 0xD0D881`, `0x00DAACAE blx r3 0xD6DB91`,
  `0x00DAACC0 bx ip 0xCFF0DF` — todos ímpares). A mesma regra não foi
  aplicada à TABELA de comparação do lr.
- Por que o teste não pegou: `test_72_envia_path_guarda`
  (tests/test_diag_trava.py:1293) escreve o lr à mão como valor **par**
  (`m.escreve32(sp + 0x14, lr)` com `lr in (0xD088E0, …)`) — essa
  premissa do emulador não corresponde ao hardware (todo `bl` devolve o
  retorno com bit0=1: `0xD088E1`, `0xD0EED5` etc.).
- Correção mínima (R1): comparar por máscara (`lr & ~1` contra a tabela)
  ou montar a tabela com `0xD088E1 / 0xD08971 / 0xD08BEF / 0xD0902D /
  0xD0EED5`; ajustar o `test_72` para escrever os lrs como o hardware
  (bit0=1 nos cinco da ViewTask e também nos de fora: `0xCFF213`,
  `0xD00C29`).
- **Teste de regressão sugerido:** no `confere_blob`, decodificar o
  movw/movt do `envia_path` e exigir bit0=1 nos cinco words da tabela
  (análogo ao que o test_71 faz para os destinos de `bx/blx`); e no
  `test_72`, rodar a guarda com TODOS os lrs ímpares (incluindo os de
  fora).

## Conferências que passaram

- **Patch e diff contra a RC7 (`3af97713…`):** `bl 0x132242 → 0xDAAA00`
  e `bl 0x0FF0C4 → 0xDAAC00` decodificam certo; `b.w 0x1AA0FE →
  0xDAA1D0` certo; `0x0FF0C4..0x0FF0D0 = bl envia_path + 4 nop`. Diff
  B4↔RC7 = 749 bytes, todos dentro dos pontos declarados (0x13223E 2 B;
  0x132242 4 B; 0x0FF0C4 12 B; 0x1AA0FE 4 B; 0x1AA188 4 B; blob
  0x1AAA00..0x1AACD7). Nada abaixo de `0x00E000` (o menor offset
  tocado é `0x0FF0C4`), nada em `0xD000..0xE000`, nada em `0x1FC000+`;
  a captura da fábrica `0x1088D8` (`bl 0xD084F8`) intocada;
  `carrega_capa` cortado em 0x1AA188 (`002000bf` = movs r0,#0 + nop,
  mesmo patch do Diag B aprovado no aparelho).
- **Contrato da rajada (0xCFF0A8).** ORIGINAL:
  `0xCFF0A8 37b5 push {r0,r1,r2,r4,r5,lr}`; ponto patcheado:
  `0xCFF0C4 0128 cmp r0,#1; 0xCFF0C6 0ad1 bne 0xCFF0DE; 0xCFF0C8 01a9
  add r1,sp,#4; 0xCFF0CA 2046 mov r0,r4; 0xCFF0CC bl 0xD6DB90`. O
  `envia_path` reimplanta exatamente: falha → `pop {r4-r8,lr}` +
  `bx 0xCFF0DF` (bit0 faz o aparelho retomar em `0xCFF0DE mov r0,r4`,
  com o `r4` já restaurado) — igual ao `bne`; sucesso → like getter com
  `r0=r4` e `r1=[r7,#4]` (o slot escrito por `0xCFF0BE 0193 str
  r3,[sp,#4]`), e o `r0` volta com o retorno do like getter para o
  resto original da rajada (`0xCFF0D0 mov r2,r0; cbnz r0; ldrb [sp,#4];
  strb r3,[r5,#0x14]` — `r5` intacto pois o `envia_path` não o
  modifica). Frame: `push.w {r4-r8,lr}` (2de9f041) e pop de 6 —
  equilibrado; `ip` é livre.
- **label_dispatch reproduz o tbb de 0xD32242 nos tipos 0..4.** RC7:
  `0xD3223E 042b cmp r3,#4; 0xD32240 2ed8 bhi 0xD322A0; 0xD32242
  dfe803f0 tbb [pc,r3]`, tabela em 0xD32246 = `03 0e 10 12 14 00`.
  Base = 0xD32246: alvos 0xD3224C (`ldr r0,[r5]`), 0xD32262
  (`[r5,#4]`), 0xD32266 (`[r5,#8]`), 0xD3226A (`[r5,#0x14]`),
  0xD3226E (`[r5,#0x18]`), todos caindo no comum `0xD3224E`
  (`38b3 cbz r0` + set_text). A tabela do blob (`00 04 08 14 18`) +
  `ldr r0,[r5,r0]` + `bx 0xD3224F` faz a MESMA seleção e o mesmo
  comum, com `r4`=msg, `r5`=view, `r6`=msg+0x14 preservados (o comum
  lê `r3=[r4,#0x10]`, `r1=r6`). O `bhi` intocado: só o r3==5 entra no
  bloco novo; qualquer outro >5 segue o epílogo `0xD322A0 70bd pop
  {r4,r5,r6,pc}` (lr do chamador do dispatcher devolvido pela própria
  pilha — o `bl 0xD32242` é irrelevante nesse caminho). No caminho
  comum, o `pop.w {r4,r5,r6,lr}; b.w 0xD5ED94` do comum restaura o lr
  original do dispatcher, não o do `bl` do patch.
- **Mensagem tipo 5 byte a byte igual à da fábrica (0xD084F8).**
  ORIGINAL: `0xD084FA movw r2,#0x414; 0xD08500 ldr
  r4,[pool]=0x008238F1; 0xD08508 bl 0xBAA` (memset msg,0,0x414);
  `0xD0850E strb r3,[r4]` (msg[0]=4); `0xD08512 [r4,#2]` (msg[2]=3);
  `0xD08514 [r4,#6]` (msg[6]=3); `0xD08518 [r4,#4]` (tipo — 2 na
  fábrica, 5 no B4); `0xD08526 [r4,#0xc]` (msg+0xC=1, com
  msg[0xD..0xF]=0; o B4 fica igual via memset); `0xD08536 bl 0xD9FD54`
  (strncpy msg+0x14, r2=0x3FF); `0xD0853E bl 0xAA2` (strlen);
  `0xD08542 str r0,[r4,#0x10]`; `0xD08544 adds r0,#9; 0xD08546 strh
  r0,[r4,#0xa]`; `0xD0854A bl 0xD0D818`; `0xD0854E pop.w; 0xD08552
  b.w 0xD0D880`. O B4 monta **identicamente** (blob:
  0x00DAAC26–0x00DAAC4E: memset via `blx 0xBAB`, msg[0]=4 @0xDAAC36,
  msg[2]=3 @0xDAAC3C, msg[4]=5 @0xDAAC42, msg[6]=3 @0xDAAC48,
  msg[0xC]=1 @0xDAAC4E, strncpy 0xD9FD55 com r2=0x3FF, strlen 0xAA3,
  `str [msg+0x10]`, `adds #9`, `strh [msg+0xA]`, send `0xD0D819`). O
  `adds r0,#9`/`strh` é o tamanho que o `0xD0D824 6189 ldrh
  r1,[r4,#0xa]` + `adds r1,#0xc` do send consome — igual à fábrica.
- **0xD0D880 é seguro nesse ponto.** Desmontado: `0xD0D884 movs
  r2,#0x24; 0xD0D890 bl 0xD6AE38; 0xD0D8AA movw r3,#0x20b; 0xD0D8AE
  adf80430 strh.w r3,[sp,#4]` … `0xD0D8CA bl 0x816DB2` — o `r0` de
  entrada **nunca é lido** (`0xD0D888 add r0,sp,#4` o sobrescreve antes
  de qualquer uso) e o frame é próprio (`push {r4,lr}; sub sp,#0x28 …
  add sp,#0x28; pop {r4,pc}`). Na fábrica, os dois construtores de
  rótulo do mesmo contexto chamam 0xD0D880 logo após o 0xD0D818
  (`0xD084E6`/`0xD08552 b.w 0xD0D880`) — mesma ViewTask do
  `envia_path`. Além disso, o like getter `0xD6DB90` é
  `push {r4,r5,r6,lr}`/`pop {r4,r5,r6,pc}` equilibrado, lê somente
  `r0`/`r1` e mutex via `0x80DB48/0x80DB6E` — sem dependência do `r5`
  do chamador.
- **Bit Thumb nos dez destinos indiretos** — verificado por varredura
  de capstone independente no blob montado (lista acima, todos
  ímpares); um deles é o `0xCFF0DF` que retoma em `0xCFF0DE mov r0,r4`
  do epílogo da rajada.
- **Guardas de nulo do tipo 5 — completas, antes de qualquer deref:**
  `[0x81CE2C]`, `[[0x81CE2C]+0xAC]` (nulo ou ≠ r5), `[r5,#4]` (título),
  `[r5,#0x30]` (ext), `[ext,#0xC]` (img) e `r6` (texto) — cinco `cbz` +
  um `cbz r6` (o test_70 exercita os seis no emulador).
- **Escrita restrita:** o copia-copia do tipo 5 escreve **só em
  ext+0x110..ext+0x20F** (loop `6:` com limite `cmp r3,#0xff` e
  terminador em `[r2,#0xFF]`; quando há NUL antes, escreve menos) — a
  mesma faixa que a fábrica usa no TITULO da RC7 (`0xDAA120 add.w
  r0,r7,#0x110` + memset de 0x100). Nada mais no ext.
- **TITULO B4:** `b.w 0xDAA1D0` desvia logo após o `blx 0xD5ED95`
  (set_text) de `0xDAA0FC`; a lógica de capa da RC7 fica morta — sem
  get_path na ViewTask, sem f_open, sem JPEG, como a ficha pede.
- **Kit:** o `.up` = cabeçalho `CONFIG` + payload = primeiros
  0x1AB000 bytes da imagem carimbada (reproduzi
  `patch_versao --em 0x1A4F00 --texto "RC7 diag B4"` sobre tmp_b4.bin —
  sha `5f0e35bd…`, igual ao do TESTAR; sha do `.up` = `74618ccf…`,
  igual ao do TESTAR); CRC `0x8C7B` no cabeçalho (offset 0x0A,
  little-endian `7b8c`); payload termina em 0x1AB000 — PSMP fora;
  TESTAR tem o roteiro certo e a volta de segurança RC6.

## Baixos (não reprova)

**[BAIXA] CONFIRMADO — comentário de tamanho errado em
`tools/build.py:684`:** "código 673 bytes"; o blob real tem **727
bytes** (0x1AAA00..0x1AACD7, com `envia_path` em 0x1AAC00). A área
declarada (0x600, até 0x1AB000) cobre com folga e o teste do MAPA
garante que não cruza lote; nada roda errado — mas o número mente.
Correção: atualizar o comentário (ou derivar do `len(cod)`).

**[BAIXA] CONFIRMADO — o tipo 5 reaplica o `img_set_src` sempre.** Na
RC7/fábrica o TITULO comparava `ext+0x110` vs `ext+0x10` (0xDAA152
`add.w r0/r1`; `bl 0xDAA1D6`; `0xDAA15E cmp r0,#0; 0xDAA160 bne
0xDAA1D0`) e só tocava na imagem quando o caminho mudava. O
`label_dispatch` tipo 5 não compara: cada mensagem re-aplica
`img_set_src`. LVGL tolera (redesenhos repetidos); é custo, não quebra.
Guarda para a ficha de produção (R1+).

**[BAIXA] HIPÓTESE — contrato de terminador do `get_path`.** O
strncpy (de fábrica e do B4) assume texto NUL-terminado no buf;
sem terminador, lixo além do caminho entraria na msg — a fábrica tem o
MESMO risco nos dois construtores de rótulo, logo não é regresso novo;
documentado em `012-analise.md` como "o que não dá para saber".

## Sem achados novos nas áreas que restam

- Fila/filtros (se o tipo 5 chega ao `0xD32204` por todos os caminhos),
  o texto exato do rótulo 2 e a transitória "capa anterior até o tipo 5
  chegar" continuam "não dá para saber" — a análise já os lista, e
  depois do MÉDIO acima o tipo 5 não chega a nem um.
- `ci.sh` verde com os PROTEGIDOS intactos (hashes conferidos pelo
  porteiro); testes de aceite não alterados.

## Síntese

REPROVADO por **um achado MÉDIA**: a tabela da guarda compara o lr salvo
(pares) com o que o hardware entrega (ímpares, bit Thumb do `bl`) — o
tipo 5 nunca é enviado e a capa nunca é aplicada; o degrau B4 fica sem
efeito no aparelho, sem fault. Correção R1 mínima: bit0 na comparação ou
na tabela + `test_72` ajustado + trava no `confere_blob`. Todo o resto —
dez destinos indiretos com bit Thumb, tbb idêntico nos tipos 0..4,
mensagem byte a byte do construtor da fábrica, escrita só em
ext+0x110..ext+0x20F, `0xD0D880` após o send como na fábrica, guardas de
nulos, diff exato de 749 bytes contra a RC7 sem bootloader/0xD000/PSMP,
kit com CRC certo e payload igual à imagem carimbada — conferido e
verde.
