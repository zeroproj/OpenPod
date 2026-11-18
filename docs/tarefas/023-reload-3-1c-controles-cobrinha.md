# Ficha 023 — Reload 3.1c: controles do GN-438 e a Cobrinha

Tipo: **Risco** (código novo no menu Aplicativos; vai ao aparelho). Base: `privado-completo` (Reload 3.1b, ficha 022).
**Comparação (D18):** esta ficha roda em paralelo, com o mesmo texto, em `opencode/deepseek-v4.1-flash-free` e
`minimax/MiniMax-M3.1-Flash`, cada um no seu worktree. Só um resultado entra no projeto.

Antes de começar, ler:
- `docs/BUTTON_ANALYSIS.md`, seção "Códigos de tecla no LVGL — medidos no aparelho".
- `docs/tarefas/022-analise.md` e `docs/tarefas/022-revisao.md`.
- `sdk/` inteiro, em especial `sdk/include/fw.h`, `sdk/src/menu.c`, `sdk/src/overlay.c` e `sdk/apps/mp3tris/main.c`.
- `tools/build_sdk.py`, `tools/fab_sdk_jogos.py`, as receitas `reload_3.1*` e `tests/test_reload_3_1.py`.

## Fato (aparelho, 2026-11-18)
- A 3.1b funciona: os apps abrem, os controles respondem e a música tocando não atrapalha.
- **Defeito:** o Mp3tris não gira a peça. Ele usa `LV_KEY_UP` (`0x11`), e o GN-438 **não tem** cima nem baixo.
- **Códigos medidos:**

  | Botão | Toque | Segurar |
  |---|---|---|
  | M | `0xA0` | `0xA2` |
  | VOL/Sair | `0x81` | — |
  | ⏭ | `0x13` | `0x89` |
  | ⏮ | `0x14` | `0x87` |
  | Play/Pause | `0x0A` | — (não usar: pode ser o desligar) |

## Controles aprovados pelo decisor
| Jogo | ⏮ / ⏭ | M | segurar M | Play/Pause | VOL/Sair |
|---|---|---|---|---|---|
| **Mp3tris** | move; segurar (`0x87`/`0x89`) repete | **gira** | derruba de vez | desce uma linha | duas vezes sai |
| **Flutter** | — | sobe | — | sobe | duas vezes sai |
| **Cobrinha** | vira à esquerda / à direita, **em relação à direção dela** | — | — | pausa e continua; no fim de jogo, recomeça | duas vezes sai |

## O que fazer
1. **`fw.h`:** constantes de tecla do GN-438, com nomes claros:
   - `FW_KEY_M`, `FW_KEY_M_LONG`, `FW_KEY_PREV`, `FW_KEY_NEXT`, `FW_KEY_PREV_LONG`, `FW_KEY_NEXT_LONG`, `FW_KEY_PLAY`, `FW_KEY_BACK`;
   - nenhum app usa mais `0x11`/`0x12`.
2. **Mp3tris e Flutter** com os controles da tabela.
3. **Cobrinha** (`sdk/apps/cobrinha/`), app novo:
   - **Tela cheia 128×160**: faixa de placar no topo (16 px) e campo em grade de 8 px abaixo.
   - **Cores do OpenPod 2.2:** fundo preto, cobrinha verde `(120,220,120)`, comida vermelha `(255,82,82)`.
   - Começa com 3 segmentos. Cada comida cresce 1 e acelera um pouco, até um limite. Bater na parede ou nela mesma é "Fim de jogo"
     com a pontuação.
   - **Desenho como o Mp3tris:** uma imagem indexada num buffer do heap do LVGL, alocado ao abrir e liberado no `LV_EVENT_DELETE`;
     timer do LVGL, apagado no `DELETE`.
   - Sem `.data`/`.bss`, sem som, aleatório com semente do `lv_tick_get`.
   - **Nome no menu:** "Cobrinha" em português e "Snake" nos outros idiomas.
     - O idioma atual é lido de onde o `get_lang_str` (`0xD2108C`) lê, com prova no ORIGINAL.
     - Se não fechar com prova, "Snake" em todos.
4. **Menu Aplicativos:** Despertador, Imagem, Flutter, Mp3tris, Cobrinha.
   - Provar que 5 linhas cabem ou rolam: a lista e o grupo do LVGL têm de levar o foco até a 5ª linha.
   - Se não couber, registrar e decidir pelo caminho mais seguro.
5. **Receita** `reload_3.1c` = a da 3.1b com o SDK novo.
   - A compilação reproduzível continua.
   - A diferença contra a 3.1b fica só no lote `0x1AB000+` e no `bl` do gancho.

## O que entregar
1. `docs/tarefas/023-analise.md`: o mapa de teclas aplicado, o idioma, o menu de 5 linhas e o desenho da Cobrinha.
2. Testes em `tests/test_reload_3_1.py` ou num arquivo novo:
   - nenhum app usa `0x11`/`0x12`;
   - as constantes de tecla;
   - 5 itens no menu;
   - compilação reproduzível, sem `.data`/`.bss`, bit Thumb;
   - diferença contra a 3.1b;
   - nada abaixo de `0xE000`, nem no setor `0xD000`, nem na PSMP.
3. Kit por `gera_versao` **com a base padrão (ORIGINAL)**:
   - carimbo **`Reload 3.1c`**;
   - `release/OpenPod-Reload-3.1c/` com `TESTAR.txt` curto: os controles de cada jogo, a Cobrinha completa (virar, comer, acelerar, fim de
     jogo, recomeçar, pausar, sair) e volta de segurança: 3.1b.
   - O Flashloader é copiado pela coordenação.
4. README do pacote: "New in 3.1c", jogos descritos pelo estilo, crédito ao Dmitry Brant mantido.
5. Entrada no `docs/CHANGELOG.md`.

**Não publicar.** Commit obrigatório antes do sinal.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; `sh tools/ci.sh` verde.
- LVGL só na tarefa de UI, nada que espere nela; bit Thumb em todo ponteiro de função.
- Não usar `cd` nem caminho absoluto; nada em `/tmp`.

Sinal final sozinho numa linha: `PRONTO-023` ou `ESCALADA-023`.
