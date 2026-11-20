# Ficha 025 — análise: Reload 3.3 (pular rápido) e a Parte 0 dos dois núcleos

Data: 2026-11-20. Base: `privado-completo` (Reload 3.2, publicada).
Branch: `limtistech/tarefa-025`. Desenvolvedor: `opencode/deepseek-v4.1-flash-free`.

Este arquivo é escrito em ordem: cada achado entra aqui **antes** de virar
patch, para a sessão poder cair sem perder a prova.

---

## Parte 0.1 — auditoria das chamadas ao kernel na CPU1

Regra: **nenhuma chamada ao kernel (heap do FreeRTOS, tarefa, semáforo,
sleep, FatFs, dispositivo) a partir da CPU1**. A CPU1 é a interface: LVGL,
eventos, timers e `label_process`; a CPU0 é o FreeRTOS e as tarefas
(PreTask, MediaTask, cartão).

| Código nosso | Onde roda | Endereço | Chamada ao kernel? |
|---|---|---|---|
| CRIA (`corpo_cria`) | ViewTask/CPU1, na criação da página 4 | `0xDAA028`, `CALLOC` em `0xDAA04C` | **SIM**: `0xCF7840` (heap do FreeRTOS) |
| APAGA (`corpo_apaga`) | ViewTask/CPU1, `LV_EVENT_DELETE` | `0xDAA212`, `FREE` em `0xDAA24E` | **SIM**: `0xCF7884` |
| CRIA, caminho de erro | ViewTask/CPU1 | `FREE` em `0xDAA0D8` | **SIM**: `0xCF7884` |
| TITULO | ViewTask/CPU1 | `0xDAA0E6` | não: só `lv_label_set_text` e epílogo |
| `label_dispatch` tipo 5/6 | ViewTask/CPU1 | `0xDAAA96` (tipo 6) | não: só copia pixels para a view |
| gancho do menu Apps | ViewTask/CPU1 | `0xD23CF8` → `0xDAD23C` (`hook_home_menu_create`) | não: `sdk/src/menu.c` só usa LVGL |
| SDK dos jogos | ViewTask/CPU1 | lote `0xDAB000` | não: `sdk/src` e `sdk/apps` só usam `lv_mem_alloc`/`lv_mem_free`; nenhum `fw_os_*`, sleep, tarefa ou FatFs |
| overlay | ViewTask/CPU1 | `sdk/src/overlay.c` | não: `lv_mem_alloc`/`lv_mem_free` |
| libc do SDK | — | `sdk/src/libc.c` | não: memset/memcpy/memmove/strlen puros |

Conclusão: o único ponto nosso que chama o kernel na CPU1 é o contexto da
capa em `corpo_cria`/`corpo_apaga`. O `carrega_capa` (que aloca FIL, JDEC,
pool e o `tmp` de `0x2210`) roda na PreTask/CPU0 e **não** muda.

---

## Parte 0.2 — tirar o contexto da capa do heap do FreeRTOS

Escolha: **(a) o alocador do LVGL**. Provas:

- `lv_mem_init` `0xD58100`: `mov.w r1,#0xa000` e pool em `0x00876000` →
  **40 KiB** (`0x00876000`–`0x00880000`).
- `lv_mem_alloc` `0xD58188`: recebe o tamanho em `r0`; no erro (bloco 0)
  registra `"couldn't allocate memory (%d bytes)"` e devolve `r4`, que é
  `0` (`cbnz r0` em `0xD5819C`; `mov r0,r4` em `0xD581DE`). Ou seja, o
  alocador do LVGL **devolve 0 na falta de memória** — ao contrário do
  `0x9D50` do OAL (item 0.4).
- `lv_mem_free` `0xD5811C`: ignora `NULL` e o ponteiro estático
  `0x00819E60`; libera o resto por `0xD59954`.
- O CRIA/APAGA já roda na ViewTask, que é a dona do LVGL: usar o
  alocador do LVGL na CPU1 é o uso normal, não uma chamada ao kernel.
- O `lv_mem_alloc` não zera; o `calloc` antigo zerava. O patch zera com o
  `memset` da fábrica (`0xBAA`), preservando o comportamento (o buffer de
  pixels não aparece com lixo antes do primeiro tipo 6).

Opção (b) recusada: um buffer permanente de `0x2210` na CPU0 **mais** o
`tmp` de `0x2210` do `envia_path` **mais** FIL/JDEC/pool (`0x25C+0x138+
0xE00 = 0x1194`) dariam `0x3BB4` (~15 KiB) só de contexto, e o pico medido
na 007/E1 é 16,4 KiB **com música**; o permanente de 8,5 KiB reduziria o
livre para ~7,9 KiB e o `tmp` do próximo decode não caberia. Além disso, o
destino (view) e a origem (tmp) têm de ser buffers diferentes; reusar o
mesmo buffer corromperia a capa enquanto a view copia os 8 pedaços.

### O patch da 3.3 (sem tocar nas receitas antigas)

