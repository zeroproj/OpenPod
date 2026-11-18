# Ficha 023 — análise do Reload 3.1c (controles do GN-438 e a Cobrinha)

Base: Reload 3.1b (`release/OpenPod-Reload-3.1b/`,
imagem carimbada `d9671d9e…`). Fonte de verdade:
`firmware/ORIGINAL/GN438_original.bin` (sha256 `b7cd5eb9…`).
Referência: `referencias/SL6801_player`, commit `0361e2c`, usada com
permissão (D15, crédito a Dmitry Brant).

## 1. Mapa de teclas aplicado

Códigos medidos no aparelho em 2026-11-18 com o app "Teste de teclas" da
3.1a (`docs/BUTTON_ANALYSIS.md`, §"Códigos de tecla no LVGL"):

| Botão | Toque | Segurar |
|---|---|---|
| M | `0xA0` | `0xA2` |
| VOL/Sair | `0x81` | — |
| ⏭ | `0x13` | `0x89` |
| ⏮ | `0x14` | `0x87` |
| Play/Pause | `0x0A` | — (pode ser o desligar; só ação de menu) |

`0x11`/`0x12` **não existem** neste aparelho. O `fw.h` agora expõe só os
nomes medidos: `FW_KEY_M`, `FW_KEY_M_LONG`, `FW_KEY_PREV`, `FW_KEY_NEXT`,
`FW_KEY_PREV_LONG`, `FW_KEY_NEXT_LONG`, `FW_KEY_PLAY`, `FW_KEY_BACK`.
Nenhum app usa mais cima/baixo (`tests/test_reload_3_1c.py::test_chaves_medidas`).

Aplicação aprovada pelo decisor:

| Jogo | ⏮ / ⏭ | M | segurar M | Play/Pause | VOL/Sair |
|---|---|---|---|---|---|
| **Mp3tris** | move; `0x87`/`0x89` repetem | gira | derruba de vez | desce uma linha | duas vezes sai |
| **Flutter** | — | sobe | — | sobe | duas vezes sai |
| **Cobrinha** | vira à esquerda/direita, relativo à direção | — | — | pausa/continua; no fim, recomeça | duas vezes sai |

Os códigos longos `0x87`/`0x89` são os eventos de auto-repetição do key
manager (há contador de repetição no log do firmware); por isso o Mp3tris
os trata como mais um passo na mesma direção.

## 2. Idioma: onde o `get_lang_str` lê — CONFIRMADO

- `get_lang_str` em `0xD2108C` (`docs/SIMBOLOS.md`) começa com
  `10b5` e faz `bl 0xD0E2B8` (`edf712f9` na 4ª palavra).
- O getter `0xD0E2B8` é `ldr r3,[pc,#4]; ldrb r0,[r3,#1]; bx lr`
  (`014b 5878 7047`) e o literal em `0xD0E2C0` é `0x00823D05`. Logo o
  idioma é o **byte em `0x00823D06`**.
- O setter `0xD0E2C4` grava o mesmo byte e chama `0xD44EBC` com a chave 3,
  que é a chave `language` da tabela de configurações persistidas.
- Em `get_lang_str`, o `tbb` mapeia o índice 8 para a tabela `0xC53B84`.
  Lendo os ponteiros dessa tabela no ORIGINAL: id 0 = `Português`,
  id 7 = `Despertador`, id 159 = `Aplicação`; a tabela inglesa `0xC52AA4`
  (índice 0) tem `English`. Portanto **índice 8 = português**.

`fw.h` expõe `FW_LANG` (`*(volatile uint8_t *)0x00823D06`) e
`FW_LANG_PT` (8). O menu e a tela da Cobrinha mostram **"Cobrinha"** nesse
idioma e **"Snake"** nos outros. A prova acima é travada por
`tests/test_reload_3_1c.py::test_idioma_do_get_lang_str`.

## 3. Menu Aplicativos: cinco linhas cabem

O criador de fábrica `page_home_menu_create` (`0xD2F0A0`) monta a lista e
três linhas. O gancho da 3.1b reaproveita o item 2 para o primeiro app e
acrescenta os demais; com três apps o resultado é:

**Despertador, Imagem, Flutter, Mp3tris, Cobrinha** — 2 linhas de fábrica
+ 3 do SDK = **5 linhas**.

Geometria medida no ORIGINAL:

- em `0xD2F1AA`–`0xD2F1BA` a lista recebe `height = 6*(ver/7) + 3`;
- em `0xD2F21E`–`0xD2F238` cada linha recebe `height = ver/7`.

Com `ver = 160`: lista `6*22+3 = 135 px`, linha `22 px`, cinco linhas
`110 px`. **Cabem sem rolagem** sobrando 25 px. Além disso a lista já é do
tipo rolável do LVGL e cada linha entra no mesmo grupo
(`lv_group_add_obj` em `0xD2F26C`); o gancho faz o mesmo para as linhas
extras. O foco, portanto, percorre as cinco linhas.
Teste: `tests/test_reload_3_1c.py::test_menu_cinco_linhas`.

