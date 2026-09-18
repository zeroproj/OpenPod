# OpenPod — GUI_ANALYSIS

Análise do sistema gráfico original do GN-438 (yp3_2.0.43).

---

## 1. Framework — CONFIRMADO

O firmware usa **LVGL v8**, compilado a partir da árvore:

```text
F:\pen133_yp3_mp\spark2\src\gui8\lvgl\src\...
```

O diretório `gui8` e a presença de `lv_obj_class.c`, `lv_obj_tree.c`,
`lv_obj_style.c`, `lv_flex.c` e `lv_tlsf.c` fixam a versão na série **8.x**
(esses arquivos não existem no LVGL 7 e anteriores). A versão menor exata
(8.0 / 8.1 / 8.2 / 8.3) **não foi determinada**.

### Módulos LVGL presentes (36 arquivos identificados por path)

| Grupo | Arquivos |
|---|---|
| core | `lv_disp`, `lv_event`, `lv_group`, `lv_indev`, `lv_obj`, `lv_obj_class`, `lv_obj_pos`, `lv_obj_style`, `lv_obj_tree`, `lv_refr` |
| draw | `lv_draw_img`, `lv_draw_label`, `lv_draw_mask`, `lv_draw_rect`, `lv_draw_blend`, `lv_img_cache`, `lv_img_decoder` |
| widgets | `lv_btnmatrix`, `lv_dropdown`, `lv_img`, `lv_label`, `lv_roller`, `lv_textarea` |
| extra | `lv_flex` (layout), `lv_chart` |
| hal | `lv_hal_disp`, `lv_hal_indev` |
| misc | `lv_anim`, `lv_color`, `lv_fs`, `lv_mem`, `lv_style`, `lv_timer`, `lv_tlsf`, `lv_txt` |

**Consequência para o OpenPod:** a lista de widgets é enxuta. Existem
`label`, `img`, `roller`, `btnmatrix`, `dropdown` e `textarea` — mas **não**
há evidência de `lv_list`, `lv_table`, `lv_bar`, `lv_slider` ou `lv_arc`.
O menu em lista vertical previsto no Design System provavelmente é montado
com containers + labels + flex, não com `lv_list`.

---

## 2. Display — CONFIRMADO

| Propriedade | Valor | Evidência |
|---|---|---|
| Resolução | **128 × 160** | duas imagens `INDEXED_8` de exatamente 128×160 (papel de parede e folha de ícones do menu) |
| Controlador (aplicação) | **GC9106** | string `gc9106_lcd_init` em `0x000E2449` |
| Controlador (bootloader) | **ST7789S** | string `st7789s_lcd_init` em `0x0000C079` |
| Formato de cor | **RGB565 (16 bits)** | string `RGB565 lcdc_read color:0x%x`; imagens `TRUE_COLOR_CHROMA` com exatamente 2 bytes/pixel |
| Nó de dispositivo | `/dev/lcd` | presente no boot e na FIRM |

> **Atenção.** O bootloader inicializa um ST7789S e a aplicação um GC9106.
> Isso pode significar (a) suporte a dois painéis diferentes com detecção
> em runtime, ou (b) código morto herdado do SDK. **NÃO RESOLVIDO.**
> Determinar qual driver realmente roda é pré-requisito para qualquer
> alteração de layout dependente de resolução.

### Impacto direto no Design System

128×160 é uma tela **pequena e retrato**. A tela de Now Playing proposta
em `OpenPod_Design_System.md` (capa + título + artista + álbum + tempo +
progresso + 3 botões) é densa demais para 128×160 com uma fonte de 12 px
de altura — sobram cerca de **13 linhas de texto** na tela inteira.
O design terá de ser simplificado. Isso é exatamente o caso previsto na
regra "Hardware/Firmware Reality > Design Spec".

---

## 3. Fontes — CONFIRMADO E TOTALMENTE DECODIFICADO

Formato: `lv_font_fmt_txt` do LVGL v8, compilado com
**`LV_FONT_FMT_TXT_LARGE = 1`** (campos alargados → descritor de 16 bytes).

### Descritor de glifo (16 bytes, little-endian)

```c
struct {
    uint32_t bitmap_index;  // +0x00  offset no blob de bitmaps
    uint32_t adv_w;         // +0x04  avanço horizontal (px)
    uint16_t box_w;         // +0x08  largura (px)
    uint16_t box_h;         // +0x0A  altura (px)
    int16_t  ofs_x;         // +0x0C
    int16_t  ofs_y;         // +0x0E
};
```

`tamanho_do_bitmap = ceil(box_w * bpp / 8) * box_h`

### Fonte de texto principal

| Propriedade | Valor |
|---|---|
| Blob de bitmaps | `0x0005E7E0` – `0x00086C32` (164.946 B) |
| Tabela de glifos | `0x00086C44` – `0x000A27E4` |
| cmap (u16) | `0x000A27E6` |
| Glifos | **7.098** |
| Profundidade | **1 bpp** |
| Altura | **12 px** |
| Cobertura | 95 ASCII (8×N px) + **6.763 CJK** (16×12 px) |
| Faixa Unicode | U+0020 – U+FFE5 |

Validação: os glifos `A`, `a`, `g`, `p`, `5` e `中` (U+4E2D) foram
renderizados e conferem visualmente. Ferramenta: `tools/extract_fonts.py`.

> **Oportunidade enorme para o OpenPod.** Os 6.763 glifos CJK ocupam a
> maior parte dos ~165 KB do blob. Se o OpenPod não precisar de chinês,
> remover o CJK libera da ordem de **150 KB** — espaço mais que suficiente
> para uma tipografia melhor, mais pesos e mais ícones. **Ainda não
> verificado** se algum texto de UI carrega CJK obrigatoriamente.

### Conjuntos de ícones

| Conjunto | Tabela | Blob | bpp | Qtd. | Tamanhos típicos |
|---|---|---|---|---|---|
| `icons_main` | `0x000BE720` | `0x000B0DC4` | **4** | **675** | 12×12, 14×14, 14×12 |
| `icons_small` | `0x000A6568` | `0x000A5F71` | 4 | 24 | 12×11, 12×9, 10×11 |

Os ícones são **fontes de símbolo**: o cmap em `0x000C1150` mapeia
`U+F000`, `U+F001`, … — a faixa de símbolos do LVGL. São renderizados
como texto, com 4 bits de alfa por pixel (antialiasing).

Validação: renderizados e reconhecíveis (lupa, nota musical, setas).
675 ícones exportados em PNG para `extracted/icons_main/`.

> **Isto é o coração da Fase 1 do OpenPod.** Trocar um ícone é substituir
> um bitmap 4bpp de poucas dezenas de bytes. Se as dimensões forem
> mantidas, **nenhum offset muda** — só o conteúdo e o CRC da FIRM.
> É o caminho de menor risco que existe neste firmware.

