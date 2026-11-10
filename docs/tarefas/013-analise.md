# Ficha 013 — análise (B5a/B5b: abrir a capa no tipo 5)

Só leitura do ORIGINAL (`b7cd5eb9…`), da RC7 (`3af97713…`) e do B4
(`39bea488…`); XIP = offset + `0xC00000`. Cada afirmação traz o endereço e
a instrução que a sustenta. **Decisão:** o tipo 5 é tratado na **ViewTask**,
não na rajada da PreTask. O B5a só abre o MP3 e olha o ID3; o B5b chama
`carrega_capa` com o monitor da ViewTask desligado. O `envia_path` do B4
continua, agora em `+0x500`.

## Q1 — onde a rajada e o `label_process` rodam

- **CONFIRMADO — a rajada roda na PreTask.** `0xD0EED0 bl 0xCFF2A4` está
  em `0xD0ED0C`; `0xCF8124 bl 0xD0ED0C` está no loop da PreTask. O handler
  `0xCF8101` é registrado em `0xCF812C`/`0xCF813A`/`0xCF813E` com o nome
  “PreTask”, fila “MgrTaskQue” e pilha `0x800`.
- **CONFIRMADO — o `page4_media_cb` também roda na PreTask.** Ele é
  `0xD088B4`, registrado em `0xD0E8F8` (guarda em `0x0081CDE0`) e chamado
  em `0xD0EEE8` com `add.w r0,r4,#8; blx r3`, dentro de `0xD0ED0C`. Logo o
  callback e a rajada estão na mesma tarefa.
- **CONFIRMADO — o `label_process` roda na ViewTask.** A ViewTask tem corpo
  em `0xCF8210`, entrada Thumb `0xCF8211`, nome em `0xC499AB`, pilha
  `0x1000` e registro em `0xCF8398`/`0xCF839C`/`0xCF83A0`. O loop
  `0xD24340`/`0xD24354` faz `bl 0xCF8444` (read), `bl 0xD23E50`
  (dispatch), `bl 0xD5811C` (free) e dorme em `0xD2436E`
  (`b.w 0x811700`). O `label_process 0xD32204` é chamado por esse
  dispatch.
- **CONFIRMADO — o tipo 5 do B4 entra no `label_process`.** O B4 troca
  `0x0013223E` por `cmp r3,#5` e `0x00132242` por `bl label_dispatch`
  (`0xDAAA00`). O `label_process` lê `[0x81CE2C]+0xAC` (view da página 4),
  compara com `r5` e exige `[view+4]` (título) não nulo.
- **CORREÇÃO da 012:** a rajada `0xCFF0A8` **não** roda na ViewTask. A 012
  afirmou ViewTask; a desmontagem mostra PreTask em `0xD0ED0C` e no loop
  `0xCF8124`. A ViewTask é a tarefa do `label_process`/LVGL.

## Q2 — por que o B travou (e o que o B5 evita)

- **CONFIRMADO — `get_path` pega o mutex do banco.** `0xCFEFC4` não pega o
  mutex no topo; `0xD6D1B4` pega `[0x81DC00]+0x5C` via `0x80DB48`, chama
  `0xD6F138`, e solta via `0x80DB6E`. `0xD6F138` abre
  `0:\DBROOT\db_audio.db` com `0xD777CC`, lê os registros (`0x21E` bytes) e
  fecha com `0xD77C9C`, tudo sob o mutex.
- **CONFIRMADO — o like getter também pega o mutex do banco.** O
  `0xD6DB90` usa o mesmo `[0x81DC00]+0x5C`.
- **CONFIRMADO — `f_open` do MP3 não pega o mutex do banco.** O
  `0xD777CC` usa o lock FatFs (`0xD77EA4`/`0xD77EBE`), não
  `[0x81DC00]+0x5C`. Isso é o que permite abrir o MP3 na ViewTask sem
  repetir a contenção do banco.
- **CONFIRMADO — o envio à view não espera a view.** `0xD0D880`
  (`pstr_send_msg_to_view`) chama `0xD6AE38(2)`, `0xCFE708` e `0x816DB2`;
  não há espera pela ViewTask.
- **PROVÁVEL — a trava do B é contenção no mutex do banco.** A ViewTask
  chama `get_path` (banco) e a PreTask chama o like getter (banco). O B2
  congelou ~15 s e reiniciou mesmo com o monitor neutralizado, o que aponta
  para a MainTask parando de alimentar o watchdog (`0xCF7FBE` →
  `0xD46B14`), mas a ordem exata dos waits não está provada.
