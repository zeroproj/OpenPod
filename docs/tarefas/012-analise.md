# Ficha 012 — análise (B4: o caminho da MainTask)

Só leitura do ORIGINAL (`b7cd5eb9…`) e da RC7 (`3af97713…`); XIP =
offset + `0xC00000`. Cada afirmação traz o endereço e a instrução que a
sustenta. **Decisão do orquestrador (vence o plano anterior):** a
mensagem do caminho (classe 3, **tipo 5**) é o gatilho da capa; o TITULO
volta a fazer só o `set_text` da fábrica. **Não** há troca de `bl` nem
índice.

## Q1 — o que é o texto do rótulo 2

- **CONFIRMADO** — `page4_media_cb` é `0xD088B4`; registrado em `0xD0E8F8`
  (guarda o cb em `0x0081CDE0`) e chamado em `0xD0EEE8` com
  `add.w r0,r4,#8; blx r3`. O callback lê `[r0]` (`0xD088B6`) e
  `[r0+0x14]` (`0xD088D4`). A mensagem do `0xD084F8` grava o texto em
  `msg+0x14` (`0xD084C4`); logo o callback recebe `r0 = msg` e o `r4` do
  chamador é o evento 8 bytes antes (`r4+8 = msg`). **Correção** do
  registro anterior (`evento = msg+8`): o texto lido é `msg+0x14`, não
  `msg+0x1C`.
- **CONFIRMADO** — `0xD084F8` monta a mensagem em `0x008238F1`: `msg[0]=4`
  (`0xD0849A`), `msg[2]=3` (`0xD0849E`), `msg[4]=2` (`0xD084A4`), `msg[6]=3`
  (`0xD084A2`), copia o texto para `msg+0x14` (`0xD084C4`), põe o strlen em
  `msg+0x10` (`0xD084D0`) e envia por `0xD0D818` (`0xD084D8`).
- **CONFIRMADO** — o rótulo 2 é a **letra** (`[view+8]`, 118×60 em y45,
  `007-rc7-capa-album.md` A4/A5/A6), não o caminho: no aparelho o texto não
  começa com `0:/` nem `0:\` (ficha 011, resultado do B3).
- **HIPÓTESE** — o texto é o nome da faixa/pasta que a MainTask monta; não é
  o caminho completo.

## Q2 — o caminho que a MainTask já calcula

- **CONFIRMADO** — `0xCFF2A4` é `b.w 0xCFF0A8`; `0xCFF0A8` aloca `0xFF`
  (`0xCF780C`), chama `get_path 0xCFEFC4` com `r0=[0x81BC84]` (origem),
  `r1=[0x81BC84+0x20]` (índice), `r2=buf` (`0xCFF0BA`..`0xCFF0C0`), chama o
  like getter `0xD6DB90` (`0xCFF0CC`), grava `[0x81BC84+0x14]`
  (`0xCFF0DC`) e libera o buffer (`0xCFF0E0`). Não sobra ponteiro.
- **CONFIRMADO** — roda na **ViewTask** (a tarefa do `page4_media_cb`).
  Antes do título em `0xD088E8` (rajada `0xD088DC`) e em `0xD089A0`
  (rajada `0xD0896C`); **depois** do título em `0xD08BE2` (rajada
  `0xD08BEA`) e em `0xD09014` (rajada `0xD09028`); e no próprio handler
  `0xD0EED0` (rajada `0xD0EED0` → `0xD0EED4`), que também chama o
  `page4_media_cb` em `0xD0EEE8`. Os retornos são `0xD088E0`, `0xD08970`,
  `0xD08BEE`, `0xD0902C` e `0xD0EED4` (o lr salvo pela rajada em
  `[sp+0x14]`).
- **CONFIRMADO** — a rajada também é chamada fora da ViewTask:
  `0xCFF20E` (`0xCFF1FC`, a **MediaTask**; retorno `0xCFF212`) e
  `0xD00C24` (`0xD00C00`, a **MainTask**/APP; retorno `0xD00C28`). A
  mensagem em `0x008238F1` é o buffer global dos construtores de rótulo da
  ViewTask; enviar o tipo 5 dessas duas tarefas corromperia o buffer. Por
  isso o `envia_path` só envia quando o lr salvo está na tabela acima; nas
  outras ele pula a mensagem (e o `0xD0D880`) e mantém o like getter.
- **CONFIRMADO** — a fábrica termina a mensagem de rótulo com
  `b.w 0xD0D880` depois do `0xD0D818`: em `0xD084E6` (builder `0xD084C8`,
  depois do `free` em `0xD084DC`) e em `0xD08552` (builder `0xD08540`).
  `0xD0D880` (`pstr_send_msg_to_view`) monta a notificação
  `0x20B`/`6` em `sp+4`, chama `0xCFE708` e `0x816DB2`; **não usa o r0 de
  entrada**. O B4 chama `0xD0D881` depois do `0xD0D818`, como a fábrica.
- **CONFIRMADO** — `get_path` devolve `0:/…` ou `0:\…`: o B3 no aparelho e
  os testes usam esses prefixos, e `0xCFF0C4 cmp r0,#1` valida o retorno.