---

## 4. Imagens — CONFIRMADO

Apenas **8** estruturas `lv_img_dsc_t` no dump inteiro. O grosso dos
gráficos são ícones-fonte, não imagens.

| Descritor | Formato | Dimensão | Conteúdo |
|---|---|---|---|
| `0x000C235C` | TRUE_COLOR_CHROMA | 50×50 | — |
| `0x000C36F0` | TRUE_COLOR_CHROMA | 50×50 | — |
| `0x000C4A84` | TRUE_COLOR_CHROMA | 50×50 | — |
| `0x000C5E18` | TRUE_COLOR_CHROMA | 50×50 | — |
| `0x000C71AC` | TRUE_COLOR_CHROMA | 16×16 | — |
| `0x000C73B8` | INDEXED_8 | 128×160 | papel de parede (gradiente azul) |
| `0x000CC7C4` | INDEXED_8 | 128×35 | **logotipo GENAI** |
| `0x000CDD50` | INDEXED_8 | 128×160 | **folha com os 9 ícones circulares do menu principal** |

`INDEXED_8` = paleta de 256 entradas BGRA (1024 B) seguida de 1 byte de
índice por pixel. `TRUE_COLOR_CHROMA` = RGB565 puro com cor-chave de
transparência.

Todas exportadas para `extracted/images/`.

> A folha 128×160 em `0x000CDD50` é literalmente a tela de menu do
> aparelho: Gravador, Vídeo, Microfone, FM, eBook, Fotos, Bluetooth,
> Configurações, Arquivos. Substituí-la por ícones no estilo iPod nano 2
> é provavelmente **a alteração visual de maior impacto e menor risco**
> do projeto inteiro.

---

## 5. Arquitetura de telas — CONFIRMADO

A interface é organizada em **páginas numeradas**, com um padrão de
nomenclatura consistente que sugere um padrão MVP
(`_presenter_key_analysis`, `ctrl_id`, `scr`).

**61 páginas identificadas:** page1–page35, page40–page49, page51, page55,
page56, page60, page68–page70, page76–page84.

### Callbacks por página

| Sufixo | Papel |
|---|---|
| `_process` | lógica principal / máquina de estados |
| `_scr_process` | eventos de tela (`lv_scr`) |
| `_btn_process` | eventos de botão |
| `_btnm_process` | eventos de `lv_btnmatrix` |
| `_cont_process` | eventos de container |
| `_index_process` | navegação por índice (listas roláveis) |
| `_mbox_process` | caixas de mensagem / diálogos |
| `_media_cb` / `_media_msg_analysis` | mensagens do subsistema de mídia |
| `_build_cb` | construção dinâmica de lista |
| `_deinit` | destruição da tela |

### Páginas com função identificável por seus callbacks

| Página | Evidência | Função provável |
|---|---|---|
| `page1` | `_music_build_cb`, `_video_build_cb`, `_pict_build_cb`, `_ebook_build_cb`, `_folder_build_cb`, `_record_build_cb`, `_img_process` | **menu principal** |
| `page3`, `page6`, `page7`, `page12`, `page19`, `page21` | `_cont_process` + `_index_process` | **listas navegáveis** (artistas / álbuns / músicas / pastas) |
| `page20` | `_show_video`, `_video_process`, `_media_cb`, `_deinit` | **reprodutor de vídeo** |
| `page22` | `_show_pict` | **visualizador de fotos** |
| `page24`, `page25` | `_record_build_cb`, `_get_record_filename`, `_init_record_para`, `_record_stop_timeout_cb` | **gravador de voz** |
| **`page4`** | `_btnm_process`, `_media_cb`; ações play/next/pre/speed/repeat/loop/love | **Now Playing — CONFIRMADO por disassembly** (ver `INPUT_MAP_COMPLETE.md` §7) |
| `page34` | `_media_msg_analysis`, `_label_process`, `_cont_process` | outra tela de mídia — função ainda não identificada |
| `page35` | `_paired_list_process`, `_search_list_process`, `_show_bt_option` | **Bluetooth** |
| `page43` | `_set_view_roller_date` | **ajuste de data** (usa `lv_roller`) |
| `page70` | `_key_process`, `_media_msg_analysis` | camada de tratamento de teclas |
| `page82` | mesmos `_build_cb` de `page1` | segundo menu / navegador de arquivos |

> **Corrigido em 2026-09-12.** A hipótese original apontava `page34` como
> Now Playing. O disassembly de `pstr_page4_process` (`0x00D08A90`) mostra
> que a tela do reprodutor é **`page4`**: ela contém as ações `- play`,
> `- next`, `- pre`, `- speed`, `- repeat`, `- loop` e `- love`.
> A função de `page34` continua não identificada.

---

## 6. Idiomas — CONFIRMADO

Oito idiomas embutidos, com os textos em `0x00053000`–`0x0005E000`:

**Deutsch · English · Español · Français · Italiano · Nederlands ·
Português · 中文**

Português já está presente (`Livro digital`, `Todas as músicas`,
`Dispositivos emparelhados`, `Configuração de fábrica`, …), o que elimina
a necessidade de traduzir a UI do zero para o OpenPod.

---

## 7. Sistema de arquivos de recursos

A string `r://60` indica um driver `lv_fs` registrado com a letra `r`,
que resolve recursos por **identificador numérico**. Apenas uma ocorrência
foi encontrada, então o mecanismo **não foi mapeado**. Os recursos
gráficos principais são endereçados por ponteiro absoluto na flash XIP,
não por esse driver.

Status: **NÃO IDENTIFICADO** — precisa de disassembly do driver `lv_fs`.

---

## 8. Comparação: YP3 original × Design System OpenPod

| Item do Design System | Situação no YP3 | Viabilidade |
|---|---|---|
| Listas verticais com item destacado | containers + flex + labels existem | **Fácil** |
| Cabeçalho superior | labels existem | **Fácil** |
| Ícones simples e monocromáticos | 675 ícones 4bpp, tamanho fixo, substituíveis | **Fácil** |
| Tipografia legível | fonte 1bpp 12 px substituível; ~150 KB liberáveis ao cortar CJK | **Média** |
| Alto contraste / paleta clara | RGB565; papel de parede substituível | **Fácil** |
| Now Playing com capa | 128×160 é apertado; capa exigiria decodificação de JPEG do arquivo | **Difícil** |
| Barra de progresso | sem `lv_bar`/`lv_slider` evidente; teria de ser desenhada | **Média** |
| Animações | `lv_anim` presente | **Média** (custo de CPU não medido) |
| Reestruturar hierarquia de menus | exige alterar lógica de 61 páginas em Thumb-2 sem símbolos | **Difícil** |

