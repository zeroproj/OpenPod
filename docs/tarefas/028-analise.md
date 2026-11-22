# 028 — análise: player na tela inicial (Reload 3.5)

Base: a **3.3** publicada, sha256 `368a7c8c98f6b6b68c7e38853a69673bb05d5216219406f8ccdc9a858a73713d`
(gerada por `python3 tools/build.py --receita reload_3.3`). Toda afirmação
abaixo foi lida no binário; o que não foi provado está marcado.

## 1. O título chega à CPU1 (a) — PROVÁVEL

**PROVÁVEL — a home trata o tipo 3; não está provado que a CPU0 o mande
com a página 4 fechada.** A fábrica entrega o tipo 3 no **ring da view**
(`0x0081BBC0`) e quem o processa é o `label_process` da página atual, na
**ViewTask** (CPU1):

- `page_music_play_label_process` `0xD32204`; tipo em `[msg+6]`, texto em
  `msg+0x14`; o tipo 3 cai em `0xD32226` e o `set_text` é o `b.w` em
  `0xD3225E` (no ORIGINAL, `b.w 0xD5ED94`; na 3.3, `b.w 0xDAA014`, o
  handler do B7b). Prova: `docs/tarefas/007-rc7-capa-album.md` A6 e
  `docs/tarefas/013-analise.md` Q3.
- `page_home_label_process` `0xD2EEC4`: o tipo 3 é reconhecido em
  `0xD2EEDE..0xD2EEE2` e o caminho termina em `0xD2EEFC`; a home **não**
  tem rótulo de título, mas recebe a mensagem. A home **trata** o tipo 3
  (`0xD2EEDE`), então ela *pode* receber a mensagem — mas isso não prova
  que a CPU0 a *mande* com a página 4 fechada. O kit Diag responde no
  aparelho, no passo "deixar a música avançar sozinha na home".
- O título é o rótulo **`[page4_view+0]`**. A tabela em `0xDAAA00`
  indexa `[view+0]`, `[view+4]`, `[view+8]`, `[view+0x14]` e `[view+0x18]`;
  o `b.w` de `0xD3225E` é o **tronco comum** dos cinco, então o hook
  precisa comparar o rótulo com `[view+0]` para não copiar artista/álbum
  como título. Prova: `0xD3224C` (`ldr r0,[r5]`) e `0xD32262/66/6A/6E`.

Consequência de projeto: o cartão pode ser alimentado **inteiramente na
CPU1**, sem buffer entre núcleos, sem `0x80001C` e sem alocar na CPU0. A
prova do envio com a página 4 fechada fica com o kit Diag, no aparelho.

## 2. Onde guardar o título sem lugar fixo na RAM

**CONFIRMADO — a lista de timers do LVGL é um lugar estável.** O
`lv_timer_create` `0xD59020` insere o timer na lista `0x0081D2D4`
(`lv_ll_t`: `n_size` em `+0`, `head` em `+4`, `tail` em `+8`). O nó é o
próprio `lv_timer_t` (dados em `+0`), e os elos ficam **depois** dos dados:
`prev` em `node + n_size`, `next` em `node + n_size + 4`
(`lv_ll_ins_head` `0xD57DFE` e `0xD57DDC/0xD57DE4`). O `lv_timer_t` desta
build tem `timer_cb` em `+8` e `user_data` em `+0xC` (`fw.h`; confirmado
em `0xD59056..0xD5906C`).

O estado do cartão é um bloco `lv_mem_alloc` guardado no `user_data` de um
timer criado **uma vez** e nunca apagado. Os hooks de título acham o
estado percorrendo a lista de timers e comparando `timer_cb` com o nosso
callback. Não há `.data`/`.bss` e não há endereço fixo de RAM.

## 3. O cartão e o timer

- O cartão é criado no hook da criação da página 1 (`page_home_create`
  `0xD2EBB8`), depois da fábrica, como filho do objeto principal da
  página (`[page+0x48]`, `docs/tarefas/021-analise.md`).
- O gancho da home em `0xD2EEE4` é um **`b.w`** de 4 B para o trampolim,
  não `bl`: a `page_home_label_process` é folha e o LR de quem chamou tem
  de sobreviver. O trampolim faz `push {r0-r4,lr}`, chama o hook C,
  `pop {r0-r4,lr}`, refaz `r3=0x00823EB0` e `ldrb r3,[r3]`, e volta com
  `b.w 0xD2EEE8` (o `cmp r3,#3` da fábrica). São 6 palavras: 8 B.
