/* Helpers shared by the OpenPod Reload 3.1 apps.
 * Based on the SL6801_player SDK by Dmitry Brant, used with permission. */
#pragma once
#include "fw.h"

/* Implemented in sdk/src/libc.c (no C library is linked). */
void *memset(void *dst, int c, size_t n);
void *memcpy(void *dst, const void *src, size_t n);
void *memmove(void *dst, const void *src, size_t n);
size_t strlen(const char *s);

/* An app shown in the Applications menu (page 0x53).  name_pt is optional:
 * when it is set and the UI language is Portuguese, the menu shows it. */
typedef struct {
	const char *name;
	void (*open)(lv_obj_t *return_focus);
	const char *name_pt;
} fw_app_t;

/* Full-screen overlay on the top layer.  It takes all key input until it
 * is deleted.  on_delete runs when the root is deleted for any reason
 * (fw_overlay_close or the firmware tearing down the UI); stop timers and
 * free the app state there.  The group is frozen while the overlay is
 * open, so the page below never sees the keys. */
typedef struct {
	lv_obj_t *root;
	lv_group_t *group;
	lv_obj_t *return_focus;
	void (*on_delete)(void *ctx);
	void *ctx;
} fw_overlay_t;

fw_overlay_t *fw_overlay_open(lv_obj_t *return_focus, lv_color_t bg, void (*on_delete)(void *ctx), void *ctx);
void fw_overlay_close(fw_overlay_t *ov);

/* Small helpers. */
char *fw_put_str(char *p, const char *s);
char *fw_put_dec(char *p, uint32_t v);
char *fw_put_hex(char *p, uint32_t v, int digits);
lv_obj_t *fw_label(lv_obj_t *parent, const char *text, lv_color_t color);
lv_obj_t *fw_rect(lv_obj_t *parent, lv_coord_t w, lv_coord_t h, lv_color_t color);
