# PAGINAS — numero, presenter e view

Gerado por `tools/mapa_paginas.py` a partir de `firmware/ORIGINAL/GN438_original.bin`.

O firmware tem **dois vocabularios** para a mesma tela: o presenter
a identifica por NUMERO, a view por NOME. Esta tabela liga os dois.

A ligacao vem de `0x0010EF64`, tabela de ponteiros **indexada por
numero de pagina**, que aponta para stubs de 6 bytes em `0x0010F0B0`
(`bl <presenter>; b <retorno>`). A ordem dos stubs **nao** e a ordem
das paginas — ha trocas e buracos, e a tabela de ponteiros desembaralha.

Coluna `ok` = o nome que o proprio firmware da ao presenter cita este
numero de pagina. E a validacao independente.

## O desencontro de numeracao, resolvido

O nome do presenter e o ID da pagina **coincidem ate a pagina 70** e
**divergem de 1 a partir da 75**:

```
pagina 0x1E (30)  ->  page30_scr_process     bate
pagina 0x44 (68)  ->  page68_btn_process     bate
pagina 0x4B (75)  ->  page76_scr_process     +1
pagina 0x53 (83)  ->  page84_scr_process     +1
```

**O ID da pagina e a autoridade** — ele vem de duas tabelas
independentes (`0x0010EF64` do presenter e `0x00D23B38` da view), e
as duas concordam: a pagina 83 e o Extras nas duas.

O numero **no nome** e historico: presenters foram acrescentados ou
removidos entre a 70 e a 75 e os nomes nao foram renumerados. Isso
desfaz o alarme que ficou em `ARQUITETURA.md` §7.3: `page84` e a
pagina 0x53 sao a mesma tela, e o Extras sempre foi a 83.

Nao ha pagina nenhuma nos intervalos 36-39, 50, 52-54, 57-59, 61-67
e 71-74: nem presenter, nem view.

