/* Full-screen overlay and small UI helpers.
 * Based on the SL6801_player SDK by Dmitry Brant, used with permission. */
#include "sdk.h"

static void overlay_delete_cb(lv_event_t *e)
{
	fw_overlay_t *ov = lv_event_get_user_data(e);
	lv_group_focus_freeze(ov->group, false);
	if (ov->on_delete)
		ov->on_delete(ov->ctx);
	lv_mem_free(ov);
}

fw_overlay_t *fw_overlay_open(lv_obj_t *return_focus, lv_color_t bg, void (*on_delete)(void *ctx), void *ctx)
{
	fw_overlay_t *ov = lv_mem_alloc(sizeof(*ov));
	if (!ov)
		return NULL;
	ov->group = fw_view_group();
	ov->return_focus = return_focus;
	ov->on_delete = on_delete;
	ov->ctx = ctx;

	lv_obj_t *root = lv_obj_create(lv_layer_top());
	ov->root = root;
	lv_obj_set_pos(root, 0, 0);
	lv_obj_set_size(root, lv_disp_get_hor_res(NULL), lv_disp_get_ver_res(NULL));
	lv_obj_clear_flag(root, LV_OBJ_FLAG_SCROLLABLE);
	lv_obj_set_style_radius(root, 0, 0);
	lv_obj_set_style_border_width(root, 0, 0);
	lv_obj_set_style_pad_top(root, 0, 0);
	lv_obj_set_style_pad_bottom(root, 0, 0);
	lv_obj_set_style_pad_left(root, 0, 0);
	lv_obj_set_style_pad_right(root, 0, 0);
	lv_obj_set_style_bg_color(root, bg, 0);
	lv_obj_set_style_bg_opa(root, 255, 0);
	lv_obj_add_event_cb(root, overlay_delete_cb, LV_EVENT_DELETE, ov);

	lv_group_add_obj(ov->group, root);
	lv_group_focus_obj(root);
	lv_group_focus_freeze(ov->group, true);
	return ov;
}

void fw_overlay_close(fw_overlay_t *ov)
{
	lv_obj_t *back = ov->return_focus;
	lv_obj_del(ov->root); /* runs overlay_delete_cb, which frees ov */
	if (back)
		lv_group_focus_obj(back);
}

char *fw_put_str(char *p, const char *s)
{
	while (*s)
		*p++ = *s++;
	*p = 0;
	return p;
}

char *fw_put_dec(char *p, uint32_t v)
{
	char tmp[10];
	int n = 0;
	do {
		tmp[n++] = (char)('0' + v % 10);
		v /= 10;
	} while (v);
	while (n)
		*p++ = tmp[--n];
	*p = 0;
	return p;
}

char *fw_put_hex(char *p, uint32_t v, int digits)
{
	static const char hex[] = "0123456789ABCDEF";
	p = fw_put_str(p, "0x");
	for (int i = digits - 1; i >= 0; i--)
		*p++ = hex[(v >> (4 * i)) & 0xF];
	*p = 0;
	return p;
}

lv_obj_t *fw_label(lv_obj_t *parent, const char *text, lv_color_t color)
{
	lv_obj_t *l = lv_label_create(parent);
	lv_obj_set_style_text_color(l, color, 0);
	lv_label_set_text(l, text);
	return l;
}

lv_obj_t *fw_rect(lv_obj_t *parent, lv_coord_t w, lv_coord_t h, lv_color_t color)
{
	lv_obj_t *r = lv_obj_create(parent);
	lv_obj_clear_flag(r, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_CLICKABLE);
	lv_obj_set_size(r, w, h);
	lv_obj_set_style_radius(r, 0, 0);
	lv_obj_set_style_border_width(r, 0, 0);
	lv_obj_set_style_pad_top(r, 0, 0);
	lv_obj_set_style_pad_bottom(r, 0, 0);
	lv_obj_set_style_pad_left(r, 0, 0);
	lv_obj_set_style_pad_right(r, 0, 0);
	lv_obj_set_style_bg_color(r, color, 0);
	lv_obj_set_style_bg_opa(r, 255, 0);
	return r;
}
