# 028b — análise: o nome da música no cartão da home (Reload 3.5 Diag 2)

Base: a **3.5 Diag** publicada (ficha 028), imagem `f49c8195…`, que o
decisor testou no aparelho em 22/11/2026. Teste do decisor: *"está tudo
certo; só o player da tela inicial não mostra o nome da música"* — o
cartão mostrava **`♪ 31/165`**, o contador da fila.

Resultado: o cartão passa a mostrar **o nome da faixa**. Tudo o que está
abaixo foi lido no binário; o que não foi provado está marcado.

---

## 1. O diagnóstico: por que o cartão mostrava o contador

### 1.1 CONFIRMADO — a mensagem tipo 3 traz o **índice do elemento** em `msg+4`

O descritor da mensagem fica num endereço **fixo**, `0x008238F1`, e o
texto em `msg+0x14`. O halfword de `msg+4` é o índice do elemento da
página que a mensagem atualiza. Os cinco apresentadores da fábrica:

| apresentador | o que monta | `msg+4` | `msg+6` (tipo) | texto |
|---|---|---|---|---|
| `0xD083C4` | o contador da fila | **0** | 3 | `"%d/%d"` (`0xD083E2`, `index+1` e o total) |
| `0xD08448` | o **título** da faixa | **1** | 3 | o nome da faixa (o getter `0xCFEE60`, `bl` em `0xD08468`) |
| `0xD084F8` | o caminho do arquivo | 2 | 3 | o caminho (ou `"  "`, `0xCE4473`) |
| `0xD086B0` | um tempo | 3 | 3 | `"%02d:%02d:%02d"` (`0xD0876A`) |
| `0xD087D8` | outro tempo | 4 | 3 | idem (`0xD087F0`) |

Provas: `strb r2,[r4,#4]` em `0xD084BA` (1), `0xD08406` (0), `0xD08518`
(2), `0xD0871A` (3), `0xD087AC` (4); o tipo 3 em `msg+6` em `0xD084A4`,
`0xD0841C`, `0xD08514`, `0xD08718`, `0xD087AA`.

### 1.2 CONFIRMADO — a view do player: `[view+0]` é o contador, `[view+4]` é o título

`page_music_play_create` (`0xD31E7C`) monta a view da página 4 (ela
está em `[[0x81CE2C]+0xAC]`, ficha 007 A4): o **primeiro** rótulo é o
contador (`lv_label_create` em `0xD31ED0`, texto `"1/253"` em
`0xD31F02`) e o **segundo** é o título (`lv_label_create` em
`0xD31F0C`, texto vazio `0xC4F981` em `0xD31F74`). O `tbb` de
`0xD32242` escolhe o rótulo pelo índice: 0 → `[r5]`, 1 → `[r5+4]`,
2 → `[r5+8]`, 3 → `[r5+0x14]`, 4 → `[r5+0x18]`; e o tronco comum
`0xD3225E` chama `lv_label_set_text(rótulo, msg+0x14)`.

