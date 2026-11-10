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
- **CONFIRMADO** — roda na MainTask. Antes do título em `0xD088E8`
  (rajada `0xD088DC`) e em `0xD089A0` (rajada `0xD0896C`); **depois** do
  título em `0xD08BE2` (rajada `0xD08BEA`) e em `0xD09014` (rajada
  `0xD09028`).
- **CONFIRMADO** — `get_path` devolve `0:/…` ou `0:\…`: o B3 no aparelho e
  os testes usam esses prefixos, e `0xCFF0C4 cmp r0,#1` valida o retorno.

## Q3 — como entregar à view

- **CONFIRMADO** — a fila copia a mensagem: `0xD0D818` → `0xCF83E4` →
  `0xD6AA72`, que grava o header `0x55AA` + tamanho e o payload. Ponteiro
  para buffer que a MainTask libera não é problema.
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

## O que não dá para saber só pelo ORIGINAL

- Se a fila da view entrega a mensagem tipo 5 ao `page_music_play_label_process`
  em todos os filtros (o caminho do evento 4 é o mesmo da mensagem do
  rótulo 2, mas não há prova de todos os filtros).
- O texto exato do rótulo 2 (nome da faixa? pasta?) sem captura no aparelho.
- Se a transitória “capa anterior até o tipo 5 chegar” é visível no aparelho
  (depende do tempo da fila; o emulador não roda a MainTask).
