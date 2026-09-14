# SIMBOLOS — a tabela de nomes recuperada do firmware

Gerado por `tools/mapa_simbolos.py` a partir de `firmware/ORIGINAL/GN438_original.bin`.

O firmware YP3 registra os proprios nomes de funcao para depuracao.
Esta tabela liga NOME -> ENDERECO achando as cargas de literal que
apontam para essas strings e atribuindo-as a funcao que as contem.

**Confianca:** `ALTA` = a funcao cita um unico nome E aparece na
tabela de paginas (`0x00D23B38`), que e fonte independente. `MEDIA` =
cita um unico nome. `BAIXA` = cita varios (pode estar logando nomes
alheios) — e **pista, nao fato**.

| # | valor |
|---|---|
| strings de nome | 475 |
| nomes distintos citados | 461 |
| **funcoes identificadas** | **412** |
| confianca ALTA | 12 |
| confianca MEDIA | 392 |
| confianca BAIXA | 8 |

## Paginas (confianca ALTA — validadas pela tabela de despacho)

| pagina | endereco | simbolo |
|---|---|---|
| 0x01 | `0x12EBB8` | — |
| 0x02 | `0x13178C` | — |
| 0x03 | `0x132EB4` | `page_music_song_create` |
| 0x04 | `0x131E7C` | `page_music_play_create` |
| 0x05 | `0x13275C` | — |
| 0x06 | `0x12FE50` | — |
| 0x07 | `0x12F794` | — |
| 0x08 | `0x13348C` | `page_music_speed_create` |
| 0x09 | `0x130A38` | — |
| 0x0A | `0x131124` | — |
| 0x0B | `0x130434` | — |
| 0x0C | `0x12AB48` | — |
| 0x0D | `0x12B8BC` | — |
| 0x0E | `0x12BED4` | `page_ebook_set_scr_process` |
| 0x0F | `0x12C3FC` | — |
| 0x10 | `0x12A128` | `page_ebook_bg_create` |
| 0x11 | `0x12A64C` | `page_ebook_input_create` |
| 0x12 | `0x12B1B4` | — |
| 0x13 | `0x13D5A4` | — |
| 0x14 | `0x13DB1C` | — |
| 0x15 | `0x133AF4` | — |
| 0x16 | `0x13404C` | — |
| 0x17 | `0x1352E8` | `page_record_time_create` |
| 0x18 | `0x13458C` | — |
| 0x19 | `0x135978` | — |
| 0x1A | `0x12CD04` | `page_fm_play_create` |
| 0x1B | `0x12D930` | — |
| 0x1C | `0x12C910` | — |
| 0x1D | `0x12D280` | — |
| 0x1E | `0x12724C` | — |
| 0x1F | `0x127B78` | — |
| 0x20 | `0x126BCC` | — |
| 0x21 | `0x1277C8` | `page_alarm_play_create` |
| 0x22 | `0x12E05C` | `page_folder_list_create` |
| 0x23 | `0x1286E0` | — |
| 0x28 | `0x13A638` | — |
| 0x29 | `0x139FB8` | — |
| 0x2A | `0x13634C` | — |
| 0x2B | `0x1388E4` | — |
| 0x2C | `0x13BE70` | — |
| 0x2D | `0x138298` | — |
| 0x2E | `0x13AD18` | `page_set_offscr_create` |
| 0x2F | `0x13B330` | `page_set_offscr_time_create` |
| 0x30 | `0x138F00` | — |
| 0x31 | `0x13951C` | — |
| 0x33 | `0x136838` | — |
| 0x37 | `0x129934` | — |
| 0x38 | `0x129C6C` | — |
| 0x3C | `0x136C38` | — |
| 0x44 | `0x137CEC` | — |
| 0x4B | `0x139A44` | — |
| 0x4C | `0x13B868` | — |
| 0x4D | `0x13C48C` | — |
| 0x4E | `0x13D040` | — |
| 0x4F | `0x1371B8` | — |
| 0x50 | `0x13773C` | — |
| 0x51 | `0x12E6B4` | — |
| 0x52 | `0x13CAA8` | — |
| 0x53 | `0x12F0A0` | — |

## Todos os simbolos, por endereco