O `tools/capa_album.s` é montado para **todas** as receitas desde a RC7;
mudá-lo mudaria a 3.2 publicada (catraca). O patch da 3.3 é aplicado
**depois** da 3.2, só nos bytes do lote da capa:

- `0xDAA03E..0xDAA04D` (16 B): a sequência `movs r0,#1; movw r1,#0x2210;
  movw/movt ip,#0xCF7841; blx ip` vira 12 B de `nop` + `bl 0xDAA9D8`.
- `0xDAA9D8..0xDAA9FF` (40 B, hoje `0xFF`): trampolim
  `push {r4,lr}; movw r0,#0x2210; lv_mem_alloc; cbz r0; memset(r0,0,0x2210);
  pop {r4,pc}`. Monta em **40 bytes exatos**.
- `0xDAA0D0`/`0xDAA0D4` e `0xDAA246`/`0xDAA24A`: `movw/movt ip` de
  `0xCF7885` para `0xD5811D` (`lv_mem_free`), mesmo tamanho.

O `bl` de `0xDAA04A` para `0xDAA9D8` volta em `0xDAA04E` (`mov r7,r0`), então
o `cmp r7,#0; beq sem_dsc` continua valendo: se o LVGL não tiver os 8,5 KiB,
o CRIA cai no quadrado cinza, sem escrever em ponteiro ruim.

---

## Parte 0.3 — a fábrica recria a página ao trocar de faixa?

**Não.** O caminho da troca de faixa é `page4_media_cb` `0xD088B4`:

- comando 5 em `0xD08950`: `ldr r0,=0x00CD9851 ("screen")`, `bl 0xD45E58`,
  `0xCFE720`, guarda a duração, chama a rajada `0xCFF2A4` (`0xD0896C`) e
  os envios de título/tempos (`0xD08448`, `0xD084F8`, `0xD083C4`, ...);
- nenhum `bl` para `page_music_play_create` `0xD31E7C` nem para a pilha de
  páginas; as mensagens são tipo 3/5/6 para a view que já existe.
- `page_music_play_create` não tem xref de `bl` no flash (a tabela de
  páginas está na máscara ROM), mas a criação é a **entrada** na página 4;
  a troca de faixa não passa por ela.

Logo o CRIA/APAGA roda na **entrada/saída** da página Tocando Agora, não a
cada pulo. O calloc/free na CPU1 continua sendo um defeito real (entrar ou
sair da página com música toca o heap da CPU0), mas **não** é a causa por
pulo do relato. Registrado.

---

## Parte 0.4 — o `calloc` devolve 0 na falta de memória?

O README do Dmitry ("Gotchas") diz que o `oal_malloc` pode devolver o
retorno do `printf` em vez de `NULL`. No **nosso** ORIGINAL:

- `0xCF7840` (`calloc`) chama `0x9E88` (livre do heap), calcula
  `tam = n * tam` e faz `cmp livre, tam; bhi 0xCF785E`; se **não** houver
  livre, registra `"[oal_mem]: ...oal_calloc1 %d failed."` e devolve **0**
  (`0xCF784E..0xCF785A`). O caso "sem memória" está coberto.
- Depois de `0x9D50` (malloc), `cbnz r0` em `0xCF7866`; se 0, registra o
  mesmo erro e devolve 0 (`0xCF7868..0xCF7870`). O caminho de erro existe.
- `0xCF780C` (`malloc`) repete o padrão; o terceiro chamador de `0x9D50`,
  `0xCF7CC6`, também faz `cbz r0` e libera/retorna.
- O `0x9D50` está na **máscara ROM**, fora do dump; não dá para ler o
  `ret` de falha dele. O que está provado no ORIGINAL é o contrato dos
  chamadores (0 = falha) e a checagem de livre **antes** do malloc.
- **A opção (a) elimina essa dúvida**: `lv_mem_alloc` `0xD58188` está no
  flash e devolve 0 de forma provada. Para o `tmp` da CPU0, o
  `0xCF7840` já checa o livre antes; a margem de folga é o que sobra
  depois do `cmp bhi`.

---

## Parte 0.5 — o que a 3.3 muda (resumo para o teste)

1. Só o lote da capa (`0x1A8000..0x1AB000`) e os três sítios de alocador
   em `corpo_cria`/`corpo_apaga`; nenhum byte abaixo de `0xE000`, setor
   `0xD000` e PSMP intocados.
2. Nenhuma chamada ao heap do FreeRTOS na CPU1; o CRIA/APAGA usa
   `lv_mem_alloc`/`lv_mem_free` (`0xD58188`/`0xD5811C`).
3. Se o LVGL não tiver os `0x2210` B, o CRIA mostra o cinza (o `cmp r7,#0`
   já existente), sem ponteiro ruim.
4. O `carrega_capa` da CPU0 continua com `0xCF7840`/`0xCF7884` e o
   `0xCF7840` continua checando o livre.

## Parte 0.2 — o patch da 3.3 (feito e verde)

