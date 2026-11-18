/* "Teste de teclas": full-screen overlay that shows the code of each key.
 * Two Back presses (or ESC) in a row close it, so a single Back can be seen.
 * Based on the SL6801_player SDK by Dmitry Brant, used with permission. */
#include "sdk.h"

typedef struct {
	fw_overlay_t *ov;
	lv_obj_t *keys;
	uint32_t presses;
	uint32_t last;
} app_t;

static void on_delete(void *ctx)
{
	lv_mem_free(ctx);
}

static void key_cb(lv_event_t *e)
{
	app_t *app = lv_event_get_user_data(e);
	uint32_t key = *(uint32_t *)lv_event_get_param(e);
	bool back = key == FW_KEY_BACK || key == LV_KEY_ESC;
	if (back && app->last == key) {
		fw_overlay_close(app->ov);
		return;
	}
	app->last = key;
	char buf[64];
	char *p = fw_put_str(buf, "tecla ");
	p = fw_put_hex(p, key, 2);
	p = fw_put_str(p, "\npressoes: ");
	p = fw_put_dec(p, ++app->presses);
	if (back)
		fw_put_str(p, "\nBack de novo para sair.");
	lv_label_set_text(app->keys, buf); /* copies the text */
}

void keytest_open(lv_obj_t *return_focus)
{
	app_t *app = lv_mem_alloc(sizeof(app_t));
	if (!app)
		return;
	app->presses = 0;
	app->last = 0;
	app->ov = fw_overlay_open(return_focus, lv_rgb(0x10, 0x20, 0x60), on_delete, app);
	if (!app->ov) {
		lv_mem_free(app);
		return;
	}
	lv_obj_t *root = app->ov->root;

	lv_obj_align(fw_label(root, "Teste de teclas", lv_rgb(0xFF, 0xD0, 0x40)), LV_ALIGN_TOP_MID, 0, 4);
	app->keys = fw_label(root, "Pressione uma tecla.\nBack duas vezes para sair.", lv_rgb(0xFF, 0xFF, 0xFF));
	lv_obj_set_style_text_align(app->keys, LV_TEXT_ALIGN_CENTER, 0);
	lv_obj_align(app->keys, LV_ALIGN_CENTER, 0, 0);
	lv_obj_add_event_cb(root, key_cb, LV_EVENT_KEY, app);
}