- O gancho do título em `0xD3225E` também é um wrapper naked: salva
  `r0/r1/LR`, atualiza o estado e faz **`b.w 0xDAA014`** (a entrada TITULO
  da capa), preservando a capa do álbum. Não chama `lv_label_set_text`
  direto.
- O timer roda a **2 Hz** (`lv_timer_create(cb, 500, st)`), só lê o estado
  e o título; troca o texto apenas quando `version` muda. Custo:
  ~20 instruções por tique (três leituras e uma comparação), sem tocar em
  kernel, banco, FatFs ou `get_path`.
- O estado tem `title[64]`, `version`, `shown_version`, `card`,
  `title_label` e `magic`. O texto longo é cortado em 63 bytes + NUL e o
  rótulo usa `LV_LABEL_LONG_DOT` (3) para o “…”.
- O cartão não é clicável nem entra no grupo: `LV_OBJ_FLAG_CLICKABLE` e
  `LV_OBJ_FLAG_SCROLLABLE` limpos. A navegação e as teclas da home não
  mudam.

## 4. “Nada tocando” (b)

**PARCIAL.** O estado de mídia é legível: `[0x81CF4C]` byte de estado e
`[0x81BC84+4]` tempo decorrido, `[0x81BC84+8]` duração (ver
`docs/tarefas/021-analise.md`). O que **não** está provado é a semântica
de “parado/sem faixa”: `[0x81CF4C]` assume 0..0x12 (`0xD42D50` testa
`#0x60006`), e o stop não manda um tipo 3 de “vazio”.

Para a etapa 1, o cartão mostra o último título capturado; se nenhum
título foi capturado, mostra **“Nada tocando”** (português) ou
**“Nothing playing”** (outros idiomas), lendo `FW_LANG` em `0x00823D06`
(`docs/tarefas/023-analise.md`). A limpeza no stop fica como hipótese a
medir no kit de diagnóstico (a mensagem de stop é o tipo 1 do
`page4_media_cb`, `0xD08904`; o `[0x81BC84+4]` volta a 0 em `0xD0890C`).
Não há prova de que o título antigo deva sumir imediatamente; o decisor
testa.

## 5. A grade mais junta

A folha é uma imagem só, `INDEXED_8` 128×160, paleta em `0x0CDD5C` e
pixels em `0x0CE15C`. Na 3.3 as três faixas estão em `29..62`, `70..105`
e `114..149`, e a tabela das molduras (arquivo `0x486A0`) tem
`(5,27) (46,27) (87,27) / (5,70) (46,70) (87,70) / (5,114) (46,114) (87,114)`.

A 3.5 move as faixas para `19..52`, `58..93`, `97..132` e a tabela para
`(5,17) (46,17) (87,17) / (5,58) (46,58) (87,58) / (5,97) (46,97) (87,97)`.
O cartão fica em `(8,136)` com `112×22`. As faixas são copiadas como
estão (só os índices dos pixels mudam); o resto é o índice preto da
paleta.

## 6. Tamanho e custo

- Código novo no SDK: ~0,9 KiB (cartão, timer, hooks e `find_state`),
  dentro do lote `0x1AB000..0x1FC000` (0x51000 B).
- Estado: `lv_mem_alloc` de ~0x60 B + `title[64]`.
- Nenhum byte abaixo de `0xE000`; setor `0xD000` e PSMP intocados.

## 7. O que fica para depois

- A prova de envio da (a) com a página 4 fechada: o kit Diag responde no
  aparelho. Até lá, a (a) é **PROVÁVEL**.
- Etapa 2 (▶/❚❚, tempo restante e barra): o estado `[0x81CF4C]` e o
  `[0x81BC84+4/+8]` são legíveis, mas a semântica de play/pause/stop não
  está fechada; entra só se o decisor aprovar a medição.
- Etapa 3 (capa): não entra na 3.5.
- A limpeza do título no stop fica como hipótese no kit de diagnóstico;
  o texto vazio por idioma já usa `FW_LANG` (provado).