### Ordem recomendada para a Fase 1

1. Folha de ícones do menu principal (`0x000CDD50`) — maior impacto visual.
2. Ícones individuais 4bpp em `icons_main` — refinamento.
3. Papel de parede (`0x000C73B8`).
4. Logotipo de boot (`0x000CC7C4`).
5. Textos de UI em português.
6. Fonte — só depois de dominar o processo de rebuild.


---

# PARTE II — Arquitetura das páginas LVGL (2026-09-12)

## 9. Localização dos handlers — CONFIRMED

Todas as **61** páginas têm uma função `pstr_pageNN_process`, localizada
pelo xref ao seu nome. Os handlers estão dispostos em ordem crescente de
número de página no binário, entre `0x100D00` e `0x10CE00` (offsets de
arquivo; endereço XIP = offset + `0x00C00000`).

| Página | Pool do nome | Página | Pool | Página | Pool |
|---|---|---|---|---|---|
| 1 | `0x101248` | 20 | `0x103644` | 47 | `0x109E04` |
| 2 | `0x103230` | 21 | `0x103AA4` | 48 | `0x109F98` |
| 3 | `0x105F74` | 22 | `0x103CA4` | 49 | `0x10A090` |
| **4** | `0x108D3C` | 23 | `0x103FCC` | 51 | `0x10A674` |
| 5 | `0x10A450` | 24 | `0x1042E4` | 55 | `0x10A7FC` |
| 6 | `0x10AEFC` | 25 | `0x104914` | 56 | `0x10AAD8` |
| 7 | `0x10B63C` | 26 | `0x1053AC` | 60 | `0x10B02C` |
| 8 | `0x10C0D0` | 27 | `0x105708` | 68 | `0x10B160` |
| 9 | `0x10CE80` | 28 | `0x105820` | 69 | `0x10B278` |
| 10 | `0x101820` | 29 | `0x105B80` | 70 | `0x10BA10` |
| 11 | `0x10195C` | 30 | `0x106328` | 76 | `0x10BB24` |
| 12 | `0x101CEC` | 31 | `0x1064D8` | 77 | `0x10BC38` |
| 13 | `0x10208C` | 32 | `0x106660` | 78 | `0x10BDC4` |
| 14 | `0x1021E8` | 33 | `0x1067B8` | 79 | `0x10BFDC` |
| 15 | `0x102314` | 34 | `0x106FE0` | 80 | `0x10C3DC` |
| 16 | `0x102458` | 35 | `0x1082EC` | 81 | `0x10C574` |
| 17 | `0x1025C0` | 40 | `0x109320` | 82 | `0x10CA04` |
| 18 | `0x10299C` | 41 | `0x109420` | 83 | `0x10CB28` |
| 19 | `0x102D00` | 42 | `0x109588` | 84 | `0x10CD78` |
| | | 43–46 | `0x109800`+ | | |

---

## 10. Estrutura da mensagem de UI — CONFIRMED

Lida de forma idêntica por todos os `pstr_pageNN_process`:

| Offset | Campo | Observado |
|---|---|---|
| `+0x02` | `cmd` | deve ser `6`; senão `"no msgp->cmd"` |
| `+0x08` | página de destino | comparada com a página ativa; senão `"curr page error"` |
| `+0x0A` | `ctrl_grp` | `1`, `4`, `5` |
| `+0x0C` | `ctrl_id` | índice do controle focado |
| `+0x0E` | `type` | `1` |
| `+0x14` | `sta` | estado |

Cadeia de erro padronizada, útil como assinatura ao identificar páginas:
`no msgp->cmd` → `no ctrl_grp` → `no type` → `no event` → `no ctrl_id` →
`no sta`.

---

## 11. `page1` — MENU PRINCIPAL — CONFIRMED

Endereço: `0x00D00D00`–`0x00D01340`.

Callbacks de construção, um por item de menu:

| Callback | Item |
|---|---|
| `page1_music_build_cb` | Música |
| `page1_video_build_cb` | Vídeo |
| `page1_pict_build_cb` | Fotos |
| `page1_ebook_build_cb` | eBook |
| `page1_record_build_cb` | Gravador |
| `page1_folder_build_cb` | Arquivos |

Mais `page1_img_process` (ícones) e `page1_build_cb` (construtor geral).

Strings de estado que revelam o modelo de dados:

```text
"-%s music dirty: %d "        base de músicas precisa reindexar
"-%s pict dirty: %d "         idem, fotos
"-recorder db is dirty ret %d error!"
"-%s total = %d "             contagem de itens
"fmsearch"                    busca de estações FM
"screen"                      recurso de tela
```

> O menu principal **é construído dinamicamente** a partir de bases de
> dados com marcação *dirty*. Trocar a **aparência** (ícones, ver §4) não
> toca nessa lógica. Trocar a **ordem ou o conjunto** de itens, sim.

---

## 12. `page3` e famílias — LISTAS ROLÁVEIS — CONFIRMED

Assinatura comum a `page3`, `page6`, `page7`, `page12`, `page19`, `page21`:
`_cont_process` + `_index_process`.

```text
"-%s PgUp, top_index: %d, select: %d, total: %d "
"-%s PgDn, top_index: %d, select: %d, total: %d "
"%d/%d"                       indicador de posição
"-page3 names malloc fail!!!" alocação dinâmica dos rótulos
"wave_scan"
```

Modelo de lista — CONFIRMED:

```text
top_index   primeiro item visível
select      item destacado
total       total de itens
```

> É exatamente o modelo que o Design System pede (lista vertical com item
> destacado e indicador de posição). **Já existe.** O OpenPod não precisa
> reimplementar rolagem — precisa apenas reestilizar.

---

## 13. `page4` — NOW PLAYING — CONFIRMED

Endereço: `0x00D08900`–`0x00D08FC0`. Confirmado por disassembly em
`docs/INPUT_MAP_COMPLETE.md` §7.

Os controles são um **`lv_btnmatrix`** (`page4_btnm_process`), com
`ctrl_id` de 0 a 7:

| Ação | String | Endereço |
|---|---|---|
| play / pause | `"- play "` | `0x00D08C1C` |
| anterior | `"- pre "` | `0x00D08BA4` |
| próxima | `"- next "` | `0x00D08C66` |
| velocidade | `"- speed "` | `0x00D08CEC` |
| repetir | `"- repeat "` | `0x00D08D04` |
| loop | `"- loop "` | `0x00D08D26` |
| favorito | `"- love "` | `0x00D08D92` |

Tipos de clique tratados: `-short click`, `-long pressed`,
`-long pressed repeat`, `-released`.

