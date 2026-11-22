/*
 * Firmware API for the OpenPod Reload 3.1 SDK on the Iigenai GN-438
 * (Smartlink/YP3, yp3_2.0.43).  Based on the SL6801_player SDK by Dmitry
 * Brant, used with permission (see docs/tarefas/022-analise.md).
 *
 * Every address below was found in OUR ORIGINAL, not copied from the
 * reference: that image is another build and its addresses differ.
 * Functions are called through a constant pointer with the Thumb bit set.
 *
 * The injected code runs from free flash (file offset 0x1AB000, XIP
 * 0xDAB000) and must not have writable globals; keep state in lv_mem_alloc.
 */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define FW_FN(addr, ret, args) ((ret (*) args)((uintptr_t)(addr) | 1u))

/* ---------------------------------------------------------------- LVGL types */

typedef struct _lv_obj_t lv_obj_t;
typedef struct _lv_font_t lv_font_t;
typedef int16_t lv_coord_t;
typedef uint32_t lv_style_selector_t;

typedef union {
	uint16_t full;
} lv_color_t;

typedef struct {
	uint32_t header; /* cf:5, always_zero:3, reserved:2, w:11, h:11 */
	uint32_t data_size;
	const uint8_t *data;
} lv_img_dsc_t;

#define LV_IMG_CF_TRUE_COLOR 4
#define LV_IMG_CF_TRUE_COLOR_CHROMA_KEYED 6
#define LV_IMG_CF_INDEXED_4BIT 9
#define LV_IMG_HEADER(cf, w, h) ((uint32_t)(cf) | ((uint32_t)(w) << 10) | ((uint32_t)(h) << 21))

/* lv_group_t: frozen is bit 0 and editing bit 1 of the byte at offset 0x18.
 * Confirmed in lv_group_focus_obj (0xD476B0): it tests bit 0 at +0x18 and
 * returns when frozen. */
typedef struct {
	uint8_t _ll[12];
	lv_obj_t **obj_focus;
	void *focus_cb;
	void *edge_cb;
	uint8_t flags;
} lv_group_t;

/* lv_event_t layout in this firmware (v8.3, LV_USE_USER_DATA=0 on objects):
 * target +0, current_target +4, code +8, user_data +0xC, param +0x10.
 * Proved by the getters: 0xD47030 ldr [r0], 0xD47034 ldrb [r0,#8],
 * 0xD47038 ldr [r0,#0x10], 0xD4703C ldr [r0,#0xC]. */
typedef struct {
	lv_obj_t *target;
	lv_obj_t *current_target;
	uint8_t code;
	void *user_data;
	void *param;
} lv_event_t;

typedef void (*lv_event_cb_t)(lv_event_t *e);

#define LV_EVENT_ALL 0
#define LV_EVENT_PRESSED 1
#define LV_EVENT_RELEASED 8
#define LV_EVENT_KEY 13
#define LV_EVENT_DELETE 33

#define LV_KEY_NEXT 9
#define LV_KEY_ENTER 10
#define LV_KEY_PREV 11
#define LV_KEY_UP 17
#define LV_KEY_DOWN 18
#define LV_KEY_RIGHT 19
#define LV_KEY_LEFT 20
#define LV_KEY_ESC 27

/* Physical buttons of the GN-438 as measured on the device (2026-11-18,
 * "Teste de teclas" of 3.1a; keyad_read 0xD21110).  This player has no
 * Up/Down: the old 0x11/0x12 codes never arrive.  The long variants of
 * Prev/Next (0x87/0x89) are the auto-repeat events forwarded by the key
 * manager.  Back long 0x82 is consumed for volume and never reaches the
 * UI: do not use it.  Play 0x0A is LV_KEY_ENTER and may also be the power
 * key on some units, so the apps use it only as a menu-like action. */
#define FW_KEY_BACK 0x81
#define FW_KEY_M 0xA0
#define FW_KEY_M_LONG 0xA2
#define FW_KEY_PREV 0x14
#define FW_KEY_NEXT 0x13
#define FW_KEY_PREV_LONG 0x87
#define FW_KEY_NEXT_LONG 0x89
#define FW_KEY_PLAY 0x0A

/* Current UI language: get_lang_str (0xD2108C) dispatches through
 * 0xD0E2B8, which returns the byte at 0x00823D06.  Index 8 selects the
 * Portuguese table 0xC53B84 (id 0 "Português", id 7 "Despertador",
 * id 159 "Aplicativos"), proved in docs/tarefas/023-analise.md. */
#define FW_LANG (*(volatile uint8_t *)0x00823D06)
#define FW_LANG_PT 8

#define LV_ALIGN_TOP_MID 2
#define LV_ALIGN_CENTER 9
#define LV_ALIGN_BOTTOM_MID 5

#define LV_LABEL_LONG_WRAP 0
#define LV_LABEL_LONG_SCROLL_CIRCULAR 4
#define LV_LABEL_LONG_DOT 3
#define LV_TEXT_ALIGN_CENTER 2