## Q3 — como entregar à view

- **CONFIRMADO** — a fila copia a mensagem: `0xD0D818` → `0xCF83E4` →
  `0xD6AA72`, que grava o header `0x55AA` + tamanho e o payload. Ponteiro
  para buffer que a ViewTask libera não é problema.
- **CONFIRMADO** — o layout da mensagem: classe em `msg+6`, tipo em `msg+4`,
  texto em `msg+0x14`, tamanho em `msg+0x10`. `page_music_play_label_process`
  `0xD32204` lê `msg+6` (3=rótulo, 4=barra); na classe 3 lê `msg+4`,
  `cmp #4; bhi 0xD322A0` (`0xD3223E`), `tbb` em `0xD32242` (tabela
  `0xD32246` = `03 0e 10 12 14 00`); tipos 0..4 escolhem `[view+0]`,
  `[view+4]`, `[view+8]`, `[view+0x14]`, `[view+0x18]`; o comum `0xD3224E`
  faz `set_text` com `msg+0x14` se `msg+0x10 != 0`.
- **CONFIRMADO** — o TITULO é `0xDAA0E6` (thunk `0xDAA014`→`0xDAA020`):
  `set_text` real em `0xDAA0F4` (12 B, termina em `0xDAA0FE`); guarda
  `r4 == [r6+4]` em `0xDAA114`; ext = `[r6+0x30]`; `memset ext+0x110` em
  `0xDAA120`; `get_path` em `0xDAA144`; `strcmp ext+0x110 vs ext+0x10` em
  `0xDAA152`; se diferente, `strcpy` em `0xDAA162`, cinza em `0xDAA174`,
  `carrega_capa` em `0xDAA188`; falha do `get_path` → cinza em `0xDAA1BE`;
  epílogo em `0xDAA1D0` (`add sp,#4; pop.w {r4..pc}`).
- **CONFIRMADO (mecanismo escolhido)** — mensagem **classe 3, tipo 5**,
  texto = caminho (ou vazio), enviada pela rajada logo depois do `get_path`,
  pela mesma infra `0xD0D818`. A view, no tratamento do tipo 5, copia o
  texto para `ext+0x110`, valida com as guardas do B3 e aplica na imagem:
  válido → `img_set_src(img, NULL)` (sem quadrado); inválido/vazio → cinza
  (`0xDA8000`). O TITULO faz **só** o `set_text` da fábrica: o patch em
  `0xDAA0FE` (`b.w 0xDAA1D0`) pula o `memset`, o `get_path`, o `strcmp`, o
  `strcpy`, o cinza e o `carrega_capa`. `carrega_capa` continua cortado
  (`0xDAA188` = `movs r0,#0 + nop`, como no B3).