Outros elementos: `page4_media_cb` (`"-%s amsgp->Duration: %d "` — duração
da faixa), `keyfreq` e `keyrelease` (recursos de repetição de tecla).

### Implicação para o Design System

> A tela Now Playing do YP3 é uma **matriz de botões com foco**, não uma
> tela estática. O layout proposto em `OpenPod_Design_System.md` §7 tem de
> ser expresso como um `lv_btnmatrix` de até 8 posições, ou a navegação
> por foco quebra.
>
> Isso reforça a conclusão da §2: em 128×160 com fonte de 12 px, o design
> precisa ser simplificado — e agora sabemos que a restrição não é só de
> espaço, é **estrutural**.


---

# PARTE III — Recursos visuais do menu principal e o patch V001 (2026-09-12)

## 14. ⚠️ Achado que muda a estratégia do patch — CONFIRMADO

A premissa de trabalho era que o menu principal usaria ícones 4bpp da
tabela `icons_main`. **Não usa.**

```asm
00D2ECD6  ldr r1, [pc, #0x124]   ; = 0x00CCDD50  (lv_img_dsc 128x160)
00D2ECDA  mov r0, sb
00D2ECDC  bl  #0xd5d868          ; lv_img_set_src(obj, &img)
```

`page_home_create` desenha **uma única imagem** `INDEXED_8` de 128×160
contendo os 9 ícones em grade 3×3. Nenhum ícone 4bpp participa do menu.

> Isso é **melhor** para o primeiro patch: um único recurso, tamanho fixo,
> sem tabela de índices, sem ponteiros a recalcular.

---

## 15. Esquema de nomes real das telas — CONFIRMADO

O binário contém **370** nomes de função no padrão
`page_<tela>_<papel>` — um mapa semântico completo da GUI, muito mais
informativo que o esquema numérico `pageNN`.

| Tela | Função de criação |
|---|---|
| **Menu principal** | `page_home_create` |
| Menu expandido | `page_expand_home_create` (usa as 4 imagens 50×50) |
| Submenu do home | `page_home_menu_create` |
| **Now Playing** | `page_music_play_create` |
| Artistas / Álbuns / Músicas | `page_music_artist_create`, `page_music_album_create`, `page_music_song_create` |
| Equalizador | `page_music_eq_create` |
| Bluetooth | `page_bt_menu_create` |
| FM | `page_fm_play_create`, `page_fm_preset_create`, `page_fm_band_create` |
| Fotos | `page_pict_list_create`, `page_pict_play_create` |
| Vídeo | `page_video_list_create`, `page_video_play_create` |
| eBook | `page_ebook_list_create`, `page_ebook_read_create`, … |
| Gravador | `page_record_menu_create`, `page_record_work_create` |
| Arquivos | `page_folder_list_create` |
| Ajustes | `page_set_menu_create` e ~20 subtelas |
| Idioma | `page_set_lang_create`, `page_lang_option_create` |
| Relógio de tela | `page_screen_clock_create` |

Papéis por tela: `_create`, `_event_cb`, `_event_reply`, `_scr_process`,
`_btn_process`, `_label_process`, `_mbox_process`, `_img_process`,
`_anim_process`.

> **Este é o mapa que faltava.** Qualquer trabalho futuro de interface
> deve partir daqui, não dos números `pageNN`.

---

## 16. A folha de ícones do menu — CONFIRMADO

| Propriedade | Valor |
|---|---|
| Descritor `lv_img_dsc_t` | `0x000CDD50` |
| Formato | `INDEXED_8` (`cf = 10`) |
| Dimensão | 128 × 160 |
| Tamanho declarado | 21.504 bytes |
| Paleta | `0x000CDD5C` – `0x000CE15C` (256 × BGRA) |
| Pixels | `0x000CE15C` – `0x000D315C` (20.480 B, 1 byte/px) |
| Índice de fundo | `1` = RGB(0,0,0), 66,6 % dos pixels |
| Referências | 1 — só `page_home_create` |

### Geometria da grade — CONFIRMADO

Derivada das faixas de linhas/colunas com conteúdo não-fundo:

| # | Item | Ícone | Posição | Tamanho | 1º pixel |
|---|---|---|---|---|---|
| 1 | **Música** | disco de vinil | (6, 16) | 33×31 | `0x0CE962` |
| 2 | **Vídeo** | play em círculo | (48, 16) | 32×31 | `0x0CE98C` |
| 3 | **Gravador** | microfone | (89, 16) | 31×31 | `0x0CE9B5` |
| 4 | **FM** | texto "FM" | (6, 65) | 33×31 | `0x0D01E2` |
| 5 | **eBook** | livro aberto | (48, 65) | 32×31 | `0x0D020C` |
| 6 | **Fotos** | imagem/montanha | (89, 65) | 31×31 | `0x0D0235` |
| 7 | **Bluetooth** | símbolo BT | (6, 112) | 33×31 | `0x0D1962` |
| 8 | **Ajustes** | engrenagem | (48, 112) | 32×31 | `0x0D198C` |
| 9 | **Arquivos** | pasta | (89, 112) | 31×31 | `0x0D19B5` |

Correspondência com os callbacks de `page1`: `music`, `video`, `record`,
`ebook`, `pict`, `folder` + FM, Bluetooth, Ajustes = **exatamente 9**.

### Tabela pedida

| Menu item | Texto | Ícone | Codepoint | Recurso | Handler |
|---|---|---|---|---|---|
| Música | idioma ativo | célula 1 | **n/a** | folha `0x0CDD50` | `page1_music_build_cb` |
| Vídeo | idioma ativo | célula 2 | n/a | idem | `page1_video_build_cb` |
| Gravador | idioma ativo | célula 3 | n/a | idem | `page1_record_build_cb` |
| FM | idioma ativo | célula 4 | n/a | idem | `page_fm_play_create` |
| eBook | `Livro digital` | célula 5 | n/a | idem | `page1_ebook_build_cb` |
| Fotos | `Imagem` | célula 6 | n/a | idem | `page1_pict_build_cb` |
| Bluetooth | idioma ativo | célula 7 | n/a | idem | `page_bt_menu_create` |
| Ajustes | `Configurar` | célula 8 | n/a | idem | `page_set_menu_create` |
| Arquivos | `Ver pastas` | célula 9 | n/a | idem | `page1_folder_build_cb` |

> **A coluna "codepoint" é `n/a` por um motivo de fato**, não por lacuna:
> os ícones do menu **não são glifos** de fonte de símbolo. Não há
> `U+Fxxx` envolvido. Os 675 ícones 4bpp existem e são usados em outras
> telas, mas **não neste menu** — CONFIRMADO.
>
> Os textos são resolvidos em runtime pelo idioma ativo (bloco
> `0x053000`–`0x05E000`); os literais em português acima são **PROVÁVEL**,
> não amarrados por disassembly a cada item.