#define LV_OBJ_FLAG_HIDDEN (1u << 0)
#define LV_OBJ_FLAG_CLICKABLE (1u << 1)
#define LV_OBJ_FLAG_SCROLLABLE (1u << 4)

typedef struct _lv_timer_t {
	uint32_t period;
	uint32_t last_run;
	void (*timer_cb)(struct _lv_timer_t *t);
	void *user_data;
	int32_t repeat_count;
	uint8_t paused;
} lv_timer_t;
typedef void (*lv_timer_cb_t)(lv_timer_t *t);

static inline lv_color_t lv_rgb(uint8_t r, uint8_t g, uint8_t b)
{
	uint16_t v = (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
	lv_color_t c = {(uint16_t)((v >> 8) | (v << 8))}; /* LV_COLOR_16_SWAP */
	return c;
}

/* ---------------------------------------------------------------- LVGL functions
 * All addresses below are CONFIRMED unless marked PROVAVEL in
 * docs/tarefas/022-analise.md. */

#define lv_mem_alloc FW_FN(0x00D58188, void *, (size_t size))
#define lv_mem_free FW_FN(0x00D5811C, void, (void *p))

#define lv_disp_get_scr_act FW_FN(0x00D46E24, lv_obj_t *, (void *disp))
#define lv_disp_get_layer_top FW_FN(0x00D46E8C, lv_obj_t *, (void *disp))
#define lv_disp_get_hor_res FW_FN(0x00D568A4, lv_coord_t, (void *disp))
#define lv_disp_get_ver_res FW_FN(0x00D568CC, lv_coord_t, (void *disp))
#define lv_layer_top() lv_disp_get_layer_top(NULL)

#define lv_obj_create FW_FN(0x00D491EC, lv_obj_t *, (lv_obj_t *parent))
#define lv_obj_del FW_FN(0x00D4D350, void, (lv_obj_t *obj))
#define lv_obj_set_size FW_FN(0x00D4A21A, void, (lv_obj_t *obj, lv_coord_t w, lv_coord_t h))
#define lv_obj_set_width FW_FN(0x00D4A1BA, void, (lv_obj_t *obj, lv_coord_t w))
#define lv_obj_set_height FW_FN(0x00D4A1EA, void, (lv_obj_t *obj, lv_coord_t h))
#define lv_obj_set_pos FW_FN(0x00D4A2D4, void, (lv_obj_t *obj, lv_coord_t x, lv_coord_t y))
#define lv_obj_align FW_FN(0x00D4A3A2, void, (lv_obj_t *obj, uint8_t align, lv_coord_t x, lv_coord_t y))
#define lv_obj_add_flag FW_FN(0x00D49204, void, (lv_obj_t *obj, uint32_t f))
#define lv_obj_clear_flag FW_FN(0x00D4924A, void, (lv_obj_t *obj, uint32_t f))
#define lv_obj_invalidate FW_FN(0x00D4A70C, void, (lv_obj_t *obj))
#define lv_obj_get_width FW_FN(0x00D4A45E, lv_coord_t, (lv_obj_t *obj))

/* lv_obj_get_parent: if (obj) return obj->parent (offset +4).  Proved by
 * lv_obj_del (0xD4D350), which reads [obj+4] as the parent.  PROVAVEL as a
 * public symbol, CONFIRMADO as behaviour. */
#define fw_obj_parent FW_FN(0x00D4D1FC, lv_obj_t *, (lv_obj_t *obj))

#define lv_timer_create FW_FN(0x00D59020, lv_timer_t *, (lv_timer_cb_t cb, uint32_t period, void *user_data))
#define lv_timer_del FW_FN(0x00D59090, void, (lv_timer_t *t))
#define lv_tick_get FW_FN(0x00D56A6C, uint32_t, (void))

#define lv_obj_add_event_cb FW_FN(0x00D47064, void *, (lv_obj_t *obj, lv_event_cb_t cb, uint8_t filter, void *user_data))
#define lv_obj_remove_event_cb FW_FN(0x00D470E4, bool, (lv_obj_t *obj, lv_event_cb_t cb))

#define lv_obj_set_style_align FW_FN(0x00D4D010, void, (lv_obj_t *obj, uint32_t v, lv_style_selector_t s))
#define lv_obj_set_style_pad_top FW_FN(0x00D4D01C, void, (lv_obj_t *obj, lv_coord_t v, lv_style_selector_t s))
#define lv_obj_set_style_pad_bottom FW_FN(0x00D4D028, void, (lv_obj_t *obj, lv_coord_t v, lv_style_selector_t s))
#define lv_obj_set_style_pad_left FW_FN(0x00D4D034, void, (lv_obj_t *obj, lv_coord_t v, lv_style_selector_t s))
#define lv_obj_set_style_pad_right FW_FN(0x00D4D040, void, (lv_obj_t *obj, lv_coord_t v, lv_style_selector_t s))
#define lv_obj_set_style_radius FW_FN(0x00D4D064, void, (lv_obj_t *obj, lv_coord_t v, lv_style_selector_t s))
#define lv_obj_set_style_bg_color FW_FN(0x00D4D092, void, (lv_obj_t *obj, lv_color_t v, lv_style_selector_t s))
#define lv_obj_set_style_bg_opa FW_FN(0x00D4D0B4, void, (lv_obj_t *obj, uint8_t v, lv_style_selector_t s))
#define lv_obj_set_style_border_color FW_FN(0x00D4D0C8, void, (lv_obj_t *obj, lv_color_t v, lv_style_selector_t s))
#define lv_obj_set_style_border_width FW_FN(0x00D4D0F4, void, (lv_obj_t *obj, lv_coord_t v, lv_style_selector_t s))
#define lv_obj_set_style_border_side FW_FN(0x00D4D100, void, (lv_obj_t *obj, uint8_t v, lv_style_selector_t s))
#define lv_obj_set_style_text_color FW_FN(0x00D4D10A, void, (lv_obj_t *obj, lv_color_t v, lv_style_selector_t s))
#define lv_obj_set_style_text_font FW_FN(0x00D4D12E, void, (lv_obj_t *obj, const lv_font_t *v, lv_style_selector_t s))
#define lv_obj_set_style_text_align FW_FN(0x00D4D13A, void, (lv_obj_t *obj, uint8_t v, lv_style_selector_t s))

#define lv_label_create FW_FN(0x00D5E2E8, lv_obj_t *, (lv_obj_t *parent))
#define lv_label_set_text FW_FN(0x00D5ED94, void, (lv_obj_t *obj, const char *text))
#define lv_label_set_long_mode FW_FN(0x00D5EF04, void, (lv_obj_t *obj, uint8_t mode))
#define lv_img_create FW_FN(0x00D5D850, lv_obj_t *, (lv_obj_t *parent))
#define lv_img_set_src FW_FN(0x00D5D868, void, (lv_obj_t *obj, const void *src))

#define lv_event_get_code FW_FN(0x00D47034, uint8_t, (lv_event_t *e))
#define lv_event_get_param FW_FN(0x00D47038, void *, (lv_event_t *e))
static inline void *lv_event_get_user_data(lv_event_t *e) { return e->user_data; }

#define lv_group_get_default FW_FN(0x00D4746C, lv_group_t *, (void))
#define lv_group_add_obj FW_FN(0x00D4751C, void, (lv_group_t *g, lv_obj_t *obj))
#define lv_group_focus_obj FW_FN(0x00D476B0, void, (lv_obj_t *obj))
#define lv_group_focus_next FW_FN(0x00D474C4, void, (lv_group_t *g))
#define lv_group_focus_prev FW_FN(0x00D474DC, void, (lv_group_t *g))
#define lv_group_get_focused FW_FN(0x00D47648, lv_obj_t *, (lv_group_t *g))
static inline void lv_group_focus_freeze(lv_group_t *g, bool en)
{
	g->flags = (uint8_t)((g->flags & ~1u) | (en ? 1u : 0u));
}

/* ---------------------------------------------------------------- vendor firmware */

#define fw_log FW_FN(0x000002B0, int, (const char *fmt, ...))

/* View context: *(FW_VIEW_CTX) points to the struct that holds the key
 * group at +0x3C and the current page at +0x1E8 (both confirmed in
 * page_home_menu_create 0xD2F0A0 and watch_key_work_process 0xCFC7A8). */
#define FW_VIEW_CTX (*(uint8_t **)0x0081CE2C)
#define fw_view_group() (*(lv_group_t **)(FW_VIEW_CTX + 0x3C))
#define fw_view_page() (*(void **)(FW_VIEW_CTX + 0x1E8))

#define FW_SYSTICK_VAL (*(volatile uint32_t *)0xE000E018)

/* Font with the UI glyphs and the FontAwesome icons.  We only use its
 * metrics indirectly; all text here is plain ASCII and inherits the theme
 * font (the firmware's own header label 0xD2F11A does the same). */
#define FW_FONT_ICONS ((const lv_font_t *)0x00CA671C)

/* App menu (page 0x53).  The factory creates the page and its three rows;
 * the hook runs after it and modifies item[2] / appends rows. */
#define FW_HOME_PAGE_CREATE FW_FN(0x00D2EBB8, int, (void))
#define FW_MENU_PAGE_CREATE FW_FN(0x00D2F0A0, int, (void))
#define FW_PAGE_MENU_EVENT_CB ((lv_event_cb_t)0x00D2EF5Du)
#define FW_MENU_LIST_ITEM_CREATE FW_FN(0x00D21764, lv_obj_t *, (lv_obj_t *list))
#define FW_MENU_LIST_ITEM_LAYOUT FW_FN(0x00D51704, void, (lv_obj_t *row, lv_coord_t a, lv_coord_t b, lv_coord_t c))