- `tools/fab_reload_3_3.py` aplica as três trocas sobre a 3.2 exata (sha
  `aa7e7a5a...`), com as premissas conferidas antes de escrever:
  alloc `0xDAA03E` → 6 `nop` + `bl 0xDAA9D8`; trampolim `0xDAA9D8`
  (40 B, `lv_mem_alloc(0x2210)` + `memset` + `cbz`); `FREE` em
  `0xDAA0D0`/`0xDAA0D4` e `0xDAA246`/`0xDAA24A` → `0xD5811D`.
- Receita `reload_3.3` em `tools/build.py` (`RELOAD_3_2` + a ferramenta).
- `tests/test_reload_3_3.py` (7 testes): reprodutível; diferença contra a
  3.2 só nos quatro intervalos do lote `0x1AA000`; `bl` e trampolim
  conferidos por capstone; `FREE` no LVGL; nenhum `0xCF7840`/`0xCF7885`
  no CRIA/APAGA (e os dois ainda no `carrega_capa` da CPU0); em unicorn,
  o trampolim chama `lv_mem_alloc(0x2210)`, zera os `0x2210` B e devolve
  o ponteiro; se a alocação devolve 0, não chama `memset` e devolve 0.
- `sh tools/ci.sh` verde (as travas antigas não mudam; a 3.3 não entra na
  catraca até o kit).

## Parte 1 — a revisão mandou retirar a 1.1

### 1.1 Desistir da capa velha — RETIRADA

A revisão (`docs/tarefas/025-revisao.md`, CRÍTICO 1 e 2) confirmou que a
guarda do yield em `0xDAAE30` não funciona:

- o `bl` para a guarda não tem palavra extra no frame: os wrappers
  `0xDAAE00`/`0xDAAE20` fazem `push {r4,r5,r6,lr}` (16 B, `lr` em
  `SP+12`), e a guarda terminava com `add sp,#4; pop {r4-r6,pc}` —
  deslocava a pilha e saltava para lixo no primeiro yield de toda capa;
- o índice `[0x0081BC84+0x20]` só muda **depois** que o decode termina:
  a mensagem de pulo fica em `MgrTaskQue` e a gravação do índice roda na
  própria PreTask. A comparação via valores iguais e não abortava a capa
  velha.

Decisão da coordenação: **retirar a Parte 1.1 inteira**. `0xDAA324` e
`0xDAAE30` voltam aos bytes da 3.2 e a área `0xDAAF00..0xDAAF4F` volta a
`0xFF`. Desistir da capa velha precisa da **contagem da fila da
PreTask** e fica para a tarefa da capa.

### 1.2 Não atropelar a fábrica no ring — MANTIDA

- `[0x0081BBC8]` é o struct do ring; `0xD6A9EA` devolve o livre (o
  mesmo que `0xCF83E4` usa em `0xCF8400`).
- Cada mensagem tipo 6 leva `0x414` B + 4 B de cabeçalho = `0x418`;
  8 = `0x20C0`. Reserva de `0x1000` para a fábrica → exigir `0x30C0`.
- `envia_path` `0xDAAC68` (`movw r0,#0x38f1`) vira `bl` para a guarda em
  `0xDAAF50`; se o livre for menor, desvia para `0xDAACFA` (libera o
  tmp) e o `0xDAAD06` manda o tipo 5 vazio. Se for maior, repõe `0x38f1`
  e volta ao `movt` original.

### 1.3 Medição

`tests/test_reload_3_3.py` (10 testes, verdes; agora roda no
`tools/ci.sh`):
- reprodução e diff: a 3.3 difere da 3.2 só no lote `0x1AA000`
  (Parte 0.2, a área `0x1AAF00..0x1AAF4F` em `0xFF` e a guarda do ring);
- estáticos: `bl`, trampolim, `FREE` no LVGL, rotina do ring byte a byte;
- unicorn: o trampolim aloca/zera/devolve e devolve 0 sem memória;
- **wrapper B7b real**: `emu_rc7.Maquina.chama` executa `0xDAAE20` com
  um chamador de verdade (frame de 16 B), callback e yield reais/stubs;
  SP, PC e r4-r6 voltam iguais aos da 3.2. Nada de frame artificial;
- **guarda do ring real**: `Maquina.chama` executa o `envia_path`
  `0xDAAC00` inteiro (com o `carrega_capa` real e um MP3 de capa);
  com `0x30C0` livres manda os 8 tipo 6; com `0x30BF` manda só o tipo 5;
  SP, PC e r4-r6 voltam iguais aos da 3.2.

### Ferramentas

- `tools/fab_reload_3_3_guardas.py` (257 linhas) aplica só a Parte 1.2
  sobre a Parte 0 exata (sha `368a7c8c...`); premissas de bytes e área.
- `tools/build.py`: `RELOAD_3_3 = RELOAD_3_2 + [fab_reload_3_3.py,
  fab_reload_3_3_guardas.py]`.
- `sh tools/ci.sh` verde.