---

## 17. Caminho A vs caminho B — decisão

| | **A — substituir recursos** | **B — modificar código LVGL** |
|---|---|---|
| O que muda | pixels da folha `0x0CDD50` | `page_home_create`, layout, foco |
| Offsets | **nenhum** | mudam |
| Tabelas | **nenhuma** | possivelmente |
| CRCs | só o da FIRM | idem, mais risco |
| Ferramenta | já existe (`rebuild_firmware.py`) | exigiria montador Thumb-2 |
| Impacto visual | **os 9 ícones do menu** | layout e navegação |
| Risco de brick | **baixo** | alto |
| Reversível | trivial | difícil |

**Decisão: A, sem hesitação.** Substituir os 9 ícones da folha produz a
maior mudança visual possível no menu com risco praticamente nulo — e o
caminho B nem é necessário para a Fase 1, já que o modelo de lista e o
`lv_btnmatrix` que o Design System pede **já existem** (§12, §13).

---

## 18. Patch V001 — executado e validado

### Recurso escolhido e por quê

**Célula 1 (Música), o disco de vinil.**

| Critério exigido | Atendido |
|---|---|
| É usado pelo menu | ✅ CONFIRMADO por disassembly |
| Dimensão pequena | ✅ 33×31 px |
| Mantém exatamente o mesmo tamanho | ✅ 1.023 px, área fixa |
| Não altera offsets | ✅ escrita in-place |
| Não exige alteração de tabelas | ✅ nenhuma tabela tocada |
| Só CRCs já suportados pelo rebuild | ✅ apenas o CRC da FIRM |

Motivo adicional: é o item **mais central para o OpenPod** — um player de
música — e o mais visível no canto superior esquerdo do menu.

### Operação

Recoloração determinística para **RGB(0, 150, 255)**, preservando a
luminância relativa de cada pixel e **mantendo o rótulo vermelho** do
disco (índices de paleta 5, 7, 8, 9, 10, 11, 12, 14).

Usa **apenas índices de paleta já existentes** — a paleta **não** é
alterada.

Ferramenta: `tools/patch_home_icon.py` (determinística e reexecutável).

### Bytes alterados

```text
716 bytes de pixels   0x0CE96C .. 0x0CF878   (42 faixas contíguas)
  2 bytes de CRC      0x00D01C .. 0x00D01D   (CRC da FIRM na ptable)
───────────────────────────────────────────────────────────────
718 bytes no total, em 43 faixas
paleta:  0 bytes alterados
tamanho: 2.097.152 -> 2.097.152 (inalterado)
```

### CRCs recalculados

| Campo | Antes | Depois | |
|---|---|---|---|
| CRC da partição FIRM | `0x49A6` | **`0x583A`** | recalculado |
| CRC da partição TONE | `0x9177` | `0x9177` | inalterado |
| `loadCrc` do bootloader | `0x759D` | `0x759D` | inalterado |
| `headerCrc` | `0x34DB` | `0x34DB` | inalterado |
| `loadCrc` da FIRM | `0x68E1` | `0x68E1` | inalterado |

Os três últimos não mudam porque o patch fica **além dos 4 KiB** cobertos
por `loadCrc` e **fora** do cabeçalho HLKJ — como previsto.

### Resultado

| | |
|---|---|
| Arquivo | `firmware/WORKING/GN438_openpod_v001.bin` |
| Tamanho | 2.097.152 bytes |
| **SHA-256** | `9dc755eef24e3e09c8939d90c89d9a241e0c6edd75b377c1792e743ccc79215c` |
| `validate_firmware.py` | **22 verificações OK, 0 falhas** |
| `fwhelper scan` (terceiros) | **limpo**, nenhuma divergência de checksum |
| Diff vs original | 718 bytes, 43 faixas, tamanho inalterado |
| Gravado no hardware | **NÃO** |

### Classificação

| Conclusão | Classe |
|---|---|
| O menu usa a folha `0x0CDD50`, não ícones 4bpp | **CONFIRMADO** |
| Geometria 3×3 e posição de cada célula | **CONFIRMADO** |
| Correspondência célula → item de menu | **CONFIRMADO** (9 callbacks ↔ 9 ícones) |
| Textos de cada item no idioma ativo | **PROVÁVEL** |
| Caminho A é superior ao B para a Fase 1 | **CONFIRMADO** |
| V001 é estruturalmente válido | **CONFIRMADO** (22 checks + validação de terceiros) |
| V001 **inicializa no aparelho** | **NÃO RESOLVIDO** — nunca foi gravado |

---

## Estilos da LVGL neste binário — a tabela de propriedades

> Levantada em 2026-09-13, depois que uma dedução errada sobre ela custou
> **duas versões** (V0xx, `patch_raio_selecao.py`). Está aqui para que
> ninguém precise deduzir de novo.

### O mecanismo

Todo estilo passa por um **despachante único**:

```text
0x00D4CAC4   set_local_style(obj, propriedade, valor, seletor)
```

Os "setters" que o código chama são cascas de 4 instruções sobre ele:

```asm
00D4D100   mov  r3, r2      ; seletor
00D4D102   mov  r2, r1      ; valor
00D4D104   movs r1, #0x33   ; propriedade  <- a unica coisa que varia
00D4D106   b.w  0xD4CAC4
```

Algumas propriedades de 32 bits (cores) usam uma casca maior, com
`bfi` para montar o valor — `0xD4D092` e `0xD4D10A` são desse tipo.

### A tabela, lida do próprio firmware

O campo é `propriedade | flags`, onde `0x0400` = herda e `0x1000` =
refaz o layout. A propriedade real são os **10 bits baixos**.

