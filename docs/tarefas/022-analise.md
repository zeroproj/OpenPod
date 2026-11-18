# Ficha 022 — análise do SDK em C e dos jogos (Reload 3.1)

Base: Reload 3.0, sha256 `43aaf5d51c364e03f9934aba0348230dda4911c2e7264c34555f69554c36ec32`.
Fonte de verdade: `firmware/ORIGINAL/GN438_original.bin` (sha256 `b7cd5eb9…`).
Referência: `referencias/SL6801_player`, commit `0361e2c`, usada com permissão
(D15, crédito a Dmitry Brant).

## 1. Tabela de funções do `fw.h`

Cada endereço abaixo foi achado no ORIGINAL por prólogo, chamador ou string de
log, e é travado por `tests/test_reload_3_1.py::test_fw_h_addresses`. Onde a
referência não tem a função, a coluna fica `—`.

| Função | Referência | Nosso GN-438 | Evidência | Estado |
|---|---|---|---|---|
| `lv_mem_alloc` | `0x00D3909C` | `0x00D58188` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_mem_free` | `0x00D39030` | `0x00D5811C` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_disp_get_scr_act` | `0x00D27E88` | `0x00D46E24` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_disp_get_layer_top` | `0x00D27EF0` | `0x00D46E8C` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_disp_get_hor_res` | `0x00D377B8` | `0x00D568A4` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_disp_get_ver_res` | `0x00D377E0` | `0x00D568CC` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_create` | `0x00D2A250` | `0x00D491EC` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_del` | `0x00D2E3B4` | `0x00D4D350` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_size` | `0x00D2B27E` | `0x00D4A21A` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_width` | `0x00D2B21E` | `0x00D4A1BA` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_height` | `0x00D2B24E` | `0x00D4A1EA` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_pos` | `0x00D2B338` | `0x00D4A2D4` | prólogo + desmonte `(obj,x,y)` | CONFIRMADO |
| `lv_obj_align` | `0x00D2B406` | `0x00D4A3A2` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_add_flag` | `0x00D2A268` | `0x00D49204` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_clear_flag` | `0x00D2A2AE` | `0x00D4924A` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_invalidate` | `0x00D2B770` | `0x00D4A70C` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_get_width` | `0x00D2B4C2` | `0x00D4A45E` | desmonte: `[+0x18]-[+0x14]+1` | CONFIRMADO |
| `fw_obj_parent` | — | `0x00D4D1FC` | comportamento `[obj+4]` | PROVÁVEL |
| `lv_timer_create` | `0x00D39F34` | `0x00D59020` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_timer_del` | `0x00D39FA4` | `0x00D59090` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_tick_get` | `0x00D37980` | `0x00D56A6C` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_add_event_cb` | — | `0x00D47064` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_remove_event_cb` | `0x00D28148` | `0x00D470E4` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_align` | `0x00D2E074` | `0x00D4D010` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_pad_top` | `0x00D2E080` | `0x00D4D01C` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_pad_bottom` | `0x00D2E08C` | `0x00D4D028` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_pad_left` | `0x00D2E098` | `0x00D4D034` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_pad_right` | `0x00D2E0A4` | `0x00D4D040` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_radius` | `0x00D2E0C8` | `0x00D4D064` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_bg_color` | `0x00D2E0F6` | `0x00D4D092` | propriedade 0x20 | CONFIRMADO |
| `lv_obj_set_style_bg_opa` | `0x00D2E118` | `0x00D4D0B4` | propriedade 0x21 | CONFIRMADO |
| `lv_obj_set_style_border_color` | `0x00D2E12C` | `0x00D4D0C8` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_border_width` | `0x00D2E158` | `0x00D4D0F4` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_border_side` | `0x00D2E164` | `0x00D4D100` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_text_color` | `0x00D2E16E` | `0x00D4D10A` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_text_font` | — | `0x00D4D12E` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_obj_set_style_text_align` | `0x00D2E19E` | `0x00D4D13A` | propriedade de alinhamento | CONFIRMADO |
| `lv_label_create` | `0x00D3F1FC` | `0x00D5E2E8` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_label_set_text` | `0x00D3FCA8` | `0x00D5ED94` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_label_set_long_mode` | `0x00D3FE18` | `0x00D5EF04` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_img_create` | `0x00D3E764` | `0x00D5D850` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_img_set_src` | `0x00D3E77C` | `0x00D5D868` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_event_get_code` | `0x00D28098` | `0x00D47034` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_event_get_param` | `0x00D2809C` | `0x00D47038` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_group_get_default` | `0x00D284D0` | `0x00D4746C` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_group_add_obj` | `0x00D28580` | `0x00D4751C` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_group_focus_obj` | `0x00D28714` | `0x00D476B0` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_group_focus_next` | — | `0x00D474C4` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_group_focus_prev` | — | `0x00D474DC` | prólogo no ORIGINAL | CONFIRMADO |
| `lv_group_get_focused` | `0x00D286AC` | `0x00D47648` | prólogo no ORIGINAL | CONFIRMADO |
| `fw_log` | `0x000002B0` | `0x000002B0` | ROM de boot; chamada em `0xD2EF72` | CONFIRMADO |
| `FW_MENU_PAGE_CREATE` | — | `0x00D2F0A0` | criador da página 0x53 | CONFIRMADO |
| `FW_MENU_LIST_ITEM_CREATE` | — | `0x00D21764` | prólogo no ORIGINAL | CONFIRMADO |
| `FW_MENU_LIST_ITEM_LAYOUT` | — | `0x00D51704` | prólogo no ORIGINAL | CONFIRMADO |