## 4. Desenho da Cobrinha

Arquivo: `sdk/apps/cobrinha/main.c`.

- **Tela cheia 128×160:** faixa de placar de 16 px no topo e campo de
  `16 × 18` células de 8 px abaixo (`128 × 144`).
- **Cores da linha 2.2:** fundo preto; cobrinha verde `(120,220,120)`;
  comida vermelha `(255,82,82)`; cabeça num verde mais claro
  `(160,255,160)` para leitura rápida.
- **Desenho como o Mp3tris:** uma imagem indexada de 4 bits num buffer do
  heap do LVGL (`game_t`, alocado por `lv_mem_alloc` em `cobrinha_open`) e
  redesenhada no lugar; sem um objeto por célula. Timer do LVGL de 20 ms;
  o buffer e o timer são liberados no `LV_EVENT_DELETE` (`on_delete`).
- **Regras:** começa com 3 segmentos no centro, virada relativa à direção
  (sem 180°, uma virada por passo). Cada comida cresce 1, soma 1 ponto e
  reduz o intervalo em 8 ms até o piso de 70 ms. Parede ou corpo =
  "Fim de jogo" com a pontuação.
- **Controles:** ⏮/⏭ viram; Play inicia, pausa/continua e, no fim de jogo,
  recomeça após 0,7 s; Back duas vezes em 0,8 s sai.
- **Sem `.data`/`.bss`**, sem som; semente do `lv_tick_get` misturada ao
  `FW_SYSTICK_VAL`.

## 5. Build, receita e diff

- `tools/build_sdk.py --variante jogos` agora compila também
  `sdk/apps/cobrinha`.
- SDK 3.1c: **11.468 B** em `0x00DAB000`, gancho `0x00DAD140`,
  sha do app `029c44b394c44dfb…`; duas compilações dão o mesmo binário
  (`--check-repro`).
- Receita nova `reload_3.1c` = a lista da 3.1b (3.0 + `fab_sdk_jogos.py
  --variante jogos`) com o SDK novo.
- Imagem 3.1c sem carimbo: sha `b84ac4988b5d7eda…`; contra a 3.0 muda só
  o lote `0x1AB000..` e os 4 bytes do `bl` em `0x123CF8`; nada abaixo de
  `0xE000`, setor `0xD000` e PSMP intocados.
- **Contra a 3.1b publicada:** as diferenças são só o lote, o `bl` e o
  carimbo "Reload 3.1b" da imagem antiga (3 bytes do literal em
  `0x10A59C` + 12 bytes do texto em `0x1A4F00`). Nenhum outro byte.
  Teste: `tests/test_reload_3_1c.py::test_diff_contra_3_1b`.

**Divergência registrada:** as fontes do SDK são compartilhadas, então a
receita `reload_3.1b` executada hoje também produz o SDK da 3.1c. A 3.1b
publicada continua sendo a referência em `release/OpenPod-Reload-3.1b/`;
o teste reconstrói a imagem dela pelo payload do `.up` versionado.

## 6. Testes

`tests/test_reload_3_1c.py` (novo, 5 testes):

1. reprodutibilidade, sem `.data`/`.bss`, bit Thumb;
2. constantes de tecla e nenhum app usando `0x11`/`0x12`;
3. fonte do idioma e tabela portuguesa no ORIGINAL;
4. cinco linhas no menu (tabela de apps + geometria);
5. diferença contra a 3.1b e limites de segurança de bytes.

`tests/test_reload_3_1.py` (da ficha 022) continua passando.

## 7. Entrega

- `docs/tarefas/023-analise.md` (este arquivo).
- `sdk/include/fw.h`, `sdk/include/sdk.h`, `sdk/src/menu.c`,
  `sdk/apps/mp3tris/main.c`, `sdk/apps/flutter/main.c`, novo
  `sdk/apps/cobrinha/main.c`, `tools/build_sdk.py`, receita `reload_3.1c`
  em `tools/build.py`.
- Testes novos em `tests/test_reload_3_1c.py`.
- Kit `release/OpenPod-Reload-3.1c/` e `docs/CHANGELOG.md` (seção 8).

## 8. Kit

Gerado por `gera_versao` **sem `--base`** (base ORIGINAL), carimbo
`Reload 3.1c` aplicado por `patch_versao.py --em 0x1A4F00`:

| item | valor |
|---|---|
| imagem carimbada | `5dd7f3ee00e48072…` |
| `.up` | 1.761.536 B, CRC `0xE744`, sha `aa99850cdec3e138…` |
| setores | 33 na imagem, 66 arquivos em `cabo/setores/` |

`release/OpenPod-Reload-3.1c/` tem `README.md` ("New in 3.1c", jogos pelo
estilo, crédito a Dmitry Brant) e `TESTAR.txt` curto com a volta de
segurança para a 3.1b. O Flashloader é copiado pela coordenação.