| # | presenter | nome do presenter | view | nome da view | ok |
|---|---|---|---|---|---|
| **1** (0x01) | `0x100F3C` | `page1_img_process` | `0x12EBB8` | `page_home_event_cb` | sim |
| **2** (0x02) | `0x102FCC` | `page2_mbox_process + page2_scr_process` | `0x13178C` | `page_music_menu_event_cb` | sim |
| **3** (0x03) | `0x105D90` | `page3_btn_process + page3_scr_process + pstr_page3_process` | `0x132EB4` | `page_music_song_create` | sim |
| **4** (0x04) | `0x108A90` | `page4_btnm_process + page4_scr_process` | `0x131E7C` | `page_music_play_create` | sim |
| **5** (0x05) | `0x10A25C` | `page5_mbox_process + page5_scr_process` | `0x13275C` | `page_music_set_event_cb` | sim |
| **6** (0x06) | `0x10AD98` | `page6_btn_process + page6_scr_process + pstr_page6_process` | `0x12FE50` | `page_music_artist_event_cb` | sim |
| **7** (0x07) | `0x10B4D8` | `page7_btn_process + page7_scr_process + pstr_page7_process` | `0x12F794` | `page_music_album_event_cb` | sim |
| **8** (0x08) | `0x10C03C` | `page8_scr_process + pstr_page8_process` | `0x13348C` | `page_music_speed_create` | sim |
| **9** (0x09) | `0x10CDE8` | `page9_btn_process` | `0x130A38` | `page_music_loop_event_cb` | sim |
| **10** (0x0A) | `0x101728` | `page10_mbox_process + page10_scr_process` | `0x131124` | `page_music_mark_event_cb` | sim |
| **11** (0x0B) | `0x1018C0` | `page11_scr_process + pstr_page11_process` | `0x130434` | `page_music_eq_event_cb` | sim |
| **12** (0x0C) | `0x101B6C` | `page12_cont_process + page12_index_process` | `0x12AB48` | `page_ebook_list_event_cb` | sim |
| **13** (0x0D) | `0x101F10` | `page13_label_process + page13_scr_process  [tambem cita: ebook_auto_play]` | `0x12B8BC` | `page_ebook_read_event_cb` | sim |
| **14** (0x0E) | `0x102140` | `page14_scr_process + pstr_page14_process  [tambem cita: ebook_auto_play]` | `0x12BED4` | `page_ebook_set_scr_process` | sim |
| **15** (0x0F) | `0x102280` | `page15_btn_process` | `0x12C3FC` | `page_ebook_time_event_cb` | sim |
| **16** (0x10) | `0x1023B8` | `page16_scr_process + pstr_page16_process` | `0x12A128` | `page_ebook_bg_create` | sim |
| **17** (0x11) | `0x1024E4` | `page17_btnm_process` | `0x12A64C` | `page_ebook_input_create` | sim |
| **18** (0x12) | `0x1028B4` | `page18_mbox_process + page18_scr_process` | `0x12B1B4` | `page_ebook_mark_event_cb` | sim |
| **19** (0x13) | `0x102B88` | `page19_cont_process + page19_index_process + pstr_page19_process` | `0x13D5A4` | `page_video_list_event_cb` | sim |
| **20** (0x14) | `0x1034F0` | `page20_video_process` | `0x13DB1C` | `page_video_play_event_cb` | sim |
| **21** (0x15) | `0x103930` | `page21_cont_process + page21_index_process + pstr_page21_process` | `0x133AF4` | `page_pict_list_event_cb` | sim |
| **22** (0x16) | `0x103BC0` | `page22_scr_process` | `0x13404C` | `page_pict_play_event_cb` | sim |
| **23** (0x17) | `0x103E00` | `page23_scr_process + pstr_page23_process` | `0x1352E8` | `page_record_time_create` | sim |
| **24** (0x18) | `0x104110` | `page24_btn_process` | `0x13458C` | `page_record_menu_event_cb` | sim |
| **25** (0x19) | `0x1047FC` | `page25_btn_process + page25_mbox_process + pstr_page25_process` | `0x135978` | `page_record_work_event_cb` | sim |
| **26** (0x1A) | `0x1051DC` | `page26_btnm_process` | `0x12CD04` | `page_fm_play_create` | sim |
| **27** (0x1B) | `0x105588` | `page27_mbox_process + page27_scr_process` | `0x12D930` | `page_fm_set_event_cb` | sim |
| **28** (0x1C) | `0x105774` | `page28_scr_process + pstr_page28_process` | `0x12C910` | `page_fm_band_event_cb` | sim |
| **29** (0x1D) | `0x105A24` | `page29_btn_process + pstr_page29_process` | `0x12D280` | `page_fm_preset_event_cb` | sim |
| **30** (0x1E) | `0x10623C` | `page30_scr_process + pstr_page30_process` | `0x12724C` | `page_alarm_menu_event_cb` | sim |
| **31** (0x1F) | `0x10640C` | `page31_btn_process` | `0x127B78` | `page_alarm_time_event_cb` | sim |
| **32** (0x20) | `0x10658C` | `page32_scr_process + pstr_page32_process` | `0x126BCC` | `page_alarm_cycle_event_cb` | sim |
| **33** (0x21) | `0x106710` | `page33_btn_process` | `0x1277C8` | `page_alarm_play_create` | sim |
| **34** (0x22) | `0x106CBC` | `page34_cont_process + page34_scr_process + pstr_page34_process` | `0x12E05C` | `page_folder_list_create` | sim |
| **35** (0x23) | `0x1081DC` | `btplay_stop | pstr_bt_analysis` | `0x1286E0` | `page_bt_menu_option_event_cb` | **nao** |
| **40** (0x28) | `0x109150` | `page40_btn_process + pstr_page40_process` | `0x13A638` | `page_set_menu_event_cb` | sim |
| **41** (0x29) | `0x10938C` | `page41_btn_process` | `0x139FB8` | `page_set_lang_event_cb` | sim |
| **42** (0x2A) | `0x1094DC` | `page42_scr_process + pstr_page42_process` | `0x13634C` | `page_date_time_event_cb` | sim |
| **43** (0x2B) | `0x1096F4` | `page43_scr_process + pstr_page43_process` | `0x1388E4` | `page_set_date_event_cb` | sim |
| **44** (0x2C) | `0x1098D0` | `page44_scr_process + pstr_page44_process` | `0x13BE70` | `page_set_time_event_cb` | sim |
| **45** (0x2D) | `0x109A18` | `page45_btn_process` | `0x138298` | `page_set_bright_event_cb` | sim |
| **46** (0x2E) | `0x109BEC` | `page46_scr_process + pstr_page46_process` | `0x13AD18` | `page_set_offscr_create` | sim |
| **47** (0x2F) | `0x109D50` | `page47_btn_process` | `0x13B330` | `page_set_offscr_time_create` | sim |
| **48** (0x30) | `0x109ED8` | `page48_scr_process + pstr_page48_process` | `0x138F00` | `page_set_idleshut_event_cb` | sim |
| **49** (0x31) | `0x109FFC` | `page49_btn_process` | `0x13951C` | `page_set_idleshut_time_event_cb` | sim |
| **51** (0x33) | `0x10A5A0` | `page51_scr_process + pstr_page51_process` | `0x136838` | `page_device_info_event_cb` | sim |
| **55** (0x37) | `0x10A6E0` | `page55_scr_process + pstr_page55_process` | `0x129934` | `page_dict_input_event_cb` | sim |
| **56** (0x38) | `0x10A99C` | `page56_scr_process + pstr_page56_process` | `0x129C6C` | `page_dict_play_event_cb` | sim |
| **60** (0x3C) | `0x10AF98` | `page60_scr_process + pstr_page60_process` | `0x136C38` | `page_lang_option_event_cb` | sim |
| **68** (0x44) | `0x10B0AC` | `page68_btn_process` | `0x137CEC` | `page_scrsaver_time_event_cb` | sim |
| **69** (0x45) | `0x10B1F8` | `page69_btn_process` | — | — | sim |
| **70** (0x46) | `0x10B904` | `page70_btn_process` | — | — | sim |
| **75** (0x4B) | `0x10BA90` | `page76_scr_process + pstr_page76_process` | `0x139A44` | `page_set_keylight_event_cb` | **nao** |
| **76** (0x4C) | `0x10BBA4` | `page77_btn_process` | `0x13B868` | `page_set_speaker_event_cb` | **nao** |
| **77** (0x4D) | `0x10BCF4` | `page78_scr_process + pstr_page78_process` | `0x13C48C` | `page_set_timershut_event_cb` | **nao** |
| **78** (0x4E) | `0x10BF60` | `page79_scr_process + pstr_page79_process` | `0x13D040` | `page_storage_info_event_cb` | **nao** |
| **79** (0x4F) | `0x10C268` | `page80_scr_process + pstr_page80_process` | `0x1371B8` | `page_pass_input_event_cb` | **nao** |
| **80** (0x50) | `0x10C498` | `page81_btn_process` | `0x13773C` | `page_pass_menu_event_cb` | **nao** |
| **81** (0x51) | `0x10C764` | `page82_scr_process` | `0x12E6B4` | `page_expand_home_event_cb` | **nao** |
| **82** (0x52) | `0x10CA94` | `page83_scr_process + pstr_page83_process` | `0x13CAA8` | `page_set_timershut_time_event_cb` | **nao** |
| **83** (0x53) | `0x10CC0C` | `page84_scr_process + pstr_page84_process` | `0x12F0A0` | `page_home_menu_event_cb` | **nao** |

## Paginas sem presenter

[]

Sao telas que a view constroi mas que nao tem logica propria de
presenter — provavelmente sub-telas tratadas pelo presenter do pai.

## Paginas sem view

[69, 70]