`FW_PAGE_MENU_EVENT_CB` tem bit Thumb e não usa `FW_FN`: ponteiro
`0x00D2EF5D`, função em `0x00D2EF5C`, primeiros bytes `454b1b68`.

## 2. Gancho e menu

- O `bl` de fábrica em `0x00123CF8` chama `0xD2F0A0` e é `0b f0 d2 f9`
  (halfwords `F00B F9D2`). A ferramenta confere esses bytes antes de escrever.
- O hook chama `FW_MENU_PAGE_CREATE`, reaproveita `item[2]` para o primeiro
  app e acrescenta uma linha por app extra. `Back` curto funciona porque o
  event cb de fábrica `0xD2EF5C` trata `0x81` antes de olhar o foco.
- Ordem resultante: **Despertador, Imagem, Flutter, Mp3tris**.
- **Divergência registrada:** a ficha 022 pedia o 3º item como "Jogos" com uma
  tela/lista própria. O decisor mudou para **jogos direto no menu Apps**; o
  Dicionário (item 2) sai e os jogos entram como linhas. O `docs/CHANGELOG.md`
  registra a mudança.
- **3.1a diag:** item 2 vira "Teste de teclas"; não há linhas extras.

## 3. Build e imagens

- `tools/build_sdk.py`: `python3 -m ziglang cc` 0.13.0, flags
  `-mthumb -Os -std=c11 -ffreestanding -fno-builtin -fno-stack-protector
  -ffunction-sections -fdata-sections -fno-pic -mcpu=cortex_m4
  -mfloat-abi=soft -target thumb-freestanding-eabi`; link
  `-nostdlib -static -Wl,--gc-sections -Wl,-e,hook_home_menu_create
  -Wl,--build-id=none -T sdk/app.ld`.
- `zig objcopy` desta máquina falha (`_sigaction`, `_bzero`, `_abort`,
  `_exit`); o `.text` é extraído por um leitor ELF em Python. O hook vem de
  `e_entry & ~1`, com bit Thumb obrigatório.
- `sdk/app.ld`: `ORIGIN = 0x00DAB000`, `LENGTH = 0x51000`; `ASSERT` de
  `.data`/`.bss` zero e `.text` dentro do lote.
- Builds reproduzíveis: duas compilações dão o mesmo `app.bin`.
  - diag: 1256 B, hook `0x00DAB13C`, app sha `c3ee8d…`;
  - jogos: 9216 B, hook `0x00DAC942`, app sha `85faa090…`.
- Imagens geradas e conferidas contra a 3.0 (só lote + 4 bytes do `bl`):
  - 3.1a diag: sha `3fc72a964d10c82b…`, hook `0xDAB13C`;
  - 3.1b: sha `9c02556d70719a95…`, hook `0xDAC942`.
- `tests/test_reload_3_1.py` passa (7 testes): repro, sem `.data/.bss`,
  prólogos, Thumb nos `.o`, tabela de apps, ganchos/diffs/PSMP e recusas.
  `sh tools/ci.sh` verde.

## 4. Som e parada da música — ESCALADA

Decisão da ficha: **sem som** nesta versão se as regras de segurança não
fecharem. O SDK não porta `sound.c`; os jogos são silenciosos.

A diretiva posterior do decisor pediu **parar a música ao abrir qualquer
jogo/app**, como a página de Imagem faria. A investigação no ORIGINAL:

- String `"Music would be stopped if you open the picture, continue?"` em
  `0xC5CFC7`, **id 140** da tabela de idioma. Tabela do inglês `0xC52AA4`,
  português `0xC53B84`; resolvedor `get_lang_str 0xD2108C`.
- Página de Imagem: `0x15 → 0xD33AF4` (`page_pict_list_create`, event cb
  `0xD3388C`); visualizador `0x16 → 0xD3404C` (`page_pict_play_create`,
  event cb `0xD33EFC`); `0x17 → 0xD3458C` (`page_record_menu_create`).
- O ENTER da lista (`0xD339E0`) só chama `0xD23510(0x15, 4, índice, …)`.
  Nem a lista nem o visualizador chamam `get_lang_str(140)`, função de
  áudio ou `0xD23510` com o id 140. **Não há, neste firmware, caminho de
  fábrica que mostre o aviso ou pare a música ao abrir a imagem.**
- A API de mídia provável é `0xD40630` (play), `0xD40660` (stop, cmd 5),
  `0xD4067E` (pause) e `0xD4069C` (seek), que enfileiram por `0xD4124C`.
  `0xD4124C` usa `0xD6AE38(8)` e `0x816DB2` com timeout `-1` — **pode
  bloquear**. O stop interno `0xD40610` fecha `/dev/audio0` e dorme 10 ms.
  Chamar qualquer um da tarefa de UI viola a 020 §2.
- Não há chamada dessas funções nas páginas de imagem, e não foi achado um
  caminho alternativo comprovado (tarefa de áudio própria, semáforo ou
  fila não bloqueante) no nosso firmware.

**Conclusão:** a parada de música **não fecha com prova**. Não foi
implementada; os jogos continuam sem som e a música, se estiver tocando,
não é parada. Fica para o arquiteto decidir entre (a) aceitar sem parada,
(b) autorizar uma tarefa própria que enfileire o stop, ou (c) uma ficha
nova de áudio. Kits e publicação ficam suspensos até essa decisão.

## 5. O que ficou de fora

- Som dos jogos (ficha 022 §4: sem som).
- Parada da música ao abrir app (diretiva nova; ver §4).
- `fw_obj_parent` é PROVÁVEL como símbolo; o comportamento `[obj+4]` está
  confirmado.
- Flashloader binário ausente em `firmware/VENDOR/`; o kit, quando sair,
  segue o aviso do `gera_versao`.
