# 016 — análise: OpenPod Reload 2.0 (o B7b byte a byte)

Base: B7b sem carimbo `26ffa272…` (receita `reload_1.0_rc7_diag_b7b`);
2.0 carimbada `b88ce8e7…` (só o texto "Reload 2.0" e o literal). Toda
afirmação foi lida no binário; as da pergunta 4 foram conferidas no
emulador (`tests/emu_rc7.py`, rodado à mão). O código não mudou.

## 1. Avanço automático: a capa troca?

**CONFIRMADO: sim. O avanço passa pela PreTask, e a capa troca. Não é
achado.**

Cadeia do fim da faixa até a rajada:

1. A MediaTask manda `0x201` (playover) para a fila do monitor em
   `0xD692EC`; `crab_monitor` (`0xD689C0`) compara `0x201` em `0xD68A0A`
   e chama o callback da mensagem (`r5 = [msg+4]`).
2. O play normal registra o callback `0xD406CD` em `0xD407DC` (corpo em
   `0xD40858`, `bl 0xD3E0D4`). Em `0xD406CC`, `r1 - 0x201` cai em
   `0xD406EA` → `bl 0xD40660`.
3. `0xD40660` monta o payload de 0x18 B com `[sp] = 5` e chama
   `0xD4124C`, que envia à fila da **MediaTask** (id 8 via `0xD6AE38(8)`,
   cabeçalho `0x808`, cmd 7).
4. O laço da MediaTask `0xD40280` vê cmd 7 → `0xD43E40`; estado 1 →
   `0xD42D94` (`-media SPKPLAY rcv cmd ` em `0xCD7EF5`). O `tbh` de
   `0xD42D94` leva o subcmd 5 a `0xD430CC` (`-next ` em `0xCD7E5B`).
5. `0xD430CC` para o áudio (`0xD40610`), incrementa o índice `[+0x18]`,
   pega o caminho (`0xD40918`), inicia a faixa (`0xD407DC`, `0xD40B58`).
   No sucesso monta outro payload com `[sp+8] = [r4]` (o cmd recebido, 5)
   e chama `0xD412B4` (`0xD4317E`/`0xD431A4`).
6. `0xD412B4` envia à **MgrTask/PreTask** (id `0xB` via `0xD6AE38(0xB)`,
   cabeçalho `0xB08`, cmd 7). O bloco do handler da MgrTask em `0xD0EE96`
   lê o tipo em `[event+8]`; tipo 5 cai em `0xD0EEB4` (`subs #4; cmp #1`)
   e chama a rajada `0xCFF2A4` em `0xD0EED0`.
7. Na página do player, a mensagem de mídia cmd 5 é o caso `0xD08950` do
   `tbb` de `page4_media_cb` (`0xD088B4`, tabela em `0xD088C4`: índice 5
   → `0x46*2` → `0xD08950`); em `0xD0896C` a rajada `0xCFF2A4` é chamada
   de novo, e o retorno `0xD08970` está na lista de chamadores do
   `envia_path` (`tools/diag_b6.s:430`).

Os 5 chamadores da PreTask (`0xD088E0`, `0xD08970`, `0xD08BEE`,
`0xD0902C`, `0xD0EED4`) são caminhos de UI; nenhum deles é o avanço. O
`0xCFF20E` fica em `0xCFF1FC` (chamado por `0xD00E28`,
`page1_music_build_cb`) e `0xD00C24` é `db_delete_cb`; o `envia_path`
pula esses dois, mas o avanço não passa por eles. O avanço passa por
`0xD08950`/`0xD0EED0`, que estão na lista e montam a capa.

## 2. Trocas rápidas: o ring enche?

**CONFIRMADO: pode encher. O `0xD0D818` devolve 0 e o B7b tenta o cinza;
as outras mensagens da fábrica são descartadas nesse intervalo.**

- Ring da view: `0x0081BBC0`; tamanho `0x3C00` = **15360 B** (init em
  `0xCF8210`, `mov.w r0,#0x3c00` em `0xCF82B4`; erro
  `-malloc view ring error!` em `0xC4993E`).
- Cada tipo 6: comprimento `[msg+0xA] = 0x408`, total `0x408 + 0xC =
  0x414` = 1044 B. Oito por capa = **8352 B**; duas capas = **16704 B**
  > 15360 B.
- `0xD0D818` não bloqueia: chama `0xCF83E4`, que exige
  `livre >= len+4` (`0xD6A9EA`, `cmp` em `0xCF8406`) e, se não couber,
  faz `movs r4,#0` e volta (`0xCF8438`). O B7b testa o retorno em
  `0xDAACCC`: `beq 0xDAACFA` → libera o `tmp`, monta um tipo 5 cinza de
  9 B (`0xDAAD06`) e chama `0xD0D819`. Esse cinza **também pode ser
  descartado** (o retorno é ignorado).
- Título, tempo e as demais mensagens da fábrica usam o mesmo
  `0xD0D818` (ex.: `0xD0186A`, `0xD0586E`); com o ring cheio, cada uma
  devolve 0 e é perdida — os chamadores não reenviam. A view processa o
  que já está na fila em FIFO; o resultado visual exato (capa anterior,
  parcial ou cinza) depende do tempo de consumo. **Não dá para saber sem
  rodar no aparelho.**