| Wrapper | campo | prop | LVGL v8 |
|---|---|---|---|
| `0x00D4CFE0` | `0x1001` | 1 | `WIDTH` |
| `0x00D4CFEC` | `0x1004` | 4 | `HEIGHT` |
| `0x00D4CFF8` | `0x1007` | 7 | `X` |
| `0x00D4D004` | `0x1008` | 8 | `Y` |
| `0x00D4D010` | `0x1009` | 9 | `ALIGN` |
| `0x00D4D01C` | `0x1010` | 16 | `PAD_TOP` |
| `0x00D4D028` | `0x1011` | 17 | `PAD_BOTTOM` |
| `0x00D4D034` | `0x1012` | 18 | `PAD_LEFT` |
| `0x00D4D040` | `0x1013` | 19 | `PAD_RIGHT` |
| `0x00D4D04C` | `0x1014` | 20 | `PAD_ROW` |
| `0x00D4D058` | `0x1015` | 21 | `PAD_COLUMN` |
| **`0x00D4D064`** | `0x0060` | **96** | **`RADIUS`** |
| `0x00D4D06E` | `0x0462` | 98 | `OPA` |
| `0x00D4D07A` | `0x1069` | 105 | `LAYOUT` |
| `0x00D4D086` | `0x146a` | 106 | `BASE_DIR` |
| `0x00D4D092` | `0x0020` | 32 | `BG_COLOR` |
| `0x00D4D0B4` | `0x0021` | 33 | `BG_OPA` |
| `0x00D4D0BE` | `0x0026` | 38 | ⚠️ **NÃO é utilizável como `BG_GRAD`** — ver abaixo |
| `0x00D4D0C8` | `0x0030` | 48 | `BORDER_COLOR` |
| `0x00D4D0EA` | `0x0031` | 49 | `BORDER_OPA` |
| `0x00D4D0F4` | `0x1032` | 50 | `BORDER_WIDTH` |
| `0x00D4D100` | `0x0033` | 51 | `BORDER_SIDE` |
| `0x00D4D10A` | `0x0457` | 87 | `TEXT_COLOR` |
| `0x00D4D12E` | `0x1459` | 89 | `TEXT_FONT` |
| `0x00D4D13A` | `0x145d` | 93 | `TEXT_ALIGN` |

**Classe: CONFIRMADO.** A tabela fecha sem sobra contra o enum da LVGL
v8, e dois membros já eram conhecidos por uso independente —
`0x00D4D12E` é a fonte (V016) e `0x00D4D092` é a cor de fundo (V021).

### Seletores de parte e estado, já confirmados

```text
0x00000004  LV_STATE_FOCUS_KEY     (usado na cor da seleção)
0x00010000  LV_PART_SCROLLBAR
0x00020000  LV_PART_INDICATOR
0x00040000  LV_PART_SELECTED
0x00050000  LV_PART_ITEMS
```

### ⚠️ A armadilha que isto resolve

O grupo 6 da LVGL v8 (`MISC`) **começa em 96**, e `RADIUS` é o primeiro
dele. Quem procurar `LV_STYLE_RADIUS` em documentação solta pode achar
`11` — que aqui é `TRANSFORM_HEIGHT`.

Foi esse o erro: duas versões setaram `TRANSFORM_HEIGHT = 0` (que já era
o padrão) achando que setavam o raio. A chamada era válida, executava, e
não fazia nada.

### ⚠️ A linha `0x00D4D0BE` não se comporta como o rótulo diz

Medido em 2026-09-18, ao investigar o **M-h** (degradê da faixa).

O wrapper realmente seta a propriedade 38:

```asm
0x00D4D0BE   movs r1, #0x26
             b.w  #0x00D4CAC4
```

Mas ele **passa o argumento como ponteiro direto**, ao contrário do
`BG_COLOR` (`0x00D4D092`), que empacota a cor por valor com `bfi`.

E os **dois únicos chamadores** passam **strings de glifo**, não
descritores de degradê:

```asm
0x00D5262C   ldr r1, = 0x00CDA20C    ; "\xef\x81\x93" + "January"...
0x00D52694   ldr r1, = 0x00CD525B    ; "\xef\x81\x94" + "-%s no page_p->..."
```

`ef 81 93` é UTF-8 de `U+E053`. Na LVGL, `bg_img_src` aceita símbolo
como ponteiro — o comportamento bate com **`BG_IMG_SRC`**, não com
`BG_GRAD`.

**Consequência: este firmware não tem wrapper de degradê.** O M-h
continua sendo rotina nova, como a estimativa original do
`MARTE_ALVO.md` dizia.

> A ironia é que esta tabela existe justamente por causa do erro do
> `RADIUS` — e ela própria tem uma linha que induz ao mesmo tipo de
> engano. A regra abaixo vale, mas com um degrau a mais: **confira o
> comportamento pelos chamadores, não só a propriedade pelo wrapper.**

> **Regra derivada:** a propriedade de um estilo se lê **desta tabela**,
> nunca da documentação da LVGL. E a ferramenta que mexer em estilo deve
> **desmontar o wrapper e conferir a propriedade** antes de gravar —
> `tools/fix_raio_selecao.py` faz isso e recusa se não bater.

### Quem é quadrado e quem é redondo

Há **51** chamadas a `0x00D4D064` no firmware, quase todas `(obj, 0, 0)`:
é o idioma do próprio firmware para deixar um objeto quadrado.

```text
0x00D21716   a faixa superior        -> recebe raio 0
0x00D3A71A   conteiner da lista      -> recebe raio 0
0x00D2F114   conteiner do Extras     -> recebe raio 0
0x00D21764   A LINHA (39 telas)      -> NAO recebia  <- o defeito
```

Por isso a linha herdava o arredondamento do tema. A home não usa
`0x00D21764`, e por isso já era quadrada.

---

# PARTE IV — Os dois caminhos de desenho do firmware de fábrica

> **Procedência.** Esta parte foi extraída em 2026-09-14 de três
> documentos da linha 2.x que foram APAGADOS no mesmo dia, a pedido do
> mantenedor: `PROJETO_SATURNO.md`, `CONVERTER_HOME.md` e
> `PADRONIZAR_HOME.md`.
>
> **O que veio e o que não veio.** Vieram só as MEDIÇÕES sobre o firmware
> ORIGINAL. Ficaram de fora os planos, as receitas e todos os endereços
> da faixa `0x001A5400..0x001A5880` — aquela área era onde os patches da
> 2.x escreviam, e não existe no firmware de fábrica. Se você encontrar
> um endereço `0x1A5xxx` citado como se fosse do firmware, é engano.

## 19. O firmware tem DOIS desenhos para a mesma ideia — CONFIRMADO

Não é uma variação: são duas implementações independentes.

```text
HOME (pagina 1)                 AS 36 TELAS DE LISTA
  rotulos soltos                  framework de widgets
  posicao por coordenada          faixa     = helper 0x00D216F0
  sem conteiner de linha          linha     = helper 0x00D21764
  sem objeto de linha             conteiner = helper 0x00D21690
  cores na mao                    cores pelo tema da LVGL
```

**CONFIRMADO:** `page_home_create` não chama nenhum dos três helpers.

### Por que isso importa

Toda propriedade que um objeto não seta explicitamente é decidida pelo
**tema da LVGL**, que não é nosso. Três defeitos visuais distintos
(raio da seleção, texto cinza nas listas, faixa clara vazia) tiveram
essa mesma causa. Não é descuido repetido: é propriedade da arquitetura.

## 20. O laço da home, decodificado — CONFIRMADO

`0x00D2ECEE` … `0x00D2ED8E`. `r5` é índice em bytes: `adds r5,#4` e
`cmp r5,#0x24` → **9 voltas**.