- **CONFIRMADO (por que a ordem deixa de importar)** — nos fluxos ruins
  (`0xD08BE2`, `0xD09014`) o título chega antes da rajada; como o título só
  faz `set_text`, a capa é atualizada logo depois, quando o tipo 5 chega.
  Se o `get_path` falhar, a rajada envia a mensagem com texto vazio → cinza.
  A transitória “capa anterior até o tipo 5 chegar” é decisão aceita.

## Q4 — ordem e faixa anterior

- **CONFIRMADO** — nos fluxos `0xD08BE2`/`0xD09014` o título é enfileirado
  antes da rajada. Sem reordenar, a capa só muda quando o tipo 5 chega; a
  faixa anterior pode aparecer por um instante, mas é substituída pelo
  caminho da faixa atual (ou pelo cinza, se vazio/inválido).
- **CONFIRMADO** — o tipo 5 não tem rótulo associado: ele não muda o texto
  da tela. Se o caminho não chegar, a view não aplica nada; o cinza só
  aparece quando a rajada envia a mensagem vazia (falha do `get_path`) ou
  quando o caminho é inválido.
- **PONTO DE VERIFICAÇÃO** — a view, o `ext` e o `img` podem ser NULL; o
  dispatcher guarda todos com `cbz` e descarta. A página do player tem de
  estar ativa: o dispatcher compara `[[0x81CE2C]+0xAC]` com a view do
  processo e exige `[view+4]` (título) não nulo; senão descarta.

## Revisão do orquestrador (B4): bits Thumb, 0xD0D880 e tarefas

- **CRÍTICO corrigido — bit Thumb em todo `bx`/`blx` indireto.** No
  Cortex-M, `bx`/`blx` com bit0=0 gera UsageFault INVSTATE e reinicia. O
  B4 tinha os 9 destinos indiretos pares (`0xD3224E`, `0xD5D868`,
  `0xD322A0`, `0xBAA`, `0xD9FD54`, `0xAA2`, `0xD0D818`, `0xD6DB90`,
  `0xCFF0DE`). Agora todos levam `|1`: `0xD3224F`, `0xD5D869`,
  `0xD322A1`, `0xBAB`, `0xD9FD55`, `0xAA3`, `0xD0D819`, `0xD6DB91`,
  `0xCFF0DF` (e o novo `0xD0D881`). A RC7 é a referência: em `0xDAA17C`
  o `img_set_src` já é `0xD5D869` (`4df6690cc0f2d50ce047`).
- **Por que o emulador não pegou.** O Unicorn não levanta INVSTATE para
  `bx`/`blx` par e o gancho de bloco normaliza o endereço (o `blx
  0xD5D869` chega como bloco `0xD5D868`), então o alvo par executava
  igual. O `tests/emu_rc7.py` é protegido e não pode ser alterado; a
  trava virou o teste estático **71** (`test_71_bit_thumb_nos_indiretos`),
  que decodifica o blob B4, o B3 e o `0xDAA17C` da RC7 e falha se algum
  `movw`/`movt` usado por `bx`/`blx` tiver destino par.
- **MÉDIO corrigido — 0xD0D880.** A fábrica termina a mensagem de rótulo
  com `b.w 0xD0D880` (`0xD084E6` e `0xD08552`, depois do `0xD0D818`); o
  `envia_path` agora chama `0xD0D881` depois do `0xD0D819`, no caminho
  da ViewTask.
- **MÉDIO corrigido — tarefas dos callers.** A rajada `0xCFF0A8` é
  chamada pela ViewTask (`0xD088E0`, `0xD08970`, `0xD08BEE`, `0xD0902C`,
  `0xD0EED4`), pela MediaTask (`0xCFF212`) e pela MainTask/APP
  (`0xD00C28`). O `envia_path` compara o lr salvo em `[r7+0x14]` com a
  tabela dos cinco retornos da ViewTask; nas outras tarefas não toca o
  buffer `0x008238F1` nem chama o `0xD0D880`, mas mantém o like getter
  `0xD6DB90` (comportamento original da rajada). O teste **72**
  (`test_72_envia_path_guarda`) exercita os cinco retornos e os dois
  callers de fora no emulador.

