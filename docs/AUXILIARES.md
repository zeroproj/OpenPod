# AUXILIARES — as funcoes sem nome, identificadas por comportamento

Gerado por `tools/mapa_auxiliares.py` sobre `firmware/ORIGINAL/GN438_original.bin`.

| | |
|---|---|
| funcoes detectadas (prologo `push {..,lr}`) | 3210 |
| com nome (`docs/SIMBOLOS.md`) | 412 |
| **anonimas** | **2798** |
| arestas de chamada | 11283 |

Nome nao da para inventar; comportamento da para medir. A lista
abaixo ranqueia as anonimas por **numero de chamadores distintos**.
Uma funcao chamada por dezenas de telas e infraestrutura — e é onde
um patch nosso tem o maior alcance, para o bem e para o mal.

**Limites:** funcoes folha sem prologo nao sao vistas, e chamadas
por ponteiro (callback) nao entram no grafo. Muitos chamadores e
evidencia forte; poucos chamadores **nao** e evidencia de nada.

## As mais chamadas

| # | endereco | chamadores | camada | chama (por nome) | ja identificamos |
|---|---|---|---|---|---|
| 1 | `0x10D818` | **173** | PRESENTER | — | PRESENTER -> VIEW: envia a mensagem pelo buffer circular. A mais chamada do presenter (173) |
| 2 | `0x15ED94` | **115** | LVGL/infra | `lv_mem_realloc` | lv_label_set_text |
| 3 | `0x14C8EC` | **112** | LVGL/infra | — | — |
| 4 | `0x176854` | **92** | LVGL/infra | — | — |
| 5 | `0x15EF04` | **91** | LVGL/infra | — | — |
| 6 | `0x177C9C` | **91** | LVGL/infra | — | — |
| 7 | `0x10D880` | **88** | PRESENTER | — | monta struct de mensagem de 0x24 bytes na pilha |
| 8 | `0x1777CC` | **87** | LVGL/infra | — | — |
| 9 | `0x158188` | **85** | LVGL/infra | — | — |
| 10 | `0x157F3C` | **83** | LVGL/infra | — | — |
| 11 | `0x0F780C` | **82** | sistema/tarefas | — | alocador: confere o limite, loga erro, aloca |
| 12 | `0x176C0A` | **81** | LVGL/infra | — | — |
| 13 | `0x0F7840` | **80** | sistema/tarefas | — | — |
| 14 | `0x15E2E8` | **79** | LVGL/infra | — | lv_label_create |
| 15 | `0x14A3A2` | **70** | LVGL/infra | — | lv_obj_align |
| 16 | `0x14A21A` | **69** | LVGL/infra | — | lv_obj_set_size |
| 17 | `0x149204` | **68** | LVGL/infra | — | — |
| 18 | `0x19FD54` | **68** | LVGL/infra | — | — |
| 19 | `0x14751C` | **66** | LVGL/infra | `lv_obj_allocate_spec_attr` | — |
| 20 | `0x14A1BA` | **64** | LVGL/infra | — | lv_obj_set_width |

## Auxiliares ja identificados por comportamento

Nenhum destes tem nome no binario. Foram identificados pelo que
fazem, ao longo do projeto e nesta varredura.

| endereco | chamadores | confianca | o que e |
|---|---|---|---|
| `0x0F780C` | 82 | PROVAVEL | alocador: confere o limite, loga erro, aloca |
| `0x0F83E4` | — | CONFIRMADO | escreve no buffer circular (moldura 0x55AA+tam) |
| `0x0F8444` | 1 | CONFIRMADO | LE do buffer circular; consumido por watch_view_rec_analysis -> view_page_msg_analysis |
| `0x10D818` | 173 | CONFIRMADO | PRESENTER -> VIEW: envia a mensagem pelo buffer circular. A mais chamada do presenter (173) |
| `0x10D880` | 88 | HIPOTESE | monta struct de mensagem de 0x24 bytes na pilha |
| `0x121384` | 14 | CONFIRMADO | getter de cor de TEXTO (fabrica: -1 = branco) |
| `0x12138A` | 7 | CONFIRMADO | getter de cor de FUNDO (fabrica: 0 = preto) |
| `0x121690` | 59 | CONFIRMADO | cria CONTEINER da lista |
| `0x1216F0` | 51 | CONFIRMADO | cria FAIXA superior |
| `0x121764` | 36 | CONFIRMADO | cria LINHA de lista |
| `0x1226AC` | 2 | CONFIRMADO | cria TITULO (usado pelo patch_titulos) |
| `0x123740` | 1 | CONFIRMADO | view_icon_create |
| `0x147654` | — | CONFIRMADO | lv_group_send_data — ponto unico de tecla |
| `0x14924A` | 42 | CONFIRMADO | lv_obj_clear_flag |
| `0x14A1A2` | — | CONFIRMADO | lv_obj_set_pos |
| `0x14A1BA` | 64 | CONFIRMADO | lv_obj_set_width |
| `0x14A1EA` | 53 | CONFIRMADO | lv_obj_set_height |
| `0x14A21A` | 69 | CONFIRMADO | lv_obj_set_size |
| `0x14A3A2` | 70 | CONFIRMADO | lv_obj_align |
| `0x14CAC4` | — | CONFIRMADO | lv_obj_set_local_style_prop — o despachante |
| `0x14D064` | 38 | CONFIRMADO | set_style_radius (96) |
| `0x14D092` | 44 | CONFIRMADO | set_style_bg_color (32) |
| `0x14D0C8` | 17 | CONFIRMADO | set_style_border_color (48) |
| `0x14D0F4` | 24 | CONFIRMADO | set_style_border_width (50) |
| `0x14D100` | 50 | CONFIRMADO | set_style_border_side (51) |
| `0x14D10A` | 33 | CONFIRMADO | set_style_text_color (87) |
| `0x14D12E` | 67 | CONFIRMADO | set_style_text_font (89) |
| `0x157B48` | 29 | CONFIRMADO | palette_main |
| `0x15B890` | 12 | CONFIRMADO | lv_obj_create |
| `0x15E2E8` | 79 | CONFIRMADO | lv_label_create |
| `0x15ED94` | 115 | CONFIRMADO | lv_label_set_text |
| `0x16B6A8` | 4 | PROVAVEL | NV: grava chave (tail-call 0x00D6CEA4) |
| `0x16B6BC` | 3 | PROVAVEL | NV: le chave (tail-call 0x00D6CBDE) |