**São DOIS objetos por item**, irmãos, filhos do contêiner, posicionados
um sobre o outro por coordenada absoluta:

```text
r7 = conteiner            <- criado antes; PAD_ROW e PAD_COLUMN = 0
fp = tabela de coordenadas
sp+0x4C = tabela de ids de texto

laco, r5 = 0 ate 0x24 de 4 em 4        (9 voltas)

    sb = 0xD5D850(r7)                  objeto 1 — o icone/quadro
    flag(sb, 2) ; add_event_cb(sb, ...) ; flag(sb, 0x8000)
    x = ldrsh[fp+r5] ; y = ldrsh[fp+r5+2]
    posiciona(sb, x, y)                COORDENADA ABSOLUTA

    r6 = lv_label_create(r7)           objeto 2 — o rotulo, IRMAO do 1o
    texto = get_string(tabela[r5])
    label_set_text(r6, texto)
    set_style_text_color(r6, cor, 0)
    label_set_long_mode(r6, 0)
    flag(r6, 0x8000)
    posiciona(r6, x, y)                tambem por coordenada

    guarda os dois ponteiros nos arrays
```

Tabelas de coordenadas: `0x00C4867C` e `0x00C486A0`.
Tabela de ids de texto da home: `0x000486C4` (offset de arquivo).

**Consequência medida:** não existe linha para pintar. O que parece
"fundo do item" é o objeto `sb`, pintado por conta própria. Por isso
uma cor de fundo de tela nunca alcança a home, a seleção precisa pintar
o fundo do próprio rótulo, e o espaçamento vem da tabela de
coordenadas, não de `PAD_ROW`.

## 21. O molde certo já existe no firmware — `page_home_menu_event_cb` (0x53)

```text
r6 = 0
laco:
    r4 = CRIA_LINHA(conteiner)                    0x00D21764
    altura = tela/7 ; set_height(r4)              0x00D4A1EA
    border_side(r4, 2)  e, se r6==2, border_side(r4, 3)
    add_event_cb(r4, handler, 0x0D)               0x00D47064
    sl = CRIA_ROTULO(r4)                          0x00D5E2E8   <- icone
         set_style_text_font(sl, 0x00CA671C)      0x00D4D12E
         set_text(sl, ...)                        0x00D5ED94
    sb = CRIA_ROTULO(r4)                          0x00D5E2E8   <- texto
         set_width / set_long_mode(sb, 4)         0x00D4A1BA / 0x00D5EF04
         id = tabela[r6] ; set_text(sb, get_string(id))
    r6 += 1
```

Um laço, uma tabela de ids, três helpers — **o rótulo mora DENTRO da
linha**. É o desenho correto, e está pronto no firmware de fábrica.

### A home, ao lado

```text
chamadas aos helpers .......... NENHUMA
set_style_text_color .......... 7x
setters de padding na mao ..... 6  (0xD4D01C 028 034 040 04C 058)
funcoes de imagem ............. 0xD55FCC 0xD55FF4 0xD56000 0xD5615C
palette_main .................. 2x
```

## 22. ⚠️ O perigo medido: a página 0x53 e a ALOCAÇÃO

A página `0x53` tem **três** itens de fábrica, e o buffer dela é
dimensionado pela contagem:

```text
Esquema confirmado em page_set_menu (10 itens):
  rotulos = N*4      icones = 2*N*4
  botoes 0x00   rotulos 0x18   icones 0x30   malloc 0x4C
```

**Esticar a contagem de itens mexe em alocação e aritmética de
ponteiro. Erro de offset corrompe a heap, e corrupção de heap NÃO
aparece na verificação byte a byte pós-gravação.**

Foi exatamente essa a única modificação da história do projeto que nunca
funcionou no aparelho — o submenu "Extras" não abria, depois de três
tentativas empilhadas.

**⚠️ CORREÇÃO — 2026-09-14, no mesmo dia.** Este parágrafo dizia que
converter a home NÃO cai nessa classe, apoiado em:

```text
page_home_event_cb        NENHUMA chamada de alocacao
page_home_menu_event_cb   NENHUMA chamada de alocacao
```

As duas linhas são verdadeiras, **mas a conclusão estava errada**: quem
aloca é o `page_home_create`, e ele aloca.

```text
00D2EBBC  5420  movs r0, #0x54     <- 84 bytes
00D2EBC0        bl   0xD58188         malloc
00D2EBC6        cbnz r0, ...          confere a falha
00D2EBDA  5422  movs r2, #0x54     <- memset(p, 0, 84)
```

A home guarda **dois** ponteiros por item (`[sl+4]!` e `[sl+0x24]`,
espaçamento `0x24` = 9×4). O molde do Configurar produz **três** — a
linha também é guardada. Adotar o molde exige um terceiro array,
**+0x24 bytes**.

**Conclusão correta:** converter a home **mexe em alocação, sim** — mas
num ponto único, com o tamanho em dois imediatos de 8 bits, e com
checagem de falha já existente. É risco localizado, não difuso.

O quadro completo — a carcaça, o molde do Configurar decodificado e a
ordem de trabalho — está em **`docs/CARCACA_PADRAO.md`**.

## 23. Cor e fonte — pontos medidos no firmware de fábrica

```text
0x00CDF078   tabela de paletas da LVGL, indexada por 16 bits
0x00CA671C   a fonte de ICONES — 44 pontos, em 32 telas
0x00D4CAC4   caminho comum do raio
```

`palette_main(7)` é chamado em três pontos: `0x00D2EB42` e `0x00D2EDB2`
(home) e `0x00DA3520` (a rotina compartilhada das 39 telas).

```text
palette_main(7) = 0xFA05 pre-invertido = RGB565 0x05FA = RGB(0,190,213)
```

Cores neste binário são RGB565 **pré-invertidas** — ver `COLOR_SOURCE.md` §9.

### Os dois getters de cor da tela de abertura

```text
0x00D21384   getter de cor CLARA   <- sobrecarregado: umas telas usam
                                      como TEXTO, outras como FUNDO
0x00D2138A   getter de PRETO
```

Escurecer o getter claro deixaria o texto de Configurar invisível. Foi
por isso que a Core 1.0.1 redirecionou as CHAMADAS (`0x0012285C` e
`0x001228E6`), e não o valor devolvido.

## 24. O que NÃO foi resolvido, e continua em aberto

**A barra no descanso de tela.** Não existe página de descanso de tela —
só `page_scrsaver_time`, que é a configuração. O relógio grande é
desenhado **sem transição de página**, e o chrome só é destruído em
`view_page_create`. Por isso ele sobrevive a uma barra desenhada.

Achar o caminho de desenho do descanso de tela é investigação aberta.