## Revisão GLM (B4): o bit0 do lr salvo

- **MÉDIA corrigida — a guarda comparava o lr ímpar com a tabela par.** O
  `bl` do Thumb salva o retorno com bit0=1: a rajada guarda em `[sp+0x14]`
  `0xD088E1`, `0xD08971`, `0xD08BEF`, `0xD0902D`, `0xD0EED5` (e os de
  fora `0xCFF213`, `0xD00C29`). A tabela `chamadores` é par; sem limpar o
  bit0 a guarda nunca batia e o tipo 5 nunca saía (o B4 ficava sem
  efeito). Agora o `envia_path` faz `bic r0, r0, #1` logo depois do
  `ldr r0, [r7, #0x14]`; a tabela continua par.
- **Travas.** O `test_72` escreve os lrs como o hardware (ímpares: os
  cinco da ViewTask e os de fora `0xCFF213`/`0xD00C29`) e exige que só os
  cinco enviem; sem o `bic` ele falha. O `confere_blob` exige a sequência
  `ldr r0,[r7,#0x14]` + `bic r0,r0,#1` (`786920f00100`); sem ela o
  `fab_diag_b4.py` recusa.
- **BAIXA corrigida — a tabela em 4 bytes e o tamanho.** O `diag_b4.s`
  tem `.balign 4` antes de `chamadores`; a tabela fica em `0xDAACC4` e o
  `adr` aponta para ela (teste **73**; o `confere_blob` recusa a tabela
  fora de 4). O blob ficou 729 bytes (727 + 4 do `bic`; o `adr` virou o
  de 16 bits); o `build.py:684` está em 731 (o número do `bic`) e o
  `fab_diag_b4.py` confere o `len(cod)` real contra o `BLOB_MAX`.
- **BAIXA registrada — o tipo 5 reaplica o `img_set_src` sempre** (a
  RC7/fábrica só mexia na imagem quando o caminho mudava). É custo, não
  quebra; fica para a ficha de produção (R1+).
- **BAIXA registrada — o terminador do `get_path`.** O `strncpy` assume
  texto NUL-terminado; a fábrica tem o mesmo risco nos construtores de
  rótulo, então não é regressão nova.

## O que não dá para saber só pelo ORIGINAL

- Se a fila da view entrega a mensagem tipo 5 ao `page_music_play_label_process`
  em todos os filtros (o caminho do evento 4 é o mesmo da mensagem do
  rótulo 2, mas não há prova de todos os filtros).
- O texto exato do rótulo 2 (nome da faixa? pasta?) sem captura no aparelho.
- Se a transitória “capa anterior até o tipo 5 chegar” é visível no aparelho
  (depende do tempo da fila; o emulador não roda a ViewTask).

## Resultado do B4 no aparelho (decisor, 2026-11-10)

- Ao dar play, a música **tocou normal**, sem congelar e sem reiniciar.
- No lugar do quadrado cinza apareceu o texto **"No data"**.
- Leitura (coordenação):
  - **CONFIRMADO pelo patch:** no B4, só o tratamento do tipo 5 (`label_dispatch`) mexe na imagem depois de criada. A RC7 cria a imagem com o cinza `0xDA8000` (`0xDAA082`..`0xDAA092`), e o caminho inválido reaplica o mesmo cinza.
  - Logo, a imagem só deixa de ser o cinza pelo ramo de sucesso: `img_set_src(img, NULL)` com caminho começando por `0:/` ou `0:\`.
  - **PROVÁVEL:** o "No data" é o aviso do próprio LVGL 8 ao desenhar uma imagem sem fonte válida.
  - Conclusão **PROVÁVEL forte:** a mensagem tipo 5 chegou à view com um caminho válido.
- Roteiro completo (decisor): trocou de faixa, parou a música, saiu e entrou: **tudo normal**, sem travar nem reiniciar.
