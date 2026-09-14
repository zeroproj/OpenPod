# TEXTOS FIXOS — o que a tabela de idiomas NAO alcanca

Gerado por `tools/textos_fixos.py` sobre `firmware/WORKING/GN438_openpod_v073_carimbado.bin`.

`docs/TEXTOS_SISTEMA.md` cobre os **216 ids x 8 idiomas**. Este
arquivo cobre o resto: o texto que a interface mostra **sem passar**
pela tabela — logo, **nenhuma traducao o alcanca**.

| origem no rotulo | chamadas |
|---|---:|
| tabela de idiomas, **direto** | 35 |
| literal no codigo (**nao traduzivel**) | 126 |
| vindo de registrador | 82 |
| **total** | **243** |

> **Nao leia isto como "so 35 textos sao traduziveis".** O caminho
> principal do texto traduzido nao passa pelo rotulo direto:
> `get_lang_str` tem **163** chamadas, e **63** delas vao para
> `pstr_cmd_view`, que copia o texto para dentro de uma mensagem
> (offset `0x14`) e a envia a view. Boa parte das chamadas "vindo
> de registrador" e justamente isso chegando. A lista de LITERAIS
> abaixo e que e solida — esses nenhuma traducao alcanca.

## Os literais

| texto | endereco | onde aparece | avaliacao |
|---|---|---|---|
| ` ` | `0x04F981` | page_alarm_cycle_event_cb, page_alarm_cycle_label_process, page_alarm_menu_event_cb, page_alarm_menu_scr_process, page_bt_menu_event_cb, page_bt_menu_scr_process, page_date_time_label_process, page_device_info_label_process, page_ebook_bg_btn_process + page_ebook_bg_event_reply   [mesma tela: page_ebook_bg], page_ebook_bg_create, page_ebook_list_event_cb, page_ebook_list_scr_process, page_ebook_mark_label_process, page_ebook_read_anim_process, page_ebook_read_event_cb, page_ebook_set_label_process, page_ebook_time_event_cb, page_fm_preset_event_cb, page_folder_list_btn_process, page_folder_list_create, page_home_menu_event_cb, page_home_menu_label_process, page_lang_option_event_cb, page_lang_option_label_process, page_music_album_event_cb, page_music_album_scr_process, page_music_artist_event_cb, page_music_artist_scr_process, page_music_eq_event_cb, page_music_loop_event_cb, page_music_loop_label_process, page_music_mark_label_process, page_music_menu_label_process, page_music_play_create, page_music_set_event_cb, page_music_song_btn_process, page_music_song_create, page_pass_menu_label_process, page_pict_list_event_cb, page_pict_list_scr_process, page_record_menu_event_cb, page_record_time_create, page_record_work_event_cb, page_set_date_event_cb, page_set_idleshut_label_process, page_set_keylight_event_cb, page_set_keylight_label_process, page_set_lang_event_cb, page_set_lang_label_process, page_set_menu_event_cb, page_set_menu_label_process, page_set_speaker_event_cb, page_set_speaker_label_process, page_set_timershut_label_process, page_storage_info_label_process, page_video_list_event_cb, page_video_list_scr_process, view_option_callback | — |
| ` Time's up!` | `0x0D33FF` | page_alarm_play_create | **INGLES visivel** — mensagem do despertador |
| `--` | `0x0D401E` | page_fm_play_create | marcador de vazio |
| `00:00:21` | `0x0D4968` | page_music_play_create | espaco reservado de tempo decorrido |
| `00:03:25` | `0x0D4971` | page_music_play_create | espaco reservado de tempo restante |
| `1/253` | `0x0D4962` | page_music_play_create | **espaco reservado do contador** da tela Tocando Agora |
| `14:00` | `0x05D61C` | volume_bar_key_event_cb | espaco reservado de hora |
| `:` | `0x048A57` | page_screen_clock_create | separador |
| `MHZ` | `0x0D401A` | page_fm_play_create | unidade; aceitavel sem traduzir |
| `OK` | `0x0D340B` | page_alarm_play_create | **INGLES visivel** — botao do despertador |
| `OpenPod` | `0x1A3038` | view_option_callback | nosso — carimbo da area livre |
| `no` | `0x057FFA` | view_power_off_mbox_create, volume_bar_key_event_cb | **INGLES visivel** — dialogo de desligar |
| `yes` | `0x05D6CA` | view_power_off_mbox_create, volume_bar_key_event_cb | **INGLES visivel** — dialogo de desligar |

## Conclusao

**Nao, a tabela de idiomas nao cobre tudo.** Ha texto em ingles
fixo no binario que aparece na tela em qualquer idioma:
`Time's up!`, `OK`, `yes`, `no`.

Traduzir isso **nao** e editar a tabela: exige gravar a string nova
na area livre e repor o ponteiro, um a um — o mesmo metodo do
`patch_menu_text.py`.

Os ponteiros de FONTE que passam pelo filtro de string estao
excluidos desta lista: `0x0A671C`, `0x0AA8A8`, `0x0AF5EC`, `0x0B0D3C`, `0x0DED88`, `0xCACFE4`, `0xCC19B8`, `0xCC2064`.