**A camada de mensagem não quebra linha.** `page_info` monta uma
mensagem (descritor em `0x008238F0`, entregue a `0x00D0D818`), e esse
caminho ignora `\n` — ao contrário de um rótulo LVGL comum. Confirmado na
tela. Limite de largura medido: **113 px** por espaço de texto.

---

# PARTE V — Por que páginas de menu novas ficam inacessíveis

> Levantado em 2026-09-15 durante a análise contínua do firmware original.
> O problema relatado pelo mantenedor — *"criou uma nova página de menu,
> os itens aparecem, mas ficam inacessíveis"* — tem uma causa estrutural
> identificável no binário.

## 25. Arquitetura de registro e navegação de páginas — CONFIRMADO

### 25.1 Cada página exporta dois pontos de entrada

Toda tela nomeada segue o padrão:

```text
page_<nome>_create        ; construtor da tela
page_<nome>_scr_process   ; processador de eventos de tela
page_<nome>_event_cb      ; callback de eventos LVGL (quando usado)
```

Exemplo medido para `page_home`:

| Símbolo | String em | Função real em |
|---|---|---|
| `page_home_create` | `0x0D43AC` | `0x00D2EE0C` |
| `page_home_scr_process` | `0x0D43BD` | `0x00D2E951` |
| `page_home_menu_create` | `0x0D442F` | `0x00D2EF5C` |
| `page_home_menu_event_cb` | `0x0D4453` | `0x00D2F540` |

A string e a função não são contíguas. O linker deixa a string no pool de
nomes e a função no texto; o nome serve para depuração e, em alguns casos,
para identificação interna.

### 25.2 O menu `page_home_menu_create` é uma lista de botões LVGL

`page_home_menu_create` (endereço efetivo `0x00D2F794`) aloca uma
estrutura de controle de `0x54` bytes e cria **6 itens de lista** em
laço. Cada iteração:

1. Cria uma linha (`CRIA_LINHA`, `0x00D21764`).
2. Adiciona um event callback (`lv_obj_add_event_cb`, `0x00D47064`).
3. Cria um rótulo para o ícone (fonte de símbolos, `0x00CA671C`).
4. Cria um rótulo para o texto, resolvendo o ID pelo idioma ativo
   (`get_string`, `0x00D2108C`).

O callback registrado é `page_home_menu_event_cb` (`0x00D2F540`).

### 25.3 O callback de evento não abre a página diretamente

Quando um item é clicado (`LV_EVENT_SHORT_CLICKED`, código `0x0A`), o
handler faz:

```text
objeto_clicado = lv_event_get_target()
user_data      = lv_obj_get_user_data(objeto_clicado)

for i = 0 .. 5:
    if tabela_de_botoes[i] == objeto_clicado:
        envia mensagem(7, 4, 4, i)
```

A função de envio (`0x00D23510`) monta uma mensagem de 0x1C bytes na
stack e chama `0x00D234AC` (post para a fila da `MgrTask`).

Campos observados na mensagem:

| Offset | Valor | Significado provável |
|---|---|---|
| `+0x00` | `1` | sinalizador |
| `+0x02` | `7` | tipo / destino da mensagem |
| `+0x04` | `7` | página de origem (`0x53` = Extras/Home menu) |
| `+0x06` | `?` | |
| `+0x08` | `4` | comando |
| `+0x0A` | `4` | sub-comando |
| `+0x0C` | `i` | índice do item selecionado (0..5) |

### 25.4 O despachante central é a `ViewTask` (correção)

> **Correção importante (2026-09-16):** a análise anterior identificou
> erroneamente a `MgrTask` como consumidora das mensagens de navegação.
> O disassembly completo mostra que as mensagens enviadas por
> `0x00D23510` são postadas na fila da **ViewTask** (task id 3), não da
> `MgrTask` (task id 9).
>
> A `MgrTask` (`0x00D3FF8C`) é responsável por eventos de hardware:
> USB/PMU/timers (`0x00D460F4`).
>
> A `ViewTask` (`0x00CF8210`) é a task de UI: recebe mensagens da fila,
> chama `0x00CFE708` para processar a navegação e mantém o estado das
> páginas. Ver `analysis/ui/UI_TASK_ARCHITECTURE.md`.

A função `0x00D23510` monta uma mensagem de 0x1C bytes e chama
`0x00D234AC`, que posta na fila da task id 3 (`ViewTask`).

### 25.5 Por que uma página nova fica inacessível

Criar apenas `page_nova_create` e adicionar um botão que a desenha **não
basta**. Para a nova página ser acessível a partir de um menu, três
condições precisam ser satisfeitas simultaneamente:

1. **A página deve estar registrada no sistema de páginas.**
   O firmware precisa saber que o índice `i` do menu corresponde à
   função `page_nova_create`. Isso é feito por uma tabela indireta
   consultada pela `MgrTask` (não a simples lista de strings de nome).

2. **O event callback do menu deve enviar a mensagem correta.**
   O botão novo precisa ter `user_data` ou posição na tabela de botões
   de forma que, ao ser clicado, o handler chame `msg(7, 4, 4, i)` com
   `i` mapeado para a nova página.

3. **O dispatcher da `MgrTask` deve interpretar o comando.**
   O estado atual e o comando `4/4` precisam cair num ramo que carregue
   a página de destino, não num ramo de erro.

Se qualquer uma dessas três peças falhar, o sintoma é exatamente o
relatado: o item aparece na tela, mas apertar o botão de "entrar" não
faz nada.

### 25.6 Implicação prática para o OpenPod

- **Mudanças visuais simples** (trocar ícones, cores, textos, papel de
  parede) não exigem tocar nesse mecanismo — são os patches de menor
  risco.
- **Adicionar uma página de menu nova** exige modificação em três
  lugares (construtor, registro no dispatcher e handler do menu) e,
  portanto, é **alto risco** para a Fase 1.
- A alternativa mais segura é **reescrever o conteúdo de uma página
  existente** (por exemplo, substituir o conteúdo de uma das 61 páginas
  já registradas) em vez de criar uma página nova.

### 25.7 Classificação

| Afirmação | Classe |
|---|---|
| Cada página tem `create` + `scr_process` + `event_cb` | **CONFIRMADO** |
| `page_home_menu_create` cria 6 itens de lista | **CONFIRMADO** |
| Clique no item envia mensagem `msg(7, 4, 4, i)` | **CONFIRMADO** (disassembly do callback) |
| `MgrTask` consome a fila e despacha por estado | **CONFIRMADO** (mas de USB/PMU, não de UI) |
| `ViewTask` consome mensagens de navegação de UI | **CONFIRMADO** |
| Existe tabela indireta índice → `page_*_create` | **HIPÓTESE** — local exato não determinado |
| Adicionar página nova exige 3 pontos de modificação | **PROVÁVEL** |