- **HIPÓTESE / LIMITE — não dá para provar o “quem espera quem”.** O
  `os_mutex_pend/give` em `0x80DB48`/`0x80DB6E` está na mask ROM, fora do
  dump. O B5 não depende de saber isso: ele tira a abertura do banco da
  ViewTask (B5a) e, no B5b, desliga o monitor durante o `carrega_capa`.
- **RISCO — o `f_open` do MP3 ainda pega o lock FatFs.** Se a trava real for
  no FatFs (e não no banco), o B5b pode repetir o congelamento. É por isso
  que o B5a existe: ele separa “abrir/ler 10 bytes” de “decodificar”.

## Q3 — onde abrir a capa

- **CONFIRMADO — a opção de abrir na rajada da PreTask não serve.** A
  rajada roda na PreTask (`0xD0ED0C`), não na ViewTask; abrir ali não coloca
  o `f_open` no contexto da view.
- **CONFIRMADO — o tipo 5 roda na ViewTask.** É o mesmo contexto do
  `label_process` e do `carrega_capa`; é o lugar em que o B4 já aplica a
  imagem.
- **DECISÃO — B5a/B5b no tipo 5, na ViewTask.** O B5a só abre o MP3 e lê
  10 bytes; não toca no monitor. O B5b compara o caminho com `ext+0x10`,
  pinta cinza, desliga o monitor, chama `carrega_capa(ext)`, religa o
  monitor e, no sucesso, faz `img_set_src(img, ext)`.
- **CONFIRMADO — contrato do `carrega_capa` (`0xDAA256`).** Recebe
  `r0=ext`; caminho em `ext+0x110`; pixels em `ext+0x210`; devolve `1` no
  sucesso. O `ext+0x10` guarda o último caminho. No sucesso o chamador faz
  `img_set_src(img, ext)`; na falha, cinza `0xDA8000`.
- **CONFIRMADO — o B5b pode chamar a função intacta do B4.** O B4 só corta
  a chamada em `0x001AA188` (`movs r0,#0 + nop`); a função em `0xDAA256`
  continua inteira.
- **DECISÃO — o B5b é o primeiro a ir ao aparelho.** Se ele congelar ou
  reiniciar, o B5a separa “abrir” de “decodificar”. Se o B5a também
  congelar, o problema não é o decode; vira `ESCALADA-013`.

## Q4 — monitor, tempo e restauração

- **CONFIRMADO — o monitor da ViewTask é desligado/religado pela fábrica.**
  `0xCFCA08 movs r0,#3; bl 0xD6AE38; 0xCFCA0E bl 0xD46ACC` desregistra a
  ViewTask; `0xD46BEC` registra o manager (id 9) e a view (id 3) via
  `0xD46A20(descritor+0x50)`. `0xD46A20` recebe ponteiro para o id;
  `0xD46ACC` recebe o descritor.
- **CONFIRMADO — o B5b usa o mesmo par.** `0xD6AE38(3)` devolve o
  descritor; `0xD46ACC(descritor)` desregistra; `0xD46A20(descritor+0x50)`
  registra. O B5b só registra de volta se o unregister deu certo; em todos
  os caminhos de erro a imagem fica no cinza.
- **PROVÁVEL — o monitor é o que reinicia o aparelho no B.** O período
  exato é desconhecido (`0x14` em `0xD46AAA`); o B2 mostra que neutralizar
  o monitor não impediu o reinício, então o watchdog também depende da
  MainTask alimentar `0xD46B14`.
- **HIPÓTESE / A MEDIR — o tempo do `carrega_capa`.** Não há prova
  estática de que 500×500 e 1000×1000 terminem dentro do prazo do monitor.
  O B5b desliga o monitor durante o decode; o B5a mede o `f_open` sem o
  decode. O tempo real tem de ser medido no aparelho.

## Implementação (B5a/B5b)

- **B5a (`0xDAAA00`)** — guardas (`[0x81CE2C]`, `[+0xAC] == view`,
  `[view+4]`, `[view+0x30]`, `[ext+0xC]`, texto); copia o caminho para
  `ext+0x110`; valida `"0:"` + `/` ou `\`, não vazio, até `0xFF`; abre com
  `f_open` modo 1, lê 10 bytes, fecha e libera. Se o cabeçalho começa com
  `"ID3"` → `img_set_src(img, NULL)`; qualquer falha → cinza `0xDA8000`.
  Não desregistra o monitor: se o `f_open` travar, o watchdog reinicia.
- **B5b (`0xDAAC00`)** — as mesmas guardas e validação; compara
  `ext+0x110` com `ext+0x10`; igual → não faz nada; diferente → copia para
  `ext+0x10`, cinza, desregistra a ViewTask, chama `carrega_capa(ext)`,
  registra de volta e, no sucesso, `img_set_src(img, ext)`; falha → cinza.
- **`envia_path` (`0xDAAF00`)** — a mesma rotina do B4, com a guarda do lr
  ímpar (`bic r0,r0,#1`) e a tabela dos cinco chamadores da ViewTask.