- Em uma capa sozinha cabem 8352 B (sobram 7008 B). Com a primeira capa
  ainda na fila, a segunda começa a falhar por volta do 7º pedaço
  (6264 B já enfileirados, faltam 1044 B e só há ~744 B), dependendo do
  consumo concorrente da view.

## 3. Página errada no meio do carregamento

**CONFIRMADO: a guarda descarta os pedaços e o `tmp` é liberado. Não é
achado.**

- O handler do tipo 6 começa em `0xDAAA96`: carrega `[0x81CE2C]`
  (`0xDAAA96`), lê `[obj+0xAC]` (`0xDAAAA2`) e compara com `r5` em
  `0xDAAAA8`; se diferente (ou qualquer ponteiro nulo) → `0xDAAAFA`,
  sem copiar.
- A guarda do B7b em `0xDAAE60` (chamada pelo `b.w` de `0xDAAABC`):
  `ldrh r0,[r4,#0xA]; cmp #0x408; bne falha` (`0xDAAE60..0xDAAE66`) e
  `cmp r3,#0x1c00; bhi falha` (`0xDAAE68..0xDAAE6C`); se passa,
  `bx 0xDAAAC3` (volta à cópia); senão `bx 0xDAAAFB` (epílogo). A cópia
  em `0xDAAAC2` ainda faz `tst r3,#0x3ff` (alinhamento) e copia 0x400 B;
  no último pedaço (`cmp r3,#0x1c00` em `0xDAAAE2`) finaliza com
  `img_set_src`.
- Na PreTask, `envia_path` (`0xDAAC00`) faz `calloc(1,0x2210)`; o
  sucesso libera o `tmp` em `0xDAACDA`, a falha do `carrega_capa` em
  `0xDAACFA`, e a falha de envio em `0xDAACCE` cai no mesmo `0xDAACFA`.
  O `calloc` que falha vai direto ao cinza (`0xDAAD06`, `b6b_vazio`) sem
  `free` — o `tmp` só existe depois do sucesso. Todos os caminhos que
  alocaram liberam; nenhum pedaço é alocado pela view.

## 4. Tipos de capa (emulador)

O `carrega_capa` do B7b foi rodado sobre a 2.0 sem carimbo com o
`TJpgDec` da fábrica e os callbacks reais (o yield `0xC43634` é falso,
como no teste B7). `r = 1` = capa; `r = 0` = falha, que o `envia_path`
converte no tipo 5 vazio (cinza):

| Caso | Arquivo / origem | `r` | Resultado |
|---|---|---:|---|
| baseline v2.3 (300×300) | `01_capa_v23.mp3` | 1 | capa |
| baseline v2.4 (500×500) | `02_capa_v24.mp3` | 1 | capa (s=3, 62×62) |
| v2.4 cabeçalho estendido (200×120) | `03_capa_v24_cabecalho_estendido.mp3` | 1 | capa |
| JPEG progressivo | `04_capa_progressiva.mp3` | 0 | cinza |
| PNG | `05_capa_png.mp3` | 0 | cinza |
| sem capa | `06_sem_capa.mp3` | 0 | cinza |
| sem tag | `07_sem_tag.mp3` | 0 | cinza |
| menor que 56 px (48×48) | `capa_pequena_48.jpg` | 0 | cinza |
| escala de cinza (500×500) | gerado com Pillow | 1 | capa (tons de cinza) |
| CMYK (500×500) | gerado com Pillow | 0 | cinza |

Nenhuma execução deixou arquivo aberto nem erro de pilha/emulação. O
teste `tests/test_reload_2_0.py` repete 01..07 e 48×48; os dois gerados
(cinza/CMYK) ficam registrados aqui.

## Achados

**[BAIXA] CONFIRMADO — pulando faixas rápido, o ring pode encher e a
capa pode não atualizar.** É o comportamento herdado do B7b, não uma
regressão da 2.0: o envio é não bloqueante, devolve 0, e o cinza de
fallback pode ser descartado junto. Título/tempo também são perdidos até
a fila esvaziar. Não trava e não vaza; o roteiro cobre "pular faixas
rápido" e "sair e entrar". Correção, se o decisor quiser, é outra ficha.

**Sem achados para Q1 e Q3.** O avanço automático troca a capa; a página
errada descarta os pedaços e não vaza na PreTask.

## Entrega

- Receita `reload_2.0` = `reload_1.0_rc7_diag_b7b` (mesma lista); sem
  carimbo, sha `26ffa272…` — provado por `tests/test_reload_2_0.py`.
- Imagem carimbada `b88ce8e7…`; `.up` 1.749.248 B, CRC `0x4D84`, sha
  `8a3c54c2…`; kit `release/OpenPod-Reload-2.0/` (base ORIGINAL).
- README e TESTAR no formato da RC6; "Beta" fica até o decisor aprovar o
  teste da 2.0 (a coordenação remove depois).