**Logo: o índice 1 é o título e o índice 0 é o contador.** Isto é o
mesmo que a ficha 011 já provou ("a mensagem do caminho grava 2 em +4
(o rótulo `[r5+8]`); a do título grava **1** (o rótulo `[r5+4]`)").

### 1.3 CONFIRMADO — o bug da 028: o gancho do player filtrava o rótulo errado

A 3.5 filtrava `[view+0]` no gancho do player (`0xD3225E`) — que é o
rótulo do **contador**, não o do título. Com a página do player aberta,
o cartão guardava o contador também. E na home o gancho copiava
**qualquer** tipo 3 como título: a fábrica manda o caminho (2), o
tempo (3), o tempo (4), o **título (1)** e o **contador (0)**, nessa
ordem (`page4_media_cb` `0xD088B4`: `0xD088D8` caminho, `0xD088E0`
tempo, `0xD088E4` tempo, `0xD088E8` **título**, `0xD088EC`
**contador**) — o contador é o **último**, e ficava por cima do título.
É exatamente o que o decisor viu.

### 1.4 CONFIRMADO — a home recebe **todas** as mensagens tipo 3

`page_home_label_process` (`0xD2EEC4`) lê o índice em `msg+4`
(`ldrh r2,[r0,#4]` em `0xD2EEC6`) e usa a **vista da home**
(`[[0x81CE2C]+0xA0]`) como base: `ldr.w r3,[r3,#0xa0]` em `0xD2ECA`,
`add r3,r3,r2,lsl#2` em `0xD2ECE`, `ldr r3,[r3,#0x24]` em `0xD2ED2` e o
`cbnz` de `0xD2ED4`. Ou seja: o índice escolhe **o rótulo de um ícone**
da home, em `vista[0x24 + 4*indice]`.

E a view da home tem **um rótulo por ícone**: no laço de criação
(`0xD2ECEE..0xD2ED8E`) cada ícone ganha uma imagem em
`[vista+4*i]` (`str sb,[sl,#4]!` em `0xD2ED84`) e um **rótulo** em
`[vista+0x24+4*i]` (`str.w r6,[sl,#0x24]` em `0xD2ED8A`, com `r6` o
rótulo criado em `0xD2ED26`). Os nove rótulos existem, então o `cbnz`
**passa** para os índices 0, 1 e 2 — o gancho da home (`0xD2EEE4`)
recebe o título (1) e o contador (0).

### 1.5 CONFIRMADO — a ViewTask entrega **toda** mensagem à página aberta

O contador (índice 0) chegou à home no aparelho; se houvesse um filtro
por página, o índice 0 iria para a página 0 e não para a home. Logo
não há filtro: cada mensagem do ring vai para o `label_process` da
página que está aberta (`0x0081BBC0` é o ring da view;
`0xD0D818` copia a mensagem para ele — `bl 0xCF83E4`).

---

## 2. De onde a CPU0 tira o título na troca de faixa

### 2.1 CONFIRMADO — o presenter `0xD08448`, sem página 4 aberta

`0xD08448` (ficha 007 A3) pega o índice da faixa (`0xCFF0FC`), aloca um
buffer (`0xCF7840`), copia o **nome** com o getter `0xCFEE60` (único
chamador no binário: `bl` em `0xD08468`) e escreve o texto em
`msg+0x14` (`strncpy 0xD9FD54`, `0xD084C4`); depois envia (`0xD0D818`).

Ele tem **4** chamadores: `0xD088E8` e `0xD089A0` (dentro de
`page4_media_cb`), `0xD08BE2` e `0xD09014` (abertura da página).

### 2.2 CONFIRMADO — o `media_cb` roda com **qualquer** página aberta

O callback de mídia é registrado em `0x0081CDE0` (`pstr_register_media_cb`,
`0xD0E8F8`, chamado em `0xD09008`) e é **chamado sem olhar a página**:
`ldr r3,[0x0081CDE0]` / `ldr r3,[r3]` / `cmp r3,#0` / `blx r3` em
`0xD0EEDE..0xD0EEEC`. O guardião é o próprio ponteiro: registrado uma
vez, fica.

Logo, com a home aberta e a música advancede, a CPU0 chama
`page4_media_cb` → o presenter do título → a mensagem tipo 3 com o
**índice 1** e o **nome da faixa** entra no ring → a ViewTask entrega
à home → o gancho da home a vê.

**Este é o "RAM que a CPU1 só lê" que a ficha pedia**: a cópia da
mensagem no ring da view (`0x0081BBC0`), com o texto em `msg+0x14`.
Não há outro lugar: o buffer da CPU0 (`0x008238F1`) é reescrito a cada
apresentador (o contador é o último), e o nome no banco só existe
durante a chamada do getter (que é da CPU0 e pega o mutex do banco —
proibido na CPU1, ficha 013).

### 2.3 CONFIRMADO — o título vem **antes** do contador

Nas duas trocas de faixa o título precede o contador:
`0xD088E8` (título) e `0xD088EC` (contador); `0xD089A0` (título) e
`0xD089A4` (contador); `0xD08BE2` (título) e `0xD08BE6` (contador).
Na **abertura** da página a ordem é o contrário (contador em
`0xD0900C`, título em `0xD09014`) — por isso o código trata as duas
ordens.

---

## 3. O que o cartão faz agora

Estado (`lv_mem_alloc`, no `user_data` do timer, como na 028): `title[64]`,
`counter[16]`, `version`, `shown_version`, `title_fresh`, `card`,
`title_label`.

- **Gancho da home** (`0xD2EEE4` → `fw_player_title_hook_home`): lê o
  índice de `msg+4`. Índice **1** → o título. Índice **0** → o
  contador. Os outros (caminho, tempos) são ignorados.
- **Gancho do player** (`0xD3225E` → `fw_player_title_update`): o
  rótulo `[view+4]` → o título; o rótulo `[view+0]` → o contador; os
  outros → nada.
- **`title_fresh`**: o título que chega marca `title_fresh = 1`; o
  contador consome a marca. Se o contador chega **sem** um título novo
  (a mensagem do título se perdeu no ring), o título que temos é de
  **outra faixa** e **some** — o cartão volta a "Nada tocando".
  **Nunca** se mostra o título de outra faixa.
- O **contador não aparece** no cartão: ele é só o sinal de troca de
  faixa (decisão D37).
- O cartão mostra o título ou "Nada tocando" / "Nothing playing", como
  na 028 (`fw_player_empty()`).

---

## 4. O que continua HIPÓTESE (o que o kit Diag 2 mede)

- **HIPÓTESE — o stop.** A mensagem de stop é o tipo 1 de
  `page4_media_cb` (`0xD08904`) e não traz título nem contador; o
  cartão deve **manter** o último nome. A 028 mediu esse ponto na 3.5
  Diag e o resultado não está no repositório; o Diag 2 repete a
  medição.
- **HIPÓTESE — a perda de mensagem no ring.** Se a mensagem do título
  se perde (ring cheio), o contador chega sozinho e o título some
  (regra segura, mas não medida no aparelho).
- **PROVÁVEL — a semântica de play/pause/stop** (`[0x81CF4C]`,
  `[0x81BC84+4]`): continua como na 028 §4; a etapa 2 (▶/❚❚, tempo,
  barra) não entra.

---

## 5. Tamanho e custo

- Código novo: **+104 B** no SDK (13.944 B → 14.048 B), dentro do lote
  `0x1AB000..0x1FC000`.
- Estado: `lv_mem_alloc` de ~0x68 B (o `counter[16]` e o `title_fresh`
  entraram) + `title[64]`.
- Timer a 2 Hz, ~20 instruções por tique: lê o `version`, compara e
  troca o texto só quando muda.
- A diferença contra a 3.5 Diag são **2.158 bytes**, todos no lote do
  SDK: os quatro ganchos, a tabela das molduras e a folha dos ícones
  ficam **byte a byte**.

Imagens: sem carimbo `ba56813d…`, carimbada `65fad72f…`; `.up`
`OpenPod_OpenPodReload3.5Diag2.up`, 1.765.632 B, CRC `0xC5C9`, sha
`3c71a462…`; 5 setores no kit de cabo.

---

## 6. O que fica para depois

- Etapa 2 da 028 (▶/❚❚, tempo restante e barra): depende de provar a
  semântica de play/pause/stop.
- Etapa 3 (a capa do álbum no cartão): fica para a tarefa da capa.
- A **3.5 pública**: só depois do teste do decisor neste kit.