- **Layout** — blob em `0x001AAA00` (XIP `0xDAAA00`), B5a em `+0x000`,
  B5b em `+0x200`, `envia_path` em `+0x500`, limite `0x600`
  (`0x1AAA00..0x1AB000`). B5a cabe em `<0x200`; B5b em `<0x300`
  relativo ao seu início; `envia_path` tem ~`0xDB` e termina em ~`0x5DB`.
- **Patch contra o B4** — `0x00132242` (4 B) vira `bl` para o B5a/B5b;
  `0x000FF0C4` (12 B) vira `bl envia_path` (`0xDAAF00`) + 4 `nop`; o blob
  inteiro em `0x001AAA00`. `0x0013223E` (`cmp r3,#5`), `0x001AA0FE`
  (`b.w 0xDAA1D0`) e `0x001AA188` (`movs r0,#0 + nop`) continuam do B4.
- **Thumb** — todo `bx`/`blx` indireto leva `|1`; o `CHAMAR` do
  `diag_b5.s` já codifica `alvo+1`. A tabela de chamadores fica
  `4`-alinhada. O teste estático 91 confere o bit; o 92 confere a tabela.
- **Ferramenta** — `tools/fab_diag_b5.py --degrau a|b`, ≤350 linhas;
  confere o sha do B4 (`39bea488…`), os patches do B4, o blob do B4 e a
  área livre antes de escrever; recusa `--out` igual/symlink/hardlink da
  entrada.
- **Receitas** — `reload_1.0_rc7_diag_b5a` e `reload_1.0_rc7_diag_b5b` =
  `RELOAD_1_0_RC7_DIAG_B4` + `fab_diag_b5.py --degrau a|b --em 0x1a8000`.

## O que não dá para saber só pelo ORIGINAL

- Se a trava do B é no mutex do banco ou no FatFs; a mask ROM esconde o
  `os_mutex_pend/give`.
- O prazo real do monitor/watchdog e o tempo de decode de 500×500 e
  1000×1000 no aparelho.
- Se o `lv_task_handler`/LVGL roda na mesma ViewTask do `label_process`
  (o loop da ViewTask foi confirmado; o handler não).
- Se a fila entrega o tipo 5 em todos os filtros da página do player.

## O que o B5a/B5b provam no aparelho

- **B5a:** se o áudio toca e a tela não reinicia, o `f_open`/`f_read` de
  10 bytes não é a trava. Se a capa continua cinza, o problema está no
  decode ou no caminho; se aparece “No data”, o ID3 foi lido.
- **B5b:** se a capa aparece, o `carrega_capa` terminou dentro do prazo e o
  monitor foi restaurado. Se congelar/reiniciar, o B5a separa a abertura do
  decode; se o B5a também falhar, o problema não é o decode.
- **Em todos os casos:** trocar de faixa, parar, sair e entrar têm de
  continuar normais; o monitor tem de voltar em todos os caminhos.

## Resultado do B5b no aparelho (decisor, 2026-11-10)

- **Trava e reinicia:** ao dar play, a tela do player **abre, fica travada e depois reinicia** (mesmo padrão do B2: com o monitor da ViewTask desligado, o reinício vem de outro ponto, provavelmente da MainTask deixando de alimentar o watchdog).
- **Tempo até reiniciar (decisor):** às vezes na hora em que o player abre, às vezes por volta de 24 s.
  - O tempo variável sugere **duas causas possíveis (HIPÓTESE):**
    - Reinício imediato: falha de execução (fault) durante o trabalho da capa, por exemplo pilha da ViewTask (`0x1000`) ou escrita fora do lugar.
    - ~24 s: outra tarefa presa esperando a view, até o watchdog de hardware cortar.
  - Conferido: a ext da RC7 tem `0x2210` B (`0xDAA040`), e o layout dsc/último caminho/caminho/pixels cabe exato.
- Leitura (coordenação): **HIPÓTESE**. A trava acontece dentro do tratamento do tipo 5, no `f_open` ou no decode, com o monitor da ViewTask desligado.
- **Próximo:** o B5a separa as duas causas.
  - Se o B5a também travar, a causa é abrir o arquivo na ViewTask.
  - Se não travar, a causa está no decode.
