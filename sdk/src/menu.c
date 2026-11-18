/* Applications menu (page 0x53) hook.
 *
 * The factory builds the page and its three rows (Despertador, Imagem,
 * Dicionario).  This hook then replaces the third row with the first SDK
 * app and, in the games build, appends Mp3tris as a fourth row.  ENTER on
 * a row opens its overlay; every other key is forwarded to the factory's
 * row callback so navigation and Back keep working.
 *
 * Based on the SL6801_player SDK by Dmitry Brant, used with permission.
 */
#include "sdk.h"

#ifdef FW_DIAG
void keytest_open(lv_obj_t *return_focus);
static const fw_app_t fw_apps[] = {
	{"Teste de teclas", keytest_open},
};
#else
void flutter_open(lv_obj_t *return_focus);
void mp3tris_open(lv_obj_t *return_focus);
static const fw_app_t fw_apps[] = {
	{"Flutter", flutter_open},
	{"Mp3tris", mp3tris_open},
};
#endif

#define FW_APP_COUNT (sizeof(fw_apps) / sizeof(fw_apps[0]))

static void app_item_cb(lv_event_t *e)
{
	if (lv_event_get_code(e) != LV_EVENT_KEY)
		return;
	uint32_t key = *(uint32_t *)lv_event_get_param(e);
	if (key == LV_KEY_ENTER) {
		const fw_app_t *app = lv_event_get_user_data(e);
		if (app && app->open)
			app->open(e->target);
		return;
	}
	/* Let the factory callback handle Left/Right/Back/... exactly as it
	 * does for its own rows.  It never reaches ENTER here. */
	FW_PAGE_MENU_EVENT_CB(e);
}

static void append_row(lv_obj_t *list, const fw_app_t *app)
{
	lv_coord_t hor = lv_disp_get_hor_res(NULL);
	lv_coord_t ver = lv_disp_get_ver_res(NULL);

	lv_obj_t *row = FW_MENU_LIST_ITEM_CREATE(list);
	if (!row)
		return;
	lv_obj_set_height(row, (lv_coord_t)(ver / 7));
	lv_obj_set_style_border_side(row, 3, 0);
	lv_obj_add_event_cb(row, app_item_cb, LV_EVENT_KEY, (void *)app);
	lv_group_add_obj(fw_view_group(), row);

	lv_obj_t *icon = lv_label_create(row);
	lv_label_set_text(icon, "");
	lv_obj_t *text = lv_label_create(row);
	lv_obj_set_width(text, (lv_coord_t)(hor - 4 - lv_obj_get_width(icon)));
	lv_label_set_long_mode(text, LV_LABEL_LONG_SCROLL_CIRCULAR);
	lv_label_set_text(text, app->name);
	FW_MENU_LIST_ITEM_LAYOUT(row, 0, 0, 2);
}

int hook_home_menu_create(void)
{
	int ret = FW_MENU_PAGE_CREATE();
	if (ret)
		return ret;

	uint8_t *page = fw_view_page();
	if (!page)
		return 0;

	lv_obj_t **items = (lv_obj_t **)page;
	lv_obj_t **texts = (lv_obj_t **)(page + 0x0C);
	lv_obj_t **icons = (lv_obj_t **)(page + 0x18);

	lv_obj_t *l = items[2];
	if (l) {
		/* Remove the factory callback from this row so ENTER no longer
		 * opens the dictionary page; keep everything else. */
		lv_obj_remove_event_cb(l, FW_PAGE_MENU_EVENT_CB);
		lv_obj_add_event_cb(l, app_item_cb, LV_EVENT_KEY, (void *)&fw_apps[0]);
		if (texts[2])
			lv_label_set_text(texts[2], fw_apps[0].name);
		if (icons[2])
			lv_label_set_text(icons[2], "");
	}

	if (FW_APP_COUNT > 1) {
		lv_obj_t *first = items[0];
		lv_obj_t *list = first ? fw_obj_parent(first) : NULL;
		if (list)
			append_row(list, &fw_apps[1]);
	}
	return 0;
}