| endereco | confianca | simbolo |
|---|---|---|
| `0x0F812C` | MEDIA | `ebook_auto_play` |
| `0x0F8210` | MEDIA | `watch_view_task` |
| `0x0F98B0` | MEDIA | `usbd_cb` |
| `0x0FC250` | MEDIA | `bt_delay_` |
| `0x0FC4D4` | MEDIA | `keyManager_send_alarm_msg_to_presenter` |
| `0x0FC5F8` | MEDIA | `do_poweroff_mode` |
| `0x0FC6A0` | MEDIA | `set_backlight_auto` |
| `0x0FC7A8` | MEDIA | `ebook_auto_play` |
| `0x0FCAA8` | MEDIA | `watch_key_back_light_off_process` |
| `0x0FE54C` | BAIXA | `get_all_app_status | sleep_stimer` |
| `0x0FEA50` | MEDIA | `pstr_alarm_open` |
| `0x0FEC32` | MEDIA | `pstr_record_stop_timer` |
| `0x0FEFC4` | MEDIA | `pstr_audio_get_path` |
| `0x0FF424` | MEDIA | `pstr_audio_start_record` |
| `0x0FF6E0` | MEDIA | `pstr_audio_music_info_save` |
| `0x0FF9F0` | MEDIA | `pstr_record_timing_set` |
| `0x0FFAA4` | MEDIA | `pstr_bt_para_init` |
| `0x0FFF2C` | MEDIA | `dshow_send_oper_msg_to_view` |
| `0x1000E0` | MEDIA | `pstr_ebook_set_cur_ebook_and_open` |
| `0x100224` | MEDIA | `ebook_auto_play` |
| `0x1003AC` | MEDIA | `pstr_ebook_nv_read` |
| `0x100430` | MEDIA | `pstr_ebook_para_init` |
| `0x100480` | MEDIA | `pstr_fm_preset_init` |
| `0x1009BC` | MEDIA | `pstr_db_enter_dir_cb` |
| `0x100C74` | MEDIA | `pstr_db_folder_delete_cb` |
| `0x100DA0` | MEDIA | `page1_record_build_cb` |
| `0x100E28` | MEDIA | `page1_music_build_cb` |
| `0x100EE0` | MEDIA | `page1_ebook_build_cb` |
| `0x100F3C` | MEDIA | `page1_img_process` |
| `0x10148C` | MEDIA | `page10_media_cb` |
| `0x101728` | MEDIA | `page10_mbox_process + page10_scr_process` |
| `0x1018C0` | MEDIA | `page11_scr_process + pstr_page11_process` |
| `0x101B6C` | MEDIA | `page12_cont_process + page12_index_process` |
| `0x101F10` | MEDIA | `page13_label_process + page13_scr_process  [tambem cita: ebook_auto_play]` |
| `0x1020C4` | MEDIA | `page14_scr_process + pstr_page14_process  [tambem cita: ebook_auto_play]` |
| `0x102280` | MEDIA | `page15_btn_process` |
| `0x1023B8` | MEDIA | `page16_scr_process + pstr_page16_process` |
| `0x1024E4` | MEDIA | `page17_btnm_process` |
| `0x1028B4` | MEDIA | `page18_mbox_process + page18_scr_process` |
| `0x102B88` | MEDIA | `page19_cont_process + page19_index_process + pstr_page19_process` |
| `0x102F74` | MEDIA | `page2_media_msg_analysis` |
| `0x102FCC` | MEDIA | `page2_mbox_process + page2_scr_process` |
| `0x1033BC` | MEDIA | `video_quit_stimer` |
| `0x103404` | MEDIA | `pstr_page20_deinit` |
| `0x103440` | MEDIA | `pstr_page20_show_video` |
| `0x1034F0` | MEDIA | `page20_video_process` |
| `0x103930` | MEDIA | `page21_cont_process + page21_index_process + pstr_page21_process` |
| `0x103B5C` | MEDIA | `pstr_page22_show_pict` |
| `0x103BC0` | MEDIA | `page22_scr_process` |
| `0x103E00` | MEDIA | `page23_scr_process + pstr_page23_process` |
| `0x1040B4` | MEDIA | `page24_record_build_cb` |
| `0x104110` | MEDIA | `page24_btn_process` |
| `0x104384` | MEDIA | `psrt_page25_get_record_filename` |
| `0x104478` | MEDIA | `pstr_record_stop_timer` |
| `0x104660` | MEDIA | `page25_set_view_name` |
| `0x1047FC` | MEDIA | `page25_btn_process + page25_mbox_process + pstr_page25_process` |
| `0x1049D0` | MEDIA | `pstr_record_stop_timer` |
| `0x104A38` | MEDIA | `pstr_record_stop_timer` |
| `0x105194` | MEDIA | `pstr_page26_deinit` |
| `0x1051DC` | MEDIA | `page26_btnm_process` |
| `0x105588` | MEDIA | `page27_mbox_process + page27_scr_process` |
| `0x105774` | MEDIA | `page28_scr_process + pstr_page28_process` |
| `0x105A24` | MEDIA | `page29_btn_process + pstr_page29_process` |
| `0x105C30` | MEDIA | `wave_scan` |
| `0x105D90` | MEDIA | `page3_btn_process + page3_scr_process + pstr_page3_process` |
| `0x105FAC` | MEDIA | `wave_scan` |
| `0x10623C` | MEDIA | `page30_scr_process + pstr_page30_process` |
| `0x10640C` | MEDIA | `page31_btn_process` |
| `0x10658C` | MEDIA | `page32_scr_process + pstr_page32_process` |
| `0x106710` | MEDIA | `page33_btn_process` |
| `0x106A14` | MEDIA | `page34_btn_process` |
| `0x106CBC` | MEDIA | `page34_cont_process + page34_scr_process + pstr_page34_process` |
| `0x107150` | MEDIA | `btplay_stop` |
| `0x1071E0` | MEDIA | `pstr_bt_enter_call_come` |
| `0x1072F4` | MEDIA | `page35_show_bt_option` |
| `0x1079A0` | MEDIA | `page35_scr_process` |
| `0x107AEC` | MEDIA | `page35_search_list_process` |
| `0x107C14` | MEDIA | `page35_mbox_process` |
| `0x107D3C` | BAIXA | `btplay_stop | pstr_bt_analysis` |
| `0x1088B4` | MEDIA | `page4_media_cb` |
| `0x108A90` | MEDIA | `page4_btnm_process + page4_scr_process` |
| `0x109050` | MEDIA | `page40_build_cb` |
| `0x109150` | MEDIA | `page40_btn_process + pstr_page40_process` |
| `0x10938C` | MEDIA | `page41_btn_process` |
| `0x1094A2` | MEDIA | `page42_scr_process + pstr_page42_process` |
| `0x1096F4` | MEDIA | `page43_scr_process + pstr_page43_process` |
| `0x1098D0` | MEDIA | `page44_scr_process + pstr_page44_process` |
| `0x109A18` | MEDIA | `page45_btn_process` |
| `0x109BEC` | MEDIA | `page46_scr_process + pstr_page46_process` |
| `0x109D50` | MEDIA | `page47_btn_process` |
| `0x109ED8` | MEDIA | `page48_scr_process + pstr_page48_process` |
| `0x109FFC` | MEDIA | `page49_btn_process` |
| `0x10A25C` | MEDIA | `page5_mbox_process + page5_scr_process` |
| `0x10A5A0` | MEDIA | `page51_scr_process + pstr_page51_process` |
| `0x10A6E0` | MEDIA | `page55_scr_process + pstr_page55_process` |
| `0x10A99C` | MEDIA | `page56_scr_process + pstr_page56_process` |
| `0x10AD98` | MEDIA | `page6_btn_process + page6_scr_process + pstr_page6_process` |
| `0x10AF98` | MEDIA | `page60_scr_process + pstr_page60_process` |
| `0x10B0AC` | MEDIA | `page68_btn_process` |
| `0x10B1F8` | MEDIA | `page69_btn_process` |
| `0x10B4D8` | MEDIA | `page7_btn_process + page7_scr_process + pstr_page7_process` |
| `0x10B840` | MEDIA | `page70_media_msg_analysis` |
| `0x10B904` | MEDIA | `page70_btn_process` |
| `0x10BA90` | MEDIA | `page76_scr_process + pstr_page76_process` |
| `0x10BBA4` | MEDIA | `page77_btn_process` |
| `0x10BCF4` | MEDIA | `page78_scr_process + pstr_page78_process` |
| `0x10BEC8` | MEDIA | `page79_scr_process + pstr_page79_process` |
| `0x10C03C` | MEDIA | `page8_scr_process + pstr_page8_process` |
| `0x10C268` | MEDIA | `page80_scr_process + pstr_page80_process` |
| `0x10C498` | MEDIA | `page81_btn_process` |
| `0x10C5DC` | MEDIA | `page82_build_cb` |
| `0x10C610` | MEDIA | `page82_record_build_cb` |
| `0x10C650` | MEDIA | `page82_ebook_build_cb` |
| `0x10C764` | MEDIA | `page82_scr_process` |
| `0x10CA94` | MEDIA | `page83_scr_process + pstr_page83_process` |
| `0x10CC0C` | MEDIA | `page84_scr_process + pstr_page84_process` |
| `0x10CDB0` | MEDIA | `page9_btn_process` |
| `0x10CFA4` | MEDIA | `pstr_pass_nv_save` |
| `0x10D0B8` | MEDIA | `pstr_pict_image_prev` |
| `0x10D2D8` | MEDIA | `pstr_video_image_prev` |
| `0x10D4B0` | MEDIA | `pstr_db_build_cb` |
| `0x10D6F4` | MEDIA | `pstr_stimer` |
| `0x10D770` | MEDIA | `pstr_select_usb_mode` |
| `0x10D7E4` | MEDIA | `pstr_poweroff_mbox_process` |
| `0x10D834` | MEDIA | `poweroff_mbox` |
| `0x10D924` | MEDIA | `pstr_cmd_view` |
| `0x10E39C` | MEDIA | `pstr_del_tip` |
| `0x10E530` | MEDIA | `pstr_show_usb_option` |
| `0x10E608` | MEDIA | `screen_clock_stimer` |
| `0x10ED0C` | BAIXA | `ebook_auto_play | pstr_delete_lightoff_page | pstr_usb_start_event_analysis | watch_presenter_entry` |
| `0x12108C` | MEDIA | `get_lang_str` |
| `0x1214E8` | MEDIA | `volume_bar_key_event_cb` |
| `0x121BF4` | MEDIA | `view_power_off_mbox_create` |
| `0x1221AC` | MEDIA | `view_option_callback` |
| `0x12311A` | MEDIA | `page_top_layer_event_reply` |
| `0x12361C` | MEDIA | `view_set_icon_bat` |
| `0x1239A0` | MEDIA | `view_clean_all_objs` |
| `0x123E50` | MEDIA | `view_page_msg_analysis` |
| `0x1242B4` | MEDIA | `watch_view_rec_analysis` |
| `0x124398` | MEDIA | `watch_view_init` |
| `0x126A34` | MEDIA | `page_alarm_cycle_event_cb` |
| `0x126E18` | MEDIA | `page_alarm_cycle_scr_process` |
| `0x126E78` | MEDIA | `page_alarm_cycle_label_process` |
| `0x127020` | MEDIA | `page_alarm_menu_event_cb` |
| `0x1274C4` | MEDIA | `page_alarm_menu_scr_process` |
| `0x127620` | MEDIA | `page_alarm_menu_label_process` |
| `0x12767C` | MEDIA | `page_alarm_menu_event_reply` |
| `0x1277C8` | ALTA | `page_alarm_play_create` |
| `0x127922` | MEDIA | `page_alarm_play_event_reply` |
| `0x1279B2` | MEDIA | `page_alarm_time_event_cb` |
| `0x127DEC` | MEDIA | `page_alarm_time_scr_process` |
| `0x127E70` | MEDIA | `page_alarm_time_label_process` |
| `0x127FDC` | MEDIA | `page_bt_menu_event_cb` |
| `0x128594` | MEDIA | `page_bt_menu_option_event_cb` |
| `0x128C34` | MEDIA | `page_bt_menu_scr_process` |
| `0x129164` | MEDIA | `page_bt_menu_label_process` |
| `0x1293F0` | MEDIA | `page_bt_menu_search_list_process` |
| `0x129674` | MEDIA | `page_bt_menu_mbox_process` |
| `0x1297CC` | MEDIA | `page_dict_input_event_cb` |
| `0x129A8C` | MEDIA | `page_dict_input_btnm_process` |
| `0x129ADC` | MEDIA | `page_dict_input_event_reply` |
| `0x129B68` | MEDIA | `page_dict_play_event_cb` |
| `0x129E70` | MEDIA | `page_dict_play_label_process` |
| `0x129EFC` | MEDIA | `page_dict_play_event_reply` |
| `0x12A128` | ALTA | `page_ebook_bg_create` |
| `0x12A380` | MEDIA | `page_ebook_bg_btn_process + page_ebook_bg_event_reply   [mesma tela: page_ebook_bg]` |
| `0x12A64C` | ALTA | `page_ebook_input_create` |
| `0x12A838` | MEDIA | `page_ebook_input_btnm_process` |
| `0x12A8F0` | MEDIA | `page_ebook_list_event_cb` |
| `0x12AD18` | MEDIA | `page_ebook_list_scr_process` |
| `0x12AEA0` | MEDIA | `page_ebook_list_label_process` |
| `0x12AF70` | MEDIA | `page_ebook_mark_event_cb` |
| `0x12B3E8` | MEDIA | `page_ebook_mark_scr_process` |
| `0x12B430` | MEDIA | `page_ebook_mark_label_process` |
| `0x12B548` | MEDIA | `page_ebook_mark_event_reply` |
| `0x12B650` | MEDIA | `page_ebook_read_event_cb` |
| `0x12BA0C` | MEDIA | `page_ebook_read_scr_process` |
| `0x12BA54` | MEDIA | `page_ebook_read_anim_process` |
| `0x12BD2C` | MEDIA | `page_ebook_set_event_cb` |
| `0x12BED4` | ALTA | `page_ebook_set_scr_process` |
| `0x12C120` | MEDIA | `page_ebook_set_label_process` |
| `0x12C2C8` | MEDIA | `page_ebook_time_event_cb` |
| `0x12C5F4` | MEDIA | `page_ebook_time_scr_process` |
| `0x12C664` | MEDIA | `page_ebook_time_label_process` |
| `0x12C7AC` | MEDIA | `page_fm_band_event_cb` |
| `0x12CAE0` | MEDIA | `page_fm_band_scr_process` |
| `0x12CB18` | MEDIA | `page_fm_band_event_reply` |
| `0x12CD04` | ALTA | `page_fm_play_create` |
| `0x12CF80` | MEDIA | `page_fm_play_label_process` |
| `0x12D04C` | MEDIA | `page_fm_preset_event_cb` |
| `0x12D474` | MEDIA | `page_fm_preset_scr_process` |
| `0x12D61C` | MEDIA | `page_fm_preset_mbox_process` |
| `0x12D70C` | MEDIA | `page_fm_set_event_cb` |
| `0x12DAD4` | MEDIA | `page_fm_set_scr_process` |
| `0x12DB6C` | MEDIA | `page_fm_set_mbox_process` |
| `0x12DC8C` | MEDIA | `folder_list_set_icon` |
| `0x12E05C` | ALTA | `page_folder_list_create` |
| `0x12E288` | MEDIA | `page_folder_list_btn_process` |
| `0x12E438` | MEDIA | `page_folder_list_mbox_process` |
| `0x12E55C` | MEDIA | `page_expand_home_event_cb` |
| `0x12E804` | MEDIA | `page_expand_home_scr_process` |
| `0x12E872` | MEDIA | `page_expand_home_label_process` |
| `0x12E950` | MEDIA | `page_home_event_cb` |
| `0x12EE0C` | MEDIA | `page_home_scr_process` |
| `0x12EE72` | MEDIA | `page_home_label_process` |
| `0x12EF60` | MEDIA | `page_home_menu_event_cb` |
| `0x12F340` | MEDIA | `page_home_menu_scr_process` |
| `0x12F3A0` | MEDIA | `page_home_menu_label_process` |
| `0x12F540` | MEDIA | `page_music_album_event_cb` |
| `0x12F984` | MEDIA | `page_music_album_scr_process` |
| `0x12FB08` | MEDIA | `page_music_album_label_process` |
| `0x12FBFC` | MEDIA | `page_music_artist_event_cb` |
| `0x130040` | MEDIA | `page_music_artist_scr_process` |
| `0x1301C4` | MEDIA | `page_music_artist_label_process` |
| `0x130288` | MEDIA | `page_music_eq_event_cb` |
| `0x130710` | MEDIA | `page_music_eq_scr_process` |
| `0x130748` | MEDIA | `page_music_eq_label_process` |
| `0x13088C` | MEDIA | `page_music_loop_event_cb` |
| `0x130CBC` | MEDIA | `page_music_loop_scr_process` |
| `0x130CF4` | MEDIA | `page_music_loop_label_process` |
| `0x130E84` | MEDIA | `page_music_mark_event_cb` |
| `0x1312F0` | MEDIA | `page_music_mark_scr_process` |
| `0x131328` | MEDIA | `page_music_mark_label_process` |
| `0x131438` | MEDIA | `page_music_mark_event_reply` |
| `0x13152C` | MEDIA | `page_music_menu_event_cb` |
| `0x1319F8` | MEDIA | `page_music_menu_scr_process` |
| `0x131A4C` | MEDIA | `page_music_menu_label_process` |
| `0x131B64` | MEDIA | `page_music_menu_event_reply` |
| `0x131E7C` | ALTA | `page_music_play_create` |
| `0x13220C` | MEDIA | `page_music_play_label_process` |
| `0x132558` | MEDIA | `page_music_set_event_cb` |
| `0x132998` | MEDIA | `page_music_set_scr_process` |
| `0x1329EC` | MEDIA | `page_music_set_label_process` |
| `0x132AF4` | MEDIA | `page_music_set_event_reply` |
| `0x132EB4` | ALTA | `page_music_song_create` |
| `0x1330C4` | MEDIA | `page_music_song_btn_process` |
| `0x1331F8` | MEDIA | `page_music_song_event_reply` |
| `0x13348C` | ALTA | `page_music_speed_create` |
| `0x1336B4` | MEDIA | `page_music_speed_btn_process` |
| `0x133784` | MEDIA | `page_music_speed_event_reply` |
| `0x13388C` | MEDIA | `page_pict_list_event_cb` |
| `0x133CB0` | MEDIA | `page_pict_list_scr_process` |
| `0x133E38` | MEDIA | `page_pict_list_label_process` |
| `0x133EFC` | MEDIA | `page_pict_play_event_cb` |
| `0x1340BC` | MEDIA | `page_pict_play_scr_process` |
| `0x13415C` | MEDIA | `page_call_come_btn_process + page_call_come_event_reply   [mesma tela: page_call_come]` |
| `0x13422C` | MEDIA | `page_call_on_btn_process` |
| `0x1342C8` | MEDIA | `page_call_on_event_reply` |
| `0x1343AC` | MEDIA | `page_record_menu_event_cb` |
| `0x134880` | MEDIA | `page_record_menu_scr_process` |
| `0x1348E6` | MEDIA | `page_record_menu_label_process` |
| `0x134DCC` | MEDIA | `page_record_time_event_cb` |
| `0x1352E8` | ALTA | `page_record_time_create` |
| `0x135662` | MEDIA | `page_record_time_btn_process` |
| `0x13580C` | MEDIA | `page_record_work_event_cb` |
| `0x135B78` | MEDIA | `page_record_work_scr_process` |
| `0x135BCC` | MEDIA | `page_record_work_label_process` |
| `0x135C90` | MEDIA | `page_record_work_event_reply` |
| `0x135E5C` | MEDIA | `page_screen_clock_event_cb` |
| `0x135F6C` | MEDIA | `page_screen_clock_create` |
| `0x1361A0` | MEDIA | `page_date_time_event_cb` |
| `0x1364D8` | MEDIA | `page_date_time_scr_process` |
| `0x136516` | MEDIA | `page_date_time_label_process` |
| `0x136678` | MEDIA | `page_device_info_event_cb` |
| `0x136978` | MEDIA | `page_device_info_scr_process` |
| `0x1369B6` | MEDIA | `page_device_info_label_process` |
| `0x136AF4` | MEDIA | `page_lang_option_event_cb` |
| `0x136E68` | MEDIA | `page_lang_option_scr_process` |
| `0x136EA0` | MEDIA | `page_lang_option_label_process` |
| `0x137022` | MEDIA | `page_pass_input_event_cb` |
| `0x137428` | MEDIA | `page_pass_input_scr_process` |
| `0x1374C8` | MEDIA | `page_pass_input_lable_process` |
| `0x1375A4` | MEDIA | `page_pass_menu_event_cb` |
| `0x137930` | MEDIA | `page_pass_menu_scr_process` |
| `0x137984` | MEDIA | `page_pass_menu_label_process` |
| `0x137B18` | MEDIA | `page_scrsaver_time_event_cb` |
| `0x137ECC` | MEDIA | `page_scrsaver_time_scr_process` |
| `0x137F6E` | MEDIA | `page_scrsaver_time_lable_process` |
| `0x1380C4` | MEDIA | `page_set_bright_event_cb` |
| `0x138474` | MEDIA | `page_set_bright_scr_process` |
| `0x138516` | MEDIA | `page_set_bright_lable_process` |
| `0x138676` | MEDIA | `page_set_date_event_cb` |
| `0x138B80` | MEDIA | `page_set_date_scr_process` |
| `0x138C04` | MEDIA | `page_set_date_label_process` |
| `0x138D60` | MEDIA | `page_set_idleshut_event_cb` |
| `0x139154` | MEDIA | `page_set_idleshut_scr_process` |
| `0x1391A8` | MEDIA | `page_set_idleshut_label_process` |
| `0x139348` | MEDIA | `page_set_idleshut_time_event_cb` |
| `0x1396FC` | MEDIA | `page_set_idleshut_time_scr_process` |
| `0x13979E` | MEDIA | `page_set_idleshut_time_lable_process` |
| `0x1398F4` | MEDIA | `page_set_keylight_event_cb` |
| `0x139CA4` | MEDIA | `page_set_keylight_scr_process` |
| `0x139CDC` | MEDIA | `page_set_keylight_label_process` |
| `0x139E5C` | MEDIA | `page_set_lang_event_cb` |
| `0x13A270` | MEDIA | `page_set_lang_scr_process` |
| `0x13A2A8` | MEDIA | `page_set_lang_label_process` |
| `0x13A428` | MEDIA | `page_set_menu_event_cb` |
| `0x13A8CC` | MEDIA | `page_set_menu_scr_process` |
| `0x13A92C` | MEDIA | `page_set_menu_label_process` |
| `0x13AA5C` | MEDIA | `page_set_menu_event_reply` |
| `0x13AD18` | ALTA | `page_set_offscr_create` |
| `0x13AFE0` | MEDIA | `page_set_offscr_btn_process + page_set_offscr_event_reply   [mesma tela: page_set_offscr]` |
| `0x13B330` | ALTA | `page_set_offscr_time_create` |
| `0x13B560` | MEDIA | `page_set_offscr_time_btn_process` |
| `0x13B630` | MEDIA | `page_set_offscr_time_event_reply` |
| `0x13B708` | MEDIA | `page_set_speaker_event_cb` |
| `0x13BAD8` | MEDIA | `page_set_speaker_scr_process` |
| `0x13BB10` | MEDIA | `page_set_speaker_label_process` |
| `0x13BC9A` | MEDIA | `page_set_time_event_cb` |
| `0x13C108` | MEDIA | `page_set_time_scr_process` |
| `0x13C18C` | MEDIA | `page_set_time_label_process` |
| `0x13C2EC` | MEDIA | `page_set_timershut_event_cb` |
| `0x13C6E0` | MEDIA | `page_set_timershut_scr_process` |
| `0x13C734` | MEDIA | `page_set_timershut_label_process` |
| `0x13C8D4` | MEDIA | `page_set_timershut_time_event_cb` |
| `0x13CC88` | MEDIA | `page_set_timershut_time_scr_process` |
| `0x13CD2A` | MEDIA | `page_set_timershut_time_lable_process` |
| `0x13CE80` | MEDIA | `page_storage_info_event_cb` |
| `0x13D198` | MEDIA | `page_storage_info_scr_process` |
| `0x13D1D6` | MEDIA | `page_storage_info_label_process` |
| `0x13D33C` | MEDIA | `page_video_list_event_cb` |
| `0x13D770` | MEDIA | `page_video_list_scr_process` |
| `0x13D8FC` | MEDIA | `page_video_list_label_process` |
| `0x13D9C0` | MEDIA | `page_video_play_event_cb` |
| `0x13DB90` | MEDIA | `page_video_play_scr_process` |
| `0x13E408` | MEDIA | `sync_rtc` |
| `0x13E534` | MEDIA | `clock_init` |
| `0x13E834` | MEDIA | `app_unregister_alarm0` |
| `0x13E92C` | MEDIA | `app_unregister_alarm1` |
| `0x13ED94` | MEDIA | `database_add_event_cb` |
| `0x140170` | MEDIA | `master_cpu_recv_task` |
| `0x140238` | MEDIA | `Master_CPU_Recv_Task` |
| `0x144EBC` | BAIXA | `authorization_code | bt_info | bt_name | restore_factory | scr_clock | usb_status` |
| `0x145064` | BAIXA | `authorization_code | bt_info | bt_name | freq_drift | restore_factory | scr_clock | usb_status` |
| `0x1452C6` | BAIXA | `authorization_code | bt_info | bt_name | freq_drift | restore_factory | scr_clock | usb_status` |
| `0x1453B8` | BAIXA | `authorization_code | bt_info | bt_name | restore_factory | scr_clock | usb_status` |
| `0x145C54` | MEDIA | `watch_sdcard_init` |
| `0x146A24` | MEDIA | `watch_monitor_register` |
| `0x146E24` | MEDIA | `lv_disp_get_scr_act` |
| `0x146E8C` | MEDIA | `lv_disp_get_layer_top` |
| `0x147064` | MEDIA | `lv_obj_add_event_cb` |
| `0x147174` | MEDIA | `lv_obj_remove_all_event_cb` |
| `0x14723C` | MEDIA | `lv_event_set_ext_draw_size` |
| `0x1473A8` | MEDIA | `lv_group_create` |
| `0x147D74` | MEDIA | `indev_pointer_proc` |
| `0x1498F0` | MEDIA | `lv_obj_allocate_spec_attr` |
| `0x14998E` | MEDIA | `lv_obj_class_create_obj` |
| `0x14A32C` | MEDIA | `lv_layout_register` |
| `0x14CAC4` | MEDIA | `get_local_style` |
| `0x14D19A` | MEDIA | `lv_obj_get_disp` |
| `0x14D350` | MEDIA | `lv_obj_del` |
| `0x14D854` | MEDIA | `lv_img_draw_core` |
| `0x1502FC` | MEDIA | `lv_img_decoder_built_in_info` |
| `0x1503E0` | MEDIA | `lv_img_decoder_built_in_read_line` |
| `0x150A14` | MEDIA | `lv_img_decoder_open` |
| `0x150CBC` | MEDIA | `find_track_end` |
| `0x152AEC` | MEDIA | `lv_chart_get_point_pos_by_id` |
| `0x156954` | MEDIA | `lv_indev_drv_register` |
| `0x156D18` | MEDIA | `lv_anim_start` |
| `0x157B4A` | MEDIA | `lv_palette_main` |
| `0x157BEA` | MEDIA | `lv_palette_darken` |
| `0x157CFC` | MEDIA | `lv_fs_open` |
| `0x158200` | MEDIA | `lv_mem_realloc` |
| `0x158358` | MEDIA | `lv_mem_buf_release` |
| `0x158ACA` | MEDIA | `lv_style_reset` |
| `0x158D3E` | MEDIA | `lv_style_set_prop` |
| `0x1590B4` | MEDIA | `lv_timer_handler` |
| `0x1592CA` | MEDIA | `block_next` |
| `0x1593D2` | MEDIA | `block_absorb` |
| `0x159514` | MEDIA | `insert_free_block` |
| `0x1595D8` | MEDIA | `block_merge_next` |
| `0x159658` | MEDIA | `search_suitable_block` |
| `0x159744` | MEDIA | `block_prepare_used` |
| `0x159824` | MEDIA | `lv_tlsf_add_pool` |
| `0x159954` | MEDIA | `lv_tlsf_free` |
| `0x159A24` | MEDIA | `block_trim_used` |
| `0x15A1A0` | MEDIA | `lv_txt_get_size` |
| `0x15BE94` | MEDIA | `allocate_btn_areas_and_controls` |
| `0x15CDA8` | MEDIA | `lv_dropdown_set_options` |
| `0x15CF48` | MEDIA | `lv_dropdown_get_selected_str` |
| `0x15DA20` | MEDIA | `draw_img` |
| `0x15E580` | MEDIA | `lv_label_get_letter_on` |
| `0x15E858` | MEDIA | `lv_label_set_dot_tmp` |
| `0x15EE56` | MEDIA | `lv_label_set_text_fmt` |
| `0x15F2BC` | MEDIA | `lv_label_is_char_under_pos` |
| `0x15FB20` | MEDIA | `lv_roller_set_options` |
| `0x161C08` | MEDIA | `lv_textarea_add_char` |
| `0x161D70` | MEDIA | `lv_textarea_del_char` |
| `0x1624DC` | MEDIA | `lv_imgshow_init` |
| `0x164DB4` | MEDIA | `driver_usbd_sd_params_init` |
| `0x1650A8` | MEDIA | `usbd_mw_pc_arrival_detect_init` |
| `0x165100` | MEDIA | `usbd_register_sd_wr_cb` |
| `0x1657E0` | MEDIA | `pmu_isr_bh` |
| `0x168A74` | MEDIA | `crab_monitor` |
| `0x16A324` | MEDIA | `cli_queue` |
| `0x16A404` | MEDIA | `CLI_HALT` |
| `0x16B774` | MEDIA | `authorization_code` |
| `0x177FC8` | MEDIA | `sdmmc_wrap_init` |
| `0x17CF76` | MEDIA | `HAL_timer_init` |
| `0x17D0BE` | MEDIA | `HAL_timer_start` |
| `0x17D2AC` | MEDIA | `HAL_uart_register_rx_callback` |
| `0x18067C` | MEDIA | `bt_isr_bh` |
| `0x189C50` | MEDIA | `spark_bt_l2cap_entry` |
| `0x18A3D0` | MEDIA | `a2dp_src_send_stream` |
| `0x18A76C` | MEDIA | `spark_bt_a2dp_src_entry` |
| `0x18CA38` | MEDIA | `spark_bt_avrcp_tg_entry` |
| `0x18F698` | MEDIA | `spark_bt_rfcomm_entry` |
| `0x1904E8` | MEDIA | `spark_bt_sdp_entry` |
| `0x191A40` | MEDIA | `bt_name` |
| `0x191A98` | MEDIA | `bt_name` |
| `0x1922FC` | BAIXA | `bt_host_task | bt_host_timer` |
| `0x192374` | MEDIA | `bt_host_task` |
